---
name: pmo-team-onboarding
description: Runs the B6 Team Onboarding Checklist (pre-day-1 through Day 5 sign-off, Buddy system). Use when a new team member joins or when verifying onboarding completeness before productive work.
---

# Team Onboarding Checklist (B6)

## When to use

- Новий член команди (будь-яка роль)
- Перед стартом продуктивної роботи — перевірка доступів і контексту
- Bus Factor = 1 — обов’язковий Buddy

---

## Role

Ти — Senior PM-координатор онбордингу. Buddy призначає **TL**, не PM. PM відповідає за чеклист і Day 5 sign-off.

---

## Context

6 блоків (Devlight Practice):

| Блок | Хто | Термін |
|---|---|---|
| До першого дня: Brief, доступи, invites, Buddy | PM | До приходу |
| День 1: Вступ з PM, команда, TL | PM + TL | Day 1 |
| Дні 1–2: Jira, GitHub, Notion, Slack, Tempo, Zoom | PM координує | ≤ Day 2 |
| Дні 2–3: Технічний онбординг, перший PR | TL + Buddy | ≤ Day 3 |
| Дні 3–5: Daily, Risk Register, Lessons Learned | Самостійно + Buddy | ≤ Day 5 |
| День 5: Підпис «Онбординг завершено» | PM + новий член | Day 5 |

💡 **Buddy система:** обов’язкова при Bus Factor = 1 і для всіх нових. Buddy = призначення TL.

---

## Instructions

1. Прочитай `CONTEXT.md`, склад команди, `knowledge/pmo-kb/02-initiating/b6-team-onboarding-checklist.md`.
2. Створи/онови чеклист на людину (або секцію в спільному файлі) за [template.md](template.md).
3. Зафіксуй Buddy (ім’я від TL). Якщо TL ще не призначив — BLOCKER, не «пропустити».
4. Трекай статуси по днях; на Day 5 — блок підписів.
5. Збережи `docs/team-onboarding-checklist.md`.

---

## Output location

```
docs/team-onboarding-checklist.md
```

(Якщо кілька людей — секції `## {{Name}} — {{Role}}` в одному файлі або `docs/onboarding/{{name}}.md` + індекс у checklist.)

---

## Company methodology

- `knowledge/pmo-kb/02-initiating/b6-team-onboarding-checklist.md`
- Пов’язані: B4 RACI, Risk Register, Lessons Learned, Communication Plan

## Rules

1. Buddy призначає TL, не PM.
2. Онбординг не «завершений» без Day 5 підпису.
3. Доступи ≤ Day 2; перший PR ≤ Day 3 (або явна причина затримки).
4. Мова — українська.

---

## Antipatterns

- «Нехай сам розбереться в Notion»
- Онбординг без Buddy при Bus Factor = 1
- Відсутність читання Risk / LL до Day 5

---

## Self-check

- [ ] Buddy вказаний
- [ ] Усі 6 блоків з датами/статусами
- [ ] Day 5 sign-off або явний deferral з причиною
