---
name: pmo-confluence-ops
description: Operates Confluence via REST — create project spaces from Devlight templates, create/update/upsert pages, export PMO KB, bidirectional registry sync, and hierarchical markdown mirrors under knowledge/confluence-spaces. Use for project wiki bootstrap or doc mirror sync.
---

# Confluence operations

## When to use

- Bootstrap проєктного Confluence space за шаблоном Devlight
- Create / update / upsert сторінок
- Дзеркало документації в `registry/confluence/`
- Експорт корпоративного PMO KB → `knowledge/pmo-kb/`

## Prerequisites

```bash
# CONFLUENCE_* / ATLASSIAN_* у .env
make integrations-check   # confluence ✅
```

Потрібні права: Create space(s), Add/Edit pages у target space.

## Bootstrap проєктного space

```bash
python3 scripts/integrations/cli.py confluence bootstrap \
  --space ACME \
  --name "Acme Delivery PMO" \
  --jira-key ACME \
  --pm "Name" --dm "Name"
```

Створює space (якщо немає) + homepage + дерево фаз Initiating→Closing з ключовими артефактами.  
Шаблон: `config/confluence-space-template.json`.

Існуючий space: додати `--existing-space`.

## Pages

```bash
python3 scripts/integrations/cli.py confluence page-upsert \
  --space ACME --title "B1 · Project Charter" --body-md "# Charter\n…"

python3 scripts/integrations/cli.py confluence page-create \
  --space ACME --title "Sprint 14 Notes" \
  --parent-title "03 · Executing" --file ./notes.md

python3 scripts/integrations/cli.py confluence page-get --space ACME --title "B1 · Project Charter"
```

`--file` за замовчуванням як markdown; `--storage` якщо файл уже Confluence storage HTML.

## Registry sync (+ markdown hierarchy)

```bash
# JSON registry + nested markdown under knowledge/confluence-spaces/{SPACE}/
python3 scripts/integrations/cli.py confluence sync-pull --space ACME

# Only rebuild markdown from existing registry (no API)
python3 scripts/integrations/cli.py confluence export-md --space ACME

# Re-pull registry then markdown
python3 scripts/integrations/cli.py confluence export-md --space ACME --refresh

python3 scripts/integrations/cli.py confluence registry-edit \
  --space ACME --title "B1 · Project Charter" --body-md "# updated"
python3 scripts/integrations/cli.py confluence sync-push --space ACME
python3 scripts/integrations/cli.py confluence sync-push --space ACME --dry-run
```

Конфлікти: dirty local + remote version↑ → не пушиться, треба pull/resolve.

**Якщо у проєкту є Confluence space — обов’язково тягни його** (hydrate / session start / weekly).  
Markdown mirror зберігає **вкладеність** parent→child як папки (`…/parent/child.md` або `parent/index.md` якщо є діти).

| Шлях | Призначення |
|---|---|
| `registry/confluence/spaces/{KEY}/` | JSON SoT для sync-push (storage HTML) |
| `knowledge/confluence-spaces/{KEY}/` | Читабельний MD зі збереженою ієрархією |
| `knowledge/pmo-kb/` | Лише корпоративний PMO methodology (`export` / `make export-pmo-kb`) |

## Корпоративний PMO KB

```bash
python3 scripts/integrations/cli.py confluence export --space PMO
# → knowledge/pmo-kb/
```

## Related

- Methodology source: `knowledge/pmo-kb/`
- Template: `config/confluence-space-template.json`
- Registry: `registry/confluence/README.md`
