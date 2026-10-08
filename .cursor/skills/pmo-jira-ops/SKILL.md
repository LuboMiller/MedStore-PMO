---
name: pmo-jira-ops
description: Operates Jira via REST (create project/bootstrap Devlight methodology, issues, transitions, assignees, boards/sprints, JQL filters, bidirectional registry sync). Use when managing Jira delivery work or syncing registry/jira.
---

# Jira operations (Devlight)

## When to use

- Створення / bootstrap проєкту за шаблоном компанії
- CRUD задач, статуси, assignees, спринти, дошки
- Фільтрація (JQL)
- Синхронізація `registry/jira/` ↔ Jira

## Prerequisites

```bash
# .env
JIRA_PROJECT_KEY=YOURKEY
# Atlassian token (може збігатися з CONFLUENCE_*)

make integrations-check   # jira має бути ✅
```

Права: Create project (для bootstrap), Browse/Edit issues, Manage sprints.

## Bootstrap (проєкт + методологія)

```bash
python3 scripts/integrations/cli.py jira bootstrap \
  --project ACME --name "Acme Delivery" --assignee you@devlight.io
```

Створює Scrum-проєкт, board, Sprint 1, epic-якір методології.  
Повний кастомний workflow scheme в Cloud API без адмін-схем **не ставиться** — очікувані статуси зафіксовані в `config/jira-company-template.json` і Confluence Rules.

Для вже існуючого проєкту: `--existing-project`.

## Задачі

```bash
# типи проєкту
python3 scripts/integrations/cli.py jira types

# створити з Devlight naming
python3 scripts/integrations/cli.py jira create --type Epic --kind epic --number 1 --summary "Checkout"
python3 scripts/integrations/cli.py jira create --type Story --kind story --epic-num 1 --story-num 1 --summary "Pay by card"
python3 scripts/integrations/cli.py jira create --type Task --kind task --role BE --epic-num 1 --summary "API contract"

python3 scripts/integrations/cli.py jira assign --key ACME-12 --assignee user@devlight.io
python3 scripts/integrations/cli.py jira transitions --key ACME-12
python3 scripts/integrations/cli.py jira transition --key ACME-12 --status "In Progress" --comment "Started"
```

## Boards / sprints

```bash
python3 scripts/integrations/cli.py jira boards
python3 scripts/integrations/cli.py jira board-config --board-id 123
python3 scripts/integrations/cli.py jira sprints --board-id 123
python3 scripts/integrations/cli.py jira sprint-create --board-id 123 --name "Sprint 2" --goal "…"
python3 scripts/integrations/cli.py jira sprint-start --sprint-id 45 --start 2026-09-10T09:00:00.000Z --end 2026-09-24T17:00:00.000Z
python3 scripts/integrations/cli.py jira sprint-add --sprint-id 45 --keys ACME-1,ACME-2
python3 scripts/integrations/cli.py jira sprint-complete --sprint-id 45
```

## Фільтри

```bash
python3 scripts/integrations/cli.py jira filter --jql 'project = ACME AND sprint in openSprints() AND status = "In Progress"'
```

## Registry sync

Автосинк **увімкнено за замовчуванням** (`JIRA_REGISTRY_AUTO_SYNC=1`):
- після `assign` / `transition` / `create` / `sprint-add` — оновлення issue в `registry/jira/`
- Cursor `sessionStart` + `make jira-sync-if-stale` — повний pull якщо `last_pull` > `JIRA_REGISTRY_STALE_HOURS` (default 4)

```bash
python3 scripts/integrations/cli.py jira sync-pull
make jira-sync
python3 scripts/integrations/cli.py jira sync-issue --key ACME-1
python3 scripts/integrations/cli.py jira registry-edit --key ACME-1 --status "In Review"
python3 scripts/integrations/cli.py jira sync-push
python3 scripts/integrations/cli.py jira sync-push --dry-run
```

Див. `registry/jira/README.md`.

## Company sources

- `config/jira-company-template.json`
- `knowledge/pmo-kb/00-rules/jira-workflow.md`
- `knowledge/pmo-kb/00-rules/jira-ticket-standards.md`

## Next waves (not this skill)

- Tempo: plan/bill/actual + resource overlaps → `pmo-tempo-ops` (planned)
- Confluence: space templates + page registry sync → `pmo-confluence-ops` (planned)
