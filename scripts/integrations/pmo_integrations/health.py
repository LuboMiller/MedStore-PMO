"""Health checks for mandatory integrations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .config import Config, load_config
from .confluence import ConfluenceClient
from .http import ApiError
from .jira import JiraClient
from .tempo import TempoClient


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str
    required: bool = True


def check_confluence(cfg: Config) -> CheckResult:
    if not cfg.confluence_ok:
        return CheckResult("confluence", False, "missing CONFLUENCE_* / Atlassian credentials")
    try:
        client = ConfluenceClient.from_config(cfg)
        user = client.ping()
        display = user.get("displayName") or user.get("publicName") or user.get("accountId") or "?"
        space = None
        try:
            space = client.get_space(cfg.confluence_space)
        except Exception as e:  # noqa: BLE001 — surface space miss separately
            return CheckResult(
                "confluence",
                True,
                f"auth ok as {display}; space '{cfg.confluence_space}' not resolved ({e})",
            )
        return CheckResult(
            "confluence",
            True,
            f"auth ok as {display}; space {space.get('key')} ({space.get('name')})",
        )
    except ApiError as e:
        return CheckResult("confluence", False, str(e))
    except Exception as e:  # noqa: BLE001
        return CheckResult("confluence", False, str(e))


def check_jira(cfg: Config) -> CheckResult:
    if not cfg.confluence_ok:
        return CheckResult("jira", False, "missing Atlassian credentials")
    if not cfg.jira_project_key:
        return CheckResult("jira", False, "missing JIRA_PROJECT_KEY")
    try:
        client = JiraClient.from_config(cfg)
        me = client.myself()
        display = me.get("displayName") or me.get("accountId") or "?"
        # light probe: one issue search
        n = 0
        for _ in client.project_issues():
            n += 1
            break
        return CheckResult(
            "jira",
            True,
            f"auth ok as {display}; project {cfg.jira_project_key} reachable"
            + (f" (sample issues: yes)" if n else " (no issues matched yet)"),
        )
    except ApiError as e:
        return CheckResult("jira", False, str(e))
    except Exception as e:  # noqa: BLE001
        return CheckResult("jira", False, str(e))


def check_tempo(cfg: Config) -> CheckResult:
    if not cfg.tempo_ok:
        return CheckResult(
            "tempo",
            False,
            "missing TEMPO_API_TOKEN (Tempo → Settings → API integration)",
        )
    try:
        client = TempoClient.from_config(cfg)
        client.ping()
        return CheckResult("tempo", True, f"auth ok; API {cfg.tempo_base_url}")
    except ApiError as e:
        return CheckResult("tempo", False, str(e))
    except Exception as e:  # noqa: BLE001
        return CheckResult("tempo", False, str(e))


def check_google(cfg: Config) -> CheckResult:
    """Optional until GOOGLE_* is configured — does not fail mandatory health."""
    if not cfg.google_ok:
        return CheckResult(
            "google",
            True,
            "skipped (add secrets/google-oauth-client.json + `google auth`, "
            "or GOOGLE_APPLICATION_CREDENTIALS — see secrets/README.md)",
            required=False,
        )
    try:
        from pathlib import Path

        from google.oauth2.credentials import Credentials

        from .google_workspace import (
            GoogleNotConfigured,
            GoogleWorkspaceClient,
            _scopes_satisfied,
        )

        client = GoogleWorkspaceClient.from_config(cfg)
        info = client.ping()
        user = (info.get("user") or {}).get("emailAddress") or "?"
        n = len(info.get("sample_files") or [])
        detail = f"auth ok as {user}"
        if cfg.google_drive_folder_id:
            detail += f"; folder {cfg.google_drive_folder_id} ({n} sample files)"

        # Warn when Drive works but Sheets hydrate will fail (common footgun).
        token_path = Path(cfg.google_oauth_token_path or "./secrets/google-oauth-token.json")
        if not token_path.is_absolute():
            from .google_workspace import ROOT

            token_path = ROOT / token_path
        if token_path.exists():
            have = set(Credentials.from_authorized_user_file(str(token_path)).scopes or [])
            need_sheets = {"https://www.googleapis.com/auth/spreadsheets.readonly"}
            if not _scopes_satisfied(have, need_sheets):
                detail += (
                    "; WARN missing Sheets scope — "
                    "`google auth` (or `--sheets`) before export-sheets"
                )
            else:
                detail += "; sheets ok"

        return CheckResult("google", True, detail, required=False)
    except GoogleNotConfigured as e:
        return CheckResult("google", False, str(e), required=False)
    except Exception as e:  # noqa: BLE001
        return CheckResult("google", False, str(e), required=False)


def check_fireflies(cfg: Config) -> CheckResult:
    """Optional until FIREFLIES_API_KEY is set — does not fail mandatory health."""
    if not cfg.fireflies_ok:
        return CheckResult(
            "fireflies",
            True,
            "skipped (add FIREFLIES_API_KEY — Fireflies → Integrations → Fireflies API)",
            required=False,
        )
    try:
        from .fireflies import FirefliesClient

        client = FirefliesClient.from_config(cfg)
        user = client.ping()
        name = user.get("name") or user.get("email") or user.get("user_id") or "?"
        n = user.get("num_transcripts")
        detail = f"auth ok as {name}"
        if n is not None:
            detail += f"; transcripts≈{n}"
        if cfg.fireflies_keyword:
            detail += f"; filter keyword={cfg.fireflies_keyword!r}"
        return CheckResult("fireflies", True, detail, required=False)
    except ApiError as e:
        return CheckResult("fireflies", False, str(e), required=False)
    except Exception as e:  # noqa: BLE001
        return CheckResult("fireflies", False, str(e), required=False)


def run_health(cfg: Optional[Config] = None) -> list[CheckResult]:
    cfg = cfg or load_config()
    return [
        check_confluence(cfg),
        check_jira(cfg),
        check_tempo(cfg),
        check_google(cfg),
        check_fireflies(cfg),
    ]
