# Integrations roadmap

## Done — Jira (wave 1)

- Project create + Devlight bootstrap (board, sprint, methodology epic)
- Issues: all creatable types, transition, assign, JQL filter
- Boards / sprints start-complete / move issues
- Bidirectional registry: `registry/jira/`

## Done — Tempo (wave 2)

- Worklogs write: **fact** (`timeSpentSeconds`) + **bill** (`billableSeconds`)
- Plans write: **plan** (`plannedSecondsPerDay`) via Planner API
- Resource **matrix** (plan vs fact vs bill) + **overlap** detection
- Registry: `registry/tempo/` (+ local drafts → sync-push)
- Skill: `pmo-tempo-ops`

## Done — Confluence (wave 3)

- Create space (v1/v2) + Devlight project page tree bootstrap
- Create / update / upsert pages (markdown → storage)
- Bidirectional registry: `registry/confluence/` (pull / dirty / push)
- **Hierarchical markdown mirror** for project spaces → `knowledge/confluence-spaces/{KEY}/` (on `sync-pull` / `export-md`)
- Corporate PMO KB export → `knowledge/pmo-kb/`
- Skill: `pmo-confluence-ops`
- Pipeline rule: if project Confluence space exists → pull it (hydrate + session)

## Done — Project hydrate (wave 3.5)

- Catch-up path when Jira/Confluence already have the project
- `cli.py project hydrate` → registries + CONTEXT hints + mapped doc stubs
- Mapping: `config/artifact-source-map.json`
- Skill: `pmo-hydrate-project`
- Report: `docs/_hydrate/FROM_SYSTEMS.md`

## Done — Fireflies (wave 6)

- GraphQL client: list / get transcript (sentences + summary + audio_url)
- Sync → `docs/meeting-notes/{date}-{slug}/` (`transcript_raw.md`, `summary.md`, `audio.mp3`)
- Registry: `registry/fireflies/`
- CLI: `fireflies ping|list|pull|sync-pull` · `make fireflies-sync`
- Skill: `pmo-fireflies-ops`
- Optional health probe (like Google)

## Next — Google Workspace (wave 4 continued)

- [x] Config + optional health + Drive list / Doc export scaffold
- [x] Registry mirror `registry/google/` + skill `pmo-google-ops`
- [x] **Gmail draft** from weekly-status email MD (`google gmail-draft`, multipart HTML + Settings signature via `sendAs`)
- [x] **Monthly Time Report / act** — Tempo bill + Jira → Sheets create/fill (`google time-report`, skill `pmo-prepare-monthly-act`)
- [x] **Contracts / SOW register** — Drive dir `contracts` + `config/contracts.json` deadlines / stages (`google contracts-status` → `docs/contracts/`)
- [ ] Docs ↔ local markdown bidirectional sync (conflict policy like Confluence)
- [ ] Sheets pull for risk/capacity matrices
- [ ] Shared Drive / folder bootstrap per project
- [ ] Optional: send-after-confirm (explicit flag only; default remains draft)

## Done — Linked repos (wave 5 scaffold)

- Optional BA documentation repos + codebase context repos
- Config: `config/linked-repos.json` (+ example)
- CLI: `repos list|status|pull|push|discover`
- Mirrors: `knowledge/ba/`, `knowledge/codebases/` (gitignored)
- Discover: `agent_mode` (cursor-skills | claude-prompts-rules | hybrid | docs-only), `read_order`, prompts/rules
- Skills: `pmo-ba-repos`, `pmo-codebase-context`
- Pipeline: BA maintained as PMO dependency when `ba_repos` set (AGENTS session start + start-project)
- Junior PM playbook: `docs/pm-playbook.md` · `pmo-pm-playbook`
- Setup wizard: `make setup` · `pmo-setup-wizard` (deps + `.env` + health)

## Done — Model orchestrator (portable)

- Tiers `fast|standard|reasoning|long` in `config/model-router.json`
- CLI: `models recommend|policy|env` (no LLM, no API keys)
- Adapters: Cursor Task slug, Claude Code / VS Code `.claude/agents`, Codex `--model`
- Skill: `pmo-model-orchestrator`

See `scripts/integrations/README.md` for current CLI.
