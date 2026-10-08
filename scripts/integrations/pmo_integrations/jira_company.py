"""Devlight company methodology helpers for Jira bootstrap & ticket naming."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

from .jira import DEVLIGHT_STATUSES, JiraClient
from .jira_agile import JiraAgileClient

ROOT = Path(__file__).resolve().parents[3]
TEMPLATE_PATH = ROOT / "config" / "jira-company-template.json"


def load_company_template() -> dict:
    if TEMPLATE_PATH.exists():
        return json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
    return {
        "project_template_key": "com.pyxis.greenhopper.jira:gh-simplified-agility-scrum",
        "board_type": "scrum",
        "methodology_label": "devlight-pmo",
        "expected_statuses": DEVLIGHT_STATUSES,
        "issue_types": ["Epic", "Story", "Task", "Sub-task", "Bug", "Change Request"],
        "naming": {
            "epic": "[E-{n}] {name}",
            "story": "[US-{epic}.{story}] {name}",
            "task": "[{role}] [US-{epic}] {name}",
            "subtask": "[{role}] [US-{epic}.{story}] {name}",
            "cr": "[CR-{n}] [US-{epic}.{story}] {name}",
        },
    }


def format_summary(kind: str, **kwargs) -> str:
    """Apply Devlight naming pattern. kind: epic|story|task|subtask|cr"""
    tpl = load_company_template()
    pattern = (tpl.get("naming") or {}).get(kind)
    if not pattern:
        return kwargs.get("name", "")
    try:
        return pattern.format(**kwargs)
    except KeyError as e:
        raise ValueError(f"Missing naming field {e} for kind={kind}") from e


def validate_summary(kind: str, summary: str) -> list[str]:
    """Return list of warnings if summary does not match Devlight conventions."""
    warnings = []
    patterns = {
        "epic": re.compile(r"^\[E-\d+\]\s+\S"),
        "story": re.compile(r"^\[US-\d+\.\d+\]\s+\S"),
        "task": re.compile(r"^\[(BA|UX/UI|FE|BE|QA|TL|PM)\]\s+"),
        "subtask": re.compile(r"^\[(BA|UX/UI|FE|BE|QA|TL|PM)\]\s+\[US-\d+\.\d+\]"),
        "cr": re.compile(r"^\[CR-\d+\]\s+\[US-\d+\.\d+\]"),
        "bug": re.compile(r".+"),  # soft
    }
    rx = patterns.get(kind)
    if rx and not rx.search(summary):
        warnings.append(f"Summary may not match Devlight {kind} naming: {summary!r}")
    return warnings


def bootstrap_project(
    jira: JiraClient,
    agile: JiraAgileClient,
    *,
    project_key: str,
    project_name: str,
    create_project: bool = True,
    board_name: Optional[str] = None,
    first_sprint_name: str = "Sprint 1",
    lead: Optional[str] = None,
) -> dict:
    """Create (optional) project + ensure scrum board + first future sprint + methodology label note.

    Custom company workflows cannot be fully installed via public API without admin
    workflow schemes — we record expected statuses and create Agile scaffolding.
    """
    tpl = load_company_template()
    result: dict = {"project_key": project_key.upper(), "steps": []}

    if create_project:
        lead_id = None
        if lead:
            lead_id = jira.find_account_id(lead)
        proj = jira.create_project(
            key=project_key,
            name=project_name,
            project_template_key=tpl.get(
                "project_template_key",
                "com.pyxis.greenhopper.jira:gh-simplified-agility-scrum",
            ),
            lead_account_id=lead_id,
            description=(
                "Devlight PMO bootstrap. Expected statuses: "
                + ", ".join(tpl.get("expected_statuses") or DEVLIGHT_STATUSES)
            ),
        )
        result["project"] = {"key": proj.get("key"), "id": proj.get("id")}
        result["steps"].append("project_created")
        jira.project_key = project_key.upper()
    else:
        result["project"] = jira.get_project(project_key)
        result["steps"].append("project_existing")

    boards = agile.list_boards(project_key=project_key.upper())
    board = boards[0] if boards else None
    if not board:
        try:
            board = agile.create_board(
                name=board_name or f"{project_name} board",
                project_key=project_key.upper(),
                board_type=tpl.get("board_type", "scrum"),
            )
            result["steps"].append("board_created")
        except Exception as e:  # noqa: BLE001
            result["board_error"] = str(e)
            result["steps"].append("board_create_failed")
    else:
        result["steps"].append("board_existing")

    if board:
        result["board"] = {"id": board.get("id"), "name": board.get("name")}
        board_id = int(board["id"])
        sprints = list(agile.list_sprints(board_id, state="future,active"))
        if not sprints:
            sprint = agile.create_sprint(name=first_sprint_name, board_id=board_id, goal="Bootstrap")
            result["sprint"] = sprint
            result["steps"].append("sprint_created")
        else:
            result["sprint"] = sprints[0]
            result["steps"].append("sprint_existing")

        # Seed a methodology epic as documentation anchor (optional soft create)
        try:
            label = tpl.get("methodology_label", "devlight-pmo")
            existing = list(
                jira.search(
                    f'project = "{project_key.upper()}" AND labels = "{label}" AND summary ~ "Methodology"',
                    fields=["summary"],
                )
            )
            if not existing:
                issue = jira.create_issue(
                    summary=format_summary("epic", n=0, name="Technical / Methodology"),
                    issuetype="Epic",
                    project_key=project_key.upper(),
                    description=(
                        "Devlight methodology anchor.\n\n"
                        "Statuses expected: " + ", ".join(tpl.get("expected_statuses") or []) + "\n"
                        "See knowledge/pmo-kb/00-rules/jira-workflow.md and jira-ticket-standards.md"
                    ),
                    labels=[label, "methodology"],
                )
                result["methodology_epic"] = issue.get("key")
                result["steps"].append("methodology_epic_created")
            else:
                result["methodology_epic"] = existing[0].get("key")
                result["steps"].append("methodology_epic_existing")
        except Exception as e:  # noqa: BLE001
            result["methodology_error"] = str(e)

    result["expected_statuses"] = tpl.get("expected_statuses") or DEVLIGHT_STATUSES
    result["issue_types_available"] = [t.get("name") for t in jira.list_issue_types(project_key.upper())]
    return result
