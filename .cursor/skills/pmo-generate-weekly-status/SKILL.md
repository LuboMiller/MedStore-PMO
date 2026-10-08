---
name: pmo-generate-weekly-status
description: Writes client weekly status with traffic light (Green/Amber/Red), No Surprises rule, and explicit Action Needed. Use every Friday for client reporting per Devlight D11 practice. Accepts optional email writing-style template path; falls back to project then default template.
---

# Генерація Weekly Status Report — Client (D11)

## When to use

- Щоп'ятниці до 17:00 — регулярний статус клієнту (без винятків)
- Коли з'явився Amber/Red і клієнт має дізнатись від PM першим (No Surprises)
- Після оновлення sprint tracker / risk register / CR перед зовнішньою комунікацією

## Role

Ти — PM Devlight. Пишеш клієнтський статус простою мовою, без внутрішнього жаргону (SPI, CPI, назви протоколів). Чесність важливіша за оптимізм.

## Context

За методологією Devlight (D11) Weekly Status — формальний щотижневий звіт PM → клієнт. Це основний регулярний канал видимості стану проєкту для decision maker клієнта. Пропуск тижня різко знижує довіру.

Внутрішній звіт PM→DM (EWS) — **окремий** skill `pmo-generate-ews-report`, не змішувати з клієнтським статусом.

### Email writing-style template (resolve order)

Перед генерацією листа визнач **один** style-файл (перший наявний виграє):

| Пріоритет | Джерело | Шлях |
|---|---|---|
| 1 | Явний шлях від користувача | напр. «стиль з `path/to/style.md`» / `--email-style path` |
| 2 | Проєктний override | `docs/weekly-status/email-style.md` *(якщо файл існує)* |
| 3 | Default репозиторію | `templates/tl-weekly-status-email.md` |

Style-файл задає **тон, мову, довжину, заборонені теми** і **структуру** листа.  
D11 hard rules (Traffic Light, No Surprises, Action Needed, без EWS) залишаються чинними навіть якщо override їх пом’якшує — при конфлікті перемагають Rules нижче.

## Instructions

1. Прочитай `CONTEXT.md`, `dashboards/sprint-tracker.md`, `docs/risk-register.md`, активні CR у `docs/change-requests/`, останні follow-up з `docs/meeting-notes/`. За потреби — Jira/Tempo через CLI.
2. Визнач Traffic Light (🟢/🟡/🔴) за фактами тижня — не «як хочеться виглядати».
3. **Резолвни email style** за таблицею вище; прочитай обраний файл повністю.
4. Згенеруй артефакти:
   - **Email** для decision maker — строго за обраним style (структура + Style-таблиця); ≤ 10 речень у тілі, якщо style не задає інше *коротше* обмеження.
   - **Wiki / розширений статус** (за потреби) — Confluence Project Status Report або `templates/tl-weekly-status-po.md`.
5. Збережи **у директорію тижня** `docs/weekly-status/{{YYYY-MM-DD}}/` (створи, якщо немає):
   - Email → `docs/weekly-status/{{YYYY-MM-DD}}/email.md`  
     (у шапці вкажи `style: <шлях використаного style-файлу>`).
   - Wiki-тіло → `docs/weekly-status/{{YYYY-MM-DD}}/project-status-report.md`  
     (+ Confluence через `pmo-confluence-ops`).
   - Опційно робочий хаб → `docs/weekly-status/{{YYYY-MM-DD}}/draft.md`.
   - **Не** класти нові `email-*.md` / `ws-*.md` / report у корінь `docs/weekly-status/` (там лише `email-style.md` + `README.md`).
   - Опційно паралельний CLIENT/TEAM/DECK → `docs/status-reports/{{YYYY-MM-DD}}/`.
6. **Gmail draft (опційно, якщо Google OAuth з `--gmail` налаштований):**
   ```bash
   python3 scripts/integrations/cli.py google gmail-draft \
     --file docs/weekly-status/{{YYYY-MM-DD}}/email.md
   ```
   Спочатку `--dry-run` за потреби. Не send — лише чернетка. За замовчуванням додає HTML-підпис з Gmail Settings (`append_gmail_signature`). Recipients: `--to` або `config/weekly-status-mail.json`. Skill: `pmo-google-ops`.
7. Запусти `pmo-qg-review-status-consistency` перед відправкою листа (після ручного review Gmail draft).

### Fallback structure (якщо style-файл пошкоджений / без Structure)

Використай блоки з `templates/tl-weekly-status-email.md`:

