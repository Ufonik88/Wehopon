"""Tests for handshakelab.capture — capture orchestration."""

from __future__ import annotations

import struct
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from handshakelab.capture import (
    CaptureError,
    CaptureResult,
    _tool_versions,
    capture_handshake,
    import_capture,
)
from handshakelab.config import LabConfig
from handshakelab.eapol import CaptureAnalysis
from handshakelab.sniffer import SnifferError, SnifferResult


def _make_pcapng_with_eapol(tmp_path: Path) -> Path:
    """Create a minimal pcapng that analyze_capture will treat as having EAPOL."""
    pcap = tmp_path / "fake.pcapng"
    # 24-byte pcap header + a fake packet that contains 0x888e somewhere
    pcap.write_bytes(
        b"\xd4\xc3\xb2\xa1"  # little-endian magic
        + struct.pack("<HHIIII", 2, 4, 0, 0, 65535, 1)
        + struct.pack("<IIII", 0, 0, 30, 30)
        + b"\x00" * 12
        + b"\x88\x8e"
        + b"\x00" * 16
    )
    return pcap


def test_capture_error_raised_without_root():
    """capture_handshake raises CaptureError if not running as root."""
    cfg = LabConfig(path=Path("/tmp/lab.toml"), require_authorization=False)
    with patch("handshakelab.capture.has_root", return_value=False):
        with pytest.raises(CaptureError, match="root"):
            capture_handshake(iface="en0", ssid="LAB", config=cfg)


def test_capture_error_on_authorization_failure():
    """capture_handshake raises if target is unauthorized."""
    from handshakelab.legal import AuthorizationError

    cfg = LabConfig(path=Path("/tmp/lab.toml"), require_authorization=True)
    with (
        patch("handshakelab.capture.has_root", return_value=True),
        patch(
            "handshakelab.capture.assert_authorized",
            side_effect=AuthorizationError("denied"),
        ),
    ):
        with pytest.raises(AuthorizationError, match="denied"):
            capture_handshake(iface="en0", ssid="LAB", config=cfg)


def test_capture_raises_on_no_channel(tmp_path, monkeypatch):
    """capture_handshake raises if channel can't be determined."""
    monkeypatch.setattr(
        "handshakelab.util.platform.vault_db_path", lambda: tmp_path / "vault.db"
    )
    monkeypatch.setattr(
        "handshakelab.util.platform.captures_dir", lambda: tmp_path / "captures"
    )
    cfg = LabConfig(path=tmp_path / "lab.toml", require_authorization=False)

    with (
        patch("handshakelab.capture.has_root", return_value=True),
        patch("handshakelab.capture.scan_networks", return_value=[]),
    ):
        with pytest.raises(CaptureError, match="Could not determine channel"):
            capture_handshake(iface="en0", ssid="LAB", config=cfg)


def test_capture_uses_scanned_bssid_and_channel(tmp_path, monkeypatch):
    """capture_handshake fills in bssid/channel from scan if not provided."""
    monkeypatch.setattr(
        "handshakelab.util.platform.vault_db_path", lambda: tmp_path / "vault.db"
    )
    monkeypatch.setattr(
        "handshakelab.util.platform.captures_dir", lambda: tmp_path / "captures"
    )
    cfg = LabConfig(path=tmp_path / "lab.toml", require_authorization=False)

    fake_pcap = _make_pcapng_with_eapol(tmp_path)

    fake_sniff = SnifferResult(
        capture_path=fake_pcap,
        backend="tcpdump",
        analysis=CaptureAnalysis(100, 4, 50, 50, True, fake_pcap.stat().st_size),
        duration_sec=5,
    )

    from handshakelab.util.wifi import Network

    scanned = [Network(ssid="LAB", bssid="AA:BB:CC:DD:EE:FF", channel=6, rssi=-50, security="WPA2")]

    with (
        patch("handshakelab.capture.has_root", return_value=True),
        patch("handshakelab.capture.scan_networks", return_value=scanned),
        patch("handshakelab.capture.passive_capture", return_value=fake_sniff),
        patch("handshakelab.capture.has_eapol_handshake", return_value=True),
    ):
        result = capture_handshake(iface="en0", ssid="LAB", config=cfg)

    assert result.bssid == "AA:BB:CC:DD:EE:FF"
    assert result.channel == 6
    assert result.backend == "tcpdump"


