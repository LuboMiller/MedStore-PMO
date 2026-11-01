"""Monthly Time Report (act) builder from Tempo bill + Jira → Google Sheets.

Layout + formatting for Devlight month tabs (Time Report act):
  A–G main table (# | Person | Work | Hours | Role | Rate | Cost)
  I–K role pivot (aligned to first data row)
  Nunito/Calibri fonts, borders, number format #,##0.00, frozen header

Config ``"layout": "compact"`` switches to the client-act layout without Person
(e.g. MedStore «Серпень/Вересень 2026»):
  row 1 blank · row 2 header A–F (# | Work | Hours | Role | Rate | Cost)
  rows 3.. data (work × role) · blank row · totals row
  H–K role pivot from row 2 (Role | SUM hours | SUM cost | rate = J/I)

Optional expenses tab (``"expenses_tab"`` in config): pass-through costs such as
API tokens, read from ``docs/acts/YYYY-MM/expenses.csv`` and written to a
separate tab (e.g. «Жовтень (Токени)»). Skipped while the CSV has no rows.
"""

from __future__ import annotations

import calendar
import csv
import json
import re
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .config import load_config
from .google_dirs import load_google_directories
from .google_workspace import GoogleNotConfigured, GoogleWorkspaceClient
from .tempo import TempoClient

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "config" / "time-report.json"
EXAMPLE_PATH = ROOT / "config" / "time-report.example.json"
ACTS_DIR = ROOT / "docs" / "acts"
JIRA_ISSUES_DIR = ROOT / "registry" / "jira" / "projects"

UA_MONTHS = {
    1: "Січень",
    2: "Лютий",
    3: "Березень",
    4: "Квітень",
    5: "Травень",
    6: "Червень",
    7: "Липень",
    8: "Серпень",
    9: "Вересень",
    10: "Жовтень",
    11: "Листопад",
    12: "Грудень",
}

HEADER = [
    "",
    "",
    "Назва етапу/робіт",
    "Кількість годин",
    "Роль/кваліфікація спеціаліста",
    "Вартість USD/год, без ПДВ",
    "Вартість USD, без ПДВ",
]

COMPACT_HEADER = [
    "",
    "Назва етапу/робіт",
    "Кількість годин",
    "Роль/кваліфікація спеціаліста",
    "Вартість USD/год, без ПДВ",
    "Вартість USD, без ПДВ",
]

COMPACT_PIVOT_HEADER = [
    "Роль/кваліфікація спеціаліста",
    "SUM з Кількість годин",
    "SUM з Вартість USD, без ПДВ",
    "rate",
]

# Column pixel widths from MedStore «Вересень 2026» (A–K).
COMPACT_COLUMN_WIDTHS_PX = [100, 616, 100, 100, 100, 100, 100, 150, 100, 100, 100]


def is_compact_layout(cfg: dict[str, Any]) -> bool:
    return str(cfg.get("layout") or "").strip().lower() == "compact"


EXPENSES_CSV_NAME = "expenses.csv"
EXPENSES_CSV_HEADER = ["Назва витрат", "Провайдер / сервіс", "Вартість USD, без ПДВ", "Примітка"]
EXPENSES_HEADER = ["", *EXPENSES_CSV_HEADER]
# A–E widths for the expenses tab.
EXPENSES_COLUMN_WIDTHS_PX = [100, 450, 200, 150, 400]


@dataclass
class ExpenseRow:
    title: str
    provider: str
    amount: float
    note: str = ""


@dataclass
class TimeReportRow:
    person: str
    work_title: str
    hours: float
    role: str
    rate: float

    @property
    def cost(self) -> float:
        return round(self.hours * self.rate, 2)


@dataclass
class TimeReportResult:
    month: str
    from_date: str
    to_date: str
    tab_title: str
    spreadsheet_id: str
    spreadsheet_url: str
    spreadsheet_created: bool
    tab_created: bool
    rows: list[TimeReportRow] = field(default_factory=list)
    totals_by_role: dict[str, dict[str, float]] = field(default_factory=dict)
    total_hours: float = 0.0
    total_cost: float = 0.0
    local_dir: str = ""
    warnings: list[str] = field(default_factory=list)
    dry_run: bool = False
    expenses_tab_title: str = ""
    expenses: list[ExpenseRow] = field(default_factory=list)
    expenses_total: float = 0.0


def load_time_report_config(path: Optional[Path] = None) -> dict[str, Any]:
    cfg_path = path or CONFIG_PATH
    if not cfg_path.exists():
        raise FileNotFoundError(
            f"Missing {cfg_path}. Copy from {EXAMPLE_PATH.name} and fill people/rates."
        )
    return json.loads(cfg_path.read_text(encoding="utf-8"))


def month_bounds(month: str) -> tuple[date, date]:
    """Parse YYYY-MM → (first day, last day)."""
    m = re.fullmatch(r"(\d{4})-(\d{2})", month.strip())
    if not m:
        raise ValueError("month must be YYYY-MM")
    year, mon = int(m.group(1)), int(m.group(2))
    if mon < 1 or mon > 12:
        raise ValueError("invalid month")
    last = calendar.monthrange(year, mon)[1]
    return date(year, mon, 1), date(year, mon, last)


def ua_tab_title(d: date) -> str:
    return f"{UA_MONTHS[d.month]} {d.year}"


def format_ua_number(value: float, *, decimals: int = 2) -> str:
    q = f"{value:.{decimals}f}"
    return q.replace(".", ",")


# Column pixel widths from Серпень/Липень 2026 reference tabs (A–K).
COLUMN_WIDTHS_PX = [76, 156, 556, 94, 187, 148, 98, 98, 98, 98, 98]

# Pivot palette (Google Sheets pivot-style greys/blues).
_PIVOT_HEADER_ROLE_BG = {"red": 0.8745098, "green": 0.89411765, "blue": 0.9254902}
_PIVOT_HEADER_VALUE_BG = {"red": 0.5019608, "green": 0.5764706, "blue": 0.7019608}
_PIVOT_ROLE_BG = {"red": 0.95686275, "green": 0.9647059, "blue": 0.972549}
_WHITE = {"red": 1.0, "green": 1.0, "blue": 1.0}


def _people_index(cfg: dict[str, Any]) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for row in cfg.get("people") or []:
        aid = str(row.get("account_id") or "").strip()
        if not aid or aid.startswith("REPLACE"):
            continue
        out[aid] = {
            "display_name": str(row.get("display_name") or aid).strip(),
            "role": str(row.get("role") or "BE").strip(),
        }
    return out


def _load_jira_issue_index(project_key: str) -> dict[str, dict[str, Any]]:
    """Map numeric Jira issue id → {key, summary}."""
    issues_dir = JIRA_ISSUES_DIR / project_key / "issues"
    by_id: dict[str, dict[str, Any]] = {}
    if not issues_dir.is_dir():
        return by_id
    for path in issues_dir.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        iid = str(data.get("id") or "").strip()
        if not iid:
            continue
        by_id[iid] = {
            "key": data.get("key"),
            "summary": (data.get("summary") or "").strip(),
            "assignee_display": data.get("assignee_display"),
            "assignee_account_id": data.get("assignee_account_id"),
        }
    return by_id


