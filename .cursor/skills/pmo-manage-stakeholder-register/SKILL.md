---
name: pmo-manage-stakeholder-register
description: Maintains the B2 Stakeholder Register with Power/Interest and C→D engagement levels. Use when initiating a project, before kick-off, or when stakeholder influence/engagement changes. Confidential — not for client.
---

# Stakeholder Register (B2)

## When to use

- Initiating: після handoff / разом із Charter
- Перед Kick-off — знати Power/Interest і стратегії
- Зміна стейкхолдера, ролі, engagement (C→D gap)

---

## Role

Ти — Senior PM. Реєстр — аналітичний інструмент управління відносинами, не телефонна книга.

---

## Context

Stakeholder Register фіксує людей/організації з інтересом до проєкту.

**Рівні залученості:** U (Unaware) → R (Resistant) → N (Neutral) → S (Supportive) → L (Leading).  
Gap між **C** (current) і **D** (desired) = завдання PM.

🔒 **Конфіденційно — не передавати клієнту.** Містить внутрішні оцінки.

Режими: **ADD** / **UPDATE** / **REVIEW** (перегляд C→D і стратегій).

---

## Instructions

1. Прочитай `CONTEXT.md` і `knowledge/pmo-kb/02-initiating/b2-stakeholder-register.md`.
2. Визнач режим і онови `docs/stakeholder-register.md` за [template.md](template.md).
3. Для кожного рядка: Power (High/Medium/Low), Interest (High/Medium/Low), C→D, стратегія engagement.
4. Внутрішніх (DM, Delivery) теж включай — вони стейкхолдери проєкту.
5. Не експортуй і не вставляй цей файл у client packs / weekly status.

**ADD:**
```
РЕЖИМ: ADD
Ім'я / роль / організація
Power / Interest
C → D
Стратегія (конкретна: канал + ритм)
```

**UPDATE:** зміна Power/Interest/C/D/стратегії + причина.

---

## Output location

```
docs/stakeholder-register.md
```

---

## Company methodology

- `knowledge/pmo-kb/02-initiating/b2-stakeholder-register.md`
- Пов’язані: B7 Communication Plan, C20 Stakeholder Engagement Plan, D12 EWS (People/Product)

## Rules

1. Конфіденційно — ніколи в client-facing артефактах.
2. C і D — обов’язкові; без gap немає actionable стратегії.
3. Стратегія конкретна («Weekly Email Пт 17:00»), не «комунікувати більше».
4. Мова — українська; імена латиницею/як у клієнта — OK.

---

## Antipatterns

- Список контактів без Power/Interest
- Відправка реєстру клієнту
- Desired = Current для всіх (мертвий реєстр)

---

## Self-check

- [ ] У кожного є Power, Interest, C→D, стратегія
- [ ] Є Decision Maker і PO
- [ ] Файл позначений як INTERNAL / confidential
