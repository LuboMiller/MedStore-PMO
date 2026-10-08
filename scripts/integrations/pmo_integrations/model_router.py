"""Environment-agnostic model orchestrator for PMO agents.

Classifies a task into fast / standard / reasoning / long, then maps the
tier to a model slug for Cursor, Claude Code, Codex, or VS Code+Claude.
Does not call any LLM — safe to run from any IDE.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "config" / "model-router.json"

TIER_RANK = {"fast": 1, "standard": 2, "reasoning": 3, "long": 4}
SKILL_RE = re.compile(r"\bpmo-[a-z0-9-]+\b", re.IGNORECASE)


def load_policy(path: Optional[Path] = None) -> dict[str, Any]:
    cfg_path = path or CONFIG_PATH
    if not cfg_path.is_file():
        raise FileNotFoundError(f"Missing model router policy: {cfg_path}")
    return json.loads(cfg_path.read_text(encoding="utf-8"))


def detect_environment(environ: Optional[dict[str, str]] = None) -> str:
    env = environ if environ is not None else os.environ
    keys = {k.upper() for k in env}
    if any(k.startswith("CURSOR_") for k in keys) or env.get("CURSOR_AGENT"):
        return "cursor"
    if env.get("CLAUDECODE") or env.get("CLAUDE_CODE") or env.get("CLAUDE_AGENT"):
        return "claude"
    if env.get("CODEX_HOME") or env.get("CODEX_CI") or env.get("CODEX_SANDBOX"):
        return "codex"
    term = (env.get("TERM_PROGRAM") or "").lower()
    if "cursor" in term:
        return "cursor"
    if env.get("VSCODE_PID") or env.get("VSCODE_INJECTION") or term == "vscode":
        return "vscode_claude"
    return "generic"


def _fold(text: str) -> str:
    return (text or "").casefold()


def _keyword_in_blob(blob: str, keyword: str) -> bool:
    needle = keyword.casefold()
    if not needle:
        return False
    # Short ASCII tokens ("qg", "ews") must not match inside longer words.
    if " " not in needle and all(ord(c) < 128 for c in needle) and len(needle) <= 4:
        return re.search(rf"\b{re.escape(needle)}\b", blob) is not None
    return needle in blob


def _hit_keywords(blob: str, keywords: list[str]) -> list[str]:
    return [kw for kw in keywords if _keyword_in_blob(blob, kw)]


def classify(
    task: str,
    *,
    policy: Optional[dict[str, Any]] = None,
    skill: Optional[str] = None,
) -> dict[str, Any]:
    pol = policy or load_policy()
    blob = _fold(task)
    skills = {m.group(0).lower() for m in SKILL_RE.finditer(task or "")}
    if skill:
        skills.add(skill.lower().strip())

    skill_tiers: dict[str, str] = pol.get("skill_tiers") or {}
    signals: dict[str, Any] = pol.get("signals") or {}
    default = pol.get("default_tier") or "standard"

    reasons: list[str] = []
    best: Optional[str] = None
    best_rank = 0

    for name in sorted(skills):
        mapped = skill_tiers.get(name)
        if not mapped:
            continue
        rank = TIER_RANK.get(mapped, 0)
        reasons.append(f"skill:{name}→{mapped}")
        if rank > best_rank:
            best, best_rank = mapped, rank

    # Higher tiers first so a mixed prompt (daily + EWS) lands on reasoning/long.
    for tier in ("long", "reasoning", "standard", "fast"):
        kws = ((signals.get(tier) or {}).get("keywords")) or []
        hits = _hit_keywords(blob, kws)
        if not hits:
            continue
        rank = TIER_RANK.get(tier, 0)
        reasons.append(f"keyword:{hits[0]}→{tier}")
        if rank > best_rank:
            best, best_rank = tier, rank

    if best is None:
        best = default
        reasons.append(f"default→{default}")
        best_rank = TIER_RANK.get(best, 2)

    confidence = 0.55
    if any(r.startswith("skill:") for r in reasons):
        confidence += 0.25
    if any(r.startswith("keyword:") for r in reasons):
        confidence += 0.15
    if len(reasons) >= 3:
        confidence += 0.05
    confidence = min(0.95, round(confidence, 2))

    return {
        "tier": best,
        "confidence": confidence,
        "reasons": reasons,
        "skills": sorted(skills),
    }


def recommend(
    task: str,
    *,
    environment: Optional[str] = None,
    skill: Optional[str] = None,
    policy: Optional[dict[str, Any]] = None,
    environ: Optional[dict[str, str]] = None,
) -> dict[str, Any]:
    pol = policy or load_policy()
    env_id = (environment or detect_environment(environ) or "generic").strip().lower()
    adapters: dict[str, Any] = pol.get("environments") or {}
    adapter = adapters.get(env_id) or adapters.get("generic") or {}
    classified = classify(task, policy=pol, skill=skill)
    tier = classified["tier"]
    models = adapter.get("models") or {}
    extra = (adapter.get("extra") or {}).get(tier) or {}
    model = models.get(tier) or models.get("standard")

    action = "spawn_subagent" if env_id == "codex" else "stay"
    if env_id != "codex" and tier in ("reasoning", "long"):
        action = "spawn_subagent"
        if env_id == "generic":
            action = "ask_user_to_switch"

    hint = {
        "fast": "Дрібна задача — лишайся на поточній / fast моделі.",
        "standard": "Типова PMO-робота — standard tier.",
        "reasoning": "Потрібне судження (EWS, QG, CR, ескалація) — opus / high-reasoning.",
        "long": "Багатокроковий оркестратор або великий зріз систем — opus / high-reasoning, краще субагент.",
    }.get(tier, "")
    if env_id == "codex":
        hint = "Делегуй один обмежений PMO-підзапит до обраного агента; parent перевіряє й відповідає."

    return {
        "environment": env_id,
        "environment_label": adapter.get("label") or env_id,
        "tier": tier,
        "model": model,
        "agent": (adapter.get("agents") or {}).get(tier),
        "extra": extra or None,
        "action": action,
        "spawn": adapter.get("spawn"),
        "hint": hint,
        "confidence": classified["confidence"],
        "reasons": classified["reasons"],
        "skills": classified["skills"],
        "all_env_models": {
            eid: (ad.get("models") or {}).get(tier)
            for eid, ad in adapters.items()
            if eid != "generic"
        },
    }


def format_recommendation(rec: dict[str, Any]) -> str:
    lines = [
        f"tier: {rec['tier']}",
        f"env: {rec['environment']} ({rec.get('environment_label')})",
        f"model: {rec.get('model')}",
        f"action: {rec.get('action')}",
        f"confidence: {rec.get('confidence')}",
    ]
    extra = rec.get("extra")
    if extra:
        lines.append(f"extra: {json.dumps(extra, ensure_ascii=False)}")
    if rec.get("spawn"):
        lines.append(f"spawn: {rec['spawn']}")
    if rec.get("agent"):
        lines.append(f"agent: {rec['agent']}")
    if rec.get("hint"):
        lines.append(f"hint: {rec['hint']}")
    for r in rec.get("reasons") or []:
        lines.append(f"- {r}")
    return "\n".join(lines) + "\n"


def policy_summary(policy: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    pol = policy or load_policy()
    return {
        "version": pol.get("version"),
        "tiers": pol.get("tiers"),
        "default_tier": pol.get("default_tier"),
        "environments": {
            eid: {
                "label": ad.get("label"),
                "models": ad.get("models"),
                "agents": ad.get("agents"),
                "spawn": ad.get("spawn"),
            }
            for eid, ad in (pol.get("environments") or {}).items()
        },
    }
