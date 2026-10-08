#!/usr/bin/env python3
"""
roadmap_link.py — генерує shareable URL для Mermaid діаграми.

Режими:
  (default)  Mermaid Ink PNG  — працює для файлів до ~2.5 KB
  --live     mermaid.live     — інтерактивний редактор, будь-який розмір
  --kroki    kroki.io SVG     — публічний API, будь-який розмір, SVG

Використання:
  python roadmap_link.py                               # default: dashboards/roadmap.mmd → Ink
  python roadmap_link.py dashboards/roadmap.mmd --live # → mermaid.live link
  python roadmap_link.py dashboards/roadmap.mmd --kroki# → kroki.io SVG link
  python roadmap_link.py roadmap.md --live             # витягне mermaid-блок з .md
  python roadmap_link.py dashboards/roadmap.mmd --svg  # Mermaid Ink SVG
"""

import sys
import base64
import json
import re
import zlib
import argparse
from pathlib import Path


def extract_mermaid_from_md(text: str) -> str:
    match = re.search(r"```mermaid\s*\n(.*?)```", text, re.DOTALL)
    if not match:
        raise ValueError("У файлі не знайдено ```mermaid блок")
    return match.group(1).strip()


def load_code(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    return extract_mermaid_from_md(text) if path.suffix == ".md" else text.strip()


# --- Mermaid Ink ---

def ink_url(code: str, fmt: str = "img", bg: str = "white") -> str:
    encoded = base64.urlsafe_b64encode(code.encode("utf-8")).decode("ascii")
    return f"https://mermaid.ink/{fmt}/{encoded}?bgColor=!{bg}"


# --- mermaid.live ---
# URL format: https://mermaid.live/edit#pako:<base64url(pako.deflate(json_state))>
# pako.deflate() = zlib-wrapped deflate = Python zlib.compress()
# State: code (str), mermaid (JSON string), updateDiagram (bool), rough (bool)

def live_url(code: str) -> str:
    state = json.dumps({
        "code": code,
        "mermaid": json.dumps({"theme": "neutral"}),
        "updateDiagram": False,
        "rough": False,
    }, ensure_ascii=False)
    compressed = zlib.compress(state.encode("utf-8"), level=9)
    encoded = base64.urlsafe_b64encode(compressed).decode("ascii").rstrip("=")
    return f"https://mermaid.live/edit#pako:{encoded}"


# --- kroki.io ---
# URL format: https://kroki.io/mermaid/<fmt>/<base64url(zlib(code))>

def kroki_url(code: str, fmt: str = "svg") -> str:
    compressed = zlib.compress(code.encode("utf-8"), level=9)
    encoded = base64.urlsafe_b64encode(compressed).decode("ascii")
    return f"https://kroki.io/mermaid/{fmt}/{encoded}"


def copy_to_clipboard(text: str) -> None:
    try:
        import pyperclip
        pyperclip.copy(text)
        print("📋 URL скопійовано в буфер обміну")
    except ImportError:
        print("💡 pip install pyperclip — для автокопіювання в буфер")


def main():
    parser = argparse.ArgumentParser(description="Генератор URL для Mermaid діаграм")
    parser.add_argument("file", nargs="?", default="dashboards/roadmap.mmd",
                        help="Шлях до .mmd або .md файлу (default: dashboards/roadmap.mmd)")
    parser.add_argument("--live",  action="store_true", help="mermaid.live URL (рекомендовано для великих файлів)")
    parser.add_argument("--kroki", action="store_true", help="kroki.io SVG URL")
    parser.add_argument("--svg",   action="store_true", help="SVG замість PNG (тільки для Mermaid Ink)")
    parser.add_argument("--bg",    default="white",     help="Колір фону (тільки для Mermaid Ink)")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"❌ Файл не знайдено: {path}")
        sys.exit(1)

    code = load_code(path)
    size_kb = path.stat().st_size / 1024

    if args.live:
        url = live_url(code)
        label = "mermaid.live (інтерактивний)"
    elif args.kroki:
        url = kroki_url(code, fmt="svg" if args.svg else "svg")
        label = "kroki.io SVG"
    else:
        if size_kb > 2.5:
            print(f"⚠️  Файл {size_kb:.1f} KB > 2.5 KB — Mermaid Ink може обрізати діаграму.")
            print("   Рекомендовано: --live або --kroki\n")
        fmt = "svg" if args.svg else "img"
        url = ink_url(code, fmt=fmt, bg=args.bg)
        label = f"Mermaid Ink {'SVG' if args.svg else 'PNG'}"

    print(f"\n✅ Roadmap URL ({label}):\n")
    print(url)
    print()
    copy_to_clipboard(url)


if __name__ == "__main__":
    main()
