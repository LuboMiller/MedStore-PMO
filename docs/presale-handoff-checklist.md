# Pre-sale Handoff Checklist — MedStore (Dobrobut)

> A2 · Skill: `pmo-presale-handoff`  
> Джерело: Confluence «Dobrobut DWH. Sales handoff document» (id: 5961908226) — Reverse Handoff від 2026-08-03  
> Оцінка: **post-factum** (handoff реконструйований з RFP Q&A + 4 call transcripts; kickoff вже відбувся 20–21.08.2026)

| Параметр | Значення |
|---|---|
| Проєкт | MedStore (Dobrobut MedStore) |
| Клієнт | Добробут |
| Sales | Viktoriia Prysyazhna |
| PM | Volodymyr Mishchenko |
| DM | Viktoriia Sukharevska |
| Дата handoff | ~2026-08-03 (reverse handoff doc) → kickoff 2026-08-20/21 |

---

## Загальний статус: ⚠️ PASSED WITH NOTES

> Handoff реконструйований, kickoff вже відбувся. Нижче — post-factum аудит повноти з Confluence.

---

## Блок 1 — Документи

| # | Пункт | Статус | Коментар |
|---|---|---|---|
| 1.1 | КП / Proposal | ⚠️ NOTES | RFP MedStore v3 згадується, але не вкладений у Confluence |
| 1.2 | SOW / Контракт | ✅ PASSED | Додаток №3 до Framework Agreement №150626, підписано 28.07.2026 (Ігор Поліч / Сергій Орел) |
| 1.3 | NDA | ⚠️ NOTES | Не згаданий явно; Framework Agreement може покривати — PM верифікувати |
| 1.4 | Estimate | ⚠️ NOTES | T&M модель; presale estimate обговорювався (€23K prediscovery, ~€71K total PERT), але окремий документ не зафіксовано |

## Блок 2 — Scope

| # | Пункт | Статус | Коментар |
|---|---|---|---|
| 2.1 | Scope IN визначений | ✅ PASSED | 7 етапів Discovery/Pilot чітко описані (kickoff + SOW) |
| 2.2 | Scope OUT визначений | ✅ PASSED | Явно: full-scale, Тип 3, SaaS, live-інтеграція |
| 2.3 | Acceptance criteria | ⚠️ NOTES | De-id recall ≥ 99% зафіксовано контрактно; recall@k/precision для golden set — «на результати Discovery» (OQ) |

## Блок 3 — Команда

| # | Пункт | Статус | Коментар |
|---|---|---|---|
| 3.1 | Персональний склад підтверджено | ⚠️ NOTES | PM, Data/AI Engineer, BA підтверджені на kickoff 21.08; Front-end TBD/опційно; OQ-02 з handoff: «хто персонально закриває ролі» |
| 3.2 | FTE узгоджено DM | ⚠️ NOTES | Контракт фіксує ставки, не FTE — PM уточнити з DM |

## Блок 4 — Бюджет

| # | Пункт | Статус | Коментар |
|---|---|---|---|
| 4.1 | Payment schedule | ⚠️ NOTES | T&M з авансом (§4.1.1); деталі payment schedule з контракту — PM верифікувати |
| 4.2 | Contract value | ⚠️ NOTES | Baseline €70 633,50 з client status sheet; точна контрактна сума — PM верифікувати |

## Блок 5 — Клієнт

| # | Пункт | Статус | Коментар |
|---|---|---|---|
| 5.1 | Decision maker визначений | ⚠️ NOTES | Дмитро Харєбов (tech sign-off) + Олександр (org SPOC) з comms plan; формальний DM map для CR — OQ з kickoff |
| 5.2 | Стейкхолдери ідентифіковані | ✅ PASSED | 6 стейкхолдерів з kickoff |
| 5.3 | Контакт для PM | ✅ PASSED | Олександр — SPOC |

## Блок 6 — Ризики

| # | Пункт | Статус | Коментар |
|---|---|---|---|
| 6.1 | Ризики presale ідентифіковані | ✅ PASSED | 6 ризиків у internal kickoff + 11 технічних у client kickoff |
| 6.2 | Gaps зафіксовані | ⚠️ NOTES | GAP-QA-01 (немає email/HubSpot), GAP-QA-02 (обірвана відповідь 8.7), GAP-QA-03 (Cases doc) |

---

## Open Questions з handoff (Sales → PM)

| # | Питання | Статус | Owner |
|---|---|---|---|
| OQ-01 | Чи отримано аванс від Dobrobut? | Closed 2026-10-08 — угода підписана, проєкт рухається (див. OQ-012) | PM |
| OQ-02 | Хто персонально закриває ролі DE/AIE/BA? | CLOSED (kickoff 21.08: Dmytro Yefimenko, Kateryna Kovshar) | PM |

---

## Висновок

Handoff post-factum: **⚠️ PASSED WITH NOTES**. Kickoff вже відбувся, проєкт активний (~7 тижнів). Основні нюанси:
- NDA та RFP не вкладені в Confluence → PM верифікувати наявність
- FTE не зафіксовані формально (T&M ставки ≠ FTE commitment)
- Decision-maker map для CR/scope changes — open question з kickoff
- Acceptance criteria для golden set recall/precision — ще не узгоджені
