"""Export Confluence project space to nested markdown (preserve page hierarchy).

Output:
  knowledge/confluence-spaces/{SPACE}/
    README.md       # nested TOC
    _index.json
    {slug}/…        # folders mirror parent→child
    {slug}.md       # leaf pages
    {slug}/index.md # pages that have children
"""

from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .confluence import ConfluenceClient
from .confluence_sync import ConfluenceRegistry, pull_space

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUT_ROOT = ROOT / "knowledge" / "confluence-spaces"


def _slugify(title: str, *, max_len: int = 80) -> str:
    s = (title or "page").strip().lower()
    s = re.sub(r"[^\w\s\-а-яіїєґА-ЯІЇЄҐ·\.]+", "", s, flags=re.UNICODE)
    s = re.sub(r"[\s/·|]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return (s or "page")[:max_len]


def _storage_to_md(storage_html: str) -> str:
    if not storage_html:
        return ""
    import html2text

    h2t = html2text.HTML2Text()
    h2t.body_width = 0
    h2t.ignore_links = False
    h2t.ignore_images = False
    return h2t.handle(storage_html).strip()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _unique_slug(base: str, used: set[str]) -> str:
    slug = base
    n = 2
    while slug in used:
        slug = f"{base}-{n}"
        n += 1
    used.add(slug)
    return slug


def _load_pages_from_registry(space_key: str) -> list[dict[str, Any]]:
    reg = ConfluenceRegistry(space_key)
    pages: list[dict[str, Any]] = []
    for page_id in reg.list_page_ids():
        rec = reg.load_page(page_id)
        if not rec:
            continue
        pages.append(
            {
                "id": str(rec["id"]),
                "title": rec.get("title") or page_id,
                "parent_id": str(rec["parent_id"]) if rec.get("parent_id") else None,
                "body_storage": rec.get("body_storage") or "",
                "webui": rec.get("webui") or "",
                "version": rec.get("version"),
            }
        )
    return pages


def export_space_markdown(
    space_key: str,
    *,
    out_root: Path = DEFAULT_OUT_ROOT,
    client: Optional[ConfluenceClient] = None,
    sync_registry_first: bool = False,
    clean: bool = True,
    base_url: str = "",
) -> dict[str, Any]:
    """Write hierarchical markdown mirror for a project Confluence space."""
    space_key = space_key.upper()
    out_dir = out_root / space_key

    if sync_registry_first:
        if client is None:
            raise ValueError("client required when sync_registry_first=True")
        pull_space(client, space_key, export_md=False)

    pages = _load_pages_from_registry(space_key)
    if not pages and client is not None:
        # Live fallback if registry empty
        pull_space(client, space_key, export_md=False)
        pages = _load_pages_from_registry(space_key)

    if not pages:
        raise FileNotFoundError(
            f"No Confluence pages in registry for {space_key} — run: "
            f"python3 scripts/integrations/cli.py confluence sync-pull --space {space_key}"
        )

    if clean and out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    by_id = {p["id"]: p for p in pages}
    children: dict[Optional[str], list[dict]] = {}
    for p in pages:
        children.setdefault(p.get("parent_id"), []).append(p)
    for kids in children.values():
        kids.sort(key=lambda x: (x.get("title") or "").lower())

    # Resolve slug path per page (unique among siblings)
    path_parts: dict[str, list[str]] = {}

    def assign(parent_id: Optional[str], prefix: list[str]) -> None:
        used: set[str] = set()
        for child in children.get(parent_id, []):
            slug = _unique_slug(_slugify(child["title"]), used)
            parts = prefix + [slug]
            path_parts[child["id"]] = parts
            assign(child["id"], parts)

    assign(None, [])

    has_children = {pid: bool(children.get(pid)) for pid in by_id}

    index_pages: list[dict[str, Any]] = []
    written = 0

    for page in pages:
        parts = path_parts.get(page["id"]) or [_slugify(page["title"])]
        if has_children.get(page["id"]):
            rel = Path(*parts) / "index.md"
        else:
            rel = Path(*parts).with_suffix(".md") if parts else Path("index.md")
            if not parts:
                rel = Path("index.md")

        out_file = out_dir / rel
        out_file.parent.mkdir(parents=True, exist_ok=True)

        md_body = _storage_to_md(page.get("body_storage") or "")
        webui = page.get("webui") or ""
        url = f"{base_url.rstrip('/')}/wiki{webui}" if base_url and webui else webui
        title = page["title"]
        front = [
            "---",
            f'title: "{title.replace(chr(34), chr(39))}"',
            f'page_id: "{page["id"]}"',
            f'space: "{space_key}"',
            f'parent_id: "{page.get("parent_id") or ""}"',
            f'url: "{url}"',
            f'source: "confluence"',
            f'exported_at: "{_now()}"',
            "---",
            "",
            f"# {title}",
            "",
        ]
        out_file.write_text("\n".join(front) + md_body + "\n", encoding="utf-8")
        written += 1
        index_pages.append(
            {
                "id": page["id"],
                "title": title,
                "parent_id": page.get("parent_id"),
                "path": str(rel).replace("\\", "/"),
                "url": url,
            }
        )

    (out_dir / "_index.json").write_text(
        json.dumps(
            {
                "space_key": space_key,
                "page_count": len(index_pages),
                "exported_at": _now(),
                "pages": index_pages,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    toc = [
        f"# Confluence space `{space_key}`",
        "",
        f"Hierarchical markdown mirror (parent → child folders).",
        f"Pages: **{len(index_pages)}** · exported `{_now()}`",
        "",
        "Regenerate:",
        "```bash",
        f"python3 scripts/integrations/cli.py confluence sync-pull --space {space_key}",
        f"# or: python3 scripts/integrations/cli.py confluence export-md --space {space_key}",
        "```",
        "",
        "## Tree",
        "",
    ]

    def walk(parent_id: Optional[str], depth: int = 0) -> None:
        for child in children.get(parent_id, []):
            meta = next(x for x in index_pages if x["id"] == child["id"])
            indent = "  " * depth
            toc.append(f"{indent}- [{child['title']}]({meta['path']})")
            walk(child["id"], depth + 1)

    walk(None)
    (out_dir / "README.md").write_text("\n".join(toc) + "\n", encoding="utf-8")

    # Root pointer README under confluence-spaces/
    out_root.mkdir(parents=True, exist_ok=True)
    root_readme = out_root / "README.md"
    root_readme.write_text(
        "# Project Confluence spaces (markdown mirrors)\n\n"
        "When a project has a Confluence space, pipeline pulls it here with "
        "**hierarchy preserved** as nested folders + `.md` files.\n\n"
        f"- [`{space_key}/`](./{space_key}/) — see `{space_key}/README.md`\n\n"
        "```bash\n"
        "python3 scripts/integrations/cli.py confluence sync-pull --space KEY\n"
        "```\n",
        encoding="utf-8",
    )

    return {
        "space": space_key,
        "out": str(out_dir.relative_to(ROOT)),
        "pages": written,
        "readme": str((out_dir / "README.md").relative_to(ROOT)),
    }
