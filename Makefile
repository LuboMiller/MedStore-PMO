.PHONY: export-confluence export-pmo-kb skills-list integrations-check integrations-install repos-pull repos-discover setup setup-status jira-sync jira-sync-if-stale fireflies-sync confluence-project-sync models-policy

integrations-install:
	python3 -m pip install -q -r scripts/integrations/requirements.txt
	python3 -m pip install -q -r scripts/confluence-export/requirements.txt

integrations-check: integrations-install
	python3 scripts/integrations/cli.py health

setup:
	python3 scripts/integrations/cli.py setup wizard

setup-status:
	python3 scripts/integrations/cli.py setup status

repos-pull:
	python3 scripts/integrations/cli.py repos pull

# BA/codebase agent surfaces after pull (REPO_ID from linked-repos.json, e.g. make repos-discover REPO_ID=acme-ba)
repos-discover:
	python3 scripts/integrations/cli.py repos discover --id $(REPO_ID)

# Fireflies → docs/meeting-notes/ (transcript_raw.md + summary.md + audio.mp3)
fireflies-sync:
	python3 scripts/integrations/cli.py fireflies sync-pull

# Project Confluence space → registry JSON + nested markdown (set SPACE=KEY or CONFLUENCE_DEFAULT_SPACE in .env)
confluence-project-sync:
	python3 scripts/integrations/cli.py confluence sync-pull --space $(or $(SPACE),$(shell grep -E '^CONFLUENCE_DEFAULT_SPACE=' .env 2>/dev/null | cut -d= -f2))

# Corporate Devlight PMO methodology → knowledge/pmo-kb/
export-pmo-kb: integrations-install
	python3 scripts/confluence-export/export_pmo.py --space PMO

# Alias (legacy name)
export-confluence: export-pmo-kb

skills-list:
	@ls -1 .cursor/skills 2>/dev/null || echo "(no skills yet)"

models-policy:
	python3 scripts/integrations/cli.py models policy

# Full Jira → registry/jira pull
jira-sync:
	python3 scripts/integrations/cli.py jira sync-pull

# Pull only when last_pull older than JIRA_REGISTRY_STALE_HOURS (default 4)
jira-sync-if-stale:
	python3 scripts/integrations/jira_registry_autosync.py
