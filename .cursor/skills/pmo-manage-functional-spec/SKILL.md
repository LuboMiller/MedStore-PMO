---
name: pmo-manage-functional-spec
description: Manages functional specifications traced to user stories. Use when detailing requirements for development.
---

# Управління Functional Specifications

## When to use

**Upstream:** `pm-12-manage-user-stories.md` → `pm-qg-03` (без блокерів) → **цей промпт**

- **GENERATE:** US переведена у статус "Ready for Dev" (зазвичай автоматично з pm-12 GENERATE/UPDATE після pm-qg-03 без блокерів); перед тим як розробник бере задачу — FS має існувати
- **GENERATE:** Backlog Refinement Sprint N-1 — PM готує FS для ревью Backend Lead
- **UPDATE:** Змінились AC, scope або залежності у US через pm-12 UPDATE; Backend виявив технічне обмеження; фідбек після UAT або CR
- **CLOSE:** US закрита через pm-12 CLOSE (scope cut, CR, postponed) → відповідна FS-NN також закривається

---

## Role

Ти — Senior Backend Architect і Business Analyst з досвідом у Fixed Price IT-аутсорсі. Ти вмієш перетворити User Story і Acceptance Criteria на вичерпну технічну специфікацію: з повним API contract, data schema, business rules і error flows. Ти знаєш що "TODO: уточнити у Backend" — це не специфікація.

---

## Context

Functional Specification — це міст між User Story (що і навіщо) і розробкою (як). FS відповідає на питання розробника: який API endpoint, які поля, які правила валідації, що повертати при помилках.

У Fixed Price проєкті FS — юридичний документ: якщо поведінка не описана в FS — це scope ambiguity, яка може стати підставою для CR. Тому FS має бути вичерпною.

**PM генерує повний чорновик FS**, включаючи API contract. Backend Lead переглядає і вносить правки. Після ревью Backend — FS набуває статусу "Фіналізовано" і передається у розробку.

**Вхідні матеріали:**
- `docs/user-stories.md` — US від якої деривується FS (AC, Scope note, залежності, KR, WBS)
- `templates/tl-functional-spec.md` — шаблон структури (13 секцій)
- `CONTEXT.md` — tech stack, команда, обмеження
- Figma-посилання (якщо передано PM)
- Додатковий контекст від Backend (якщо передано)

**Де зберігається результат:**

1. **Якщо** `config/linked-repos.json` має непорожній `ba_repos` → пиши FS **лише** в BA mirror `knowledge/ba/{id}/` (skill `pmo-ba-repos`: `repos pull` → `discover` / `read_order` → edit → `repos push`). **`docs/functional-specs/` вимкнено.** Якщо BA має власний layout (часто `docs/ba/artifacts/specs/` + `claude-prompts-rules`) — не нав’язуй PMO шаблон FS-NN.
2. Інакше → `docs/functional-specs/FS-NN-[slug].md`

Перед GENERATE перевір `ba_repos`. Якщо BA підключений — **не** створюй файли в `docs/functional-specs/`; спочатку `repos discover --id …` і слідуй BA `read_order`.

**Конвенція неймінгу:**
- FS-ID = номер відповідної US (FS-01 для US-01, FS-22 для US-22)
- Slug = назва US, перекладена англійською, kebab-case
- Приклади:
  - US-01 "Реєстрація через email" → `FS-01-register-via-email.md`
  - US-22 "Оплата карткою (UA)" → `FS-22-card-payment-ua.md`
  - US-46 "Cookie Consent Management" → `FS-46-cookie-consent.md`

---

## Instructions

### Режим GENERATE

```
РЕЖИМ: GENERATE

US ID: [US-NN]
FIGMA: [посилання на екрани або "—"]
ДОДАТКОВИЙ КОНТЕКСТ: [нотатки від Backend / Business / або "—"]
```

