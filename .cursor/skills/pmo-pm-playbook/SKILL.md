---
name: pmo-pm-playbook
description: Junior/new PM operating guide for the Devlight PMO pipeline — what to do first, weekly rhythm, which skills to run by phase, and when to use hydrate, BA/codebase repos, and integrations. Use when onboarding a PM to this repo or asking what to do next.
---

# Playbook для ПМ (новачок → операційний ритм)

Читай також: [`docs/pm-playbook.md`](../../../docs/pm-playbook.md) (повний текст).

## When to use

- Перший день у цьому репо / проєкті
- «Що мені робити далі?»
- Онбординг junior PM на Devlight pipeline

## Quick path

1. `make setup` / `pmo-setup-wizard` (deps + `.env` + health)
2. `CONTEXT.md` заповнений?
3. `make export-pmo-kb` (якщо візард не зробив) + `make setup-status`
4. **Linked repos EARLY** — `config/linked-repos.json` + `repos pull` + `repos discover` (`pmo-ba-repos` / `pmo-codebase-context`). Якщо є BA → FS SoT = BA mirror (не `docs/functional-specs/`); BA = maintained dependency (edit mirror → push).
5. Новий проєкт → `pmo-start-project` | Уже є Atlassian → `pmo-hydrate-project`
6. Щодня → `pmo-daily-pm-actions` | Щотижня → `pmo-weekly-rhythm`
7. Карта skills → `AGENTS.md`

Не вигадуй процес — бери з `knowledge/pmo-kb/` і skills.
