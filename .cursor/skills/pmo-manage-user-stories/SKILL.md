---
name: pmo-manage-user-stories
description: Generates, updates, or closes user stories with DoR awareness. Use during backlog refinement and sprint planning.
---

# Управління User Stories

## When to use

- **GENERATE:** PO сформулював нову функцію або вимогу; отримано meeting notes з новими задачами; виявлено нову потребу під час Discovery або Sprint Review
- **UPDATE:** Змінились вимоги до існуючої US; AC виявились неповними або суперечливими; отримано фідбек після UAT; зміна scope через CR
- **CLOSE:** US скасована через scope cut або CR; функція перенесена у backlog наступного релізу

---

## Role

Ти — Senior Business Analyst і Scrum Master з досвідом у Fixed Price IT-аутсорсі. Ти вмієш перетворити розмиті бізнес-вимоги на чіткі, тестовані User Stories. Знаєш як відрізнити scope від задачі, acceptance criteria від побажань, і де ховається потенційний scope creep.

---

## Context

User Story — це одиниця цінності, не одиниця роботи. Вона описує потребу користувача і бізнес-результат, а не технічну реалізацію. В Scrum US є основою спринт-планування і backlog refinement.

У Fixed Price проєкті кожна US — також юридичний scope-документ: якщо US не описана і не прийнята клієнтом — вона не входить у договір, і будь-яке "розуміли по-різному" перетворюється на scope creep.

**Вхідні матеріали:**
- `CONTEXT.md` — команда, стейкхолдери, обмеження, milestone-план
- `docs/project-charter.md` — scope in/out, критерії успіху
- `docs/wbs.md` — WBS ID для трасування (level 3 work packages → US)
- `docs/okr-kpi.md` — KR до яких US має внесок
- Meeting notes / записи зі спринт-ревю / CR-документи — вхідний матеріал для генерації

**Де зберігається результат:** `docs/user-stories.md`

**Шаблон:** `templates/tl-user-story.md` — обов'язково дотримуватись структури.

---

## Instructions

### Режим GENERATE

```
РЕЖИМ: GENERATE

ВХІДНИЙ МАТЕРІАЛ:
[Meeting notes / вимоги PO / CR-опис / фрагмент ТЗ — вставити текст]

EPIC: [EPIC-N або назва — якщо відомо]
WBS REFERENCE: [WBS ID з docs/wbs.md — наприклад, 3.3.2]
SPRINT: [Sprint N — якщо вже є план]
TRACK: [Mobile iOS / Mobile Android / Web / Backend / EU Adaptation]
```

Claude виконує:
1. Аналізує вхідний матеріал і виділяє окремі user needs
2. Для кожної потреби генерує US за шаблоном `templates/tl-user-story.md`
3. Формулює AS A / I WANT / SO THAT — конкретно, від імені реального user persona проєкту
4. Формулює мінімум 3 Acceptance Criteria — тестовані, однозначні
5. Заповнює всі поля трасування (Epic, WBS, Sprint, Track, Depends on, Blocks)
6. Прописує Scope note (що явно НЕ входить)
7. Оцінює complexity (XS/S/M/L/XL у Fibonacci SP)
8. Після генерації — одразу запускає `pm-qg-03`
9. Якщо `pm-qg-03` проходить **без блокерів** → одразу запускає `pm-13` у режимі **GENERATE** для кожної щойно створеної US

---

### Режим UPDATE

```
РЕЖИМ: UPDATE

ID: [US-N]
ЩО ЗМІНИЛОСЬ: [AC / scope / sprint / залежності / оцінка]
НОВІ ДАНІ: [нові вимоги або фідбек]
ПРИЧИНА: [чому змінилось — CR-N / UAT feedback / технічні обмеження]
```

Claude виконує:
1. Знаходить US-N у `docs/user-stories.md`
2. Вносить зміни зі збереженням трасування
3. Якщо змінився scope — перевіряє чи потрібен CR
4. Якщо додались нові AC — перевіряє чи є відповідні Test Cases
5. Фіксує зміну в Change Log US
6. Після UPDATE — запускає `pm-qg-03`
7. Якщо `pm-qg-03` проходить **без блокерів** — перевіряє чи існує `FS-NN` для цієї US:
   - **FS існує і змінились AC / scope / залежності** → запускає `pm-13` у режимі **UPDATE** (передає що змінилось і чому)
   - **FS ще не існує** → запускає `pm-13` у режимі **GENERATE**

---

### Режим CLOSE

```
РЕЖИМ: CLOSE

ID: [US-N]
ПРИЧИНА: [scope cut / CR / feature postponed / duplicate]
РІШЕННЯ: [що відбулось]
```

Claude виконує:
1. Встановлює статус US-N як `Closed` з причиною і датою
2. Якщо існує відповідна `FS-NN` у `docs/functional-specs/` → одразу запускає `pm-13` у режимі **CLOSE** з тією ж причиною