def _bill_seconds(wl: dict[str, Any]) -> int:
    bill = wl.get("billableSeconds")
    if bill is None:
        return 0
    return int(bill)


def _author_id(wl: dict[str, Any]) -> str:
    return str(
        (wl.get("author") or {}).get("accountId")
        or wl.get("authorAccountId")
        or "unknown"
    )


def _issue_id(wl: dict[str, Any]) -> str:
    issue = wl.get("issue") or {}
    raw = issue.get("id") or wl.get("issueId") or ""
    return str(raw).strip()


def aggregate_bill_rows(
    worklogs: list[dict[str, Any]],
    *,
    cfg: dict[str, Any],
    issues_by_id: dict[str, dict[str, Any]],
) -> tuple[list[TimeReportRow], list[str]]:
    """Aggregate Tempo bill hours → Time Report rows (person × work title × role).

    Compact layout groups by work title × role (person left blank) and orders
    rows by ``role_order`` then title. ``work_title_overrides`` maps a Jira key
    to the title used in the act; ``title_prefix_by_role`` prepends e.g.
    ``[BA]`` to every title of that role.
    """
    people = _people_index(cfg)
    rates: dict[str, float] = {str(k): float(v) for k, v in (cfg.get("rates") or {}).items()}
    compact = is_compact_layout(cfg)
    title_overrides: dict[str, str] = {
        str(k): str(v) for k, v in (cfg.get("work_title_overrides") or {}).items()
    }
    role_prefixes: dict[str, str] = {
        str(k): str(v).strip() for k, v in (cfg.get("title_prefix_by_role") or {}).items()
    }
    warnings: list[str] = []
    # key → seconds
    buckets: dict[tuple[str, str, str], float] = defaultdict(float)
    unknown_people: set[str] = set()

    for wl in worklogs:
        secs = _bill_seconds(wl)
        if secs <= 0:
            continue
        aid = _author_id(wl)
        person_meta = people.get(aid)
        if person_meta:
            person = person_meta["display_name"]
            role = person_meta["role"]
        else:
            unknown_people.add(aid)
            person = aid
            role = "BE"
        iid = _issue_id(wl)
        issue = issues_by_id.get(iid) if iid else None
        title = title_overrides.get(str((issue or {}).get("key") or "")) or (
            (issue or {}).get("summary") or ""
        )
        if not title:
            title = (wl.get("description") or "").strip() or f"Issue {iid or 'unknown'}"
        prefix = role_prefixes.get(role)
        if prefix and not title.startswith(prefix):
            title = f"{prefix} {title}"
        if compact:
            person = ""
        buckets[(person, title, role)] += secs / 3600.0

    if unknown_people:
        warnings.append(
            "Unknown Tempo authors (add to config/time-report.json people): "
            + ", ".join(sorted(unknown_people))
        )

    role_order = [str(r) for r in (cfg.get("role_order") or [])]

    def _sort_key(item: tuple[tuple[str, str, str], float]) -> tuple[Any, ...]:
        person, title, role = item[0]
        if compact:
            rank = role_order.index(role) if role in role_order else len(role_order)
            return (rank, role, title.lower())
        return (person.lower(), title.lower())

    rows: list[TimeReportRow] = []
    for (person, title, role), hours in sorted(buckets.items(), key=_sort_key):
        rate = float(rates.get(role, rates.get("BE", 45.0)))
        rows.append(
            TimeReportRow(
                person=person,
                work_title=title,
                hours=round(hours, 2),
                role=role,
                rate=rate,
            )
        )
    return rows, warnings


def _attach_ijk(row: list[Any], block: list[Any]) -> None:
    """Pad/truncate row to A–G, add empty H, then append I–K block in-place."""
    if len(row) < 7:
        row.extend([""] * (7 - len(row)))
    else:
        del row[7:]
    row.append("")  # H spacer
    row.extend(block)


def build_sheet_values(rows: list[TimeReportRow]) -> list[list[Any]]:
    """Sheet matrix matching July/August 2026 layout.

    Structure (1-based sheet rows):
      1     — headers A–G
      2     — blank
      3..N  — data; G is ``=D{r}*F{r}``; pivot I–K starts on row 3
      N+1   — footer totals ``=SUM(D3:DN)`` / ``=SUM(G3:GN)``

    Pivot I–K (from row 3): header → blank 0-row → roles → «Загальний результат».
    """
    values: list[list[Any]] = [list(HEADER)]
    values.append([])  # blank row like recent months

    by_role_hours: dict[str, float] = defaultdict(float)
    by_role_cost: dict[str, float] = defaultdict(float)
    for i, row in enumerate(rows, start=1):
        sheet_row = i + 2  # data starts at sheet row 3
        values.append(
            [
                i,
                row.person,
                row.work_title,
                round(row.hours, 2),
                row.role,
                round(row.rate, 2),
                f"=D{sheet_row}*F{sheet_row}",
            ]
        )
        by_role_hours[row.role] += row.hours
        by_role_cost[row.role] += row.cost

    n = len(rows)
    data_start = 2  # 0-based index of first data row
    last_data_sheet_row = n + 2  # 1-based
    footer_idx = data_start + n

    # Reserve footer slot now (before pivot may extend the matrix).
    values.append(["", "", "", "", "", "", ""])

    # Pivot I–K: header + blank 0-row (Sheets pivot artifact) + roles + total.
    pivot_blocks: list[list[Any]] = [
        [
            "Роль/кваліфікація спеціаліста",
            "COUNTA з Кількість годин",
            "SUM з Вартість USD, без ПДВ",
        ],
        ["", 0.0, 0.0],
    ]
    for role, hours in sorted(by_role_hours.items(), key=lambda x: x[0]):
        pivot_blocks.append(
            [role, round(hours, 2), round(by_role_cost[role], 2)]
        )
    pivot_blocks.append(
        [
            "Загальний результат",
            round(sum(by_role_hours.values()), 2),
            round(sum(by_role_cost.values()), 2),
        ]
    )

    for offset, block in enumerate(pivot_blocks):
        target = data_start + offset
        while len(values) <= target:
            values.append([])
        # Never let pivot wipe the footer A–G formulas — only attach I–K there.
        if target == footer_idx:
            _attach_ijk(values[target], block)
            # restore footer A–G after attach (attach keeps A–G from row; ensure formulas)
        else:
            _attach_ijk(values[target], block)

    # Always write footer totals into A–G at footer_idx (preserve I–K if present).
    while len(values) <= footer_idx:
        values.append([])
    fr = values[footer_idx]
    while len(fr) < 7:
        fr.append("")
    fr[0] = ""
    fr[1] = ""
    fr[2] = ""
    fr[3] = f"=SUM(D3:D{last_data_sheet_row})"
    fr[4] = ""
    fr[5] = ""
    fr[6] = f"=SUM(G3:G{last_data_sheet_row})"

    return values


