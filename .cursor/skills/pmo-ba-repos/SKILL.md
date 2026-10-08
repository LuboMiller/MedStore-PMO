---
name: pmo-ba-repos
description: Links optional BA documentation repositories — pull specs/stories/context and BA agent surfaces (CLAUDE/prompts/rules or Cursor skills) into knowledge/ba, discover operating mode, and push agreed updates back. Use when BA docs live in a separate repo or PM needs BA SoT for stories/FS/QG. When configured, BA fully replaces docs/functional-specs/ and is maintained as a PMO dependency.
---

# BA linked repositories

## When to use

- Спеки / user stories / glossary живуть у **окремому BA-репо**
- **Ранній крок пайплайну** — одразу після CONTEXT (до charter stories/FS)
- Треба підтягнути BA-контекст і їхні agent surfaces перед `pmo-manage-user-stories` / FS / QG
- Потрібно повернути узгоджені правки з PMO-сесії назад у BA-репо
- **Підтримувати BA надалі як залежність цього PMO-проєкту** (не як окремий orphan)

## Hard rule — FS SoT

Якщо `config/linked-repos.json` → `ba_repos` **непорожній**:

| | |
|---|---|
| **SoT functional specs** | `knowledge/ba/{id}/` (після pull) |
| **`docs/functional-specs/`** | **Вимкнено** — не GENERATE/UPDATE FS туди |
| Skill FS | Пиши/оновлюй у BA mirror (+ `repos push` за потреби); QG читає з BA |

Якщо `ba_repos` порожній — як раніше: `docs/functional-specs/` + `pmo-manage-functional-spec`.

## Maintained dependency model (pipeline)

BA-репо лишається **окремим git upstream**. PMO не зливає його історію в себе — працює через mirror:

```
repos pull --kind ba
  → repos discover --id {id}   # agent_mode + read_order + prompts/rules/skills
  → edit SoT in knowledge/ba/{id}/  (follow BA manuals/prompts)
  → repos push --id {id}       # sync=bidirectional only; dry-run first
```

Обов’язково в session start / start-project / перед stories·FS·QG (див. `AGENTS.md`).

## Agent surfaces (discover)

`repos discover` визначає `agent_mode`:

| Mode | Що читати в mirror |
|---|---|
| `claude-prompts-rules` | `CLAUDE.md` → `CLAUDE-PROJECT.md` → релевантний `docs/ba/prompts/*` → rules |
| `cursor-skills` | `AGENTS.md` / `CONTEXT.md` → `.cursor/skills/**/SKILL.md` |
| `hybrid` | skills **і** CLAUDE/prompts — не супереч BA rules |
| `docs-only` | лише артефакти під `docs/` |

Типовий BA layout: **`claude-prompts-rules`** — FS часто в `docs/ba/artifacts/specs/` (або як у `discover.read_order`).

Перед BA-роботою з PMO-сесії: виконай discover і прочитай `read_order` з дзеркала. Не вигадуй BA-процес поверх `CLAUDE.md`.

## Setup

1. Додай запис у `config/linked-repos.json` (зразок: `config/linked-repos.example.json`):

```json
{
  "ba_repos": [{
    "id": "acme-ba",
    "url": "git@github.com:org/acme-ba-docs.git",
    "ref": "main",
    "sync": "bidirectional",
    "context_files": ["CLAUDE.md", "CLAUDE-PROJECT.md", "AGENTS.md", "docs/**"],
    "agent_entrypoints": ["CLAUDE.md", "CLAUDE-PROJECT.md", "AGENTS.md", "CONTEXT.md"],
    "skills_glob": ".cursor/skills/**/SKILL.md",
    "prompts_globs": ["docs/ba/prompts/**/*.md"],
    "rules_globs": ["docs/ba/rules/**/*", ".cursor/rules/**/*"]
  }]
}
```

Або `"path": "../acme-ba-docs"` для локального checkout без clone з remote.

2. Pull + discover:

```bash
python3 scripts/integrations/cli.py repos pull --kind ba
python3 scripts/integrations/cli.py repos discover --id acme-ba
```

Mirror: `knowledge/ba/{id}/` (gitignored).

## Instructions

1. `repos list` / `repos status` — що підключено.
2. `repos pull --kind ba` — оновити дзеркало.
3. `repos discover --id …` — `agent_mode`, `read_order`, prompts/rules/skills, `artifact_roots`.
4. Перед BA / stories / FS / QG — читай SoT і manuals з mirror за `read_order` (не дублюй у `docs/functional-specs/`).
5. Зміни вимог — лише в mirror; узгоджені — `repos push --id …` (спочатку `--dry-run`).
6. Конфлікти git — вручну в mirror; не force-push з пайплайну.

## Rules

1. BA-репо опційне; відсутність запису ≠ помилка (тоді FS у `docs/functional-specs/`).
2. **Наявність `ba_repos` = повна заміна `docs/functional-specs/`.**
3. SoT для вимог — BA-репо; PMO `docs/` — delivery/PMO шар.
4. Не пуш у codebase через цей skill.
5. Поважай BA `CLAUDE.md` / `AGENTS.md` / prompts / skills у mirror — не супереч їхнім правилам документації.
6. **Підтримка BA йде з цього PMO-проєкту як залежність** — окремий «тільки BA» workflow не потрібен, якщо pull/discover/push дотримані.

## Related

- `pmo-codebase-context` · `pmo-manage-user-stories` · `pmo-manage-functional-spec`
- Pipeline: `AGENTS.md` session start · `pmo-start-project` · `docs/pm-playbook.md` §2
- CLI: `scripts/integrations/cli.py repos …`
- Pointer: `docs/functional-specs/README.md`
