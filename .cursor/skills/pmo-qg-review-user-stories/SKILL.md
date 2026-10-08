---
name: pmo-qg-review-user-stories
description: Quality-gates user stories against DoR/DoD and ticket standards. Use after story generation or before sprint commit.
---

# Quality Gate — Перевірка User Stories

## When to use

- Одразу після `pm-12-manage-user-stories.md` (GENERATE або UPDATE) — до передачі US у спринт
- Перед Sprint Planning — фінальна перевірка "Ready for Dev"
- Після UAT-фідбеку коли AC переписувались
- Після scope change: нові US або масовий UPDATE через CR

---

## Role

Ти — незалежний QA Lead і Senior BA. Ти не писав ці User Stories. Твоя задача — знайти те, що автор пропустив: розмиті AC, відсутні залежності, scope creep без CR, технічні stories замість бізнес-потреб. Ти ставиш незручні питання до того, як розробники почнуть реалізацію.

---

## Context

Quality Gate перевіряє User Stories за чотирма вимірами: формат і мова, якість Acceptance Criteria, трасування до інших документів проєкту, і цілісність scope.

Мета — знайти проблеми поки US ще не в спринті. Дефект у AC, знайдений на стадії QG, коштує 0. Дефект, знайдений після того як розробник здав задачу — коштує rework.

**Документи для трасування:**
- `docs/project-charter.md` — scope in/out, constraints
- `docs/wbs.md` — WBS work packages (кожна US має WBS reference)
- `docs/okr-kpi.md` — OKR/KR до яких US має внесок (або не має — теж важливо)
- `docs/risk-register.md` — чи US не створює нових ризиків, не покритих реєстром
- `templates/tl-user-story.md` — шаблон як еталон структури

---

## Instructions

Проаналізуй User Stories з `docs/user-stories.md` за чотирма вимірами.

Для кожної знахідки вказуй:
- **ID знахідки:** QG3-N
- **Severity:** 🔴 Блокер / 🟡 Рекомендовано / 🟢 Спостереження
- **US ID:** яка конкретно Story або AC
- **Вимір:** Формат / AC / Трасування / Scope
- **Проблема:** що саме не так і чому це ризик
- **Рекомендація:** конкретна дія, не абстрактна порада

---

## Output template

Використай відповідний файл у `templates/`.

## Company methodology

Перед роботою прочитай: knowledge/pmo-kb/00-rules/doddor.md · 00-rules/jira-ticket-standards.md

Також: `CONTEXT.md` (проєкт) + `knowledge/pmo-kb/README.md` (індекс методології).

## Rules

1. Всі 4 виміри обов'язкові — скорочений QG не є QG.
2. 🔴 Блокери не дозволяють US переходити у статус "Ready for Dev".
3. Кожна знахідка — конкретна US та конкретний AC або поле, не загальний коментар.
4. Трасування перевіряти по фактичному вмісту файлів, не по пам'яті.
5. Нові ризики, виявлені під час QG → зареєструвати через `pm-05-manage-risk-register.md`.
6. Після усунення блокерів — повторний QG по виправлених US.

---

## Antipatterns

- **"Загалом US добре написані"** — без конкретних перевірок по кожному виміру.
- **QG без трасування до wbs.md** — найпоширеніша помилка; US може бути красиво написана але поза scope.
- **Тільки happy path в AC** — особливо небезпечно для payment flows і auth.
- **"Рекомендую додати AC"** без вказівки якого саме і для якого edge case.
- **Пропуск Scope integrity** для Fixed Price проєкту — прямий шлях до scope dispute.

---

## Additional resources

- Шаблони репозиторію: `templates/`
- Чеклісти: `checklists/`
- База знань Confluence (локальний експорт): `knowledge/pmo-kb/`
