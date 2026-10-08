"""Load and validate integration credentials from repo-root `.env`."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[3]


def _expand(value: str, env: dict[str, str]) -> str:
    """Resolve simple `$VAR` / `${VAR}` references used in some .env files."""
    value = value.strip().strip('"').strip("'")
    if value.startswith("${") and value.endswith("}"):
        return env.get(value[2:-1], "").strip()
    if value.startswith("$") and len(value) > 1 and value[1:].replace("_", "").isalnum():
        return env.get(value[1:], "").strip()
    return value


def _repo_path(raw: str) -> Path:
    p = Path(raw).expanduser()
    return p if p.is_absolute() else ROOT / p


@dataclass(frozen=True)
class Config:
    atlassian_base_url: str
    atlassian_username: str
    atlassian_api_token: str
    confluence_space: str
    jira_project_key: str
    tempo_api_token: str
    tempo_base_url: str = "https://api.tempo.io/4"
    google_auth_mode: str = "auto"
    google_credentials_path: str = ""
    google_oauth_client_secrets: str = ""
    google_oauth_token_path: str = ""
    google_drive_folder_id: str = ""
    google_delegated_user: str = ""
    fireflies_api_key: str = ""
    fireflies_graphql_url: str = "https://api.fireflies.ai/graphql"
    fireflies_keyword: str = ""
    fireflies_keyword_scope: str = "title"
    fireflies_download_audio: bool = True
    fireflies_from_date: str = ""

    @property
    def confluence_ok(self) -> bool:
        return bool(self.atlassian_base_url and self.atlassian_username and self.atlassian_api_token)

    @property
    def jira_ok(self) -> bool:
        return self.confluence_ok and bool(self.jira_project_key)

    @property
    def tempo_ok(self) -> bool:
        return bool(self.tempo_api_token)

    @property
    def google_ok(self) -> bool:
        """True when SA JSON, OAuth client secrets, or saved OAuth token is available."""
        if self.google_credentials_path and _repo_path(self.google_credentials_path).exists():
            return True
        if self.google_oauth_client_secrets and _repo_path(self.google_oauth_client_secrets).exists():
            return True
        if self.google_oauth_token_path and _repo_path(self.google_oauth_token_path).exists():
            return True
        # Defaults under secrets/ even if .env not filled yet
        return any(
            (ROOT / "secrets" / name).exists()
            for name in (
                "google-sa.json",
                "google-oauth-client.json",
                "google-oauth-token.json",
            )
        )

    @property
    def fireflies_ok(self) -> bool:
        return bool(self.fireflies_api_key)


def load_config(*, require: tuple[str, ...] = ()) -> Config:
    load_dotenv(ROOT / ".env")
    raw = {k: v for k, v in os.environ.items()}

    def get(*keys: str, default: str = "") -> str:
        for k in keys:
            v = raw.get(k, "")
            if v:
                return _expand(v, raw)
        return default

    base = get("ATLASSIAN_BASE_URL", "JIRA_BASE_URL", "CONFLUENCE_BASE_URL")
    base = base.rstrip("/")
    if base.endswith("/wiki"):
        base = base[:-5]

    username = get("ATLASSIAN_USERNAME", "JIRA_USERNAME", "CONFLUENCE_USERNAME")
    token = get("ATLASSIAN_API_TOKEN", "JIRA_API_TOKEN", "CONFLUENCE_API_TOKEN")

    # Google — service account and/or user OAuth (see secrets/README.md)
    sa_path = get("GOOGLE_APPLICATION_CREDENTIALS", "GOOGLE_SERVICE_ACCOUNT_JSON")
    oauth_client = get("GOOGLE_OAUTH_CLIENT_SECRETS")
    oauth_token = get("GOOGLE_OAUTH_TOKEN", default="./secrets/google-oauth-token.json")

    if not oauth_client and (ROOT / "secrets" / "google-oauth-client.json").exists():
        oauth_client = "./secrets/google-oauth-client.json"
    if not sa_path and (ROOT / "secrets" / "google-sa.json").exists():
        sa_path = "./secrets/google-sa.json"

    cfg = Config(
        atlassian_base_url=base,
        atlassian_username=username,
        atlassian_api_token=token,
        confluence_space=get("CONFLUENCE_DEFAULT_SPACE", default="PMO"),
        jira_project_key=get("JIRA_PROJECT_KEY"),
        tempo_api_token=get("TEMPO_API_TOKEN"),
        tempo_base_url=get("TEMPO_BASE_URL", default="https://api.tempo.io/4").rstrip("/"),
        google_auth_mode=get("GOOGLE_AUTH_MODE", default="auto") or "auto",
        google_credentials_path=sa_path,
        google_oauth_client_secrets=oauth_client,
        google_oauth_token_path=oauth_token,
        google_drive_folder_id=get("GOOGLE_DRIVE_FOLDER_ID"),
        google_delegated_user=get("GOOGLE_DELEGATED_USER"),
        fireflies_api_key=get("FIREFLIES_API_KEY"),
        fireflies_graphql_url=get(
            "FIREFLIES_GRAPHQL_URL", default="https://api.fireflies.ai/graphql"
        ).rstrip("/")
        or "https://api.fireflies.ai/graphql",
        fireflies_keyword=get("FIREFLIES_KEYWORD"),
        fireflies_keyword_scope=get("FIREFLIES_KEYWORD_SCOPE", default="title") or "title",
        fireflies_download_audio=get("FIREFLIES_DOWNLOAD_AUDIO", default="1").lower()
        not in ("0", "false", "no", "off"),
        fireflies_from_date=get("FIREFLIES_FROM_DATE"),
    )

    checks = {
        "confluence": cfg.confluence_ok,
        "jira": cfg.jira_ok,
        "tempo": cfg.tempo_ok,
        "google": cfg.google_ok,
        "fireflies": cfg.fireflies_ok,
    }
    missing = [name for name in require if not checks.get(name)]
    if missing:
        hints = {
            "confluence": "CONFLUENCE_BASE_URL / CONFLUENCE_USERNAME / CONFLUENCE_API_TOKEN",
            "jira": "JIRA_PROJECT_KEY (+ Atlassian credentials; may reuse CONFLUENCE_*)",
            "tempo": "TEMPO_API_TOKEN (Tempo → Settings → API integration)",
            "google": "secrets/google-oauth-client.json + `cli.py google auth` "
            "OR GOOGLE_APPLICATION_CREDENTIALS (see secrets/README.md)",
            "fireflies": "FIREFLIES_API_KEY (Fireflies → Integrations → Fireflies API)",
        }
        lines = [f"Missing config for: {', '.join(missing)}"]
        for m in missing:
            lines.append(f"  - set {hints[m]}")
        sys.exit("\n".join(lines))
    return cfg
