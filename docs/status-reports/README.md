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
| [2026-11-05](2026-11-05/) | 🟠 AMBER | Прогрес 56%, burn 67%, CPI 84%, SPI 76%, SV 41 дн., Estim. 18.01.2027; STG-01 до 30.11 (25 дн.); 1.1.8 Пілот стартував |
| [2026-11-02](2026-11-02/) | 🔴 CRITICAL | Прогрес 10% без змін, burn 62%, CPI 16% · + [SoW-готовність від Дмитра](2026-11-02/sow-readiness-yefimenko-2026-11-02.md): 303,4 год, прогноз 480-512 з 448-536 |
| [2026-10-20](2026-10-20/) | 🔴 CRITICAL | Після morning sync; EAC/валюта — умовний QG |

Це **не** стандартний щотижневий пакет. Використовувати директорію лише для
окремої потреби у CLIENT / TEAM / DECK варіантах або додаткового зрізу.

Клієнтський D11 cover + Confluence wiki-тіло — у `docs/weekly-status/{{YYYY-MM-DD}}/`
(див. `docs/weekly-status/README.md`). Файли зі звичайного weekly-пакета сюди не
дублювати.
