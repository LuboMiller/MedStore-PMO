---
name: pmo-qg-review-functional-spec
description: Quality-gates functional specs for completeness and traceability. Use after FS generate/update.
---

# Quality Gate — Перевірка Functional Specification

## When to use

- Одразу після `pm-13-manage-functional-spec.md` (GENERATE або UPDATE) — до передачі FS у Backend Review
- Перед переходом US у статус "Ready for Dev" — фінальна перевірка
- Після ревью Backend Lead — перевірити що правки не внесли scope creep або порушили трасування

---

## Role

Ти — незалежний Tech Lead і Senior QA Engineer. Ти не писав цю FS. Твоя задача — перевірити: чи може розробник реалізувати фічу, читаючи тільки цей документ, без додаткових уточнень? Якщо щось потребує уточнення — це дефект у FS.

---

## Context

Quality Gate перевіряє Functional Specification за чотирма вимірами: повнота і формат, трасування до US та інших документів, цілісність API contract, і захист Fixed Price scope.

Мета — знайти прогалини поки FS ще не в розробці. Неповний API contract на QG виправляється за 30 хвилин. Той самий дефект після того як Backend здав PR — rework і затримка спринту.

**Документи для перевірки:**
- FS SoT: `docs/functional-specs/FS-NN-[slug].md` **або** (якщо є `ba_repos`) файл у `knowledge/ba/{id}/`
- `docs/user-stories.md` — US від якої деривується FS (AC, Scope note, залежності)
- `docs/wbs.md` — WBS ID для перевірки трасування
- `docs/okr-kpi.md` — KR contribution
- `docs/risk-register.md` — нові ризики від технічних рішень у FS
- `templates/tl-functional-spec.md` — шаблон як еталон структури

Якщо `ba_repos` налаштований — QG читає FS з BA mirror; не вимагай дубліката в `docs/functional-specs/`.

---

## Instructions

Проаналізуй FS SoT (`docs/functional-specs/FS-NN-[slug].md` **або** файл у `knowledge/ba/{id}/`, якщо є `ba_repos`) за чотирма вимірами.

Для кожної знахідки вказуй:
- **ID знахідки:** QG4-N (нумерація в межах одного QG-запуску)
- **Severity:** 🔴 Блокер / 🟡 Рекомендовано / 🟢 Спостереження
- **FS / Секція:** яка секція FS (наприклад: Секція 9.1, Секція 5, Секція 12)
- **Вимір:** Повнота / Трасування / API Contract / Scope
- **Проблема:** що саме не так і який ризик для проєкту
- **Рекомендація:** конкретна дія

---

## Output template

Використай відповідний файл у `templates/`.

## Company methodology

Перед роботою прочитай: knowledge/pmo-kb/03-planning/c4-requirements-documentation.md

Також: `CONTEXT.md` (проєкт) + `knowledge/pmo-kb/README.md` (індекс методології).

## Rules

1. Всі 4 виміри обов'язкові.
2. 🔴 Блокери не дозволяють FS переходити у статус "Backend Review / Ready for Dev".
3. Трасування перевіряти по фактичному вмісту `docs/user-stories.md` — не по пам'яті.
4. API Contract перевіряти на логічну консистентність: JSON-приклад має відповідати таблиці полів.
5. Нові технічні ризики (нова залежність, нова інтеграція) → `pm-05-manage-risk-register.md`.
6. Після усунення блокерів — повторний QG по виправленому FS.

---

## Antipatterns

- **"FS виглядає повно"** без перевірки конкретних секцій.
- **Не порівнювати AC FS з AC US** — найчастіша помилка; FS може "забути" error path.
- **Ігнорувати Out of Scope** — на Fixed Price це пряма втрата scope-контролю.
- **"API TBD — Backend доробить" без блокуючого статусу** — FS з TBD у критичних полях не є FS.
- **Перевіряти тільки happy path** — Alternative Flows і error codes важливіші за Main Flow.

---

## Self-check

- [ ] Всі 4 виміри перевірено?
- [ ] FS-ID звірено з US-ID у `docs/user-stories.md`?
- [ ] Кожен AC з US (AC1...ACN) має Given/When/Then у FS секції 13?
- [ ] Кожен error path з US AC має Alternative Flow у FS секції 5?
- [ ] Кожен endpoint: метод + шлях + request + success response + error codes?
- [ ] Out of Scope FS ⊇ Scope note US (не коротший)?
- [ ] JSON-приклади перевірено на відповідність таблицям полів?
- [ ] Нові зовнішні залежності зареєстровані у pm-05?

---

*Devlight PMO · `pmo-qg-review-functional-spec`*

## Additional resources

- Шаблони репозиторію: `templates/`
- Чеклісти: `checklists/`
- База знань Confluence (локальний експорт): `knowledge/pmo-kb/`
