"""Cross-platform OS detection and paths."""

from __future__ import annotations

import platform
import sys
from pathlib import Path


def system() -> str:
    return sys.platform


def is_linux() -> bool:
    return sys.platform.startswith("linux")


def is_macos() -> bool:
    return sys.platform == "darwin"


def is_supported() -> bool:
    return is_linux() or is_macos()


def data_dir() -> Path:
    if is_macos():
        base = Path.home() / "Library" / "Application Support" / "handshakelab"
    else:
        base = Path.home() / ".local" / "share" / "handshakelab"
    base.mkdir(parents=True, exist_ok=True)
    return base


def log_dir() -> Path:
    path = data_dir() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def captures_dir() -> Path:
    path = data_dir() / "captures"
    path.mkdir(parents=True, exist_ok=True)
    return path


def vault_db_path() -> Path:
    return data_dir() / "vault.db"


def platform_label() -> str:
    return f"{platform.system()} {platform.release()}"