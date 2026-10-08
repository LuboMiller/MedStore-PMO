# Jira registry (local mirror)

Дзеркало Jira-проєкту в репозиторії. Синхронізація **туди й назад** через CLI.

```
registry/jira/
  index.json
  projects/{KEY}/
    project.json
    boards.json
    sprints.json
    issues/{KEY-123}.json
```

## Автосинк (увімкнено за замовчуванням)

| Тригер | Що робить |
|---|---|
| Після `jira assign` / `transition` / `create` / `sprint-add` | Оновлює змінені issue JSON у `registry/jira/` |
| Cursor `sessionStart` (`.cursor/hooks.json`) | Повний `sync-pull`, якщо `last_pull` старший за **4h** |
| `make jira-sync` | Повний pull завжди |
| `make jira-sync-if-stale` | Pull лише якщо stale |

```bash
# Вимкнути автосинк
JIRA_REGISTRY_AUTO_SYNC=0

# Поріг «протухлості» для sessionStart (години)
JIRA_REGISTRY_STALE_HOURS=4
```

## Команди

```bash
# Повний pull з Jira → репо
python3 scripts/integrations/cli.py jira sync-pull
make jira-sync

# Один / кілька тікетів
python3 scripts/integrations/cli.py jira sync-issue --key PROJ-123
python3 scripts/integrations/cli.py jira sync-issue --keys PROJ-123,PROJ-124

# Відправити локальні dirty-зміни → Jira
python3 scripts/integrations/cli.py jira sync-push
python3 scripts/integrations/cli.py jira sync-push --dry-run

# Локально змінити і позначити dirty (потім sync-push)
python3 scripts/integrations/cli.py jira registry-edit --key PROJ-1 --status "In Progress" --assignee user@devlight.io
```

## Конфлікти

Якщо локальний файл `dirty: true` і `jira_updated` на remote змінився — sync **не перезаписує**, пише conflict у звіт. Спочатку розбери вручну.

## Git

JSON у `registry/jira/projects/` **можна комітити** (стан проєкту як код). Не клади секрети.
