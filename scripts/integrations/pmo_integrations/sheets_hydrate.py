"""Export Google Spreadsheet tabs to local hydrate (CSV + JSON) for daily PM sync.

Read-only. Used by morning automation after `google sync-pull` (folder metadata only).
"""

from __future__ import annotations

import csv
import json
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .google_workspace import GoogleWorkspaceClient

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "config" / "client-status-sheet.json"
EXAMPLE_PATH = ROOT / "config" / "client-status-sheet.example.json"
DEFAULT_OUT_ROOT = ROOT / "docs" / "_hydrate" / "google" / "sheets"

# Tabs that feed EWS / daily actions / burn signals (Devlight Client status sheet defaults)
DEFAULT_DAILY_TABS = [
    "Overview",
    "Scope Dashboard",
    "CSAT log",
    "СHANGE REQUESTS",
    "CHANGE REQUESTS",
    "Monthly Budget",
]


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _slug(title: str) -> str:
    s = title.strip().lower()
    s = s.replace(" ", "_")
    s = re.sub(r"[^\w\-]+", "", s, flags=re.UNICODE)
    return s or "sheet"


def load_client_status_config(path: Optional[Path] = None) -> dict[str, Any]:
    cfg_path = path or CONFIG_PATH
    if not cfg_path.is_file():
        raise FileNotFoundError(
            f"Missing {cfg_path} — copy from {EXAMPLE_PATH.name} and set spreadsheet_id"
        )
    return json.loads(cfg_path.read_text(encoding="utf-8"))


def resolve_tabs(
    available: list[str],
    *,
    wanted: Optional[list[str]] = None,
    all_tabs: bool = False,
) -> list[str]:
    if all_tabs:
        return [t for t in available if t]
    wanted = wanted or list(DEFAULT_DAILY_TABS)
    # Preserve order of wanted; match case-insensitive; skip missing
    avail_map = {t.casefold(): t for t in available if t}
    out: list[str] = []
    seen: set[str] = set()
    for w in wanted:
        hit = avail_map.get(w.casefold())
        if not hit:
            prefix = w.casefold()
            for key, actual in avail_map.items():
                if actual not in seen and key.startswith(prefix):
                    hit = actual
                    break
        if hit and hit not in seen:
            out.append(hit)
            seen.add(hit)
    return out


def _write_tab(out_dir: Path, title: str, values: list[list[Any]]) -> dict[str, str]:
    slug = _slug(title)
    csv_path = out_dir / f"{slug}.csv"
    json_path = out_dir / f"{slug}.json"
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        for row in values:
            writer.writerow(row)
    payload = {
        "title": title,
        "exported_at": _now(),
        "rows": len(values),
        "formatted": values,
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"csv": str(csv_path), "json": str(json_path)}


def export_spreadsheet_tabs(
    client: GoogleWorkspaceClient,
    spreadsheet_id: str,
    *,
    out_dir: Path,
    tabs: Optional[list[str]] = None,
    all_tabs: bool = False,
    label: str = "",
) -> dict[str, Any]:
    """Read selected tabs via Sheets API → CSV+JSON under out_dir."""
    out_dir.mkdir(parents=True, exist_ok=True)
    available = client.list_sheet_titles(spreadsheet_id)
    selected = resolve_tabs(available, wanted=tabs, all_tabs=all_tabs)
    exported: list[dict[str, Any]] = []
    errors: list[str] = []
    for title in selected:
        try:
            # Quote sheet name for A1 if needed
            range_a1 = f"'{title}'" if any(c in title for c in " '!") else title
            values = client.read_sheet_values(spreadsheet_id, range_a1)
            paths = _write_tab(out_dir, title, values)
            exported.append({"title": title, **paths, "rows": len(values)})
        except Exception as e:  # noqa: BLE001
            errors.append(f"{title}: {e}")

    meta = {
        "spreadsheet_id": spreadsheet_id,
        "label": label,
        "exported_at": _now(),
        "out_dir": str(out_dir),
        "available_tabs": available,
        "exported_tabs": [e["title"] for e in exported],
        "tabs": exported,
        "errors": errors,
    }
    (out_dir / "catalog.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return meta


def hydrate_client_status_sheet(
    client: GoogleWorkspaceClient,
    *,
    config_path: Optional[Path] = None,
    spreadsheet_id: Optional[str] = None,
    out_dir: Optional[Path] = None,
    as_of: Optional[date] = None,
    all_tabs: bool = False,
    tabs: Optional[list[str]] = None,
) -> dict[str, Any]:
    """Daily hydrate of Client Project status spreadsheet."""
    cfg: dict[str, Any] = {}
    if spreadsheet_id is None or out_dir is None or tabs is None:
        try:
            cfg = load_client_status_config(config_path)
        except FileNotFoundError:
            if not spreadsheet_id:
                raise

    sid = (spreadsheet_id or cfg.get("spreadsheet_id") or "").strip()
    if not sid:
        raise ValueError("spreadsheet_id required (CLI --file-id or config/client-status-sheet.json)")

    day = as_of or date.today()
    label = str(cfg.get("label") or "Client Project status report")
    wanted = tabs
    if wanted is None and not all_tabs:
        wanted = list(cfg.get("daily_tabs") or DEFAULT_DAILY_TABS)

    if out_dir is None:
        tmpl = str(cfg.get("out_dir_template") or "docs/_hydrate/google/sheets/client-status-live-{date}")
        rel = tmpl.format(date=day.isoformat())
        out_dir = ROOT / rel if not Path(rel).is_absolute() else Path(rel)

    return export_spreadsheet_tabs(
        client,
        sid,
        out_dir=out_dir,
        tabs=wanted,
        all_tabs=all_tabs,
        label=label,
    )
