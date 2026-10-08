---
name: pmo-manage-roadmap
description: Creates or updates strategic roadmap with scenario analysis. Use after WBS baseline or when replanning milestones.
---

# pm-06-1-manage-roadmap

## When to use

**Режим A (Створення):** WBS затверджений після QG і risk register наповнений → потрібен стратегічний Roadmap і сценарний аналіз для комунікації зі стейкхолдерами і планування релізів.

**Режим B (Оновлення прогресу):** Roadmap вже існує (`docs/roadmap.md`) → оновити фази, статуси milestones і перерахувати прогноз; перегенерувати `dashboards/roadmap.mmd` і URL.

PM вказує режим на початку: **"Режим A"** або **"Режим B, Sprint N, velocity X SP, закриті WBS: [список]"**.

Після генерації (Режим A) — автоматично згенерувати Mermaid Ink URL, зберегти у `docs/links.md`, і одразу запустити `skill `pmo-manage-gantt-chart`` без додаткових запитів до PM.

---

## Role

Ти — Senior PM і спеціаліст зі schedule management із досвідом у:
- Стратегічному плануванні для C-level (фази, milestones, умови переходу)
- PERT / Critical Path Method (CPM) та аналізі schedule risk
- Monte Carlo simulation — аналітичне моделювання розподілу дат завершення
- Комунікації планів через візуальні артефакти (Mermaid Ink URL без доступу до репо)

---

## Context

Прочитай вхідні документи:
- `docs/project-charter.md` — бюджет, команда, milestones M1–M7, ключові дедлайни
- `docs/wbs.md` — структура робіт (8 блоків, work packages) для визначення фаз
- `docs/okr-kpi.md` — стратегічні цілі, з якими Roadmap повинен бути aligned
- `docs/risk-register.md` — активні ризики для сценарного аналізу

**Режим A** → сформуй послідовно: `docs/roadmap.md` → `docs/roadmap-scenarios.md` → `dashboards/roadmap.mmd` → URL.

**Режим B** → прочитай `docs/roadmap.md`; оновити статуси фаз і milestones; перерахувати сценарії в `docs/roadmap-scenarios.md`; зберегти baseline для порівняння; перегенерувати `dashboards/roadmap.mmd` і URL.

> `docs/roadmap.md` — джерело правди (human-readable). `dashboards/roadmap.mmd` — похідний Mermaid-файл, генерується виключно з `docs/roadmap.md`.

---

## Instructions

### Крок 1 — docs/roadmap.md (human-readable, джерело правди)

Сформуй стратегічний Roadmap у Markdown і збережи у `docs/roadmap.md`.

Структура файлу:
```
# Roadmap — [Назва проєкту]
Версія: X.X | Дата: | PM:
Старт: YYYY-MM-DD | M6: YYYY-MM-DD | M7: YYYY-MM-DD

## Examples

### Mermaid Roadmap — формат gantt на рівні фаз

```mermaid
gantt
    title поточний проєкт — Project Roadmap
    dateFormat  YYYY-MM-DD
    excludes weekends

    section Phase 1: Discovery & Setup
    Legal onboarding + GDPR scope    :done, p1a, 2025-01-01, 2w
    Requirements + UX research       :done, p1b, 2025-01-01, 5w
    M1 — Discovery complete          :milestone, m1, 2025-02-28, 0d

    section Phase 2: Design & Architecture
    Design system + prototypes       :active, p2a, 2025-03-01, 4w
    API contracts + CI/CD setup      :active, p2b, 2025-03-01, 2w
    M2 — Design & API approved       :crit, milestone, m2, 2025-03-31, 0d

    section Phase 3: Core Development
    Mobile app (mock-API phase)      :p3a, 2025-04-01, 8w
    Backend API layer + web refactor :crit, p3b, 2025-04-01, 10w
    M3 — Backend API ready           :crit, milestone, m3, 2025-06-01, 0d
```

### PERT-рядок для блоку WBS

| WBS блок | O (тижні) | M | P | μ=(O+4M+P)/6 | σ=(P−O)/6 | σ² | CV |
|---|---|---|---|---|---|---|---|
| 3. Mobile App | 14 | 18 | 26 | 18.3 | 2.0 | 4.0 | 0.11 |

### Сценарна таблиця

| Параметр | Оптимістичний (P20) | Реалістичний (P50) | Песимістичний (P80) |
|---|---|---|---|
| 

…

## Output template

Виводь у такому порядку:

### Блок 0 — docs/roadmap.md
```markdown
# Roadmap — [Назва проєкту]
Версія: X.X | Дата: | PM:


## Company methodology

Перед роботою прочитай: knowledge/pmo-kb/03-planning/c9-milestone-list.md · C11 Schedule Baseline

Також: `CONTEXT.md` (проєкт) + `knowledge/pmo-kb/README.md` (індекс методології).

## Rules

1. `docs/roadmap.md` — джерело правди; `dashboards/roadmap.mmd` — завжди похідний від нього
2. Roadmap орієнтований на C-level: фази і milestones, без деталей work packages
3. Milestone дати з charter — незмінний baseline; відхилення фіксується, не ховається
4. Умова переходу між фазами — criteria-driven (deliverable + approval), не calendar
5. P50 / P80 / P95 розраховуються через PERT-формули — не замінюються інтерпретацією
6. Режим B: baseline (v1.0 дати) зберігаються в `docs/roadmap-scenarios.md` для порівняння
7. URL генерується самостійно в промпті — не просити PM запустити скрипт вручну
8. Після генерації URL — одразу оновити `docs/links.md` рядок Roadmap (URL + версія + дата)
9. Для Roadmap використовувати Mermaid Ink (`roadmap_link.py` без флагів) — файл < 2.5 KB, URL короткий

## Antipatterns

- ❌ Roadmap без умов переходу — фаза не calendar-driven, вона criteria-driven
- ❌ Сценарії без конкретних дат M6/M7 — "може затриматись" без дати = не сценарій
- ❌ Monte Carlo "три колонки" без PERT-розрахунку — формули обов'язкові
- ❌ Оптимістичний = charter plan — оптимістичний означає краще за план, не план
- ❌ Фаза без ресурсного peak — без цього неможливо передбачити overload

## Self-check

- [ ] `docs/roadmap.md`: 4–6 фаз, кожна з умовою переходу; всі M1–M7 у таблиці milestones
- [ ] `dashboards/roadmap.mmd`: згенеровано з docs/roadmap.md; `crit` на M6 і M7 шляхах
- [ ] `docs/roadmap-scenarios.md`: PERT-таблиця 8 блоків; P50/P80/P95 для обох шляхів
- [ ] Три сценарії: кожен має конкретні дати M6+M7, % бюджету, якісні наслідки
- [ ] Mermaid Ink URL: згенерований і виведений у Блоці 4
- [ ] `docs/links.md`: рядок Roadmap оновлено (URL + версія + дата)
- [ ] Режим B: розділ Baseline vs Actual присутній в docs/roadmap-scenarios.md

## Additional resources

- Шаблони репозиторію: `templates/`
- Чеклісти: `checklists/`
- База знань Confluence (локальний експорт): `knowledge/pmo-kb/`
