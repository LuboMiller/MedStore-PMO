# Knowledge base

Локальні дзеркала методології та залежностей для PMO-пайплайну.

## `knowledge/pmo-kb/` — Devlight PMO база знань

Експорт корпоративного Confluence space **PMO** (методологія A*…F*, rules, procedures).
**gitignored** — не комітиться.

```bash
make export-pmo-kb
# alias: make export-confluence
# python3 scripts/confluence-export/export_pmo.py --space PMO
```

## `knowledge/confluence-spaces/{KEY}/` — wiki проєкту

Markdown-дзеркало **проєктного** Confluence space (ієрархія parent→child).
Обов’язково, якщо space є в CONTEXT / hydrate.

```bash
python3 scripts/integrations/cli.py confluence sync-pull --space KEY
# → registry/confluence/spaces/KEY/      (JSON, для push)
# → knowledge/confluence-spaces/KEY/     (MD tree)
```

Лише MD з уже стягнутого registry:

```bash
python3 scripts/integrations/cli.py confluence export-md --space KEY
```

## Як агенту користуватись

1. На старті сесії: `CONTEXT.md` + цей файл / `knowledge/pmo-kb/README.md` (методологія).
2. Skills `pmo-*` посилаються на сторінки в `knowledge/pmo-kb/` (`a2-…`, `b1-…`, `d12-…`, …).
3. Якщо `knowledge/pmo-kb/` відсутній — `make export-pmo-kb`, не вигадуй процес Devlight.
4. Проєктна wiki — `knowledge/confluence-spaces/{KEY}/`, не плутати з PMO KB.

Канонічна карта: [`AGENTS.md`](../AGENTS.md).

## Linked BA / codebase repos (optional)

| Каталог | Призначення | Config |
|---|---|---|
| `knowledge/ba/{id}/` | Дзеркало BA SoT (+ CLAUDE/prompts/rules або skills) — **залежність пайплайну** | `ba_repos` |
| `knowledge/codebases/{id}/` | Контекст коду / README | `codebase_repos` |

```bash
python3 scripts/integrations/cli.py repos pull --kind ba
python3 scripts/integrations/cli.py repos discover --id <ba-id>
python3 scripts/integrations/cli.py repos pull --kind codebase
```

Якщо `ba_repos` непорожній: FS лише з BA mirror; перед BA-роботою читай `discover.read_order`. Зміни → `repos push`.

Skills: `pmo-ba-repos`, `pmo-codebase-context` · гайд: [`docs/pm-playbook.md`](../docs/pm-playbook.md).
