---
name: pmo-manage-raci
description: Creates or updates the B4 RACI/DACI matrix with exactly one Accountable per row. Use during initiating/planning, after team changes, or when ownership of deliverables is unclear.
---

# RACI / DACI Matrix (B4)

## When to use

- Initiating / Planning — розподіл відповідальностей
- Зміна складу команди або появи нового deliverable
- Конфлікт «хто Accountable» / розмите ownership

---

## Role

Ти — Senior PM. Матриця знімає двозначність: хто робить, хто відповідає, кого питають, кого інформують.

---

## Context

**RACI:** Responsible / Accountable / Consulted / Informed.  
**Ключове правило Devlight/PMBOK: один A на кожен рядок** — не два, не нуль.

**DACI** (Driver / Approver / Consulted / Informed) — для рішень без одного «виконавця»; зручніший для процесів, ніж для deliverables.

Режими: **CREATE** (перша матриця) / **UPDATE** (рядки або ролі) / **AUDIT** (перевірка «один A»).

---

## Instructions

1. Прочитай `CONTEXT.md`, charter/команду, `knowledge/pmo-kb/02-initiating/b4-raci-daci-matrix.md`.
2. Побудуй або онови матрицю за [template.md](template.md).
3. Мінімальний набір рядків (якщо CREATE): Project Charter, Requirements/Stories, Sprint Backlog, Release, Scope Change (CR), Escalation Red, Weekly Status, EWS.
4. Для кожного рядка рівно один `A` (або один Approver у DACI).
5. Збережи `docs/raci-matrix.md`.

---

## Output location

```
docs/raci-matrix.md
```

---

## Company methodology

- `knowledge/pmo-kb/02-initiating/b4-raci-daci-matrix.md`
- Пов’язані: B1 Charter, B6 Onboarding, B7 Communication Plan

## Rules

1. **Один A на рядок.** Два A = дефект; нуль A = дефект.
2. R може бути кілька; A — лише один.
3. Не плутати R і A: R робить роботу, A відповідає за результат.
4. Мова — українська (заголовки/нотатки); коди R/A/C/I — латиницею.

---

## Antipatterns

- PM як A на всіх рядках «щоб було просто»
- Порожні клітинки замість явного `--` де роль не бере участі
- DACI і RACI в одній таблиці без пояснення

---

## Self-check

- [ ] Кожен рядок має рівно один A
- [ ] Escalation Red: DM = A (типово Devlight)
- [ ] Scope Change: зрозуміло хто A (зазвичай PM)
