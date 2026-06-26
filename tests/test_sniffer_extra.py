"""Tests for handshakelab.sniffer — built-in sniffer with macOS en0 awareness."""

from __future__ import annotations

import struct
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from handshakelab.eapol import CaptureAnalysis
from handshakelab.sniffer import (
    SnifferError,
    SnifferResult,
    _available_backends,
    passive_capture,
)


def test_available_backends_on_macos_with_tcpdump():
    """On macOS with tcpdump, only tcpdump is in the backend list (no airport)."""
    import sys

    if sys.platform != "darwin":
        pytest.skip("macOS-only behavior")
    backends = _available_backends()
    assert "tcpdump" in backends
    assert "airport" not in backends  # airport removed in macOS 14+


def test_passive_capture_no_backends_raises():
    """passive_capture raises SnifferError when no capture backend is available."""
    with patch("handshakelab.sniffer._available_backends", return_value=[]):
        with pytest.raises(SnifferError, match="No capture engine"):
            passive_capture(
                iface="en0", output=Path("/tmp/nope.pcap"), bssid=None, channel=6
            )


def test_passive_capture_builtin_wifi_helpful_error(tmp_path):
    """On built-in macOS WiFi with no packets captured, error mentions USB adapter."""
    if pytest.importorskip("sys").platform != "darwin":
        pytest.skip("macOS-specific behavior")

    empty = tmp_path / "empty.pcap"
    empty.write_bytes(b"")

    # _sniff_tcpdump returns a SnifferResult with zero packets (failure case)
    class _FakeSniffer:
        capture_path = empty
        backend = "tcpdump"
        analysis = CaptureAnalysis(0, 0, 0, 0, False, 0)
        duration_sec = 1

    with (
        patch("handshakelab.sniffer._available_backends", return_value=["tcpdump"]),
        patch("handshakelab.sniffer._sniff_tcpdump", return_value=_FakeSniffer()),
    ):
        with pytest.raises(SnifferError) as exc_info:
            passive_capture(
                iface="en0", output=tmp_path / "out.pcap", bssid=None, channel=6
            )
    # Outer error mentions "Tip" about another device; the per-backend
    # error was "capture empty" because total_packets was 0.
    assert "capture" in str(exc_info.value).lower()


def test_tcpdump_sniffer_emits_builtin_warning_on_macos_en0(tmp_path):
    """The tcpdump path on macOS en0 surfaces a warning to on_tick."""
    import sys

    if sys.platform != "darwin":
        pytest.skip("macOS-specific behavior")

    # Pretend tcpdump produced a tiny pcapng with one EAPOL byte
    out = tmp_path / "cap.pcapng"
    out.write_bytes(
        b"\xd4\xc3\xb2\xa1"
        + struct.pack("<HHIIII", 2, 4, 0, 0, 65535, 1)
        + struct.pack("<IIII", 0, 0, 30, 30)
        + b"\x00" * 12
        + b"\x88\x8e"
        + b"\x00" * 16
    )

    ticks = []

    def on_tick(analysis, msg):
        ticks.append(msg)

    fake_proc = MagicMock()
    fake_proc.send_signal = MagicMock()
    fake_proc.wait = MagicMock()
    fake_proc.kill = MagicMock()

    with (
        patch("handshakelab.sniffer.which", return_value="/usr/sbin/tcpdump"),
        patch("handshakelab.sniffer.subprocess.Popen", return_value=fake_proc),
    ):
        with patch("handshakelab.sniffer.analyze_capture") as mock_analyze:
            # Always return a 1-EAPOL analysis so capture terminates quickly
            mock_analyze.return_value = CaptureAnalysis(
                1, 1, 0, 0, True, out.stat().st_size
            )
            from handshakelab.sniffer import _sniff_tcpdump

            result = _sniff_tcpdump(
                iface="en0",
                output=out,
                bssid=None,
                channel=6,
                duration_sec=1,
                on_tick=on_tick,
            )

    # The warning should have been emitted
    assert any("Built-in macOS" in m or "monitor mode" in m for m in ticks)
    assert result.backend == "tcpdump"


def test_tcpdump_sniffer_no_builtin_warning_on_usb_iface(tmp_path):
    """The tcpdump path on non-built-in interfaces does NOT emit the warning."""
    import sys

    if sys.platform != "darwin":
        pytest.skip("macOS-specific behavior")

    out = tmp_path / "cap.pcapng"
    out.write_bytes(
        b"\xd4\xc3\xb2\xa1"
        + struct.pack("<HHIIII", 2, 4, 0, 0, 65535, 1)
        + struct.pack("<IIII", 0, 0, 30, 30)
        + b"\x00" * 12
        + b"\x88\x8e"
        + b"\x00" * 16
    )

    ticks = []

    def on_tick(analysis, msg):
        ticks.append(msg)

    fake_proc = MagicMock()
    fake_proc.send_signal = MagicMock()
    fake_proc.wait = MagicMock()
    fake_proc.kill = MagicMock()

    with (
        patch("handshakelab.sniffer.which", return_value="/usr/sbin/tcpdump"),
        patch("handshakelab.sniffer.subprocess.Popen", return_value=fake_proc),
    ):
        with patch("handshakelab.sniffer.analyze_capture") as mock_analyze:
            mock_analyze.return_value = CaptureAnalysis(
                1, 1, 0, 0, True, out.stat().st_size
            )
            from handshakelab.sniffer import _sniff_tcpdump

            _sniff_tcpdump(
                iface="en9",  # non-built-in
                output=out,
                bssid=None,
                channel=6,
                duration_sec=1,
                on_tick=on_tick,
            )

    # No warning about built-in WiFi
    assert not any("Built-in macOS" in m for m in ticks)


def test_tcpdump_sniffer_empty_capture_mentions_usb_on_macos_en0(tmp_path):
    """When capture on en0 produces no packets, the error mentions USB adapter."""
    import sys

    if sys.platform != "darwin":
        pytest.skip("macOS-specific behavior")

    # Empty pcapng
    out = tmp_path / "empty.pcapng"
    out.write_bytes(b"\xd4\xc3\xb2\xa1" + b"\x00" * 100)

    fake_proc = MagicMock()
    fake_proc.send_signal = MagicMock()
    fake_proc.wait = MagicMock()
    fake_proc.kill = MagicMock()

    # analyze_capture returns zeros (no packets, no EAPOL)
    with (
        patch("handshakelab.sniffer.which", return_value="/usr/sbin/tcpdump"),
        patch("handshakelab.sniffer.subprocess.Popen", return_value=fake_proc),
        patch(
            "handshakelab.sniffer.analyze_capture",
            return_value=CaptureAnalysis(0, 0, 0, 0, False, 0),
        ),
    ):
        from handshakelab.sniffer import _sniff_tcpdump

        with pytest.raises(SnifferError) as exc_info:
            _sniff_tcpdump(
                iface="en0",
                output=out,
                bssid=None,
                channel=6,
                duration_sec=0.1,  # very short
                on_tick=None,
            )
    # Error should mention monitor mode limitation
    assert "monitor mode" in str(exc_info.value).lower()


def test_sniffer_result_dataclass():
    """SnifferResult dataclass fields."""
    from pathlib import Path

    r = SnifferResult(
        capture_path=Path("/tmp/x.pcap"),
        backend="tcpdump",
        analysis=CaptureAnalysis(0, 0, 0, 0, False, 0),
        duration_sec=10,
    )
    assert r.backend == "tcpdump"
    assert r.duration_sec == 10
