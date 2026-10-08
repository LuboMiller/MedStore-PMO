---
name: pmo-start-project
description: Orchestrates Devlight project start sequence from pre-sale handoff through initiating artifacts (charter, stakeholders, RACI, glossary, comms, onboarding, kickoff). Use when a new project is handed from Sales or PM asks to bootstrap PMO docs.
---

# Start Project — Orchestrator

## When to use

- Новий проєкт після Sales / A2 handoff
- PM просить «підняти» PMO-пакет з нуля
- Аудит initiating completeness
- **Existing Atlassian project** — спочатку hydrate, потім дозаповнення skills

## Instructions

Виконай **послідовно**, питаючи PM лише коли BLOCKED / не вистачає вхідних даних. Після кожного кроку — короткий статус (DONE / SKIPPED / BLOCKED).

Спочатку (якщо репо свіжий): **`pmo-setup-wizard`** / `make setup` — deps + `.env` + health.

### Path A — greenfield (немає Jira/Confluence проєкту)

### Checklist

```
Start Progress:
- [ ] 1. pmo-presale-handoff → docs/presale-handoff-checklist.md
- [ ] 2. CONTEXT.md заповнений / оновлений з handoff
- [ ] 3. Linked repos EARLY: config/linked-repos.json + repos pull (`pmo-ba-repos` / `pmo-codebase-context`)
       → якщо ba_repos є: FS SoT = knowledge/ba/{id}/ (docs/functional-specs/ ВИМКНЕНО)
       → repos discover --id … → follow BA read_order before stories/FS (BA = maintained dependency)
- [ ] 4. pmo-generate-project-charter → pmo-qg-review-project-charter
- [ ] 5. pmo-manage-stakeholder-register
- [ ] 6. pmo-manage-raci
- [ ] 7. pmo-manage-glossary
- [ ] 8. pmo-manage-communication-plan
- [ ] 9. pmo-manage-escalation-matrix
- [ ] 10. pmo-team-onboarding (якщо команда вже відома)
- [ ] 11. pmo-generate-kickoff-deck
- [ ] 12. (Planning next) pmo-generate-pmp як хаб для baseline
- [ ] 13. (Optional) jira/confluence bootstrap + google folder link у CONTEXT
```

### Path B — existing systems (Jira/Confluence уже є)

```
Catch-up Progress:
- [ ] 1. make integrations-check
- [ ] 2. pmo-hydrate-project (--jira-key + --space) → docs/_hydrate/FROM_SYSTEMS.md
       → Confluence sync-pull: registry JSON + knowledge/confluence-spaces/{SPACE}/ (MD hierarchy)
- [ ] 3. Дозаповнити CONTEXT.md (клієнт, цілі, бюджет) вручну
- [ ] 4. Linked repos EARLY: config/linked-repos.json + repos pull
       → ba_repos non-empty ⇒ FS лише в BA mirror (не docs/functional-specs/)
       → repos discover + BA read_order; maintain via push, not orphan BA workflow
- [ ] 5. Для кожного mapped stub — відповідний skill + QG (не лишати seed)
- [ ] 6. Якщо є Google Drive — pmo-google-ops sync-pull / export потрібних Docs
- [ ] 7. Далі за Path A з кроку, якого ще немає (часто charter QG / RACI / risks)
```

### Правила оркестрації

1. Якщо A2 = **BLOCKED** — зупинись; не генеруй Charter як «офіційний».
2. Charter — **внутрішній** (PM+DM); не пропонуй слати клієнту.
3. Не пропускай QG після charter.
4. Не вигадуй імена стейкхолдерів — бери з CONTEXT / handoff / hydrate map.
5. Hydrate не замінює skills: лише підтягує факти й stubs.
6. **BA-репо, якщо підключене, повністю замінює `docs/functional-specs/`** — не дублюй FS у PMO docs; підтримуй BA як залежність (`pull` → mirror → `push`).
7. В кінці видай таблицю артефактів і наступний рекомендований крок (WBS / risks / roadmap).

## Company methodology

`knowledge/pmo-kb/01-pre-sale/` · `02-initiating/` · `AGENTS.md` skill map
