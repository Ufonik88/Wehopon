"""Tests for handshakelab.legal — authorization gate."""

from __future__ import annotations

from pathlib import Path

import pytest

from handshakelab.config import (
    AllowedTarget,
    LabConfig,
    UiConfig,
    load_config,
)
from handshakelab.legal import AuthorizationError, assert_authorized


def test_assert_authorized_skips_when_not_required():
    """assert_authorized returns silently when require_authorization=False."""
    cfg = LabConfig(path=Path("/tmp/lab.toml"), require_authorization=False)
    # Should not raise
    assert_authorized("ANY", None, cfg, ack=False)


def test_assert_authorized_raises_without_ack():
    """assert_authorized raises when ack=False and require_authorization=True."""
    cfg = LabConfig(path=Path("/tmp/lab.toml"), require_authorization=True)
    with pytest.raises(AuthorizationError, match="--ack-authorized"):
        assert_authorized("ANY", None, cfg, ack=False)


def test_assert_authorized_raises_when_no_targets():
    """assert_authorized raises when ack=True but no allowed_targets listed."""
    cfg = LabConfig(path=Path("/tmp/lab.toml"), require_authorization=True)
    with pytest.raises(AuthorizationError, match="No allowed_targets"):
        assert_authorized("ANY", None, cfg, ack=True)


def test_assert_authorized_passes_for_known_target():
    """assert_authorized passes when target is in allowed_targets."""
    cfg = LabConfig(
        path=Path("/tmp/lab.toml"),
        require_authorization=True,
        allowed_targets=[AllowedTarget(ssid="LAB-AP", bssid="AA:BB:CC:DD:EE:FF")],
    )
    # Should not raise
    assert_authorized("LAB-AP", "AA:BB:CC:DD:EE:FF", cfg, ack=True)


def test_assert_authorized_passes_for_ssid_match():
    """assert_authorized passes when SSID matches (BSSID not required)."""
    cfg = LabConfig(
        path=Path("/tmp/lab.toml"),
        require_authorization=True,
        allowed_targets=[AllowedTarget(ssid="LAB-AP", bssid=None)],
    )
    assert_authorized("LAB-AP", "AA:BB:CC:DD:EE:FF", cfg, ack=True)


def test_assert_authorized_trusts_operator_ack():
    """When ui.trust_operator_ack is True, unknown targets with ack pass."""
    cfg = LabConfig(
        path=Path("/tmp/lab.toml"),
        require_authorization=True,
        allowed_targets=[AllowedTarget(ssid="KNOWN-AP", bssid=None)],
        ui=UiConfig(trust_operator_ack=True),
    )
    # ack=True + trust_operator_ack=True should allow even unknown target
    assert_authorized("UNKNOWN-AP", None, cfg, ack=True)


def test_assert_authorized_rejects_unknown_target():
    """When ui.trust_operator_ack is False, unknown targets rejected even with ack."""
    cfg = LabConfig(
        path=Path("/tmp/lab.toml"),
        require_authorization=True,
        allowed_targets=[AllowedTarget(ssid="KNOWN-AP", bssid=None)],
        ui=UiConfig(trust_operator_ack=False),
    )
    with pytest.raises(AuthorizationError, match="Target not in allow-list"):
        assert_authorized("UNKNOWN-AP", None, cfg, ack=True)


def test_assert_authorized_bssid_mismatch():
    """BSSID mismatch with allow-listed target raises."""
    cfg = LabConfig(
        path=Path("/tmp/lab.toml"),
        require_authorization=True,
        allowed_targets=[AllowedTarget(ssid="LAB-AP", bssid="AA:BB:CC:DD:EE:FF")],
        ui=UiConfig(trust_operator_ack=False),
    )
    with pytest.raises(AuthorizationError, match="Target not in allow-list"):
        assert_authorized("LAB-AP", "11:22:33:44:55:66", cfg, ack=True)


