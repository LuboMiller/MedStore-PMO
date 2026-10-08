---
name: pmo-generate-sprint-summary
description: Produces sprint review summary and demo notes. Use at sprint end before or after Sprint Review.
---

# Підсумок спринту (Sprint Summary)

## When to use

- **Після sprint review / demo** — зафіксувати результат для клієнта і команди
- **Перед sprint planning наступного спринту** — вхідний матеріал для планування
- **На запит стейкхолдера** — CEO / PO хочуть знати що було зроблено

---

## Role

Ти — Senior Project Manager з досвідом у Fixed Price аутсорсі. Ти генеруєш структуровані sprint summaries, які: (1) чесно відображають що було доставлено; (2) явно пояснюють незавершені US; (3) підтримують трасування velocity для прогнозування; (4) є зрозумілими як для технічної команди, так і для бізнес-стейкхолдерів.

---

## Context

Sprint Summary — це офіційний артефакт завершення спринту. У Fixed Price проєкті він виконує дві ролі одночасно:

1. **Клієнтська комунікація** — показує що було доставлено, що перенесено і чому; є основою для demo і затвердження delivered scope
2. **Внутрішній облік** — velocity, scope delta, блокери, рішення; є вхідним матеріалом для sprint planning і risk review

Критично для Fixed Price: **кожна незавершена US у закритому спринті** — це або scope creep майбутнього спринту, або потенційний CR. Фіксуємо явно, з причиною.

**Джерела даних для генерації:**
- GitHub milestone `Sprint N` — список закритих і відкритих issues (реальні факти)
- `docs/user-stories.md` — SP оцінка кожної US
- `docs/risk-register.md` — активні ризики і нові, що з'явились під час спринту
- Meeting notes спринту (передаються як вхідний матеріал)
- `CONTEXT.md` — контекст, команда, цілі

**Де зберігається результат:** `docs/sprint-summaries/sprint-N-summary.md`

---

## Instructions

```
РЕЖИМ: GENERATE

СПРИНТ: [N]
MEETING NOTES: [текст нотаток sprint review / demo — або "—" якщо немає]
ДОДАТКОВИЙ КОНТЕКСТ: [блокери, рішення, зміни scope — або "—"]
```

Claude виконує:

1. **Читає дані спринту з Jira** (обов’язкова інтеграція, не GitHub milestones):
   - `CONTEXT.md` → Jira project key
   - `python3 scripts/integrations/cli.py jira sync-pull` (або свіжий `registry/jira/`)
   - Активний / завершений sprint з `registry/jira/projects/{KEY}/boards.json` + issues у `registry/jira/projects/{KEY}/issues/`
   - За потреби JQL через `pmo-jira-ops` (closed / open у Sprint N)

2. **Читає SP / estimates** — з Jira custom fields / story points у registry; fallback `docs/user-stories.md` або BA mirror, якщо проєкт так веде

3. **Рахує velocity** — сума SP/годин закритих issues; порівнює з планом і середньою з `CONTEXT.md` / попередніх `docs/sprint-summaries/`

4. **Аналізує незавершені issues** — для кожного відкритого у спринті:
   - Причину (блокер / залежність / складність / scope change)
   - Куди переноситься (Sprint N+1 або backlog)
   - Чи є пов'язаний ризик у `docs/risk-register.md`

5. **Виявляє scope delta** — нові задачі поза планом; потенційний CR → `docs/change-requests/` / Client status sheet

6. **Фіксує рішення** — з meeting notes; Decision Log (D13) ≤ 4h

7. **Генерує summary** у `docs/sprint-summaries/sprint-N-summary.md`

8. **Оновлює velocity** — у `scripts/sync-sprint-tracker.py` словник `FACT_SP` (якщо проєкт ще використовує цей трекер)

9. **Запускає** `make sync-tracker` за потреби (опційно `GITHUB_SPRINT_REPO=…` якщо milestones ще в GitHub)

---

## Examples

**Слабкий summary (уникати):**
> Sprint 11 завершено. Команда добре попрацювала. Деякі задачі перенесено на наступний спринт через складність. Наступний спринт буде продуктивнішим.

