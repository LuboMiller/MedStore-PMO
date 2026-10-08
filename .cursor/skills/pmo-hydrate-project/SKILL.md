---
name: pmo-hydrate-project
description: Partially fills the local PMO repo from an existing Jira project and Confluence space (registries, CONTEXT hints, mapped doc stubs). Use when delivery already exists in Atlassian and the repo must catch up — not greenfield-only bootstrap.
---

# Hydrate project from existing systems

## When to use

- Проєкт уже живе в Jira / Confluence, а цей репо порожній або відстає
- PM клонував pipeline і хоче підтягнути фактичний стан
- Перед `pmo-start-project` / weekly rhythm, коли артефакти частково вже в wiki

## Instructions

1. Health: `make integrations-check` (потрібні Confluence + Jira).
2. Запусти hydrate:

```bash
python3 scripts/integrations/cli.py project hydrate \
  --jira-key KEY \
  --space SPACE
```

Опції: `--dry-run`, `--no-seed`, `--no-sync`, `--no-context`, `--force`.

3. Прочитай звіт: `docs/_hydrate/FROM_SYSTEMS.md`.
4. Дозаповни `CONTEXT.md` (клієнт, цілі, бюджет) — hydrate не вигадує бізнес-контекст.
5. Для кожного mapped stub — запусти відповідний skill (не лишай seed як фінальний артефакт).
6. Якщо є Google Drive folder проєкту — див. `pmo-google-ops`.

## What it does

| Крок | Результат |
|---|---|
| Jira project + status counts | метадані + `registry/jira/` sync-pull |
| Confluence space pages | `registry/confluence/` sync-pull |
| Title → local map | `config/artifact-source-map.json` |
| Seed stubs | порожні `docs/*` лише якщо файлу ще немає |
| CONTEXT | блок посилань Jira/Confluence |

## Rules

1. Hydrate ≠ заміна skills / QG.
2. Не overwrite існуючих docs без `--force`.
3. Не плутати корпоративний space `PMO` (методологія) з проєктним space.

## Related

- `pmo-start-project` (шлях B — existing systems)
- `pmo-jira-ops` · `pmo-confluence-ops` · `pmo-google-ops`
