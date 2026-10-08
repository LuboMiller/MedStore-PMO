---
name: pmo-daily-pm-actions
description: Aggregates open PM work into a prioritized daily action list from Issue Log, open questions, EWS, decisions, meeting follow-ups, and cadence calendar. Use when the PM asks what to do today, morning briefing, daily actions, or reminders for the project.
---

# Daily PM Actions

## When to use

- «Що мені зробити сьогодні?» / morning briefing / daily actions
- Нагадування перед standup або Status Meet
- Cursor Automation (cron) на ранок — той самий skill

Не замінює `pmo-weekly-rhythm` (Пн EWS / Пт D11) і не створює новий Issue Log / OQ — лише **зчитує** джерела й зводить пріоритезований список.

---

## Role

Ти — Senior PM. Список — внутрішній, для PM (і DM, якщо dual-role). Мова — українська. Без FAB: лише те, що є в артефактах / реєстрах.

---

## Sources (read in order)

| # | Джерело | Що брати |
|---|---|---|
| 1 | `CONTEXT.md` | фаза, дедлайни, dual-role, blockers у §status якщо є |
| 2 | `docs/issue-log.md` | Open / In Progress; P1→P2 першими; overdue = escalate |
| 3 | `docs/open-questions.md` | Open OQ + Follow-ups з owner=PM або без owner |
| 4 | Останній `docs/ews/ews-*.md` + `dashboards/ews-dashboard.md` | відкриті Action Items; Amber/Red виміри → обов’язкові кроки сьогодні |
| 5 | `docs/decisions/` (Active) | рішення з pending follow-through для PM |
| 6 | `docs/meeting-notes/**/summary.md` (останні 14 днів) | незакриті Action items з owner PM / «команда» / без owner |
| 7 | `docs/communication-plan.md` | щоденний/тижневий календар **на сьогодні** (standup, Status Meet, EWS, D11…) |
| 8 | `docs/risk-register.md` | лише ризики з mitigation due ≤ сьогодні або overdue (не всі) |
| 9 | `docs/change-requests/` / `change-log.json` | CR у статусі, що вимагає PM action сьогодні |
| 10 | `docs/_hydrate/google/sheets/client-status-live-YYYY-MM-DD/` | Overview / Scope / CSAT після `google export-sheets` (burn, completion, Estim.) |
| 11 | `docs/contracts/register.md` (+ `config/contracts.json`) | Контракт / етапи з end_date у warn/overdue → P0/P1 (пролонгація, acceptance) |
| Опційно | live Jira/Tempo | лише якщо PM просив live або automation з `--live`; спочатку `pmo-integrations-health` |

Пропусти відсутній файл однією позначкою в §Sources scanned — не вигадуй.

> **Automation:** `google sync-pull` ≠ контент Client status sheet. Ранковий прогін має викликати `google export-sheets` (див. [automation-prompt.md](automation-prompt.md) Phase A2) **перед** цим skill.

---

## Instructions

1. Визнач **дату** (сьогодні, або дату з запиту) і день тижня (для cadence).
2. Прочитай джерела з таблиці; для meeting notes — лише `summary.md` з секцією Action items, не raw transcript.
3. Зведи кандидати у єдиний список; **дедуп** за змістом (ISS + той самий EWS AI → один рядок з обома ID).
4. Пріоритезуй (див. нижче). Максимум **7–10** дій на день; решту — «Backlog / later this week».
5. Запиши артефакт за [template.md](template.md) у `docs/daily-actions/YYYY-MM-DD.md`.
6. У чаті — короткий TL;DR (топ-3) + шлях до файлу. Не дублюй увесь файл, якщо він довгий.

### Priority rules

