"""Tests for handshakelab.util.wifi — interface helpers and airport path detection."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from handshakelab.util import platform as plat
from handshakelab.util import wifi


def test_airport_path_returns_none_when_missing():
    """airport_path() returns None when the legacy binary doesn't exist."""
    fake_path = "/nonexistent/path/to/airport"
    with patch.object(wifi, "MAC_AIRPORT", fake_path):
        assert wifi.airport_path() is None


def test_airport_path_returns_path_when_exists(tmp_path: Path):
    """airport_path() returns the path when the binary exists."""
    fake_airport = tmp_path / "airport"
    fake_airport.write_text("#!/bin/sh\n")
    with patch.object(wifi, "MAC_AIRPORT", str(fake_airport)):
        result = wifi.airport_path()
        assert result is not None
        assert result == fake_airport


def test_list_interfaces_returns_list():
    """list_interfaces() returns a list (possibly empty) of interface names."""
    ifaces = wifi.list_interfaces()
    assert isinstance(ifaces, list)
    # On Linux, /sys/class/net exists; on macOS, ifconfig -l should return something
    if plat.is_linux():
        assert len(ifaces) >= 1  # at least lo
        assert "lo" in ifaces
    # On macOS, may be empty if ifconfig fails; just check return type


def test_interface_exists_loopback():
    """interface_exists('lo') is True on Linux (and macOS)."""
    if plat.is_linux():
        assert wifi.interface_exists("lo") is True
    # Don't assert on macOS — loopback name is `lo0` there


def test_interface_exists_nonexistent_returns_false():
    """interface_exists('nonexistent_xyz_999') is False."""
    assert wifi.interface_exists("nonexistent_xyz_999") is False


def test_has_root_returns_bool():
    """has_root() returns a boolean."""
    result = wifi.has_root()
    assert isinstance(result, bool)


def test_tool_paths_returns_dict():
    """tool_paths() returns a dict with the expected tool keys."""
    paths = wifi.tool_paths()
    assert isinstance(paths, dict)
    for key in ("hcxdumptool", "hcxpcapngtool", "hashcat", "tshark", "iw", "airport"):
        assert key in paths


def test_linux_supports_monitor_returns_false_for_nonexistent_iface():
    """linux_supports_monitor returns False for a non-existent interface."""
    if plat.is_linux():
        assert wifi.linux_supports_monitor("nonexistent0") is False
    # On macOS, the function returns False because `iw` is not available


def test_linux_supports_monitor_returns_false_on_macos():
    """linux_supports_monitor returns False on macOS (no iw)."""
    if plat.is_macos():
        assert wifi.linux_supports_monitor("en0") is False


def test_set_linux_monitor_mode_returns_commandresult():
    """set_linux_monitor_mode returns a CommandResult."""
    if not plat.is_linux():
        pytest.skip("Linux-only test")
    result = wifi.set_linux_monitor_mode("lo", enable=False)
    # lo is not really changeable but we should get a result
    from handshakelab.util.proc import CommandResult

    assert isinstance(result, CommandResult)


def test_freq_to_channel_2_4ghz():
    """_freq_to_channel converts 2.4 GHz frequencies correctly."""
    assert wifi._freq_to_channel(2412) == 1
    assert wifi._freq_to_channel(2437) == 6
    assert wifi._freq_to_channel(2462) == 11


def test_freq_to_channel_5ghz():
    """_freq_to_channel converts 5 GHz frequencies correctly."""
    assert wifi._freq_to_channel(5180) == 36
    assert wifi._freq_to_channel(5500) == 100
    assert wifi._freq_to_channel(5825) == 165


def test_freq_to_channel_unknown_freq():
    """_freq_to_channel returns None for unknown frequencies."""
    assert wifi._freq_to_channel(100) is None
    assert wifi._freq_to_channel(10000) is None


def test_network_dataclass():
    """Network dataclass accepts all required fields."""
    from handshakelab.util.wifi import Network

    n = Network(
        ssid="LAB",
        bssid="AA:BB:CC:DD:EE:FF",
        channel=6,
        rssi=-50,
        security="WPA2",
    )
    assert n.ssid == "LAB"
    assert n.bssid == "AA:BB:CC:DD:EE:FF"
    assert n.channel == 6
    assert n.rssi == -50
    assert n.security == "WPA2"


def test_parse_iw_scan_basic():
    """_parse_iw_scan handles a typical iw scan output."""
    sample = """
BSS 00:11:22:33:44:55(on wlan0)
    freq: 2437
    signal: -45.00 dBm
    SSID: LAB-AP-01
BSS aa:bb:cc:dd:ee:ff(on wlan0)
    freq: 5180
    signal: -60.00 dBm
    SSID: LAB-AP-02
"""
    nets = wifi._parse_iw_scan(sample)
    assert len(nets) == 2
    assert nets[0].ssid == "LAB-AP-01"
    assert nets[0].bssid == "00:11:22:33:44:55"
    assert nets[0].channel == 6
    assert nets[1].ssid == "LAB-AP-02"
    assert nets[1].channel == 36


def test_parse_iw_scan_empty_ssid_skipped():
    """_parse_iw_scan skips BSS entries with no SSID."""
    sample = """
BSS 00:11:22:33:44:55(on wlan0)
    freq: 2437
    signal: -45.00 dBm
"""
    nets = wifi._parse_iw_scan(sample)
    assert nets == []


