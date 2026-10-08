# Playbook ПМ — Devlight PMO Pipeline

Гайд для новачка: **за чим іти**, які skills запускати, де SoT. Детальна карта артефактів — у [`AGENTS.md`](../AGENTS.md).

---

## 0. За 30 хвилин (перший сетап)

**Рекомендовано — візард** (deps → `.env` → optional repos → health → KB):

```bash
make setup                 # інтерактивно
make setup-status          # що ще відсутнє
# або: python3 scripts/integrations/cli.py setup wizard
```

Skill: **`pmo-setup-wizard`**. Звіт: `docs/_hydrate/SETUP_STATUS.md`.

Ручний мінімум (якщо без візарда):

1. Скопіюй `.env.example` → `.env`, додай Atlassian (+ Tempo за потреби).
2. `make export-pmo-kb` — локальна PMO база знань у `knowledge/pmo-kb/`.
3. `make integrations-check` — Confluence / Jira / Tempo (Google / Fireflies optional).
4. Заповни [`CONTEXT.md`](../CONTEXT.md) (назва, клієнт, PM/DM, посилання).
5. У Cursor працюй із skills `pmo-*`; на старті сесії — CONTEXT + AGENTS + knowledge.

---

## 1. Два сценарії старту

### A. Новий проєкт (greenfield)

Skill: **`pmo-start-project`** (Path A)

Порядок: handoff A2 → CONTEXT → charter+QG → stakeholders → RACI → glossary → comms → escalation → onboarding → kickoff → далі PMP/WBS.

### B. Уже є Jira / Confluence

Skill: **`pmo-hydrate-project`**

```bash
python3 scripts/integrations/cli.py project hydrate --jira-key KEY --space SPACE
```

Потім дочитай `docs/_hydrate/FROM_SYSTEMS.md`, дозаповни CONTEXT, прожени mapped stubs через відповідні skills (не лишай seed як фінал). Далі — Path A з відсутніх кроків.

---

## 2. Опційні залежності (BA + codebase) — **рано в пайплайні**

Підключай **одразу після CONTEXT** (до charter/stories/FS), не в кінці catch-up.

PMO-репо **не зобов’язаний** тримати всю BA-документацію чи код. Підключи їх у `config/linked-repos.json` (зразок: `config/linked-repos.example.json`).

| Тип | Skill | Mirror | Типовий sync |
|---|---|---|---|
| BA docs (+ agent surfaces) | `pmo-ba-repos` | `knowledge/ba/{id}/` | pull + за потреби push |
| Application codebase | `pmo-codebase-context` | `knowledge/codebases/{id}/` | pull (context-only) |

```bash
python3 scripts/integrations/cli.py repos pull --kind ba
python3 scripts/integrations/cli.py repos pull --kind codebase
python3 scripts/integrations/cli.py repos discover --id <id>
```

**Правило FS / BA:** якщо `ba_repos[]` **непорожній** — BA-репо **повністю замінює** `docs/functional-specs/` як SoT специфікацій. Не пиши FS у `docs/functional-specs/`. Якщо BA немає — FS лишаються в `docs/functional-specs/` (див. README там).

**BA як залежність цього проєкту:** окремий BA-репо лишається upstream; надалі підтримуй його з PMO-сесії — `pull` → зміни в mirror за `discover.read_order` (`CLAUDE.md` / prompts / rules або Cursor skills) → `repos push --id …`. Не дублюй BA-процес у PMO docs.

**Правило:** BA-репо = SoT вимог (якщо так зафіксовано в CONTEXT). Код = лише контекст для ризиків/scope. Методологія компанії = `knowledge/pmo-kb/`.

---

## 3. Тижневий ритм (обов’язково запам’ятати)

Skill: **`pmo-weekly-rhythm`**

