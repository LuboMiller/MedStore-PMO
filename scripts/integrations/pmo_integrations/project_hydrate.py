"""Hydrate local PMO repo from existing Jira + Confluence project data.

Use when the delivery already lives in Atlassian and this repo should catch up
(partial CONTEXT, registry mirrors, suggested docs from page titles) — not only
greenfield bootstrap.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .confluence import ConfluenceClient
from .confluence_sync import pull_space
from .jira import JiraClient
from .jira_sync import pull_project

ROOT = Path(__file__).resolve().parents[3]
MAP_PATH = ROOT / "config" / "artifact-source-map.json"
HYDRATE_DIR = ROOT / "docs" / "_hydrate"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _load_map() -> dict:
    if not MAP_PATH.exists():
        return {"confluence_title_patterns": []}
    return json.loads(MAP_PATH.read_text(encoding="utf-8"))


def _match_local(title: str, patterns: list[dict]) -> Optional[dict]:
    for pat in patterns:
        if re.search(pat["match"], title or ""):
            return pat
    return None


def _status_counts(jira: JiraClient) -> dict[str, int]:
    return jira.status_counts(max_issues=500)

def _patch_context(
    *,
    project_name: str,
    jira_key: str,
    space_key: str,
    lead: str,
    dry_run: bool,
) -> list[str]:
    path = ROOT / "CONTEXT.md"
    if not path.exists():
        return ["CONTEXT.md missing — skipped"]
    text = path.read_text(encoding="utf-8")
    actions: list[str] = []

    replacements = [
        ("{{PROJECT_NAME}}", project_name),
        ("{{CLIENT}}", "{{CLIENT}}"),  # keep unless we know client
    ]
    # Only fill identification table cells that still look empty / templated
    if "{{PROJECT_NAME}}" in text and project_name:
        text2 = text.replace("{{PROJECT_NAME}}", project_name)
        if text2 != text:
            actions.append(f"CONTEXT PROJECT_NAME → {project_name}")
            text = text2

    # Append / refresh links section note
    marker = "<!-- hydrate:atlassian -->"
    block = (
        f"\n{marker}\n"
        f"- Jira: `{jira_key}`\n"
        f"- Confluence space: `{space_key}`\n"
        f"- Lead (Jira): {lead or '—'}\n"
        f"- Hydrated: {_now()}\n"
    )
    if marker in text:
        # replace existing hydrate block until next blank line cluster or EOF section
        text = re.sub(
            rf"{re.escape(marker)}[\s\S]*?(?=\n## |\Z)",
            block.strip() + "\n\n",
            text,
            count=1,
        )
        actions.append("CONTEXT hydrate block refreshed")
    else:
        # insert before session notes if present
        if "## 9. Нотатки сесії" in text:
            text = text.replace("## 9. Нотатки сесії", block + "\n## 9. Нотатки сесії")
        else:
            text = text.rstrip() + "\n" + block
        actions.append("CONTEXT hydrate block added")

    if dry_run:
        return [f"[dry-run] {a}" for a in actions]
    path.write_text(text, encoding="utf-8")
    return actions


def _seed_stub(local: str, *, title: str, source: str, page_id: str, force: bool, dry_run: bool) -> str:
    path = ROOT / local
    if local.endswith("/"):
        path = path / f"from-{page_id}.md"
    if path.exists() and not force:
        return f"skip existing {path.relative_to(ROOT)}"
    body = (
        f"# {title}\n\n"
        f"> Seeded by hydrate from {source}. Review and replace with skill output.\n\n"
        f"- Source page id: `{page_id}`\n"
        f"- Date: {_now()}\n"
    )
    if dry_run:
        return f"[dry-run] would write {path.relative_to(ROOT)}"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return f"seeded {path.relative_to(ROOT)}"


def hydrate_project(
    *,
    jira: JiraClient,
    confluence: ConfluenceClient,
    jira_key: str,
    space_key: str,
    sync_registries: bool = True,
    seed_docs: bool = True,
    update_context: bool = True,
    force: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Pull existing Atlassian project state into registries + local hints."""
    jira_key = jira_key.upper()
    space_key = space_key.upper()
    report: dict[str, Any] = {
        "date": _now(),
        "jira_key": jira_key,
        "space_key": space_key,
        "steps": [],
        "jira": {},
        "confluence": {},
        "mappings": [],
        "actions": [],
        "errors": [],
    }

    # ---- Jira ----
    try:
        jira.project_key = jira_key
        project = jira.get_project(jira_key)
        lead = ((project.get("lead") or {}).get("displayName")) or ""
        report["jira"] = {
            "key": project.get("key"),
            "name": project.get("name"),
            "id": project.get("id"),
            "lead": lead,
            "style": project.get("style"),
            "projectTypeKey": project.get("projectTypeKey"),
        }
        report["steps"].append("jira_project_ok")
        try:
            counts = _status_counts(jira)
            report["jira"]["status_counts"] = counts
            report["jira"]["issue_sample"] = sum(counts.values())
        except Exception as e:  # noqa: BLE001
            report["errors"].append(f"jira status counts: {e}")

        if sync_registries and not dry_run:
            pull_report = pull_project(jira, project_key=jira_key)
            report["jira"]["sync_pull"] = pull_report.as_dict()
            report["steps"].append("jira_registry_pulled")
        elif sync_registries:
            report["steps"].append("jira_registry_pull_skipped_dry_run")
    except Exception as e:  # noqa: BLE001
        report["errors"].append(f"jira: {e}")

    # ---- Confluence ----
    try:
        space = confluence.get_space(space_key)
        report["confluence"]["space"] = {
            "key": space.get("key"),
            "name": space.get("name"),
            "id": space.get("id"),
        }
        pages = confluence.list_pages_by_key(space_key)
        report["confluence"]["page_count"] = len(pages)
        report["confluence"]["titles"] = [p.get("title") for p in pages[:200]]
        report["steps"].append("confluence_space_ok")

        if sync_registries and not dry_run:
            pull_report = pull_space(confluence, space_key, export_md=True)
            report["confluence"]["sync_pull"] = {
                "pulled": pull_report.get("pulled"),
                "errors": pull_report.get("errors"),
                "markdown": pull_report.get("markdown"),
            }
            report["steps"].append("confluence_registry_pulled")
            if pull_report.get("markdown"):
                report["steps"].append("confluence_markdown_exported")
        elif sync_registries:
            report["steps"].append("confluence_registry_pull_skipped_dry_run")

        patterns = _load_map().get("confluence_title_patterns") or []
        for p in pages:
            title = p.get("title") or ""
            hit = _match_local(title, patterns)
            if not hit:
                continue
            mapping = {
                "title": title,
                "page_id": p.get("id"),
                "local": hit["local"],
                "skill": hit.get("skill"),
            }
            report["mappings"].append(mapping)
            if seed_docs:
                action = _seed_stub(
                    hit["local"],
                    title=title,
                    source=f"Confluence {space_key}",
                    page_id=str(p.get("id")),
                    force=force,
                    dry_run=dry_run,
                )
                report["actions"].append(action)
    except Exception as e:  # noqa: BLE001
        report["errors"].append(f"confluence: {e}")

    # ---- CONTEXT ----
    if update_context:
        name = (report.get("jira") or {}).get("name") or space_key
        lead = (report.get("jira") or {}).get("lead") or ""
        report["actions"].extend(
            _patch_context(
                project_name=name,
                jira_key=jira_key,
                space_key=space_key,
                lead=lead,
                dry_run=dry_run,
            )
        )

    # ---- Write report ----
    HYDRATE_DIR.mkdir(parents=True, exist_ok=True)
    json_path = HYDRATE_DIR / "last-run.json"
    md_path = HYDRATE_DIR / "FROM_SYSTEMS.md"
    md = _render_md(report)
    if not dry_run:
        json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        md_path.write_text(md, encoding="utf-8")
        report["report_paths"] = {
            "json": str(json_path.relative_to(ROOT)),
            "md": str(md_path.relative_to(ROOT)),
        }
    else:
        report["report_preview"] = md[:2000]
    return report


