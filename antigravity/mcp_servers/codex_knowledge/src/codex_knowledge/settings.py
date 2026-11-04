from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    data_root: Path = Path.home() / ".local" / "share" / "codex" / "projects"
    vault_root: Path = Path.home() / "Documents" / "Obsidian"


SETTINGS = Settings()
