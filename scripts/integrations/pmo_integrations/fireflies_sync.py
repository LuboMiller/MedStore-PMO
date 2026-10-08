"""Sync Fireflies meetings into docs/meeting-notes/ + registry/fireflies/."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .config import ROOT, Config, load_config
from .fireflies import FirefliesClient
from .http import ApiError

NOTES_DIR = ROOT / "docs" / "meeting-notes"
REGISTRY_DIR = ROOT / "registry" / "fireflies"
REGISTRY_INDEX = REGISTRY_DIR / "index.json"
REGISTRY_ITEMS = REGISTRY_DIR / "transcripts"


def _slugify(text: str, *, max_len: int = 60) -> str:
    text = (text or "meeting").strip().lower()
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return (text or "meeting")[:max_len]


def _ms_to_iso_date(ms: Any) -> str:
    try:
        n = float(ms)
        # Fireflies `date` is often epoch ms
        if n > 1e12:
            n = n / 1000.0
        dt = datetime.fromtimestamp(n, tz=timezone.utc)
        return dt.strftime("%Y-%m-%d")
    except (TypeError, ValueError, OSError):
        return "unknown-date"


def _fmt_ts(seconds: Any) -> str:
    try:
        s = float(seconds or 0)
    except (TypeError, ValueError):
        return "00:00"
    m, sec = divmod(int(s), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h:02d}:{m:02d}:{sec:02d}"
    return f"{m:02d}:{sec:02d}"


def _meeting_base_name(tr: dict[str, Any]) -> str:
    date = (tr.get("dateString") or "")[:10]
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
        date = _ms_to_iso_date(tr.get("date"))
    return f"{date}-{_slugify(tr.get('title') or 'meeting')}"


def _folder_transcript_id(folder: Path) -> Optional[str]:
    meta_path = folder / "fireflies-meta.json"
    if not meta_path.is_file():
        return None
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    transcript_id = meta.get("id")
    return str(transcript_id) if transcript_id else None


def meeting_folder_name(tr: dict[str, Any], *, out_root: Path = NOTES_DIR) -> str:
    """Return a stable readable folder name, suffixing only real name collisions."""
    base = _meeting_base_name(tr)
    transcript_id = str(tr.get("id") or "")

    # Transcript ID is the identity key. Reuse a legacy readable folder (or an
    # already-suffixed collision folder) instead of downloading the same meeting
    # into a second directory after naming rules change.
    matches: list[Path] = []
    if transcript_id and out_root.is_dir():
        for folder in out_root.iterdir():
            if folder.is_dir() and _folder_transcript_id(folder) == transcript_id:
                matches.append(folder)
    if matches:
        exact_base = out_root / base
        if exact_base in matches:
            return exact_base.name
        return min(matches, key=lambda folder: (len(folder.name), folder.name)).name

    base_folder = out_root / base
    if not base_folder.exists():
        return base

    # A different meeting already owns the readable date/title path.
    suffix = transcript_id[-8:].lower() if transcript_id else "unknown"
    candidate = f"{base}-{suffix}"
    candidate_folder = out_root / candidate
    if not candidate_folder.exists() or _folder_transcript_id(candidate_folder) == transcript_id:
        return candidate

    # Extremely rare last-eight-character collision: fall back to the full ID.
    full_suffix = transcript_id.lower() if transcript_id else "unknown-id"
    return f"{base}-{full_suffix}"


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            if isinstance(item, str):
                out.append(item)
            elif item is not None:
                out.append(str(item))
        return out
    if isinstance(value, str):
        # Fireflies sometimes returns markdown/bullet blob
        lines = [ln.strip(" -\t") for ln in value.splitlines() if ln.strip()]
        return lines or [value]
    return [str(value)]


def render_transcript_md(tr: dict[str, Any]) -> str:
    title = tr.get("title") or "Meeting"
    date = (tr.get("dateString") or "")[:10] or _ms_to_iso_date(tr.get("date"))
    duration = tr.get("duration")
    dur_s = f"{duration} min" if duration is not None else "—"
    participants = tr.get("participants") or []
    if isinstance(participants, str):
        participants = [participants]
    speakers = [s.get("name") for s in (tr.get("speakers") or []) if s.get("name")]

    lines = [
        f"# {title}",
        "",
        f"- **Date:** {date}",
        f"- **Duration:** {dur_s}",
        f"- **Host:** {tr.get('host_email') or '—'}",
        f"- **Organizer:** {tr.get('organizer_email') or '—'}",
        f"- **Fireflies ID:** `{tr.get('id')}`",
        f"- **Transcript URL:** {tr.get('transcript_url') or '—'}",
        f"- **Meeting link:** {tr.get('meeting_link') or '—'}",
        "",
        "## Participants",
        "",
    ]
    if participants:
        for p in participants:
            lines.append(f"- {p}")
    else:
        lines.append("- —")
    lines.extend(["", "## Speakers", ""])
    if speakers:
        for s in speakers:
            lines.append(f"- {s}")
    else:
        lines.append("- —")
    lines.extend(["", "## Transcript", ""])

    sentences = tr.get("sentences") or []
    if not sentences:
        lines.append("_No sentences returned by Fireflies API._")
    else:
        for sent in sentences:
            speaker = sent.get("speaker_name") or "Unknown"
            text = (sent.get("raw_text") or sent.get("text") or "").strip()
            ts = _fmt_ts(sent.get("start_time"))
            lines.append(f"**[{ts}] {speaker}:** {text}")
            lines.append("")

    lines.append("_Source: Fireflies.ai — raw export, do not edit; use structured notes via pmo-extract-meeting-notes._")
    lines.append("")
    return "\n".join(lines)


def render_summary_md(tr: dict[str, Any]) -> str:
    title = tr.get("title") or "Meeting"
    date = (tr.get("dateString") or "")[:10] or _ms_to_iso_date(tr.get("date"))
    summary = tr.get("summary") or {}

    lines = [
        f"# Summary — {title}",
        "",
        f"- **Date:** {date}",
        f"- **Fireflies ID:** `{tr.get('id')}`",
        f"- **Meeting type:** {summary.get('meeting_type') or '—'}",
        f"- **Transcript URL:** {tr.get('transcript_url') or '—'}",
        "",
    ]

    overview = summary.get("overview") or summary.get("short_overview") or summary.get("short_summary") or summary.get("gist")
    if overview:
        lines.extend(["## Overview", "", str(overview).strip(), ""])

    gist = summary.get("bullet_gist") or summary.get("shorthand_bullet")
    for label, key in (
        ("Bullet gist", "bullet_gist"),
        ("Shorthand", "shorthand_bullet"),
        ("Outline", "outline"),
    ):
        val = summary.get(key)
        items = _as_list(val)
        if items:
            lines.extend([f"## {label}", ""])
            for item in items:
                lines.append(f"- {item}" if not str(item).startswith("-") else str(item))
            lines.append("")

    actions = _as_list(summary.get("action_items"))
    if actions:
        lines.extend(["## Action items", ""])
        for a in actions:
            lines.append(f"- {a}" if not str(a).startswith("-") else str(a))
        lines.append("")

    topics = _as_list(summary.get("topics_discussed"))
    if topics:
        lines.extend(["## Topics discussed", ""])
        for t in topics:
            lines.append(f"- {t}")
        lines.append("")

    keywords = _as_list(summary.get("keywords"))
    if keywords:
        lines.extend(["## Keywords", "", ", ".join(keywords), ""])

    chapters = summary.get("transcript_chapters")
    if chapters:
        lines.extend(["## Chapters", ""])
        if isinstance(chapters, list):
            for ch in chapters:
                if isinstance(ch, dict):
                    lines.append(f"- {ch.get('title') or ch.get('name') or ch}")
                else:
                    lines.append(f"- {ch}")
        else:
            lines.append(str(chapters))
        lines.append("")

    if not overview and not actions and not topics and not gist:
        lines.extend(["_No AI summary fields returned (meeting may still be processing)._", ""])

    lines.append("_Source: Fireflies.ai summary export._")
    lines.append("")
    return "\n".join(lines)


def _load_index() -> dict[str, Any]:
    if REGISTRY_INDEX.exists():
        return json.loads(REGISTRY_INDEX.read_text(encoding="utf-8"))
    return {"version": 1, "transcripts": {}, "last_sync": None}


def _save_index(index: dict[str, Any]) -> None:
    REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
    REGISTRY_ITEMS.mkdir(parents=True, exist_ok=True)
    REGISTRY_INDEX.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_registry_item(tr: dict[str, Any], folder: Path, files: dict[str, Any]) -> Path:
    REGISTRY_ITEMS.mkdir(parents=True, exist_ok=True)
    path = REGISTRY_ITEMS / f"{tr['id']}.json"
    payload = {
        "id": tr.get("id"),
        "title": tr.get("title"),
        "date": tr.get("date"),
        "dateString": tr.get("dateString"),
        "duration": tr.get("duration"),
        "host_email": tr.get("host_email"),
        "organizer_email": tr.get("organizer_email"),
        "transcript_url": tr.get("transcript_url"),
        "folder": str(folder.relative_to(ROOT)),
        "files": files,
        "synced_at": datetime.now(timezone.utc).isoformat(),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def pull_transcript(
    client: FirefliesClient,
    transcript_id: str,
    *,
    out_root: Path = NOTES_DIR,
    download_audio: bool = True,
    force: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Fetch one meeting → transcript_raw.md + summary.md + audio.mp3."""
    tr = client.get_transcript(transcript_id)
    folder = out_root / meeting_folder_name(tr, out_root=out_root)
    report: dict[str, Any] = {
        "id": transcript_id,
        "title": tr.get("title"),
        "folder": str(folder.relative_to(ROOT)) if folder.is_relative_to(ROOT) else str(folder),
    }

    transcript_path = folder / "transcript_raw.md"
    summary_path = folder / "summary.md"
    audio_path = folder / "audio.mp3"
    meta_path = folder / "fireflies-meta.json"

    if folder.exists() and meta_path.exists() and not force:
        report["skipped"] = True
        report["reason"] = "already synced (use --force to overwrite)"
        return report

    if dry_run:
        report["dry_run"] = True
        report["would_write"] = [
            str(transcript_path.relative_to(ROOT)),
            str(summary_path.relative_to(ROOT)),
        ]
        if download_audio and tr.get("audio_url"):
            report["would_write"].append(str(audio_path.relative_to(ROOT)))
        return report

    folder.mkdir(parents=True, exist_ok=True)
    transcript_path.write_text(render_transcript_md(tr), encoding="utf-8")
    summary_path.write_text(render_summary_md(tr), encoding="utf-8")

    files: dict[str, Any] = {
        "transcript_raw": str(transcript_path.relative_to(ROOT)),
        "summary": str(summary_path.relative_to(ROOT)),
    }

    audio_url = tr.get("audio_url")
    if download_audio:
        if audio_url:
            try:
                size = client.download_audio(audio_url, audio_path)
                files["audio"] = str(audio_path.relative_to(ROOT))
                report["audio_bytes"] = size
            except ApiError as e:
                report["audio_error"] = str(e)
        else:
            report["audio_error"] = "no audio_url (Pro+ plan or recording unavailable)"

    meta = {
        "id": tr.get("id"),
        "title": tr.get("title"),
        "date": tr.get("date"),
        "dateString": tr.get("dateString"),
        "duration": tr.get("duration"),
        "transcript_url": tr.get("transcript_url"),
        "meeting_link": tr.get("meeting_link"),
        "files": files,
        "synced_at": datetime.now(timezone.utc).isoformat(),
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    files["meta"] = str(meta_path.relative_to(ROOT))

    reg_path = _write_registry_item(tr, folder, files)
    index = _load_index()
    index.setdefault("transcripts", {})[transcript_id] = {
        "title": tr.get("title"),
        "folder": str(folder.relative_to(ROOT)),
        "registry": str(reg_path.relative_to(ROOT)),
        "synced_at": meta["synced_at"],
    }
    index["last_sync"] = meta["synced_at"]
    _save_index(index)

    report["files"] = files
    report["ok"] = True
    return report


def sync_pull(
    cfg: Optional[Config] = None,
    *,
    keyword: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    limit: int = 50,
    download_audio: Optional[bool] = None,
    force: bool = False,
    dry_run: bool = False,
    mine: bool = False,
) -> dict[str, Any]:
    cfg = cfg or load_config(require=("fireflies",))
    client = FirefliesClient.from_config(cfg)
    kw = keyword if keyword is not None else (cfg.fireflies_keyword or None)
    audio = cfg.fireflies_download_audio if download_audio is None else download_audio
    if from_date is None:
        from_date = cfg.fireflies_from_date or None

    listed = client.list_transcripts(
        limit=limit,
        keyword=kw or None,
        keyword_scope=cfg.fireflies_keyword_scope or "title",
        from_date=from_date,
        to_date=to_date,
        mine=True if mine else None,
    )

    results = []
    for item in listed:
        tid = item.get("id")
        if not tid:
            continue
        try:
            results.append(
                pull_transcript(
                    client,
                    tid,
                    download_audio=audio,
                    force=force,
                    dry_run=dry_run,
                )
            )
        except ApiError as e:
            results.append({"id": tid, "title": item.get("title"), "error": str(e)})

    return {
        "keyword": kw,
        "from_date": from_date,
        "to_date": to_date,
        "listed": len(listed),
        "results": results,
        "pulled": sum(1 for r in results if r.get("ok")),
        "skipped": sum(1 for r in results if r.get("skipped")),
        "errors": sum(1 for r in results if r.get("error") or r.get("audio_error")),
    }
