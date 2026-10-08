"""Named Google Drive directories for a PMO project.

Config file: `config/google-directories.json` (copy from `.example.json`).
Each entry has a stable `key` used by CLI `--dir KEY`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "config" / "google-directories.json"
EXAMPLE_PATH = ROOT / "config" / "google-directories.example.json"


@dataclass(frozen=True)
class GoogleDirectory:
    key: str
    label: str
    folder_id: str
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "label": self.label,
            "folder_id": self.folder_id,
            "description": self.description,
        }


@dataclass(frozen=True)
class GoogleDirectoriesConfig:
    default: str
    directories: list[GoogleDirectory]

    def get(self, key: Optional[str] = None) -> GoogleDirectory:
        k = key or self.default
        for d in self.directories:
            if d.key == k:
                if not d.folder_id or d.folder_id.startswith("REPLACE"):
                    raise ValueError(
                        f"Directory '{k}' has no real folder_id — edit {CONFIG_PATH}"
                    )
                return d
        known = ", ".join(d.key for d in self.directories) or "(none)"
        raise KeyError(f"Unknown Google directory key '{k}'. Known: {known}")

    def resolve_folder_id(
        self, *, dir_key: Optional[str] = None, folder_id: Optional[str] = None
    ) -> str:
        """Prefer explicit folder_id; else named dir; else error."""
        if folder_id:
            return folder_id
        return self.get(dir_key).folder_id


def load_google_directories(*, required: bool = False) -> Optional[GoogleDirectoriesConfig]:
    path = CONFIG_PATH if CONFIG_PATH.exists() else None
    if path is None:
        if required:
            raise FileNotFoundError(
                f"Missing {CONFIG_PATH}. Copy from {EXAMPLE_PATH.name} and fill folder_id values."
            )
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    dirs = [
        GoogleDirectory(
            key=str(item["key"]).strip(),
            label=str(item.get("label") or item["key"]).strip(),
            folder_id=str(item.get("folder_id") or "").strip(),
            description=str(item.get("description") or "").strip(),
        )
        for item in data.get("directories") or []
        if item.get("key")
    ]
    default = str(data.get("default") or (dirs[0].key if dirs else "")).strip()
    return GoogleDirectoriesConfig(default=default, directories=dirs)


def ensure_example_copied() -> Path:
    """If local config missing, copy example so PM can edit folder IDs."""
    if CONFIG_PATH.exists():
        return CONFIG_PATH
    if not EXAMPLE_PATH.exists():
        raise FileNotFoundError(f"Missing example: {EXAMPLE_PATH}")
    CONFIG_PATH.write_text(EXAMPLE_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    return CONFIG_PATH
