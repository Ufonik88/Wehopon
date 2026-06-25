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


def macos_major_version() -> int | None:
    """Return the macOS major version (e.g. 14 for Sonoma) or None on other OSes.

    Uses the Darwin kernel version: kernel 23 = macOS 14, kernel 24 = macOS 15,
    kernel 25 = macOS 26 (Tahoe), etc. The release field is used as fallback.
    """
    if not is_macos():
        return None
    release = platform.release()  # e.g. "25.5.0"
    try:
        return int(release.split(".")[0])
    except (ValueError, IndexError):
        return None


def is_modern_macos(min_major: int = 14) -> bool:
    """Return True if running on macOS >= min_major (default 14 = Sonoma).

    The legacy `airport` CLI was removed in macOS 14. Use this to gate
    guidance and capability detection.
    """
    v = macos_major_version()
    return v is not None and v >= min_major


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
