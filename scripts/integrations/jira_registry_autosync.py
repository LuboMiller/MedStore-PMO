#!/usr/bin/env python3
"""Auto-refresh registry/jira when stale (Cursor sessionStart / make).

Default max age: 4 hours (JIRA_REGISTRY_STALE_HOURS).
Disable: JIRA_REGISTRY_AUTO_SYNC=0
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from pmo_integrations.config import load_config  # noqa: E402
from pmo_integrations.jira import JiraClient  # noqa: E402
from pmo_integrations.jira_agile import JiraAgileClient  # noqa: E402
from pmo_integrations.jira_sync import (  # noqa: E402
    auto_sync_enabled,
    pull_project_if_stale,
    registry_stale_hours,
)


def main() -> int:
    # Cursor hooks may pass JSON on stdin — ignore content
    if not sys.stdin.isatty():
        try:
            sys.stdin.read()
        except Exception:  # noqa: BLE001
            pass

    def hook_ok() -> None:
        # sessionStart: empty JSON object (fail-open, no follow-up)
        print("{}")

    if not auto_sync_enabled():
        print("jira registry autosync skipped (disabled)", file=sys.stderr)
        hook_ok()
        return 0

    try:
        cfg = load_config()
        if not cfg.jira_ok:
            print("jira registry autosync skipped (jira not configured)", file=sys.stderr)
            hook_ok()
            return 0
        jira = JiraClient.from_config(cfg)
        agile = JiraAgileClient.from_config(cfg)
        max_age = float(os.environ.get("JIRA_REGISTRY_STALE_HOURS") or "4")
        key = cfg.jira_project_key
        if not registry_stale_hours(key, max_age_hours=max_age):
            print(f"jira registry fresh ({key})", file=sys.stderr)
            hook_ok()
            return 0
        report = pull_project_if_stale(jira, agile, project_key=key, max_age_hours=max_age)
        if report:
            print(
                json.dumps({"synced": True, "project": key, **report.as_dict()}, ensure_ascii=False),
                file=sys.stderr,
            )
        hook_ok()
        return 0
    except Exception as e:  # noqa: BLE001
        print(f"jira registry autosync error: {e}", file=sys.stderr)
        hook_ok()
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
