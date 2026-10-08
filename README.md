# Devlight PMO Pipeline

Узагальнений AI PMO-пайплайн компанії на базі [Confluence PMO space](https://devlight.atlassian.net/wiki/spaces/PMO/) (локально: `knowledge/pmo-kb/`) і Cursor skills у `.cursor/skills/pmo-*`.

**GitHub Template:** [Use this template](https://github.com/LuboMiller/pmo-pipilene/generate) — створи новий репозиторій проєкту з цієї бази (без історії комітів template’а). Далі `make setup` → заповни `CONTEXT.md` → `pmo-start-project` або `pmo-hydrate-project`.

## Швидкий старт

```bash
# 1. Setup wizard (deps + .env + health; optional linked repos / KB export)
make setup
make setup-status

# 2. Або вручну:
cp .env.example .env   # заповни токени
make export-pmo-kb

# 3. У Cursor — skills у `.cursor/skills/pmo-*`
# На початку сесії: CONTEXT.md + AGENTS.md + knowledge/pmo-kb/
```

Типові входи:

- Перший сетап → `make setup` · skill `pmo-setup-wizard`
- Новий ПМ / «що робити?» → `docs/pm-playbook.md` · skill `pmo-pm-playbook`
- Новий проєкт → skill `pmo-start-project`
- Уже є Jira/Confluence → skill `pmo-hydrate-project` (часткове заповнення репо)
- BA-репо / codebase → `config/linked-repos.json` · `pmo-ba-repos` / `pmo-codebase-context` (BA = maintained dependency: pull → discover → push)
- Тижневий ритм → skill `pmo-weekly-rhythm`
- Ранковий sync перед першою PMO-роботою → rule `.cursor/rules/daily-repo-sync-gate.mdc` · `pmo-daily-pm-actions`
- Яка модель (Cursor / Claude / Codex / VS Code) → `python3 scripts/integrations/cli.py models recommend --task "…"` · skill `pmo-model-orchestrator`
- Codex: нові PMO-задачі маршрутизуються до проєктних субагентів `.codex/agents/` за рівнем моделі; основний чат перевіряє результат (див. `AGENTS.md`).
- Перевірка API (Confluence / Jira / Tempo; Google optional) → `make integrations-check`

## Структура

| Шлях | Призначення |
|---|---|
| `.cursor/skills/` | PMO skills (`pmo-*`) |
| `.cursor/rules/` | Always-on agent rules (model orchestrator, daily sync gate) |
| `.codex/agents/` | Codex subagents by model tier (`pmo_fast` … `pmo_long`) |
| `scripts/integrations/` | **Обов'язковий** REST-шар: Confluence, Jira, Tempo (+ Google scaffold) |
| `knowledge/pmo-kb/` | PMO база знань (методологія) (локально, gitignored) |
| `config/` | Jira/Confluence templates + artifact source map |
| `registry/` | Дзеркала Jira / Tempo / Confluence / Google |
| `templates/` | Шаблони артефактів (`tl-*`) |
| `checklists/` | Процесні чеклісти |
| `docs/` | Живі документи проєкту |
| `dashboards/` | Roadmap, sprint tracker, EWS |
| `scripts/confluence-export/` | Pull PMO space через API |

## Пайплайн за фазами Devlight

```
Pre-sale (A*) → Initiating (B*) → Planning (C*) → Executing (D*)
                                              ↘ Monitoring & Controlling (E*)
                                              → Closing (F*)
```

Детальна карта skills ↔ артефактів Confluence — у [AGENTS.md](./AGENTS.md).

## Команди

```bash
make setup                # wizard: deps + .env + health
make setup-status         # checklist missing items
make integrations-check   # Confluence + Jira + Tempo health
make export-pmo-kb    # оновити knowledge/pmo-kb з Atlassian
make repos-pull           # optional BA/codebase mirrors from linked-repos.json
make repos-discover       # BA agent surfaces (set REPO_ID=<ba-id>)
make skills-list          # список pmo-* skills
```
