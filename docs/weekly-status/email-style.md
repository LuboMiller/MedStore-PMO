# Weekly Status — стиль листа клієнту (проєктний override)

> Опційний override для D11-листа. Якщо цей файл існує, `pmo-generate-weekly-status`
> бере його **замість** `templates/tl-weekly-status-email.md`.
>
> Залиш як є для default, або адаптуй тон / структуру / сталі посилання під клієнта.
> Не клади сюди персональні email-адреси — вони в `config/weekly-status-mail.json`.

## Стиль

| Правило | Значення |
|---|---|
| Аудиторія | PO / клієнтські стейкхолдери з CONTEXT |
| Формат | За замовчуванням — шаблон `templates/tl-weekly-status-email.md` |
| Мова | Українська (якщо клієнт не просив інше) |
| Підпис | Не писати в MD — підставляє Gmail Settings через `gmail-draft` |

## Сталі посилання

Заповни після появи Sheets / Confluence (або тримай в `config/weekly-status-mail.json` → `links`):

| # | Що | URL |
|---|---|---|
| 1 | Confluence Project Status Report | {{CONFLUENCE_STATUS_PAGE_URL}} |
| 2 | Project Timeline | {{TIMELINE_URL}} |
| 3 | Budget Report | {{BUDGET_URL}} |
