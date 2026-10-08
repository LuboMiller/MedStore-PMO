# Operating playbook — місячний акт (Time Report)

> SoT алгоритму для T&M актів. CLI: `google time-report` · skill: `pmo-prepare-monthly-act`.
> Проєктні id / люди / rates — лише в `config/time-report.json` (з `time-report.example.json`).

## Spreadsheet

| Параметр | Значення |
|---|---|
| Назва | `{project_name} \| {year} Time Report` |
| File id | з `config/time-report.json` → `spreadsheet_id` (або CLI створить новий) |
| Drive | key `dir_key` (типово `commercial`) → папка `reports_folder_name` (`Reports`) |
| Config | `config/time-report.json` |

Якщо spreadsheet **немає** — CLI створює файл у `Reports` (або корені `commercial`) з вкладкою `Rates` + місяцем.

## Формат вкладки місяця

| Col | Поле |
|---|---|
| A | # |
| B | ПІБ |
| C | Назва етапу/робіт (Jira summary) |
| D | Кількість годин (bill) |
| E | Роль (Short з Rates) |
| F | Вартість USD/год, без ПДВ |
| G | Вартість USD, без ПДВ |
| I–K | Pivot: роль → SUM годин / SUM вартості (старт з рядка першого data-рядка) |

Назва вкладки: українською `Серпень 2026`, `Вересень 2026`, …

### Візуальний стиль (обовʼязково CLI)

Після `values.update` CLI застосовує `spreadsheets.batchUpdate` (`apply_month_tab_formatting` у `time_report.py`):

- Ширини колонок A–K
- Header A1:G1 — Nunito 11 bold, wrap, borders; C left, D–G center
- Data: A–B Nunito center+borders; C Calibri 12; D/F/G number `# ,##0.00` + borders
- **G** = формула `=D{r}*F{r}` (не hardcoded cost)
- **Footer** одразу під останнім data-рядком: `=SUM(D3:D{n})` і `=SUM(G3:G{n})`, bold + borders
- Pivot I–K: header → порожній 0-рядок → ролі → «Загальний результат»
- `frozenRowCount = 1`
- Числа як float / формула (locale `uk_UA` → кома)

Не форматувати вкладку вручну після fill — наступний `--force` перезапише стиль з коду.

## Джерела даних

| Що | Звідки |
|---|---|
| Години | Tempo **bill** (`billableSeconds`) за календарний місяць, project з config |
| Назва роботи | Jira issue summary з `registry/jira/projects/{{JIRA_KEY}}/issues/` |
| ПІБ + роль | `config/time-report.json` → `people` |
| Rates | config `rates` (і вкладка `Rates` при create) |

## Каденція PM

1. Після закриття Tempo за місяць (зазвичай 1–3 число).
2. `jira sync-pull` (свіжі summary).
3. `google time-report --month YYYY-MM --dry-run` → review `docs/acts/YYYY-MM/`.
4. `google time-report --month YYYY-MM` → fill вкладки.
5. Передати Finance / вкласти в акт.
6. Опційно: рядок «Роботи за {місяць}» у client status BUDGET (`pmo-manage-client-status-sheet`).

## Hard rules

- Не підміняти bill на fact.
- Не overwrite існуючої заповненої вкладки без `--force`.
- Unknown `account_id` з Tempo → додати в `people`, не вигадувати роль «на око» у чаті без запису в config.
