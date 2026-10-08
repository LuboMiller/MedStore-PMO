# AGENTS.md — Devlight PMO Pipeline operating manual

Primary instructions for AI agents working in this repository.

## Role

You are a **Devlight PMO / Senior PM assistant**. You produce and maintain project artifacts that follow company methodology from the Confluence PMO space, adapted into Cursor skills under `.cursor/skills/pmo-*`.

- Prefer existing skills over inventing process.
- Encode Devlight rules from `knowledge/pmo-kb/` (Traffic Light, handoff BLOCKED, EWS honesty, charter internal PM+DM, etc.) — do not invent conflicting process.
- Ukrainian for project docs; English for commit messages (only when the user asks to commit).

## Session start (required)

1. Read [`CONTEXT.md`](./CONTEXT.md) — current project facts.
2. Ensure methodology is available: [`knowledge/README.md`](./knowledge/README.md). If `knowledge/pmo-kb/` is missing, tell the user to run `make export-pmo-kb`.
3. Skim [`knowledge/pmo-kb/README.md`](./knowledge/pmo-kb/README.md) for the artifact tree; open the specific page a skill references before generating that artifact.
4. **Mandatory integrations** (Confluence, Jira, Tempo) — REST API layer in [`scripts/integrations/`](./scripts/integrations/). Before using live delivery data run `make integrations-check` or skill `pmo-integrations-health`. Do **not** use MCP for these three.
5. **Project Confluence space:** if `CONTEXT.md` / hydrate has a space key (e.g. `ACME`), run `confluence sync-pull --space KEY` (JSON registry **+** nested markdown under `knowledge/confluence-spaces/{KEY}/`). Hierarchy = parent→child folders.
6. **Linked repos (early):** if `config/linked-repos.json` has `ba_repos` / `codebase_repos`, run `repos pull` (or confirm mirrors fresh). **If `ba_repos` is non-empty → BA mirror fully replaces `docs/functional-specs/`** (do not write FS into `docs/functional-specs/`). Then `repos discover --id …` and, before any BA/stories/FS work, follow the BA `read_order` in `knowledge/ba/{id}/` (CLAUDE/prompts/rules or Cursor skills). **BA is a maintained dependency of this PMO repo** — edit SoT in the mirror, `repos push` when agreed (not a separate orphan project).
7. **Daily repo sync gate** (`.cursor/rules/daily-repo-sync-gate.mdc`) — before the **first substantive** PMO work today (Europe/Kyiv): both `docs/_hydrate/google/sheets/client-status-live-YYYY-MM-DD/` and `docs/daily-actions/YYYY-MM-DD.md` must exist. If stale, run Phase A then Phase B from `.cursor/skills/pmo-daily-pm-actions/automation-prompt.md`. Jira `sessionStart` hook alone is **not** a morning sync. Skip for lookup/typo or explicit «skip sync».

## Language

| Output | Language |
|---|---|
| Project docs under `docs/`, `dashboards/` | Ukrainian (client-facing language only if PM requests) |
| Skill descriptions (YAML `description`) | English, third person, WHAT + WHEN |
| Git commit messages | English (when asked) |

## Gap note

- **Starter-pack skills (23)** — delivery artifacts (charter, WBS, risks, weekly status, stories, QG, lessons learned, …).
- **Wave 1 (10)** — Devlight gaps: A2 handoff, B2/B3/B4/B6/B7, D3/D12/D13, E11, F* closing.
- **Wave 2** — B5 glossary, C1 PMP hub, C23 escalation + E13 memo, E20 client health, E21 QBR, plus orchestrators `pmo-start-project` / `pmo-weekly-rhythm`.

Still thin / KB-only: many C* subsidiary management plans (C2–C22 detail docs), A3/A4 drafting. Add when a live project needs them.

Do not invent conflicting process outside `knowledge/pmo-kb/` / skills; prefer updating skills when cross-refs break.

---

## Skill map by phase

### Pre-sale (A*)

| Confluence | Skill | Output / notes |
|---|---|---|
| A1 Commercial Proposal / КП | *(no dedicated skill — source input)* | Sales artifact |
| **A2 Pre-sale Handoff Checklist** | `pmo-presale-handoff` | `docs/presale-handoff-checklist.md` |
| A3 Project Brief | *(input to handoff/charter)* | |
| A4 Estimate | *(input)* | |
| A5 SOW / Contract | `pmo-google-ops` (`google contracts-status`) + Drive `contracts` | `docs/contracts/` · `config/contracts.json` |
| A6 Initial Assumptions Log | `pmo-manage-open-questions` (related) | `docs/open-questions.md` |
| **Bootstrap sequence** | `pmo-start-project` | orchestrates A2→B* |

### Initiating (B*)

