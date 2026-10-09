# Apps Script — task-level WBS lookup (MedStore)

## Навіщо

`Data!E` раніше отримував **parent Epic** (`[DISCOVERY]`). SETUP тепер мапить **Task JIRA → WBS name**, тому скрипт має писати **summary задачі** (для Sub-task — summary батьківської Task).

## Статус

Застосовано в bound-проєкті **PM Report** (`1n9R__4phM4Vv5EhRS2-twigwTIa47Z7Osy7QpxDq89c8UDoTo3j-YCxx`): `getJiraIssuesByIds` пише `wbsName` (Task summary / parent Task для Sub-task), імпорт Data кладе це в колонку E (`Task JIRA`).

## Як вставити (якщо знову руками)

1. Відкрий spreadsheet → **Extensions → Apps Script** → **PM Report**
2. У `getJiraIssuesByIds` / циклі імпорту Data замість `epicName` у колонку E
3. Збережи → Run імпорт Data → перевір `Data!E` і `Data!H`

## Хелпер (вставити в той самий `.gs`)

```javascript
/**
 * WBS lookup key for MedStore (task-level mapping in SETUP!U:V).
 * - Sub-task / Sub-bug / Sub-change → parent Task summary
 * - Task / Story / Bug / CR → own summary
 */
function getWbsLookupName_(issue) {
  var fields = issue.fields || {};
  var typeName = (fields.issuetype && fields.issuetype.name) || '';
  var summary = (fields.summary || '').trim();
  var subTypes = { 'Sub-task': 1, 'Sub-bug': 1, 'Sub-change': 1 };

  if (subTypes[typeName] && fields.parent) {
    var parentSummary =
      (fields.parent.fields && fields.parent.fields.summary) ||
      fields.parent.summary ||
      '';
    parentSummary = String(parentSummary).trim();
    if (parentSummary) return parentSummary;
  }
  return summary;
}
```

У циклі імпорту замість:

```javascript
var epicName = /* ... parent epic summary ... */;
row.push(epicName);
```

постав:

```javascript
row.push(getWbsLookupName_(issue));
```

Якщо Jira `getIssue` зараз не тягне `parent.fields.summary` — додай у `fields`:

```text
summary,issuetype,parent,parent.fields.summary
```

(або окремий `getIssue` для parent key).

## Тимчасовий обхід без правки скрипта

Поки AppScript не оновлено, можна перезалити `Data` з репо:

```bash
python3 scripts/integrations/client_status_data_import.py
```

(див. скрипт у `scripts/integrations/`). Після нічного тригера AppScript знову затре колонку E на `[DISCOVERY]` — доки скрипт не пропатчений, тригер краще вимкнути або запускати Python після нього.
