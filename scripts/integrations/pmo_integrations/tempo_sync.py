"""Local Tempo registry — plans + worklogs mirror with pull/push helpers.

Layout:
  registry/tempo/
    index.json
    worklogs/{id}.json
    plans/{id}.json
    local/              # not-yet-pushed drafts
      plans/*.json
      worklogs/*.json
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .tempo import TempoClient

ROOT = Path(__file__).resolve().parents[3]
REGISTRY = ROOT / "registry" / "tempo"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class TempoRegistry:
    def __init__(self, root: Path = REGISTRY):
        self.root = root
        self.worklogs_dir = root / "worklogs"
        self.plans_dir = root / "plans"
        self.local_plans = root / "local" / "plans"
        self.local_worklogs = root / "local" / "worklogs"

    def ensure(self) -> None:
        for d in (
            self.worklogs_dir,
            self.plans_dir,
            self.local_plans,
            self.local_worklogs,
        ):
            d.mkdir(parents=True, exist_ok=True)

    def write_index(self, meta: dict) -> None:
        self.ensure()
        path = self.root / "index.json"
        data: dict[str, Any] = {}
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
        data.update(meta)
        data["updated_at"] = _now()
        data["worklog_count"] = len(list(self.worklogs_dir.glob("*.json")))
        data["plan_count"] = len(list(self.plans_dir.glob("*.json")))
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def pull_period(
    client: TempoClient,
    *,
    from_date: str,
    to_date: str,
    project_id: Optional[str] = None,
    account_ids: Optional[list[str]] = None,
) -> dict:
    """Pull worklogs + plans into registry for a date range."""
    reg = TempoRegistry()
    reg.ensure()

    worklogs = list(
        client.worklogs(from_date=from_date, to_date=to_date, project_id=project_id)
    )
    for wl in worklogs:
        wid = wl.get("tempoWorklogId") or wl.get("id") or wl.get("jiraWorklogId")
        if wid is None:
            continue
        (reg.worklogs_dir / f"{wid}.json").write_text(
            json.dumps(wl, ensure_ascii=False, indent=2, default=str) + "\n",
            encoding="utf-8",
        )

    plans = list(
        client.search_plans(
            from_date=from_date,
            to_date=to_date,
            account_ids=account_ids,
            project_ids=[int(project_id)] if project_id and str(project_id).isdigit() else None,
        )
    )
    for p in plans:
        pid = p.get("id") or p.get("planId")
        if pid is None:
            continue
        (reg.plans_dir / f"{pid}.json").write_text(
            json.dumps(p, ensure_ascii=False, indent=2, default=str) + "\n",
            encoding="utf-8",
        )

    reg.write_index(
        {
            "last_pull": _now(),
            "from": from_date,
            "to": to_date,
            "project_id": project_id,
        }
    )
    return {"worklogs": len(worklogs), "plans": len(plans)}


def save_local_plan(plan: dict, *, slug: Optional[str] = None) -> Path:
    reg = TempoRegistry()
    reg.ensure()
    name = slug or plan.get("id") or _now().replace(":", "").replace("+", "")
    path = reg.local_plans / f"{name}.json"
    plan = {**plan, "dirty": True, "local_updated": _now()}
    path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def save_local_worklog(worklog: dict, *, slug: Optional[str] = None) -> Path:
    reg = TempoRegistry()
    reg.ensure()
    name = slug or worklog.get("id") or _now().replace(":", "").replace("+", "")
    path = reg.local_worklogs / f"{name}.json"
    worklog = {**worklog, "dirty": True, "local_updated": _now()}
    path.write_text(json.dumps(worklog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def push_local(client: TempoClient, *, dry_run: bool = False) -> dict:
    """Push dirty local drafts to Tempo."""
    reg = TempoRegistry()
    reg.ensure()
    created_plans = 0
    created_worklogs = 0
    errors: list[str] = []

    for path in sorted(reg.local_plans.glob("*.json")):
        draft = json.loads(path.read_text(encoding="utf-8"))
        if not draft.get("dirty", True):
            continue
        try:
            if dry_run:
                created_plans += 1
                continue
            result = client.create_plan(
                account_id=draft["account_id"],
                start=draft["start"],
                end=draft["end"],
                planned_seconds_per_day=int(draft["planned_seconds_per_day"]),
                plan_item_type=draft.get("plan_item_type", "ISSUE"),
                plan_item_id=draft.get("plan_item_id"),
                description=draft.get("description", ""),
            )
            pid = result.get("id") or result.get("planId")
            if pid is not None:
                (reg.plans_dir / f"{pid}.json").write_text(
                    json.dumps(result, ensure_ascii=False, indent=2, default=str) + "\n",
                    encoding="utf-8",
                )
            draft["dirty"] = False
            draft["pushed_at"] = _now()
            draft["remote"] = result
            path.write_text(json.dumps(draft, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            created_plans += 1
        except Exception as e:  # noqa: BLE001
            errors.append(f"plan {path.name}: {e}")

    for path in sorted(reg.local_worklogs.glob("*.json")):
        draft = json.loads(path.read_text(encoding="utf-8"))
        if not draft.get("dirty", True):
            continue
        try:
            if dry_run:
                created_worklogs += 1
                continue
            result = client.create_worklog(
                issue_id=draft["issue_id"],
                time_spent_seconds=int(draft["time_spent_seconds"]),
                start_date=draft["start_date"],
                start_time=draft.get("start_time", "09:00:00"),
                billable_seconds=draft.get("billable_seconds"),
                description=draft.get("description", ""),
                author_account_id=draft.get("author_account_id"),
            )
            wid = result.get("tempoWorklogId") or result.get("id")
            if wid is not None:
                (reg.worklogs_dir / f"{wid}.json").write_text(
                    json.dumps(result, ensure_ascii=False, indent=2, default=str) + "\n",
                    encoding="utf-8",
                )
            draft["dirty"] = False
            draft["pushed_at"] = _now()
            draft["remote"] = result
            path.write_text(json.dumps(draft, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            created_worklogs += 1
        except Exception as e:  # noqa: BLE001
            errors.append(f"worklog {path.name}: {e}")

    reg.write_index({"last_push": _now(), "dry_run": dry_run})
    return {
        "plans_pushed": created_plans,
        "worklogs_pushed": created_worklogs,
        "errors": errors,
    }