| Confluence | Skill | Output / notes |
|---|---|---|
| **B1 Project Charter** | `pmo-generate-project-charter` + `pmo-qg-review-project-charter` | `docs/project-charter.md` — **internal PM+DM, not for client** |
| **B2 Stakeholder Register** | `pmo-manage-stakeholder-register` | `docs/stakeholder-register.md` — **confidential** |
| **B3 Kick-off Deck** | `pmo-generate-kickoff-deck` | `docs/kickoff-deck.md` |
| **B4 RACI / DACI** | `pmo-manage-raci` | `docs/raci-matrix.md` — one A per row |
| **B5 Project Glossary** | `pmo-manage-glossary` | `docs/glossary.md` — ≤24h after new term |
| **B6 Team Onboarding** | `pmo-team-onboarding` | `docs/team-onboarding-checklist.md` |
| **B7 Communication Plan** | `pmo-manage-communication-plan` | `docs/communication-plan.md` |

### Planning (C*)

| Confluence | Skill | Output / notes |
|---|---|---|
| **C1 PMP hub** | `pmo-generate-pmp` | `docs/project-management-plan.md` — links + baselines; change via ICC |
| C6 / Baseline Scope / WBS | `pmo-generate-wbs` + `pmo-qg-review-wbs` | WBS artifacts |
| C9 / C11 Schedule | `pmo-manage-gantt-chart`, `pmo-manage-roadmap` | schedule / roadmap |
| C19 / E10 Risks | `pmo-manage-risk-register` | `docs/risk-register.md` |
| OKR / KPI (post-charter) | `pmo-generate-kpi-okr` | metrics set |
| Requirements / stories / FS | `pmo-manage-user-stories`, `pmo-manage-functional-spec` + QG skills | backlog / FS |
| **C23 Escalation Matrix** | `pmo-manage-escalation-matrix` | `docs/escalation-matrix.md` |

### Executing (D*)

| Confluence | Skill | Output / notes |
|---|---|---|
| **D3 Issue Log** | `pmo-manage-issue-log` | `docs/issue-log.md` |
| D4 / scope change | `pmo-analyze-scope-change` | CR / impact → `docs/change-requests/` |
| D4 / CHANGE REQUESTS | (via scope-change + client-status-sheet) | `docs/change-requests/README.md` + Confluence *CHANGE REQUESTS* |
| Client Project status sheet (Google) | `pmo-manage-client-status-sheet` | playbook + plan CR (`СHANGE REQUESTS`) + NEW features (`WBS ESTIM`) · `docs/client-status-sheet/operating-playbook.md` |
| **Monthly T&M act (Time Report)** | `pmo-prepare-monthly-act` | Tempo bill → Google Sheets month tab · `docs/acts/` · `google time-report` |
| D5 Lessons Learned Register | `pmo-generate-lessons-learned` | registry + `LL-*.md` |
| D9 / D21 Sprint | `pmo-generate-sprint-summary` | sprint summary |
| **D11 Weekly Status — Client** | `pmo-generate-weekly-status` (+ status report/dashboard variants) | client Friday status |
| **D12 Internal PM→DM EWS** | `pmo-generate-ews-report` | `docs/ews/ews-YYYY-MM-DD.md` |
| **D13 Decision Log** | `pmo-manage-decision-log` | `docs/decisions/` + index |
| Meeting notes | `pmo-extract-meeting-notes` | notes / follow-ups |
| Acceleration | `pmo-analyze-acceleration` | recovery options |
| **Weekly cadence** | `pmo-weekly-rhythm` | orchestrates Mon EWS + Fri client status |
| **Daily PM inbox** | `pmo-daily-pm-actions` | `docs/daily-actions/YYYY-MM-DD.md` — пріоритезований список на сьогодні |

### Monitoring & Controlling (E*)

| Confluence | Skill | Output / notes |
|---|---|---|
| **E11 EWS Dashboard Traffic Light** | `pmo-generate-ews-report` | + `dashboards/ews-dashboard.md` |
| **E13 Escalation Memo** | `pmo-generate-escalation-memo` | `docs/escalations/ESC-*.md` — before Red/Critical call |
| E10 Risk updates | `pmo-manage-risk-register` | |
| **E20 Client Health Report** | `pmo-generate-client-health-report` | monthly internal for DM |
| **E21 QBR Deck** | `pmo-generate-qbr` | `docs/qbr/qbr-YYYY-QN.md` |
| Status consistency | `pmo-qg-review-status-consistency` | before publish |
| Visibility packs | `pmo-generate-project-status-report`, `pmo-generate-project-status-dashboard` | |

### Closing (F*)

