"""Client contract register — deadlines + Drive folder linkage.

Config: ``config/contracts.json`` (from ``contracts.example.json``).
Drive mirror: google-directories key ``contracts`` (often commercial/Договір).
Outputs: ``docs/contracts/register.md`` + optional dated status snapshot.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "config" / "contracts.json"
EXAMPLE_PATH = ROOT / "config" / "contracts.example.json"
DOCS_DIR = ROOT / "docs" / "contracts"
REGISTER_PATH = DOCS_DIR / "register.md"


def _parse_date(value: Any) -> Optional[date]:
    if value is None or value == "":
        return None
    s = str(value).strip()
    if not s or s.startswith("YYYY"):
        return None
    return date.fromisoformat(s[:10])


def _days_until(target: Optional[date], *, as_of: date) -> Optional[int]:
    if target is None:
        return None
    return (target - as_of).days


def _traffic(
    days: Optional[int],
    *,
    status: str,
    warn_days: int,
    critical_days: int,
) -> str:
    st = (status or "").strip().lower()
    if st in {"done", "accepted", "closed", "expired", "terminated", "renewed"}:
        if st in {"expired", "terminated"}:
            return "🔴"
        return "🟢"
    if days is None:
        return "⚪"
    if days < 0:
        return "🔴"
    if days <= critical_days:
        return "🔴"
    if days <= warn_days:
        return "🟡"
    return "🟢"


@dataclass
class DeadlineRow:
    kind: str  # contract | stage
    contract_id: str
    item_id: str
    title: str
    status: str
    end_date: Optional[date]
    days_left: Optional[int]
    light: str
    drive_file_id: Optional[str] = None
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "contract_id": self.contract_id,
            "item_id": self.item_id,
            "title": self.title,
            "status": self.status,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "days_left": self.days_left,
            "light": self.light,
            "drive_file_id": self.drive_file_id,
            "notes": self.notes,
        }


def load_contracts_config(*, path: Optional[Path] = None, required: bool = True) -> dict[str, Any]:
    p = path or CONFIG_PATH
    if not p.exists():
        if required:
            raise FileNotFoundError(
                f"Missing {p}. Copy from {EXAMPLE_PATH.name} and fill contract/stage dates."
            )
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def ensure_example_copied() -> Path:
    if CONFIG_PATH.exists():
        return CONFIG_PATH
    if not EXAMPLE_PATH.exists():
        raise FileNotFoundError(f"Missing example: {EXAMPLE_PATH}")
    CONFIG_PATH.write_text(EXAMPLE_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    return CONFIG_PATH


def compute_deadline_rows(
    cfg: dict[str, Any],
    *,
    as_of: Optional[date] = None,
) -> list[DeadlineRow]:
    today = as_of or date.today()
    warn = int(cfg.get("warn_days") or 14)
    critical = int(cfg.get("critical_days") or 7)
    rows: list[DeadlineRow] = []

    for c in cfg.get("contracts") or []:
        cid = str(c.get("id") or "").strip() or "CTR-?"
        c_title = str(c.get("title") or cid).strip()
        c_status = str(c.get("status") or "active").strip()
        c_end = _parse_date(c.get("end_date"))
        c_days = _days_until(c_end, as_of=today)
        rows.append(
            DeadlineRow(
                kind="contract",
                contract_id=cid,
                item_id=cid,
                title=c_title,
                status=c_status,
                end_date=c_end,
                days_left=c_days,
                light=_traffic(c_days, status=c_status, warn_days=warn, critical_days=critical),
                drive_file_id=(str(c["drive_file_id"]) if c.get("drive_file_id") else None),
                notes=str(c.get("notes") or "").strip(),
            )
        )
        for s in c.get("stages") or []:
            sid = str(s.get("id") or "").strip() or "STG-?"
            s_title = str(s.get("title") or sid).strip()
            s_status = str(s.get("status") or "planned").strip()
            s_end = _parse_date(s.get("end_date"))
            s_days = _days_until(s_end, as_of=today)
            rows.append(
                DeadlineRow(
                    kind="stage",
                    contract_id=cid,
                    item_id=sid,
                    title=f"{c_title} · {s_title}",
                    status=s_status,
                    end_date=s_end,
                    days_left=s_days,
                    light=_traffic(
                        s_days, status=s_status, warn_days=warn, critical_days=critical
                    ),
                    notes=str(s.get("notes") or "").strip(),
                )
            )
    return rows


def actionable_rows(rows: list[DeadlineRow], *, warn_days: int) -> list[DeadlineRow]:
    """Open items overdue or within warn window (for daily PM / EWS)."""
    out: list[DeadlineRow] = []
    for r in rows:
        st = r.status.lower()
        if st in {"done", "accepted", "closed", "renewed"}:
            continue
        if r.days_left is None:
            continue
        if r.days_left < 0 or r.days_left <= warn_days:
            out.append(r)
    return out


def render_register_md(
    cfg: dict[str, Any],
    rows: list[DeadlineRow],
    *,
    as_of: date,
) -> str:
    warn = int(cfg.get("warn_days") or 14)
    critical = int(cfg.get("critical_days") or 7)
    dir_key = str(cfg.get("dir_key") or "contracts")
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    lines = [
        "# Contract register",
        "",
        "> Локальний SoT дедлайнів контрактів / етапів. PDF/Docs — у Drive "
        f"`google-directories` → `{dir_key}`. "
        "Оновлення: `python3 scripts/integrations/cli.py google contracts-status --write`.",
        "",
        f"- **As of:** {as_of.isoformat()}",
        f"- **Generated (UTC):** {generated}",
        f"- **Warn / critical windows:** ≤{warn}д 🟡 / ≤{critical}д 🔴",
        f"- **Config:** `config/contracts.json`",
        f"- **Playbook:** [operating-playbook.md](./operating-playbook.md)",
        "",
        "## Traffic light",
        "",
        "| Light | Meaning |",
        "|---|---|",
        "| 🟢 | On track or closed |",
        f"| 🟡 | Due within {warn} days |",
        f"| 🔴 | Due within {critical} days, overdue, or expired/terminated |",
        "| ⚪ | No end_date set |",
        "",
        "## Contracts & stages",
        "",
        "| Light | Kind | ID | Title | Status | End | Days left | Drive |",
        "|---|---|---|---|---|---|---|---|",
    ]

    for r in rows:
        end = r.end_date.isoformat() if r.end_date else "—"
        days = "—" if r.days_left is None else str(r.days_left)
        drive = f"`{r.drive_file_id}`" if r.drive_file_id else "—"
        lines.append(
            f"| {r.light} | {r.kind} | {r.item_id} | {r.title} | {r.status} | {end} | {days} | {drive} |"
        )

    action = actionable_rows(rows, warn_days=warn)
    lines.extend(["", "## Action needed (≤ warn / overdue)", ""])
    if not action:
        lines.append("_Немає відкритих дедлайнів у вікні попередження._")
    else:
        lines.append("| Light | ID | Title | Status | End | Days left |")
        lines.append("|---|---|---|---|---|---|")
        for r in action:
            end = r.end_date.isoformat() if r.end_date else "—"
            days = "—" if r.days_left is None else str(r.days_left)
            lines.append(
                f"| {r.light} | {r.item_id} | {r.title} | {r.status} | {end} | {days} |"
            )

    lines.extend(["", "## Contract details", ""])
    for c in cfg.get("contracts") or []:
        cid = c.get("id") or "?"
        lines.append(f"### {cid} — {c.get('title') or ''}")
        lines.append("")
        lines.append("| Field | Value |")
        lines.append("|---|---|")
        for key, label in (
            ("type", "Type"),
            ("status", "Status"),
            ("signed_date", "Signed"),
            ("start_date", "Start"),
            ("end_date", "End"),
            ("contract_value_usd", "Value (USD)"),
            ("owner", "Owner"),
            ("drive_file_name", "Drive file name"),
            ("drive_web_link", "Drive link"),
            ("notes", "Notes"),
        ):
            val = c.get(key)
            if val is None or val == "":
                val = "—"
            lines.append(f"| {label} | {val} |")
        stages = c.get("stages") or []
        if stages:
            lines.append("")
            lines.append("| Stage | Status | Start | End | Acceptance | Notes |")
            lines.append("|---|---|---|---|---|---|")
            for s in stages:
                lines.append(
                    "| {id} {title} | {status} | {start} | {end} | {acc} | {notes} |".format(
                        id=s.get("id") or "",
                        title=s.get("title") or "",
                        status=s.get("status") or "—",
                        start=s.get("start_date") or "—",
                        end=s.get("end_date") or "—",
                        acc=s.get("acceptance_date") or "—",
                        notes=(s.get("notes") or "—").replace("|", "/"),
                    )
                )
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(
        "_Не зберігайте підписані PDF у git — лише метадані + Drive file id. "
        "Після upload: `google sync-pull --dir contracts`, потім оновіть "
        "`drive_file_id` у `config/contracts.json`._"
    )
    lines.append("")
    return "\n".join(lines)


def write_register(
    cfg: dict[str, Any],
    *,
    as_of: Optional[date] = None,
    also_snapshot: bool = False,
) -> dict[str, Any]:
    today = as_of or date.today()
    rows = compute_deadline_rows(cfg, as_of=today)
    md = render_register_md(cfg, rows, as_of=today)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    REGISTER_PATH.write_text(md, encoding="utf-8")
    out: dict[str, Any] = {
        "as_of": today.isoformat(),
        "wrote": str(REGISTER_PATH.relative_to(ROOT)),
        "contracts": len(cfg.get("contracts") or []),
        "rows": len(rows),
        "action_needed": [r.to_dict() for r in actionable_rows(rows, warn_days=int(cfg.get("warn_days") or 14))],
    }
    if also_snapshot:
        snap = DOCS_DIR / f"status-{today.isoformat()}.md"
        snap.write_text(md, encoding="utf-8")
        out["snapshot"] = str(snap.relative_to(ROOT))
    return out


def build_status_report(
    *,
    config_path: Optional[Path] = None,
    as_of: Optional[date] = None,
    write: bool = False,
    snapshot: bool = False,
) -> dict[str, Any]:
    cfg = load_contracts_config(path=config_path, required=True)
    today = as_of or date.today()
    rows = compute_deadline_rows(cfg, as_of=today)
    report: dict[str, Any] = {
        "as_of": today.isoformat(),
        "dir_key": cfg.get("dir_key") or "contracts",
        "warn_days": cfg.get("warn_days") or 14,
        "critical_days": cfg.get("critical_days") or 7,
        "rows": [r.to_dict() for r in rows],
        "action_needed": [
            r.to_dict()
            for r in actionable_rows(rows, warn_days=int(cfg.get("warn_days") or 14))
        ],
    }
    if write:
        written = write_register(cfg, as_of=today, also_snapshot=snapshot)
        report["wrote"] = written
    return report
