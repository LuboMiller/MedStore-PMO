"""Resource planning helpers: capacity view + overlap detection for Tempo plans."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any, Optional


DEFAULT_CAPACITY_SECONDS = 8 * 3600  # 8h working day


def _parse_day(value: str) -> date:
    return date.fromisoformat(str(value)[:10])


def _daterange(start: date, end: date):
    cur = start
    while cur <= end:
        yield cur
        cur += timedelta(days=1)


@dataclass
class DayLoad:
    day: str
    account_id: str
    planned_seconds: int = 0
    plan_ids: list[Any] = field(default_factory=list)
    items: list[dict] = field(default_factory=list)


@dataclass
class OverlapHit:
    account_id: str
    day: str
    planned_seconds: int
    capacity_seconds: int
    over_seconds: int
    plan_ids: list[Any]
    details: list[dict]


def expand_plans_by_day(plans: list[dict]) -> list[DayLoad]:
    """Flatten plans into per-user per-day loads."""
    loads: dict[tuple[str, str], DayLoad] = {}
    for p in plans:
        account = p.get("accountId") or (p.get("assignee") or {}).get("accountId")
        if not account:
            continue
        start = p.get("start") or p.get("startDate")
        end = p.get("end") or p.get("endDate")
        if not start or not end:
            continue
        per_day = int(p.get("plannedSecondsPerDay") or p.get("plannedPerDaySeconds") or 0)
        if per_day <= 0:
            continue
        plan_id = p.get("id") or p.get("planId") or p.get("self")
        item = {
            "plan_id": plan_id,
            "planItemType": p.get("planItemType"),
            "planItemId": p.get("planItemId"),
            "description": p.get("description"),
            "plannedSecondsPerDay": per_day,
        }
        try:
            d0, d1 = _parse_day(start), _parse_day(end)
        except ValueError:
            continue
        for d in _daterange(d0, d1):
            key = (account, d.isoformat())
            if key not in loads:
                loads[key] = DayLoad(day=d.isoformat(), account_id=account)
            loads[key].planned_seconds += per_day
            loads[key].plan_ids.append(plan_id)
            loads[key].items.append(item)
    return sorted(loads.values(), key=lambda x: (x.account_id, x.day))


def find_overlaps(
    plans: list[dict],
    *,
    capacity_seconds: int = DEFAULT_CAPACITY_SECONDS,
) -> list[OverlapHit]:
    """Days where planned load > capacity for a person."""
    hits: list[OverlapHit] = []
    for load in expand_plans_by_day(plans):
        if load.planned_seconds > capacity_seconds:
            hits.append(
                OverlapHit(
                    account_id=load.account_id,
                    day=load.day,
                    planned_seconds=load.planned_seconds,
                    capacity_seconds=capacity_seconds,
                    over_seconds=load.planned_seconds - capacity_seconds,
                    plan_ids=load.plan_ids,
                    details=load.items,
                )
            )
    return hits


def planning_matrix(
    plans: list[dict],
    worklogs: Optional[list[dict]] = None,
    *,
    capacity_seconds: int = DEFAULT_CAPACITY_SECONDS,
) -> dict[str, Any]:
    """Build plan vs fact vs bill summary + overlap list for a period."""
    by_day = expand_plans_by_day(plans)
    plan_h: dict[str, float] = defaultdict(float)
    for load in by_day:
        plan_h[load.account_id] += load.planned_seconds / 3600.0

    fact_h: dict[str, float] = defaultdict(float)
    bill_h: dict[str, float] = defaultdict(float)
    for wl in worklogs or []:
        author = (wl.get("author") or {}).get("accountId") or wl.get("authorAccountId") or "unknown"
        fact_h[author] += (wl.get("timeSpentSeconds") or 0) / 3600.0
        bill = wl.get("billableSeconds")
        if bill is None:
            bill = wl.get("timeSpentSeconds") or 0
        bill_h[author] += bill / 3600.0

    people = sorted(set(plan_h) | set(fact_h) | set(bill_h))
    rows = []
    for p in people:
        rows.append(
            {
                "account_id": p,
                "plan_h": round(plan_h.get(p, 0.0), 2),
                "fact_h": round(fact_h.get(p, 0.0), 2),
                "bill_h": round(bill_h.get(p, 0.0), 2),
                "delta_plan_fact_h": round(plan_h.get(p, 0.0) - fact_h.get(p, 0.0), 2),
            }
        )

    overlaps = find_overlaps(plans, capacity_seconds=capacity_seconds)
    return {
        "capacity_h_per_day": capacity_seconds / 3600.0,
        "people": rows,
        "overlap_days": [
            {
                "account_id": o.account_id,
                "day": o.day,
                "planned_h": round(o.planned_seconds / 3600.0, 2),
                "capacity_h": round(o.capacity_seconds / 3600.0, 2),
                "over_h": round(o.over_seconds / 3600.0, 2),
                "plan_ids": o.plan_ids,
            }
            for o in overlaps
        ],
        "overlap_count": len(overlaps),
    }


def hours_to_seconds(hours: float) -> int:
    return int(round(float(hours) * 3600))