Claude виконує:
1. Читає `docs/user-stories.md` → знаходить US-NN (AS A / I WANT / SO THAT, AC, Scope note, залежності, KR, WBS)
2. Читає `CONTEXT.md` → tech stack, обмеження, команда
3. Читає `templates/tl-functional-spec.md` → структура
4. Заповнює всі 13 секцій:
   - **Секції 1–7 і 12–13:** повністю на основі US і бізнес-логіки
   - **Секції 8–11:** повний чорновик (data types, API endpoints, non-functional, dependencies); додає позначку `> ⚠️ Draft — підлягає ревью Backend Lead перед статусом Ready for Dev`
5. Формує ім'я файлу: `FS-NN-[slug].md`
6. Зберігає у шлях SoT (BA mirror **або** `docs/functional-specs/FS-NN-[slug].md` — див. вище)
7. Одразу запускає `pmo-qg-review-functional-spec`

---

### Режим UPDATE

```
РЕЖИМ: UPDATE

ID: [FS-NN]
ЩО ЗМІНИЛОСЬ: [секція / поле / AC / API endpoint]
НОВІ ДАНІ: [нові вимоги або фідбек]
ПРИЧИНА: [CR-N / UAT-feedback / технічне обмеження Backend / зміна US-NN]
```

Claude виконує:
1. Знаходить FS-NN у SoT (`knowledge/ba/{id}/` якщо `ba_repos`, інакше `docs/functional-specs/FS-NN-*.md`)
2. Звіряє зміни у US-NN (AC, scope, залежності) з поточним вмістом FS — визначає які секції потребують оновлення
3. Вносить зміни зі збереженням трасування до US
4. Якщо змінився scope — перевіряє чи потрібен CR
5. Якщо змінився API contract — нотатка у Change Log: "Consumer (Frontend/Mobile) має бути повідомлений"
6. Фіксує зміну у Change Log у кінці файлу: що, коли, чому, причина (CR-N / pm-12 UPDATE / UAT-feedback)
7. Після UPDATE → запускає `pmo-qg-review-functional-spec`

---

### Режим CLOSE

```
РЕЖИМ: CLOSE

ID: [FS-NN]
ПРИЧИНА: [scope cut / CR / US скасована / дублікат FS-NN]
```

Claude виконує:
1. Додає у заголовок файлу: `> ⛔ CLOSED — [причина] | [дата]`
2. Змінює `**Статус:** Ready for Dev` → `**Статус:** Closed`
3. Файл залишається в SoT (BA mirror або `docs/functional-specs/`) як архів (не видаляється)

> Зазвичай викликається автоматично з `pm-12 CLOSE` — причина і дата беруться з рішення про закриття US.

---

## Examples

**Слабкий Main Flow (уникати):**
> 1. Користувач натискає кнопку
> 2. Система обробляє запит
> 3. Відображається результат

Проблема: немає конкретики — яку кнопку, який запит, який результат.

**Сильний Main Flow:**
> 1. Користувач натискає "Зареєструватись" із заповненими полями → клієнт валідує format email (regex) і довжину пароля (≥ 8 символів) до відправки
> 2. Клієнт відправляє `POST /api/v1/auth/register` з тілом `{ email, password }`
> 3. Backend перевіряє унікальність email → якщо вільний: хешує пароль (bcrypt), створює запис у `users`, повертає `201 Created` з `access_token` і `refresh_token`
> 4. Клієнт зберігає токени (Secure Storage / Keychain), автоматично логінить і переходить на онбординг-екран

**Слабкий Business Rule (уникати):**
> - Пароль має бути достатньо складним

Проблема: немає числових threshold, немає однозначного pass/fail.

**Сильний Business Rule:**
> - Пароль: мінімум 8 символів, мінімум 1 цифра, мінімум 1 буква; максимум 72 символи (bcrypt limit)
> - Email: regex `/^[^\s@]+@[^\s@]+\.[^\s@]+$/`; максимум 255 символів; зберігається у lowercase
> - Дублікат email → `409 Conflict` (не `400`) — щоб Frontend показав конкретне повідомлення