def _render_md(report: dict) -> str:
    j = report.get("jira") or {}
    c = report.get("confluence") or {}
    lines = [
        f"# Hydrate з існуючих систем — {report.get('date')}",
        "",
        "Локальний репо частково заповнено з live Jira / Confluence.",
        "Це **не** замінює skills: charter/EWS тощо все одно проходять через відповідні `pmo-*`.",
        "",
        "## Джерела",
        "",
        f"- Jira: `{report.get('jira_key')}` — {j.get('name') or '—'} (lead: {j.get('lead') or '—'})",
        f"- Confluence: `{report.get('space_key')}` — {(c.get('space') or {}).get('name') or '—'}",
        f"- Сторінок у space: {c.get('page_count', '—')}",
        "",
        "## Jira status counts (sample)",
        "",
    ]
    counts = j.get("status_counts") or {}
    if counts:
        lines.append("| Status | Count |")
        lines.append("|---|---|")
        for k, v in sorted(counts.items(), key=lambda x: (-x[1], x[0])):
            lines.append(f"| {k} | {v} |")
    else:
        lines.append("_немає даних_")
    lines += ["", "## Mapped Confluence → local docs", ""]
    if report.get("mappings"):
        lines.append("| Confluence page | Local | Suggested skill |")
        lines.append("|---|---|---|")
        for m in report["mappings"]:
            lines.append(f"| {m['title']} | `{m['local']}` | `{m.get('skill') or '—'}` |")
    else:
        lines.append("_немає збігів за `config/artifact-source-map.json`_")
    lines += ["", "## Actions", ""]
    for a in report.get("actions") or []:
        lines.append(f"- {a}")
    if report.get("errors"):
        lines += ["", "## Errors", ""]
        for e in report["errors"]:
            lines.append(f"- {e}")
    lines += [
        "",
        "## Next",
        "",
        "1. Переглянути `CONTEXT.md` і дозаповнити клієнта / цілі вручну.",
        "2. Для mapped артефактів — запустити відповідний skill (не лишати seed-stub).",
        "3. За потреби: Google Drive folder → `cli.py google …` (wave 4).",
        "",
    ]
    return "\n".join(lines)
