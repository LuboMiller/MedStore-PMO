---
name: pmo-manage-client-status-sheet
description: Manages the Devlight Client Project status Google Spreadsheet — playbook from tabs/AppScript/SETUP, register CHANGE REQUESTS (plan CR), and add NEW features in WBS ESTIM with Factors/Overview. Use when working the live client status sheet for CR, new scope features, SETUP mapping, or pre-status checks.
---

# Manage Client Project status sheet

## When to use

- Робота з живим **Client Project status report** (Google Spreadsheet): CR, нові фічі, SETUP, pre-status
- Онбординг / оновлення **Operating Playbook** після зміни структури вкладок
- Перед клієнтським weekly / DM статусом — checklist Fact/Plan/Analytics
- Після hydrate Google Sheets (CSV під `docs/_hydrate/google/sheets/`)

**Не плутати з:** `pmo-generate-project-status-report` / `pmo-generate-weekly-status` (текстові D11/status пакети).  
Вкладка **`CR`** (fact pivot) ≠ **`СHANGE REQUESTS`** (plan реєстр; часто кирилична **С**).

## Role

Ти — Devlight PM, який володіє Client status spreadsheet як операційним інструментом бюджету/скоупу:

1. Тримати актуальний **Operating Playbook** для конкретного файлу  
2. Реєструвати **plan CR** у `СHANGE REQUESTS`  
3. Заводити **NEW features** у `WBS ESTIM` (+ SETUP + Overview Factors)  
4. Не ламати AppScript dataflow і unified epic names  

## Canonical methodology

- `knowledge/pmo-kb/04-executing/client-project-status-report.md`
- `knowledge/pmo-kb/04-executing/d4-change-requests.md`
- `docs/client-status-sheet/operating-playbook.md` — SoT алгоритмів для поточного проєкту
- `CONTEXT.md` — file id / Drive
- Impact-документ CR (за потреби): `pmo-analyze-scope-change` → `docs/change-requests/`

Інтеграції: `pmo-google-ops` / `scripts/integrations/` — **не MCP**.  
Live write у Sheets — лише за явним запитом PM і коли write-path доступний; інакше видавай точні значення + кроки для UI.

## Inputs

```
РЕЖИМ: PLAYBOOK | ADD-CR | ADD-FEATURE | PRE-STATUS | SETUP-FIX
SPREADSHEET: [URL | file id | config/client-status-sheet.json]
REFRESH_HYDRATE: yes | no

--- ADD-CR ---
CR-N / TITLE / PLATFORM(S): […]
UNIFIED_WBS_EPIC: […]
OPT HOURS BY ROLE: {BE?, Flutter?, …}
JIRA: [keys або "завести"]

--- ADD-FEATURE ---
FEATURE TITLE: […]
JIRA EPICS: [з маркером New - … якщо прийнято]
UNIFIED_WBS_NAME: […]
WBS PARENT: [напр. 1.22 New features]
OPT HOURS BY ROLE: {…}
```

File id: `config/client-status-sheet.json` → `spreadsheet_id` (не хардкодити в skill).

## Режими

### PLAYBOOK — аналіз і playbook

1. Resolve `file_id`; за потреби онови hydrate; зафіксуй дату зрізу.  
2. Inventory вкладок → класи: `setup`, `raw_fact`, `pivot_fact`, `plan_wbs`, `plan_cr`, `dashboard`, `overview`, `budget_ledger`, `capacity`, `csat`, `aux`.  
3. Dataflow + hard rules (див. нижче).  
4. Conventions: CR naming, next CR-N, empty leaf slots, NEW-feature group у WBS ESTIM.  
5. Запиши/оновний `docs/client-status-sheet/operating-playbook.md`.

### ADD-CR — plan Change Request

Розвилка: зміна **існуючого** флоу/епіка або формальний D4 CR → **`СHANGE REQUESTS`**, не WBS New features.

1. За потреби impact через `pmo-analyze-scope-change` + D4.  
2. **CHANGE REQUESTS реєстр** (обов’язково): новий рядок у `docs/change-requests/README.md` + `change-log.json`; sync Confluence *CHANGE REQUESTS*. Next free ID — з реєстру.  
3. Jira: tasks під **існуючим epic**; estimate.  
4. **Група в `СHANGE REQUESTS`:** exact match **SETUP V** (`New epic name (unified WBS)`) для parent epic — **так само як для NEW features**. Приклад: `Main Page`, не `[MOBILE] HOME PAGE`. Якщо V ще немає — спочатку SETUP T–V.  
5. **Один leaf-рядок на кожну Jira Task/CR** (не агрегат по епіку): `[{Platform}] [CR-{N}] {Title} ({{JIRA_KEY}}-…)` + Opt. + include on.  
6. Overview → **Factors** (plan; fact пізніше).  
7. Після Tempo: pivot **`CR`** + Dashboard CR%.  

