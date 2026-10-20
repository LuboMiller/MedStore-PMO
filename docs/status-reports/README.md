# Status reports (CLIENT / TEAM / DECK)

Пакети з `pmo-generate-project-status-report` — **по одній директорії на звітну дату**:

```
docs/status-reports/
  README.md
  {{YYYY-MM-DD}}/
    client-{{YYYY-MM-DD}}.md
    team-{{YYYY-MM-DD}}.md
    deck-{{YYYY-MM-DD}}.md
    qg-consistency-report.md   # опційно
```

Цикли:

| Дата | RAG | Нотатка |
|---|---|---|
| [2026-10-20](2026-10-20/) | 🔴 CRITICAL | Після morning sync; EAC/валюта — умовний QG |

Це **не** стандартний щотижневий пакет. Використовувати директорію лише для
окремої потреби у CLIENT / TEAM / DECK варіантах або додаткового зрізу.

Клієнтський D11 cover + Confluence wiki-тіло — у `docs/weekly-status/{{YYYY-MM-DD}}/`
(див. `docs/weekly-status/README.md`). Файли зі звичайного weekly-пакета сюди не
дублювати.
