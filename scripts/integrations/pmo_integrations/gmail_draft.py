"""Parse weekly-status email markdown and create Gmail drafts via Google API."""

from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).resolve().parents[3]

DEFAULT_MAIL_CONFIG = ROOT / "config" / "weekly-status-mail.json"

_URL_RE = re.compile(r"(https?://[^\s<>\]\)]+)")


@dataclass
class ParsedEmailDraft:
    subject: str
    body: str
    source_path: Optional[str] = None
    meta: dict[str, str] = field(default_factory=dict)


def _strip_md_noise(text: str) -> str:
    text = text.replace("\r\n", "\n").strip()
    # unwrap accidental markdown emphasis left in body
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    return text.strip() + "\n"


def parse_weekly_status_email_md(path: Path | str) -> ParsedEmailDraft:
    """Extract subject + body from `docs/weekly-status/{date}/email.md` (or legacy email-*.md).

    Prefers fenced ```text``` / ```email``` block. Supports UA `Тема:` or EN `Subject:`.
    """
    path = Path(path)
    raw = path.read_text(encoding="utf-8")
    meta: dict[str, str] = {}
    for m in re.finditer(
        r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|",
        raw,
        flags=re.MULTILINE,
    ):
        key = m.group(1).strip().lower()
        if key in ("поле", "---", ""):
            continue
        meta[key] = m.group(2).strip()

    fence = re.search(
        r"```(?:text|email|mail)?\s*\n(.*?)```",
        raw,
        flags=re.DOTALL | re.IGNORECASE,
    )
    block = fence.group(1).strip() if fence else raw

    subject = ""
    body_lines: list[str] = []
    lines = block.splitlines()
    for i, line in enumerate(lines):
        m = re.match(
            r"^(?:Тема|Subject|Subject line)\s*:\s*(.+)\s*$",
            line.strip(),
            flags=re.IGNORECASE,
        )
        if m and not subject:
            subject = m.group(1).strip()
            body_lines = lines[i + 1 :]
            break
    if not subject:
        # fallback: first non-empty line
        for i, line in enumerate(lines):
            if line.strip():
                subject = line.strip()
                body_lines = lines[i + 1 :]
                break

    body = _strip_md_noise("\n".join(body_lines).lstrip("\n"))
    if not subject:
        raise ValueError(f"Cannot find Тема/Subject in {path}")
    return ParsedEmailDraft(
        subject=subject,
        body=body,
        source_path=str(path),
        meta=meta,
    )


def load_mail_config(path: Optional[Path | str] = None) -> dict[str, Any]:
    cfg_path = Path(path) if path else DEFAULT_MAIL_CONFIG
    if not cfg_path.is_absolute():
        cfg_path = ROOT / cfg_path
    if not cfg_path.exists():
        return {}
    return json.loads(cfg_path.read_text(encoding="utf-8"))


def resolve_recipients(
    *,
    to: Optional[list[str]] = None,
    cc: Optional[list[str]] = None,
    config_path: Optional[Path | str] = None,
) -> tuple[list[str], list[str]]:
    cfg = load_mail_config(config_path)
    resolved_to = list(to or []) or list(cfg.get("default_to") or [])
    resolved_cc = list(cc or []) or list(cfg.get("default_cc") or [])
    if not resolved_to:
        raise ValueError(
            "No recipients: pass --to emails or set default_to in "
            "config/weekly-status-mail.json (see .example.json)"
        )
    return resolved_to, resolved_cc


def want_append_signature(
    *,
    config_path: Optional[Path | str] = None,
    cli_flag: Optional[bool] = None,
) -> bool:
    """Resolve whether to append Gmail Settings signature (default True)."""
    if cli_flag is not None:
        return bool(cli_flag)
    cfg = load_mail_config(config_path)
    if "append_gmail_signature" in cfg:
        return bool(cfg.get("append_gmail_signature"))
    return True


def plain_body_to_html(plain: str) -> str:
    """Escape plain email body and turn URLs into links; preserve line breaks."""
    text = (plain or "").replace("\r\n", "\n").strip("\n")
    if not text:
        return ""
    parts: list[str] = []
    last = 0
    for m in _URL_RE.finditer(text):
        parts.append(html.escape(text[last : m.start()]))
        url = m.group(1).rstrip(".,);]")
        # keep trailing punctuation outside the href when stripped
        trailing = m.group(1)[len(url) :]
        safe_url = html.escape(url, quote=True)
        parts.append(f'<a href="{safe_url}">{html.escape(url)}</a>')
        if trailing:
            parts.append(html.escape(trailing))
        last = m.end()
    parts.append(html.escape(text[last:]))
    inner = "".join(parts).replace("\n", "<br>\n")
    return (
        '<div style="font-family:Arial,Helvetica,sans-serif;font-size:14px;'
        f'line-height:1.45;color:#202124;">{inner}</div>'
    )


def build_email_bodies(
    plain: str,
    *,
    signature_html: str = "",
    html_override: Optional[str] = None,
) -> tuple[str, str]:
    """Return (plain, html) for multipart/alternative.

    Plain keeps a text hint that an HTML signature follows when signature is present.
    HTML includes the Gmail Settings signature as-is (already HTML).
    """
    plain_core = (plain or "").rstrip() + "\n"
    sig = (signature_html or "").strip()
    if html_override is not None:
        html_core = html_override
    else:
        html_core = plain_body_to_html(plain_core)

    if not sig:
        return plain_core, html_core

    # Strip tags for a rough plain-text signature fallback
    plain_sig = re.sub(r"<br\s*/?>", "\n", sig, flags=re.IGNORECASE)
    plain_sig = re.sub(r"</p\s*>", "\n", plain_sig, flags=re.IGNORECASE)
    plain_sig = re.sub(r"<[^>]+>", "", plain_sig)
    plain_sig = html.unescape(plain_sig).strip()
    plain_out = plain_core.rstrip() + "\n\n" + plain_sig + "\n"
    html_out = html_core + "<br>\n<br>\n" + sig
    return plain_out, html_out


def write_draft_registry(
    record: dict[str, Any],
    *,
    slug: Optional[str] = None,
) -> Path:
    out_dir = ROOT / "registry" / "google" / "gmail-drafts"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    name = slug or record.get("local_file") or "draft"
    safe = re.sub(r"[^\w.\-]+", "-", Path(str(name)).stem)[:80]
    path = out_dir / f"{stamp}-{safe}.json"
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path
