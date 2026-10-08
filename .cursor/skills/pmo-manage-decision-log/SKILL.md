---
name: pmo-manage-decision-log
description: Maintains the D13 Decision Log (DEC-NNN entries with context, alternatives, impact). Use when a key decision is made in a meeting or Slack — capture within 4 hours — or when auditing what was formally decided.
---

# Decision Log (D13)

## When to use

- Ключове рішення на зустрічі / у Slack / email
- Після Issue resolve, що змінює scope/schedule/cost/quality
- Аудит «ми ж домовлялись інакше»

---

## Role

Ти — Senior PM (або BA фіксує, PM перевіряє). Незафіксоване рішення = офіційно не існує.

---

## Context

Decision Log — реєстр ключових рішень: хто, на якій підставі, які альтернативи.

**Правило Devlight:** рішення усно / у Slack → зафіксувати в Decision Log **протягом 4 годин**.

⚠️ Decision Log ≠ Meeting Minutes. Minutes = протокол. Decision Log = лише ключові рішення в структурованому вигляді.

Режими: **ADD** / **SUPERSEDE** / **REVERSE** / **INDEX** (оновити індекс).

---

## Instructions

1. Прочитай `knowledge/pmo-kb/04-executing/d13-decision-log.md`.
2. Створи файл рішення + онови індекс:
   - `docs/decisions/DEC-NNN-{slug}.md`
   - `docs/decisions/README.md` (індекс усіх DEC)
3. Поля: ID, дата, рішення (одне речення), контекст, альтернативи+чому відхилено, вплив (scope/schedule/cost/quality), хто вирішив, статус Active / Superseded / Reversed.
4. Якщо рішення з мітингу — можна після `pmo-extract-meeting-notes`, але Decision Log ведеться окремо.

Шаблон: [template.md](template.md)

---

## Output location

```
docs/decisions/DEC-NNN-{slug}.md
docs/decisions/README.md
```

---

## Company methodology

- `knowledge/pmo-kb/04-executing/d13-decision-log.md`
- Пов’язані: Issue Log, Change Requests, Meeting Notes

## Rules

1. Фіксація ≤ 4 год після усного/Slack рішення.
2. ID `DEC-001…` унікальний.
3. Статус: Active / Superseded / Reversed (не видаляти історію).
4. При SUPERSEDE — вказати новий DEC-ID.
5. Мова — українська.

---

## Antipatterns

- Писати повний протокол зустрічі в Decision Log
- Рішення без альтернатив («так вирішили»)
- Відсутність імені/ролі Approver

---

## Self-check

- [ ] Одне чітке речення «що вирішено»
- [ ] Альтернативи з причинами відхилення
- [ ] Індекс README оновлено
