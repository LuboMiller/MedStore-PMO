#!/usr/bin/env python3
"""Import Tempo billable hours into Client status sheet Data tab (task-level WBS lookup).

MedStore maps SETUP!U (Task JIRA) → V (WBS name). Sub-tasks roll up to parent Task summary.

Usage (from repo root):
  python3 scripts/integrations/client_status_data_import.py
  python3 scripts/integrations/client_status_data_import.py --from 2026-08-01 --to 2026-10-09
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from pmo_integrations.config import load_config
from pmo_integrations.google_workspace import GoogleWorkspaceClient
from pmo_integrations.http import get_json
from pmo_integrations.jira import JiraClient
from pmo_integrations.tempo import TempoClient

SUBTYPES = {"Sub-task", "Sub-bug", "Sub-change"}


def _lookup_name(issue: dict, parents: dict[str, dict]) -> str:
    fields = issue.get("fields") or {}
    itype = ((fields.get("issuetype") or {}).get("name")) or ""
    summary = (fields.get("summary") or "").strip()
    if itype in SUBTYPES:
        parent = fields.get("parent") or {}
        pkey = parent.get("key")
        if pkey and pkey in parents:
            return ((parents[pkey].get("fields") or {}).get("summary") or summary).strip()
        embedded = ((parent.get("fields") or {}).get("summary") or "").strip()
        return embedded or summary
    return summary


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--from", dest="from_date", default="2026-08-01")
    ap.add_argument("--to", dest="to_date", default=None, help="YYYY-MM-DD (default: today)")
    ap.add_argument(
        "--spreadsheet-id",
        default=None,
        help="Override; default from config/client-status-sheet.json",
    )
    args = ap.parse_args()

    from datetime import date

    to_date = args.to_date or date.today().isoformat()

    cfg = load_config()
    g = GoogleWorkspaceClient.from_config(cfg)
    tempo = TempoClient.from_config(cfg)
    jira = JiraClient.from_config(cfg)

    import json

    sheet_cfg = json.loads((ROOT / "config/client-status-sheet.json").read_text(encoding="utf-8"))
    sid = args.spreadsheet_id or sheet_cfg["spreadsheet_id"]
    project_key = cfg.jira_project_key
    if not project_key:
        raise SystemExit("JIRA_PROJECT_KEY not set")

    proj = get_json(jira.session, jira._url(f"/project/{project_key}"), service="jira")
    project_id = str(proj["id"])

    wls = list(tempo.worklogs(from_date=args.from_date, to_date=to_date, project_id=project_id))
    issue_ids = sorted(
        {str((w.get("issue") or {}).get("id")) for w in wls if (w.get("issue") or {}).get("id")}
    )
    issues: dict[str, dict] = {}
    for iid in issue_ids:
        issues[iid] = get_json(
            jira.session,
            jira._url(f"/issue/{iid}"),
            service="jira",
            params={"fields": "summary,issuetype,parent"},
        )

    parent_keys = {
        ((iss.get("fields") or {}).get("parent") or {}).get("key")
        for iss in issues.values()
        if ((iss.get("fields") or {}).get("parent") or {}).get("key")
    }
    parents: dict[str, dict] = {}
    for key in sorted(k for k in parent_keys if k):
        parents[key] = get_json(
            jira.session,
            jira._url(f"/issue/{key}"),
            service="jira",
            params={"fields": "summary,issuetype"},
        )

    name_by_account: dict[str, str] = {}
    for row in g.read_sheet_values(sid, "'🛠️SETUP'!Q2:S80"):
        if len(row) >= 2 and row[0] and row[1]:
            name_by_account[str(row[1])] = str(row[0])

    rows_out: list[list] = []
    for w in sorted(wls, key=lambda x: (x.get("startDate") or "", x.get("tempoWorklogId") or 0)):
        iid = str((w.get("issue") or {}).get("id") or "")
        issue = issues.get(iid)
        if not issue:
            continue
        fields = issue.get("fields") or {}
        itype = ((fields.get("issuetype") or {}).get("name")) or ""
        author = ((w.get("author") or {}).get("accountId")) or ""
        bill_h = round((w.get("billableSeconds") or 0) / 3600, 2)
        full = name_by_account.get(author, author)
        rows_out.append([bill_h, full, author, itype, _lookup_name(issue, parents)])

    g.clear_sheet_values(sid, "'Data'!A2:H1000")
    g.write_sheet_values(sid, "'Data'!E1", [["Task JIRA"]])
    g.write_sheet_values(sid, "'Data'!H1", [["WBS name (unified)"]])

    if rows_out:
        g.write_sheet_values(sid, f"'Data'!A2:E{1 + len(rows_out)}", rows_out)
        formulas = []
        for i in range(len(rows_out)):
            r = i + 2
            formulas.append(
                [
                    f'=IFERROR(VLOOKUP(C{r}; \'🛠️SETUP\'!$R:$S; 2; FALSE); "")',
                    f'=IFERROR(VLOOKUP(D{r}; \'🛠️SETUP\'!X:Y; 2; FALSE); "")',
                    f'=IFERROR(VLOOKUP(E{r}; \'🛠️SETUP\'!U:V; 2; FALSE); "")',
                ]
            )
        g.write_sheet_values(sid, f"'Data'!F2:H{1 + len(formulas)}", formulas)

    mapped = 0
    data = g.read_sheet_values(sid, f"'Data'!E2:H{1 + max(len(rows_out), 1)}")
    for row in data:
        if len(row) >= 4 and row[3]:
            mapped += 1

    print(
        json.dumps(
            {
                "spreadsheet_id": sid,
                "from": args.from_date,
                "to": to_date,
                "worklogs": len(wls),
                "rows_written": len(rows_out),
                "wbs_mapped": mapped,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
