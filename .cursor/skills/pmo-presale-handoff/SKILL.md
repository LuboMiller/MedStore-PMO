---
name: pmo-presale-handoff
description: Runs the A2 Pre-sale Handoff Checklist gate (Sales→PM) with PASSED/WITH NOTES/BLOCKED statuses. Use when receiving a new deal from Sales, before PM ownership, or verifying handoff completeness.
---

# Pre-sale Handoff Checklist (A2)

## When to use

- Sales передає проєкт PM (формальний gate Pre-sale → Initiating)
- Перед тим як PM бере відповідальність за delivery
- Аудит: чи був handoff підписаний, чи є BLOCKED gaps

---

## Role

Ти — Senior PM Devlight. Ти не «приймаєш на віру» КП від Sales: ти проганяєш 6 блоків чеклісту і ставиш статус. Без підписаного checklist PM офіційно не бере проєкт.

---

## Context

Pre-sale Handoff Checklist — **формальний gate між Sales і PM**. Без нього PM не відповідає за проблеми через неповноту переданої інформації (правило Devlight).

Статуси:

| Статус | Значення | Дія |
|---|---|---|
| ✅ PASSED | Усі блоки OK | PM бере проєкт |
| ⚠️ PASSED WITH NOTES | Нюанси, некритичні | PM бере з умовою відстеження |
| 🔴 BLOCKED | Критичний gap | Sales вирішує **перед** передачею |

Блоки з жорстким BLOCKED при провалі: **Документи**, **Scope**, **Команда**.  
Бюджет / Клієнт / Ризики частіше → PASSED WITH NOTES (якщо є часткові дані).

---

## Instructions

1. Прочитай `CONTEXT.md` і джерела pre-sale (`КП`, SOW, estimate, assumptions), якщо є в `docs/` або вкладеннях.
2. Прочитай методологію: `knowledge/pmo-kb/01-pre-sale/a2-pre-sale-handoff-checklist.md`.
3. Заповни 6 блоків (див. template). Кожен рядок: PASSED / PASSED WITH NOTES / BLOCKED + коментар.
4. Визнач **загальний** статус:
   - будь-який BLOCKED у Документи / Scope / Команда → загальний 🔴 BLOCKED
   - немає BLOCKED, але є NOTES → ⚠️ PASSED WITH NOTES
   - усе PASSED → ✅ PASSED
5. Збережи `docs/presale-handoff-checklist.md`.
6. Якщо BLOCKED — явно напиши, що PM **не бере** проєкт, і список що Sales має закрити.
7. Якщо PASSED / WITH NOTES — наступний крок: `pmo-generate-project-charter` (B1, внутрішній PM+DM).

**Вхід:**
```
Проєкт: {{PROJECT_NAME}}
Клієнт: {{CLIENT}}
Sales: {{SALES_OWNER}}
PM: {{PM_NAME}}
DM: {{DM_NAME}}
Дата handoff: {{DATE}}
Посилання на КП / SOW / Estimate / NDA: {{LINKS}}
Нотатки Sales: {{NOTES}}
```

---

## Output location

```
docs/presale-handoff-checklist.md
```

Шаблон: [template.md](template.md)

---

## Company methodology

- `knowledge/pmo-kb/01-pre-sale/a2-pre-sale-handoff-checklist.md`
- Пов’язані: A1 КП, A3 Brief, A4 Estimate, A5 SOW, A6 Assumptions
- `CONTEXT.md` + `knowledge/pmo-kb/README.md`

## Rules

1. Без підписаного checklist (PASSED / WITH NOTES) PM не стартує delivery.
2. BLOCKED не «пом’якшувати» до NOTES, якщо немає підписаного SOW/контракту, незрозумілий scope IN/OUT, або FTE не підтверджені DM.
3. Мова документу — українська.
4. Фіксуй конкретні gaps («немає payment schedule»), не загальні («треба уточнити»).

---

## Antipatterns

- Прийняти проєкт «на словах» без checklist
- PASSED при відсутньому SOW / NDA
- Ховати BLOCKED у NOTES, щоб «не блокувати Sales»

---

## Self-check

- [ ] Усі 6 блоків мають статус і коментар
- [ ] Загальний статус узгоджений з найгіршим критичним блоком
- [ ] Є підписи / імена Sales + PM (+ DM якщо потрібно)
- [ ] При BLOCKED — явний action list для Sales
