# Confluence registry (local mirror)

Дзеркало Confluence space у репозиторії.

```
registry/confluence/
  index.json
  spaces/{KEY}/
    space.json
    pages/{page_id}.json
    by-title/{slug}.json

knowledge/confluence-spaces/{KEY}/   # markdown hierarchy (auto on sync-pull)
  README.md
  _index.json
  {parent}/{child}.md | {parent}/index.md
```

## Команди

```bash
# Space + Devlight project tree
python3 scripts/integrations/cli.py confluence bootstrap \
  --space ACME --name "Acme Delivery" --jira-key ACME --pm "…" --dm "…"

# Pages
python3 scripts/integrations/cli.py confluence page-upsert \
  --space ACME --title "B1 · Project Charter" --body-md "# Charter\n…"

python3 scripts/integrations/cli.py confluence page-create \
  --space ACME --title "Notes" --parent-title "03 · Executing" --file ./notes.md

# Sync ↔ repo (JSON registry + nested markdown)
python3 scripts/integrations/cli.py confluence sync-pull --space ACME
python3 scripts/integrations/cli.py confluence export-md --space ACME
python3 scripts/integrations/cli.py confluence registry-edit --space ACME --title "B1 · Project Charter" --body-md "…"
python3 scripts/integrations/cli.py confluence sync-push --space ACME
```

**Правило пайплайну:** якщо проєкт має Confluence space — `sync-pull` обов’язковий (hydrate + session).  
Markdown у `knowledge/confluence-spaces/{KEY}/` зберігає вкладеність сторінок.

Методологічний PMO space компанії як і раніше: `confluence export` → `knowledge/pmo-kb/`.
