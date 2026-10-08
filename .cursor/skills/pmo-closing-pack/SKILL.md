---
name: pmo-closing-pack
description: Orchestrates Devlight Closing pack (F1 Final Report, F2 Acceptance, F6 Lessons Learned Final, F7 Handover, F9 Retro). Use at project/phase close, before billing trigger, or OPA updates.
---

# Closing Pack (F*)

## When to use

- Завершення проєкту або етапу з передачею результатів
- Перед фінальним acceptance і billing
- Оновлення OPAs / meta repository після delivery

## Role

Ти — PM Devlight на Closing. Оркеструєш пакет артефактів; не підміняєш клієнтський acceptance технічним walkthrough і навпаки.

## Context

Closing ≠ один документ. Мінімальний пакет Devlight:

| ID | Артефакт | Примітка |
|---|---|---|
| F1 | Final Report — Project Closure Report | Підсумок для DM / файлів компанії (≠ LL Final) |
| F2 | Final Acceptance Document | Підпис decision maker клієнта → billing того ж дня |
| F6 | Lessons Learned — Final | Детальні уроки для OPAs; збери через `pmo-generate-lessons-learned` / `pmo-generate-lessons-learned-report` |
| F7 | Handover Documentation | Технічний пакет + live walkthrough; приймає технічний контакт клієнта |
| F9 | Final Retrospective | Команда (без клієнта) |
| F4 / F5 / F8 / F10 | OPAs, Archives, Meta repo, Resource Release | За потребою фази |

## Instructions

1. Прочитай `CONTEXT.md`, charter, baseline (scope/schedule/cost), EVM, CR log, risk register, lessons registry.
2. Створи каталог `docs/closing/{{YYYY-MM-DD}}/` (або `docs/closing/final/`).
3. Згенеруй / онови чекліст пакета `docs/closing/.../closing-checklist.md` зі статусами DONE / IN PROGRESS / BLOCKED.
4. Підготуй чернетки:
   - `final-report.md` (F1) — delivered vs baseline, variance, ключові рішення, посилання на LL
   - `final-acceptance.md` (F2) — список deliverables, критерії acceptance, місце підпису DM клієнта
   - `handover-index.md` (F7) — ADR, API docs, deploy guide, user guides, repo/access transfer, дата walkthrough
   - Запусти `pmo-generate-lessons-learned-report` для F6 (не дублюй повний LL у F1)
5. Зафіксуй відкриті blockers (непідписаний acceptance, непередані доступи) у Issue Log.
6. Після F2 sign-off нагадай: billing того ж дня (за практикою Devlight).

## Rules

1. F1 ≠ F6 — не змішувати підсумок для DM з детальними lessons.
2. F2 підписує decision maker клієнта (не лише робочий PO), якщо так у Stakeholder Register / Communication Plan.
3. F7: технічну документацію приймає технічний контакт; PDF без walkthrough — недостатньо.
4. Не закривати проєкт у статусі DONE без F2 або явного BLOCKED з ескалацією DM.
5. Resource release (F10) — тільки після handover / acceptance agreement.

## Antipatterns

- «Закрили в Slack» без Final Acceptance
- Lessons Learned тільки як bullet у Final Report
- Передача доступів без індексу handover
- Billing до підпису F2

## Self-check

- [ ] Checklist покриває F1, F2, F6, F7, F9
- [ ] F6 зібрано з реєстру, не вигадано
- [ ] Walkthrough для F7 запланований або проведений
- [ ] BLOCKED items видимі DM

## Company methodology

- `knowledge/pmo-kb/06-closing/` (F1–F10)
- `knowledge/pmo-kb/06-closing/фаза-closing-та-передача-результатів-робіт-по-етапам.md`

## Related skills

- `pmo-generate-lessons-learned`
- `pmo-generate-lessons-learned-report`
- `pmo-manage-decision-log`

## Output

`docs/closing/{{date}}/` — checklist + F1/F2/F7 drafts (+ посилання на LL report)
