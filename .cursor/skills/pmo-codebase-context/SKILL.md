---
name: pmo-codebase-context
description: Links optional application codebase repositories as read-mostly context under knowledge/codebases for scope, tech risks, and estimation. Use when PM/DM need code or README/docs context without treating the app repo as PMO SoT.
---

# Codebase linked repositories (context)

## When to use

- **Ранній крок пайплайну** — разом з BA, одразу після CONTEXT (до charter / tech risks / EWS Technical)
- Потрібен додатковий технічний контекст (README, architecture docs, module map)
- Scope change / acceleration / EWS Technical dimension
- Онбординг ПМ у домен продукту

## Setup

У `config/linked-repos.json`:

```json
{
  "codebase_repos": [{
    "id": "acme-web",
    "path": "../acme-web",
    "ref": "main",
    "sync": "pull",
    "purpose": "context-only",
    "include": ["README.md", "docs/**"],
    "exclude": ["node_modules", "dist", "build"]
  }]
}
```

```bash
python3 scripts/integrations/cli.py repos pull --kind codebase
python3 scripts/integrations/cli.py repos discover --id acme-web
```

Mirror: `knowledge/codebases/{id}/` (gitignored).

## Instructions

1. Pull перед аналізом, якщо mirror застарів.
2. Читай лише релевантні `include` / README / docs — не вантаж увесь monorepo в відповідь.
3. Використовуй для: ризиків Technical, impact CR, оцінок «що вже є в коді».
4. **Не** коміть продуктові зміни з PMO-пайплайну; `repos push` для codebase заборонений за замовчуванням (`sync: pull`).
5. Факти delivery (статус, scope baseline) лишаються в `CONTEXT.md` / `docs/` / Jira — код лише контекст.

## Rules

1. Codebase = optional context, не SoT PMO.
2. Секрети з app `.env` не копіюй у PMO-репо.
3. Великі бінарники / `node_modules` — у `exclude`.

## Related

- `pmo-ba-repos` · `pmo-analyze-scope-change` · `pmo-generate-ews-report`
- Config: `config/linked-repos.json`
