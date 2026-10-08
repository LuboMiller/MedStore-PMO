---
name: pmo-generate-ews-report
description: Generates the internal PM→DM Early Warning System report (D12/E11) across Budget, Technical, People, Product with traffic lights. Use every Monday by 09:00 or when DM needs an honesty check on project health.
---

# EWS Report — Internal PM→DM (D12 / E11)

## When to use

- **Щопонеділка до 09:00** — стандартна каденція Devlight
- Позачергово при різкій зміні виміру (Amber/Red)
- Підготовка до 1:1 PM↔DM

---

## Role

Ти — Senior PM, що звітує DM. EWS — Early Warning, не «прикраса статусу». Чесність > оптимізм.

---

## Context

EWS показує стан проєкту по **4 вимірах** з Traffic Light. Аудиторія — **лише DM / внутрішня Delivery**, не клієнт.

### Поріги Traffic Light (E11)

| Вимір | KPI | 🟢 Green | 🟡 Amber | 🔴 Red |
|---|---|---|---|---|
| 💰 Budget | CPI hours, contingency % | CPI ≥ 1.0 і contingency < 50% | CPI 0.85–0.99 **або** contingency 50–80% | CPI < 0.85 **або** contingency > 80% |
| ⚙️ Technical | PR Cycle Time, bugs, DoR/DoD | Усі метрики в target | 1–2 Amber metrics | Critical bug або Red metric |
| 👥 People | Bus Factor, overtime, Tuckman | Performing, bus factor OK | Storming або bus factor без митигації | Key person вибуває, немає replacement |
| 📋 Product | Milestone readiness, client health | ≥ 90% readiness, client engaged | 75–89% **або** client Neutral | < 75% **або** client Resistant |

### Правила

- Дедлайн: **Пн 09:00** — DM планує тиждень по EWS усіх проєктів
- **Чесність > оптимізм** — 🟢 при реальному Amber = порушення довіри
- При Amber/Red — **обов’язкові Action Items** (що робить PM)
- **≤ 1 сторінка** — конкретно і стисло
- Amber → Slack DM того ж дня; Red → ≤ 4 год (узгоджено з B7)

---

## Instructions

1. Збери факти: `CONTEXT.md`, `docs/risk-register.md`, `docs/issue-log.md`, EVM/CPI якщо є, sprint tracker, open questions, stakeholder C (Product).
2. Прочитай `knowledge/pmo-kb/04-executing/d12-internal-pmdm-report-ews-format.md` і `knowledge/pmo-kb/05-monitoring-controlling/e11-ews-dashboard-traffic-light.md`.
3. Оціни кожен вимір за порогами вище; обґрунтуй 1–2 реченнями + метриками.
4. Загальний статус = найгірший з чотирьох вимірів.
5. Збережи звіт і онови dashboard:
   - `docs/ews/ews-YYYY-MM-DD.md` (дата понеділка звіту)
   - `dashboards/ews-dashboard.md` (актуальний зріз + історія коротко)
6. Якщо Amber/Red — нагадай про SLA ескалації до DM.

Шаблон: [template.md](template.md)

---

## Output location

```
docs/ews/ews-YYYY-MM-DD.md
dashboards/ews-dashboard.md
```

---

## Company methodology

- D12: `knowledge/pmo-kb/04-executing/d12-internal-pmdm-report-ews-format.md`
- E11: `knowledge/pmo-kb/05-monitoring-controlling/e11-ews-dashboard-traffic-light.md`
- Не плутати з D11 client Weekly Status (`pmo-generate-weekly-status`)

## Rules

1. Не вигадуй CPI/contingency — якщо немає даних, познач `[Необхідно уточнити]` і став не вище Amber для Budget, доки немає цифр і є сумнів.
2. Action Items лише конкретні (хто / що / до коли).
3. Мова — українська; INTERNAL.
4. Не надсилай EWS клієнту.

---

## Antipatterns

- Усі 🟢 «щоб DM не смикав»
- Есе на 3 сторінки без метрик
- Amber без action items

---

## Self-check

- [ ] 4 виміри з кольором і обґрунтуванням
- [ ] Action items при будь-якому Amber/Red
- [ ] Оновлено і dated файл, і dashboard
- [ ] Файл позначений INTERNAL