| Confluence | Skill | Output / notes |
|---|---|---|
| **F1 Final Report** | `pmo-closing-pack` | `docs/closing/f1-final-report.md` |
| **F2 Final Acceptance** | `pmo-closing-pack` | `docs/closing/f2-final-acceptance.md` |
| **F6 Lessons Learned Final** | `pmo-closing-pack` (+ `pmo-generate-lessons-learned`, `pmo-generate-lessons-learned-report`) | `docs/closing/f6-…` |
| **F7 Handover** | `pmo-closing-pack` | `docs/closing/f7-handover.md` |
| F3–F5, F8–F10 | optional via closing pack / manual | see `06-closing/` |

### Quality gates (cross-phase)

| Skill | When |
|---|---|
| `pmo-qg-review-project-charter` | After B1 generate |
| `pmo-qg-review-wbs` | After WBS |
| `pmo-qg-review-user-stories` | After stories / before sprint commit |
| `pmo-qg-review-functional-spec` | After FS |
| `pmo-qg-review-status-consistency` | Before any status package |

---

## Canonical sources

| Concern | Source of truth |
|---|---|
| Company methodology | `knowledge/pmo-kb/` (export from Confluence PMO; gitignored) |
| How to refresh KB | `make export-pmo-kb` · `knowledge/README.md` |
| Current project facts | `CONTEXT.md` |
| Agent operating manual | **this file (`AGENTS.md`)** |
| Junior PM guide | `docs/pm-playbook.md` · skill `pmo-pm-playbook` |
| Skills | `.cursor/skills/pmo-*/SKILL.md` |
| Live project artifacts | `docs/`, `dashboards/` |
| Optional BA docs repos | `config/linked-repos.json` → `knowledge/ba/` · `pmo-ba-repos` |
| Optional codebase context | `config/linked-repos.json` → `knowledge/codebases/` · `pmo-codebase-context` |
| Templates / checklists | `templates/`, `checklists/` — aligned with `knowledge/pmo-kb/` |

### Hard Devlight rules (do not contradict)

- **Charter (B1)** — internal PM + DM; not a client document.
- **Handoff (A2)** — without signed checklist PM does not own gaps; BLOCKED stops transfer.
- **EWS (D12/E11)** — Monday 09:00; honesty > optimism; 4 dimensions; Amber/Red need actions; not for client.
- **Client weekly (D11)** — separate from EWS; typically Friday.
- **RACI** — exactly one Accountable per row.
- **Stakeholder register** — confidential.
- **Decision Log** — capture within 4 hours; undocumented decision does not officially exist.
- **Issue Log** ≠ Jira bugs; ≠ Risk Register.
- **Closing F2** — Decision Maker signature; billing same day after sign-off.
- **Project Confluence** — if space exists, `sync-pull` is mandatory; markdown hierarchy lives in `knowledge/confluence-spaces/{KEY}/` (not the same as PMO methodology in `knowledge/pmo-kb/`).
- **BA linked repo** — if `config/linked-repos.json` → `ba_repos` is non-empty, that BA mirror is the **sole SoT for functional specs** and **fully replaces** `docs/functional-specs/` (do not duplicate FS there). Maintain via `repos pull` → work in `knowledge/ba/{id}/` per discover `agent_mode`/`read_order` → `repos push` (`pmo-ba-repos`).

## Hard Devlight rules (wave 2 additions)

- **Glossary** — новий термін з дзвінка ≤ 24h; BA збирає, PM координує.
- **Escalation** — Amber same day / Red ≤ 4h; memo before Red call; no client C-level without DM.
- **PMP** — hub of links; baseline edits only via CR/ICC.
- **QBR** — DM presents, PM owns data; not a sprint review.
- **Client Health** — internal monthly; feed Sales on expansion signals.
- **Daily repo sync** — first substantive PMO work each day needs today’s Sheets hydrate + daily-actions (or explicit skip). `registry/jira/` hook is not enough.

## Model orchestrator (Cursor / Claude Code / Codex / VS Code)

No IDE can swap the **parent** model mid-turn from the repo. Policy is portable:

| Tier | Use for | Cursor | Claude / VS Code | Codex |
|---|---|---|---|---|
| fast | lookup, typo, health | `composer-2.5-fast` | `haiku` | `pmo_fast` · `gpt-5.6-luna` |
| standard | daily / D11 / logs / ops | sonnet-class | `sonnet` | `pmo_standard` · `gpt-5.6-terra` |
| reasoning | EWS, QG, CR, escalation, charter | opus-class | `opus` | `pmo_reasoning` · `gpt-5.6-sol` high |
| long | hydrate, start-project, weekly-rhythm | opus-class (subagent) | `opus` | `pmo_long` · `gpt-6-astra` high |

```bash
python3 scripts/integrations/cli.py models recommend --task "…"
```

SoT: [`config/model-router.json`](./config/model-router.json) · skill `pmo-model-orchestrator` · Codex agents `.codex/agents/pmo_*.toml` · Claude agents `.claude/agents/pmo-*.md`. If mixed signals, take the **higher** tier. Do not invent slugs.