def test_capture_raises_on_sniffer_error(tmp_path, monkeypatch):
    """SnifferError from passive_capture becomes CaptureError."""
    monkeypatch.setattr(
        "handshakelab.util.platform.vault_db_path", lambda: tmp_path / "vault.db"
    )
    monkeypatch.setattr(
        "handshakelab.util.platform.captures_dir", lambda: tmp_path / "captures"
    )
    cfg = LabConfig(path=tmp_path / "lab.toml", require_authorization=False)

    with (
        patch("handshakelab.capture.has_root", return_value=True),
        patch("handshakelab.capture.scan_networks", return_value=[]),
        patch("handshakelab.capture.passive_capture", side_effect=SnifferError("no backend")),
    ):
        with pytest.raises(CaptureError, match="no backend"):
            capture_handshake(
                iface="en0", ssid="LAB", config=cfg, bssid="AA:BB:CC:DD:EE:FF", channel=6
            )


def test_capture_raises_on_empty_capture(tmp_path, monkeypatch):
    """Empty capture file raises CaptureError."""
    monkeypatch.setattr(
        "handshakelab.util.platform.vault_db_path", lambda: tmp_path / "vault.db"
    )
    monkeypatch.setattr(
        "handshakelab.util.platform.captures_dir", lambda: tmp_path / "captures"
    )
    cfg = LabConfig(path=tmp_path / "lab.toml", require_authorization=False)

    empty_pcap = tmp_path / "empty.pcapng"
    empty_pcap.write_bytes(b"")

    fake_sniff = SnifferResult(
        capture_path=empty_pcap,
        backend="tcpdump",
        analysis=CaptureAnalysis(0, 0, 0, 0, False, 0),
        duration_sec=1,
    )

    with (
        patch("handshakelab.capture.has_root", return_value=True),
        patch("handshakelab.capture.passive_capture", return_value=fake_sniff),
    ):
        with pytest.raises(CaptureError, match="Empty capture"):
            capture_handshake(
                iface="en0",
                ssid="LAB",
                config=cfg,
                bssid="AA:BB:CC:DD:EE:FF",
                channel=6,
            )


def test_capture_raises_on_no_handshake(tmp_path, monkeypatch):
    """Capture with packets but no handshake raises CaptureError."""
    monkeypatch.setattr(
        "handshakelab.util.platform.vault_db_path", lambda: tmp_path / "vault.db"
    )
    monkeypatch.setattr(
        "handshakelab.util.platform.captures_dir", lambda: tmp_path / "captures"
    )
    cfg = LabConfig(path=tmp_path / "lab.toml", require_authorization=False)

    # Write a non-empty pcap without EAPOL
    pcap = tmp_path / "no_eapol.pcapng"
    pcap.write_bytes(b"\x00" * 1024)

    fake_sniff = SnifferResult(
        capture_path=pcap,
        backend="tcpdump",
        analysis=CaptureAnalysis(50, 0, 0, 0, False, 1024),
        duration_sec=1,
    )

    with (
        patch("handshakelab.capture.has_root", return_value=True),
        patch("handshakelab.capture.passive_capture", return_value=fake_sniff),
    ):
        with pytest.raises(CaptureError, match="no WPA handshake"):
            capture_handshake(
                iface="en0",
                ssid="LAB",
                config=cfg,
                bssid="AA:BB:CC:DD:EE:FF",
                channel=6,
            )


