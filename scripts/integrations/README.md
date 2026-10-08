# PMO integrations — Confluence, Jira, Tempo (REST API, no MCP)

Mandatory layer for the Devlight PMO pipeline. Skills that need live delivery
data **must** go through this package, not ad-hoc curl/MCP.

## Setup

1. Copy `.env.example` → `.env` (repo root).
2. Fill Atlassian + Tempo credentials (see below).
3. Install deps and verify:

```bash
make integrations-check
# or
./scripts/integrations/check.sh
```

## Credentials

| Key | Required | Notes |
|---|---|---|
| `CONFLUENCE_BASE_URL` / `ATLASSIAN_BASE_URL` | ✅ | `https://devlight.atlassian.net` (no `/wiki`) |
| `CONFLUENCE_USERNAME` / `ATLASSIAN_USERNAME` | ✅ | Atlassian email |
| `CONFLUENCE_API_TOKEN` / `ATLASSIAN_API_TOKEN` | ✅ | [Atlassian API token](https://id.atlassian.com/manage-profile/security/api-tokens) |
| `CONFLUENCE_DEFAULT_SPACE` | ✅ | Default `PMO` |
| `JIRA_BASE_URL` / `JIRA_USERNAME` / `JIRA_API_TOKEN` | optional | If omitted, reuse Confluence/Atlassian keys |
| `JIRA_PROJECT_KEY` | ✅ for Jira | e.g. `ACME` |
| `TEMPO_API_TOKEN` | ✅ for Tempo | Tempo → Settings → **API integration** (Bearer). **Not** the Atlassian token |
| `TEMPO_BASE_URL` | optional | default `https://api.tempo.io/4` |
| `GOOGLE_APPLICATION_CREDENTIALS` | optional | Service account JSON path (Drive/Docs) |
| `GOOGLE_DRIVE_FOLDER_ID` | optional | Project Drive folder |
| `GOOGLE_DELEGATED_USER` | optional | Domain-wide delegation subject email |
| `FIREFLIES_API_KEY` | optional | Fireflies → Integrations → Fireflies API |
| `FIREFLIES_KEYWORD` | optional | Default keyword filter for `sync-pull` (e.g. project name) |
| `FIREFLIES_DOWNLOAD_AUDIO` | optional | `1` (default) download `audio.mp3`; `0` to skip |

## CLI

```bash
python3 scripts/integrations/cli.py health

# Model orchestrator (no API keys) — Cursor / Claude Code / Codex / VS Code
python3 scripts/integrations/cli.py models recommend --task "Зроби EWS"
python3 scripts/integrations/cli.py models recommend --task "Зроби EWS" --env codex --json  # → agent/model/action
python3 scripts/integrations/cli.py models policy

# Catch up local repo from existing Atlassian project
python3 scripts/integrations/cli.py project hydrate --jira-key KEY --space SPACE

python3 scripts/integrations/cli.py confluence ping
python3 scripts/integrations/cli.py confluence pages --space PMO
python3 scripts/integrations/cli.py confluence export          # → knowledge/pmo-kb/ (PMO methodology)
python3 scripts/integrations/cli.py confluence sync-pull --space KEY  # → registry + knowledge MD under knowledge/confluence-spaces/KEY/
python3 scripts/integrations/cli.py confluence export-md --space KEY  # rebuild MD from registry

python3 scripts/integrations/cli.py jira myself
python3 scripts/integrations/cli.py jira status-counts
python3 scripts/integrations/cli.py jira search --jql 'project = KEY AND sprint in openSprints()'
python3 scripts/integrations/cli.py jira issue --key KEY-123

python3 scripts/integrations/cli.py tempo ping
python3 scripts/integrations/cli.py tempo worklogs --from 2026-09-01 --to 2026-09-10 --summary

python3 scripts/integrations/cli.py google ping                # needs GOOGLE_* 
python3 scripts/integrations/cli.py google sync-pull

python3 scripts/integrations/cli.py google contracts-status --write   # SOW/stage deadlines → docs/contracts/

python3 scripts/integrations/cli.py fireflies ping             # needs FIREFLIES_API_KEY
python3 scripts/integrations/cli.py fireflies sync-pull        # → docs/meeting-notes/ + registry/fireflies/
```

## Package layout

```
scripts/integrations/
  cli.py
  check.sh
  requirements.txt
  pmo_integrations/
    config.py              # .env loader + validation
    http.py                # sessions / errors
    confluence.py          # spaces + pages (create/update/upsert)
    confluence_company.py  # Devlight space tree bootstrap
    confluence_sync.py     # registry/confluence bidirectional sync
    jira.py / jira_*       # Cloud REST + agile + bootstrap + sync
    tempo.py / tempo_*     # Tempo Cloud + matrix + sync
    google_workspace.py    # Drive / Docs
    fireflies.py           # GraphQL transcripts
    fireflies_sync.py      # → docs/meeting-notes/ + registry/fireflies/
    health.py              # mandatory + optional probes
```

## Policy

- **Jira / Tempo / Confluence:** read + write + bidirectional registries — see [ROADMAP.md](./ROADMAP.md).
- **Hydrate:** existing Atlassian project → partial local `docs/` + registries (`project hydrate`).
- **Google Workspace:** optional until credentials set; Drive list/export scaffold; Docs/Sheets sync on roadmap; **contracts/SOW** deadlines via `google contracts-status`.
- **Fireflies:** optional — pull transcript MD + summary MD + audio MP3 into `docs/meeting-notes/` (`pmo-fireflies-ops`).
- **No MCP** for these systems — keep automation deterministic for scripts/CI.
- Session start / EWS skills should run `health` when live data is required.

## Jira CLI (wave 1)

```bash
# Bootstrap company project (Scrum + board + Sprint 1 + methodology epic)
python3 scripts/integrations/cli.py jira bootstrap --project ACME --name "Acme Delivery"

# Issues
python3 scripts/integrations/cli.py jira types
python3 scripts/integrations/cli.py jira create --type Story --kind story --epic-num 1 --story-num 1 --summary "Login"
python3 scripts/integrations/cli.py jira transition --key ACME-1 --status "In Progress"
python3 scripts/integrations/cli.py jira assign --key ACME-1 --assignee user@devlight.io
python3 scripts/integrations/cli.py jira filter --jql 'project = ACME AND status = "In Progress"'

# Boards / sprints
python3 scripts/integrations/cli.py jira boards
python3 scripts/integrations/cli.py jira sprint-create --board-id 1 --name "Sprint 2"
python3 scripts/integrations/cli.py jira sprint-start --sprint-id 10 --start 2026-09-10T09:00:00.000Z --end 2026-09-24T17:00:00.000Z
python3 scripts/integrations/cli.py jira sprint-complete --sprint-id 10

# Registry sync ↔ repo
python3 scripts/integrations/cli.py jira sync-pull
python3 scripts/integrations/cli.py jira registry-edit --key ACME-1 --status "In Review"
python3 scripts/integrations/cli.py jira sync-push
```

Company template: `config/jira-company-template.json`  
Skills: `pmo-jira-ops`, `pmo-tempo-ops`, `pmo-confluence-ops`  
Registries: `registry/jira/`, `registry/tempo/`, `registry/confluence/`

## Tempo CLI (wave 2)

```bash
# Fact + bill worklog
python3 scripts/integrations/cli.py tempo log \
  --issue-id 10001 --date 2026-09-10 --hours 3 --bill-hours 2

# Plan allocation (hours per day)
python3 scripts/integrations/cli.py tempo plan \
  --account-id ACCOUNT --start 2026-09-10 --end 2026-09-12 --hours 4 --issue-id 10001

# Planning matrix + overlaps
python3 scripts/integrations/cli.py tempo matrix --from 2026-09-01 --to 2026-09-14
python3 scripts/integrations/cli.py tempo overlaps --from 2026-09-01 --to 2026-09-14 --capacity-hours 8

# Registry
python3 scripts/integrations/cli.py tempo sync-pull --from 2026-09-01 --to 2026-09-14
python3 scripts/integrations/cli.py tempo plan-draft … / log-draft …
python3 scripts/integrations/cli.py tempo sync-push
```

## Confluence CLI (wave 3)

```bash
# Bootstrap project space + Devlight phase tree
python3 scripts/integrations/cli.py confluence bootstrap \
  --space ACME --name "Acme Delivery" --jira-key ACME --pm "…" --dm "…"

# Pages
python3 scripts/integrations/cli.py confluence page-upsert \
  --space ACME --title "B1 · Project Charter" --body-md "# Charter\n…"
python3 scripts/integrations/cli.py confluence page-create \
  --space ACME --title "Notes" --parent-title "03 · Executing" --file ./notes.md

# Registry sync ↔ repo
python3 scripts/integrations/cli.py confluence sync-pull --space ACME
python3 scripts/integrations/cli.py confluence registry-edit --space ACME --title "B1 · Project Charter" --body-md "…"
python3 scripts/integrations/cli.py confluence sync-push --space ACME

# Corporate PMO KB → knowledge/pmo-kb/
python3 scripts/integrations/cli.py confluence export --space PMO
```

Company template: `config/confluence-space-template.json`  
Skill: `pmo-confluence-ops` · Registry: `registry/confluence/`

## Project hydrate (wave 3.5)

When Jira/Confluence already contain the delivery project:

```bash
python3 scripts/integrations/cli.py project hydrate --jira-key ACME --space ACME
# → registry sync + CONTEXT hints + mapped stubs + docs/_hydrate/FROM_SYSTEMS.md
```

Map: `config/artifact-source-map.json` · Skill: `pmo-hydrate-project`

## Google Workspace (wave 4)

```bash
pip install -r scripts/integrations/requirements-google.txt
# One-shot (recommended): Drive write + Sheets + Gmail — consent once; refresh is silent.
python3 scripts/integrations/cli.py google auth
# Or add scopes explicitly (existing token scopes are preserved / not wiped):
python3 scripts/integrations/cli.py google auth --gmail
python3 scripts/integrations/cli.py google auth --sheets --write-scope
python3 scripts/integrations/cli.py google ping
python3 scripts/integrations/cli.py google list
python3 scripts/integrations/cli.py google sync-pull
python3 scripts/integrations/cli.py google export-sheets   # needs Sheets scope
python3 scripts/integrations/cli.py google export-doc --file-id ID --out ./export.txt

# Inspect / attach Gmail Settings signature on drafts
python3 scripts/integrations/cli.py google gmail-signature
python3 scripts/integrations/cli.py google gmail-draft \
  --file docs/weekly-status/YYYY-MM-DD/email.md --dry-run
python3 scripts/integrations/cli.py google gmail-draft \
  --file docs/weekly-status/YYYY-MM-DD/email.md

# Monthly T&M act — Tempo bill → Time Report sheet tab (creates spreadsheet if missing)
python3 scripts/integrations/cli.py google time-report --month YYYY-MM --dry-run
python3 scripts/integrations/cli.py google time-report --month YYYY-MM
```

Recipients: `--to` / `--cc` or `config/weekly-status-mail.json`.  
Signature: fetched from Gmail Settings (`sendAs`) and appended as HTML (use `--no-signature` to skip).  
Skill: `pmo-google-ops` · monthly act: `pmo-prepare-monthly-act` · contracts: `docs/contracts/` · Registry: `registry/google/` · drafts: `registry/google/gmail-drafts/` · packs: `docs/weekly-status/{YYYY-MM-DD}/` · acts: `docs/acts/{YYYY-MM}/`

## Setup wizard

```bash
make setup                          # interactive
make setup-status                   # diagnose missing pieces
python3 scripts/integrations/cli.py setup wizard --yes --export-kb   # non-interactive
```

Skill: `pmo-setup-wizard` · Status file: `docs/_hydrate/SETUP_STATUS.md`

## Linked repos — BA + codebases (wave 5)

Optional dependencies declared in `config/linked-repos.json` (see `linked-repos.example.json`).

BA is a **maintained dependency** of the PMO pipeline when `ba_repos` is set: pull → discover (`agent_mode` / `read_order`) → edit mirror → push. Discover understands both Cursor `SKILL.md` and BA `CLAUDE.md` + `docs/ba/prompts` + rules.

```bash
python3 scripts/integrations/cli.py repos list
python3 scripts/integrations/cli.py repos pull --kind ba
python3 scripts/integrations/cli.py repos pull --kind codebase
python3 scripts/integrations/cli.py repos discover --id acme-ba
python3 scripts/integrations/cli.py repos push --id acme-ba --dry-run   # BA only when sync allows
```

Mirrors (gitignored): `knowledge/ba/`, `knowledge/codebases/`  
Skills: `pmo-ba-repos`, `pmo-codebase-context` · Playbook: `docs/pm-playbook.md`

