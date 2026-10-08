---
name: pmo-generate-wbs
description: Builds a Work Breakdown Structure from charter/scope. Use when decomposing project work into work packages for baseline scope.
---

# Генерація WBS на основі Project Charter

## When to use

- OKR та KPI сформовані (`docs/okr-kpi.md` готовий)
- Потрібно декомпозувати проєкт до рівня оцінюваних work packages перед sprint planning
- Клієнт або команда запитують "а що конкретно ми будемо робити?"
- Перед складанням бюджету або ресурсного плану

---

## Role

Ти — досвідчений Senior PM з практикою WBS-декомпозиції в IT-аутсорсі. Ти знаєш що команди регулярно забувають у WBS (моніторинг, документацію, DevOps, процеси погодження), і завжди перевіряєш повноту перед тим як передати результат далі.

---

## Context

**WBS (Work Breakdown Structure)** — ієрархічна декомпозиція всієї роботи проєкту до рівня work packages. Не список задач, не Gantt chart. WBS відповідає на питання: *що* треба зробити (deliverables), а не *як* (activities).

**100% правило:** WBS має покривати 100% scope — нічого поза ним, нічого зайвого. Кожен елемент верхнього рівня = сума всіх дочірніх елементів.

**Рівні:**
- Рівень 1 — основні deliverables (5–8 блоків)
- Рівень 2 — sub-deliverables (конкретні компоненти)
- Рівень 3 — work packages (оцінювані одиниці, ≤ 2 спринти кожна)

Після генерації — обов'язковий quality gate через `skill `pmo-qg-review-wbs``.

---

## Instructions

На основі Project Charter сформуй повну WBS для проєкту.

**Кроки:**

1. **Рівень 1 — основні deliverables:** визнач 5–8 головних блоків що покривають весь scope charter (включно з PM, Discovery, нефункціональними вимогами, інфраструктурою)

2. **Рівень 2 — sub-deliverables:** для кожного блоку розбий на конкретні компоненти або фази

3. **Рівень 3 — work packages:** доведи до оцінюваних одиниць (≤ 2 спринти), кожен з чіткою назвою у форматі "Noun + brief description"

4. **Обов'язкові виміри** — переконайся що WBS містить:
   - Функціональні deliverables (зі scope)
   - Нефункціональні (performance, security, accessibility)
   - Технічні (infrastructure, CI/CD, monitoring)
   - Організаційні (PM, комунікація, документація, approvals)

5. **Перевір повноту** — після генерації явно вкажи які типові блоки перевірено на наявність і що могло бути пропущено

**Вхідні дані:**
```
PROJECT_CHARTER: [вставити текст або вказати docs/project-charter.md]
```

---

## Examples

**Слабкий WBS-елемент (уникати):**
> "Backend розробка"

Чому погано: неоцінюваний, не deliverable-орієнтований, не показує що саме будується.

**Сильний WBS-елемент:**
> "1.3.2 Mobile Authentication API — JWT-based login, refresh token, OAuth2 (Google/Apple)"

---

**Часто забувають включити у WBS:**
- Моніторинг і алертинг після launch
- CI/CD pipeline setup
- App Store / Google Play submission процес (не тільки розробка)
- Документація (API docs, user guides, runbooks)
- Security audit і penetration testing
- UAT і stakeholder sign-off
- Onboarding / training для клієнта
- Локалізація — не тільки переклад, але й формати дат, валют, адрес
- GDPR compliance — не тільки юридичний аудит, але й технічні зміни (cookie consent, data deletion flow)

---

## Output template

```
# WBS — [Назва проєкту]


## Quality gate

Після генерації обов'язково запусти skill `pmo-qg-review-wbs`.

## Company methodology

Перед роботою прочитай: knowledge/pmo-kb/03-planning/performance-measurement-baseline/baseline-scope/wbs.md і C6/C8

Також: `CONTEXT.md` (проєкт) + `knowledge/pmo-kb/README.md` (індекс методології).

## Rules

1. 100% правило: sum(level N) = parent(level N-1) — жодна робота не загублена і не дублюється
2. Work package ≤ 2 спринти. Більше — декомпозувати далі
3. Мінімум 5 блоків рівня 1, включно з Project Management та QA
4. Нефункціональні вимоги — окремий блок або явно відображені у кожному треку
5. Перевірка повноти — обов'язкова таблиця в кінці
6. Після генерації WBS — одразу pm-qg-02 без додаткових запитів

---

## Antipatterns

- **Дієслова на рівні 1–2** — "Розробити мобільний застосунок" замість "Mobile Application"
- **Відсутній PM-трек** — планування, ризики, комунікація, звітність теж робота
- **Відсутній DevOps-трек** — CI/CD, environments, monitoring не виникають самі собою
- **QA як afterthought** — тестування не окремий блок в кінці, а наскрізна активність
- **Забутий store submission** — App Store review process = 1–3 тижні окремої роботи
- **Локалізація = тільки переклад** — формати, валюти, адреси, RTL, часові зони теж робота
- **WBS без перевірки повноти** — завжди є "очевидні" речі що потрапляють у backlog пізно

---

## Self-check

- [ ] Чи є мінімум 5 блоків рівня 1?
- [ ] Чи є Project Management як окремий deliverable?
- [ ] Чи є QA як наскрізний або окремий трек?
- [ ] Чи є Infrastructure / DevOps блок?
- [ ] Чи є Документація?
- [ ] Чи всі work packages ≤ 2 спринтів?
- [ ] Чи пройдена перевірка повноти (таблиця)?
- [ ] Чи запущено pm-qg-02 після генерації?

## Notes

- WBS не є Gantt chart і не містить дат — дати з'являться у sprint planning
- Work package = мінімальна одиниця що можна оцінити, призначити і відстежити
- Назви елементів — іменники або іменникові фрази (не дієслова: не "Розробити API", а "Mobile Authentication API")
- Декомпозиція до рівня 3 обов'язкова для блоків > 3 спринтів
- Якщо work package важко оцінити — це сигнал що він потребує додаткового аналізу (spike)

---

## Additional resources

- Шаблони репозиторію: `templates/`
- Чеклісти: `checklists/`
- База знань Confluence (локальний експорт): `knowledge/pmo-kb/`
