"""Tempo Cloud Timesheets + Planner API v4 (Bearer token).

Docs: https://apidocs.tempo.io/ — base https://api.tempo.io/4
Token: Tempo → Settings → API integration (not the Atlassian API token).

PMO semantics:
  - fact   → worklog.timeSpentSeconds
  - bill   → worklog.billableSeconds
  - plan   → Planner plan (plannedSecondsPerDay / plannedSeconds)
"""

from __future__ import annotations

from typing import Any, Iterator, Optional

from .config import Config
from .http import bearer_session, delete, get_json, post_json, put_json


class TempoClient:
    def __init__(self, api_token: str, base_url: str = "https://api.tempo.io/4"):
        self.base_url = base_url.rstrip("/")
        self.session = bearer_session(api_token)

    @classmethod
    def from_config(cls, cfg: Config) -> "TempoClient":
        return cls(cfg.tempo_api_token, cfg.tempo_base_url)

    def _url(self, path: str) -> str:
        if not path.startswith("/"):
            path = "/" + path
        return f"{self.base_url}{path}"

    def ping(self) -> dict:
        return get_json(
            self.session,
            self._url("/worklogs"),
            service="tempo",
            params={"limit": 1, "offset": 0},
        )

    # ---- worklogs (fact / bill) ----

    def worklogs(
        self,
        *,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        project_id: Optional[str] = None,
        issue_id: Optional[str] = None,
        updated_from: Optional[str] = None,
        limit: int = 100,
    ) -> Iterator[dict]:
        offset = 0
        while True:
            params: dict[str, Any] = {"limit": limit, "offset": offset}
            if from_date:
                params["from"] = from_date
            if to_date:
                params["to"] = to_date
            if project_id:
                params["projectId"] = project_id
            if issue_id:
                params["issueId"] = issue_id
            if updated_from:
                params["updatedFrom"] = updated_from
            data = get_json(self.session, self._url("/worklogs"), service="tempo", params=params)
            results = data.get("results") or data.get("worklogs") or []
            if isinstance(data, list):
                results = data
            yield from results
            if len(results) < limit or not results:
                break
            offset += limit

    def worklogs_for_user(
        self,
        account_id: str,
        *,
        from_date: str,
        to_date: str,
        limit: int = 100,
    ) -> Iterator[dict]:
        offset = 0
        while True:
            data = get_json(
                self.session,
                self._url(f"/worklogs/user/{account_id}"),
                service="tempo",
                params={"from": from_date, "to": to_date, "limit": limit, "offset": offset},
            )
            results = data.get("results") or []
            yield from results
            if len(results) < limit:
                break
            offset += limit

    def create_worklog(
        self,
        *,
        issue_id: str | int,
        time_spent_seconds: int,
        start_date: str,
        start_time: str = "09:00:00",
        billable_seconds: Optional[int] = None,
        description: str = "",
        author_account_id: Optional[str] = None,
        remaining_estimate_seconds: Optional[int] = None,
    ) -> dict:
        """Log actual time (fact). Optionally set billable separately.

        If billable_seconds is None → Tempo defaults billable = time spent (typical).
        Set billable_seconds=0 for non-billable.
        """
        payload: dict[str, Any] = {
            "issueId": int(issue_id),
            "timeSpentSeconds": int(time_spent_seconds),
            "startDate": start_date,
            "startTime": start_time,
            "description": description,
        }
        if billable_seconds is not None:
            payload["billableSeconds"] = int(billable_seconds)
        if author_account_id:
            payload["authorAccountId"] = author_account_id
        if remaining_estimate_seconds is not None:
            payload["remainingEstimateSeconds"] = int(remaining_estimate_seconds)
        return post_json(self.session, self._url("/worklogs"), service="tempo", payload=payload)

    def update_worklog(self, tempo_worklog_id: int, fields: dict) -> dict:
        return put_json(
            self.session,
            self._url(f"/worklogs/{tempo_worklog_id}"),
            service="tempo",
            payload=fields,
        )

    def delete_worklog(self, tempo_worklog_id: int) -> None:
        delete(self.session, self._url(f"/worklogs/{tempo_worklog_id}"), service="tempo")

    def timesheet_approval(self, account_id: str, *, from_date: str, to_date: str) -> dict:
        return get_json(
            self.session,
            self._url(f"/timesheet-approvals/user/{account_id}"),
            service="tempo",
            params={"from": from_date, "to": to_date},
        )

    # ---- plans (resource planning) ----

    def search_plans(
        self,
        *,
        from_date: str,
        to_date: str,
        account_ids: Optional[list[str]] = None,
        issue_ids: Optional[list[int]] = None,
        project_ids: Optional[list[int]] = None,
        limit: int = 100,
    ) -> Iterator[dict]:
        """POST /plans/search — Cloud v4."""
        offset = 0
        while True:
            payload: dict[str, Any] = {
                "from": from_date,
                "to": to_date,
                "limit": limit,
                "offset": offset,
            }
            if account_ids:
                payload["accountIds"] = account_ids
            if issue_ids:
                payload["issueIds"] = issue_ids
            if project_ids:
                payload["projectIds"] = project_ids
            data = post_json(
                self.session,
                self._url("/plans/search"),
                service="tempo",
                payload=payload,
            )
            results = data.get("results") or data.get("plans") or []
            if isinstance(data, list):
                results = data
            yield from results
            if len(results) < limit or not results:
                break
            offset += limit

    def create_plan(
        self,
        *,
        account_id: str,
        start: str,
        end: str,
        planned_seconds_per_day: int,
        plan_item_type: str = "ISSUE",
        plan_item_id: Optional[str | int] = None,
        description: str = "",
        include_non_working_days: bool = False,
        start_time: Optional[str] = None,
    ) -> dict:
        """Create a Planner allocation (plan hours).

        plan_item_type: ISSUE | PROJECT (per Tempo Cloud).
        planned_seconds_per_day: e.g. 14400 = 4h/day.
        """
        payload: dict[str, Any] = {
            "accountId": account_id,
            "start": start,
            "end": end,
            "plannedSecondsPerDay": int(planned_seconds_per_day),
            "planItemType": plan_item_type,
            "description": description,
            "includeNonWorkingDays": include_non_working_days,
        }
        if plan_item_id is not None:
            payload["planItemId"] = int(plan_item_id) if str(plan_item_id).isdigit() else plan_item_id
        if start_time:
            payload["startTime"] = start_time
        return post_json(self.session, self._url("/plans"), service="tempo", payload=payload)

    def update_plan(self, plan_id: int, fields: dict) -> dict:
        return put_json(
            self.session,
            self._url(f"/plans/{plan_id}"),
            service="tempo",
            payload=fields,
        )

    def delete_plan(self, plan_id: int) -> None:
        delete(self.session, self._url(f"/plans/{plan_id}"), service="tempo")

    def get_plan(self, plan_id: int) -> dict:
        return get_json(self.session, self._url(f"/plans/{plan_id}"), service="tempo")

    # ---- summaries ----

    def summarize_hours(self, worklogs: list[dict]) -> dict[str, dict[str, float]]:
        """Per author: fact hours + bill hours."""
        by_user: dict[str, dict[str, float]] = {}
        for wl in worklogs:
            author = (wl.get("author") or {}).get("accountId") or wl.get("authorAccountId") or "unknown"
            bucket = by_user.setdefault(author, {"fact_h": 0.0, "bill_h": 0.0})
            bucket["fact_h"] += (wl.get("timeSpentSeconds") or 0) / 3600.0
            bill = wl.get("billableSeconds")
            if bill is None:
                bill = wl.get("timeSpentSeconds") or 0
            bucket["bill_h"] += bill / 3600.0
        return by_user

    def summarize_plans(self, plans: list[dict]) -> dict[str, float]:
        """Approximate total planned hours by accountId (sum plannedSecondsPerDay * day span)."""
        from datetime import date

        by_user: dict[str, float] = {}
        for p in plans:
            account = p.get("accountId") or (p.get("assignee") or {}).get("accountId") or "unknown"
            per_day = p.get("plannedSecondsPerDay") or p.get("plannedPerDaySeconds") or 0
            start = p.get("start") or p.get("startDate")
            end = p.get("end") or p.get("endDate")
            days = 1
            if start and end:
                try:
                    d0 = date.fromisoformat(str(start)[:10])
                    d1 = date.fromisoformat(str(end)[:10])
                    days = max(1, (d1 - d0).days + 1)
                except ValueError:
                    days = 1
            by_user[account] = by_user.get(account, 0.0) + (per_day * days) / 3600.0
        return by_user
