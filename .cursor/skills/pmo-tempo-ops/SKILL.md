---
name: pmo-tempo-ops
description: Operates Tempo Timesheets/Planner via REST — log plan/bill/fact hours, resource planning matrix, overlap detection, and registry/tempo sync. Use for capacity planning, EWS Budget dimension, or timesheet ops.
---

# Tempo operations (plan / bill / fact)

## When to use

- Планування ресурсів на тиждень/спринт
- Логування fact/bill годин
- Пошук оверлапів (людина > capacity/день)
- Підготовка Budget-виміру EWS

## Prerequisites

```bash
# .env — окремий Tempo token (не Atlassian API token)
TEMPO_API_TOKEN=…
TEMPO_BASE_URL=https://api.tempo.io/4

make integrations-check   # tempo ✅
```

Потрібен **issueId** (числовий Jira id), не завжди issue key — візьми з `jira issue --key PROJ-1` → поле `id`.

## Plan / fact / bill

```bash
# PLAN — allocation (години на день у періоді)
python3 scripts/integrations/cli.py tempo plan \
  --account-id ACCOUNT_ID --start 2026-09-10 --end 2026-09-12 \
  --hours 4 --issue-id 10001 --description "Sprint FE"

# FACT + BILL — worklog
python3 scripts/integrations/cli.py tempo log \
  --issue-id 10001 --date 2026-09-10 --hours 3 --bill-hours 2 \
  --description "Implemented login" --account-id ACCOUNT_ID

# Non-billable fact
python3 scripts/integrations/cli.py tempo log \
  --issue-id 10001 --date 2026-09-10 --hours 1 --non-billable
```

## Resource planning & overlaps

```bash
# План vs факт vs bill по людях + дні з оверлапами
python3 scripts/integrations/cli.py tempo matrix \
  --from 2026-09-01 --to 2026-09-14 --capacity-hours 8

# Тільки overlaps (exit 2 якщо є)
python3 scripts/integrations/cli.py tempo overlaps \
  --from 2026-09-01 --to 2026-09-14 --capacity-hours 8
```

Оверлап = у один день `sum(plannedSecondsPerDay)` > capacity (default 8h).

## Registry sync

```bash
python3 scripts/integrations/cli.py tempo sync-pull --from 2026-09-01 --to 2026-09-14
python3 scripts/integrations/cli.py tempo plan-draft …   # local draft
python3 scripts/integrations/cli.py tempo log-draft …
python3 scripts/integrations/cli.py tempo sync-push
python3 scripts/integrations/cli.py tempo sync-push --dry-run
```

Див. `registry/tempo/README.md`.

## Read helpers

```bash
python3 scripts/integrations/cli.py tempo worklogs --from … --to … --summary
python3 scripts/integrations/cli.py tempo plans --from … --to … --summary
```

## Related

- EWS Budget: `pmo-generate-ews-report`
- Jira issue ids: `pmo-jira-ops`
