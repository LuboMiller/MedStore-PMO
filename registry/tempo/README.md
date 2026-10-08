# Tempo registry

Локальне дзеркало Tempo Timesheets + Planner.

```
registry/tempo/
  index.json
  worklogs/{id}.json      # fact/bill з Tempo
  plans/{id}.json         # plan allocations
  local/
    worklogs/*.json       # drafts → sync-push
    plans/*.json
```

## Семантика годин

| Тип | Де | CLI |
|---|---|---|
| **plan** | Planner `plannedSecondsPerDay` | `tempo plan` / `plan-draft` |
| **fact** | Worklog `timeSpentSeconds` | `tempo log` / `log-draft` |
| **bill** | Worklog `billableSeconds` | `--bill-hours` або `--non-billable` |

## Команди

```bash
python3 scripts/integrations/cli.py tempo sync-pull --from 2026-09-01 --to 2026-09-14
python3 scripts/integrations/cli.py tempo matrix --from 2026-09-01 --to 2026-09-14
python3 scripts/integrations/cli.py tempo overlaps --from 2026-09-01 --to 2026-09-14 --capacity-hours 8

python3 scripts/integrations/cli.py tempo plan-draft --account-id ACC --start 2026-09-10 --end 2026-09-12 --hours 4 --issue-id 10001
python3 scripts/integrations/cli.py tempo log-draft --issue-id 10001 --date 2026-09-10 --hours 3 --bill-hours 2
python3 scripts/integrations/cli.py tempo sync-push
```
