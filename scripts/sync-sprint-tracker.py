#!/usr/bin/env python3
"""
sync-sprint-tracker.py
Regenerates dashboards/sprint-tracker.md from GitHub milestone data + historical velocity.
Run via: make sync-tracker
"""

import os
import subprocess
import json
import sys
import re
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
OUTPUT = ROOT_DIR / "dashboards" / "sprint-tracker.md"
# Optional: GitHub milestones repo (owner/name). Empty = skip live fetch; use FACT_SP only.
REPO = os.environ.get("GITHUB_SPRINT_REPO", "").strip()
TOTAL_SP = int(os.environ.get("SPRINT_TOTAL_SP", "920"))
PLAN_SP = int(os.environ.get("SPRINT_PLAN_SP", "45"))


def project_name() -> str:
    ctx = ROOT_DIR / "CONTEXT.md"
    if not ctx.exists():
        return "проєкт"
    text = ctx.read_text(encoding="utf-8")
    m = re.search(r"\|\s*\*\*Назва проєкту\*\*\s*\|\s*([^|]+)\|", text)
    return m.group(1).strip() if m else "проєкт"

# ── Velocity per sprint (UPDATE this dict when a sprint closes) ──────────────
# Key = sprint number, Value = actual SP delivered
# Add new entry after each sprint retrospective, then re-run make sync-tracker
FACT_SP = {
    1:  44,
    2:  48,
    3:  46,
    4:  41,
    5:  43,
    6:  47,
    7:  44,
    8:  46,
    9:  38,   # Sprint 9: replanning (example — replace with project facts)
    10: 42,
    11: 46,
    12: 45,
    13: 44,
    # 14: add after Sprint 14 retrospective
}

# ── Sprint dates ──────────────────────────────────────────────────────────────
SPRINT_DATES = {
    1:  "02.01–15.01.2026",  2:  "16.01–29.01.2026",
    3:  "30.01–12.02.2026",  4:  "13.02–26.02.2026",
    5:  "27.02–12.03.2026",  6:  "13.03–26.03.2026",
    7:  "27.03–09.04.2026",  8:  "10.04–23.04.2026",
    9:  "24.04–07.05.2026",  10: "08.05–21.05.2026",
    11: "22.05–04.06.2026",  12: "05.06–18.06.2026",
    13: "19.06–02.07.2026",  14: "03.07–16.07.2026",
    15: "17.07–30.07.2026",  16: "31.07–13.08.2026",
    17: "14.08–27.08.2026",  18: "28.08–10.09.2026",
    19: "11.09–24.09.2026",  20: "25.09–08.10.2026",
}

# ── Phase lookup ──────────────────────────────────────────────────────────────
def get_phase(s: int) -> str:
    if s <= 2:  return "Discovery & Architecture"
    if s <= 4:  return "Design & Planning"
    if s == 9:  return "Build ⚠️ Replanning"
    if s <= 15: return "Build"
    if s <= 17: return "Testing & Stabilization"
    if s == 18: return "Soft Launch UA"
    return "EU Launch Poland"

# ── GitHub data ───────────────────────────────────────────────────────────────
def fetch_milestones() -> dict:
    if not REPO:
        print(
            "ℹ️  GITHUB_SPRINT_REPO unset — building tracker from FACT_SP only "
            "(prefer Jira sync via pmo-jira-ops for live delivery).",
            file=sys.stderr,
        )
        return {}
    try:
        result = subprocess.run(
            ["gh", "api", f"repos/{REPO}/milestones?state=all&per_page=100"],
            capture_output=True, text=True, check=True
        )
        return {m["title"]: m for m in json.loads(result.stdout)}
    except Exception as e:
        print(f"⚠️  Could not fetch milestones: {e}", file=sys.stderr)
        return {}

def detect_current_sprint(milestones: dict) -> int:
    """Current sprint = lowest-numbered open sprint that has at least one issue."""
    for s in range(1, 21):
        ms = milestones.get(f"Sprint {s}", {})
        if ms.get("state") == "open":
            if ms.get("open_issues", 0) + ms.get("closed_issues", 0) > 0:
                return s
    # Fallback: first open milestone regardless of issue count
    for s in range(1, 21):
        if milestones.get(f"Sprint {s}", {}).get("state") == "open":
            return s
    return 14  # hard fallback