| Prio | Коли |
|---|---|
| **P0 Today — must** | P1 issue; EWS Amber/Red action due; cadence на сьогодні (Пн EWS, Пт D11, Status Meet); overdue deadline |
| **P1 Today — should** | P2 issue; Open OQ з PM owner; decision follow-through; meeting AI з due ≤ сьогодні |
| **P2 If capacity** | P3–P4; risk mitigation; CR prep без жорсткого due |
| **Parked** | чужий owner без ескалації; Closed/Resolved; «моніторити» без next step |

Формула рядка: **дієслово + результат + owner + due** (як у meeting notes). Не «розглянути X».

### Cadence hints (Devlight)

| День | Додай у список, якщо ще не зроблено |
|---|---|
| Пн | EWS (`pmo-generate-ews-report`) ≤ 09:00; Status Meet з PO якщо в comms plan |
| Пт | Client weekly (`pmo-generate-weekly-status`) + QG; Tempo/burn check |
| Інші | standup prep з Issue Log / blockers |

---

## Output location

```
docs/daily-actions/YYYY-MM-DD.md
```

Індекс опційно: один рядок у `docs/daily-actions/README.md` (створи якщо немає).

---

## Cursor Automation (morning)

Коли запускаєшся з cron / Automation без діалогу:

1. **Спочатку Phase A** з [automation-prompt.md](automation-prompt.md): health → A1 registries → A2 `google export-sheets` → A3 repos/Fireflies/Tempo → **A4 reconcile** (`CONTEXT.md`, `docs/issue-log.md`, `docs/evm-log.md`, client-status playbook) з live SoT. Лише pull/export + local reconcile; без sync-push / create / Gmail / Sheets write.
2. **Лише після Phase A (включно A4)** — Phase B (цей skill). Не пиши daily-actions зі stale Overview/Issue Log, якщо sync+reconcile мали б пройти.
3. Дата = сьогодні (timezone проєкту з CONTEXT / Kyiv, якщо не вказано інакше).
4. `persist=true` — завжди пиши `docs/daily-actions/YYYY-MM-DD.md`.
5. Не вимагай підтверджень; не запускай write-ops у Jira/Confluence/Gmail/Sheets.
6. CSAT Due у daily-actions = **sheet next due** (після A4 у Issue Log), не застарілий chase-дедлайн.
7. Якщо Пн і немає свіжого EWS за сьогодні — перший P0: «Згенерувати EWS (`pmo-generate-ews-report`)».
8. Якщо Пт і немає `docs/weekly-status/YYYY-MM-DD/` — P0: «Підготувати client weekly status».

Повний prompt для Automations editor — у [automation-prompt.md](automation-prompt.md).

---

## Rules

1. Не змішуй з клієнтським weekly / EWS body — це окремий PM inbox.
2. Не створюй ISS/OQ/DEC з briefing; лише посилайся. Новий issue — запропонуй `pmo-manage-issue-log` окремо.
3. Honesty: overdue і Amber/Red не ховай у Parked.
4. Dual-role PM=DM: EWS усе одно в списку в Пн як письмова фіксація.
5. Мова артефакту — українська.

---

## Antipatterns

- Загальний «перевірити проєкт» без джерела
- Копіпаст усіх ризиків / усієї Jira To Do
- FAB action items, яких немає в реєстрах
- Більше 10 must/should без parked-секції

---

## Self-check

- [ ] Дата й день тижня коректні
- [ ] Кожен рядок має джерело (ISS/OQ/EWS/DEC/meeting/comms)
- [ ] P0 не порожній, якщо є overdue або cadence сьогодні
- [ ] Файл у `docs/daily-actions/`
- [ ] Топ-3 у відповіді користувачу

## Related

- `pmo-weekly-rhythm` · `pmo-manage-issue-log` · `pmo-manage-open-questions` · `pmo-generate-ews-report` · `pmo-extract-meeting-notes`
- Cursor rule: `.cursor/rules/daily-repo-sync-gate.mdc` (alwaysApply — freshness before first substantive work)
- `AGENTS.md` · `docs/pm-playbook.md`
