# Open Questions — MedStore (Dobrobut)

> Skill: `pmo-manage-open-questions`  
> Джерела: Charter QG (2026-10-08), Sales handoff OQ, Kickoff follow-ups

| ID | Питання | Блок / Джерело | Пріоритет | Owner | Статус | Дедлайн | Відповідь |
|---|---|---|---|---|---|---|---|
| OQ-001 | FTE commitment: контракт фіксує ставки, не FTE. Скільки годин/тиждень заплановано на кожну роль? | Charter §6 / Handoff | 🟠 High | PM + DM | Open | Tracking (delivery вже йде) | Не старт-блокер: угода підписана, проєкт активний |
| OQ-002 | Contingency / резерв бюджету не зафіксований. Який % резерву узгоджений з DM? | Charter §6 | 🟠 High | PM + DM | Open | Tracking (delivery вже йде) | Не старт-блокер: угода підписана, проєкт активний |
| OQ-003 | Пороги якості recall@k/precision для golden set — контракт відкладає «на результати Discovery». Потрібні мінімально прийнятні значення для дизайну pipeline. | Charter §3, §9 R-03 / Kickoff follow-up | 🟠 High | PM + BA + клієнт | Open | Тиждень 2 | |
| OQ-004 | Decision-maker map для CR/scope changes: Дмитро Харєбов / Олександр / Сергій Орел — хто підписує зміни під час Discovery? | Charter §10 / Kickoff follow-up | 🟠 High | PM | Open | Overdue (з 21.08) | |
| OQ-005 | Роль ІТ-команди клієнта під час і після Discovery: спостерігачі, співвиконавці, чи майбутні власники підтримки? | Charter §7 / Kickoff follow-up / Handoff GAP-QA-02 | 🟡 Medium | PM → Олександр | Open | Overdue (з 21.08) | |
| OQ-006 | Overview: start date вже 01.08.2026, але Estim. completion 09.10.2028 і SPI=16% / schedule deviation 671 дн. — ще підозрілі. Підтвердити формули дат і rebaseline BAC/валюту ($ vs €). | Charter §6 / Client status sheet Overview 2026-10-20 | 🟠 High | PM | Open | Overdue (з 24.10) | 2026-10-20: start date виправлено; Estim./SPI/валюта — відкриті · 2026-11-02: Estim. вже 06.02.2029, SPI 14%, deviation 791; completion 10% не рухається — перевірити, чи оновлюється Epic % · 2026-11-03: причина — Epic % не оновлювався; PM оновив → completion 56%, SPI 78%, Estim. 12.01.2027. Залишок (baseline vs SoW) → OQ-013 |
| OQ-007 | VPN/whitelisting для інженерів та готовність VM під NER-модель — не підтверджені. | Charter §7 / Kickoff follow-up | 🟠 High | Dmytro Yefimenko → Дмитро Харєбов | Open | Overdue (з 21.08) | |
| OQ-008 | NDA — не згаданий явно в handoff. Чи покриває Framework Agreement №150626? | Handoff §1 | 🟡 Medium | PM → DM | Open | — | |
| OQ-009 | Хто формально приймає щомісячні акти приймання-передачі з боку клієнта? | Kickoff follow-up Q6 | 🟡 Medium | PM → Олександр | Open | — | |
| OQ-010 | Скільки лікарів/аналітиків на старті пілота? | Kickoff follow-up Q7 | 🟡 Low | PM → клієнт | Open | — | |
| OQ-011 | Чи існує окремий документ з переліком кейсів (Cases v2026-05-18, ref у RFP Q&A)? | Handoff GAP-QA-03 | 🟡 Low | PM → Олександр | Open | — | |
| OQ-012 | Чи отримано аванс від Dobrobut? (Контрактно блокував старт) | Handoff OQ-01 | — | PM | Closed | 2026-10-08 | PM: угода давно підписана, проєкт рухається → старт-блокер знято |
| OQ-013 | Прогноз Discovery 480-512 год (60-64 л/д): у годинах у межах WBS Pes (540 год), але в грошах $38,4-41K проти Pes $37 440, бо роботу BA/PM (1.1.1, 1.1.7, частина 1.1.9; оцінені по $40) виконує DE по $80. Як і коли комунікувати клієнту; чи переводити частину годин на ставку BA. | Звіт Дмитра 02.11 / коментар CTO 03.11 / WBS ESTIM 03.11 | 🟠 High | PM → CTO + DM | Closed | 2026-11-03 | 2026-11-03: Epic % оновлено (completion 56%, CPI 84%, EAC $39 743). Baseline = PERT $33 520 (WBS ESTIM), клієнт знає Pes $37 440. `docs/status-reports/2026-11-02/sow-readiness-yefimenko-2026-11-02.md` §3 · 2026-11-03 PM: клієнту про гроші не говоримо; виставляємо не більше Pes WBS ($37 440), надлишок понад Pes іде за рахунок Devlight. Лист: `docs/client-comms/2026-11-03/email-discovery-forecast-shemet.md` |

## Статуси

- **Open** — потребує відповіді
- **In Progress** — обговорюється
- **Closed** — відповідь отримана (записати тут)
- **Deferred** — відкладено з причиною

## QG Charter Summary (2026-10-08)

### Знахідки Quality Gate

1. **Математична перевірка бюджет × FTE:** Estim. cost €99K значно перевищує baseline €70,6K (+40%). При T&M це не автоматичний overrun, але потребує пояснення PM — чи це scope expansion, чи перевитрата? CPI=71% підтверджує.
2. **SPI=21% — аномально низький:** Overview start date 01.12.2025 нетиповий для проєкту з kickoff 08.2026. Ймовірно шаблонний артефакт → OQ-006.
3. **FTE не commitment, а ставки:** Без зафіксованого FTE budget burn може бути непрогнозований → OQ-001.
4. **Contingency відсутній:** Для Discovery-проєкту з великою невизначеністю (DLL декодер, якість NER) — ризиковано → OQ-002.
5. **Acceptance criteria для golden set розмиті:** «На результати Discovery» не дає baseline для pipeline design → OQ-003.
6. **6 з 8 follow-up items з kickoff 21.08 — overdue (7+ тижнів):** Жоден не позначений DONE у Confluence → PM верифікувати.

### Verdict: ⚠️ CONDITIONAL PASS

Charter достатній для внутрішнього підпису PM+DM за умови закриття OQ-001, OQ-002 (FTE + contingency) протягом тижня. Решта OQ — tracking items.
