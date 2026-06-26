"""Shared test fixtures for HandshakeLab tests."""

import sys
from pathlib import Path

import pytest

# Ensure `handshakelab` is importable even if the editable install's .pth
# file has been clobbered (see TEST_CHECKLIST issue O3). Prepend src/ to
# sys.path so tests can run after `git pull` or any `pyproject.toml` change
# that resets the editable install.
_SRC = Path(__file__).resolve().parent.parent / "src"
if _SRC.exists() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    """Return path to test fixtures directory."""
    return FIXTURES_DIR


@pytest.fixture
def test_config_path(fixtures_dir: Path) -> Path:
    """Return path to test configuration file."""
    config_path = fixtures_dir / "test_config.toml"
    if not config_path.exists():
        pytest.skip("Test config fixture not found. See fixtures/README.md")
    return config_path


@pytest.fixture
def sample_pcap_path(fixtures_dir: Path) -> Path:
    """Return path to sample PCAP file with handshake."""
    pcap_path = fixtures_dir / "handshake.pcapng"
    if not pcap_path.exists():
        pytest.skip("Sample PCAP fixture not found. See fixtures/README.md")
    return pcap_path


@pytest.fixture
def empty_pcap_path(fixtures_dir: Path) -> Path:
    """Return path to empty PCAP file for negative tests."""
    pcap_path = fixtures_dir / "empty.pcapng"
    if not pcap_path.exists():
        pytest.skip("Empty PCAP fixture not found. See fixtures/README.md")
    return pcap_path
