---
name: pmo-analyze-scope-change
description: Assesses scope changes (quick impact or full CR). Use when PO/client requests new work mid-delivery.
---

# Аналіз Scope Change (QUICK / CR)

## When to use

- **QUICK:** PO/CMO/CTO кидає нову задачу під час планінгу або в чаті — потрібна швидка відповідь "чи поміщається і що впаде"
- **CR:** Клієнт хоче нову функціональність поза поточним scope — потрібен офіційний CR-документ для decision meeting із стейкхолдерами
- **Будь-коли:** хтось каже "це ж маленька задача", "просто додайте", "це логічне продовження"

---

## Role

Ти — Senior Project Manager який перетворює "хочу нову фічу" у кількісний аналіз з рекомендацією. Ти:
- Відрізняєш "розширення існуючої фічі" від "нової системи" — і пояснюєш різницю стейкхолдерам
- Завжди рахуєш не тільки SP, але й вплив на дедлайн і бюджет
- Даєш конкретну рекомендацію, а не список опцій без висновку

---

## Context

Scope change — одна з головних причин зриву дедлайнів і бюджетного overrun. Два режими вирішують різні задачі:

**QUICK** — відповідь за 2 хвилини до або під час sprint planning. Показує чи є місце в спринті і що потрібно відкласти. Не зберігається як документ.

**CR (Change Request)** — формальний impact assessment, який PM кладе на стіл стейкхолдерам перед decision meeting. Містить scope definition, SP estimate, capacity варіанти, timeline і budget impact, рекомендацію. Зберігається у `docs/change-requests/CR-NN-{slug}.md`.

Після approve / оцінки:

1. **CHANGE REQUESTS (D4)** — рядок у `docs/change-requests/README.md` + `change-log.json`; upsert Confluence project space → *CHANGE REQUESTS*.
2. **Plan** у Google Client Project status sheet через `pmo-manage-client-status-sheet` (ADD-CR → `СHANGE REQUESTS`; NEW → ADD-FEATURE / WBS ESTIM). Не плутати з pivot `CR`.
3. За потреби formal impact: `docs/change-requests/CR-NN-{slug}.md` ([template.md](../../../docs/change-requests/template.md)).

**Джерела даних:**
- `CONTEXT.md` — velocity, BAC, дедлайни, поточний спринт
- `dashboards/sprint-tracker.md` — SP left in sprint, capacity
- `docs/risk-register.md` — нові ризики від CR
- `dashboards/roadmap.md` — milestone вплив
- `docs/client-status-sheet/operating-playbook.md` — якщо проєкт веде Client status spreadsheet

---

## Instructions

```
РЕЖИМ: QUICK | CR

--- QUICK ---
ЗАДАЧА: [опис]
SP ОЦІНКА: [N або "невідомо"]
ПОТОЧНИЙ СПРИНТ: [N із 20]
SP ЗАЛИШОК У СПРИНТІ: [N]
СПРИНТІВ ДО M6 (mobile launch): [N]
СПРИНТІВ ДО M7 (EU launch): [N]

--- CR ---
CR НАЗВА: [назва фічі]
ЗАПИТ ВІД: [ім'я (роль), дата]
ОПИС: [що хоче клієнт, для чого, контекст]
SP ОЦІНКА: [N або "TBD — очікую від TL"]
ВИМОГИ ВІД КЛІЄНТА: [деталі або "[УТОЧНИТИ]"]
ПОТОЧНИЙ СПРИНТ: [N із 20]
UNTOUCHABLE SCOPE: [що не можна чіпати за словами стейкхолдерів]
```

---

Claude виконує залежно від режиму:

### Режим QUICK

1. Порівняти SP задачі з залишком у спринті
2. Якщо не поміщається — назвати що потрібно прибрати (конкретна US + SP)
3. Перевірити чи зачіпається milestone (M4, M6, M7)
4. Дати рекомендацію: взяти / перенести / відхилити

### Режим CR

1. **Читає** `CONTEXT.md`, `dashboards/sprint-tracker.md`, `dashboards/roadmap.md`, `docs/risk-register.md`
2. **Scope Definition** — що входить у MVP, що виноситься в Phase 2, що вже є в проєкті
3. **SP Estimate** — мінімальний / MVP / повний варіант; якщо TL ще не дав оцінку — позначити `[УТОЧНИТИ]`
4. **Capacity Analysis** — мінімум 3 варіанти (displacement / +ресурс / Phase 2 / відхилити)
5. **Timeline Impact** — вплив на M6 і M7 по кожному варіанту
6. **Budget Impact** — новий EAC і VAC по кожному варіанту
7. **Нові ризики** — що CR додає до risk-register
8. **Рекомендація PM** — один варіант з обґрунтуванням
9. **Decision table** — від кого яке рішення потрібне і до коли
10. **Зберігає** impact у `docs/change-requests/CR-NN-{slug}.md` (якщо formal CR)
11. **Оновлює реєстр CHANGE REQUESTS** (`docs/change-requests/README.md` + JSON) і Confluence *CHANGE REQUESTS*
12. Після approve — plan у sheet (`pmo-manage-client-status-sheet`)

---

## Examples

**QUICK — слабко:**
> Задача на 8 SP, можна взяти в спринт якщо є місце.

Немає: що випадає, чи впливає на milestone, чи є ризики.