def test_capture_result_dataclass():
    """CaptureResult dataclass has expected fields."""
    from pathlib import Path

    r = CaptureResult(
        run_id="x",
        run_dir=Path("/tmp/r"),
        capture_path=Path("/tmp/r/c.pcapng"),
        ssid="L",
        bssid="A:B:C:D:E:F",
        channel=6,
        backend="tcpdump",
        analysis=CaptureAnalysis(0, 0, 0, 0, False, 0),
    )
    assert r.run_id == "x"
    assert r.ssid == "L"


def test_import_capture_missing_file(tmp_path, monkeypatch):
    """import_capture raises if source file doesn't exist."""
    monkeypatch.setattr(
        "handshakelab.util.platform.vault_db_path", lambda: tmp_path / "vault.db"
    )
    monkeypatch.setattr(
        "handshakelab.util.platform.captures_dir", lambda: tmp_path / "captures"
    )
    cfg = LabConfig(path=tmp_path / "lab.toml", require_authorization=False)
    with pytest.raises(CaptureError, match="File not found"):
        import_capture(
            source=tmp_path / "missing.pcapng",
            ssid="LAB",
            config=cfg,
        )


def test_import_capture_no_eapol(tmp_path, monkeypatch):
    """import_capture raises if imported file has no EAPOL."""
    monkeypatch.setattr(
        "handshakelab.util.platform.vault_db_path", lambda: tmp_path / "vault.db"
    )
    monkeypatch.setattr(
        "handshakelab.util.platform.captures_dir", lambda: tmp_path / "captures"
    )
    cfg = LabConfig(path=tmp_path / "lab.toml", require_authorization=False)

    # File exists but has no EAPOL
    src = tmp_path / "no_eapol.pcapng"
    src.write_bytes(b"\x00" * 1024)

    with pytest.raises(CaptureError, match="no detectable EAPOL"):
        import_capture(source=src, ssid="LAB", config=cfg)


def test_import_capture_success(tmp_path, monkeypatch):
    """import_capture copies file and registers run."""
    monkeypatch.setattr(
        "handshakelab.util.platform.vault_db_path", lambda: tmp_path / "vault.db"
    )
    monkeypatch.setattr(
        "handshakelab.util.platform.captures_dir", lambda: tmp_path / "captures"
    )
    cfg = LabConfig(path=tmp_path / "lab.toml", require_authorization=False)

    src = _make_pcapng_with_eapol(tmp_path)

    with patch("handshakelab.capture.has_eapol_handshake", return_value=True):
        result = import_capture(
            source=src,
            ssid="LAB",
            config=cfg,
            bssid="AA:BB:CC:DD:EE:FF",
            channel=6,
        )
    assert result.run_id is not None
    assert result.capture_path.exists()
    assert result.backend == "import"
    assert result.ssid == "LAB"


def test_tool_versions_with_no_tools(monkeypatch):
    """_tool_versions returns empty dict when no tools are on PATH."""
    monkeypatch.setattr("handshakelab.capture.which", lambda name: None)
    versions = _tool_versions()
    assert versions == {}


def test_tool_versions_with_some_tools(monkeypatch):
    """_tool_versions collects available tool versions."""
    fake_result = MagicMock()
    fake_result.stdout = "v7.1.2\n"
    fake_result.stderr = ""
    fake_result.ok = True

    def fake_which(name):
        return "/opt/homebrew/bin/" + name if name in ("hashcat", "tcpdump") else None

    def fake_run(argv, check=False):
        # Return a version string
        return MagicMock(stdout="v7.1.2\n", stderr="", ok=True)

    monkeypatch.setattr("handshakelab.capture.which", fake_which)
    monkeypatch.setattr("handshakelab.capture.run", fake_run)

    versions = _tool_versions()
    assert "hashcat" in versions
    assert "tcpdump" in versions
    assert versions["hashcat"] == "v7.1.2"
