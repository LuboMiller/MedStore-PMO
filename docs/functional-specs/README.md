# Functional Specs

> Якщо в `config/linked-repos.json` є непорожній `ba_repos[]`,
> **SoT функціональних специфікацій = BA-репо** (`knowledge/ba/{id}/` після `repos pull --kind ba`).
> У такому разі **не створюй і не оновлюй** файли в цій директорії — `docs/functional-specs/` вважається **вимкненою**.

| Стан | Де писати FS |
|---|---|
| `ba_repos` порожній / немає | Тут: `docs/functional-specs/FS-NN-*.md` (skill `pmo-manage-functional-spec`) |
| `ba_repos` налаштований | Mirror BA: `knowledge/ba/{id}/` · skill `pmo-ba-repos` |

Див. `AGENTS.md` · `docs/pm-playbook.md` §2 · `.cursor/skills/pmo-ba-repos/SKILL.md`.
