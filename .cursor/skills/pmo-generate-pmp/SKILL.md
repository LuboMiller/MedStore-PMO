---
name: pmo-generate-pmp
description: Builds the C1 Project Management Plan hub linking subsidiary plans and baselines (scope/schedule/cost). Use after initiating artifacts exist and when assembling the planning baseline package; changes only via ICC/CR.
---

# Project Management Plan Hub (C1)

## When to use

- Після Initiating (B*) — збір Planning baseline
- Аудит: чи всі subsidiary plans / baselines існують і залінковані
- Після approved CR, що змінює baseline (нова версія PMP)

## Role

PMP — **навігаційний хаб**, не монолітний документ. Зміни **тільки** через ICC / Change Request. Правити дату «втихоря» — порушення дисципліни.

## Context — 3 шари

1. **Subsidiary plans** (scope, schedule, cost, quality, resource, communications, risk, procurement, stakeholder engagement, change, configuration, requirements…)
2. **Baselines**: Scope (Statement + WBS + dictionary) · Schedule · Cost
3. **PMB** = Scope + Schedule + Cost → база для EVM

### CR authorization (Devlight)

| Вплив | Хто |
|---|---|
| ≤ 8 год | PM |
| 8–40 год | PM + DM |
| > 40 год | DM + клієнт C-level |

## Instructions

1. Проскануй `docs/`, `dashboards/`, skills outputs — що вже є.
2. Згенеруй/оновлюй `docs/project-management-plan.md` за [template.md](template.md): версія, дата, лінки, статус кожного плану (EXISTS / DRAFT / MISSING).
3. Для MISSING — запропонуй наступний skill (напр. WBS, risks, roadmap, communication plan).
4. Не дублюй повний текст subsidiary plans у PMP — лише посилання + 1–2 рядки призначення.
5. При зміні baseline — bump version, зафіксуй CR ID у Decision/Change Log.

## Rules

1. PMP без Scope/Schedule/Cost baseline лінків = incomplete.
2. Кожна зміна baseline → нова версія + підписи (PM/DM).
3. Не вигадуй статуси файлів — перевіряй наявність у репо.

## Company methodology

`knowledge/pmo-kb/03-planning/c1-project-management-plan.md`  
PMB: `knowledge/pmo-kb/03-planning/performance-measurement-baseline.md`

## Related skills

`pmo-generate-wbs`, `pmo-manage-roadmap`, `pmo-manage-gantt-chart`, `pmo-manage-risk-register`, `pmo-manage-communication-plan`, `pmo-analyze-scope-change`
