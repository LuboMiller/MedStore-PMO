"""Bootstrap a project Confluence space from company template."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from .confluence import ConfluenceClient, markdown_to_storage

ROOT = Path(__file__).resolve().parents[3]
TEMPLATE_PATH = ROOT / "config" / "confluence-space-template.json"


def load_space_template() -> dict:
    return json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))


def _fmt(text: str, ctx: dict[str, str]) -> str:
    try:
        return text.format(**ctx)
    except KeyError:
        return text


def bootstrap_space(
    client: ConfluenceClient,
    *,
    space_key: str,
    space_name: str,
    create_space: bool = True,
    project_name: Optional[str] = None,
    jira_key: str = "",
    pm_name: str = "",
    dm_name: str = "",
    private: bool = False,
) -> dict[str, Any]:
    """Create space (optional) and ensure phase page tree exists (idempotent upsert)."""
    tpl = load_space_template()
    ctx = {
        "project_name": project_name or space_name,
        "jira_key": jira_key or "—",
        "pm_name": pm_name or "—",
        "dm_name": dm_name or "—",
    }
    result: dict[str, Any] = {"space_key": space_key.upper(), "pages": [], "steps": []}

    if create_space:
        try:
            client.get_space(space_key)
            result["steps"].append("space_existing")
        except RuntimeError:
            created = client.create_space(
                key=space_key,
                name=space_name,
                description=f"Devlight PMO delivery space for {ctx['project_name']}",
                private=private,
            )
            result["space"] = {"key": created.get("key"), "id": created.get("id")}
            result["steps"].append("space_created")
    else:
        result["space"] = client.get_space(space_key)
        result["steps"].append("space_existing")

    homepage_title = _fmt(tpl.get("homepage_title", "{project_name} — PMO"), ctx)
    homepage_body = markdown_to_storage(_fmt(tpl.get("homepage_body_md", ""), ctx))
    home = client.upsert_page(space_key.upper(), homepage_title, homepage_body)
    result["homepage"] = {"id": home.get("id"), "title": home.get("title")}
    result["pages"].append(home.get("title"))
    result["steps"].append("homepage_upserted")

    for node in tpl.get("tree") or []:
        parent = client.upsert_page(
            space_key.upper(),
            node["title"],
            markdown_to_storage(node.get("body_md", "")),
            parent_id=home.get("id"),
        )
        result["pages"].append(parent.get("title"))
        for child in node.get("children") or []:
            page = client.upsert_page(
                space_key.upper(),
                child["title"],
                markdown_to_storage(child.get("body_md", "")),
                parent_id=parent.get("id"),
            )
            result["pages"].append(page.get("title"))

    result["steps"].append("tree_upserted")
    result["page_count"] = len(result["pages"])
    return result
