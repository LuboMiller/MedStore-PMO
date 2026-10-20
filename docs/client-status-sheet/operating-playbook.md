# Operating Playbook — Client Project status sheet

> Алгоритм роботи з Devlight **Client Project status report** (Google Spreadsheet).
> Проєктний file id / URL — у `config/client-status-sheet.json` і CONTEXT §8.
> Скіл: `pmo-manage-client-status-sheet`. Методологія: `knowledge/pmo-kb/04-executing/client-project-status-report.md`.

Шапка після hydrate (`google export-sheets`):

| Поле | Значення |
|---|---|
| Файл | MedStore \| Client Project status report \| Updated 20-10-26 |
| File ID | `1dtRGvD-5IeuXvzN9JGuv-OpO2H4JRsdeyBkWSTmcTuo` (`config/client-status-sheet.json`) |
| URL | https://docs.google.com/spreadsheets/d/1dtRGvD-5IeuXvzN9JGuv-OpO2H4JRsdeyBkWSTmcTuo/edit |
| Drive modifiedTime | 2026-10-20T01:57:07Z |
| Daily live hydrate | `docs/_hydrate/google/sheets/client-status-live-2026-10-20/` (export 2026-10-20) |

> Перед live-операціями онови hydrate. AppScript зазвичай оновлює вкладку Data щодня (ніч / ранок).

---

## 1. Типові вкладки (класи)

Інвентаризуй **конкретний** файл проєкту (назви можуть відрізнятися) і віднеси до класів:

| Клас | Типові назви | Режим |
|---|---|---|
| `budget_ledger` | BUDGET, Monthly budget YYYY | MANUAL / FORMULA + fact |
| `overview` | Overview | FORMULA + **MANUAL Factors** |
| `dashboard` | Scope Dashboard | FORMULA |
| `plan_wbs` | WBS ESTIM | MANUAL (Opt.) |
| `csat` | CSAT log | MANUAL |
| `plan_cr` | **СHANGE REQUESTS** (часто кирилична **С**) | MANUAL |
| `capacity` | RESOURCE PLAN | MANUAL |
| `raw_fact` | Data | **AUTO** AppScript — не правити для mapping |
| `pivot_fact` | Epics, CR, Bugs | AUTO/FORMULA |
| `setup` | SETUP | MANUAL (rates, Role/Type/Epic map) |

Вкладка **`CR`** (fact pivot) ≠ **`СHANGE REQUESTS`** (plan реєстр).

---

## 2. Dataflow

```
Tempo / Jira
    │  AppScript daily
    ▼
  Data  (Bill hours, Full name, Issue Type, Epic, …)
    │  + SETUP maps → Role (unified), Type (unified), New epic name (unified WBS)
    ├──────────────┬──────────────┐
    ▼              ▼              ▼
  Epics           CR            Bugs
    │              │              │
    └──────────────┼──────────────┘
                   ▼
            Scope Dashboard  ◄── WBS ESTIM (plan baseline + NEW)
                   ▲         ◄── СHANGE REQUESTS (plan CR)
                   │
                   ▼
               Overview  ◄── CSAT log
                   ▲
                   └── Factors affecting… (MANUAL)
```

**SETUP** годує: rates ($/h), Opt→ML / Pes, QA/PM/BA коеф., calendar, Full name→Role, Epic JIRA→unified WBS name, Issue Type→unified Type (`Change request` → `CR`).

Не змінюй rates/коефіцієнти без узгодження з DM — перерахується весь plan $.

---

## 3. SETUP mapping (MedStore: **Task → WBS**)

У цьому проєкті rollup іде **по задачах**, не по епіках (усі delivery tasks під `[DISCOVERY]`).

| Col (SETUP) | Поле | Зміст |
|---|---|---|
| **U** | Task JIRA | Summary задачі **як у Jira** (exact match з тим, що AppScript пише в `Data` lookup-колонку) |
| **V** | WBS name (unified) | Ім’я leaf у **WBS ESTIM / Scope Dashboard** — exact match |

`Data` формула: `VLOOKUP(lookup_col; SETUP!U:V; 2; FALSE)`.

**Критично:** lookup-колонка (`Data!E` = Task JIRA) має містити **summary Task**, не parent Epic.

- Патч для Apps Script: `docs/client-status-sheet/appscript-task-lookup-patch.md`
- Обхід / заміна імпорту: `python3 scripts/integrations/client_status_data_import.py`

Поки нічний AppScript знову пише `[DISCOVERY]` — або пропатч скрипт, або вимкни тригер і ганяй Python-імпорт.

