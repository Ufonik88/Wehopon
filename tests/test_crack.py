"""Tests for the potfile parser and crack attempt wrapper (no live hashcat)."""

from pathlib import Path
from unittest import mock

import pytest

from handshakelab.crack import CrackError, _parse_potfile, attempt_crack
from handshakelab.config import CrackConfig


def test_parse_potfile_missing(tmp_path: Path):
    assert _parse_potfile(tmp_path / "nope.potfile") is None


def test_parse_potfile_basic(tmp_path: Path):
    pot = tmp_path / "h.potfile"
    pot.write_text("WPA*02*abc*def:supersecret\n")
    assert _parse_potfile(pot) == "supersecret"


def test_parse_potfile_empty(tmp_path: Path):
    pot = tmp_path / "h.potfile"
    pot.write_text("\n\n")
    assert _parse_potfile(pot) is None


def test_attempt_crack_missing_wordlist(tmp_path: Path):
    hash_path = tmp_path / "h.22000"
    hash_path.write_text("dummy\n")
    with pytest.raises(CrackError, match="Wordlist not found"):
        attempt_crack(hash_path, tmp_path / "missing.txt", CrackConfig())


def test_attempt_crack_hashcat_not_installed(tmp_path: Path, monkeypatch):
    """When hashcat is missing, we raise a clear CrackError."""
    hash_path = tmp_path / "h.22000"
    hash_path.write_text("WPA*02*abc*def:hash\n")
    wl = tmp_path / "wl.txt"
    wl.write_text("candidate\n")

    monkeypatch.setattr("handshakelab.crack.which", lambda _: None)

    with pytest.raises(CrackError, match="hashcat not found"):
        attempt_crack(hash_path, wl, CrackConfig(hashcat_bin="hashcat"))


def test_attempt_crack_no_match(tmp_path: Path, monkeypatch):
    """When hashcat runs but finds no match, success is False."""
    hash_path = tmp_path / "h.22000"
    hash_path.write_text("WPA*02*abc*def:hash\n")
    wl = tmp_path / "wl.txt"
    wl.write_text("candidate\n")

    monkeypatch.setattr("handshakelab.crack.which", lambda _: "/usr/bin/hashcat")
    monkeypatch.setattr(
        "handshakelab.crack.run",
        lambda *a, **kw: mock.Mock(ok=False, stdout="", stderr=""),
    )

    out = attempt_crack(hash_path, wl, CrackConfig(hashcat_bin="hashcat"))
    assert out.success is False
    assert out.passphrase is None
