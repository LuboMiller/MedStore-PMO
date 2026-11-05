# CONTEXT.md — контекст проєкту MedStore

> Єдине джерело правди про поточний проєкт для AI-асистента PMO.
> Не дублюй сюди корпоративну методологію — вона в `knowledge/pmo-kb/`.

---

## 0. Ідентифікація

| Параметр | Значення |
|---|---|
| **Назва проєкту** | MedStore (Dobrobut MedStore) |
| **Клієнт** | Добробут (Dobrobut) — найбільша мережа приватних медичних центрів України |
| **Домен** | E-Health |
| **Тип контракту** | T&M (Додаток №3 до Framework Agreement №150626) |
| **PM** | Volodymyr Mishchenko |
| **DM (Delivery Director)** | Viktoriia Sukharevska |
| **BA** | Kateryna Kovshar |
| **Data/AI Engineer** | Dmytro Yefimenko (об'єднана роль SA+DE+AIE) |
| **Sales Manager** | Viktoriia Prysyazhna |
| **CTO (internal stakeholder)** | Oleksandr Seredenko |
| **Дата internal kick-off** | 2026-08-20 |
| **Дата client kick-off** | 2026-08-21 |
| **Планова тривалість** | ~13 тижнів (оптимістичний сценарій); таргет — презентабельний Pilot до кінця листопада 2026 |
| **Поточна фаза** | Discovery / Pilot v1 |
| **Методологія** | Kanban |
| **Decision Maker (клієнт, tech sign-off)** | Дмитро Харєбов — IT Director (Dobrobut) |
| **SPOC (клієнт, org/project)** | Олександр — Project Manager (Dobrobut) |
| **Контракт підписано** | 2026-07-28 (Devlight: Ігор Поліч; Dobrobut: Сергій Орел) |

---

## 1. Business case (коротко)

Побудувати незалежне від МІС «Доктор Елекс» деперсоналізоване сховище медичних даних (MedStore) та рівень доступу (Query Interface) з когортним, по-пацієнтним і семантичним пошуком. Поточний етап — Discovery/Pilot v1 на реальних деперсоналізованих даних (~половина цільової функціональності) + data-driven оцінка бюджету й календаря повномасштабного впровадження. Мета — підтримати внутрішнє бюджетне рішення клієнта в грудні 2026.

---

## 2. Цілі / успіх (SMART)

| # | Ціль | Метрика | Дедлайн |
|---|---|---|---|
| 1 | Здати працездатний Pilot v1, протестований клієнтом за сценарним чек-листом | Бінарний pass/fail за узгодженими сценаріями | кінець листопада 2026 |
| 2 | Де-ідентифікація ПІБ на holdout-наборі | recall ≥ 99% (контрактний acceptance gate) | кінець Discovery |
| 3 | Data-driven оцінка бюджету й календаря full-scale | Звіт з виміряними recall@k/precision | кінець Discovery |

---

## 3. Scope (high-level)

| IN scope | OUT of scope |
|---|---|
| Week-0 precondition: sandbox/реальний export | Повномасштабне впровадження (~30М документів) |
| DLL export & ingest: обхід типів/версій, ETL, де-ідентифікація | Немедичні файли (Тип 3) — знижений пріоритет, фаза 2/3 |
| Pipeline: chunking/reranking/NER + recall/precision | SaaS/multi-client доступ |
| Бенчмарк моделей (embedder, реренкер, NER, local/cloud) | Live-інтеграція з МІС (лише нічна репліка) |
| Golden set + каталог сценаріїв + критерії приймання | Синоніми/діалогові сценарії (V1) |
| Де-ідентифікація: NER імен, holdout, fail-closed | Юридична обробка за Законом про ПД |
| Pilot v1 deployment у пісочниці клієнта | Power BI дашборди (внутрішня справа клієнта) |
| Архітектура пілота, канонічна модель даних, скоуп full-scale | |
| Беклог V1, цілі V1, зв'язки з іншими системами | |

---

## 4. Команда і FTE

| Роль | Ім'я | FTE | Нотатки |
|---|---|---|---|
| PM | Volodymyr Mishchenko | <!-- PM: уточнити --> | головний контакт, звітність |
| DM / Delivery Director | Viktoriia Sukharevska | — | гарантує результат, ескалація |
| Data/AI Engineer (SA+DE+AIE) | Dmytro Yefimenko | <!-- PM: уточнити --> | об'єднана роль; пайплайн, архітектура, бенчмарк |
| BA | Kateryna Kovshar | <!-- PM: уточнити --> | golden set, сценарії, критерії приймання |
| Front-end Engineer | TBD (опційно) | 0 | бонусна історія; UI поверх Query Interface |

---

## 5. Стейкхолдери клієнта

| Ім'я | Роль | Power / Interest | Нотатки |
|---|---|---|---|
| Дмитро Харєбов | IT Director (Dobrobut) | High / High | tech sign-off, архітектура, інтеграції |
| Олександр | PM (Dobrobut), SPOC | High / High | загальні org/project, координація ескалацій |
| Анна Пивовар | Head of Project Office (PMO) | Medium / Medium | |
| Владислав | Експерт МІС «Доктор Елекс» | Medium / High | стандартизація шаблонів/полів |
| Зоя | Технічний спеціаліст ДЕ | Low / High | схема ДЕ, Discovery sessions |
| Сергій Орел | Contract signatory (Dobrobut) | High / Low | підписує договір |

Конфіденційний детальний реєстр — `docs/stakeholder-register.md`.

---

## 6. Бюджет / margin (внутрішнє)

| Параметр | Значення | Джерело |
|---|---|---|
| Baseline cost | $33 520 | Client status sheet Overview 2026-11-05 |
| Current cost (fact) | $22 440 | Client status sheet Overview 2026-11-05 |
| Estim. cost | $39 743 | Client status sheet Overview 2026-11-05 |
| WBS ESTIM Opt / ML / Pes / PERT | $24 960 / $31 200 / $37 440 / $33 520 (360 / 450 / 540 / 484 год) | WBS ESTIM 2026-11-03; Baseline = PERT; Pes клієнт знає |
| Presale cost (Scope Dashboard) | $34 260 | Scope Dashboard 2026-11-05 |
| Cost variance | −$3 513 | Overview 2026-11-05 |
| Contract value | <!-- PM: уточнити --> | |
| Margin target | <!-- PM: уточнити --> | |
| Contingency | <!-- PM: уточнити --> | |
| CPI | 84% | Client status sheet Overview 2026-11-05 |
| SPI | 76% | Client status sheet Overview 2026-11-05 (було 78% на 03.11) |
| Project completion % | 56% | Client status sheet Overview 2026-11-05 |
| Budget completion % | 67% | Client status sheet Overview 2026-11-05 |
| Start date | 01.08.2026 | Overview |
| Baseline end | 08.12.2026 | Overview |
| Estim. completion | 18.01.2027 | Overview 2026-11-05 (було 12.01.2027 на 03.11; SV зріс 36→41 дн.) |

> ⚠️ SPI 76% / SV 41 дн. / Estim. completion 18.01.2027 — відставання від baseline зростає (+5 дн. SV vs 03.11). Контрактний етап STG-01 закінчується 30.11.2026 (Estim. completion +49 дн. після end). AC/EAC з 03.11 без змін — Tempo за 04–05.11 ще може не відбитись у sheet. Drive label «Updated 05-10-26» не збігається з Overview Current date 05.11.2026 — PM верифікувати modifiedTime.

---

## 7. Топ-ризики

| # | Ризик | Ймовірність | Вплив | Рівень | Мітігація |
|---|---|---|---|---|---|
| R-01 | Затримка sandbox/реального export'у від клієнта (week-0 precondition) — критичний шлях | 🟠 | 🔴 | 🔴 | Чіткий SLA на week-0, ескалація через IT Director |
| R-02 | Розбіжність у кількості шаблонів (493/~2000 vs 2685) — впливає на нормалізацію | 🟡 | 🟡 | 🟠 | Уточнити з Зоєю/Владиславом |
| R-03 | Пороги якості recall@k/precision не узгоджені | 🟡 | 🟡 | 🟠 | Узгодити на kickoff |
| R-04 | Обмежені ресурси клієнта для верифікації AI-виводу (~100 docs spot-check) | 🟡 | 🟡 | 🟡 | Планувати golden set під обмеження |
| R-05 | Чанкінг/реренкінг дають хибну видачу | — | High | High | Гібрид FTS+вектор RRF; крос-енкодер; вимір на препілоті |
| R-06 | Знеособлення на відмінюваних іменах — витік ПІБ | — | High | High | Відмінково-свідомий NER; fail-closed; вимірюваний цільовий рівень |

Повний реєстр — `docs/risk-register.md`.

---

## 8. Канонічні посилання проєкту

| Тема | Шлях |
|---|---|
| Charter | `docs/project-charter.md` |
| WBS | `docs/wbs.md` |
| Glossary | `docs/glossary.md` |
| Risk register | `docs/risk-register.md` |
| Open questions | `docs/open-questions.md` |
| Sprint tracker | `dashboards/sprint-tracker.md` |
| EVM log | `docs/evm-log.md` |
| Jira project | `DOBDWH` (Kanban board, ~30 issues) |
| Confluence space | `DD1` · MD mirror: `knowledge/confluence-spaces/DD1/` |
| Google Drive folders | `config/google-directories.json` · registry: `registry/google/` |
| Client contracts / SOW | `config/contracts.json` · `docs/contracts/` · `google contracts-status --write` |
| Time Report (monthly act) | `config/time-report.json` · `docs/acts/` · skill `pmo-prepare-monthly-act` |
| Client Project status sheet | `config/client-status-sheet.json` (ID: `1dtRGvD-5IeuXvzN9JGuv-OpO2H4JRsdeyBkWSTmcTuo`) · playbook `docs/client-status-sheet/operating-playbook.md` |
| Client calendar plan | Google Sheets `100F5PIfBaTrr1u_hji9-witEhKkIBIWXFAy5uoxcizQ` |
| CHANGE REQUESTS (D4) | `docs/change-requests/README.md` |
| Fireflies | `FIREFLIES_API_KEY` → `docs/meeting-notes/` (0 transcripts знайдено) |
| BA linked repos | `config/linked-repos.json` → порожні |
| Codebase linked repos | `config/linked-repos.json` → порожні |

---

<!-- hydrate:atlassian -->
- Jira: `DOBDWH`
- Confluence space: `DD1`
- Lead (Jira): Viktoriia Sukharevska
- Hydrated: 2026-11-02 (jira/confluence sync-pull)

<!-- hydrate:google -->
- Client status sheet: `1dtRGvD-5IeuXvzN9JGuv-OpO2H4JRsdeyBkWSTmcTuo`
- Drive title: `MedStore | Client Project status report | Updated 05-10-26` — Overview «Current date» 05.11.2026 (export 2026-11-05T10:18:11Z)
- Calendar plan: `100F5PIfBaTrr1u_hji9-witEhKkIBIWXFAy5uoxcizQ`
- Sheets hydrate: `docs/_hydrate/google/sheets/client-status-live-2026-11-05/`
- Drive folders: `main` + `contracts` OK; `commercial` / `finance` / `client-share` — folder_id not set
- ⚠️ Drive label stamp «05-10-26» — ймовірно дата останнього редагування шаблону (05 жовт.), не дата звіту. PM верифікувати.

## 9. Нотатки сесії

- 2026-11-05: **DEC-002** — внутрішньо: оптимізувати ETC до **130–160 год** під hard cap $37k (DEC-001); прогноз Дмитра 02.11 (177–209) більше не план А. Цільовий bill ~$32,8–35,2k. Briefing оновлено.
- 2026-11-05: Morning sync Phase A+B. Overview: AC $22 440 (без змін), EAC $39 743, CPI 84%, SPI 76% (↓2 пп vs 03.11), SV 41 дн. (↑5 дн.), completion 56%, budget 67%, Estim. completion 18.01.2027 (↑6 дн.). Drive label stamp «05-10-26» — аномалія (ймовірно дата редагування шаблону, не звітна дата). STG-01 end 30.11, 25 дн. до warn-вікна. 1.1.8 (Пілот) змінено з TO DO→IN PROGRESS з Epic % 52%. Контракт пролонгація ще не підтверджена.
- 2026-11-03: PM оновив client status sheet за % Дмитра → completion 56%, budget 67%, CPI 84%, SPI 78%, EAC $39 743, CV −$3 513, Estim. 12.01.2027. Baseline = PERT $33 520; Pes $37 440 (WBS ESTIM, клієнт знає). У годинах прогноз Дмитра (480-512) < Pes 540, у грошах EAC вище Pes: BA/PM-обсяг ($40) робить DE ($80) (OQ-013).
- 2026-11-03: Дмитро (через CTO) — SoW-готовність на 02.11: 303,45 год, прогноз 480-512 год (60-64 л/д) із 448-536 SoW; оптимістична межа недосяжна, запас до песимістичної 24-56 год, драйвер — 1.1.4 + темп клієнта (еталонні відповіді, тестування). CTO: чи комунікувати клієнту завчасно → PM: так, разом із продовженням Додатку №3 (end 30.11) і після вирівнювання sheet (OQ-013). `docs/status-reports/2026-11-02/sow-readiness-yefimenko-2026-11-02.md`
- 2026-11-02: Morning sync Phase A+B. Overview: AC $20 615 (+$3 250 vs 20.10), EAC $206 148, budget burn 62%, project completion 10% (без змін), CPI 16%, SPI 14%, Estim. completion 06.02.2029, schedule deviation 791. Перевитрата vs Refine: 1.1.1 ($1 410 / $860), 1.1.6 ($5 719 / $4 280), 1.1.8 ($2 651 / $2 600 при epic 0% / TO DO).
- Jira DOBDWH 20.10→02.11: статуси без змін; +≈64,5 год логів (DOBDWH-28 +22,2 · DOBDWH-10 +19,1 · DOBDWH-8 +5,7 · DOBDWH-11 +5,4 · DOBDWH-15 +4,8 · DOBDWH-9 +3,7 · інші ≤2). Розбіжність sheet↔Jira: 1.1.8 TO DO vs DOBDWH-10 In Progress; 1.1.7 IN REVIEW vs DOBDWH-9 In Progress.
- Контракт STG-01 end 2026-11-30 — 28 дн. · 🟢 (з ~16.11 стане 🟡). Fireflies 0 hits. Confluence DD1 без змін контенту.
- 2026-10-20: Morning sync Phase A+B. Overview rebaseline vs 08.10: BAC $33 520 (було €70,6K), AC $17 365, EAC $173 652, completion 10% / budget burn 52%, CPI 19%, SPI 16%. Scope: 1.1.1 і 1.1.7 IN REVIEW (~80% epic); 1.1.2 і 1.1.8 TO DO; решта IN PROGRESS.
- Jira DOBDWH (зріз sync): Backlog 11 · In Progress 8 · In Review 2 · To Do 2 · Done 2 · Released 1 · Cancelled 4.
- Estim. completion 09.10.2028 і schedule deviation 671 дн. — далі підозрілі (OQ-006); start date уже 01.08.2026.
- Fireflies: 0 hits за keyword DWH/MedStore/ДВХ (зустрічі ймовірно MS Teams).
- Контракт STG-01 (Додаток №3) active, end 2026-11-30, 41 дн. · 🟢.
- 2026-10-08: Path B catch-up після setup + hydrate. CONTEXT дозаповнено з Confluence + Jira + Overview.
- Контракт: Додаток №3 до Framework Agreement №150626, T&M, підписано 28.07.2026.
