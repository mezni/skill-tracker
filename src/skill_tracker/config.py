"""Runtime configuration sourced from environment variables."""

from __future__ import annotations

import os
from pathlib import Path

DEFAULT_DB_FILENAME = "skill_tracker.db"


def database_path() -> Path:
    raw = os.getenv("SKILL_TRACKER_DB", DEFAULT_DB_FILENAME)
    return Path(raw).expanduser()


def static_dir() -> Path:
    override = os.getenv("SKILL_TRACKER_WEB")
    if override:
        return Path(override).expanduser()
    return Path(__file__).resolve().parents[2] / "web"
