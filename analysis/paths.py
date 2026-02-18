"""
Centralized path resolution for ARPGBuilds.

Handles the difference between running from source and running
from a PyInstaller-bundled exe (where data dirs are read-only).
"""

import sys
from pathlib import Path


def get_base_dir() -> Path:
    """Return the base directory for read-only game data.

    PyInstaller frozen: sys._MEIPASS (temp extraction dir with data/ and builds/)
    Development:        project root (parent of analysis/)
    """
    if getattr(sys, "_MEIPASS", None):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


def get_custom_builds_dir() -> Path:
    """Return the writable directory for user-created builds.

    PyInstaller frozen: custom_builds/ next to the .exe
    Development:        custom_builds/ in project root

    The directory is NOT created here -- callers create it on first save.
    """
    if getattr(sys, "_MEIPASS", None):
        return Path(sys.executable).resolve().parent / "custom_builds"
    return Path(__file__).resolve().parent.parent / "custom_builds"