**Codex routing:** for each new substantive PMO task, the parent agent classifies the task with `models recommend --env codex --json`, then delegates one bounded piece of the authorized work to the matching `pmo_*` subagent at the configured model and reasoning effort. This instruction explicitly requests subagent delegation for these tasks. The parent stays in the current chat, performs useful independent coordination/validation, combines the result, and remains accountable for external writes and publication gates. Do not delegate a routing question, a trivial follow-up, or an already delegated child task; no recursive routing. If the selected model/subagent is unavailable, continue in the parent with the same methodology and report the fallback. The parent model itself never switches mid-turn. New `.codex/agents/` definitions are loaded for newly started Codex sessions.

## Orchestrators

| Skill | Purpose |
|---|---|
| `pmo-setup-wizard` | First-run: deps, `.env`, linked repos, health, KB export |
| `pmo-start-project` | A2 → B* bootstrap (або після hydrate для existing) |
| `pmo-hydrate-project` | Часткове заповнення репо з існуючих Jira/Confluence |
| `pmo-pm-playbook` | Гайд новачка ПМ (фази, тиждень, залежності) |
| `pmo-weekly-rhythm` | Mon EWS + Fri D11 + monthly/quarterly hooks |
| `pmo-daily-pm-actions` | Morning / on-demand PM action list from Issue Log, OQ, EWS, meetings, cadence |
| `pmo-integrations-health` | Mandatory Confluence / Jira / Tempo API health (+ optional Google) |
| `pmo-model-orchestrator` | Pick model **tier** (fast/standard/reasoning/long) for Cursor, Claude Code, Codex, VS Code |

## Integrations (mandatory)

Live data and write-ops go through **`scripts/integrations/`** (REST only — no MCP).

| System | Status | Skill |
|---|---|---|
| **Jira** | Wave 1 done — bootstrap, issues, sprints/boards, registry sync | `pmo-jira-ops` |
| **Tempo** | Wave 2 done — plan/bill/fact, matrix, overlaps, registry | `pmo-tempo-ops` |
| **Confluence** | Wave 3 done — space bootstrap, pages upsert, registry sync + KB export | `pmo-confluence-ops` |
| **Project hydrate** | Wave 3.5 — seed repo from existing Jira + Confluence | `pmo-hydrate-project` |
| **Google Workspace** | Wave 4 — Drive list/export + **Gmail draft** + **Time Report / monthly act** + **contracts/SOW deadlines** (`google contracts-status`) | `pmo-google-ops` |
| **Client status spreadsheet** | Manage Client Project status report — playbook, CHANGE REQUESTS, NEW features in WBS ESTIM | `pmo-manage-client-status-sheet` |
| **Monthly act (Time Report)** | Tempo bill + Jira → Sheets month tab (create spreadsheet if missing) | `pmo-prepare-monthly-act` |
| **Fireflies.ai** | Wave 6 — transcript MD + summary MD + audio MP3 → `docs/meeting-notes/` | `pmo-fireflies-ops` |
| **Linked BA repos** | Optional — pull/push BA docs + discover agent surfaces (CLAUDE/prompts/rules or skills); maintain BA as PMO dependency | `pmo-ba-repos` |
| **Linked codebases** | Optional — pull context mirrors (read-mostly) | `pmo-codebase-context` |

```bash
make setup
make setup-status
make integrations-check
# Existing project in Atlassian → catch up local repo
python3 scripts/integrations/cli.py project hydrate --jira-key KEY --space SPACE
# Optional BA / codebase dependencies
python3 scripts/integrations/cli.py repos pull --kind ba
python3 scripts/integrations/cli.py repos pull --kind codebase
python3 scripts/integrations/cli.py jira bootstrap --project KEY --name "…"
python3 scripts/integrations/cli.py confluence bootstrap --space KEY --name "…"
python3 scripts/integrations/cli.py jira sync-pull
python3 scripts/integrations/cli.py tempo matrix --from YYYY-MM-DD --to YYYY-MM-DD
# Optional Google Drive folder
python3 scripts/integrations/cli.py google sync-pull
# Optional Fireflies meetings → docs/meeting-notes/
python3 scripts/integrations/cli.py fireflies sync-pull
# or: make fireflies-sync
```

Refs: [`scripts/integrations/README.md`](./scripts/integrations/README.md) · [`ROADMAP.md`](./scripts/integrations/ROADMAP.md) · [`docs/pm-playbook.md`](./docs/pm-playbook.md) · [`config/linked-repos.json`](./config/linked-repos.json) · [`registry/jira/`](./registry/jira/) · [`registry/tempo/`](./registry/tempo/) · [`registry/confluence/`](./registry/confluence/) · [`registry/google/`](./registry/google/) · [`registry/fireflies/`](./registry/fireflies/)