```text
Тема: [{{PROJECT_NAME}}] Тижневий статус — {{DATE}} — {{GREEN|AMBER|RED}}

{{TRAFFIC}} Статус: {{COLOR}} — {{короткий підсумок одним рядком}}.

Цього тижня: {{2-4 пункти результатів бізнес-мовою}}.

Наступного тижня: {{2-3 заплановані результати}}.

Ризики / блокери: {{немає | простими словами проблема + що робимо}}.

Потрібна дія: {{Дій не потрібно | Будь ласка, зробіть X до Y}}.

Детальніше у Confluence: {{CONFLUENCE_STATUS_PAGE_URL}}
```

Лінк на опублікований Confluence Project Status Report — **обов’язковий** у email (один рядок). Якщо сторінки ще немає — опублікуй через `pmo-confluence-ops`, потім встав URL.

### Розширений статус (PO / working contact / wiki)

Використай структуру з `templates/tl-weekly-status-po.md` або історичний формат проєктного Confluence (`ALL REPORTS`), узагальнений під CONTEXT.md.

## Traffic Light — формулювання

| Ситуація | Формулювання |
|---|---|
| Все добре | 🟢 Green — project on track, no concerns |
| Незначне відставання | 🟡 Amber — slightly behind on X; back on track next week |
| CR чекає підпису | 🟡 Amber — awaiting approval on CR-N; no timeline impact if approved this week |
| Milestone під ризиком | 🔴 Red — blocked on X; escalated; timeline impact possible |

## Rules

1. **Пт 17:00 без винятків** — навіть якщо «нічого нового».
2. Traffic Light **завжди** в першому абзаці / subject.
3. **No Surprises** — Amber/Red клієнт дізнається від PM першим, не від когось іншого.
4. Без жаргону: технічні терміми → бізнес-мова; метрики пояснюй словами.
5. **Потрібна дія** завжди явно: `Дій не потрібно` або `Будь ласка, зробіть X до Y`.
6. Не вигадуй прогрес — лише з канонічних джерел.
7. Мова листа **і wiki-звіту**: **українська** за дефолтним / проєктним email-style (інше — лише за явним override).
8. **Назви задач українською:** у Overview / баги / таблиці прогресу / email — не копіювати англійський Jira summary; писати `{{JIRA_KEY}}-NNN — український опис` (власні назви Stripe/Brevo/GraphQL можна лишати).
9. Style override **не** може прибрати Traffic Light або «Потрібна дія» і **не** може копіювати EWS клієнту.

## Antipatterns

- Зелений статус при відомому блокері
- «Ми працюємо над інтеграцією» без outcome
- Прохання до клієнта, сховані в середині тексту
- Копіювання внутрішнього EWS клієнту
- Пропуск тижня бо «все тихо»
- Ігнорування явного `--email-style` / проєктного `email-style.md` без причини
- Збереження тижневих артефактів у **корінь** `docs/weekly-status/` замість `{{YYYY-MM-DD}}/`

## Self-check

- [ ] Style-файл зарезолвлено і вказано в шапці `{{YYYY-MM-DD}}/email.md`
- [ ] Усі артефакти тижня в `docs/weekly-status/{{YYYY-MM-DD}}/` (не в корені)
- [ ] Traffic Light узгоджений з рисками/CR/фактами (wiki / внутрішнє; cover-стиль проєкту — у wiki, якщо так у `email-style.md`)
- [ ] Email відповідає Structure з обраного style
- [ ] «Потрібна дія» явна **або** cover-стиль проєкту без цього рядка (якщо override cover)
- [ ] Немає внутрішніх метрик без перекладу
- [ ] У email є лінк на Confluence status page (cover: пункт 1 списку)
- [ ] Лист і wiki-звіт українською; назви задач не англійським Jira summary
- [ ] Пройдено `pmo-qg-review-status-consistency`

## Quality gate

Після генерації обов'язково запусти skill `pmo-qg-review-status-consistency`.

## Company methodology

- `knowledge/pmo-kb/04-executing/d11-weekly-status-report-client.md`
- `knowledge/pmo-kb/04-executing/client-project-status-report.md`
- `knowledge/pmo-kb/02-initiating/b7-communication-plan.md`

## Additional resources

- `templates/tl-weekly-status-email.md` — **default** email style
- `docs/weekly-status/email-style.md` — project override (optional)
- `docs/weekly-status/README.md` — layout: пакети в `{{YYYY-MM-DD}}/`
- `config/weekly-status-mail.example.json` — default To/Cc for Gmail draft
- `pmo-google-ops` — `google gmail-draft`
- `templates/tl-weekly-status-po.md`
- `templates/tl-weekly-status-internal.md`
- `checklists/pre-send-status.md`
