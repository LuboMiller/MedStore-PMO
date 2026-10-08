<!--
  tl-deck-status-presentation.md — DECK Status Presentation Template (Marp)
  Usage: skill pmo-generate-project-status-report (DECK mode)
  KB: D11 / status reporting · не підміняє EWS (D12/E11)
  Populated file: docs/status-reports/{YYYY-MM-DD}/deck-{YYYY-MM-DD}.md
  ─────────────────────────────────────────────────────────────────────
  Render options:
    VS Code:  "Marp for VS Code" extension → Ctrl+Shift+P → "Marp: Export Slide Deck"
    CLI:      marp deck.md               → deck.html
              marp deck.md --pdf         → deck.pdf
              marp deck.md --pptx        → deck.pptx
  ─────────────────────────────────────────────────────────────────────
  PLACEHOLDER REFERENCE
  ─────────────────────────────────────────────────────────────────────
  {{DECK_DATE}}            e.g. "08 Jul 2026"
  {{DECK_SUBTITLE}}        e.g. "Sprint 15 Review" | "Weekly Status"
  {{RAG_LABEL}}            "🟢 ON TRACK" | "🟡 AT RISK" | "🔴 CRITICAL"
  {{PCT_COMPLETE}}         integer 0–100, e.g. 62
  {{SPRINT_CURRENT}}       e.g. 15
  {{SPRINT_TOTAL}}         e.g. 20
  {{MONTH_CURRENT}}        e.g. 7
  {{MONTH_TOTAL}}          e.g. 10
  {{VELOCITY_FACT}}        e.g. 38
  {{VELOCITY_TARGET}}      e.g. 45
  {{VELOCITY_NOTE}}        e.g. "⚠️ below target" | "✓ on target"
  {{CURRENT_PHASE}}        e.g. "EU Localization — Польща"
  {{NEXT_MILESTONE}}       e.g. "M7 EU Launch · ⚠️ at risk (+2 weeks) · Oct 2026"
  {{RISK_CRITICAL_COUNT}}  e.g. 5
  {{RISK_HIGH_COUNT}}      e.g. 7
  {{RISK_ROWS}}            Markdown table rows — see RISK_ROWS FORMAT below
  {{MILESTONE_ROWS}}       Markdown table rows — see MILESTONE_ROWS FORMAT below
  {{DECISION_SUMMARY}}     e.g. "2 decisions needed" | "No action needed from stakeholders"
  {{DECISION_ROWS}}        Markdown table rows — see DECISION_ROWS FORMAT below

  ─── RISK_ROWS FORMAT ───────────────────────────────────────────────
  One markdown table row per risk. Keep Mitigation ≤ 60 chars (one line on slide).
  Max 6 rows. Priority: Critical first, then High.

  | R-09 | Blik/P24 sandbox >3 тижнів — блокує EU Fast-track | Critical | Подали 2026-07-08; daily tracking; backup агрегатор |
  | R-06 | GDPR compliance затримується — EU launch під загрозою | Critical | Юрист залучений; gap-аналіз завершено |

  Level values: Critical | High | Medium

  ─── MILESTONE_ROWS FORMAT ──────────────────────────────────────────
  One row per milestone. Icon column: ✓ (done) · → (in progress) · · (planned) · ! (at risk)

  | ✓ | M4 — Seller Dashboard Launch | 14 May 2026 | Done |
  | → | M6 — EU Feature Freeze (PL) | 14 Aug 2026 | In Progress |
  | ! | M7 — EU Launch (Poland) | 08 Oct 2026 | At Risk +2w |
  | · | M8 — Black Friday Readiness | 06 Nov 2026 | Planned |

  ─── DECISION_ROWS FORMAT ───────────────────────────────────────────
  One row per decision needed from a stakeholder. If none:
  | — | No action needed from stakeholders this week. | | |

  Otherwise:
  | 1 | Підтвердити EU Fast-track vs Standard scope для M7 | Michał (PO) | 2026-07-14 |
  | 2 | Availability юриста для EU intermediate legal review | PM + юрист | 2026-07-10 |
-->
---
marp: true
theme: default
paginate: true
footer: "{{PROJECT_NAME}} · {{DECK_DATE}} · {{DECK_SUBTITLE}}"
style: |
  section {
    font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
    font-size: 16px;
    padding: 48px 56px;
    color: #1a1f2e;
    background: #ffffff;
  }
  h1 {
    font-size: 21px;
    font-weight: 700;
    color: #1e3a5f;
    border-bottom: 2px solid #1e3a5f;
    padding-bottom: 8px;
    margin-bottom: 16px;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13.5px;
    margin-top: 6px;
  }
  th {
    background: #f0f2f7;
    color: #6b7a99;
    font-size: 10.5px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .05em;
    padding: 6px 10px;
    text-align: left;
    border-bottom: 1px solid #e2e5ec;
  }
  td {
    padding: 7px 10px;
    border-bottom: 1px solid #eaecf2;
    vertical-align: top;
    line-height: 1.45;
  }
  tr:last-child td { border-bottom: none; }
  strong { color: #1e3a5f; }
  p { margin-bottom: 10px; }
  section::after { font-size: 11px; color: #a0aabb; }
  footer { font-size: 11px; color: #a0aabb; }
---

# 01 — Progress

**{{PROJECT_NAME}} · {{DECK_SUBTITLE}} · {{DECK_DATE}}** · {{RAG_LABEL}}

| Metric | Value |
|---|---|
| Complete | **{{PCT_COMPLETE}}%** |
| Sprint | {{SPRINT_CURRENT}} / {{SPRINT_TOTAL}} |
| Month | {{MONTH_CURRENT}} / {{MONTH_TOTAL}} |
| Velocity | {{VELOCITY_FACT}} SP (target: {{VELOCITY_TARGET}} SP) — {{VELOCITY_NOTE}} |
| Phase | {{CURRENT_PHASE}} |

**Next milestone:** {{NEXT_MILESTONE}}

---

# 02 — Risks & Mitigations

Critical: **{{RISK_CRITICAL_COUNT}}** · High: **{{RISK_HIGH_COUNT}}**

| ID | Risk | Level | Mitigation |
|---|---|---|---|
{{RISK_ROWS}}

---

# 03 — Timeline

| | Milestone | Date | Status |
|:---:|---|---|---|
{{MILESTONE_ROWS}}

---

# 04 — Decisions & Support Needed

{{DECISION_SUMMARY}}

| # | Decision / Question | From | By |
|---|---|---|---|
{{DECISION_ROWS}}
