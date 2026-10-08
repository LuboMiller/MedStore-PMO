# CLAUDE.md

Primary operating manual for agents in this repo: **[AGENTS.md](./AGENTS.md)**.

At session start: read `CONTEXT.md` and ensure `knowledge/pmo-kb/` is available (`make export-pmo-kb` if missing). Skills live under `.cursor/skills/pmo-*`. Before the first substantive PMO work today, apply `.cursor/rules/daily-repo-sync-gate.mdc` (today’s Sheets hydrate + daily-actions, or explicit skip).

Model routing (this CLI, Claude Code, VS Code, Codex): `python3 scripts/integrations/cli.py models recommend --task "…"` · Cursor/Claude agents `.claude/agents/` (`haiku` / `sonnet` / `opus`) · Codex `.codex/agents/pmo_*.toml`. Policy: `config/model-router.json`.
