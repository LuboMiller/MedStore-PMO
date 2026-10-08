---
name: pmo-manage-issue-log
description: Maintains the D3 Issue Log for management problems that have already occurred (not risks, not Jira bugs). Use when blockers appear, client delays, unclear requirements, or resource issues need tracking to resolution.
---

# Issue Log (D3)

## When to use

- Проблема **вже сталась** і блокує/впливає на проєкт зараз
- Weekly review відкритих issues
- Закриття issue після рішення (і за потреби лінк на Decision Log)

---

## Role

Ти — Senior PM. Issue Log — управлінські проблеми, не баг-трекер.

---

## Context

| Артефакт | Коли | Приклад |
|---|---|---|
| Risk Register | Може статись | «LabAPI може бути недоступна» |
| **Issue Log** | Вже сталось | «LabAPI docs неповні — BE заблокований» |
| Assumption Log | Вважаємо правдою | «LabAPI v2 стабільна до дати» |

⚠️ **Issue Log ≠ Bug tracker.** Bugs → Jira. Сюди: неясні вимоги, блокери клієнта, vendor delays, ресурсні питання.

Режими: **ADD** / **UPDATE** / **RESOLVE** / **CLOSE**.

---

## Instructions

1. Прочитай `docs/issue-log.md` (або створи), `knowledge/pmo-kb/04-executing/d3-issue-log.md`.
2. Перед ADD — перевір, чи це не ризик (ще не сталось) і не Jira-bug.
3. Заповни поля: ID `ISS-NNN`, Priority P1–P4, опис+вплив, варіанти A/B/C, Owner, Deadline, Action, Status, зв’язок (Risk/Assumption/CR/Decision).
4. При RESOLVE — коротко зафіксуй рішення; якщо це ключове рішення проєкту — також `pmo-manage-decision-log`.

Шаблон рядка: [template.md](template.md)

---

## Output location

```
docs/issue-log.md
```

---

## Company methodology

- `knowledge/pmo-kb/04-executing/d3-issue-log.md`
- Пов’язані: Risk Register, Decision Log, Change Requests

## Rules

1. ID `ISS-001…` унікальний, не перевикористовується.
2. Priority: P1 Critical / P2 High / P3 Medium / P4 Low.
3. Status: Open / In Progress / Resolved / Closed.
4. Варіанти рішення — мінімум 2 з оцінкою, якщо issue ще Open/In Progress.
5. Мова — українська.

---

## Antipatterns

- Дублювати Jira bugs у Issue Log
- Issue без Owner і Deadline
- «Моніторити» замість Action

---

## Self-check

- [ ] Це вже сталось (не ризик)
- [ ] Є Owner, Deadline, Action
- [ ] Зв’язок з Risk/CR/Decision якщо релевантно
