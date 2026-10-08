#!/usr/bin/env python3
"""Obsolete one-shot converter (prompts → Cursor skills).

Skills under `.cursor/skills/pmo-*` and methodology in `knowledge/pmo-kb/`
are the source of truth. Do not re-run this script.
"""

from __future__ import annotations

import sys


def main() -> int:
    print(
        "convert-prompts-to-skills.py: obsolete.\n"
        "Edit `.cursor/skills/pmo-*` directly.\n"
        "Methodology: knowledge/pmo-kb/ (make export-pmo-kb).",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
