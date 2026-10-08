"""Bidirectional Confluence ↔ local registry sync.

Layout:
  registry/confluence/
    index.json
    spaces/{KEY}/
      space.json
      pages/{page_id}.json     # metadata + storage body + hashes
      by-title/{slug}.json     # symlink-like pointer {id, title}
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .confluence import ConfluenceClient, markdown_to_storage

ROOT = Path(__file__).resolve().parents[3]
REGISTRY = ROOT / "registry" / "confluence"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slug(title: str) -> str:
    s = title.strip().lower()
    s = re.sub(r"[^\w\s\-а-яіїєґ]+", "", s, flags=re.UNICODE)
    s = re.sub(r"[\s/]+", "-", s)
    return (s[:80] or "page").strip("-")


def _hash(value: str) -> str:
    return hashlib.sha256((value or "").encode("utf-8")).hexdigest()[:16]


class ConfluenceRegistry:
    def __init__(self, space_key: str, root: Path = REGISTRY):
        self.space_key = space_key.upper()
        self.root = root
        self.space_dir = root / "spaces" / self.space_key
        self.pages_dir = self.space_dir / "pages"
        self.by_title_dir = self.space_dir / "by-title"

    def ensure(self) -> None:
        self.pages_dir.mkdir(parents=True, exist_ok=True)
        self.by_title_dir.mkdir(parents=True, exist_ok=True)

    def page_path(self, page_id: str) -> Path:
        return self.pages_dir / f"{page_id}.json"

    def load_page(self, page_id: str) -> Optional[dict]:
        path = self.page_path(page_id)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def find_by_title(self, title: str) -> Optional[dict]:
        pointer = self.by_title_dir / f"{_slug(title)}.json"
        if not pointer.exists():
            return None
        meta = json.loads(pointer.read_text(encoding="utf-8"))
        return self.load_page(str(meta["id"]))

    def save_page(self, record: dict, *, dirty: bool = False) -> Path:
        self.ensure()
        body = record.get("body_storage") or ""
        record = {
            **record,
            "dirty": dirty,
            "content_hash": _hash(body),
            "local_updated": _now(),
        }
        path = self.page_path(str(record["id"]))
        path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        pointer = {
            "id": record["id"],
            "title": record.get("title"),
            "path": f"pages/{record['id']}.json",
        }
        (self.by_title_dir / f"{_slug(record.get('title') or record['id'])}.json").write_text(
            json.dumps(pointer, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return path

    def list_page_ids(self) -> list[str]:
        if not self.pages_dir.exists():
            return []
        return sorted(p.stem for p in self.pages_dir.glob("*.json"))

    def write_index(self, meta: dict) -> None:
        self.ensure()
        index_path = self.root / "index.json"
        index: dict[str, Any] = {}
        if index_path.exists():
            index = json.loads(index_path.read_text(encoding="utf-8"))
        spaces = index.setdefault("spaces", {})
        spaces[self.space_key] = {
            **meta,
            "page_count": len(self.list_page_ids()),
            "updated_at": _now(),
        }
        index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _normalize_page(page: dict, space_key: str) -> dict:
    body = (
        page.get("body", {}).get("storage", {}).get("value")
        if isinstance(page.get("body"), dict)
        else ""
    )
    version = (page.get("version") or {}).get("number")
    return {
        "id": page.get("id"),
        "title": page.get("title"),
        "space_key": space_key.upper(),
        "parent_id": page.get("parentId"),
        "status": page.get("status"),
        "version": version,
        "body_storage": body or "",
        "webui": (page.get("_links") or {}).get("webui"),
    }


def pull_space(
    client: ConfluenceClient,
    space_key: str,
    *,
    export_md: bool = True,
    md_out_root: Optional[Path] = None,
) -> dict:
    reg = ConfluenceRegistry(space_key)
    reg.ensure()
    space = client.get_space(space_key)
    (reg.space_dir / "space.json").write_text(
        json.dumps(space, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )

    pulled = 0
    skipped = 0
    conflicts = 0
    errors: list[str] = []

    for stub in client.list_pages(str(space["id"])):
        try:
            full = client.get_page(stub["id"])
            norm = _normalize_page(full, space_key)
            # v2 list stubs may omit parentId — prefer full page
            if not norm.get("parent_id") and stub.get("parentId"):
                norm["parent_id"] = stub.get("parentId")
            local = reg.load_page(str(norm["id"]))
            if local and local.get("dirty"):
                if local.get("version") != norm.get("version"):
                    conflicts += 1
                    errors.append(f"conflict {norm['id']} ({norm['title']}): dirty local + remote version change")
                else:
                    skipped += 1
                continue
            reg.save_page(norm, dirty=False)
            pulled += 1
        except Exception as e:  # noqa: BLE001
            errors.append(f"{stub.get('id')}: {e}")

    reg.write_index({"last_pull": _now()})
    report: dict[str, Any] = {
        "pulled": pulled,
        "skipped": skipped,
        "conflicts": conflicts,
        "errors": errors,
    }

    if export_md:
        try:
            from .confluence_md_export import DEFAULT_OUT_ROOT, export_space_markdown

            md = export_space_markdown(
                space_key,
                out_root=md_out_root or DEFAULT_OUT_ROOT,
                client=client,
                sync_registry_first=False,
                base_url=client.base_url,
            )
            report["markdown"] = md
            reg.write_index({"last_pull": _now(), "last_md_export": _now(), "md_out": md.get("out")})
        except Exception as e:  # noqa: BLE001
            report["markdown_error"] = str(e)
            errors.append(f"markdown export: {e}")

    return report


def push_space(client: ConfluenceClient, space_key: str, *, dry_run: bool = False) -> dict:
    reg = ConfluenceRegistry(space_key)
    pushed = 0
    skipped = 0
    conflicts = 0
    errors: list[str] = []

    for page_id in reg.list_page_ids():
        local = reg.load_page(page_id)
        if not local or not local.get("dirty"):
            skipped += 1
            continue
        try:
            remote = client.get_page(page_id)
            remote_version = (remote.get("version") or {}).get("number")
            if local.get("version") is not None and remote_version != local.get("version"):
                conflicts += 1
                errors.append(f"conflict {page_id}: remote version advanced — pull first")
                continue
            if dry_run:
                pushed += 1
                continue
            updated = client.update_page(
                remote,
                title=local.get("title"),
                body_storage=local.get("body_storage"),
                parent_id=local.get("parent_id"),
            )
            reg.save_page(_normalize_page(client.get_page(updated["id"]), space_key), dirty=False)
            pushed += 1
        except Exception as e:  # noqa: BLE001
            errors.append(f"{page_id}: {e}")

    reg.write_index({"last_push": _now(), "dry_run": dry_run})
    return {
        "pushed": pushed,
        "skipped": skipped,
        "conflicts": conflicts,
        "errors": errors,
    }


def mark_dirty(
    space_key: str,
    *,
    page_id: Optional[str] = None,
    title: Optional[str] = None,
    body_md: Optional[str] = None,
    body_storage: Optional[str] = None,
    new_title: Optional[str] = None,
) -> dict:
    reg = ConfluenceRegistry(space_key)
    local = None
    if page_id:
        local = reg.load_page(page_id)
    elif title:
        local = reg.find_by_title(title)
    if not local:
        raise FileNotFoundError("Page not in registry — sync-pull first or create remotely")
    if new_title:
        local["title"] = new_title
    if body_storage is not None:
        local["body_storage"] = body_storage
    elif body_md is not None:
        local["body_storage"] = markdown_to_storage(body_md)
    reg.save_page(local, dirty=True)
    return local