def build_compact_sheet_values(rows: list[TimeReportRow]) -> list[list[Any]]:
    """Sheet matrix matching MedStore «Вересень 2026» layout.

    Structure (1-based sheet rows):
      1      — blank
      2      — headers A–F; pivot header H–K
      3..N   — data; F is ``=E{r}*C{r}``
      N+1    — blank (bordered)
      N+2    — totals ``=SUM(C3:C{N+1})`` / ``=SUM(F3:F{N+1})``

    Pivot H–K (from row 3): blank 0-row → roles (K = J/I) → «Загальний результат».
    """
    values: list[list[Any]] = [[], list(COMPACT_HEADER) + [""] + list(COMPACT_PIVOT_HEADER)]

    by_role_hours: dict[str, float] = defaultdict(float)
    by_role_cost: dict[str, float] = defaultdict(float)
    role_seen: list[str] = []
    for i, row in enumerate(rows, start=1):
        sheet_row = i + 2  # data starts at sheet row 3
        values.append(
            [
                i,
                row.work_title,
                round(row.hours, 2),
                row.role,
                round(row.rate, 2),
                f"=E{sheet_row}*C{sheet_row}",
            ]
        )
        by_role_hours[row.role] += row.hours
        by_role_cost[row.role] += row.cost
        if row.role not in role_seen:
            role_seen.append(row.role)

    n = len(rows)
    blank_sheet_row = n + 3
    values.append([])  # blank bordered row under data
    values.append(
        ["", "", f"=SUM(C3:C{blank_sheet_row})", "", "", f"=SUM(F3:F{blank_sheet_row})"]
    )

    pivot_blocks: list[list[Any]] = [["", 0, 0.0]]
    for role in sorted(role_seen):
        r = 3 + len(pivot_blocks)  # sheet row of this pivot line (0-row is row 3)
        pivot_blocks.append(
            [role, round(by_role_hours[role], 2), round(by_role_cost[role], 2), f"=J{r}/I{r}"]
        )
    pivot_blocks.append(
        [
            "Загальний результат",
            round(sum(by_role_hours.values()), 2),
            round(sum(by_role_cost.values()), 2),
        ]
    )

    data_start = 2  # 0-based index of sheet row 3
    for offset, block in enumerate(pivot_blocks):
        target = data_start + offset
        while len(values) <= target:
            values.append([])
        row = values[target]
        if len(row) < 7:
            row.extend([""] * (7 - len(row)))
        else:
            del row[7:]
        row.extend(block)

    return values