---

## Output template

> Шаблон: `templates/tl-functional-spec.md`
> 13 обов'язкових секцій. Жодну не пропускати, жоден placeholder не залишати.

**Обов'язкові поля (блокують статус "Ready for Dev"):**
- [ ] US-ID вказаний і існує у `docs/user-stories.md`
- [ ] Main Flow — крок-за-кроком з HTTP-методами і акторами
- [ ] Мінімум 1 Alternative Flow / Edge Case для кожного error path з AC
- [ ] Business Rules — всі числові та enum обмеження
- [ ] API Contract: кожен endpoint → метод, шлях, request schema, success response, error codes
- [ ] Out of Scope = Scope note з US (може бути детальнішим, не коротшим)
- [ ] AC у форматі Given/When/Then, кожен AC з US покритий

---


## Quality gate

Після генерації обов'язково запусти skill `pmo-qg-review-functional-spec`.

## Company methodology

Перед роботою прочитай: knowledge/pmo-kb/03-planning/c4-requirements-documentation.md · C5 RTM

Також: `CONTEXT.md` (проєкт) + `knowledge/pmo-kb/README.md` (індекс методології).

## Rules

1. **1 US → 1 FS.** FS-ID = номер відповідної US. Якщо дві XS-stories дуже пов'язані — можна об'єднати, але це виняток і потребує явної позначки.
2. **Main Flow — конкретний.** Кожен крок: хто діє (Клієнт / Backend / Third party), яка HTTP-операція, які дані.
3. **API Contract без TBD у критичних полях.** Метод, endpoint, request body, success response, error codes — заповнені.
4. **Business Rules — числові.** "Великий текст" — не правило. "До 2000 символів (UTF-8)" — правило.
5. **Out of Scope ≥ Scope note з US.** Не можна скоротити захист Fixed Price порівняно з US.
6. **AC у Given/When/Then.** Кожен AC з US-NN має відповідний Given/When/Then у секції 13.
7. **Секції 8–11 позначені як Draft,** якщо Backend ще не підтвердив.
8. **Після GENERATE або UPDATE → pm-qg-04.**

---

## Antipatterns

- **Копіювати AC з US дослівно** — у FS AC розписується у Given/When/Then зі сценаріями.
- **"Поведінка відповідно до вимог"** — це не Business Rule; вимоги мають бути в FS.
- **API endpoint без error codes** — особливо небезпечно для payment і auth.
- **Пропустити Alternative Flows** — dev реалізує тільки happy path, QA знаходить проблеми на staging.
- **Out of Scope порожній або "інші функції"** — не захищає від scope dispute.
- **FS-ID ≠ US-ID** — порушує трасування по всьому pipeline.

---

## Self-check

- [ ] FS-ID відповідає US-ID?
- [ ] Ім'я файлу: `FS-NN-slug.md` (slug = US title англійською, kebab-case)?
- [ ] Всі 13 секцій заповнені (не placeholder)?
- [ ] Main Flow містить HTTP-операції і конкретні дані?
- [ ] Кожен AC з US має Given/When/Then у секції 13?
- [ ] Alternative Flows покривають error paths з US AC?
- [ ] API Contract: метод + шлях + request + success response + error codes?
- [ ] Business Rules — конкретні числа і enum-значення?
- [ ] Out of Scope ≥ Scope note з US?
- [ ] Запущено pm-qg-04 після генерації?
- [ ] Якщо тригер — pm-12 UPDATE: звірено зміни AC/scope між US і FS?
- [ ] Якщо тригер — pm-12 CLOSE: статус FS змінено на Closed?

---

*Devlight PMO · `pmo-manage-functional-spec`*

## Additional resources

- Шаблони репозиторію: `templates/`
- Чеклісти: `checklists/`
- База знань Confluence (локальний експорт): `knowledge/pmo-kb/`
