"""Jira Software (Agile) REST API — boards and sprints."""

from __future__ import annotations

from typing import Iterator, Optional

from .config import Config
from .http import basic_session, get_json, post_json, put_json
from .jira import JiraClient


class JiraAgileClient:
    def __init__(self, base_url: str, username: str, api_token: str):
        self.base_url = base_url.rstrip("/")
        self.session = basic_session(username, api_token)

    @classmethod
    def from_config(cls, cfg: Config) -> "JiraAgileClient":
        return cls(cfg.atlassian_base_url, cfg.atlassian_username, cfg.atlassian_api_token)

    @classmethod
    def from_jira(cls, jira: JiraClient) -> "JiraAgileClient":
        return cls(jira.base_url, "", "")  # unused — prefer from_config

    def _url(self, path: str) -> str:
        return f"{self.base_url}/rest/agile/1.0{path}"

    # ---- boards ----

    def list_boards(self, *, project_key: Optional[str] = None, name: Optional[str] = None) -> list[dict]:
        params: dict = {"maxResults": 50}
        if project_key:
            params["projectKeyOrId"] = project_key
        if name:
            params["name"] = name
        data = get_json(self.session, self._url("/board"), service="jira-agile", params=params)
        return data.get("values") or []

    def create_board(
        self,
        *,
        name: str,
        project_key: str,
        board_type: str = "scrum",
        filter_id: Optional[int] = None,
    ) -> dict:
        """Create a board. Prefer filter_id if provided; else Jira may require existing filter.

        For team-managed projects, board often comes with the template — then use list_boards.
        """
        payload: dict = {
            "name": name,
            "type": board_type,  # scrum | kanban
        }
        if filter_id:
            payload["filterId"] = filter_id
        else:
            # location-based create (supported on many Cloud sites)
            payload["location"] = {"type": "project", "projectKeyOrId": project_key}
        return post_json(self.session, self._url("/board"), service="jira-agile", payload=payload)

    def get_board_configuration(self, board_id: int) -> dict:
        return get_json(
            self.session,
            self._url(f"/board/{board_id}/configuration"),
            service="jira-agile",
        )

    # ---- sprints ----

    def list_sprints(self, board_id: int, *, state: Optional[str] = None) -> Iterator[dict]:
        start = 0
        while True:
            params: dict = {"startAt": start, "maxResults": 50}
            if state:
                params["state"] = state  # future,active,closed
            data = get_json(
                self.session,
                self._url(f"/board/{board_id}/sprint"),
                service="jira-agile",
                params=params,
            )
            values = data.get("values") or []
            yield from values
            if data.get("isLast", True) or not values:
                break
            start += len(values)

    def create_sprint(
        self,
        *,
        name: str,
        board_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        goal: str = "",
    ) -> dict:
        """Create a future sprint. Dates ISO-8601 e.g. 2026-09-10T09:00:00.000Z"""
        payload: dict = {"name": name, "originBoardId": board_id}
        if start_date:
            payload["startDate"] = start_date
        if end_date:
            payload["endDate"] = end_date
        if goal:
            payload["goal"] = goal
        return post_json(self.session, self._url("/sprint"), service="jira-agile", payload=payload)

    def update_sprint(self, sprint_id: int, fields: dict) -> dict:
        return put_json(
            self.session,
            self._url(f"/sprint/{sprint_id}"),
            service="jira-agile",
            payload=fields,
        )

    def start_sprint(
        self,
        sprint_id: int,
        *,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> dict:
        payload: dict = {"state": "active"}
        if start_date:
            payload["startDate"] = start_date
        if end_date:
            payload["endDate"] = end_date
        return self.update_sprint(sprint_id, payload)

    def complete_sprint(self, sprint_id: int) -> dict:
        return self.update_sprint(sprint_id, {"state": "closed"})

    def move_issues_to_sprint(self, sprint_id: int, issue_keys: list[str]) -> None:
        post_json(
            self.session,
            self._url(f"/sprint/{sprint_id}/issue"),
            service="jira-agile",
            payload={"issues": issue_keys},
        )

    def board_issues(self, board_id: int, *, jql: Optional[str] = None) -> Iterator[dict]:
        start = 0
        while True:
            params: dict = {"startAt": start, "maxResults": 50}
            if jql:
                params["jql"] = jql
            data = get_json(
                self.session,
                self._url(f"/board/{board_id}/issue"),
                service="jira-agile",
                params=params,
            )
            issues = data.get("issues") or []
            yield from issues
            if start + len(issues) >= data.get("total", 0) or not issues:
                break
            start += len(issues)
