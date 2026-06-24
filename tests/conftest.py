"""Shared test fixtures for HandshakeLab tests."""

from pathlib import Path

import pytest

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
