"""Optional linked BA and codebase repositories for PMO context / sync.

Config: config/linked-repos.json (see linked-repos.example.json).
Mirrors: knowledge/ba/{id}/ , knowledge/codebases/{id}/ (gitignored).

BA repos are a maintained dependency of the PMO pipeline:
  pull → work in mirror (FS SoT; follow BA CLAUDE/prompts/skills) → push.
Discover reports agent_mode (cursor-skills | claude-prompts-rules | hybrid | docs-only).

Codebases are pull/context-only by default.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Optional

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "config" / "linked-repos.json"
BA_ROOT = ROOT / "knowledge" / "ba"
CODE_ROOT = ROOT / "knowledge" / "codebases"

Kind = Literal["ba", "codebase"]
SyncMode = Literal["pull", "push", "bidirectional", "none"]


# Default BA agent surfaces (CLAUDE + prompts/rules, or Cursor skills).
BA_DEFAULT_AGENT_ENTRYPOINTS = (
    "AGENTS.md",
    "CONTEXT.md",
    "CLAUDE.md",
    "CLAUDE-PROJECT.md",
    "README.md",
)
BA_DEFAULT_PROMPTS_GLOBS = (
    "docs/ba/prompts/**/*.md",
    "docs/ba/prompts/**/*.mdc",
)
BA_DEFAULT_RULES_GLOBS = (
    "docs/ba/rules/**/*",
    ".cursor/rules/**/*",
)
BA_DEFAULT_ARTIFACT_HINTS = (
    "docs/ba/artifacts/specs",
    "docs/ba/artifacts",
    "docs/ba",
)


@dataclass
class LinkedRepo:
    id: str
    kind: Kind
    url: Optional[str]
    path: Optional[str]
    ref: str
    local_mirror: str
    sync: SyncMode
    context_files: list[str]
    skills_glob: str
    prompts_globs: list[str]
    rules_globs: list[str]
    agent_entrypoints: list[str]
    include: list[str]
    exclude: list[str]
    purpose: str
    notes: str
    raw: dict[str, Any]

    @property
    def mirror_path(self) -> Path:
        p = Path(self.local_mirror)
        return p if p.is_absolute() else ROOT / p

    @property
    def source_path(self) -> Optional[Path]:
        if not self.path:
            return None
        p = Path(self.path).expanduser()
        return p if p.is_absolute() else (ROOT / p).resolve()


def ba_fs_sot_active(path: Path = CONFIG_PATH) -> bool:
    """True when at least one BA linked repo is configured — FS must not use docs/functional-specs/."""
    return any(r.kind == "ba" for r in load_linked_repos(path))


def ba_fs_sot_mirrors(path: Path = CONFIG_PATH) -> list[Path]:
    """Mirror roots for BA FS SoT (may be empty)."""
    return [r.mirror_path for r in load_linked_repos(path) if r.kind == "ba"]


def load_linked_repos(path: Path = CONFIG_PATH) -> list[LinkedRepo]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    out: list[LinkedRepo] = []
    for kind, key in (("ba", "ba_repos"), ("codebase", "codebase_repos")):
        for item in data.get(key) or []:
            if not isinstance(item, dict) or not item.get("id"):
                continue
            default_mirror = (
                f"knowledge/ba/{item['id']}"
                if kind == "ba"
                else f"knowledge/codebases/{item['id']}"
            )
            default_context = (
                list(BA_DEFAULT_AGENT_ENTRYPOINTS) + ["docs/**"]
                if kind == "ba"
                else ["CONTEXT.md", "AGENTS.md", "README.md"]
            )
            prompts = item.get("prompts_globs") or item.get("prompts_glob")
            rules = item.get("rules_globs") or item.get("rules_glob")
            if isinstance(prompts, str):
                prompts = [prompts]
            if isinstance(rules, str):
                rules = [rules]
            entrypoints = item.get("agent_entrypoints")
            if isinstance(entrypoints, str):
                entrypoints = [entrypoints]
            out.append(
                LinkedRepo(
                    id=str(item["id"]),
                    kind=kind,  # type: ignore[arg-type]
                    url=item.get("url") or None,
                    path=item.get("path") or None,
                    ref=str(item.get("ref") or "main"),
                    local_mirror=str(item.get("local_mirror") or default_mirror),
                    sync=str(item.get("sync") or ("bidirectional" if kind == "ba" else "pull")),  # type: ignore[arg-type]
                    context_files=list(item.get("context_files") or default_context),
                    skills_glob=str(item.get("skills_glob") or ".cursor/skills/**/SKILL.md"),
                    prompts_globs=list(prompts or (BA_DEFAULT_PROMPTS_GLOBS if kind == "ba" else [])),
                    rules_globs=list(rules or (BA_DEFAULT_RULES_GLOBS if kind == "ba" else [])),
                    agent_entrypoints=list(
                        entrypoints or (BA_DEFAULT_AGENT_ENTRYPOINTS if kind == "ba" else [])
                    ),
                    include=list(item.get("include") or []),
                    exclude=list(item.get("exclude") or ["node_modules", "dist", ".git"]),
                    purpose=str(item.get("purpose") or ("ba-docs" if kind == "ba" else "context-only")),
                    notes=str(item.get("notes") or ""),
                    raw=item,
                )
            )
    return out


def _glob_files(base: Path, patterns: list[str], *, limit: int = 200) -> list[str]:
    found: list[str] = []
    for pattern in patterns:
        if not pattern:
            continue
        if "**" in pattern or "*" in pattern:
            found.extend(str(p.relative_to(base)) for p in base.glob(pattern) if p.is_file())
        else:
            p = base / pattern
            if p.is_file():
                found.append(pattern)
            elif p.is_dir():
                found.extend(
                    str(x.relative_to(base))
                    for x in p.rglob("*")
                    if x.is_file() and x.suffix.lower() in {".md", ".mdc", ".txt"}
                )
    # Prefer stable order; drop binaries / noise already filtered by suffix for dirs
    return sorted(set(found))[:limit]


def _run(cmd: list[str], *, cwd: Optional[Path] = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        text=True,
        capture_output=True,
        check=False,
    )


def _git_ok(path: Path) -> bool:
    return (path / ".git").exists() or (path / ".git").is_file()


def list_repos() -> list[dict[str, Any]]:
    rows = []
    for r in load_linked_repos():
        mirror = r.mirror_path
        src = r.source_path
        rows.append(
            {
                "id": r.id,
                "kind": r.kind,
                "sync": r.sync,
                "url": r.url,
                "path": str(src) if src else None,
                "path_exists": bool(src and src.exists()),
                "ref": r.ref,
                "local_mirror": str(mirror.relative_to(ROOT)) if mirror.is_relative_to(ROOT) else str(mirror),
                "mirror_exists": mirror.exists(),
                "purpose": r.purpose,
                "notes": r.notes,
            }
        )
    return rows


def status_repo(repo: LinkedRepo) -> dict[str, Any]:
    mirror = repo.mirror_path
    info: dict[str, Any] = {
        "id": repo.id,
        "kind": repo.kind,
        "mirror": str(mirror),
        "exists": mirror.exists(),
    }
    if mirror.exists() and _git_ok(mirror):
        head = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=mirror)
        sha = _run(["git", "rev-parse", "--short", "HEAD"], cwd=mirror)
        dirty = _run(["git", "status", "--porcelain"], cwd=mirror)
        info["branch"] = (head.stdout or "").strip()
        info["sha"] = (sha.stdout or "").strip()
        info["dirty"] = bool((dirty.stdout or "").strip())
    elif mirror.exists():
        info["note"] = "mirror exists but is not a git checkout (path copy)"
    return info


def discover_context(repo: LinkedRepo) -> dict[str, Any]:
    """List context files / BA agent surfaces available in the mirror (or source path).

    BA repos may expose either Cursor skills (``.cursor/skills/**/SKILL.md``) or a
    CLAUDE.md + ``docs/ba/prompts`` + rules layout. Discover reports both.
    """
    base = repo.mirror_path if repo.mirror_path.exists() else repo.source_path
    result: dict[str, Any] = {"id": repo.id, "kind": repo.kind, "base": str(base) if base else None}
    if not base or not base.exists():
        result["error"] = "mirror/source missing — run repos pull first"
        return result

    found_context = _glob_files(base, repo.context_files, limit=200)

    skills: list[str] = []
    if repo.skills_glob:
        skills = _glob_files(base, [repo.skills_glob], limit=200)

    prompts: list[str] = []
    rules: list[str] = []
    if repo.kind == "ba":
        prompts = _glob_files(base, repo.prompts_globs, limit=200)
        rules = _glob_files(base, repo.rules_globs, limit=200)

    entrypoints_present: list[str] = []
    for name in repo.agent_entrypoints or BA_DEFAULT_AGENT_ENTRYPOINTS:
        if (base / name).is_file():
            entrypoints_present.append(name)

    has_claude = (base / "CLAUDE.md").is_file() or (base / "CLAUDE-PROJECT.md").is_file()
    has_agents = (base / "AGENTS.md").is_file()
    has_skills = bool(skills)
    has_prompts = bool(prompts)

    if has_skills and (has_claude or has_prompts):
        agent_mode = "hybrid"
    elif has_skills or has_agents:
        agent_mode = "cursor-skills"
    elif has_claude or has_prompts:
        agent_mode = "claude-prompts-rules"
    else:
        agent_mode = "docs-only"

    # Ordered reading list for PMO agents working BA as a dependency
    read_order: list[str] = []
    for name in ("CLAUDE.md", "CLAUDE-PROJECT.md", "AGENTS.md", "CONTEXT.md"):
        if name in entrypoints_present:
            read_order.append(name)
    if prompts:
        read_order.append(f"prompts ({len(prompts)} files under docs/ba/prompts/)")
    if rules:
        read_order.append(f"rules ({len(rules)} files)")
    if skills:
        read_order.append(f"skills ({len(skills)} SKILL.md)")

    artifact_roots = [
        hint for hint in BA_DEFAULT_ARTIFACT_HINTS if (base / hint).exists()
    ]

    result["context_files"] = found_context
    result["skills"] = skills
    result["prompts"] = prompts
    result["rules"] = rules
    result["agent_entrypoints"] = entrypoints_present
    result["agent_mode"] = agent_mode
    result["read_order"] = read_order
    result["artifact_roots"] = artifact_roots
    result["agents_md"] = has_agents
    result["context_md"] = (base / "CONTEXT.md").is_file()
    result["claude_md"] = (base / "CLAUDE.md").is_file()
    result["claude_project_md"] = (base / "CLAUDE-PROJECT.md").is_file()
    result["pipeline_hint"] = (
        "BA is a maintained dependency of this PMO repo: pull → edit SoT in mirror "
        "(follow BA read_order / prompts) → repos push. Do not duplicate FS into "
        "docs/functional-specs/."
        if repo.kind == "ba"
        else "Codebase mirror is context-only unless sync explicitly allows push."
    )
    return result


def pull_repo(repo: LinkedRepo, *, shallow: bool = True, dry_run: bool = False) -> dict[str, Any]:
    if repo.sync == "none":
        return {"id": repo.id, "skipped": True, "reason": "sync=none"}
    if repo.sync == "push":
        return {"id": repo.id, "skipped": True, "reason": "sync=push only — use push"}

    mirror = repo.mirror_path
    report: dict[str, Any] = {"id": repo.id, "kind": repo.kind, "action": "pull", "mirror": str(mirror)}

    # Prefer existing local path: rsync/copy selected files OR use as git worktree source
    src = repo.source_path
    if src and src.exists():
        report["source"] = str(src)
        if dry_run:
            report["dry_run"] = f"would sync from local path {src} → {mirror}"
            return report
        mirror.parent.mkdir(parents=True, exist_ok=True)
        if _git_ok(src):
            # clone/fetch via local path
            if not mirror.exists():
                cmd = ["git", "clone"]
                if shallow:
                    cmd += ["--depth", "1"]
                if repo.ref:
                    cmd += ["--branch", repo.ref]
                cmd += [str(src), str(mirror)]
                proc = _run(cmd)
                report["clone"] = {"code": proc.returncode, "stderr": (proc.stderr or "")[:500]}
            else:
                proc = _run(["git", "fetch", "--all"], cwd=mirror)
                _run(["git", "checkout", repo.ref], cwd=mirror)
                pull = _run(["git", "pull", "--ff-only"], cwd=mirror)
                report["pull"] = {
                    "fetch": proc.returncode,
                    "pull": pull.returncode,
                    "stderr": ((pull.stderr or proc.stderr) or "")[:500],
                }
        else:
            # plain directory copy (respect exclude lightly)
            if mirror.exists():
                shutil.rmtree(mirror)
            shutil.copytree(
                src,
                mirror,
                ignore=shutil.ignore_patterns(*repo.exclude) if repo.exclude else None,
            )
            report["copied"] = True
        report["discover"] = discover_context(repo)
        return report

    if not repo.url:
        return {
            "id": repo.id,
            "error": "no url and no existing path — set url or path in linked-repos.json",
        }

    if dry_run:
        report["dry_run"] = f"would clone/pull {repo.url}@{repo.ref} → {mirror}"
        return report

    mirror.parent.mkdir(parents=True, exist_ok=True)
    if not mirror.exists():
        cmd = ["git", "clone"]
        if shallow:
            cmd += ["--depth", "1"]
        if repo.ref:
            cmd += ["--branch", repo.ref]
        cmd += [repo.url, str(mirror)]
        proc = _run(cmd)
        report["clone"] = {"code": proc.returncode, "stderr": (proc.stderr or "")[:800]}
        if proc.returncode != 0:
            report["error"] = "clone failed"
            return report
    else:
        if not _git_ok(mirror):
            report["error"] = "mirror exists but is not a git repo"
            return report
        _run(["git", "remote", "set-url", "origin", repo.url], cwd=mirror)
        fetch = _run(["git", "fetch", "origin", repo.ref], cwd=mirror)
        checkout = _run(["git", "checkout", repo.ref], cwd=mirror)
        pull = _run(["git", "pull", "--ff-only", "origin", repo.ref], cwd=mirror)
        report["pull"] = {
            "fetch": fetch.returncode,
            "checkout": checkout.returncode,
            "pull": pull.returncode,
            "stderr": ((pull.stderr or fetch.stderr) or "")[:800],
        }
        if pull.returncode != 0:
            report["error"] = "pull failed (maybe local dirty commits — resolve manually)"

    report["discover"] = discover_context(repo)
    report["status"] = status_repo(repo)
    return report


def push_repo(repo: LinkedRepo, *, message: str = "", dry_run: bool = False) -> dict[str, Any]:
    """Push BA mirror changes upstream. Codebases refused unless sync explicitly allows push."""
    if repo.kind == "codebase" and repo.sync not in ("push", "bidirectional"):
        return {
            "id": repo.id,
            "error": "codebase is context-only — set sync to bidirectional/push only if intentional",
        }
    if repo.sync not in ("push", "bidirectional"):
        return {"id": repo.id, "error": f"sync={repo.sync} does not allow push"}

    mirror = repo.mirror_path
    if not mirror.exists() or not _git_ok(mirror):
        return {"id": repo.id, "error": "mirror missing or not a git repo — pull first"}

    dirty = _run(["git", "status", "--porcelain"], cwd=mirror)
    if not (dirty.stdout or "").strip():
        return {"id": repo.id, "skipped": True, "reason": "nothing to commit"}

    if dry_run:
        return {
            "id": repo.id,
            "dry_run": True,
            "dirty_files": (dirty.stdout or "").strip().splitlines()[:50],
        }

    msg = message or f"PMO pipeline sync from {ROOT.name}"
    add = _run(["git", "add", "-A"], cwd=mirror)
    commit = _run(["git", "commit", "-m", msg], cwd=mirror)
    push = _run(["git", "push", "origin", "HEAD"], cwd=mirror)
    return {
        "id": repo.id,
        "add": add.returncode,
        "commit": commit.returncode,
        "commit_stderr": (commit.stderr or "")[:400],
        "push": push.returncode,
        "push_stderr": (push.stderr or "")[:800],
        "error": None if push.returncode == 0 else "push failed",
    }


def pull_all(*, kind: Optional[Kind] = None, repo_id: Optional[str] = None, dry_run: bool = False) -> dict[str, Any]:
    repos = load_linked_repos()
    if kind:
        repos = [r for r in repos if r.kind == kind]
    if repo_id:
        repos = [r for r in repos if r.id == repo_id]
    results = [pull_repo(r, dry_run=dry_run) for r in repos]
    return {"count": len(results), "results": results}


def get_repo(repo_id: str) -> Optional[LinkedRepo]:
    for r in load_linked_repos():
        if r.id == repo_id:
            return r
    return None
