---
name: pmo-integrations-health
description: Verifies mandatory Confluence, Jira, and Tempo REST API integrations (and optional Google Workspace / Fireflies) before live PMO work. Use at session start, before EWS/weekly status from live data, or when API credentials may be broken.
---

# Integrations health

## When to use

- Початок сесії з live-даними (не лише локальний markdown)
- Перед `pmo-generate-ews-report` / `pmo-weekly-rhythm` / sprint status з Jira/Tempo
- Після зміни `.env` або токенів
- Перед `pmo-hydrate-project` / Google Drive ops
- Якщо health ❌ — спочатку `pmo-setup-wizard` / `make setup`

## Instructions

1. З кореня репо виконай:

```bash
make integrations-check
```

або:

```bash
python3 scripts/integrations/cli.py health
```

2. Інтерпретація:
   - ✅ confluence / jira / tempo — можна тягнути live дані
   - ❌ confluence — спочатку полагодь Atlassian token / space (`CONFLUENCE_*`)
   - ❌ jira — додай `JIRA_PROJECT_KEY` (credentials можуть успадковуватись від Confluence)
   - ❌ tempo — окремий `TEMPO_API_TOKEN` з Tempo → Settings → API integration
   - google `skipped` — нормально, доки немає OAuth/SA
   - fireflies `skipped` — нормально, доки немає `FIREFLIES_API_KEY`
   - ⚠️/❌ google / fireflies — credentials або API access

3. Не вигадуй метрики EWS/status, якщо відповідна інтеграція ❌ — або виправ конфіг, або явно працюй у offline-режимі з `docs/` / `dashboards/` і познач обмеження.

## Rules

1. Інтеграції — **через REST API** у `scripts/integrations/` (не MCP).
2. Секрети лише в `.env` / `secrets/` (gitignored).
3. Деталі CLI: `scripts/integrations/README.md`.

## Related

- `pmo-hydrate-project` · `pmo-google-ops` · `pmo-fireflies-ops` · `pmo-weekly-rhythm`
- Export KB: `make export-pmo-kb` / `cli.py confluence export`
