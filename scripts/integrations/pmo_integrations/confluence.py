"""Confluence Cloud REST client — read + write (spaces, pages, upsert).

Space create: tries v1 `/rest/api/space` (widely available), falls back to v2.
Pages: Cloud API v2 create/update with storage body.
"""

from __future__ import annotations

from typing import Any, Iterator, Optional
from urllib.parse import parse_qs, urlsplit

from .config import Config
from .http import ApiError, basic_session, get_json, post_json, put_json


def _next_cursor(data: dict) -> Optional[str]:
    nxt = data.get("_links", {}).get("next")
    if not nxt:
        return None
    cursors = parse_qs(urlsplit(nxt).query).get("cursor")
    return cursors[0] if cursors else None


def markdown_to_storage(md: str) -> str:
    """Minimal markdown → Confluence storage XHTML (paragraphs + headings + lists)."""
    import html
    import re

    lines = (md or "").replace("\r\n", "\n").split("\n")
    out: list[str] = []
    in_ul = False

    def close_ul() -> None:
        nonlocal in_ul
        if in_ul:
            out.append("</ul>")
            in_ul = False

    for line in lines:
        if re.match(r"^#{1,3}\s+", line):
            close_ul()
            level = len(line) - len(line.lstrip("#"))
            level = min(level, 3)
            text = html.escape(line.lstrip("#").strip())
            out.append(f"<h{level}>{text}</h{level}>")
        elif re.match(r"^[-*]\s+", line):
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            text = html.escape(re.sub(r"^[-*]\s+", "", line))
            out.append(f"<li>{text}</li>")
        elif not line.strip():
            close_ul()
        else:
            close_ul()
            out.append(f"<p>{html.escape(line)}</p>")
    close_ul()
    return "\n".join(out) if out else "<p></p>"


class ConfluenceClient:
    def __init__(self, base_url: str, username: str, api_token: str):
        self.base_url = base_url.rstrip("/")
        self.session = basic_session(username, api_token)

    @classmethod
    def from_config(cls, cfg: Config) -> "ConfluenceClient":
        return cls(cfg.atlassian_base_url, cfg.atlassian_username, cfg.atlassian_api_token)

    def _url(self, path: str) -> str:
        return f"{self.base_url}/wiki{path}"

    def ping(self) -> dict:
        return get_json(self.session, self._url("/rest/api/user/current"), service="confluence")

    # ---- spaces ----

    def get_space(self, space_key: str) -> dict:
        data = get_json(
            self.session,
            self._url("/api/v2/spaces"),
            service="confluence",
            params={"keys": space_key},
        )
        results = data.get("results", [])
        if not results:
            raise RuntimeError(f"Confluence space not found: {space_key}")
        return results[0]

    def get_space_id(self, space_key: str) -> str:
        return str(self.get_space(space_key)["id"])

    def create_space(
        self,
        *,
        key: str,
        name: str,
        description: str = "",
        private: bool = False,
    ) -> dict:
        """Create a space. Prefer v1 (compatible); fall back to v2 on some tenants."""
        key = key.upper()
        # v1
        payload_v1: dict[str, Any] = {
            "key": key,
            "name": name,
            "description": {
                "plain": {"value": description or f"PMO space {name}", "representation": "plain"}
            },
        }
        path = "/rest/api/space/_private" if private else "/rest/api/space"
        try:
            return post_json(self.session, self._url(path), service="confluence", payload=payload_v1)
        except ApiError as e:
            if e.status not in (404, 405, 410):
                # try v2 anyway for RBAC tenants that reject v1 shape, or re-raise
                pass
            else:
                pass
        payload_v2 = {
            "key": key,
            "name": name,
            "description": {
                "value": description or f"PMO space {name}",
                "representation": "plain",
            },
        }
        return post_json(self.session, self._url("/api/v2/spaces"), service="confluence", payload=payload_v2)

    # ---- pages read ----

    def list_pages(self, space_id: str, *, limit: int = 50) -> Iterator[dict]:
        cursor = None
        while True:
            params: dict = {"space-id": space_id, "limit": limit, "status": "current"}
            if cursor:
                params["cursor"] = cursor
            data = get_json(
                self.session,
                self._url("/api/v2/pages"),
                service="confluence",
                params=params,
            )
            yield from data.get("results", [])
            cursor = _next_cursor(data)
            if not cursor:
                break

    def list_pages_by_key(self, space_key: str) -> list[dict]:
        return list(self.list_pages(self.get_space_id(space_key)))

    def get_page(self, page_id: str, *, body_format: str = "storage") -> dict:
        return get_json(
            self.session,
            self._url(f"/api/v2/pages/{page_id}"),
            service="confluence",
            params={"body-format": body_format},
        )

    def find_page_by_title(self, space_key: str, title: str) -> Optional[dict]:
        space_id = self.get_space_id(space_key)
        data = get_json(
            self.session,
            self._url("/api/v2/pages"),
            service="confluence",
            params={"space-id": space_id, "title": title, "body-format": "storage"},
        )
        results = data.get("results", [])
        return results[0] if results else None

    # ---- pages write ----

    def create_page(
        self,
        space_key: str,
        title: str,
        body_storage: str = "",
        *,
        parent_id: Optional[str] = None,
        parent_title: Optional[str] = None,
    ) -> dict:
        space_id = self.get_space_id(space_key)
        if parent_id is None and parent_title:
            parent = self.find_page_by_title(space_key, parent_title)
            if not parent:
                raise RuntimeError(f"Parent page not found: '{parent_title}' in {space_key}")
            parent_id = parent["id"]
        payload: dict[str, Any] = {
            "spaceId": space_id,
            "status": "current",
            "title": title,
            "body": {"representation": "storage", "value": body_storage or "<p></p>"},
        }
        if parent_id:
            payload["parentId"] = str(parent_id)
        return post_json(self.session, self._url("/api/v2/pages"), service="confluence", payload=payload)

    def update_page(
        self,
        page: dict,
        *,
        title: Optional[str] = None,
        body_storage: Optional[str] = None,
        parent_id: Optional[str] = None,
    ) -> dict:
        page_id = page["id"]
        # Ensure we have version + body
        if "version" not in page or (body_storage is None and "body" not in page):
            page = self.get_page(page_id)
        version_number = int(page["version"]["number"]) + 1
        payload: dict[str, Any] = {
            "id": page_id,
            "status": "current",
            "title": title if title is not None else page["title"],
            "version": {"number": version_number},
        }
        if body_storage is not None:
            payload["body"] = {"representation": "storage", "value": body_storage}
        else:
            body = page.get("body", {}).get("storage", {})
            payload["body"] = {
                "representation": "storage",
                "value": body.get("value") or "<p></p>",
            }
        if parent_id is not None:
            payload["parentId"] = str(parent_id)
        return put_json(
            self.session,
            self._url(f"/api/v2/pages/{page_id}"),
            service="confluence",
            payload=payload,
        )

    def upsert_page(
        self,
        space_key: str,
        title: str,
        body_storage: str,
        *,
        parent_id: Optional[str] = None,
        parent_title: Optional[str] = None,
    ) -> dict:
        """Create or update by title within a space."""
        existing = self.find_page_by_title(space_key, title)
        if existing:
            full = self.get_page(existing["id"])
            return self.update_page(
                full,
                title=title,
                body_storage=body_storage,
                parent_id=parent_id,
            )
        return self.create_page(
            space_key,
            title,
            body_storage,
            parent_id=parent_id,
            parent_title=parent_title,
        )