def build_compact_tab_format_requests(
    sheet_id: int,
    *,
    data_row_count: int,
    role_count: int,
) -> list[dict[str, Any]]:
    """batchUpdate requests matching MedStore «Вересень 2026» styling."""
    if data_row_count < 0 or role_count < 0:
        raise ValueError("data_row_count and role_count must be >= 0")

    header_row = 1  # 0-indexed sheet row 2
    data_start = 2
    data_end = data_start + data_row_count
    blank_row = data_end
    footer_row = data_end + 1
    pivot_blank_row = data_start
    pivot_roles_start = data_start + 1
    pivot_roles_end = pivot_roles_start + role_count
    pivot_total_row = pivot_roles_end
    last_content_row = max(footer_row + 1, pivot_total_row + 1)

    reqs: list[dict[str, Any]] = []
    for i, px in enumerate(COMPACT_COLUMN_WIDTHS_PX):
        reqs.append(
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": sheet_id,
                        "dimension": "COLUMNS",
                        "startIndex": i,
                        "endIndex": i + 1,
                    },
                    "properties": {"pixelSize": px},
                    "fields": "pixelSize",
                }
            }
        )

    reqs.append(
        _repeat_cell(
            sheet_id,
            start_row=0,
            end_row=max(last_content_row, 3),
            start_col=0,
            end_col=11,
            cell={"userEnteredFormat": {}},
            fields="userEnteredFormat",
        )
    )

    border = _solid_border()
    num_fmt = {"type": "NUMBER", "pattern": "#,##0.00"}
    fmt_fields = "userEnteredFormat(textFormat,horizontalAlignment,verticalAlignment,wrapStrategy,numberFormat,borders)"

    def cell(
        *,
        tf: dict[str, Any],
        h: str,
        v: str = "BOTTOM",
        wrap: str = "WRAP",
        num: bool = False,
        borders: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        fmt: dict[str, Any] = {
            "textFormat": tf,
            "horizontalAlignment": h,
            "verticalAlignment": v,
            "wrapStrategy": wrap,
            "borders": border if borders is None else borders,
        }
        if num:
            fmt["numberFormat"] = num_fmt
        return {"userEnteredFormat": fmt}

    # Header A–F: Nunito 11 bold, wrap, borders; B left, rest center.
    reqs.append(
        _repeat_cell(
            sheet_id, start_row=header_row, end_row=header_row + 1, start_col=0, end_col=6,
            cell=cell(tf=_text_format(bold=True), h="CENTER"), fields=fmt_fields,
        )
    )
    reqs.append(
        _repeat_cell(
            sheet_id, start_row=header_row, end_row=header_row + 1, start_col=1, end_col=2,
            cell={"userEnteredFormat": {"horizontalAlignment": "LEFT"}},
            fields="userEnteredFormat.horizontalAlignment",
        )
    )

    if data_row_count > 0:
        column_cells = [
            (0, 1, cell(tf=_text_format(), h="CENTER", v="TOP")),
            (1, 2, cell(tf=_text_format(font="Arial", size=10), h="LEFT", wrap="OVERFLOW_CELL")),
            (2, 3, cell(tf=_text_format(font="Arial", size=10), h="RIGHT", wrap="OVERFLOW_CELL")),
            (3, 4, cell(tf=_text_format(), h="CENTER")),
            (4, 6, cell(tf=_text_format(), h="CENTER", num=True)),
        ]
        for c0, c1, c in column_cells:
            reqs.append(
                _repeat_cell(
                    sheet_id, start_row=data_start, end_row=data_end, start_col=c0, end_col=c1,
                    cell=c, fields=fmt_fields,
                )
            )

    # Blank + totals rows: bordered A–F; totals C/F Arial 12 bold center.
    reqs.append(
        _repeat_cell(
            sheet_id, start_row=blank_row, end_row=footer_row + 1, start_col=0, end_col=6,
            cell=cell(tf=_text_format(font="Arial", size=10), h="LEFT", wrap="OVERFLOW_CELL"),
            fields=fmt_fields,
        )
    )
    for col in (2, 5):
        reqs.append(
            _repeat_cell(
                sheet_id, start_row=footer_row, end_row=footer_row + 1, start_col=col, end_col=col + 1,
                cell=cell(
                    tf=_text_format(font="Arial", size=12, bold=True),
                    h="CENTER", wrap="OVERFLOW_CELL", num=(col == 5),
                ),
                fields=fmt_fields,
            )
        )

    # Pivot header H (role) + I–J (values) + K (rate).
    pivot_tf = _text_format(font="Arial", size=10)
    reqs.append(
        _repeat_cell(
            sheet_id, start_row=header_row, end_row=header_row + 1, start_col=7, end_col=8,
            cell={"userEnteredFormat": {
                "textFormat": pivot_tf,
                "backgroundColor": _PIVOT_HEADER_ROLE_BG,
                "borders": {"bottom": {"style": "SOLID_THICK"}},
            }},
            fields="userEnteredFormat(textFormat,backgroundColor,borders)",
        )
    )
    reqs.append(
        _repeat_cell(
            sheet_id, start_row=header_row, end_row=header_row + 1, start_col=8, end_col=10,
            cell={"userEnteredFormat": {
                "textFormat": _text_format(font="Arial", size=10, fg=_WHITE),
                "backgroundColor": _PIVOT_HEADER_VALUE_BG,
                "borders": {"bottom": {"style": "SOLID_THICK"}},
            }},
            fields="userEnteredFormat(textFormat,backgroundColor,borders)",
        )
    )
    reqs.append(
        _repeat_cell(
            sheet_id, start_row=header_row, end_row=header_row + 1, start_col=10, end_col=11,
            cell={"userEnteredFormat": {"textFormat": pivot_tf, "horizontalAlignment": "CENTER"}},
            fields="userEnteredFormat(textFormat,horizontalAlignment)",
        )
    )

    # Pivot 0-row + role rows: H grey label, I–K right-aligned numbers.
    reqs.append(
        _repeat_cell(
            sheet_id, start_row=pivot_blank_row, end_row=pivot_roles_end, start_col=7, end_col=8,
            cell={"userEnteredFormat": {
                "textFormat": pivot_tf,
                "backgroundColor": _PIVOT_ROLE_BG,
                "borders": {"right": {"style": "SOLID"}},
            }},
            fields="userEnteredFormat(textFormat,backgroundColor,borders)",
        )
    )
    reqs.append(
        _repeat_cell(
            sheet_id, start_row=pivot_blank_row, end_row=pivot_roles_end, start_col=8, end_col=11,
            cell={"userEnteredFormat": {"textFormat": pivot_tf, "horizontalAlignment": "RIGHT"}},
            fields="userEnteredFormat(textFormat,horizontalAlignment)",
        )
    )
    reqs.append(
        _repeat_cell(
            sheet_id, start_row=pivot_blank_row, end_row=pivot_roles_end, start_col=9, end_col=10,
            cell={"userEnteredFormat": {"numberFormat": num_fmt}},
            fields="userEnteredFormat.numberFormat",
        )
    )

    # Pivot total H–J.
    reqs.append(
        _repeat_cell(
            sheet_id, start_row=pivot_total_row, end_row=pivot_total_row + 1, start_col=7, end_col=10,
            cell={"userEnteredFormat": {
                "textFormat": _text_format(font="Arial", size=10, bold=True),
                "backgroundColor": _PIVOT_HEADER_ROLE_BG,
                "borders": {"top": {"style": "SOLID"}},
                "horizontalAlignment": "RIGHT",
            }},
            fields="userEnteredFormat(textFormat,backgroundColor,borders,horizontalAlignment)",
        )
    )
    reqs.append(
        _repeat_cell(
            sheet_id, start_row=pivot_total_row, end_row=pivot_total_row + 1, start_col=7, end_col=8,
            cell={"userEnteredFormat": {"horizontalAlignment": "LEFT"}},
            fields="userEnteredFormat.horizontalAlignment",
        )
    )
    reqs.append(
        _repeat_cell(
            sheet_id, start_row=pivot_total_row, end_row=pivot_total_row + 1, start_col=9, end_col=10,
            cell={"userEnteredFormat": {"numberFormat": num_fmt}},
            fields="userEnteredFormat.numberFormat",
        )
    )

    return reqs


def expenses_tab_title(cfg: dict[str, Any], d: date) -> str:
    tpl = str((cfg.get("expenses_tab") or {}).get("title_template") or "{month_name} (Токени)")
    return tpl.format(month_name=UA_MONTHS[d.month], year=d.year)


def _parse_amount(raw: str) -> float:
    s = str(raw or "").replace("$", "").replace("\xa0", "").replace(" ", "").replace(",", ".")
    return float(s) if s else 0.0


def load_expenses_csv(path: Path) -> list[ExpenseRow]:
    """Read pass-through expenses (header ``EXPENSES_CSV_HEADER``); blank rows skipped."""
    if not path.exists():
        return []
    out: list[ExpenseRow] = []
    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.reader(fh)
        next(reader, None)
        for row in reader:
            row = [c.strip() for c in row] + [""] * (4 - len(row))
            if not row[0] and not row[2]:
                continue
            out.append(
                ExpenseRow(title=row[0], provider=row[1], amount=_parse_amount(row[2]), note=row[3])
            )
    return out


def ensure_expenses_csv(path: Path) -> None:
    """Create an empty expenses CSV (header only) for the PM to fill from invoices."""
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        csv.writer(fh).writerow(EXPENSES_CSV_HEADER)


def build_expenses_sheet_values(rows: list[ExpenseRow]) -> list[list[Any]]:
    """Row 1 blank · row 2 header A–E · rows 3.. data · blank · total ``=SUM(D…)``."""
    values: list[list[Any]] = [[], list(EXPENSES_HEADER)]
    for i, row in enumerate(rows, start=1):
        values.append([i, row.title, row.provider, round(row.amount, 2), row.note])
    blank_sheet_row = len(rows) + 3
    values.append([])
    values.append(["", "Разом", "", f"=SUM(D3:D{blank_sheet_row})", ""])
    return values


def build_expenses_tab_format_requests(sheet_id: int, *, data_row_count: int) -> list[dict[str, Any]]:
    """Compact-act styling for the expenses tab (A–E)."""
    header_row, data_start = 1, 2
    data_end = data_start + data_row_count
    footer_row = data_end + 1
    border = _solid_border()
    num_fmt = {"type": "NUMBER", "pattern": "#,##0.00"}
    fields = "userEnteredFormat(textFormat,horizontalAlignment,verticalAlignment,wrapStrategy,numberFormat,borders)"

    def fmt(tf: dict[str, Any], h: str, *, num: bool = False, v: str = "BOTTOM") -> dict[str, Any]:
        f: dict[str, Any] = {
            "textFormat": tf,
            "horizontalAlignment": h,
            "verticalAlignment": v,
            "wrapStrategy": "WRAP",
            "borders": border,
        }
        if num:
            f["numberFormat"] = num_fmt
        return {"userEnteredFormat": f}

    reqs: list[dict[str, Any]] = []
    for i, px in enumerate(EXPENSES_COLUMN_WIDTHS_PX):
        reqs.append(
            {
                "updateDimensionProperties": {
                    "range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": i, "endIndex": i + 1},
                    "properties": {"pixelSize": px},
                    "fields": "pixelSize",
                }
            }
        )
    reqs.append(
        _repeat_cell(
            sheet_id, start_row=0, end_row=footer_row + 1, start_col=0, end_col=5,
            cell={"userEnteredFormat": {}}, fields="userEnteredFormat",
        )
    )
    reqs.append(
        _repeat_cell(
            sheet_id, start_row=header_row, end_row=header_row + 1, start_col=0, end_col=5,
            cell=fmt(_text_format(bold=True), "CENTER"), fields=fields,
        )
    )
    body = [
        (0, 1, fmt(_text_format(), "CENTER", v="TOP")),
        (1, 3, fmt(_text_format(font="Arial", size=10), "LEFT")),
        (3, 4, fmt(_text_format(), "CENTER", num=True)),
        (4, 5, fmt(_text_format(font="Arial", size=10), "LEFT")),
    ]
    for c0, c1, c in body:
        reqs.append(
            _repeat_cell(
                sheet_id, start_row=data_start, end_row=footer_row, start_col=c0, end_col=c1,
                cell=c, fields=fields,
            )
        )
    reqs.append(
        _repeat_cell(
            sheet_id, start_row=footer_row, end_row=footer_row + 1, start_col=0, end_col=5,
            cell=fmt(_text_format(font="Arial", size=12, bold=True), "CENTER", num=True), fields=fields,
        )
    )
    return reqs


