"""Tests for handshakelab.wordlist_gen — SSID/BSSID heuristic wordlist generation."""

from __future__ import annotations

from pathlib import Path

from handshakelab.wordlist_gen import (
    build_combined_wordlist,
    generate_from_ssid,
    load_common_passwords,
    stage_wordlists,
)


def test_load_common_passwords_returns_list():
    """load_common_passwords returns a list of strings."""
    passwords = load_common_passwords()
    assert isinstance(passwords, list)
    assert len(passwords) > 0
    assert all(isinstance(p, str) for p in passwords)


def test_generate_from_ssid_empty_returns_empty():
    """Empty SSID returns no candidates."""
    assert generate_from_ssid("") == []
    assert generate_from_ssid("   ") == []


def test_generate_from_ssid_basic():
    """Basic SSID produces base + common suffixes/prefixes."""
    out = generate_from_ssid("LAB-AP")
    assert "LAB-AP" in out
    assert "lab-ap" in out
    assert "LAB-AP1" in out or "lab-ap1" in out
    assert "wifiLAB-AP" in out or "wifi_lab-ap" in out


def test_generate_from_ssid_with_bssid():
    """BSSID adds tail-derived candidates."""
    out = generate_from_ssid("LAB", bssid="AA:BB:CC:DD:EE:FF")
    # Tail of BSSID (last 6 hex chars) lowercased
    assert "ddeeff" in out
    assert "wifiddeeff" in out


def test_generate_from_ssid_digits_extracted():
    """Digits in SSID are extracted as a candidate."""
    out = generate_from_ssid("LAB2024")
    assert "2024" in out
    assert "2024123" in out


def test_generate_from_ssid_substitutions():
    """Common leet substitutions are applied."""
    out = generate_from_ssid("password")
    # a→@, i→1, o→0 (first pass on "password")
    assert "p@ssw0rd" in out
    # e→3, s→$ (second pass on "password" → "pa$$word")
    assert "pa$$word" in out


def test_generate_from_ssid_returns_sorted():
    """Output is sorted by length (shortest first)."""
    out = generate_from_ssid("X")
    # Lengths should be non-decreasing
    for i in range(len(out) - 1):
        assert len(out[i]) <= len(out[i + 1])


def test_generate_from_ssid_dedupes():
    """No duplicates in output."""
    out = generate_from_ssid("LAB")
    assert len(out) == len(set(out))


def test_build_combined_wordlist(tmp_path: Path):
    """build_combined_wordlist writes a dedup'd wordlist and returns line count."""
    out = tmp_path / "wordlist.txt"
    n = build_combined_wordlist("LAB-AP", output=out)
    assert out.exists()
    lines = out.read_text().splitlines()
    assert len(lines) == n
    # No duplicates
    assert len(set(lines)) == len(lines)
    # Contains SSID-derived candidate
    assert any("LAB" in ln for ln in lines)


def test_build_combined_wordlist_includes_ai(tmp_path: Path):
    """AI candidates are included in the combined wordlist."""
    out = tmp_path / "wordlist.txt"
    n = build_combined_wordlist(
        "LAB",
        ai_candidates=["ai_guess_1", "ai_guess_2"],
        output=out,
    )
    content = out.read_text()
    assert "ai_guess_1" in content
    assert "ai_guess_2" in content
    assert n >= 2


def test_build_combined_wordlist_includes_extra_files(tmp_path: Path):
    """Extra wordlist files are merged in."""
    extra = tmp_path / "extra.txt"
    extra.write_text("from_extra_1\nfrom_extra_2\n")
    out = tmp_path / "wordlist.txt"
    build_combined_wordlist("LAB", extra_paths=[extra], output=out)
    content = out.read_text()
    assert "from_extra_1" in content
    assert "from_extra_2" in content


def test_build_combined_wordlist_ignores_missing_extra(tmp_path: Path):
    """Missing extra_paths are silently skipped."""
    out = tmp_path / "wordlist.txt"
    build_combined_wordlist(
        "LAB",
        extra_paths=[tmp_path / "does_not_exist.txt"],
        output=out,
    )
    assert out.exists()


def test_build_combined_wordlist_creates_parent_dir(tmp_path: Path):
    """build_combined_wordlist creates parent directories."""
    out = tmp_path / "subdir" / "deep" / "wl.txt"
    build_combined_wordlist("LAB", output=out)
    assert out.exists()


def test_stage_wordlists_returns_stages(tmp_path: Path):
    """stage_wordlists returns (name, path) tuples in order."""
    stages = stage_wordlists(
        "LAB-AP",
        bssid="AA:BB:CC:DD:EE:FF",
        work_dir=tmp_path,
        config_wordlist=None,
        ai_candidates=None,
    )
    assert len(stages) >= 2
    for name, path in stages:
        assert isinstance(name, str)
        assert isinstance(path, Path)
        assert path.exists()
    # First stage is always SSID heuristics
    assert "SSID" in stages[0][0] or "heuristic" in stages[0][0].lower()


def test_stage_wordlists_with_ai(tmp_path: Path):
    """AI candidates add an extra stage."""
    stages = stage_wordlists(
        "LAB",
        bssid=None,
        work_dir=tmp_path,
        config_wordlist=None,
        ai_candidates=["ai_a", "ai_b"],
    )
    names = [s[0] for s in stages]
    assert any("AI" in n for n in names)


def test_stage_wordlists_with_config_wordlist(tmp_path: Path):
    """Config wordlist adds an extra stage if file exists."""
    cfg_wl = tmp_path / "config.txt"
    cfg_wl.write_text("config_word\n")
    stages = stage_wordlists(
        "LAB",
        bssid=None,
        work_dir=tmp_path,
        config_wordlist=cfg_wl,
        ai_candidates=None,
    )
    # config wordlist should be one of the stage paths
    assert cfg_wl in [s[1] for s in stages]


def test_stage_wordlists_skips_missing_config(tmp_path: Path):
    """Missing config wordlist is skipped."""
    stages = stage_wordlists(
        "LAB",
        bssid=None,
        work_dir=tmp_path,
        config_wordlist=tmp_path / "missing.txt",
        ai_candidates=None,
    )
    paths = [s[1] for s in stages]
    assert tmp_path / "missing.txt" not in paths


def test_stage_wordlists_includes_mutations(tmp_path: Path):
    """Mutations stage is always present."""
    stages = stage_wordlists(
        "LAB", bssid=None, work_dir=tmp_path, config_wordlist=None, ai_candidates=None
    )
    names = [s[0] for s in stages]
    assert any("mutation" in n.lower() for n in names)