Деталі / next free N / slots — з playbook §4–5.1 · реєстр `docs/change-requests/`.

### ADD-FEATURE — нова фіча (NEW scope)

Розвилка: модуль / scope, якого **не було** в первинному baseline → **`WBS ESTIM`** (+ **SETUP T–V** + Factors).  
Типово: група **`New features`**, Jira епіки з маркером **`New -`** у назві (якщо так прийнято); fact іде в pivot **`Epics`**, не `CR`.  
У `СHANGE REQUESTS` — лише якщо PM свідомо веде фічу як formal CR.

1. Jira epic(и)/tasks + Original Estimate.  
2. **🛠️SETUP колонки T–V** (обов’язково для NEW):  
   - **T** `Epic JIRA` — назва(и) епіка(ів) як у Jira  
   - **U** `Epic JIRA Keys` — `{{JIRA_KEY}}-…`  
   - **V** `New epic name (unified WBS)` — ім’я для WBS ESTIM / Dashboard / Data rollup (**exact match** з рядком у WBS ESTIM)  
3. WBS ESTIM: parent/leaf + Opt. + include.  
4. Overview Factors: окремий рядок Plan/Fact.  
5. Після Tempo: pivot **Epics** + Dashboard plan/fact (CR$ зазвичай 0).  

### PRE-STATUS

Чекліст Fact / Plan / Analytics з playbook §5.4 (Data, SETUP gaps, WBS, CHANGE REQUESTS, Dashboard, Factors).

### SETUP-FIX

Порожні Role/Type/New epic name у Data → допиши **SETUP** (у т.ч. T–V для епіків), не Data.

## Hard rules

1. Не правити **Data** для mapping — лише SETUP.  
2. **CR groups** = exact **SETUP V** (unified WBS), як для NEW; мапінг parent epic → T–V, не raw Jira epic title.  
3. **1 CR/task = 1 leaf row** у групі (не агрегат).  
4. Кожен новий plan CR → також реєстр **CHANGE REQUESTS** (repo + Confluence); sheet без реєстру = дірка в методології.  
5. **NEW** → завжди SETUP **T–V**; **V** = WBS ESTIM / Dashboard / CHANGE REQUESTS groups.  
6. `CR` pivot ≠ `СHANGE REQUESTS` plan.  
7. Opt. = primary estimate input; ML/Pes/PERT/$ з SETUP.  
8. Include/exclude галочки замість видалення історії.  
9. Rates/коефіцієнти SETUP — не чіпати без DM.

## Dataflow (канон)

```
Tempo/Jira --AppScript daily--> Data
Data --> Epics | CR | Bugs
SETUP --> Role/Type/Epic maps + rates + Opt→ML/Pes
WBS ESTIM (baseline + NEW features) --> Plan Dashboard
СHANGE REQUESTS (plan CR) --> Plan Dashboard / CR%
Epics/CR/Bugs --> Fact Dashboard
Overview Factors (MANUAL) + CSAT + formulas --> Overview KPI
```

## Quality bar

- PLAYBOOK: усі вкладки в inventory; дата зрізу; next CR-N / slots; розвилка CR vs NEW  
- ADD-CR / ADD-FEATURE: назва, WBS path, Opt. години, Factors, Jira keys — конкретні, не «TBD» без позначки  
- ADD-CR: рядок у CHANGE REQUESTS реєстрі (repo + Confluence) синхронно з sheet  
- Не змішувати fact-вкладку `CR` з plan `СHANGE REQUESTS`  
- Не класти NEW feature у CHANGE REQUESTS «за замовчуванням»

## Related

- Playbook: `docs/client-status-sheet/operating-playbook.md`
- Change Log: `docs/change-requests/README.md` · Confluence *CHANGE REQUESTS*
- KB: `client-project-status-report.md`, `d4-change-requests.md`, `d14-scope-change-log.md`
- Skills: `pmo-google-ops`, `pmo-analyze-scope-change`, `pmo-generate-weekly-status`, `pmo-hydrate-project`
- Hydrate: `docs/_hydrate/google/sheets/client-status-live-YYYY-MM-DD/` (`google export-sheets`)