def _write_tab(
    google: GoogleWorkspaceClient,
    sid: str,
    title: str,
    *,
    force: bool,
    allow_overwrite: bool,
) -> tuple[str, bool]:
    """Find or add tab ``title``; refuse to overwrite data unless allowed. Returns (real_title, created)."""
    existing = {t.strip(): t for t in google.list_sheet_titles(sid)}
    if title in existing:
        real_title = existing[title]
        if not force and not allow_overwrite:
            existing_vals = google.read_sheet_values(sid, f"'{real_title}'!A1:G5")
            if [r for r in existing_vals[1:] if any(str(c).strip() for c in r)]:
                raise RuntimeError(
                    f"Tab '{real_title}' already has data. Re-run with --force to overwrite."
                )
        google.clear_sheet_values(sid, f"'{real_title}'!A:K")
        return real_title, False
    google.add_sheet(sid, title)
    return title, True


def _solid_border(style: str = "SOLID") -> dict[str, Any]:
    return {
        "top": {"style": style},
        "bottom": {"style": style},
        "left": {"style": style},
        "right": {"style": style},
    }


def _text_format(
    *,
    font: str = "Nunito",
    size: int = 11,
    bold: bool = False,
    fg: Optional[dict[str, float]] = None,
) -> dict[str, Any]:
    tf: dict[str, Any] = {
        "fontFamily": font,
        "fontSize": size,
        "bold": bold,
    }
    if fg is not None:
        tf["foregroundColor"] = fg
    return tf


def _repeat_cell(
    sheet_id: int,
    *,
    start_row: int,
    end_row: int,
    start_col: int,
    end_col: int,
    cell: dict[str, Any],
    fields: str,
) -> dict[str, Any]:
    return {
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": start_row,
                "endRowIndex": end_row,
                "startColumnIndex": start_col,
                "endColumnIndex": end_col,
            },
            "cell": cell,
            "fields": fields,
        }
    }


