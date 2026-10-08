---
name: pmo-generate-kickoff-deck
description: Builds a B3 Kick-off Deck outline (10 slides) including mandatory Out of Scope pause. Use before the first official client meeting to align on goals, scope, timeline, and working rhythm.
---

# Kick-off Deck (B3)

## When to use

- Перед першою офіційною зустріччю з клієнтом
- Після Charter (внутрішній) + Communication Plan / Stakeholder Register
- Повторний kick-off нової фази (адаптуй слайди)

---

## Role

Ти — Senior PM. Deck формує перше враження і **верифікує scope до старту розробки**.

---

## Context

Структура **10 слайдів** (Devlight Practice):

| # | Зміст | Мета |
|---|---|---|
| 1 | Титул | Партнерство — два логотипи |
| 2 | Команда Devlight | Клієнт знає хто ці люди |
| 3 | Як ми розуміємо задачу | Верифікація розуміння |
| 4–5 | Scope IN / OUT (**явно**) | Межі |
| 6 | Timeline по milestones | Дати + що готово |
| 7–8 | Як працюємо + комунікація | Ритм, канали, очікування |
| 9 | Відкриті питання (закрити сьогодні) | Блокери |
| 10 | Наступні кроки | Хто / що / до коли |

**Ключове правило:** слайд Out of Scope обов’язковий. На ньому PM робить паузу і питає: «Чи є питання щодо цього переліку?» Підтвердження → Meeting Minutes (+ за потреби Decision Log).

Зразки структури: `knowledge/pmo-kb/02-initiating/b3-kick-off-deck/` (internal + client samples).

---

## Instructions

1. Прочитай `CONTEXT.md`, charter (внутрішній — **не копіюй confidential** у client deck), communication plan, open questions.
2. Прочитай `knowledge/pmo-kb/02-initiating/b3-kick-off-deck.md` і зразки в тій теці.
3. Згенеруй markdown-outline слайдів за [template.md](template.md) — текст для спікера + bullets на слайд.
4. Scope OUT ≥ 3 пункти; open questions — з пропозицією закрити на зустрічі.
5. Збережи `docs/kickoff-deck.md`.
6. Після зустрічі: `pmo-extract-meeting-notes`; підтвердження OUT scope → Decision Log за потреби.

---

## Output location

```
docs/kickoff-deck.md
```

---

## Company methodology

- `knowledge/pmo-kb/02-initiating/b3-kick-off-deck.md`
- Samples: `…/b3-kick-off-deck/kick-off-xxxxxx.md`, `internal-kick-off-sample-250925.md`
- Charter (B1) — внутрішній; у deck лише client-safe формулювання цілей/scope

## Rules

1. Out of Scope слайд обов’язковий + скрипт паузи.
2. Не включати margin, внутрішні оцінки стейкхолдерів, EWS.
3. Мова — українська (або мова клієнта, якщо PM явно просить).
4. Наступні кроки — з Owner і датою.

---

## Antipatterns

- Kick-off без OUT scope
- Технічний deep-dive замість alignment
- «Ми все уточнимо пізніше» без списку питань на сьогодні

---

## Self-check

- [ ] 10 слайдів за структурою
- [ ] IN і OUT явні
- [ ] Є питання на закриття сьогодні + next steps
