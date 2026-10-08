# Template — pmo-generate-project-status-dashboard

Шаблон: `templates/tl-project-status-dashboard.html`

**Заміни у шаблоні:**

| Placeholder | Значення |
|---|---|
| `{{REPORT_DATE}}` | DD Mon YYYY |
| `{{SPRINT_CURRENT}}` | Sprint N / M · Month X / Y |
| `{{PROJECT_STATUS_CLASS}}` | `rag-green` / `rag-amber` / `rag-red` |
| `{{PROJECT_STATUS_TEXT}}` | `ON TRACK` / `AT RISK` / `CRITICAL` |
| `{{DATE_START}}` | 02 Jan 2026 |
| `{{DATE_BASELINE_END}}` | 08 Oct 2026 |
| `{{DATE_TODAY}}` | поточна дата |
| `{{DATE_ESTIM_END}}` | DD Mon YYYY |
| `{{SCHEDULE_DELTA_DAYS}}` | +N days / −N days |
| `{{SCHEDULE_DELTA_CLASS}}` | `delta-over` / `delta-ok` |
| `{{COST_BASELINE}}` | $320,000 |
| `{{COST_AC}}` | $XXX,XXX |
| `{{COST_AC_PCT}}` | XX.X% |
| `{{COST_EAC}}` | $XXX,XXX |
| `{{COST_VAC}}` | −$XX,XXX / +$X,XXX |
| `{{VAC_CLASS}}` | `delta-over` / `delta-ok` |
| `{{CPI_VALUE}}` | 0.000 |
| `{{CPI_CLASS}}` | `metric-ok` / `metric-warn` / `metric-bad` |
| `{{SPI_VALUE}}` | 0.000 |
| `{{SPI_CLASS}}` | `metric-ok` / `metric-warn` / `metric-bad` |
| `{{SV_DAYS}}` | Значення **окремого `.perf`-тайла**, що йде одразу після тайла SPI в `.perf-band` (не бейдж і не рядок усередині тайла SPI), напр. `≈ −8` — бізнес-переклад SPI, див. формулу вище |
| `{{SV_DAYS_CLASS}}` | `metric-ok` / `metric-warn` / `metric-bad` — **власний поріг у днях** (див. таблицю порогів вище), **не** копія `{{SPI_CLASS}}` |
| `{{PCT_PROJECT}}` | XX.X% |
| `{{SP_DONE}}` | NNN |
| `{{SP_TOTAL}}` | 920 |
| `{{PCT_BUDGET}}` | XX.X% |
| `{{PCT_BUDGET_BAR_COLOR}}` | `var(--ok)` / `var(--warn)` / `var(--crit)` — з таблиці порогів вище (`PCT_BUDGET − PCT_PROJECT`), **не** хардкодити `var(--warn)` |
| `{{COST_CR_COLOR}}` | `var(--ok)` / `var(--warn)` / `var(--crit)` — CR Cost як % бюджетного резерву (з таблиці порогів вище); `var(--muted)`, якщо CR Cost = "N/A" |
| `{{RISK_CRITICAL_COUNT}}` | N |
| `{{RISK_HIGH_COUNT}}` | N |
| `{{RISK_ROWS}}` | HTML `<li>` рядки ризиків — кожен з описом **і мітігацією** |

**Формат `{{RISK_ROWS}}`** — кожен ризик з трьох рядків: опис + мітігація + contingency:
```html
<li class="risk-item">
  <span class="rtag c">R-01</span>
  <span class="rcat">Scope</span>
  <div>
    <div>Scope creep від PO — нові задачі без CR процесу</div>
    <div class="risk-mit">Мітігація: CR-процес обов'язковий; щотижневий scope review</div>
    <div class="risk-con">Contingency: Заморозити нові запити; ескалація до CEO</div>
  </div>
</li>
```
Клас `rtag`: `c` — critical, `h` — high. Мітігацію брати з колонки "Мітігація" реєстру (~80 символів). Contingency — з секції **Mitigation Plan** реєстру (~80 символів). Категорію брати з колонки "Категорія".
| `{{MILESTONE_ROWS}}` | HTML `<div>` рядки milestones |
| `{{SPRINT_TABLE_ROWS}}` | HTML `<tr>` рядки таблиці (останні 5 спринтів) |
| `{{VELOCITY_SVG_AREA}}` | SVG path d="M..." |
| `{{VELOCITY_SVG_LINE}}` | SVG path d="M..." |
| `{{VELOCITY_DOTS}}` | SVG `<circle>` елементи |
| `{{AVG_VELOCITY}}` | XX.X SP |
| `{{VELOCITY_TARGET}}` | 45 SP |

---