**QUICK — сильно:**
> 8 SP не поміщається (залишок 5 SP). Щоб взяти — прибираємо US-44 (cart sorting, 8 SP) → переносимо в Sprint 15. Milestone M4 не зачіпається. Рекомендую: взяти зараз, перенести US-44.

---

**CR — слабко:**
> Нова фіча займе ~2 місяці і вплине на дедлайн.

Немає: scope definition, звідки беремо SP, конкретні цифри, рекомендація з обґрунтуванням.

**CR — сильно:**
> CR-01: Seller Push Campaigns. MVP = 60 SP. Три варіанти capacity: displacement (M7 +4w), +ресурс ($9,600), мінімальний hook (20 SP, без впливу на M7). Рекомендація: Варіант C — мінімальний hook зараз, повний campaign manager після M7 launch.

---

## Output template

### QUICK output (inline, не зберігається)

```


## Company methodology

Перед роботою прочитай: knowledge/pmo-kb/04-executing/d4-change-requests.md · D14 Scope Change Log · E3/E4

Також: `CONTEXT.md` (проєкт) + `knowledge/pmo-kb/README.md` (індекс методології).

## Rules

1. **QUICK — не більше 5 рядків.** Якщо відповідь займає більше — це вже CR.
2. **CR — завжди мінімум 3 capacity варіанти.** Один варіант — не аналіз.
3. **SP estimate без TL = припущення.** Позначати `[УТОЧНИТИ — pending TL]`, не подавати як факт.
4. **Рекомендація — один варіант.** "Залежить від пріоритетів" — не рекомендація.
5. **Дефолт при мовчанні.** Кожен CR має explicit fallback: "якщо рішення не прийнято до X → за замовчуванням Варіант Y".
6. **Budget impact обов'язковий.** CR без EAC/VAC — неповний документ.
7. **Нові ризики — до risk-register.** Після затвердження CR — оновити `docs/risk-register.md`.
8. **"Дата рішення" ≠ "Дата запиту".** Поле "Дата рішення" заповнюється лише в момент, коли Статус фактично змінюється на ✅ Прийнято / ❌ Відхилено — це дата decision meeting, дата явного підтвердження стейкхолдером, або дата спрацювання дефолту (RULE 5), а не дата створення CR-документа. Якщо на момент запису статус ще 🟡 На розгляді — поле лишається "—".
9. **Джерело рішення обов'язкове.** "Дата рішення" супроводжується тим, хто/що підтвердило рішення (ім'я стейкхолдера, посилання на meeting notes, або "спрацював дефолт RULE 5") — без цього дата непровірювана.
10. **Звірка з Meeting Notes.** Перед тим як проставити "Дата рішення", перевір відповідні `docs/meeting-notes/*/followup.md` — статус рішення там і в CR має збігатись (обидва "відкладено" або обидва "прийнято", і на ту саму дату).

---

## Antipatterns

- ❌ **"Маленька задача" без перевірки** — будь-яка "маленька задача" від клієнта вимагає QUICK-аналізу мінімум
- ❌ **CR без scope definition** — "додати push notifications" не є scope; "campaign API + admin UI + 3 сегменти" — є
- ❌ **Один варіант capacity** — displacement без альтернативи змушує стейкхолдера або погодитись або відхилити; варіанти дають вибір
- ❌ **SP estimate як факт без TL** — PM-оцінка ≠ TL-оцінка; позначати різницю
- ❌ **CR без дедлайну рішення** — без дати рішення decision meeting зависає
- ❌ **Рекомендація "залежить від пріоритетів"** — стейкхолдери платять PM щоб він вже врахував пріоритети і дав відповідь
- ❌ **"Дата рішення" = дата створення CR-документа "для акуратності"** — якщо рішення насправді ще не ухвалено (statusу meeting notes "відкладено"), проставлена дата робить документ недостовірним і розходиться з першоджерелом

---

## Self-check

**QUICK:**
- [ ] SP задачі vs залишок у спринті порівняно?
- [ ] Якщо не поміщається — названо конкретно що прибираємо?
- [ ] Milestone вплив перевірено?
- [ ] Рекомендація одна і конкретна?

**CR:**
- [ ] Scope definition: MVP / Phase 2 / existing — три колонки?
- [ ] SP estimate: мінімум три варіанти (minimal / MVP / full)?
- [ ] Capacity: мінімум 3 варіанти (включно з Phase 2 і відхилити)?
- [ ] Timeline: M6 і M7 по кожному варіанту?
- [ ] Budget: EAC і VAC після CR?
- [ ] Нові ризики перераховані?
- [ ] Рекомендація одна з обґрунтуванням?
- [ ] Decision table: хто, що, до коли?
- [ ] Дефолт при мовчанні вказаний?
- [ ] Файл збережено у `docs/change-requests/`?
- [ ] "Дата рішення" звірена з відповідним `docs/meeting-notes/*/followup.md` — не проставлена наперед?
- [ ] "Дата рішення" супроводжується джерелом (хто підтвердив / яка зустріч / чи спрацював дефолт)?

---

*Devlight PMO · `pmo-analyze-scope-change`*

## Additional resources

- Шаблони репозиторію: `templates/`
- Чеклісти: `checklists/`
- База знань Confluence (локальний експорт): `knowledge/pmo-kb/`