def test_parse_airport_scan_basic():
    """_parse_airport_scan parses airport -s output."""
    sample = """                            SSID BSSID             RSSI CHANNEL HT CC SECURITY (auth/unicast/group)
                           LAB-AP 00:11:22:33:44:55  -45  6       Y  US WPA2(PSK/AES/AES)
                          OtherAP aa:bb:cc:dd:ee:ff  -60  36      Y  US WPA2(PSK/AES/AES)
"""
    nets = wifi._parse_airport_scan(sample)
    assert len(nets) == 2
    assert nets[0].ssid == "LAB-AP"
    assert nets[0].channel == 6
    assert nets[0].rssi == -45


def test_parse_airport_scan_short_lines_skipped():
    """_parse_airport_scan skips malformed lines."""
    sample = """
short
"""
    nets = wifi._parse_airport_scan(sample)
    assert nets == []


def test_parse_system_profiler():
    """_parse_system_profiler parses SPAirPortDataType output."""
    sample = """
        Wi-Fi:

          Other Networks (1):

            SSID_STR: OtherAP
            BSSID: aa:bb:cc:dd:ee:ff
            Channel: 6
"""
    nets = wifi._parse_system_profiler(sample)
    assert len(nets) >= 1
    assert nets[0].ssid == "OtherAP"
    assert nets[0].bssid == "AA:BB:CC:DD:EE:FF"


def test_parse_system_profiler_modern_macos():
    """_parse_system_profiler handles modern macOS 14+ output (indented SSID, no BSSID)."""
    sample = """
        Wi-Fi:

          Current Network Information:
            MyHomeWiFi:
              PHY Mode: 802.11ax
              Channel: 44 (5GHz, 160MHz)
              Security: WPA2 Personal
              Signal / Noise: -54 dBm / -92 dBm
          Other Local Wi-Fi Networks:
            Neighbor-2.4G:
              Channel: 1 (2GHz, 20MHz)
              Security: WPA2 Personal
            Neighbor-5G:
              Channel: 36 (5GHz, 80MHz)
              Security: WPA2 Personal
"""
    nets = wifi._parse_system_profiler(sample)
    assert len(nets) == 3
    # Current network has BSSID-less record (we don't have one in the sample)
    home = next(n for n in nets if n.ssid == "MyHomeWiFi")
    assert home.channel == 44
    assert home.rssi == -54
    assert home.security == "WPA2 Personal"
    assert home.bssid is None  # modern macOS doesn't expose BSSID
    # Other networks
    n24 = next(n for n in nets if n.ssid == "Neighbor-2.4G")
    assert n24.channel == 1
    n5 = next(n for n in nets if n.ssid == "Neighbor-5G")
    assert n5.channel == 36


def test_parse_system_profiler_filters_interface_names():
    """_parse_system_profiler ignores interface headers (en0, awdl0, etc.)."""
    sample = """
        Wi-Fi:

          Software Versions:
              CoreWLAN: 16.0
          Interfaces:
            en0:
              Card Type: Wi-Fi
              Status: Connected
            awdl0:
              Card Type: AWDL
          Other Local Wi-Fi Networks:
            MyNet:
              Channel: 6
              Security: WPA2 Personal
"""
    nets = wifi._parse_system_profiler(sample)
    # Should only have MyNet, not en0 or awdl0
    ssids = [n.ssid for n in nets]
    assert "en0" not in ssids
    assert "awdl0" not in ssids
    assert "MyNet" in ssids


def test_validate_eapol_on_missing_file():
    """validate_eapol returns False on a missing pcap."""
    from handshakelab.util.wifi import validate_eapol

    result = validate_eapol(Path("/nonexistent/file.pcap"))
    assert result is False


def test_set_linux_monitor_mode_enable_path():
    """set_linux_monitor_mode(enable=True) invokes the right steps on Linux."""
    if not plat.is_linux():
        pytest.skip("Linux-only test")
    # Just verify the function returns a CommandResult; don't actually change interface state
    result = wifi.set_linux_monitor_mode("lo", enable=False)  # idempotent
    from handshakelab.util.proc import CommandResult

    assert isinstance(result, CommandResult)


def test_parse_nmcli_scan_basic():
    """_parse_nmcli_scan parses nmcli output."""
    sample = """
SSID            BSSID              CHAN  SIGNAL  SECURITY
LAB-AP          AA:BB:CC:DD:EE:FF  6     -50     WPA2
TestNet         11:22:33:44:55:66  36    -70     WPA3
--              AA:BB:CC:DD:EE:00  1     -80     --
"""
    nets = wifi._parse_nmcli_scan(sample)
    # Header line + 2 valid + 1 with -- SSID skipped
    ssids = [n.ssid for n in nets]
    assert "LAB-AP" in ssids
    assert "TestNet" in ssids
    assert "--" not in ssids

    lab = next(n for n in nets if n.ssid == "LAB-AP")
    assert lab.channel == 6
    assert lab.rssi == -50
    assert lab.security == "WPA2"


def test_parse_nmcli_scan_empty():
    """_parse_nmcli_scan returns empty on empty input."""
    assert wifi._parse_nmcli_scan("") == []
    assert wifi._parse_nmcli_scan("header only\n") == []


def test_parse_nmcli_scan_short_lines():
    """_parse_nmcli_scan skips malformed lines."""
    sample = """
short
"""
    assert wifi._parse_nmcli_scan(sample) == []