def test_load_config_returns_defaults_on_missing_file(tmp_path):
    """load_config returns permissive defaults when file is missing."""
    p = tmp_path / "nope.toml"
    cfg = load_config(p)
    assert cfg.path == p
    assert cfg.require_authorization is False


def test_load_config_with_full_lab_toml(tmp_path):
    """load_config parses a fully-populated lab.toml."""
    p = tmp_path / "lab.toml"
    p.write_text("""
[lab]
name = "My Lab"
operator = "tester"
require_authorization = true

[[allowed_targets]]
ssid = "LAB-AP-01"
bssid = "AA:BB:CC:DD:EE:FF"
owner = "QA"
authorization_ref = "TICKET-1"

[[allowed_targets]]
ssid = "LAB-AP-02"
bssid = "11:22:33:44:55:66"

[capture]
default_adapter = "wlan1"
default_duration_sec = 600
deauth_enabled = true

[crack]
hashcat_bin = "/usr/bin/hashcat"
wordlist = "/tmp/wordlist.txt"
workload_profile = 3

[ui]
trust_operator_ack = false
default_port = 9000
""")
    cfg = load_config(p)
    assert cfg.name == "My Lab"
    assert cfg.operator == "tester"
    assert cfg.require_authorization is True
    assert len(cfg.allowed_targets) == 2
    assert cfg.allowed_targets[0].ssid == "LAB-AP-01"
    assert cfg.allowed_targets[0].owner == "QA"
    assert cfg.capture.default_adapter == "wlan1"
    assert cfg.capture.default_duration_sec == 600
    assert cfg.capture.deauth_enabled is True
    assert cfg.crack.hashcat_bin == "/usr/bin/hashcat"
    assert cfg.crack.wordlist == "/tmp/wordlist.txt"
    assert cfg.crack.workload_profile == 3
    assert cfg.ui.trust_operator_ack is False
    assert cfg.ui.default_port == 9000


def test_load_config_defaults(tmp_path):
    """load_config fills in defaults for missing sections."""
    p = tmp_path / "minimal.toml"
    p.write_text('[lab]\nname = "X"\n')
    cfg = load_config(p)
    assert cfg.name == "X"
    assert cfg.capture.default_adapter == "wlan0"  # default
    assert cfg.ui.default_port == 8765
    assert cfg.ui.trust_operator_ack is True


def test_find_target_bssid_normalization():
    """find_target normalizes BSSIDs (hyphens → colons, uppercase)."""
    cfg = LabConfig(
        path=Path("/tmp/x.toml"),
        allowed_targets=[AllowedTarget(ssid="LAB", bssid="aa-bb-cc-dd-ee-ff")],
    )
    # Hyphen input matches colon-stored target
    found = cfg.find_target("LAB", "AA-BB-CC-DD-EE-FF")
    assert found is not None
    assert found.bssid == "aa-bb-cc-dd-ee-ff"


def test_find_target_no_bssid_match():
    """find_target returns None for unknown SSID."""
    cfg = LabConfig(
        path=Path("/tmp/x.toml"),
        allowed_targets=[AllowedTarget(ssid="LAB", bssid="AA:BB:CC:DD:EE:FF")],
    )
    assert cfg.find_target("OTHER", None) is None


def test_find_target_case_insensitive_ssid():
    """SSID matching is case-insensitive."""
    cfg = LabConfig(
        path=Path("/tmp/x.toml"),
        allowed_targets=[AllowedTarget(ssid="LAB-AP", bssid=None)],
    )
    assert cfg.find_target("lab-ap", None) is not None
    assert cfg.find_target("LAB-AP", None) is not None


def test_load_config_with_none_path():
    """load_config with None uses 'lab.toml' as default."""
    # If lab.toml doesn't exist in cwd, returns permissive config
    import os
    cwd = os.getcwd()
    try:
        os.chdir("/tmp")
        cfg = load_config(None)
        assert cfg.require_authorization is False
    finally:
        os.chdir(cwd)