| Коли | Що | Skill / вихід |
|---|---|---|
| Щодня / ранок | Live SoT + PM inbox (gate) | `.cursor/rules/daily-repo-sync-gate.mdc` → hydrate + `pmo-daily-pm-actions` → `docs/daily-actions/YYYY-MM-DD.md` |
| Пн ≤ 09:00 | EWS для DM (чесність > оптимізм) | `pmo-generate-ews-report` → `docs/ews/` + dashboard |
| Пт | Client weekly (No Surprises) | `pmo-generate-weekly-status` → `docs/weekly-status/{{YYYY-MM-DD}}/` + QG · опційно `gmail-draft` |
| За потребою | Issue / decision / risk updates | відповідні `pmo-manage-*` |

EWS **не** для клієнта. Client status **окремо** від EWS.

Перед live-цифрами: `make integrations-check` (+ Tempo для Budget).

Перед **першою** змістовною PMO-роботою за день: rule **daily-repo-sync-gate** — потрібні сьогоднішні `docs/_hydrate/google/sheets/client-status-live-YYYY-MM-DD/` і `docs/daily-actions/YYYY-MM-DD.md`. Якщо немає — Phase A + B з `automation-prompt.md`. Jira sessionStart hook сам по собі недостатній. Lookup / «skip sync» — винятки.

---

## 4. Фазовий маршрутизатор (що робити далі)

| Фаза | Типові skills | Вихід |
|---|---|---|
| Pre-sale | `pmo-presale-handoff` | `docs/presale-handoff-checklist.md` |
| Initiating | charter, stakeholders, RACI, glossary, comms, kickoff | `docs/*` |
| Planning | PMP, WBS+QG, risks, roadmap/gantt, stories/FS+QG, escalation | baselines |
| Executing | issue log, decisions, meeting notes, sprint summary, weekly | logs + status |
| Controlling | EWS, escalation memo, client health, QBR | internal + QBR |
| Closing | `pmo-closing-pack` | `docs/closing/*` |

Повна таблиця — **AGENTS.md → Skill map by phase**.

---

## 5. Інтеграції (коли чіпати системи)

| Система | Навіщо ПМ | Skill |
|---|---|---|
| Jira | проєкт, issues, спринти | `pmo-jira-ops` |
| Tempo | plan/fact/bill, matrix | `pmo-tempo-ops` |
| Confluence | space/pages проєкту + KB | `pmo-confluence-ops` |
| Google Drive/Docs | опційно, статуси в Docs | `pmo-google-ops` |
| Fireflies | опційно, transcript + summary + mp3 → `docs/meeting-notes/` | `pmo-fireflies-ops` |
| Linked repos | BA + code context | `pmo-ba-repos`, `pmo-codebase-context` |
| Model orchestrator | яку модель у Cursor / Claude / Codex / VS Code | `pmo-model-orchestrator` |

Усе через `scripts/integrations/` (REST/git) — **без MCP** для цих систем. Модель: `python3 scripts/integrations/cli.py models recommend --task "…"`.

---

## 6. Жорсткі правила (не порушуй)

- Charter — внутрішній (PM+DM), не клієнту.
- Handoff BLOCKED → не бери ownership gap’ів.
- RACI — рівно один Accountable на рядок.
- Decision — зафіксуй ≤ 4 год.
- Issue Log ≠ Jira bugs ≠ Risk Register.
- Escalation Red — memo перед дзвінком; клієнтський C-level лише через DM.
- Daily sync gate — перша змістовна робота за день не на stale hydrate (або explicit skip).

---

## 7. Чекліст «що далі?» (швидка діагностика)

- [ ] Немає CONTEXT → заповни / hydrate  
- [ ] Немає handoff / charter → `pmo-start-project`  
- [ ] Є BA-репо, але порожній `knowledge/ba/` → `repos pull --kind ba`  
- [ ] Пн без EWS → `pmo-weekly-rhythm` / EWS  
- [ ] Клієнт питає статус → weekly status + QG, не сирий EWS  
- [ ] Scope change → `pmo-analyze-scope-change`  
- [ ] Red/Critical → escalation matrix + memo  

---

## 8. Куди дивитись

| Питання | Файл |
|---|---|
| Карта skills | `AGENTS.md` |
| Факти проєкту | `CONTEXT.md` |
| Методологія | `knowledge/pmo-kb/` |
| CLI інтеграцій | `scripts/integrations/README.md` |
| Linked repos | `config/linked-repos.json` |
