#!/usr/bin/env bash
# Mandatory integrations health check (Confluence, Jira, Tempo).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
python3 -m pip install -q -r scripts/integrations/requirements.txt
exec python3 scripts/integrations/cli.py health
