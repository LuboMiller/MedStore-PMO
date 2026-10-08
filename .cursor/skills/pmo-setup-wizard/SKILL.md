---
name: pmo-setup-wizard
description: Guides first-run setup of the PMO pipeline — Python deps, .env credentials, optional linked BA/codebase repos, integrations health, and Confluence KB export. Use when cloning the repo, onboarding a new PM, or env/deps are missing.
---

# Setup wizard (deps + env)

## When to use

- Свіжий clone `pmo-pipilene`
- Немає `.env` / падає `integrations-check`
- Новачок ПМ питає «з чого почати технічно»
- Перед `pmo-start-project` / hydrate, якщо сетап ще не робили

## Instructions

1. Діагностика (без змін):

```bash
make setup-status
# або
python3 scripts/integrations/cli.py setup status
```

2. Інтерактивний візард (веде по кроках):

```bash
make setup
# або
python3 scripts/integrations/cli.py setup wizard
```

Кроки візарда:
1. `pip install` (integrations + confluence-export; опційно Google)
2. Створити `.env` з `.env.example` якщо немає
3. Запитати Atlassian / Jira key / опційно Tempo / Google / Fireflies
4. **Linked repos EARLY** — `config/linked-repos.json` (BA + codebase). Якщо BA є → FS SoT = BA (не `docs/functional-specs/`); після pull — `repos discover` і підтримка BA як залежності (`pmo-ba-repos`)
5. `health` check
6. Опційно `export` PMO KB → `knowledge/pmo-kb/`
7. Записати `docs/_hydrate/SETUP_STATUS.md` + next actions

3. Non-interactive (агент / CI після того як секрети вже в env):

```bash
python3 scripts/integrations/cli.py setup wizard --yes --export-kb
```

4. Після зеленого status → `docs/pm-playbook.md` / `pmo-start-project` / `pmo-hydrate-project`.

## Rules

1. Не коміть `.env` і `secrets/`.
2. Не вигадуй токени — якщо користувач не дав, залиш missing у status.
3. Tempo / Google / Fireflies — optional на першому проході; Atlassian — required для live Confluence.

## Related

- `pmo-pm-playbook` · `pmo-integrations-health` · `pmo-ba-repos`
- Makefile: `make setup` · `make setup-status`