# ── Build table ───────────────────────────────────────────────────────────────
def build_rows(milestones: dict, current: int) -> list:
    rows = []
    cum_sp = 0

    for s in range(1, 21):
        ms    = milestones.get(f"Sprint {s}", {})
        open_i   = ms.get("open_issues", 0)
        closed_i = ms.get("closed_issues", 0)
        total_i  = open_i + closed_i
        ms_state = ms.get("state", "")

        issues_col = f"{closed_i}/{total_i}" if total_i > 0 else "—"

        fact = FACT_SP.get(s)
        if fact is not None:
            cum_sp  += fact
            fact_col = str(fact)
            cum_col  = str(cum_sp)
            rem_col  = str(TOTAL_SP - cum_sp)
        else:
            fact_col = "—"
            cum_col  = "—"
            rem_col  = "—"

        if ms_state == "closed":
            status = "✅" if open_i == 0 else "✅ ⚠️"
        elif s == current:
            status = "🔄 Активний"
        else:
            status = "⏳"

        phase = get_phase(s)
        dates = SPRINT_DATES.get(s, "—")

        if s == current:
            rows.append(
                f"| **Sprint {s}** | **{dates}** | **{phase}** "
                f"| **{issues_col}** | **{fact_col}** | **{cum_col}** | **{rem_col}** | **{status}** |"
            )
        else:
            rows.append(
                f"| Sprint {s} | {dates} | {phase} "
                f"| {issues_col} | {fact_col} | {cum_col} | {rem_col} | {status} |"
            )
    return rows

# ── Summary stats ─────────────────────────────────────────────────────────────
def build_summary(milestones: dict, current: int) -> list:
    done_sp    = sum(FACT_SP.values())
    rem_sp     = TOTAL_SP - done_sp
    n_done     = max(FACT_SP.keys()) if FACT_SP else 0
    avg_v      = round(done_sp / n_done, 1) if n_done else PLAN_SP
    forecast   = round(rem_sp / avg_v, 1) if avg_v else "?"
    sprints_left = 20 - current + 1
    gap_sp     = max(0, round(rem_sp - sprints_left * PLAN_SP))

    cur_ms     = milestones.get(f"Sprint {current}", {})
    cur_open   = cur_ms.get("open_issues", "—")
    cur_closed = cur_ms.get("closed_issues", "—")
    if isinstance(cur_open, int) and isinstance(cur_closed, int):
        cur_total = cur_open + cur_closed
        cur_pct   = f"{round(cur_closed / cur_total * 100)}%" if cur_total > 0 else "0%"
        cur_col   = f"{cur_closed}/{cur_total} issues закрито ({cur_pct})"
    else:
        cur_col = "—"

    return [
        f"**Підсумок (Sprint 1–{n_done} завершено):**",
        "",
        "| Метрика | Значення |",
        "|---|---|",
        f"| Виконано SP | {done_sp} / {TOTAL_SP} ({round(done_sp/TOTAL_SP*100)}%) |",
        f"| Середня velocity (факт) | {avg_v} SP |",
        f"| Залишок SP | {rem_sp} SP |",
        f"| Поточний спринт | Sprint {current} — {cur_col} |",
        f"| Прогноз за поточною velocity | {rem_sp} / {avg_v} = **~{forecast} спринтів** |",
        f"| ⚠️ Дефіцит | **~{gap_sp} SP** поза планом ({sprints_left} спр. × {PLAN_SP} = {sprints_left * PLAN_SP} SP доступно) |",
        "",
        "> Sprint 9: нижча velocity через replanning — оновлюй коментар під факти проєкту.",
    ]

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    name = project_name()
    print(f"🔄 Building sprint tracker for {name}...", file=sys.stderr)
    milestones = fetch_milestones()
    current    = detect_current_sprint(milestones)
    rows       = build_rows(milestones, current)
    summary    = build_summary(milestones, current)

    done_sp = sum(FACT_SP.values())
    source = f"GitHub `{REPO}` + FACT_SP" if REPO else "FACT_SP (локально; Jira — через registry/pmo-jira-ops)"

    lines = [
        f"# Sprint Tracker — {name}",
        f"**Velocity ціль:** {PLAN_SP} SP / спринт | **Загальний обсяг:** {TOTAL_SP} SP | "
        f"**Поточний спринт:** Sprint {current} 🔄",
        "",
        f"> Генерується: `make sync-tracker` | Джерело: {source} · `scripts/sync-sprint-tracker.py`",
        "",
        "---",
        "",
        "| Спринт | Дати | Фаза | Issues | SP Факт | Накоп. SP | Залишок SP | Статус |",
        "|---|---|---|---|---|---|---|---|",
    ] + rows + [
        "",
        "---",
        "",
    ] + summary

    output_text = "\n".join(lines) + "\n"
    OUTPUT.write_text(output_text, encoding="utf-8")
    print(
        f"✅ sprint-tracker.md updated — Sprint {current} active | "
        f"{done_sp}/{TOTAL_SP} SP done",
        file=sys.stderr
    )

if __name__ == "__main__":
    main()
