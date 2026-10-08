"""Bidirectional Jira ↔ local registry sync.

Layout:
  registry/jira/
    README.md
    index.json                 # keys + last sync meta
    projects/{KEY}/project.json
    projects/{KEY}/issues/{KEY-123}.json
    projects/{KEY}/boards.json
    projects/{KEY}/sprints.json

Each issue JSON stores:
  key, id, fields (normalized), jira_updated, local_updated, content_hash, dirty
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .jira import DEFAULT_FIELDS, JiraClient
from .jira_agile import JiraAgileClient

ROOT = Path(__file__).resolve().parents[3]
REGISTRY = ROOT / "registry" / "jira"

SYNC_FIELDS = [
    f
    for f in DEFAULT_FIELDS
    if f
    not in {
        "comment",  # keep issue body lean; comments optional later
    }
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_payload(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _normalize_issue(issue: dict) -> dict:
    fields = issue.get("fields") or {}
    status = (fields.get("status") or {}).get("name")
    issuetype = (fields.get("issuetype") or {}).get("name")
    assignee = fields.get("assignee") or {}
    parent = fields.get("parent") or {}
    priority = (fields.get("priority") or {}).get("name")
    labels = fields.get("labels") or []
    description = fields.get("description")
    # Keep ADF as-is for round-trip; also store plain extract when possible
    return {
        "key": issue.get("key"),
        "id": issue.get("id"),
        "summary": fields.get("summary"),
        "status": status,
        "issuetype": issuetype,
        "assignee_account_id": assignee.get("accountId"),
        "assignee_display": assignee.get("displayName"),
        "parent_key": parent.get("key"),
        "priority": priority,
        "labels": labels,
        "description_adf": description,
        "jira_updated": fields.get("updated"),
        "jira_created": fields.get("created"),
        "raw_fields": {
            k: fields.get(k)
            for k in ("timetracking", "timeoriginalestimate", "timespent", "customfield_10016")
            if k in fields
        },
    }


@dataclass
class SyncReport:
    pulled: int = 0
    pushed: int = 0
    conflicts: int = 0
    skipped: int = 0
    errors: list[str] | None = None

    def as_dict(self) -> dict:
        return {
            "pulled": self.pulled,
            "pushed": self.pushed,
            "conflicts": self.conflicts,
            "skipped": self.skipped,
            "errors": self.errors or [],
        }


class JiraRegistry:
    def __init__(self, project_key: str, root: Path = REGISTRY):
        self.project_key = project_key.upper()
        self.root = root
        self.project_dir = self.root / "projects" / self.project_key
        self.issues_dir = self.project_dir / "issues"

    def ensure_dirs(self) -> None:
        self.issues_dir.mkdir(parents=True, exist_ok=True)
        self.root.mkdir(parents=True, exist_ok=True)

    def issue_path(self, key: str) -> Path:
        return self.issues_dir / f"{key.upper()}.json"

    def load_issue(self, key: str) -> Optional[dict]:
        path = self.issue_path(key)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def save_issue(self, record: dict, *, dirty: bool = False) -> Path:
        self.ensure_dirs()
        key = record["key"]
        core = {k: v for k, v in record.items() if k not in ("dirty", "content_hash", "local_updated")}
        record = {
            **record,
            "dirty": dirty,
            "content_hash": _hash_payload(core),
            "local_updated": _now(),
        }
        path = self.issue_path(key)
        path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return path

    def list_local_keys(self) -> list[str]:
        if not self.issues_dir.exists():
            return []
        return sorted(p.stem for p in self.issues_dir.glob("*.json"))

    def write_index(self, meta: dict) -> None:
        self.ensure_dirs()
        index_path = self.root / "index.json"
        index: dict[str, Any] = {}
        if index_path.exists():
            index = json.loads(index_path.read_text(encoding="utf-8"))
        projects = index.setdefault("projects", {})
        projects[self.project_key] = {
            **meta,
            "issue_count": len(self.list_local_keys()),
            "updated_at": _now(),
        }
        index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def auto_sync_enabled() -> bool:
    """Registry auto-refresh after Jira writes. Default ON; set JIRA_REGISTRY_AUTO_SYNC=0 to disable."""
    raw = (os.environ.get("JIRA_REGISTRY_AUTO_SYNC") or "1").strip().lower()
    return raw not in ("0", "false", "no", "off")


def pull_issue(
    jira: JiraClient,
    issue_key: str,
    *,
    project_key: Optional[str] = None,
    force: bool = False,
) -> dict:
    """Refresh a single issue into registry/jira (respects dirty unless force=True)."""
    key = issue_key.upper().strip()
    proj = (project_key or key.split("-")[0] or jira.project_key).upper()
    reg = JiraRegistry(proj)
    reg.ensure_dirs()
    remote = jira.get_issue(key, fields=SYNC_FIELDS)
    norm = _normalize_issue(remote)
    local = reg.load_issue(key)
    if local and local.get("dirty") and not force:
        if local.get("jira_updated") != norm.get("jira_updated"):
            raise RuntimeError(
                f"conflict {key}: local dirty and remote updated — resolve or pull with force"
            )
        return local
    path = reg.save_issue(norm, dirty=False)
    reg.write_index({"last_issue_pull": _now(), "source": "jira", "last_issue_key": key})
    return {"path": str(path), **norm}


def pull_issues(
    jira: JiraClient,
    issue_keys: list[str],
    *,
    project_key: Optional[str] = None,
) -> SyncReport:
    """Refresh multiple issues into the registry."""
    report = SyncReport(errors=[])
    for key in issue_keys:
        key = key.strip()
        if not key:
            continue
        try:
            pull_issue(jira, key, project_key=project_key)
            report.pulled += 1
        except Exception as e:  # noqa: BLE001
            report.errors.append(f"{key}: {e}")
    return report


def maybe_auto_sync_issues(
    jira: JiraClient,
    issue_keys: list[str] | str,
    *,
    project_key: Optional[str] = None,
    quiet: bool = False,
) -> Optional[SyncReport]:
    """If auto-sync enabled, refresh given keys after a write. Failures are non-fatal."""
    if not auto_sync_enabled():
        return None
    if isinstance(issue_keys, str):
        keys = [issue_keys]
    else:
        keys = list(issue_keys)
    keys = [k for k in keys if k]
    if not keys:
        return None
    report = pull_issues(jira, keys, project_key=project_key)
    if not quiet:
        if report.errors:
            print(
                f"⚠️  registry auto-sync: pulled={report.pulled} errors={report.errors}",
                file=__import__("sys").stderr,
            )
        else:
            print(f"↻ registry auto-sync: {report.pulled} issue(s)", file=__import__("sys").stderr)
    return report


def registry_stale_hours(project_key: str, *, max_age_hours: float = 4.0) -> bool:
    """True if index last_pull is missing or older than max_age_hours."""
    from datetime import datetime, timezone

    index_path = REGISTRY / "index.json"
    if not index_path.exists():
        return True
    try:
        index = json.loads(index_path.read_text(encoding="utf-8"))
        meta = (index.get("projects") or {}).get(project_key.upper()) or {}
        last = meta.get("last_pull")
        if not last:
            return True
        ts = datetime.fromisoformat(last.replace("Z", "+00:00"))
        age_h = (datetime.now(timezone.utc) - ts.astimezone(timezone.utc)).total_seconds() / 3600.0
        return age_h >= max_age_hours
    except Exception:  # noqa: BLE001
        return True


def pull_project_if_stale(
    jira: JiraClient,
    agile: Optional[JiraAgileClient] = None,
    *,
    project_key: Optional[str] = None,
    max_age_hours: float = 4.0,
) -> Optional[SyncReport]:
    """Full sync-pull when registry is older than max_age_hours (for session hooks)."""
    key = (project_key or jira.project_key).upper()
    if not registry_stale_hours(key, max_age_hours=max_age_hours):
        return None
    return pull_project(jira, agile, project_key=key)


def pull_project(
    jira: JiraClient,
    agile: Optional[JiraAgileClient] = None,
    *,
    project_key: Optional[str] = None,
) -> SyncReport:
    key = (project_key or jira.project_key).upper()
    reg = JiraRegistry(key)
    reg.ensure_dirs()
    report = SyncReport(errors=[])

    project = jira.get_project(key)
    (reg.project_dir / "project.json").write_text(
        json.dumps(project, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )

    if agile:
        boards = agile.list_boards(project_key=key)
        (reg.project_dir / "boards.json").write_text(
            json.dumps(boards, ensure_ascii=False, indent=2, default=str) + "\n",
            encoding="utf-8",
        )
        sprints_all = []
        for b in boards:
            try:
                sprints_all.extend(list(agile.list_sprints(int(b["id"]))))
            except Exception as e:  # noqa: BLE001
                report.errors.append(f"sprints board {b.get('id')}: {e}")
        (reg.project_dir / "sprints.json").write_text(
            json.dumps(sprints_all, ensure_ascii=False, indent=2, default=str) + "\n",
            encoding="utf-8",
        )

    for issue in jira.project_issues(fields=SYNC_FIELDS):
        norm = _normalize_issue(issue)
        local = reg.load_issue(norm["key"])
        if local and local.get("dirty"):
            # Local edits pending push — do not clobber
            if local.get("jira_updated") != norm.get("jira_updated"):
                report.conflicts += 1
                report.errors.append(
                    f"conflict {norm['key']}: local dirty and remote updated — resolve manually"
                )
            else:
                report.skipped += 1
            continue
        reg.save_issue(norm, dirty=False)
        report.pulled += 1

    reg.write_index({"last_pull": _now(), "source": "jira"})
    return report


def push_project(jira: JiraClient, *, project_key: Optional[str] = None, dry_run: bool = False) -> SyncReport:
    """Push locally dirty issues to Jira (summary, assignee, labels, status, description)."""
    key = (project_key or jira.project_key).upper()
    reg = JiraRegistry(key)
    report = SyncReport(errors=[])

    for issue_key in reg.list_local_keys():
        local = reg.load_issue(issue_key)
        if not local or not local.get("dirty"):
            report.skipped += 1
            continue
        try:
            remote = jira.get_issue(issue_key, fields=SYNC_FIELDS)
            remote_updated = (remote.get("fields") or {}).get("updated")
            if remote_updated and local.get("jira_updated") and remote_updated != local.get("jira_updated"):
                report.conflicts += 1
                report.errors.append(
                    f"conflict {issue_key}: remote changed since last pull — pull first"
                )
                continue

            fields: dict[str, Any] = {}
            if local.get("summary"):
                fields["summary"] = local["summary"]
            if local.get("labels") is not None:
                fields["labels"] = local["labels"]
            if local.get("priority"):
                fields["priority"] = {"name": local["priority"]}
            if local.get("description_adf") is not None:
                fields["description"] = local["description_adf"]

            if dry_run:
                report.pushed += 1
                continue

            if fields:
                jira.update_issue(issue_key, fields)
            if local.get("assignee_account_id"):
                jira.assign(issue_key, local["assignee_account_id"])
            if local.get("status"):
                current = ((remote.get("fields") or {}).get("status") or {}).get("name")
                if current and current.lower() != str(local["status"]).lower():
                    jira.transition(issue_key, local["status"])

            # refresh from remote
            refreshed = _normalize_issue(jira.get_issue(issue_key, fields=SYNC_FIELDS))
            reg.save_issue(refreshed, dirty=False)
            report.pushed += 1
        except Exception as e:  # noqa: BLE001
            report.errors.append(f"{issue_key}: {e}")

    reg.write_index({"last_push": _now(), "dry_run": dry_run})
    return report


def mark_dirty(project_key: str, issue_key: str, updates: dict) -> dict:
    """Apply local field updates and mark dirty for later push."""
    reg = JiraRegistry(project_key)
    local = reg.load_issue(issue_key)
    if not local:
        raise FileNotFoundError(f"No local registry entry for {issue_key} — run sync pull first")
    local.update(updates)
    reg.save_issue(local, dirty=True)
    return local
