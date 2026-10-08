"""Google Workspace client (Drive / Docs) for PMO document ops.

Supports:
- Service account JSON (`GOOGLE_APPLICATION_CREDENTIALS`)
- User OAuth desktop client (`GOOGLE_OAUTH_CLIENT_SECRETS` + token) — preferred when
  Drive folders are private / not shared to a service account
- Multiple named directories via `config/google-directories.json`
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from .config import Config

ROOT = Path(__file__).resolve().parents[3]

DRIVE_SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/drive.metadata.readonly",
]
# Broader scope when write/export needs it — export Doc works with drive.readonly
DRIVE_SCOPES_RW = ["https://www.googleapis.com/auth/drive"]
SHEETS_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SHEETS_READONLY_SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
# Create/update Gmail drafts (does not send)
GMAIL_COMPOSE_SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]
# Read sendAs signature (HTML footer from Gmail Settings)
GMAIL_SETTINGS_SCOPES = ["https://www.googleapis.com/auth/gmail.settings.basic"]
# Read mailbox (sent status emails for style calibration)
GMAIL_READONLY_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def oauth_scopes(
    *,
    drive_rw: bool = False,
    gmail: bool = False,
    sheets: bool = False,
    sheets_readonly: bool = False,
) -> list[str]:
    """Scopes for interactive OAuth / token refresh."""
    scopes = list(DRIVE_SCOPES_RW if drive_rw or sheets else DRIVE_SCOPES)
    if sheets:
        for s in SHEETS_SCOPES:
            if s not in scopes:
                scopes.append(s)
    elif sheets_readonly:
        for s in SHEETS_READONLY_SCOPES:
            if s not in scopes:
                scopes.append(s)
    if gmail:
        for s in GMAIL_COMPOSE_SCOPES + GMAIL_SETTINGS_SCOPES + GMAIL_READONLY_SCOPES:
            if s not in scopes:
                scopes.append(s)
    return scopes


def _scopes_satisfied(have: set[str], need: set[str]) -> bool:
    """True if token grants every needed scope (full Sheets implies readonly)."""
    if not need:
        return True
    effective = set(have)
    if "https://www.googleapis.com/auth/spreadsheets" in effective:
        effective.add("https://www.googleapis.com/auth/spreadsheets.readonly")
    if "https://www.googleapis.com/auth/drive" in effective:
        effective.add("https://www.googleapis.com/auth/drive.readonly")
        effective.add("https://www.googleapis.com/auth/drive.metadata.readonly")
    return need.issubset(effective)


def _canonicalize_scopes(scopes: list[str]) -> list[str]:
    """Drop redundant readonly scopes when a broader grant is present."""
    s = set(scopes)
    if "https://www.googleapis.com/auth/drive" in s:
        s.discard("https://www.googleapis.com/auth/drive.readonly")
        s.discard("https://www.googleapis.com/auth/drive.metadata.readonly")
    if "https://www.googleapis.com/auth/spreadsheets" in s:
        s.discard("https://www.googleapis.com/auth/spreadsheets.readonly")
    # Stable order: drive → sheets → gmail*
    order = [
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/drive.readonly",
        "https://www.googleapis.com/auth/drive.metadata.readonly",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/gmail.compose",
        "https://www.googleapis.com/auth/gmail.settings.basic",
        "https://www.googleapis.com/auth/gmail.readonly",
    ]
    out = [x for x in order if x in s]
    out.extend(sorted(x for x in s if x not in order))
    return out


# Recommended one-shot for PMO: Drive write + Sheets + Gmail drafts/signature.
PMO_OAUTH_SCOPES = oauth_scopes(drive_rw=True, sheets=True, gmail=True)


class GoogleNotConfigured(RuntimeError):
    pass


def _resolve_path(raw: str) -> Path:
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = ROOT / path
    return path


def _json_type(path: Path) -> str:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("type") == "service_account":
        return "service_account"
    if "installed" in data or "web" in data:
        return "oauth_client"
    return "unknown"


class GoogleWorkspaceClient:
    """Thin wrapper around Google APIs used by PMO (Drive folders = project docs hubs)."""

    def __init__(
        self,
        *,
        auth_mode: str = "auto",
        credentials_path: str = "",
        oauth_client_secrets: str = "",
        oauth_token_path: str = "",
        folder_id: str = "",
        delegated_user: str = "",
    ):
        self.auth_mode = (auth_mode or "auto").strip().lower()
        self.credentials_path = credentials_path
        self.oauth_client_secrets = oauth_client_secrets
        self.oauth_token_path = oauth_token_path or "./secrets/google-oauth-token.json"
        self.folder_id = folder_id
        self.delegated_user = delegated_user
        self._creds = None
        self._drive = None
        self._gmail = None
        self._sheets = None

    @classmethod
    def from_config(cls, cfg: Config) -> "GoogleWorkspaceClient":
        if not cfg.google_ok:
            raise GoogleNotConfigured(
                "Configure Google auth: put OAuth client JSON in secrets/ and run "
                "`cli.py google auth`, or set GOOGLE_APPLICATION_CREDENTIALS (service account). "
                "See secrets/README.md"
            )
        return cls(
            auth_mode=cfg.google_auth_mode,
            credentials_path=cfg.google_credentials_path,
            oauth_client_secrets=cfg.google_oauth_client_secrets,
            oauth_token_path=cfg.google_oauth_token_path,
            folder_id=cfg.google_drive_folder_id,
            delegated_user=cfg.google_delegated_user,
        )

    def _detect_mode(self) -> str:
        mode = self.auth_mode
        if mode in ("oauth", "user", "installed"):
            return "oauth"
        if mode in ("service_account", "sa"):
            return "service_account"
        # auto
        if self.oauth_client_secrets and _resolve_path(self.oauth_client_secrets).exists():
            return "oauth"
        if self.credentials_path:
            p = _resolve_path(self.credentials_path)
            if p.exists():
                kind = _json_type(p)
                if kind == "oauth_client":
                    return "oauth"
                return "service_account"
        if _resolve_path(self.oauth_token_path).exists():
            return "oauth"
        raise GoogleNotConfigured("Cannot detect Google auth mode — missing credentials files")

    def _load_service_account(self, scopes: list[str]):
        from google.oauth2 import service_account

        path = _resolve_path(self.credentials_path)
        if not path.exists():
            raise GoogleNotConfigured(f"Service account file not found: {path}")
        creds = service_account.Credentials.from_service_account_file(
            str(path), scopes=scopes
        )
        if self.delegated_user:
            creds = creds.with_subject(self.delegated_user)
        return creds

    def _load_oauth(self, scopes: list[str], *, interactive: bool = False):
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow

        token_path = _resolve_path(self.oauth_token_path)
        client_path = (
            _resolve_path(self.oauth_client_secrets)
            if self.oauth_client_secrets
            else None
        )
        if client_path is None and self.credentials_path:
            cand = _resolve_path(self.credentials_path)
            if cand.exists() and _json_type(cand) == "oauth_client":
                client_path = cand

        creds = None
        granted_scopes: list[str] | None = None
        if token_path.exists():
            # Load granted scopes from the token file first (do not pass desired scopes —
            # that would mask missing scopes and break refresh with invalid_scope).
            creds = Credentials.from_authorized_user_file(str(token_path))
            have = set(creds.scopes or [])
            granted_scopes = list(creds.scopes or [])
            need = set(scopes or [])
            if need and not _scopes_satisfied(have, need):
                if not interactive:
                    missing = sorted(need - have)
                    raise GoogleNotConfigured(
                        "OAuth token missing scopes: "
                        + ", ".join(missing)
                        + ". Re-run: python3 scripts/integrations/cli.py google auth "
                        "--sheets --write-scope   # or --gmail if only mail"
                    )
                token_path.unlink(missing_ok=True)
                creds = None
                granted_scopes = None
            # Keep creds as loaded from disk. Do NOT rebuild with a narrower
            # `scopes=` list — google-auth then overwrites token JSON on refresh
            # and silently drops Sheets/Gmail (Drive sync-pull footgun).

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            token_path.parent.mkdir(parents=True, exist_ok=True)
            # Always persist the originally granted scope set, never the
            # per-call request list (which may be Drive-readonly only).
            payload = json.loads(creds.to_json())
            if granted_scopes:
                payload["scopes"] = granted_scopes
            token_path.write_text(json.dumps(payload), encoding="utf-8")
            return creds

        if creds and creds.valid:
            return creds

        if not interactive:
            raise GoogleNotConfigured(
                f"OAuth token missing/expired at {token_path}. Run: "
                "python3 scripts/integrations/cli.py google auth"
            )
        if not client_path or not client_path.exists():
            raise GoogleNotConfigured(
                "OAuth client secrets JSON required "
                "(GOOGLE_OAUTH_CLIENT_SECRETS=./secrets/google-oauth-client.json). "
                "See secrets/README.md"
            )
        flow = InstalledAppFlow.from_client_secrets_file(str(client_path), scopes)
        # prompt=consent so adding Gmail scopes always yields a fresh refresh_token
        creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")
        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(creds.to_json(), encoding="utf-8")
        return creds

    def _load_creds(self, scopes: list[str], *, interactive: bool = False):
        try:
            mode = self._detect_mode()
        except GoogleNotConfigured:
            raise
        try:
            if mode == "oauth":
                return self._load_oauth(scopes, interactive=interactive)
            return self._load_service_account(scopes)
        except ImportError as e:
            raise RuntimeError(
                "Install Google deps: pip install -r scripts/integrations/requirements-google.txt"
            ) from e

    def authorize_interactive(
        self,
        *,
        readonly: bool = True,
        gmail: bool = False,
        sheets: bool = False,
        sheets_readonly: bool = False,
        scopes: Optional[list[str]] = None,
        preserve_existing: bool = True,
    ) -> dict[str, Any]:
        """Run browser OAuth and persist token (user credentials).

        By default unions already-granted scopes into the request so a narrower
        `google auth` (Drive-only) cannot wipe Sheets/Gmail. If the token already
        satisfies the need, skips the browser entirely.
        """
        use_scopes = list(
            scopes
            or oauth_scopes(
                drive_rw=not readonly or sheets,
                gmail=gmail,
                sheets=sheets,
                sheets_readonly=sheets_readonly and not sheets,
            )
        )
        self.auth_mode = "oauth"
        # Load granted scopes WITHOUT overriding — otherwise google-auth pretends
        # the token already has new scopes and refresh fails with invalid_scope.
        token_path = _resolve_path(self.oauth_token_path)
        have: set[str] = set()
        if token_path.exists():
            try:
                from google.oauth2.credentials import Credentials

                existing = Credentials.from_authorized_user_file(str(token_path))
                have = set(existing.scopes or [])
            except Exception:  # noqa: BLE001
                token_path.unlink(missing_ok=True)
                have = set()

        if preserve_existing and have:
            use_scopes = _canonicalize_scopes(list(use_scopes) + list(have))

        need = set(use_scopes)
        if have and _scopes_satisfied(have, need):
            creds = self._load_oauth(use_scopes, interactive=False)
            self._creds = creds
            self._drive = None
            self._gmail = None
            self._sheets = None
            email = None
            try:
                info = self.ping()
                email = (info.get("user") or {}).get("emailAddress")
            except Exception:  # noqa: BLE001
                pass
            return {
                "auth_mode": "oauth",
                "token_path": str(token_path),
                "email": email,
                "scopes": list(have) or use_scopes,
                "gmail": gmail or any("gmail" in s for s in have),
                "sheets": sheets
                or sheets_readonly
                or any("spreadsheets" in s for s in have),
                "reused_existing": True,
            }

        if token_path.exists():
            token_path.unlink(missing_ok=True)

        use_scopes = _canonicalize_scopes(use_scopes)
        creds = self._load_oauth(use_scopes, interactive=True)
        self._creds = creds
        self._drive = None
        self._gmail = None
        self._sheets = None
        email = None
        try:
            info = self.ping()
            email = (info.get("user") or {}).get("emailAddress")
        except Exception:  # noqa: BLE001
            pass
        return {
            "auth_mode": "oauth",
            "token_path": str(token_path),
            "email": email,
            "scopes": use_scopes,
            "gmail": gmail or any("gmail" in s for s in use_scopes),
            "sheets": sheets
            or sheets_readonly
            or any("spreadsheets" in s for s in use_scopes),
        }

    def _drive_service(self, *, interactive: bool = False, rw: bool = False):
        # Rebuild when RW needed after a readonly-cached service.
        if self._drive is not None and not rw:
            return self._drive
        from googleapiclient.discovery import build

        if rw or self._detect_mode() == "service_account":
            scopes = oauth_scopes(drive_rw=True, sheets=True)
            self._drive = None  # force rebuild with RW creds
        else:
            scopes = DRIVE_SCOPES
        self._creds = self._load_creds(scopes, interactive=interactive)
        self._drive = build("drive", "v3", credentials=self._creds, cache_discovery=False)
        return self._drive

    def ping(self) -> dict[str, Any]:
        """Verify credentials; list a few files in the configured folder if set."""
        drive = self._drive_service()
        about = drive.about().get(fields="user,storageQuota").execute()
        result: dict[str, Any] = {
            "auth_mode": self._detect_mode(),
            "user": about.get("user"),
            "folder_id": self.folder_id or None,
        }
        if self.folder_id:
            files = (
                drive.files()
                .list(
                    q=f"'{self.folder_id}' in parents and trashed=false",
                    pageSize=10,
                    fields="files(id,name,mimeType,modifiedTime)",
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True,
                )
                .execute()
            )
            result["sample_files"] = files.get("files") or []
        return result

    def list_folder(self, folder_id: Optional[str] = None, *, page_size: int = 50) -> list[dict]:
        folder_id = folder_id or self.folder_id
        if not folder_id:
            raise GoogleNotConfigured(
                "Pass --folder-id, --dir KEY, or set GOOGLE_DRIVE_FOLDER_ID / google-directories.json"
            )
        drive = self._drive_service()
        files: list[dict] = []
        token = None
        while True:
            resp = (
                drive.files()
                .list(
                    q=f"'{folder_id}' in parents and trashed=false",
                    pageSize=min(page_size, 100),
                    pageToken=token,
                    fields="nextPageToken,files(id,name,mimeType,modifiedTime,webViewLink)",
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True,
                )
                .execute()
            )
            files.extend(resp.get("files") or [])
            token = resp.get("nextPageToken")
            if not token or len(files) >= page_size:
                break
        return files[:page_size]

    def export_google_doc(self, file_id: str, *, mime: str = "text/plain") -> bytes:
        """Export a Google Doc (Docs mime) via Drive export."""
        drive = self._drive_service()
        return (
            drive.files()
            .export(fileId=file_id, mimeType=mime)
            .execute()
        )

    def _gmail_service(self, *, interactive: bool = False):
        if self._gmail is not None:
            return self._gmail
        from googleapiclient.discovery import build

        # Prefer compose + existing drive scopes so one token covers Drive + Gmail
        scopes = oauth_scopes(drive_rw=False, gmail=True)
        self._creds = self._load_creds(scopes, interactive=interactive)
        self._gmail = build("gmail", "v1", credentials=self._creds, cache_discovery=False)
        return self._gmail

    def get_gmail_send_as(
        self,
        *,
        send_as_email: Optional[str] = None,
    ) -> dict[str, Any]:
        """Return the chosen sendAs alias (default/primary) including HTML signature.

        Requires gmail.settings.basic. API drafts do not auto-append this signature —
        callers must attach it to the message body when desired.
        """
        gmail = self._gmail_service()
        if send_as_email:
            return (
                gmail.users()
                .settings()
                .sendAs()
                .get(userId="me", sendAsEmail=send_as_email)
                .execute()
            )
        listed = (
            gmail.users().settings().sendAs().list(userId="me").execute().get("sendAs")
            or []
        )
        if not listed:
            raise GoogleNotConfigured("No Gmail sendAs aliases found for this account")
        for prefer in ("isDefault", "isPrimary"):
            for row in listed:
                if row.get(prefer):
                    return row
        return listed[0]

    def get_gmail_signature(
        self,
        *,
        send_as_email: Optional[str] = None,
    ) -> dict[str, Any]:
        """Fetch HTML signature from Gmail Settings for the sendAs alias."""
        alias = self.get_gmail_send_as(send_as_email=send_as_email)
        sig = (alias.get("signature") or "").strip()
        return {
            "sendAsEmail": alias.get("sendAsEmail"),
            "displayName": alias.get("displayName"),
            "isDefault": bool(alias.get("isDefault")),
            "isPrimary": bool(alias.get("isPrimary")),
            "signature_html": sig,
            "signature_chars": len(sig),
            "has_signature": bool(sig),
        }

    def create_gmail_draft(
        self,
        *,
        to: list[str],
        subject: str,
        body: str,
        cc: Optional[list[str]] = None,
        bcc: Optional[list[str]] = None,
        html_body: Optional[str] = None,
        append_signature: bool = True,
        send_as_email: Optional[str] = None,
    ) -> dict[str, Any]:
        """Create a Gmail draft (does not send).

        Requires gmail.compose. When append_signature=True (default), fetches the
        account HTML signature (gmail.settings.basic) and builds multipart/alternative
        so styled footers render in Gmail.
        """
        import base64
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        from .gmail_draft import build_email_bodies

        if not to:
            raise ValueError("create_gmail_draft: `to` is required")

        signature_html = ""
        signature_meta: dict[str, Any] = {"appended": False}
        if append_signature:
            try:
                sig_info = self.get_gmail_signature(send_as_email=send_as_email)
                signature_html = sig_info.get("signature_html") or ""
                signature_meta = {
                    "appended": bool(signature_html),
                    "sendAsEmail": sig_info.get("sendAsEmail"),
                    "signature_chars": sig_info.get("signature_chars", 0),
                }
            except GoogleNotConfigured:
                raise
            except Exception as e:  # noqa: BLE001
                raise GoogleNotConfigured(
                    "Cannot read Gmail signature. Re-run: "
                    "python3 scripts/integrations/cli.py google auth --gmail "
                    f"({e})"
                ) from e

        plain, html = build_email_bodies(
            body or "",
            signature_html=signature_html if append_signature else "",
            html_override=html_body,
        )

        if html:
            message = MIMEMultipart("alternative")
            message.attach(MIMEText(plain, "plain", "utf-8"))
            message.attach(MIMEText(html, "html", "utf-8"))
        else:
            message = MIMEText(plain, _charset="utf-8")

        message["To"] = ", ".join(to)
        if cc:
            message["Cc"] = ", ".join(cc)
        if bcc:
            message["Bcc"] = ", ".join(bcc)
        message["Subject"] = subject
        if send_as_email:
            message["From"] = send_as_email

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")
        gmail = self._gmail_service()
        draft = (
            gmail.users()
            .drafts()
            .create(userId="me", body={"message": {"raw": raw}})
            .execute()
        )
        msg = draft.get("message") or {}
        return {
            "id": draft.get("id"),
            "message_id": msg.get("id"),
            "thread_id": msg.get("threadId"),
            "to": to,
            "cc": cc or [],
            "subject": subject,
            "body_chars": len(plain),
            "html": bool(html),
            "signature": signature_meta,
        }

    def get_file_meta(self, file_id: str) -> dict:
        drive = self._drive_service(rw=True)
        return (
            drive.files()
            .get(
                fileId=file_id,
                fields="id,name,mimeType,modifiedTime,webViewLink,parents,shortcutDetails",
                supportsAllDrives=True,
            )
            .execute()
        )

    def _sheets_service(self, *, interactive: bool = False, readonly: bool = False):
        if self._sheets is not None:
            return self._sheets
        from googleapiclient.discovery import build

        if readonly:
            scopes = oauth_scopes(drive_rw=False, sheets_readonly=True)
        else:
            scopes = oauth_scopes(drive_rw=True, sheets=True)
        self._creds = self._load_creds(scopes, interactive=interactive)
        self._sheets = build("sheets", "v4", credentials=self._creds, cache_discovery=False)
        # Drive may need same RW creds for create-in-folder
        self._drive = None
        return self._sheets

    def list_sheet_titles(self, spreadsheet_id: str) -> list[str]:
        sheets = self._sheets_service(readonly=True)
        meta = (
            sheets.spreadsheets()
            .get(spreadsheetId=spreadsheet_id, fields="sheets.properties.title")
            .execute()
        )
        return [
            (s.get("properties") or {}).get("title") or ""
            for s in (meta.get("sheets") or [])
        ]

    def add_sheet(self, spreadsheet_id: str, title: str) -> int:
        """Add a tab; return sheetId."""
        sheets = self._sheets_service()
        resp = (
            sheets.spreadsheets()
            .batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={"requests": [{"addSheet": {"properties": {"title": title}}}]},
            )
            .execute()
        )
        replies = resp.get("replies") or []
        props = ((replies[0].get("addSheet") or {}).get("properties") or {}) if replies else {}
        return int(props.get("sheetId") or 0)

    def get_sheet_id(self, spreadsheet_id: str, title: str) -> int:
        """Resolve sheetId by tab title (strip match, like list_sheet_titles consumers)."""
        sheets = self._sheets_service(readonly=True)
        meta = (
            sheets.spreadsheets()
            .get(
                spreadsheetId=spreadsheet_id,
                fields="sheets.properties(sheetId,title)",
            )
            .execute()
        )
        want = title.strip()
        for s in meta.get("sheets") or []:
            props = s.get("properties") or {}
            if (props.get("title") or "").strip() == want:
                return int(props["sheetId"])
        raise KeyError(f"Sheet tab not found: {title!r}")

    def batch_update_spreadsheet(
        self,
        spreadsheet_id: str,
        requests: list[dict[str, Any]],
    ) -> dict:
        """Sheets spreadsheets.batchUpdate (formatting, grid, etc.)."""
        if not requests:
            return {}
        sheets = self._sheets_service()
        return (
            sheets.spreadsheets()
            .batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={"requests": requests},
            )
            .execute()
        )

    def write_sheet_values(
        self,
        spreadsheet_id: str,
        range_a1: str,
        values: list[list[Any]],
        *,
        value_input_option: str = "USER_ENTERED",
    ) -> dict:
        sheets = self._sheets_service()
        return (
            sheets.spreadsheets()
            .values()
            .update(
                spreadsheetId=spreadsheet_id,
                range=range_a1,
                valueInputOption=value_input_option,
                body={"values": values},
            )
            .execute()
        )

    def read_sheet_values(self, spreadsheet_id: str, range_a1: str) -> list[list[Any]]:
        sheets = self._sheets_service(readonly=True)
        resp = (
            sheets.spreadsheets()
            .values()
            .get(spreadsheetId=spreadsheet_id, range=range_a1)
            .execute()
        )
        return resp.get("values") or []

    def clear_sheet_values(self, spreadsheet_id: str, range_a1: str) -> dict:
        sheets = self._sheets_service()
        return (
            sheets.spreadsheets()
            .values()
            .clear(spreadsheetId=spreadsheet_id, range=range_a1, body={})
            .execute()
        )

    def find_spreadsheets(
        self,
        folder_id: str,
        *,
        name_substr: str,
        recursive: bool = True,
        page_size: int = 200,
    ) -> list[dict]:
        """Find spreadsheets (resolve shortcuts) under folder whose name contains substr."""
        needle = (name_substr or "").lower()
        found: list[dict] = []
        queue = [folder_id]
        seen_folders: set[str] = set()
        while queue:
            current = queue.pop(0)
            if current in seen_folders:
                continue
            seen_folders.add(current)
            for f in self.list_folder(current, page_size=page_size):
                mime = f.get("mimeType") or ""
                name = f.get("name") or ""
                if mime == "application/vnd.google-apps.folder" and recursive:
                    queue.append(f["id"])
                    continue
                target_id = f["id"]
                target_mime = mime
                target_name = name
                if mime == "application/vnd.google-apps.shortcut":
                    meta = self.get_file_meta(f["id"])
                    details = meta.get("shortcutDetails") or {}
                    target_id = details.get("targetId") or target_id
                    target_mime = details.get("targetMimeType") or target_mime
                    try:
                        tmeta = self.get_file_meta(target_id)
                        target_name = tmeta.get("name") or target_name
                        target_mime = tmeta.get("mimeType") or target_mime
                        f = {**f, **tmeta, "id": target_id, "shortcut_id": meta.get("id")}
                    except Exception:  # noqa: BLE001
                        continue
                if target_mime != "application/vnd.google-apps.spreadsheet":
                    continue
                if needle and needle not in target_name.lower():
                    continue
                found.append(
                    {
                        "id": target_id,
                        "name": target_name,
                        "mimeType": target_mime,
                        "webViewLink": f.get("webViewLink"),
                        "modifiedTime": f.get("modifiedTime"),
                    }
                )
        return found

    def create_spreadsheet(
        self,
        *,
        title: str,
        parent_folder_id: str,
        sheet_titles: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """Create a Google Spreadsheet in a Drive folder."""
        sheets = self._sheets_service()
        drive = self._drive_service(rw=True)
        titles = sheet_titles or ["Sheet1"]
        body = {
            "properties": {"title": title},
            "sheets": [{"properties": {"title": t}} for t in titles],
        }
        created = sheets.spreadsheets().create(body=body, fields="spreadsheetId,spreadsheetUrl").execute()
        sid = created["spreadsheetId"]
        # Move into target folder (Sheets.create puts file in My Drive root)
        meta = (
            drive.files()
            .get(fileId=sid, fields="parents", supportsAllDrives=True)
            .execute()
        )
        prev_parents = ",".join(meta.get("parents") or [])
        update_kwargs: dict[str, Any] = {
            "fileId": sid,
            "addParents": parent_folder_id,
            "fields": "id,parents,webViewLink",
            "supportsAllDrives": True,
        }
        if prev_parents:
            update_kwargs["removeParents"] = prev_parents
        drive.files().update(**update_kwargs).execute()
        return created


def write_registry_index(
    files: list[dict],
    *,
    folder_id: str,
    dir_key: Optional[str] = None,
) -> Path:
    """Mirror Drive listing into registry/google/ (optionally per named directory)."""
    out = ROOT / "registry" / "google"
    if dir_key:
        out = out / dir_key
    out.mkdir(parents=True, exist_ok=True)
    index = {
        "dir_key": dir_key,
        "folder_id": folder_id,
        "files": files,
    }
    path = out / "index.json"
    path.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # also refresh aggregate index when syncing default/main
    if not dir_key or dir_key in ("main", "default"):
        agg = ROOT / "registry" / "google" / "index.json"
        if dir_key:
            # keep root index as pointer when using named dirs
            if not agg.exists() or dir_key == "main":
                agg.write_text(
                    json.dumps(
                        {"dir_key": dir_key, "folder_id": folder_id, "files": files},
                        ensure_ascii=False,
                        indent=2,
                    )
                    + "\n",
                    encoding="utf-8",
                )
        else:
            pass
    return path