def build_month_tab_format_requests(
    sheet_id: int,
    *,
    data_row_count: int,
    role_count: int,
) -> list[dict[str, Any]]:
    """batchUpdate requests matching July/August 2026 Time Report styling."""
    if data_row_count < 0 or role_count < 0:
        raise ValueError("data_row_count and role_count must be >= 0")

    data_start = 2  # 0-indexed sheet row 3
    data_end = data_start + data_row_count
    footer_row = data_end  # totals row right under last data row
    # Pivot: header @ data_start, blank 0-row, then roles, then «Загальний результат»
    pivot_header_row = data_start
    pivot_blank_row = data_start + 1
    pivot_roles_start = data_start + 2
    pivot_roles_end = pivot_roles_start + role_count
    pivot_total_row = pivot_roles_end
    last_content_row = max(footer_row + 1, pivot_total_row + 1)

    reqs: list[dict[str, Any]] = []

    # Freeze header; size grid to content (+ buffer) like Jul/Aug.
    reqs.append(
        {
            "updateSheetProperties": {
                "properties": {
                    "sheetId": sheet_id,
                    "gridProperties": {
                        "frozenRowCount": 1,
                        "rowCount": max(last_content_row + 5, 50),
                        "columnCount": max(11, 23),
                    },
                },
                "fields": "gridProperties.frozenRowCount,gridProperties.rowCount,gridProperties.columnCount",
            }
        }
    )

    for i, px in enumerate(COLUMN_WIDTHS_PX):
        reqs.append(
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": sheet_id,
                        "dimension": "COLUMNS",
                        "startIndex": i,
                        "endIndex": i + 1,
                    },
                    "properties": {"pixelSize": px},
                    "fields": "pixelSize",
                }
            }
        )

    # Clear formats on used area before applying (avoids stale styles after --force).
    clear_end = max(last_content_row, data_end + 1, 3)
    reqs.append(
        _repeat_cell(
            sheet_id,
            start_row=0,
            end_row=clear_end,
            start_col=0,
            end_col=11,
            cell={"userEnteredFormat": {}},
            fields="userEnteredFormat",
        )
    )

    border = _solid_border()
    num_fmt = {"type": "NUMBER", "pattern": "#,##0.00"}

    # Header row A–G
    reqs.append(
        _repeat_cell(
            sheet_id,
            start_row=0,
            end_row=1,
            start_col=0,
            end_col=7,
            cell={
                "userEnteredFormat": {
                    "textFormat": _text_format(bold=True),
                    "horizontalAlignment": "CENTER",
                    "verticalAlignment": "BOTTOM",
                    "wrapStrategy": "WRAP",
                    "borders": border,
                }
            },
            fields="userEnteredFormat(textFormat,horizontalAlignment,verticalAlignment,wrapStrategy,borders)",
        )
    )
    # C header left-aligned (Назва етапу/робіт)
    reqs.append(
        _repeat_cell(
            sheet_id,
            start_row=0,
            end_row=1,
            start_col=2,
            end_col=3,
            cell={
                "userEnteredFormat": {
                    "horizontalAlignment": "LEFT",
                }
            },
            fields="userEnteredFormat.horizontalAlignment",
        )
    )

    if data_row_count == 0:
        return reqs

    # Data cols A–B: Nunito, center, top, wrap, borders
    reqs.append(
        _repeat_cell(
            sheet_id,
            start_row=data_start,
            end_row=data_end,
            start_col=0,
            end_col=2,
            cell={
                "userEnteredFormat": {
                    "textFormat": _text_format(),
                    "horizontalAlignment": "CENTER",
                    "verticalAlignment": "TOP",
                    "wrapStrategy": "WRAP",
                    "borders": border,
                }
            },
            fields="userEnteredFormat(textFormat,horizontalAlignment,verticalAlignment,wrapStrategy,borders)",
        )
    )
    # Col C work title: Calibri 12, left, no borders
    reqs.append(
        _repeat_cell(
            sheet_id,
            start_row=data_start,
            end_row=data_end,
            start_col=2,
            end_col=3,
            cell={
                "userEnteredFormat": {
                    "textFormat": _text_format(font="Calibri", size=12),
                    "horizontalAlignment": "LEFT",
                    "verticalAlignment": "BOTTOM",
                    "wrapStrategy": "OVERFLOW_CELL",
                }
            },
            fields="userEnteredFormat(textFormat,horizontalAlignment,verticalAlignment,wrapStrategy)",
        )
    )
    # Col D hours: number + borders center
    reqs.append(
        _repeat_cell(
            sheet_id,
            start_row=data_start,
            end_row=data_end,
            start_col=3,
            end_col=4,
            cell={
                "userEnteredFormat": {
                    "textFormat": _text_format(),
                    "horizontalAlignment": "CENTER",
                    "verticalAlignment": "BOTTOM",
                    "numberFormat": num_fmt,
                    "borders": border,
                }
            },
            fields="userEnteredFormat(textFormat,horizontalAlignment,verticalAlignment,numberFormat,borders)",
        )
    )
    # Col E role
    reqs.append(
        _repeat_cell(
            sheet_id,
            start_row=data_start,
            end_row=data_end,
            start_col=4,
            end_col=5,
            cell={
                "userEnteredFormat": {
                    "textFormat": _text_format(),
                    "horizontalAlignment": "CENTER",
                    "verticalAlignment": "BOTTOM",
                    "wrapStrategy": "WRAP",
                    "borders": border,
                }
            },
            fields="userEnteredFormat(textFormat,horizontalAlignment,verticalAlignment,wrapStrategy,borders)",
        )
    )
    # Cols F–G rate/cost (G is =D*F formula)
    reqs.append(
        _repeat_cell(
            sheet_id,
            start_row=data_start,
            end_row=data_end,
            start_col=5,
            end_col=7,
            cell={
                "userEnteredFormat": {
                    "textFormat": _text_format(),
                    "horizontalAlignment": "CENTER",
                    "verticalAlignment": "BOTTOM",
                    "wrapStrategy": "WRAP",
                    "numberFormat": num_fmt,
                    "borders": border,
                }
            },
            fields="userEnteredFormat(textFormat,horizontalAlignment,verticalAlignment,wrapStrategy,numberFormat,borders)",
        )
    )

    # Footer totals row: bold D + G, borders on D–G
    reqs.append(
        _repeat_cell(
            sheet_id,
            start_row=footer_row,
            end_row=footer_row + 1,
            start_col=3,
            end_col=7,
            cell={
                "userEnteredFormat": {
                    "textFormat": _text_format(bold=True),
                    "horizontalAlignment": "CENTER",
                    "verticalAlignment": "BOTTOM",
                    "numberFormat": num_fmt,
                    "borders": border,
                }
            },
            fields="userEnteredFormat(textFormat,horizontalAlignment,verticalAlignment,numberFormat,borders)",
        )
    )

    # Pivot header I
    reqs.append(
        _repeat_cell(
            sheet_id,
            start_row=pivot_header_row,
            end_row=pivot_header_row + 1,
            start_col=8,
            end_col=9,
            cell={
                "userEnteredFormat": {
                    "textFormat": _text_format(font="Arial", size=10),
                    "backgroundColor": _PIVOT_HEADER_ROLE_BG,
                    "borders": {"bottom": {"style": "SOLID_THICK"}},
                }
            },
            fields="userEnteredFormat(textFormat,backgroundColor,borders)",
        )
    )
    # Pivot header J–K
    reqs.append(
        _repeat_cell(
            sheet_id,
            start_row=pivot_header_row,
            end_row=pivot_header_row + 1,
            start_col=9,
            end_col=11,
            cell={
                "userEnteredFormat": {
                    "textFormat": _text_format(font="Arial", size=10, fg=_WHITE),
                    "backgroundColor": _PIVOT_HEADER_VALUE_BG,
                    "borders": {"bottom": {"style": "SOLID_THICK"}},
                }
            },
            fields="userEnteredFormat(textFormat,backgroundColor,borders)",
        )
    )

    # Blank pivot 0-row (I bg + J/K zeros)
    reqs.append(
        _repeat_cell(
            sheet_id,
            start_row=pivot_blank_row,
            end_row=pivot_blank_row + 1,
            start_col=8,
            end_col=9,
            cell={
                "userEnteredFormat": {
                    "textFormat": _text_format(font="Arial", size=10),
                    "backgroundColor": _PIVOT_ROLE_BG,
                    "borders": {"right": {"style": "SOLID"}},
                }
            },
            fields="userEnteredFormat(textFormat,backgroundColor,borders)",
        )
    )
    reqs.append(
        _repeat_cell(
            sheet_id,
            start_row=pivot_blank_row,
            end_row=pivot_blank_row + 1,
            start_col=9,
            end_col=11,
            cell={
                "userEnteredFormat": {
                    "textFormat": _text_format(font="Arial", size=10),
                    "horizontalAlignment": "RIGHT",
                    "numberFormat": num_fmt,
                }
            },
            fields="userEnteredFormat(textFormat,horizontalAlignment,numberFormat)",
        )
    )

    if role_count > 0:
        # Role labels I
        reqs.append(
            _repeat_cell(
                sheet_id,
                start_row=pivot_roles_start,
                end_row=pivot_roles_end,
                start_col=8,
                end_col=9,
                cell={
                    "userEnteredFormat": {
                        "textFormat": _text_format(font="Arial", size=10),
                        "backgroundColor": _PIVOT_ROLE_BG,
                        "borders": {"right": {"style": "SOLID"}},
                    }
                },
                fields="userEnteredFormat(textFormat,backgroundColor,borders)",
            )
        )
        # Role values J–K
        reqs.append(
            _repeat_cell(
                sheet_id,
                start_row=pivot_roles_start,
                end_row=pivot_roles_end,
                start_col=9,
                end_col=11,
                cell={
                    "userEnteredFormat": {
                        "textFormat": _text_format(font="Arial", size=10),
                        "horizontalAlignment": "RIGHT",
                        "numberFormat": num_fmt,
                    }
                },
                fields="userEnteredFormat(textFormat,horizontalAlignment,numberFormat)",
            )
        )

    # Total row I–K
    reqs.append(
        _repeat_cell(
            sheet_id,
            start_row=pivot_total_row,
            end_row=pivot_total_row + 1,
            start_col=8,
            end_col=11,
            cell={
                "userEnteredFormat": {
                    "textFormat": _text_format(font="Arial", size=10, bold=True),
                    "backgroundColor": _PIVOT_HEADER_ROLE_BG,
                    "borders": {"top": {"style": "SOLID"}},
                    "horizontalAlignment": "LEFT",
                    "numberFormat": num_fmt,
                }
            },
            fields="userEnteredFormat(textFormat,backgroundColor,borders,horizontalAlignment,numberFormat)",
        )
    )
    # Total numeric cols right-aligned
    reqs.append(
        _repeat_cell(
            sheet_id,
            start_row=pivot_total_row,
            end_row=pivot_total_row + 1,
            start_col=9,
            end_col=11,
            cell={
                "userEnteredFormat": {
                    "horizontalAlignment": "RIGHT",
                }
            },
            fields="userEnteredFormat.horizontalAlignment",
        )
    )

    return reqs


