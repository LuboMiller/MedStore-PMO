---
name: pmo-manage-glossary
description: Maintains the B5 Project Glossary (shared project language, disambiguation). Use when a new domain term appears on a call, during initiating/planning, or before BA publishes specs.
---

# Project Glossary (B5)

## When to use

- Initiating / Planning — зафіксувати спільну мову
- Нове поняття прозвучало на дзвінку зі стейкхолдерами
- Перед публікацією requirements / FS / user stories

## Role

BA збирає терміни, PM координує узгодження з PO/клієнтом. Будь-яке нове поняття на дзвінку → запис у Glossary **протягом 24 годин**.

## Instructions

1. Прочитай `CONTEXT.md` і наявний `docs/glossary.md` (створи, якщо немає).
2. Режим: **ADD** / **UPDATE** / **AUDIT**.
3. Для кожного терміна заповни: визначення в системі · **НЕ плутати з** · джерело · статус (Draft / Confirmed).
4. Не вигадуй доменні визначення — якщо неясно, познач Draft і додай Open Question.

## Output template

Див. [template.md](template.md). Файл: `docs/glossary.md`.

## Rules

1. Один канонічний термін на поняття — без синонімів-дублікатів у «Визначення».
2. Колонка «НЕ плутати з» обов'язкова для термінів з ризиком двозначності.
3. Confirmed — лише після підтвердження власника терміна (зазвичай PO / BA lead).

## Company methodology

`knowledge/pmo-kb/02-initiating/b5-project-glossary.md`

## Additional resources

- `pmo-manage-open-questions` — якщо визначення заблоковане
- `pmo-manage-functional-spec` — FS мають узгоджуватись із glossary
