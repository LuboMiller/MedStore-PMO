#!/usr/bin/env python3
"""Export Devlight PMO Confluence space to local markdown knowledge base.

Usage (from repo root):
  python3 scripts/confluence-export/export_pmo.py
  python3 scripts/confluence-export/export_pmo.py --space PMO
  # → knowledge/pmo-kb/
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import html2text
import requests
from dotenv import load_dotenv
import os
from requests.auth import HTTPBasicAuth

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = ROOT / "knowledge" / "pmo-kb"


def load_env() -> dict[str, str]:
    """Load Confluence credentials; fall back to ATLASSIAN_* (same as integrations CLI)."""
    load_dotenv(ROOT / ".env")

    def first(*keys: str) -> str:
        for k in keys:
            v = os.getenv(k, "").strip()
            if v:
                return v
        return ""

    # Prefer ATLASSIAN_* (same order as scripts/integrations config) so stale
    # CONFLUENCE_* placeholders in .env do not break KB export.
    vals = {
        "CONFLUENCE_BASE_URL": first(
            "ATLASSIAN_BASE_URL", "JIRA_BASE_URL", "CONFLUENCE_BASE_URL"
        ),
        "CONFLUENCE_USERNAME": first(
            "ATLASSIAN_USERNAME", "JIRA_USERNAME", "CONFLUENCE_USERNAME"
        ),
        "CONFLUENCE_API_TOKEN": first(
            "ATLASSIAN_API_TOKEN", "JIRA_API_TOKEN", "CONFLUENCE_API_TOKEN"
        ),
    }
    missing = [k for k, v in vals.items() if not v]
    if missing:
        sys.exit(f"Missing env keys: {', '.join(missing)} (or ATLASSIAN_* equivalents)")
    base = vals["CONFLUENCE_BASE_URL"].rstrip("/")
    if base.endswith("/wiki"):
        base = base[:-5]
    vals["CONFLUENCE_BASE_URL"] = base
    vals["CONFLUENCE_DEFAULT_SPACE"] = os.getenv("CONFLUENCE_DEFAULT_SPACE", "PMO").strip() or "PMO"
    return vals


def next_cursor(data: dict) -> str | None:
    nxt = data.get("_links", {}).get("next")
    if not nxt:
        return None
    cursors = parse_qs(urlsplit(nxt).query).get("cursor")
    return cursors[0] if cursors else None


def slugify(title: str) -> str:
    s = title.strip().lower()
    s = re.sub(r"[^\w\s\-а-яіїєґА-ЯІЇЄҐ·\.]+", "", s, flags=re.UNICODE)
    s = re.sub(r"[\s/·]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s[:80] or "page"


class Exporter:
    def __init__(self, base_url: str, username: str, api_token: str, out_dir: Path):
        self.base = base_url.rstrip("/")
        self.out = out_dir
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(username, api_token)
        self.session.headers.update({"Accept": "application/json"})
        self.h2t = html2text.HTML2Text()
        self.h2t.body_width = 0
        self.h2t.ignore_links = False
        self.h2t.ignore_images = False
        self.api_version = "v2"
        self.space_key = ""

    def _url(self, path: str) -> str:
        return f"{self.base}/wiki{path}"

    def resolve_space(self, space_key: str) -> dict:
        r = self.session.get(self._url("/api/v2/spaces"), params={"keys": space_key})
        if r.status_code == 404:
            # Some Confluence Cloud tenants expose the legacy content API but
            # return 404 for the v2 space endpoint. Keep export read-only and
            # transparently fall back to the supported v1 API.
            legacy = self.session.get(self._url(f"/rest/api/space/{space_key}"))
            legacy.raise_for_status()
            space = legacy.json()
            self.api_version = "v1"
            self.space_key = space.get("key", space_key)
            return space
        r.raise_for_status()
        results = r.json().get("results", [])
        if not results:
            # fallback: search by name fragment
            r = self.session.get(self._url("/api/v2/spaces"), params={"limit": 100})
            r.raise_for_status()
            for sp in r.json().get("results", []):
                if space_key.upper() in (sp.get("key", "").upper(), sp.get("name", "").upper()):
                    self.space_key = sp.get("key", space_key)
                    return sp
                if "project management office" in sp.get("name", "").lower():
                    self.space_key = sp.get("key", space_key)
                    return sp
            sys.exit(f"Space not found: {space_key}")
        self.space_key = results[0].get("key", space_key)
        return results[0]

    def list_pages(self, space_id: str) -> list[dict]:
        if self.api_version == "v1":
            pages: list[dict] = []
            start = 0
            while True:
                r = self.session.get(
                    self._url("/rest/api/content"),
                    params={
                        "spaceKey": self.space_key,
                        "type": "page",
                        "status": "current",
                        "limit": 50,
                        "start": start,
                        "expand": "ancestors",
                    },
                )
                r.raise_for_status()
                data = r.json()
                batch = data.get("results", [])
                for page in batch:
                    ancestors = page.get("ancestors", [])
                    page["parentId"] = ancestors[-1]["id"] if ancestors else None
                pages.extend(batch)
                if not data.get("_links", {}).get("next") or not batch:
                    break
                start += len(batch)
            return pages

        pages: list[dict] = []
        cursor = None
        while True:
            params = {"space-id": space_id, "limit": 50, "status": "current"}
            if cursor:
                params["cursor"] = cursor
            r = self.session.get(self._url("/api/v2/pages"), params=params)
            r.raise_for_status()
            data = r.json()
            pages.extend(data.get("results", []))
            cursor = next_cursor(data)
            if not cursor:
                break
        return pages

    def get_page_body(self, page_id: str) -> dict:
        if self.api_version == "v1":
            r = self.session.get(
                self._url(f"/rest/api/content/{page_id}"),
                params={"expand": "body.storage"},
            )
            r.raise_for_status()
            return r.json()

        r = self.session.get(
            self._url(f"/api/v2/pages/{page_id}"),
            params={"body-format": "storage"},
        )
        r.raise_for_status()
        return r.json()

    def storage_to_md(self, storage_html: str) -> str:
        if not storage_html:
            return ""
        return self.h2t.handle(storage_html).strip()

    def export(self, space_key: str) -> None:
        space = self.resolve_space(space_key)
        space_id = space["id"]
        space_key_real = space.get("key", space_key)
        print(f"Space: {space.get('name')} ({space_key_real}) id={space_id}")

        pages = self.list_pages(space_id)
        print(f"Pages: {len(pages)}")

        by_id = {p["id"]: p for p in pages}
        children: dict[str | None, list[dict]] = {}
        for p in pages:
            children.setdefault(p.get("parentId"), []).append(p)

        def path_for(page: dict) -> list[str]:
            parts = []
            cur = page
            seen = set()
            while cur and cur["id"] not in seen:
                seen.add(cur["id"])
                parts.append(slugify(cur["title"]))
                parent_id = cur.get("parentId")
                cur = by_id.get(parent_id) if parent_id else None
            return list(reversed(parts))

        self.out.mkdir(parents=True, exist_ok=True)
        index = []
        phase_dirs = [
            ("pre-sale", "01-pre-sale"),
            ("initiating", "02-initiating"),
            ("planning", "03-planning"),
            ("executing", "04-executing"),
            ("monitoring-controlling", "05-monitoring-controlling"),
            ("monitoring", "05-monitoring-controlling"),
            ("closing", "06-closing"),
            ("rules", "00-rules"),
            ("policies", "00-policies"),
            ("procedures", "00-procedures"),
        ]

        def detect_phase(parts: list[str]) -> tuple[str | None, list[str]]:
            """Skip root space page; map first matching phase segment."""
            rest = parts[1:] if parts and "project-management-office" in parts[0] else parts
            if not rest:
                return ("00-overview", ["index"])
            for i, seg in enumerate(rest):
                for key, folder in phase_dirs:
                    if key in seg:
                        return (folder, rest[i + 1 :] or ["index"])
            return ("99-other", rest)

        for i, page in enumerate(pages, 1):
            full = self.get_page_body(page["id"])
            title = full.get("title") or page["title"]
            body = (
                full.get("body", {})
                .get("storage", {})
                .get("value", "")
            )
            md = self.storage_to_md(body)
            parts = path_for(page)
            phase_key, remainder = detect_phase(parts)
            rel = Path(phase_key).joinpath(*remainder) if remainder else Path(phase_key) / "index"

            out_file = self.out / f"{rel}.md"
            out_file.parent.mkdir(parents=True, exist_ok=True)
            webui = full.get("_links", {}).get("webui", "")
            url = f"{self.base}/wiki{webui}" if webui else ""
            front = [
                "---",
                f'title: "{title.replace(chr(34), chr(39))}"',
                f"page_id: \"{page['id']}\"",
                f"space: \"{space_key_real}\"",
                f'parent_id: "{page.get("parentId") or ""}"',
                f'url: "{url}"',
                f'source: "confluence"',
                "---",
                "",
                f"# {title}",
                "",
            ]
            out_file.write_text("\n".join(front) + md + "\n", encoding="utf-8")
            index.append(
                {
                    "id": page["id"],
                    "title": title,
                    "parentId": page.get("parentId"),
                    "path": str(out_file.relative_to(self.out)),
                    "url": url,
                }
            )
            print(f"[{i}/{len(pages)}] {title} → {out_file.relative_to(ROOT)}")

        (self.out / "_index.json").write_text(
            json.dumps(
                {
                    "space_key": space_key_real,
                    "space_id": space_id,
                    "space_name": space.get("name"),
                    "page_count": len(index),
                    "pages": index,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        # human-readable TOC
        toc_lines = [
            f"# PMO Knowledge Base — {space.get('name')}",
            "",
            f"Source: `{space_key_real}` @ {self.base}",
            f"Pages: {len(index)}",
            "",
            "## Tree",
            "",
        ]

        def walk(parent_id: str | None, depth: int = 0) -> None:
            for child in sorted(children.get(parent_id, []), key=lambda x: x["title"]):
                meta = next(x for x in index if x["id"] == child["id"])
                indent = "  " * depth
                toc_lines.append(f"{indent}- [{child['title']}]({meta['path']})")
                walk(child["id"], depth + 1)

        walk(None)
        (self.out / "README.md").write_text("\n".join(toc_lines) + "\n", encoding="utf-8")
        print(f"\nDone. Index: {self.out / 'README.md'}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Export PMO Confluence space to markdown")
    parser.add_argument("--space", default=None, help="Space key (default from .env)")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Output directory")
    args = parser.parse_args()
    env = load_env()
    space = args.space or env["CONFLUENCE_DEFAULT_SPACE"]
    exporter = Exporter(
        env["CONFLUENCE_BASE_URL"],
        env["CONFLUENCE_USERNAME"],
        env["CONFLUENCE_API_TOKEN"],
        args.out,
    )
    exporter.export(space)


if __name__ == "__main__":
    main()
