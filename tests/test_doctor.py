"""Tests for the doctor preflight checks."""

from pathlib import Path

from handshakelab.doctor import run_doctor


def test_doctor_returns_checks():
    checks, ok = run_doctor(iface=None, config_path=Path("/nonexistent/lab.toml"))
    names = {c.name for c in checks}
    # Core system checks are always present
    assert "platform" in names
    assert "hashcat" in names
    assert "hcxpcapngtool" in names
    assert "capture_backend" in names
    # When lab.toml is missing, the check is reported (not raised)
    assert "lab.toml" in names
    assert isinstance(ok, bool)


def test_doctor_with_explicit_iface():
    checks, _ = run_doctor(iface="wlan0", config_path=None)
    iface_checks = [c for c in checks if c.name.startswith("interface:")]
    assert len(iface_checks) == 1
    assert iface_checks[0].name == "interface:wlan0"
