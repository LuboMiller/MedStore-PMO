"""Interactive / non-interactive first-run setup for the PMO pipeline.

Guides: Python deps → .env → linked repos EARLY (BA replaces docs/functional-specs when set) → health → optional KB export.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).resolve().parents[3]
ENV_PATH = ROOT / ".env"
ENV_EXAMPLE = ROOT / ".env.example"
LINKED = ROOT / "config" / "linked-repos.json"
LINKED_EXAMPLE = ROOT / "config" / "linked-repos.example.json"
STATUS_PATH = ROOT / "docs" / "_hydrate" / "SETUP_STATUS.md"
REQ_INTEGRATIONS = ROOT / "scripts" / "integrations" / "requirements.txt"
REQ_EXPORT = ROOT / "scripts" / "confluence-export" / "requirements.txt"

PLACEHOLDER_TOKEN = re.compile(
    r"^(your@email\.com|your-atlassian-api-token|YOURPROJ)?$",
    re.I,
)


@dataclass
class StepResult:
    id: str
    ok: bool
    detail: str
    skipped: bool = False


@dataclass
class WizardReport:
    steps: list[StepResult] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)

    def add(self, step_id: str, ok: bool, detail: str, *, skipped: bool = False) -> None:
        self.steps.append(StepResult(step_id, ok, detail, skipped=skipped))

    def as_dict(self) -> dict[str, Any]:
        return {
            "steps": [
                {"id": s.id, "ok": s.ok, "detail": s.detail, "skipped": s.skipped}
                for s in self.steps
            ],
            "next_actions": self.next_actions,
            "all_required_ok": all(s.ok or s.skipped for s in self.steps if s.id.startswith("req:")),
        }


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _prompt(label: str, default: str = "", *, secret: bool = False) -> str:
    hint = f" [{default}]" if default else ""
    if secret and default:
        hint = " [keep existing]"
    try:
        raw = input(f"{label}{hint}: ").strip()
    except EOFError:
        return default
    if not raw:
        return default
    return raw


def _yes(label: str, default: bool = True) -> bool:
    d = "Y/n" if default else "y/N"
    try:
        raw = input(f"{label} [{d}]: ").strip().lower()
    except EOFError:
        return default
    if not raw:
        return default
    return raw in ("y", "yes", "так", "t")


def _parse_env(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.exists():
        return data
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, _, v = s.partition("=")
        data[k.strip()] = v.strip().strip('"').strip("'")
    return data


def _is_empty_or_placeholder(value: str) -> bool:
    v = (value or "").strip()
    if not v:
        return True
    if PLACEHOLDER_TOKEN.match(v):
        return True
    if v.lower().startswith("your-") or v.lower().startswith("your@"):
        return True
    return False


def _write_env(values: dict[str, str]) -> None:
    """Merge values into .env preserving comments/order from example when creating new."""
    existing_lines: list[str] = []
    if ENV_PATH.exists():
        existing_lines = ENV_PATH.read_text(encoding="utf-8").splitlines()
    elif ENV_EXAMPLE.exists():
        existing_lines = ENV_EXAMPLE.read_text(encoding="utf-8").splitlines()

    keys_written: set[str] = set()
    out: list[str] = []
    for line in existing_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in line:
            out.append(line)
            continue
        k, _, _ = line.partition("=")
        key = k.strip()
        if key in values:
            out.append(f"{key}={values[key]}")
            keys_written.add(key)
        else:
            out.append(line)
    for k, v in values.items():
        if k not in keys_written:
            out.append(f"{k}={v}")
    ENV_PATH.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")


def ensure_env_file(*, interactive: bool) -> StepResult:
    if ENV_PATH.exists():
        return StepResult("req:env_file", True, f".env exists ({ENV_PATH})")
    if not ENV_EXAMPLE.exists():
        return StepResult("req:env_file", False, ".env.example missing")
    if interactive:
        if not _yes("Create .env from .env.example?", True):
            return StepResult("req:env_file", False, "user declined creating .env", skipped=True)
    shutil.copy(ENV_EXAMPLE, ENV_PATH)
    return StepResult("req:env_file", True, "created .env from .env.example")


def install_deps(*, optional_google: bool = False) -> StepResult:
    cmds = [
        [sys.executable, "-m", "pip", "install", "-q", "-r", str(REQ_INTEGRATIONS)],
        [sys.executable, "-m", "pip", "install", "-q", "-r", str(REQ_EXPORT)],
    ]
    if optional_google:
        cmds.append(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "-q",
                "google-api-python-client",
                "google-auth",
            ]
        )
    errors: list[str] = []
    for cmd in cmds:
        proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
        if proc.returncode != 0:
            errors.append((proc.stderr or proc.stdout or "pip failed")[:300])
    if errors:
        return StepResult("req:deps", False, "; ".join(errors))
    detail = "integrations + confluence-export"
    if optional_google:
        detail += " + google"
    return StepResult("req:deps", True, f"pip ok ({detail})")


def configure_env_interactive(env: dict[str, str]) -> dict[str, str]:
    print("\n=== Credentials (.env) ===")
    print("Atlassian API token: https://id.atlassian.com/manage-profile/security/api-tokens")
    print("Tempo token: Tempo → Settings → API integration (separate from Atlassian)\n")

    updates: dict[str, str] = {}

    def ask(key: str, label: str, *, secret: bool = False, required: bool = False) -> None:
        current = env.get(key, "")
        show_default = "" if secret and current else current
        val = _prompt(label, show_default, secret=secret)
        if secret and not val and current:
            return
        if required and _is_empty_or_placeholder(val):
            print(f"  ⚠️  {key} still empty/placeholder — fill later or re-run wizard")
        if val != current and val:
            updates[key] = val
            env[key] = val

    ask("ATLASSIAN_BASE_URL", "Atlassian base URL (no /wiki)")
    ask("ATLASSIAN_USERNAME", "Atlassian email / username")
    ask("ATLASSIAN_API_TOKEN", "Atlassian API token", secret=True, required=True)

    # Keep aliases in sync if primary set
    if updates.get("ATLASSIAN_BASE_URL") or env.get("ATLASSIAN_BASE_URL"):
        base = env.get("ATLASSIAN_BASE_URL", "")
        for k in ("CONFLUENCE_BASE_URL", "JIRA_BASE_URL"):
            if _is_empty_or_placeholder(env.get(k, "")) or env.get(k) == updates.get("ATLASSIAN_BASE_URL"):
                updates[k] = base
                env[k] = base
    if updates.get("ATLASSIAN_USERNAME") or env.get("ATLASSIAN_USERNAME"):
        user = env.get("ATLASSIAN_USERNAME", "")
        for k in ("CONFLUENCE_USERNAME", "JIRA_USERNAME"):
            updates[k] = user
            env[k] = user
    if updates.get("ATLASSIAN_API_TOKEN"):
        tok = updates["ATLASSIAN_API_TOKEN"]
        for k in ("CONFLUENCE_API_TOKEN", "JIRA_API_TOKEN"):
            updates[k] = tok
            env[k] = tok

    ask("CONFLUENCE_DEFAULT_SPACE", "Default Confluence space (PMO methodology or project)")
    ask("JIRA_PROJECT_KEY", "Jira project key (required for jira CLI)", required=True)

    if _yes("Configure Tempo now?", False):
        ask("TEMPO_API_TOKEN", "Tempo API token", secret=True)
        ask("TEMPO_BASE_URL", "Tempo base URL")

    if _yes("Configure Google Workspace (optional)?", False):
        ask("GOOGLE_APPLICATION_CREDENTIALS", "Path to service account JSON")
        ask("GOOGLE_DRIVE_FOLDER_ID", "Project Drive folder id")
        ask("GOOGLE_DELEGATED_USER", "Delegated Workspace user email (optional)")

    if _yes("Configure Fireflies.ai (optional)?", False):
        ask("FIREFLIES_API_KEY", "Fireflies API key", secret=True)
        ask("FIREFLIES_KEYWORD", "Default keyword filter (e.g. project name)")
        ask("FIREFLIES_DOWNLOAD_AUDIO", "Download audio.mp3? (1/0)")

    return updates


def configure_linked_repos_interactive() -> StepResult:
    print("\n=== Linked repos EARLY (BA / codebase) ===")
    print("Note: if BA is configured, it fully replaces docs/functional-specs/ as FS SoT.")
    if not _yes("Add a BA or codebase repository link now?", False):
        return StepResult("opt:linked_repos", True, "skipped", skipped=True)

    data = {"ba_repos": [], "codebase_repos": []}
    if LINKED.exists():
        try:
            data = json.loads(LINKED.read_text(encoding="utf-8"))
            data.setdefault("ba_repos", [])
            data.setdefault("codebase_repos", [])
        except json.JSONDecodeError:
            pass

    kind = _prompt("Kind (ba/codebase)", "ba").lower()
    if kind not in ("ba", "codebase"):
        kind = "ba"
    repo_id = _prompt("Repo id (slug)", "project-ba")
    url = _prompt("Git URL (or leave empty)", "")
    path = _prompt("Local path (or leave empty)", "")
    ref = _prompt("Git ref", "main")
    entry = {
        "id": repo_id,
        "kind": kind,
        "url": url or None,
        "path": path or None,
        "ref": ref,
        "sync": "bidirectional" if kind == "ba" else "pull",
        "local_mirror": f"knowledge/{'ba' if kind == 'ba' else 'codebases'}/{repo_id}",
    }
    key = "ba_repos" if kind == "ba" else "codebase_repos"
    # replace same id
    data[key] = [e for e in data[key] if e.get("id") != repo_id]
    data[key].append(entry)
    LINKED.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return StepResult("opt:linked_repos", True, f"added {kind} id={repo_id}")


def run_health_step() -> StepResult:
    from .health import run_health

    results = run_health()
    failed = [r for r in results if not r.ok and r.required]
    lines = [f"{'OK' if r.ok else 'FAIL'} {r.name}: {r.detail}" for r in results]
    if failed:
        return StepResult("req:health", False, "; ".join(lines))
    return StepResult("req:health", True, "; ".join(lines))


def maybe_export_kb(*, interactive: bool, non_interactive_flag: bool) -> StepResult:
    kb = ROOT / "knowledge" / "pmo-kb"
    has_kb = kb.exists() and any(kb.iterdir())
    if has_kb:
        return StepResult("opt:export_kb", True, "knowledge/pmo-kb already present", skipped=True)
    do_export = non_interactive_flag
    if interactive:
        do_export = _yes("Export Devlight PMO knowledge base now? (make export-pmo-kb)", True)
    if not do_export:
        return StepResult("opt:export_kb", True, "skipped — run make export-pmo-kb later", skipped=True)
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts/confluence-export/export_pmo.py"), "--space", "PMO"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return StepResult(
            "opt:export_kb",
            False,
            (proc.stderr or proc.stdout or "export failed")[:400],
        )
    return StepResult("opt:export_kb", True, "exported knowledge/pmo-kb")


def write_status(report: WizardReport) -> Path:
    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# Setup status — {_now()}",
        "",
        "| Step | OK | Detail |",
        "|---|---|---|",
    ]
    for s in report.steps:
        mark = "skip" if s.skipped else ("✅" if s.ok else "❌")
        detail = s.detail.replace("|", "\\|")
        lines.append(f"| `{s.id}` | {mark} | {detail} |")
    lines += ["", "## Next", ""]
    for a in report.next_actions:
        lines.append(f"- {a}")
    lines += [
        "",
        "Playbook: `docs/pm-playbook.md` · Re-run: `make setup` / `python3 scripts/integrations/cli.py setup wizard`",
        "",
    ]
    STATUS_PATH.write_text("\n".join(lines), encoding="utf-8")
    return STATUS_PATH


def diagnose() -> dict[str, Any]:
    """Non-mutating checklist for agents / `setup status`."""
    env = _parse_env(ENV_PATH) if ENV_PATH.exists() else {}
    checks = {
        "python": f"{sys.version_info.major}.{sys.version_info.minor}",
        "env_file": ENV_PATH.exists(),
        "atlassian_token": not _is_empty_or_placeholder(
            env.get("ATLASSIAN_API_TOKEN") or env.get("CONFLUENCE_API_TOKEN") or ""
        ),
        "atlassian_user": not _is_empty_or_placeholder(
            env.get("ATLASSIAN_USERNAME") or env.get("CONFLUENCE_USERNAME") or ""
        ),
        "jira_project_key": not _is_empty_or_placeholder(env.get("JIRA_PROJECT_KEY", "")),
        "tempo_token": not _is_empty_or_placeholder(env.get("TEMPO_API_TOKEN", "")),
        "google_creds": not _is_empty_or_placeholder(env.get("GOOGLE_APPLICATION_CREDENTIALS", "")),
        "knowledge_pmo_kb": (ROOT / "knowledge" / "pmo-kb").exists()
        and any((ROOT / "knowledge" / "pmo-kb").glob("*")),
        "linked_repos_configured": False,
        "context_filled": False,
    }
    if LINKED.exists():
        try:
            data = json.loads(LINKED.read_text(encoding="utf-8"))
            checks["linked_repos_configured"] = bool(data.get("ba_repos") or data.get("codebase_repos"))
        except json.JSONDecodeError:
            pass
    ctx = ROOT / "CONTEXT.md"
    if ctx.exists():
        text = ctx.read_text(encoding="utf-8")
        checks["context_filled"] = "{{PROJECT_NAME}}" not in text

    missing = []
    if not checks["env_file"]:
        missing.append("Create .env (make setup)")
    if not checks["atlassian_token"] or not checks["atlassian_user"]:
        missing.append("Set ATLASSIAN_USERNAME + ATLASSIAN_API_TOKEN")
    if not checks["jira_project_key"]:
        missing.append("Set JIRA_PROJECT_KEY (for jira CLI / hydrate)")
    if not checks["knowledge_pmo_kb"]:
        missing.append("make export-pmo-kb")
    if not checks["context_filled"]:
        missing.append("Fill CONTEXT.md")

    return {"checks": checks, "missing": missing, "hint": "python3 scripts/integrations/cli.py setup wizard"}


def run_wizard(
    *,
    interactive: bool = True,
    install_google: bool = False,
    export_kb: bool = False,
    skip_env_prompts: bool = False,
) -> WizardReport:
    report = WizardReport()
    print(f"PMO pipeline setup wizard — {ROOT}\n")

    # 1 deps
    if interactive and not install_google:
        install_google = _yes("Install optional Google API packages?", False)
    step = install_deps(optional_google=install_google)
    report.add(step.id, step.ok, step.detail, skipped=step.skipped)
    print(f"[{'OK' if step.ok else 'FAIL'}] deps: {step.detail}")

    # 2 env file
    step = ensure_env_file(interactive=interactive)
    report.add(step.id, step.ok, step.detail, skipped=step.skipped)
    print(f"[{'OK' if step.ok else 'FAIL'}] env file: {step.detail}")

    # 3 env values
    env = _parse_env(ENV_PATH) if ENV_PATH.exists() else {}
    if interactive and not skip_env_prompts and ENV_PATH.exists():
        updates = configure_env_interactive(env)
        if updates:
            _write_env({**env, **updates})
            report.add("req:env_values", True, f"updated keys: {', '.join(sorted(updates))}")
            print(f"[OK] env values: updated {len(updates)} key(s)")
        else:
            report.add("req:env_values", True, "no changes")
            print("[OK] env values: unchanged")
    else:
        # validate placeholders
        need = []
        if _is_empty_or_placeholder(env.get("ATLASSIAN_API_TOKEN") or env.get("CONFLUENCE_API_TOKEN") or ""):
            need.append("ATLASSIAN_API_TOKEN")
        if _is_empty_or_placeholder(env.get("ATLASSIAN_USERNAME") or env.get("CONFLUENCE_USERNAME") or ""):
            need.append("ATLASSIAN_USERNAME")
        if need:
            report.add("req:env_values", False, f"missing/placeholder: {', '.join(need)}")
            print(f"[FAIL] env values: {need}")
        else:
            report.add("req:env_values", True, "required Atlassian keys present")
            print("[OK] env values: Atlassian keys present")

    # 4 linked repos
    if interactive:
        step = configure_linked_repos_interactive()
        report.add(step.id, step.ok, step.detail, skipped=step.skipped)
        print(f"[{'skip' if step.skipped else 'OK'}] linked repos: {step.detail}")
    else:
        report.add("opt:linked_repos", True, "non-interactive — edit config/linked-repos.json", skipped=True)

    # 5 health
    # reload env into process for health
    if ENV_PATH.exists():
        from dotenv import load_dotenv

        load_dotenv(ENV_PATH, override=True)
    try:
        step = run_health_step()
    except Exception as e:  # noqa: BLE001
        step = StepResult("req:health", False, str(e))
    report.add(step.id, step.ok, step.detail, skipped=step.skipped)
    print(f"[{'OK' if step.ok else 'FAIL'}] health: {step.detail[:200]}")

    # 6 export KB
    step = maybe_export_kb(interactive=interactive, non_interactive_flag=export_kb)
    report.add(step.id, step.ok, step.detail, skipped=step.skipped)
    print(f"[{'skip' if step.skipped else ('OK' if step.ok else 'FAIL')}] kb: {step.detail}")

    # next actions
    diag = diagnose()
    report.next_actions = list(diag["missing"]) or [
        "Read docs/pm-playbook.md",
        "Run pmo-start-project or pmo-hydrate-project",
    ]
    if not any(s.id == "opt:linked_repos" and not s.skipped for s in report.steps):
        if not diag["checks"].get("linked_repos_configured"):
            report.next_actions.append("Optional: configure config/linked-repos.json + make repos-pull")

    path = write_status(report)
    print(f"\nStatus written → {path.relative_to(ROOT)}")
    print("Next:")
    for a in report.next_actions:
        print(f"  - {a}")
    return report