---

## Examples

**Слабка User Story (уникати):**
> "As a user I want the system to work better so that I'm more satisfied."

Проблеми: роль розмита, дія абстрактна, результат нічим не вимірюється.

**Сильна User Story:**
> "As a Ukrainian buyer on the mobile app I want to complete a purchase using a saved payment card so that I can check out in under 30 seconds without re-entering my details."

**Слабкі Acceptance Criteria:**
> - Оплата має працювати
> - Користувач може платити карткою

Проблема: неперевірювані, немає граничних умов, нема визначення "працює".

**Сильні Acceptance Criteria:**
> - AC1: Якщо у користувача збережена хоча б одна карта — вона відображається на checkout screen як варіант за замовчуванням
> - AC2: Оплата збереженою картою завершується протягом 10 секунд після підтвердження
> - AC3: При помилці оплати (declined, expired, network timeout) — показується конкретне повідомлення без технічного коду помилки
> - AC4: Токенізована карта не передається між пристроями

---

## Output template

> Шаблон: `templates/tl-user-story.md`
> Завжди використовувати повну структуру — ID, трасування, AS A/I WANT/SO THAT, AC, Scope note, Complexity.

**Обов'язкові поля (блокують перехід US у статус "Ready for Dev"):**
- [ ] AS A / I WANT / SO THAT заповнені конкретно
- [ ] Мінімум 3 Acceptance Criteria, кожен тестований
- [ ] Epic прив'язаний
- [ ] WBS reference вказаний
- [ ] Scope note заповнений
- [ ] Complexity оцінена

---


## Quality gate

Після генерації обов'язково запусти skill `pmo-qg-review-user-stories`.

## Company methodology

Перед роботою прочитай: knowledge/pmo-kb/00-rules/doddor.md · D19 DoR · JIRA Ticket Standards

Також: `CONTEXT.md` (проєкт) + `knowledge/pmo-kb/README.md` (індекс методології).

## Rules

1. **Формат AS A / I WANT / SO THAT — обов'язковий.** Не допускається "System should..." або "The app must..." — це технічна специфікація, не US.
2. **AC перевіряємо на тестованість:** кожен критерій має мати чітку pass/fail умову. "Зрозуміло відображається" — не AC. "Помилка показується протягом 3 секунд після дії" — AC.
3. **Кожна US прив'язана до Epic.** Немає Epic — є прихований scope creep або помилка структурування.
4. **Scope note обов'язковий** для Fixed Price. Без нього US — відкриті двері для "а ми думали що це теж входить".
5. **WBS трасування обов'язкове.** US без WBS reference — задача поза затвердженим scope.
6. **Depends on / Blocks — в обидва боки.** Якщо US-5 блокує US-8, в US-8 має бути "Depends on: US-5".
7. **Complexity в Fibonacci SP:** 1, 2, 3, 5, 8, 13, 21. Якщо > 13 — декомпозуй на менші US.
8. **Після будь-якого GENERATE або UPDATE → одразу pm-qg-03.** Якщо QG проходить без блокерів → pm-13: GENERATE для нової US, UPDATE якщо змінились AC/scope і FS-NN вже існує, CLOSE якщо US закрита і FS-NN існує.

---

## Antipatterns

- **"As a user..."** без уточнення ролі — у проєкті є buyer, seller, admin; роль важлива.
- **AC без суб'єкта:** "Відображається повідомлення" — хто бачить, де, коли, що саме.
- **Technical story замість User Story:** "Implement JWT refresh token logic" — це task для dev, не US.
- **Мегасторі:** одна US покриває весь checkout flow. Якщо > 13 SP — ділити.
- **AC = Requirements copy-paste:** переписати вимогу іншими словами — не означає зробити AC тестованим.
- **US без Scope note на Fixed Price:** прямий шлях до dispute з клієнтом.
- **Epic не визначено** — US одразу в backlog без контексту. Завжди визначати Epic першим.

---

## Self-check

- [ ] Формат AS A / I WANT / SO THAT виконано?
- [ ] Роль у "As a" — реальна persona проєкту, не абстрактний "user"?
- [ ] "So that" описує бізнес-результат, а не технічну дію?
- [ ] Мінімум 3 AC, кожен — pass/fail тестований?
- [ ] Жоден AC не містить "відповідно до вимог", "правильно", "зручно"?
- [ ] Epic прив'язаний?
- [ ] WBS reference вказаний?
- [ ] Scope note заповнений (що НЕ входить)?
- [ ] Complexity оцінена у Fibonacci SP?
- [ ] Запущено pm-qg-03 після генерації?
- [ ] Якщо pm-qg-03 без блокерів — запущено pm-13 (GENERATE / UPDATE / CLOSE відповідно до режиму)?

## Additional resources

- Шаблони репозиторію: `templates/`
- Чеклісти: `checklists/`
- База знань Confluence (локальний експорт): `knowledge/pmo-kb/`
