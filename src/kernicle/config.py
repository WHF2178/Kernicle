"""Configuration and filesystem layout.

Sprint 1 creates archives under:
  ~/.kernicle/archives

No extra features (zipping/encryption/background) are implemented in Sprint 1.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class KerniclePaths:
    """Resolved directories for Kernicle."""

    home_dir: Path
    archives_dir: Path


def get_paths() -> KerniclePaths:
    """Return resolved Kernicle directories and ensure archives folder exists."""

    home_dir = Path.home() / ".kernicle"
    archives_dir = home_dir / "archives"
    archives_dir.mkdir(parents=True, exist_ok=True)
    return KerniclePaths(home_dir=home_dir, archives_dir=archives_dir)
