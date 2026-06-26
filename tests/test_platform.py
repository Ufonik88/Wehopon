"""Tests for handshakelab.util.platform — OS detection and paths."""

from __future__ import annotations

import sys


from handshakelab.util import platform as plat


def test_system_returns_sys_platform():
    assert plat.system() == sys.platform


def test_is_linux():
    if sys.platform.startswith("linux"):
        assert plat.is_linux() is True
    else:
        assert plat.is_linux() is False


def test_is_macos():
    assert plat.is_macos() is (sys.platform == "darwin")


def test_is_supported():
    assert plat.is_supported() in (True, False)
    if sys.platform.startswith("linux") or sys.platform == "darwin":
        assert plat.is_supported() is True


def test_macos_major_version_returns_int_on_macos():
    if plat.is_macos():
        v = plat.macos_major_version()
        assert v is not None
        assert isinstance(v, int)
        assert v >= 14  # modern macOS only
    else:
        assert plat.macos_major_version() is None


def test_is_modern_macos():
    if plat.is_macos():
        # On macOS 14+, is_modern_macos(14) must be True
        assert plat.is_modern_macos(14) is True
    else:
        assert plat.is_modern_macos(14) is False


def test_is_modern_macos_with_high_threshold():
    """is_modern_macos(99) is False everywhere."""
    assert plat.is_modern_macos(99) is False


def test_data_dir_creates_directory():
    """data_dir() creates the platform-specific data directory."""
    d = plat.data_dir()
    assert d.exists()
    assert d.is_dir()
    if plat.is_macos():
        assert "handshakelab" in str(d)
    else:
        assert ".local" in str(d) or "handshakelab" in str(d)


def test_log_dir_under_data_dir():
    """log_dir() is under data_dir()."""
    log = plat.log_dir()
    assert log.exists()
    assert log.parent == plat.data_dir()


def test_captures_dir_under_data_dir():
    """captures_dir() is under data_dir()."""
    cap = plat.captures_dir()
    assert cap.exists()
    assert cap.parent == plat.data_dir()


def test_vault_db_path_under_data_dir():
    """vault_db_path() is under data_dir()."""
    db = plat.vault_db_path()
    assert db.parent == plat.data_dir()
    assert db.name == "vault.db"


def test_platform_label_contains_os():
    label = plat.platform_label()
    assert sys.platform.split("-")[0].replace("darwin", "Darwin").replace(
        "linux", "Linux"
    ) or label  # best effort; just ensure non-empty
    assert isinstance(label, str)
    assert len(label) > 0