**CR / NEW:** група plan-рядка = значення **V** (unified WBS name).

---

## 4. Conventions

### 4.1 CR naming

**Група (`1.x`) у `СHANGE REQUESTS`:** = **SETUP V** (unified WBS) батьківського Epic.

**Leaf (`1.x.y`):**

```
[{Platform}] [CR-{N}] {Title} ({{JIRA_KEY}}-…)
```

Один leaf-рядок на кожну Jira Task/CR (не агрегат по епіку).

### 4.2 WBS у СHANGE REQUESTS

| Рівень | Роль рядка |
|---|---|
| 1 | Корінь |
| 1.x | Група = unified epic name |
| 1.x.y | Leaf — CR item + Opt. години |

Нові leaf’и — вставляти **без порожніх рядків між групами** (інакше WBS-формула дає `.1`).

### 4.3 Оцінка

1. Заповни **Opt.** години по ролях.
2. ML / Pes / PERT і COST рахуються формулами від SETUP — не затирай їх руками без потреби.
3. Галочки include — увімкни leaf у scope.

### 4.4 Next CR-N

Вести в `docs/change-requests/README.md` + `change-log.json`. Не вигадувати номер.

---

## 5. Algorithms

### 5.1 Додати CR (plan)

Розвилка: зміна **існуючого** флоу/епіка → **`СHANGE REQUESTS`**, не WBS New features.

1. **Jira:** Task під існуючим Epic (+ estimate).
2. **CHANGE REQUESTS реєстр** (`docs/change-requests/README.md` + Confluence) — новий CR-ID.
3. **Група** = **SETUP V** для цього Epic.
4. **Impact** за потреби: `pmo-analyze-scope-change` + formal `CR-NN-*.md`.
5. **Один leaf на кожну Task/CR.**
6. **Opt.** години по ролях.
7. **Include** = TRUE.
8. **Overview → Factors** за потреби.
9. Після Tempo: pivot `CR` + Dashboard.

### 5.2 Додати нову фічу (NEW scope)

Модуль, якого **не було** в первинному baseline → **`WBS ESTIM`** (+ SETUP T–V + Factors). Fact іде в pivot **Epics**, не `CR`.

Типова практика: окрема група на кшталт `New features`; Jira епіки з маркером `New -` у назві (якщо так прийнято на проєкті).

1. Jira epic(и)/tasks + Original Estimate.
2. SETUP **T–V**.
3. WBS ESTIM: parent/leaf + Opt. + include.
4. **Не** класти в `СHANGE REQUESTS` за замовчуванням.
5. Overview Factors: окремий рядок Plan/Fact.
6. Після Tempo: pivot **Epics** + Scope Dashboard.

### 5.3 Дозаповнити SETUP mapping

Якщо в Data порожні `Role (unified)` / `Type (unified)` / `New epic name (unified WBS)`:

1. Не редагуй Data.
2. Додай людину / issue type / epic у SETUP.
3. Дочекайся перерахунку / наступного імпорту.

### 5.4 Pre-status / pre-weekly checklist

**Fact**

- [ ] Data оновився
- [ ] Немає порожніх Epic / Role / Type / New epic name у Data
- [ ] Epics / CR / Bugs pivots без дірок по ключових WBS

**Plan**

- [ ] WBS ESTIM актуальний
- [ ] СHANGE REQUESTS покриває всі узгоджені CR
- [ ] Імена епіків = SETUP V

**Analytics**

- [ ] Scope Dashboard: немає необґрунтованих 🔴 Fact≫Plan
- [ ] Overview: Budget% vs Scope%; CR%; Bugs%
- [ ] Factors на Overview синхронні з plan CR / новими фічами

Потім: `pmo-generate-weekly-status` / status report за потреби.

---

## 6. Do-not-touch

- Масове ручне редагування **Data**
- Перейменування unified epic «для краси» без оновлення SETUP + усіх plan-вкладок
- Видалення історичних leaf замість зняття галочки include
- Плутанина вкладок **CR** (fact) і **СHANGE REQUESTS** (plan)
- Зміна ML/Pes/rates «на око» під один CR

## Related

| Що | Де |
|---|---|
| Керування sheet | `pmo-manage-client-status-sheet` |
| Google auth / export | `pmo-google-ops` |
| Impact CR документ | `pmo-analyze-scope-change` · `docs/change-requests/template.md` |
| D4 / ICC | `knowledge/pmo-kb/04-executing/d4-change-requests.md` |
