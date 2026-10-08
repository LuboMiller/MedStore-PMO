---
name: pmo-model-orchestrator
description: Routes a PMO request to a model tier (fast/standard/reasoning/long) for Cursor, Claude Code, Codex, or VS Code. Use at session start, before heavy skills (EWS, QG, hydrate), or when the PM asks which model to use.
---

# Model orchestrator (portable)

## When to use

- «Яку модель взяти?» / занадто слабка або занадто дорога модель на задачі
- Перед EWS, QG, charter, CR impact, escalation, hydrate, start-project
- Сесія в **Cursor**, **Claude Code**, **Codex** або **VS Code + Claude**

Жодне середовище не вміє надійно **замінити батьківську модель посеред ходу**. Оркестратор класифікує задачу і:

1. спавнить **субагента** з потрібною моделлю (Cursor Task / Claude `.claude/agents` / Codex `.codex/agents`), **або**
2. працює в основному чаті, якщо субагенти недоступні. Модель основного чату не змінюється.

## Role

Ти не вигадуєш slug моделі. SoT: `config/model-router.json`. Класифікація — детермінована (без LLM):

```bash
python3 scripts/integrations/cli.py models recommend --task "{{USER REQUEST}}"
python3 scripts/integrations/cli.py models recommend --task "…" --env cursor --json
python3 scripts/integrations/cli.py models policy
python3 scripts/integrations/cli.py models env
```

Якщо CLI недоступний — застосуй таблицю нижче з того ж JSON.

## Tiers

| Tier | Коли | Приклади |
|---|---|---|
| **fast** | lookup, шлях, typo, health, список skills | «де CONTEXT?» |
| **standard** | типові артефакти PM | daily actions, D11, issue log, notes, акт |
| **reasoning** | судження, конфлікт джерел, honesty | EWS, QG, CR impact, escalation, charter |
| **long** | багато кроків / великий зріз систем | hydrate, start-project, weekly-rhythm, closing pack |

Якщо в запиті кілька сигналів — бери **вищий** tier.

## Що робити з результатом

| `action` | Поведінка |
|---|---|
| `stay` | Працюй у поточному чаті |
| `spawn_subagent` | Cursor: Task/subagent з `model` з JSON. Claude/VS Code: агент `pmo-fast` / `pmo-standard` / `pmo-reasoning`. Codex: один bounded task до агента з поля `agent` і моделі з `model` / `extra`; parent перевіряє та відповідає. |
| `ask_user_to_switch` | Одна коротка репліка: яку модель увімкнути + навіщо; далі не блокуй, якщо PM лишається |

Для Codex маршрутизуй лише нове змістовне PMO-завдання, не кожен follow-up, не саму розмову про маршрутизатор і не задачу субагента повторно. Якщо потрібний агент або модель недоступні, залишайся в parent, не блокуй PM.

Не викликай CLI на **кожному** дрібному follow-up у тому ж чаті — лише на нову задачу або зміну типу роботи.

## Env adapters (default slugs — прав у JSON)

| Env | fast | standard | reasoning / long |
|---|---|---|---|
| Cursor | `composer-2.5-fast` | `claude-4.6-sonnet-medium-thinking` | `claude-4.6-opus-high-thinking` |
| Claude Code / VS Code Claude | `haiku` | `sonnet` | `opus` |
| Codex | `pmo_fast` · `gpt-5.6-luna` | `pmo_standard` · `gpt-5.6-terra` | `pmo_reasoning` · `gpt-5.6-sol` high / `pmo_long` · `gpt-6-astra` high |

## Related

- Policy: `config/model-router.json`
- Cursor rule: `.cursor/rules/model-orchestrator.mdc`
- Claude/VS Code agents: `.claude/agents/pmo-*.md`
- Codex project agents: `.codex/agents/pmo_*.toml`
- `AGENTS.md` → Model orchestrator