Проблеми: немає конкретики, причини перенесення розмиті, velocity не зафіксована, ризики не зв'язані.

**Сильний summary:**
> **Sprint 11 (22.05–04.06.2026)** — Delivered 46 SP / plan 45 SP (+2%)
>
> ✅ Доставлено 17/19 US: EPIC-3 повністю закрито (US-14–18), EPIC-5 старт (US-27, US-28), EU Localization старт (US-38–40, US-46).
>
> ⚠️ Перенесено 2 US:
> - US-22 (Оплата карткою UA, 8 SP) → Sprint 12. Причина: затримка підтвердження PCI DSS scope від CTO клієнта — блокер зафіксовано у Risk R-03.
> - US-47 (Нотифікації, 3 SP) → Sprint 12. Причина: залежність від US-23 (email-підтвердження), яка також перенесена.
>
> **Velocity:** 46 SP (план 45, середня 44.2).
> **Наступний спринт:** Sprint 12 фокус — EPIC-4 завершення (US-24–26), EPIC-5 продовження (US-29–31), польські платежі старт (US-42–43).

---

## Output template

```markdown
# Sprint N Summary — поточний проєкт
**Дати:** DD.MM – DD.MM.YYYY | **Фаза:** [Build / Testing / Launch]
**Velocity:** X SP факт / 45 SP план | **Середня (S1–N):** X.X SP

---


## Company methodology

Перед роботою прочитай: knowledge/pmo-kb/04-executing/d21-sprint-review-notes.md · D9 Retrospective

Також: `CONTEXT.md` (проєкт) + `knowledge/pmo-kb/README.md` (індекс методології).

## Rules

1. **Velocity — конкретне число SP.** Не "виконали більшість задач" — а "46 SP з 45 запланованих".
2. **Кожна незавершена US має явну причину.** "Не встигли" — не причина. "Backend не завершив API endpoint X (блокер R-03)" — причина.
3. **Scope delta фіксується явно.** Якщо під час спринту додавались задачі поза планом — вони позначаються як potential CR або internal overhead.
4. **Рішення прив'язані до стейкхолдерів.** Хто прийняв рішення, коли, що вирішили.
5. **Прогноз оновлюється щоспринту.** Середня velocity перераховується, дефіцит SP оновлюється.
6. **FACT_SP оновлюється в скрипті** після кожного спринту — щоб `make sync-tracker` давав актуальні дані.
7. **Папка `docs/sprint-summaries/`** — якщо не існує, створити перед збереженням.

---

## Antipatterns

- **"Команда добре попрацювала"** — не вимірюваний результат; замінити на velocity і % доставлених US.
- **Перенесена US без причини** — в Fixed Price це потенційна претензія клієнта; причина обов'язкова.
- **Не оновлювати FACT_SP** — sprint-tracker.md покаже застарілі дані.
- **Ігнорувати ризики в summary** — якщо блокер пов'язаний з Risk Register, це зв'язок має бути явним.
- **Summary без прогнозу** — PM і стейкхолдери мають бачити чи ми на track після кожного спринту.

---

## Self-check

- [ ] Velocity вказана як конкретне число SP (не діапазон)?
- [ ] Кожна незавершена US має причину і destination (Sprint N+1 / backlog)?
- [ ] Scope delta (нові задачі поза планом) зафіксована?
- [ ] Рішення прив'язані до стейкхолдерів і дати?
- [ ] Прогноз завершення оновлено (накоп. SP / середня velocity)?
- [ ] FACT_SP оновлено у `scripts/sync-sprint-tracker.py`?
- [ ] Запущено `make sync-tracker` після оновлення velocity?
- [ ] Файл збережено у `docs/sprint-summaries/sprint-N-summary.md`?

---

*Devlight PMO · `pmo-generate-sprint-summary`*

## Additional resources

- Шаблони репозиторію: `templates/`
- Чеклісти: `checklists/`
- База знань Confluence (локальний експорт): `knowledge/pmo-kb/`
