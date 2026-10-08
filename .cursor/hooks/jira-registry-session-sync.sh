#!/usr/bin/env bash
# Cursor sessionStart: refresh registry/jira if stale (>4h by default).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
# Consume hook stdin (JSON)
cat >/dev/null || true
exec python3 scripts/integrations/jira_registry_autosync.py
