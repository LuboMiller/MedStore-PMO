---
name: pmo-manage-escalation-matrix
description: Creates or updates the C23 Escalation Matrix (Amber/Red/Critical triggers, SLA, hierarchy). Use during planning after charter/comms plan, or when escalation paths are unclear.
---

# Escalation Matrix (C23)

## When to use

- Planning після Communication Plan / RACI
- Коли команда питає «чи варто ескалювати»
- Після зміни DM / клієнтських decision makers

## Role

Ти — PM Devlight. Матриця прибирає суб'єктивність: рівні і SLA фіксовані.

## Context — принципи Devlight

- **No Surprises** — DM і клієнт дізнаються від PM першими
- **По ієрархії** — PM → DM → CEO (не перестрибувати)
- Amber — того ж дня; Red — ≤ 4 годин
- Ескалація до C-level клієнта **тільки після** повідомлення DM

## Instructions

1. Візьми ролі з `CONTEXT.md`, `docs/stakeholder-register.md`, `docs/communication-plan.md`.
2. Заповни 3 рівні + клієнтську ієрархію + контакти (див. [template.md](template.md)).
3. Збережи `docs/escalation-matrix.md`.
4. Переконайся, що SLA узгоджені з EWS / Communication Plan.

## Levels (default triggers)

| Рівень | Тригери (будь-який) | Хто | SLA |
|---|---|---|---|
| 🟡 Amber L1 | SPI/CPI 0.85–0.99; spillover 10–20%; readiness 75–89% / 2 тижні; клієнт мовчить 3–5 р.д. | PM | Action plan ≤ 24h; DM via EWS |
| 🔴 Red L2 | SPI/CPI < 0.85; milestone at risk; key person out; scope dispute > 3 р.д.; contingency > 80% | PM+DM | Slack DM now; Zoom 30m; plan ≤ 4h |
| 🆘 Critical L3 | Contract at risk; GDPR breach; churn threat; margin < 0%; L2 unresolved | CEO+DM+PM | CEO ≤ 2h after DM confirms Critical |

## Rules

1. Не ескалювати до клієнтського C-level без DM.
2. Контакти й канали — реальні з CONTEXT, не плейсхолдери в фіналі.
3. Зміна матриці — через Decision Log / CR за потреби.

## Company methodology

`knowledge/pmo-kb/03-planning/c23-escalation-matrix.md`  
Related: `pmo-generate-escalation-memo`, `pmo-generate-ews-report`
