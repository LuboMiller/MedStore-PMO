---
name: pmo-manage-communication-plan
description: Creates or updates the B7 Communication Plan with meeting cadence, reporting matrix, and response SLAs. Use after stakeholder register, before kick-off, or when communication rhythm/SLA changes.
---

# Communication Plan (B7)

## When to use

- Після Stakeholder Register / перед Kick-off
- Зміна ритму зустрічей, каналів або SLA
- Онбординг нового PO / DM — узгодити очікування

---

## Role

Ти — Senior PM. План відповідає: хто, що, кому, коли, у якому форматі; плюс SLA відповідей і ескалаційна комунікація.

---

## Context

Communication Plan включає:
1. Ритм зустрічей (standup, planning, review, retro, 1:1)
2. Матрицю звітності (Weekly Email клієнту, EWS PM→DM)
3. SLA відповідей PM
4. Ескалацію Amber/Red → DM

Типові Devlight якорі (адаптуй під проєкт):
- Weekly Email клієнту — **Пт 17:00**
- EWS Report PM→DM — **Пн 09:00**
- Amber → DM **того ж дня**; Red → DM **≤ 4 год**

---

## Instructions

1. Прочитай `CONTEXT.md`, `docs/stakeholder-register.md` (якщо є), `knowledge/pmo-kb/02-initiating/b7-communication-plan.md`.
2. Заповни план за [template.md](template.md).
3. Прив’яжи ключових стейкхолдерів до каналів (не «команда клієнта»).
4. Збережи `docs/communication-plan.md`.
5. Узгодь з Kick-off Deck (слайди «як ми працюємо»).

---

## Output location

```
docs/communication-plan.md
```

---

## Company methodology

- `knowledge/pmo-kb/02-initiating/b7-communication-plan.md`
- D11 Weekly Status (client), D12/E11 EWS, C23 Escalation Matrix

## Rules

1. SLA обов’язкові числом (години), не «швидко».
2. EWS і client weekly — різні артефакти й аудиторії; не змішувати в один рядок без пояснення.
3. Retro — без клієнта (типово).
4. Мова — українська.

### SLA за замовчуванням (Devlight), якщо клієнт не погодив інше

| Сигнал | SLA |
|---|---|
| Slack від клієнта (робочий час) | ≤ 4 роб. год |
| Email від клієнта | ≤ 24 роб. год |
| URGENT тег | ≤ 1 год |
| Amber → DM | того ж дня |
| Red → DM | ≤ 4 год |

---

## Antipatterns

- План без SLA
- Daily 1 год «статус» замість 15 хв standup
- Відправка EWS клієнту

---

## Self-check

- [ ] Є ритм + звітність + SLA + ескалація
- [ ] Вказані канал і тривалість для кожної зустрічі
- [ ] Власник кожного артефакту звітності зрозумілий
