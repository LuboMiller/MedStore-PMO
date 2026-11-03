"""Slack Web API client — User Token (as you) and/or Bot Token."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional

from .config import Config, ROOT
from .http import ApiError, bearer_session, get_json, post_json

API_BASE = "https://slack.com/api"


class SlackClient:
    def __init__(self, token: str, *, kind: str = "user", api_base: str = API_BASE):
        self.token = token
        self.kind = kind  # user | bot
        self.api_base = api_base.rstrip("/")
        self.session = bearer_session(token)

    @classmethod
    def from_config(cls, cfg: Config, *, prefer: Optional[str] = None) -> "SlackClient":
        if not cfg.slack_ok:
            raise SystemExit(
                "Missing Slack token: set SLACK_USER_TOKEN (xoxp-…, posts as you) "
                "and/or SLACK_BOT_TOKEN (xoxb-…)"
            )
        token, kind = cfg.slack_token(prefer=prefer)
        if not token:
            raise SystemExit("No usable Slack token for requested prefer mode")
        return cls(token, kind=kind, api_base=cfg.slack_api_base)

    def _url(self, method: str) -> str:
        return f"{self.api_base}/{method.lstrip('/')}"

    def api(self, method: str, *, payload: Optional[dict[str, Any]] = None, http: str = "post") -> dict[str, Any]:
        if http == "get":
            data = get_json(self.session, self._url(method), service="slack", params=payload or {})
        else:
            data = post_json(self.session, self._url(method), service="slack", payload=payload or {})
        if not data.get("ok"):
            err = data.get("error") or data
            raise ApiError("slack", 200, json.dumps({"ok": False, "error": err}, ensure_ascii=False))
        return data

    def ping(self) -> dict[str, Any]:
        data = self.api("auth.test")
        return {
            "ok": True,
            "auth_as": self.kind,
            "url": data.get("url"),
            "team": data.get("team"),
            "team_id": data.get("team_id"),
            "user": data.get("user"),
            "user_id": data.get("user_id"),
            "bot_id": data.get("bot_id"),
        }

    def list_channels(
        self,
        *,
        types: str = "public_channel,private_channel",
        limit: int = 200,
        exclude_archived: bool = True,
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        cursor: Optional[str] = None
        while True:
            params: dict[str, Any] = {
                "types": types,
                "limit": min(limit, 200),
                "exclude_archived": str(exclude_archived).lower(),
            }
            if cursor:
                params["cursor"] = cursor
            data = self.api("conversations.list", payload=params, http="get")
            for ch in data.get("channels") or []:
                rows.append(
                    {
                        "id": ch.get("id"),
                        "name": ch.get("name"),
                        "is_private": ch.get("is_private"),
                        "is_member": ch.get("is_member"),
                        "num_members": ch.get("num_members"),
                    }
                )
                if len(rows) >= limit:
                    return rows
            cursor = (data.get("response_metadata") or {}).get("next_cursor") or None
            if not cursor:
                break
        return rows

    def resolve_channel(self, channel: str) -> str:
        """Accept C… / G… id, #name, or bare name → channel id when possible."""
        raw = (channel or "").strip()
        if not raw:
            raise SystemExit("Slack channel is empty")
        if raw.startswith("C") or raw.startswith("G") or raw.startswith("D"):
            return raw
        name = raw[1:] if raw.startswith("#") else raw
        for ch in self.list_channels(limit=1000):
            if ch.get("name") == name:
                return str(ch["id"])
        # Let Slack API resolve #name for public channels the bot is in
        return raw if raw.startswith("#") else f"#{name}"

    def post_message(
        self,
        channel: str,
        text: str,
        *,
        mrkdwn: bool = True,
        thread_ts: Optional[str] = None,
        unfurl_links: bool = False,
    ) -> dict[str, Any]:
        channel_id = self.resolve_channel(channel)
        payload: dict[str, Any] = {
            "channel": channel_id,
            "text": text,
            "mrkdwn": mrkdwn,
            "unfurl_links": unfurl_links,
            "unfurl_media": False,
        }
        if thread_ts:
            payload["thread_ts"] = thread_ts
        data = self.api("chat.postMessage", payload=payload)
        return {
            "ok": True,
            "channel": data.get("channel"),
            "ts": data.get("ts"),
            "message": (data.get("message") or {}).get("text", "")[:200],
        }


def load_slack_project_config() -> dict[str, Any]:
    path = ROOT / "config" / "slack.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def extract_slack_body(path: Path) -> str:
    """Prefer fenced ```slack … ``` body; else whole file (strip YAML/MD chrome lightly)."""
    text = path.read_text(encoding="utf-8")
    m = re.search(r"```slack\s*\n(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip() + "\n"
    # Drop leading markdown title / blockquote notes
    lines = text.splitlines()
    out: list[str] = []
    started = False
    for line in lines:
        if not started:
            if line.startswith("#") or line.startswith(">") or not line.strip():
                continue
            started = True
        out.append(line)
    return "\n".join(out).strip() + "\n"
