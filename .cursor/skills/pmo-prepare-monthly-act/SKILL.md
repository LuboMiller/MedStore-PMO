---
name: pmo-prepare-monthly-act
description: Builds the monthly T&M act Time Report from Tempo bill hours and Jira summaries, then creates or fills the Google Sheets month tab. Use at month-end billing, when Finance asks for акт робіт, or when the Time Report spreadsheet is missing in Drive.
---

# Prepare monthly act (Time Report)

## When to use

- Кінець звітного місяця — підготовка додатку до акту (перелік робіт)
- Finance / PM просить «акт за {місяць}»
- У Google Drive немає spreadsheet **Time Report** — skill створює його
- Після Tempo bill-закриття періоду

**Не плутати з:** `pmo-manage-client-status-sheet` (бюджет/CR/WBS) · `pmo-generate-weekly-status` (D11) · F2 Final Acceptance (`pmo-closing-pack`).

## Role

Ти — Devlight PM. Джерело годин — **лише Tempo bill**. Гранулярність як у липні/серпні 2026: **ПІБ × назва роботи (Jira summary) × роль × rate**. Пишеш у Google Sheets через REST (не MCP).

## Inputs

```
MONTH: YYYY-MM
FORCE_OVERWRITE: yes | no   # якщо вкладка місяця вже заповнена
DRY_RUN: yes | no
CREATE_IF_MISSING: yes (default)
```

## Prerequisites

```bash
make integrations-check   # tempo + google
# Sheets + Drive write scopes (once):
python3 scripts/integrations/cli.py google auth --sheets --write-scope

# People / rates / spreadsheet id:
# config/time-report.json  (from config/time-report.example.json)
```

Jira registry має бути свіжим для назв робіт:

```bash
python3 scripts/integrations/cli.py jira sync-pull
```

## Commands (canonical)

```bash
# Dry-run: агрегат + локальна чернетка, без write у Sheets
python3 scripts/integrations/cli.py google time-report --month 2026-08 --dry-run

# Create/fill вкладки місяця (і spreadsheet, якщо немає)
python3 scripts/integrations/cli.py google time-report --month 2026-08

# Перезаписати непорожню вкладку
python3 scripts/integrations/cli.py google time-report --month 2026-08 --force
```

## Workflow

1. Прочитай `CONTEXT.md` + `config/time-report.json` + `docs/acts/operating-playbook.md`.
2. За потреби `jira sync-pull` (якщо registry старий).
3. Запусти `google time-report --month YYYY-MM` (спочатку `--dry-run`, якщо PM не просив одразу write).
4. Перевір локальний пакет `docs/acts/YYYY-MM/`:
   - `time-report-draft.md` — totals / preview
   - `time-report-draft.csv`
   - `time-report-meta.json`
5. Відкрий spreadsheet URL з CLI output; звір вкладку `{Місяць} {рік}` (напр. `Серпень 2026`) — таблиця A–G + pivot I–K і візуальний стиль мають збігатись з попередніми місяцями.
6. Якщо CLI попередив про unknown Tempo authors — додай їх у `people` у `config/time-report.json` і перезапусти з `--force`.
7. Коротко в чаті: години / $ / URL / warnings. Не дублюй усі рядки.

## Spreadsheet resolution

1. Якщо в config є `spreadsheet_id` — використати (resolve shortcut → target).
2. Інакше шукати в `dir_key` (default `commercial`) / підпапці `Reports` файли з `name_pattern` («Time Report»), з перевагою назви з роком місяця.
3. Якщо не знайдено і `CREATE_IF_MISSING` — створити `{project} | {year} Time Report` з вкладками `Rates` + місяць, засіяти rates з config.

## Policy

1. REST через `scripts/integrations/` — **не MCP**.
2. Лише **billableSeconds** (bill); fact / non-billable ігноруються.
3. Не overwrite непорожньої вкладки без `--force` / `overwrite_month_tab`.
4. Після запису значень CLI **завжди** застосовує форматування як у липні/серпні 2026 (Nunito/Calibri, borders, `# ,##0.00`, pivot I–K, footer `=SUM`, G=`=D*F`, frozen header) — не покладайся на ручне copy-paste стилів.
5. Секрети лише в `secrets/` + `.env`.
6. Після write — локальний draft у `docs/acts/` лишається audit trail.
7. **Layout changes:** перед правкою `build_sheet_values` / formatting — deep-scan референсну вкладку (`Серпень 2026`) через Sheets API (`includeGridData`): header, data formulas, **footer SUM row**, pivot blank+total, fonts/widths/frozen. Чекліст — `docs/acts/operating-playbook.md`.

## Related

- Playbook: `docs/acts/operating-playbook.md`
- Template: `templates/monthly-act-time-report.md`
- Config: `config/time-report.json` · example `config/time-report.example.json`
- Google ops: `pmo-google-ops` (`google auth --sheets`, `google time-report`)
- Tempo: `pmo-tempo-ops`
- Client budget ledger (опційно після акту): `pmo-manage-client-status-sheet`
