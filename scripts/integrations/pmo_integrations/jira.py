"""Jira Cloud REST client — read + write for PMO (issues, projects, transitions).

Agile boards/sprints: see `jira_agile.py`.
Registry sync: see `jira_sync.py`.
Company naming/bootstrap: see `jira_company.py`.
"""

from __future__ import annotations

from typing import Any, Iterator, List, Optional

from .config import Config
from .http import ApiError, basic_session, get_json, post_json, put_json

DEFAULT_FIELDS: List[str] = [
    "summary",
    "status",
    "issuetype",
    "labels",
    "parent",
    "updated",
    "created",
    "description",
    "assignee",
    "reporter",
    "priority",
    "resolution",
    "timetracking",
    "timeoriginalestimate",
    "timespent",
    "customfield_10016",
    "sprint",
    "comment",
]

# Devlight-oriented status names (company workflow). Matching is case-insensitive.
DEVLIGHT_STATUSES = [
    "Backlog",
    "To Do",
    "In Progress",
    "In Review",
    "To Test",
    "Testing",
    "Done",
    "Ready for Release",
    "Released",
    "Paused",
    "Blocked",
    "Canceled",
]


class JiraClient:
    def __init__(self, base_url: str, username: str, api_token: str, project_key: str = ""):
        self.base_url = base_url.rstrip("/")
        self.project_key = project_key
        self.session = basic_session(username, api_token)
        self._use_legacy_search = False
        self._account_cache: dict[str, Optional[str]] = {}

    @classmethod
    def from_config(cls, cfg: Config) -> "JiraClient":
        return cls(
            cfg.atlassian_base_url,
            cfg.atlassian_username,
            cfg.atlassian_api_token,
            cfg.jira_project_key,
        )

    def _url(self, path: str) -> str:
        return f"{self.base_url}/rest/api/3{path}"

    # ---- identity / users ----

    def myself(self) -> dict:
        return get_json(self.session, self._url("/myself"), service="jira")

    def find_account_id(self, query: str) -> Optional[str]:
        """Resolve email or display name → accountId (cached)."""
        q = query.strip()
        if q in self._account_cache:
            return self._account_cache[q]
        data = get_json(
            self.session,
            self._url("/user/search"),
            service="jira",
            params={"query": q, "maxResults": 10},
        )
        account_id = None
        if isinstance(data, list) and data:
            for u in data:
                if (u.get("emailAddress") or "").lower() == q.lower():
                    account_id = u.get("accountId")
                    break
            if account_id is None and len(data) == 1:
                account_id = data[0].get("accountId")
        self._account_cache[q] = account_id
        return account_id

    # ---- projects ----

    def get_project(self, key: Optional[str] = None) -> dict:
        key = key or self.project_key
        return get_json(self.session, self._url(f"/project/{key}"), service="jira")

    def create_project(
        self,
        *,
        key: str,
        name: str,
        project_type_key: str = "software",
        project_template_key: str = "com.pyxis.greenhopper.jira:gh-simplified-agility-scrum",
        lead_account_id: Optional[str] = None,
        description: str = "",
    ) -> dict:
        """Create a Jira Cloud software project.

        Requires admin (Create projects). Template defaults to simplified Scrum.
        Company methodology (statuses/naming) is applied via bootstrap after create.
        """
        me = self.myself()
        lead = lead_account_id or me.get("accountId")
        payload = {
            "key": key.upper(),
            "name": name,
            "projectTypeKey": project_type_key,
            "projectTemplateKey": project_template_key,
            "leadAccountId": lead,
            "description": description
            or "Created by PMO pipeline (Devlight methodology bootstrap).",
        }
        return post_json(self.session, self._url("/project"), service="jira", payload=payload)

    def list_issue_types(self, project_key: Optional[str] = None) -> list[dict]:
        key = project_key or self.project_key
        meta = get_json(
            self.session,
            self._url("/issue/createmeta"),
            service="jira",
            params={"projectKeys": key, "expand": "projects.issuetypes"},
        )
        projects = meta.get("projects") or []
        if not projects:
            return []
        return projects[0].get("issuetypes") or []

    # ---- issues read ----

    def get_issue(self, key: str, fields: Optional[List[str]] = None) -> dict:
        params = {"fields": ",".join(fields or DEFAULT_FIELDS)}
        return get_json(self.session, self._url(f"/issue/{key}"), service="jira", params=params)

    def search(self, jql: str, fields: Optional[List[str]] = None) -> Iterator[dict]:
        fields = fields or DEFAULT_FIELDS
        if not self._use_legacy_search:
            yield from self._search_jql(jql, fields)
        else:
            yield from self._search_legacy(jql, fields)

    def _search_jql(self, jql: str, fields: List[str]) -> Iterator[dict]:
        token: Optional[str] = None
        while True:
            payload: dict = {"jql": jql, "maxResults": 100, "fields": fields}
            if token:
                payload["nextPageToken"] = token
            try:
                data = post_json(
                    self.session,
                    self._url("/search/jql"),
                    service="jira",
                    payload=payload,
                )
            except ApiError as e:
                if e.status in (404, 410):
                    self._use_legacy_search = True
                    yield from self._search_legacy(jql, fields)
                    return
                raise
            yield from data.get("issues", [])
            token = data.get("nextPageToken")
            if not token:
                break

    def _search_legacy(self, jql: str, fields: List[str]) -> Iterator[dict]:
        start = 0
        while True:
            data = get_json(
                self.session,
                self._url("/search"),
                service="jira",
                params={
                    "jql": jql,
                    "startAt": start,
                    "maxResults": 100,
                    "fields": ",".join(fields),
                },
            )
            issues = data.get("issues", [])
            yield from issues
            start += len(issues)
            if start >= data.get("total", 0) or not issues:
                break

    def project_issues(self, *, extra_jql: str = "", fields: Optional[List[str]] = None) -> Iterator[dict]:
        if not self.project_key:
            raise RuntimeError("JIRA_PROJECT_KEY is not set")
        jql = f'project = "{self.project_key}"'
        if extra_jql:
            jql = f"{jql} AND ({extra_jql})"
        jql += " ORDER BY updated DESC"
        yield from self.search(jql, fields=fields)

    def active_sprint_issues(self) -> Iterator[dict]:
        return self.project_issues(extra_jql="sprint in openSprints() OR statusCategory != Done")

    def status_counts(self, *, max_issues: int = 500) -> dict[str, int]:
        counts: dict[str, int] = {}
        for i, issue in enumerate(self.project_issues()):
            if i >= max_issues:
                break
            status = (issue.get("fields") or {}).get("status", {}).get("name", "?")
            counts[status] = counts.get(status, 0) + 1
        return counts

    # ---- issues write ----

    def create_issue(
        self,
        *,
        summary: str,
        issuetype: str,
        project_key: Optional[str] = None,
        description: Optional[str] = None,
        assignee: Optional[str] = None,
        parent_key: Optional[str] = None,
        labels: Optional[List[str]] = None,
        priority: Optional[str] = None,
        extra_fields: Optional[dict] = None,
    ) -> dict:
        """Create Epic / Story / Task / Bug / Sub-task / etc.

        `assignee` may be email or accountId.
        `description` plain text → ADF paragraph.
        """
        key = project_key or self.project_key
        if not key:
            raise RuntimeError("project key required")
        fields: dict[str, Any] = {
            "project": {"key": key},
            "summary": summary,
            "issuetype": {"name": issuetype},
        }
        if description:
            fields["description"] = _plain_to_adf(description)
        if labels:
            fields["labels"] = labels
        if priority:
            fields["priority"] = {"name": priority}
        if parent_key:
            fields["parent"] = {"key": parent_key}
        if assignee:
            if "@" in assignee:
                account_id = self.find_account_id(assignee)
            else:
                # bare accountId or display name
                account_id = assignee if len(assignee) >= 16 and " " not in assignee else self.find_account_id(assignee)
            if not account_id:
                raise RuntimeError(f"Cannot resolve assignee: {assignee}")
            fields["assignee"] = {"accountId": account_id}
        if extra_fields:
            fields.update(extra_fields)
        return post_json(self.session, self._url("/issue"), service="jira", payload={"fields": fields})

    def update_issue(self, key: str, fields: dict) -> None:
        put_json(self.session, self._url(f"/issue/{key}"), service="jira", payload={"fields": fields})

    def assign(self, key: str, assignee: str) -> None:
        account_id = assignee if len(assignee) > 20 else self.find_account_id(assignee)
        if not account_id:
            raise RuntimeError(f"Cannot resolve assignee: {assignee}")
        put_json(
            self.session,
            self._url(f"/issue/{key}/assignee"),
            service="jira",
            payload={"accountId": account_id},
        )

    def get_transitions(self, key: str) -> list[dict]:
        data = get_json(self.session, self._url(f"/issue/{key}/transitions"), service="jira")
        return data.get("transitions") or []

    def transition(self, key: str, status_name: str, *, comment: Optional[str] = None) -> None:
        """Move issue to a status by name (case-insensitive match on available transitions)."""
        target = status_name.strip().lower()
        transitions = self.get_transitions(key)
        match = None
        for t in transitions:
            to_name = ((t.get("to") or {}).get("name") or t.get("name") or "").strip().lower()
            if to_name == target or (t.get("name") or "").strip().lower() == target:
                match = t
                break
        if not match:
            available = ", ".join(
                f"{t.get('name')}→{(t.get('to') or {}).get('name')}" for t in transitions
            )
            raise RuntimeError(
                f"No transition to '{status_name}' for {key}. Available: {available or '(none)'}"
            )
        payload: dict[str, Any] = {"transition": {"id": match["id"]}}
        if comment:
            payload["update"] = {
                "comment": [{"add": {"body": _plain_to_adf(comment)}}]
            }
        post_json(self.session, self._url(f"/issue/{key}/transitions"), service="jira", payload=payload)

    def add_comment(self, key: str, body: str) -> dict:
        return post_json(
            self.session,
            self._url(f"/issue/{key}/comment"),
            service="jira",
            payload={"body": _plain_to_adf(body)},
        )


def _plain_to_adf(text: str) -> dict:
    """Minimal Atlassian Document Format for plain multiline text."""
    paragraphs = []
    for block in (text or "").split("\n"):
        paragraphs.append(
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": block}] if block else [],
            }
        )
    if not paragraphs:
        paragraphs = [{"type": "paragraph", "content": []}]
    return {"type": "doc", "version": 1, "content": paragraphs}