def apply_month_tab_formatting(
    client: GoogleWorkspaceClient,
    spreadsheet_id: str,
    sheet_title: str,
    *,
    data_row_count: int,
    role_count: int,
    compact: bool = False,
) -> None:
    """Apply July/August (or compact MedStore) visual style to a filled month tab."""
    sheet_id = client.get_sheet_id(spreadsheet_id, sheet_title)
    builder = build_compact_tab_format_requests if compact else build_month_tab_format_requests
    requests = builder(
        sheet_id,
        data_row_count=data_row_count,
        role_count=role_count,
    )
    client.batch_update_spreadsheet(spreadsheet_id, requests)


def write_local_pack(
    *,
    month: str,
    rows: list[TimeReportRow],
    meta: dict[str, Any],
) -> Path:
    out = ACTS_DIR / month
    out.mkdir(parents=True, exist_ok=True)
    csv_path = out / "time-report-draft.csv"
    md_path = out / "time-report-draft.md"
    json_path = out / "time-report-meta.json"

    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(
            [
                "#",
                "Person",
                "Work",
                "Hours",
                "Role",
                "Rate",
                "Cost",
            ]
        )
        for i, row in enumerate(rows, start=1):
            w.writerow(
                [
                    i,
                    row.person,
                    row.work_title,
                    f"{row.hours:.2f}",
                    row.role,
                    f"{row.rate:.2f}",
                    f"{row.cost:.2f}",
                ]
            )

    total_h = sum(r.hours for r in rows)
    total_c = sum(r.cost for r in rows)
    by_role: dict[str, dict[str, float]] = defaultdict(lambda: {"hours": 0.0, "cost": 0.0})
    for r in rows:
        by_role[r.role]["hours"] += r.hours
        by_role[r.role]["cost"] += r.cost

    lines = [
        f"# Time Report draft — {month}",
        "",
        f"- Period: `{meta.get('from_date')}` → `{meta.get('to_date')}`",
        f"- Source: Tempo **bill** only + Jira summaries",
        f"- Spreadsheet: `{meta.get('spreadsheet_id')}`",
        f"- Tab: `{meta.get('tab_title')}`",
        f"- Rows: **{len(rows)}** · Hours: **{total_h:.2f}** · Cost: **${total_c:,.2f}** (no VAT)",
        "",
        "## Totals by role",
        "",
        "| Role | Hours | Cost USD |",
        "|---|---:|---:|",
    ]
    for role, agg in sorted(by_role.items()):
        lines.append(f"| {role} | {agg['hours']:.2f} | {agg['cost']:,.2f} |")
    lines.extend(
        [
            "",
            "## Rows (preview)",
            "",
            "| # | Person | Work | Hours | Role | Cost |",
            "|---|---|---|---:|---|---:|",
        ]
    )
    for i, row in enumerate(rows[:40], start=1):
        title = row.work_title.replace("|", "/")
        lines.append(
            f"| {i} | {row.person} | {title[:80]} | {row.hours:.2f} | {row.role} | {row.cost:,.2f} |"
        )
    if len(rows) > 40:
        lines.append(f"| … | _{len(rows) - 40} more_ | | | | |")
    lines.append("")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    json_path.write_text(
        json.dumps({**meta, "row_count": len(rows), "total_hours": total_h, "total_cost": total_c}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )
    return out


def _resolve_parent_folder(
    client: GoogleWorkspaceClient,
    cfg: dict[str, Any],
) -> tuple[str, Optional[str]]:
    """Return (folder_id, dir_key) for commercial/Reports."""
    dirs = load_google_directories(required=False)
    dir_key = cfg.get("dir_key") or "commercial"
    if dirs is None:
        raise GoogleNotConfigured(
            "config/google-directories.json missing — run: google init-dirs"
        )
    d = dirs.get(dir_key)
    folder_id = d.folder_id
    reports_name = (cfg.get("reports_folder_name") or "Reports").strip()
    if reports_name:
        for f in client.list_folder(folder_id, page_size=100):
            if f.get("mimeType") == "application/vnd.google-apps.folder" and (
                f.get("name") or ""
            ).strip() == reports_name:
                return f["id"], dir_key
    return folder_id, dir_key


def find_or_create_spreadsheet(
    client: GoogleWorkspaceClient,
    cfg: dict[str, Any],
    *,
    year: int,
    create_if_missing: bool = True,
    dry_run: bool = False,
) -> tuple[str, str, bool]:
    """Return (spreadsheet_id, url, created)."""
    sid = (cfg.get("spreadsheet_id") or "").strip()
    if sid:
        meta = client.get_file_meta(sid)
        # Resolve Drive shortcut → target spreadsheet
        if meta.get("mimeType") == "application/vnd.google-apps.shortcut":
            target = (meta.get("shortcutDetails") or {}).get("targetId")
            if not target:
                raise RuntimeError(f"Shortcut {sid} has no targetId")
            sid = target
            meta = client.get_file_meta(sid)
        url = meta.get("webViewLink") or f"https://docs.google.com/spreadsheets/d/{sid}"
        return sid, url, False

    parent_id, _ = _resolve_parent_folder(client, cfg)
    pattern = (cfg.get("name_pattern") or "Time Report").lower()
    candidates = client.find_spreadsheets(
        parent_id,
        name_substr=pattern,
        recursive=True,
    )
    # Prefer name containing year
    ranked = sorted(
        candidates,
        key=lambda f: (
            0 if str(year) in (f.get("name") or "") else 1,
            (f.get("name") or ""),
        ),
    )
    if ranked:
        hit = ranked[0]
        sid = hit["id"]
        url = hit.get("webViewLink") or f"https://docs.google.com/spreadsheets/d/{sid}"
        return sid, url, False

    if not create_if_missing:
        raise FileNotFoundError(
            f"No spreadsheet matching '{pattern}' under folder {parent_id}"
        )

    title = (cfg.get("create_title_template") or "{project_name} | {year} Time Report").format(
        project_name=cfg.get("project_name") or "Project",
        year=year,
    )
    if dry_run:
        return "DRY_RUN_NEW", f"(would create) {title}", True

    created = client.create_spreadsheet(
        title=title,
        parent_folder_id=parent_id,
        sheet_titles=["Rates", ua_tab_title(date(year, 1, 1))],
    )
    sid = created["spreadsheetId"]
    # Seed Rates tab
    rate_rows = [["Вид робіт", "Ціна без ПДВ", "Short"]]
    labels = cfg.get("rate_labels") or {}
    rates = cfg.get("rates") or {}
    for short, amount in sorted(rates.items(), key=lambda x: x[0]):
        label = labels.get(short, short)
        rate_rows.append([label, f"${format_ua_number(float(amount))}", short])
    client.write_sheet_values(sid, "Rates!A1", rate_rows)
    url = created.get("spreadsheetUrl") or f"https://docs.google.com/spreadsheets/d/{sid}"
    return sid, url, True


def prepare_monthly_act(
    month: str,
    *,
    cfg_path: Optional[Path] = None,
    dry_run: bool = False,
    force: bool = False,
    create_if_missing: bool = True,
    expenses_only: bool = False,
) -> TimeReportResult:
    """End-to-end: Tempo bill → aggregate → local draft → Sheets create/fill.

    With ``expenses_tab`` configured, also writes the expenses tab from
    ``docs/acts/YYYY-MM/expenses.csv`` (a separate act). ``expenses_only`` skips
    the month tab so the expenses act can be filed after the hours act.
    """
    tr_cfg = load_time_report_config(cfg_path)
    d0, d1 = month_bounds(month)
    tab_title = ua_tab_title(d0)
    warnings: list[str] = []

    exp_cfg = tr_cfg.get("expenses_tab") or {}
    exp_title = expenses_tab_title(tr_cfg, d0) if exp_cfg else ""
    exp_csv = ACTS_DIR / month / EXPENSES_CSV_NAME
    expenses: list[ExpenseRow] = []
    if exp_cfg:
        ensure_expenses_csv(exp_csv)
        expenses = load_expenses_csv(exp_csv)
        if not expenses:
            warnings.append(
                f"expenses: {exp_csv.relative_to(ROOT)} has no rows — tab '{exp_title}' not written"
            )
    elif expenses_only:
        raise ValueError("--expenses-only needs \"expenses_tab\" in config/time-report.json")

    integ = load_config(require=("tempo",))
    tempo = TempoClient.from_config(integ)

    project_id = str(tr_cfg.get("tempo_project_id") or "").strip() or None
    worklogs = list(
        tempo.worklogs(
            from_date=d0.isoformat(),
            to_date=d1.isoformat(),
            project_id=project_id,
        )
    )

    project_key = str(tr_cfg.get("jira_project_key") or "MIT")
    issues = _load_jira_issue_index(project_key)
    if not issues:
        warnings.append(
            f"Jira registry empty for {project_key} — run: jira sync-pull. "
            "Work titles will fall back to Tempo descriptions."
        )

    rows, agg_warnings = aggregate_bill_rows(worklogs, cfg=tr_cfg, issues_by_id=issues)
    warnings.extend(agg_warnings)

    sid = (tr_cfg.get("spreadsheet_id") or "").strip()
    url = f"https://docs.google.com/spreadsheets/d/{sid}" if sid else ""
    created_ss = False
    tab_created = False
    sheet_title = tab_title

    if dry_run and sid:
        warnings.append("dry_run: skipped Google Sheets write (using config spreadsheet_id)")
    else:
        # Need Google for discovery/create/fill (also when dry_run without spreadsheet_id)
        integ_g = load_config(require=("google",))
        google = GoogleWorkspaceClient.from_config(integ_g)
        sid, url, created_ss = find_or_create_spreadsheet(
            google,
            tr_cfg,
            year=d0.year,
            create_if_missing=create_if_missing,
            dry_run=dry_run,
        )
        if dry_run:
            warnings.append("dry_run: skipped Google Sheets write")
        elif sid != "DRY_RUN_NEW":
            if not expenses_only:
                # Tab match strips spaces — some tabs have leading space.
                sheet_title, tab_created = _write_tab(
                    google,
                    sid,
                    tab_title,
                    force=force,
                    allow_overwrite=bool(tr_cfg.get("overwrite_month_tab")),
                )
                compact = is_compact_layout(tr_cfg)
                values = build_compact_sheet_values(rows) if compact else build_sheet_values(rows)
                google.write_sheet_values(sid, f"'{sheet_title}'!A1", values)
                role_count = len({r.role for r in rows})
                apply_month_tab_formatting(
                    google,
                    sid,
                    sheet_title,
                    data_row_count=len(rows),
                    role_count=role_count,
                    compact=compact,
                )
            if expenses:
                exp_title, _ = _write_tab(
                    google,
                    sid,
                    exp_title,
                    force=force,
                    allow_overwrite=bool(exp_cfg.get("overwrite")),
                )
                google.write_sheet_values(
                    sid, f"'{exp_title}'!A1", build_expenses_sheet_values(expenses)
                )
                google.batch_update_spreadsheet(
                    sid,
                    build_expenses_tab_format_requests(
                        google.get_sheet_id(sid, exp_title), data_row_count=len(expenses)
                    ),
                )

    totals_by_role: dict[str, dict[str, float]] = defaultdict(lambda: {"hours": 0.0, "cost": 0.0})
    for r in rows:
        totals_by_role[r.role]["hours"] += r.hours
        totals_by_role[r.role]["cost"] += r.cost
    totals_by_role = {
        k: {"hours": round(v["hours"], 2), "cost": round(v["cost"], 2)}
        for k, v in totals_by_role.items()
    }

    meta = {
        "month": month,
        "from_date": d0.isoformat(),
        "to_date": d1.isoformat(),
        "tab_title": sheet_title,
        "spreadsheet_id": sid,
        "spreadsheet_url": url,
        "spreadsheet_created": created_ss,
        "tab_created": tab_created,
        "dry_run": dry_run,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "worklog_count": len(worklogs),
        "bill_row_count": len(rows),
        "warnings": warnings,
    }
    local_dir = write_local_pack(month=month, rows=rows, meta=meta)

    return TimeReportResult(
        month=month,
        from_date=d0.isoformat(),
        to_date=d1.isoformat(),
        tab_title=sheet_title,
        spreadsheet_id=sid,
        spreadsheet_url=url,
        spreadsheet_created=created_ss,
        tab_created=tab_created,
        rows=rows,
        totals_by_role={k: dict(v) for k, v in totals_by_role.items()},
        total_hours=round(sum(r.hours for r in rows), 2),
        total_cost=round(sum(r.cost for r in rows), 2),
        local_dir=str(local_dir.relative_to(ROOT)),
        warnings=warnings,
        dry_run=dry_run,
        expenses_tab_title=exp_title,
        expenses=expenses,
        expenses_total=round(sum(e.amount for e in expenses), 2),
    )


def result_to_dict(result: TimeReportResult) -> dict[str, Any]:
    data = asdict(result)
    data["rows"] = [
        {
            "person": r.person,
            "work_title": r.work_title,
            "hours": r.hours,
            "role": r.role,
            "rate": r.rate,
            "cost": r.cost,
        }
        for r in result.rows
    ]
    return data
