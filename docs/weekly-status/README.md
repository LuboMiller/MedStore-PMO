# Weekly Status (D11) — локальні пакети

Кожен тижневий цикл клієнтського статусу лежить у **окремій директорії** за датою розсилки / зрізу (`YYYY-MM-DD`, зазвичай п’ятниця).

## Layout

```
docs/weekly-status/
  README.md                 ← цей файл
  email-style.md            ← опційний проєктний стиль листа (override)
  {{YYYY-MM-DD}}/
    email.md                ← чернетка листа клієнту (для gmail-draft)
    project-status-report.md← тіло Confluence Project Status Report
    draft.md                ← робочий хаб / внутрішні нотатки (опційно)
    qg-consistency.md       ← результат QG (опційно)
```

## Правила пайплайну

1. **Не** складати нові `email-*.md` / `ws-*.md` / report у корінь `docs/weekly-status/` — лише в `{{YYYY-MM-DD}}/`.
2. `email-style.md` лишається в корені (спільний для всіх тижнів). Якщо файлу немає — default `templates/tl-weekly-status-email.md`.
3. Gmail draft:
   ```bash
   python3 scripts/integrations/cli.py google gmail-draft \
     --file docs/weekly-status/{{YYYY-MM-DD}}/email.md
   ```
4. Skills: `pmo-generate-weekly-status` · `pmo-weekly-rhythm` · `pmo-google-ops` · `pmo-qg-review-status-consistency`.

## Поточні пакети

| Дата | Період звіту | Статус |
|---|---|---|
| | | |
