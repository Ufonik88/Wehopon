from pathlib import Path

from handshakelab.wordlist_gen import build_combined_wordlist, generate_from_ssid, stage_wordlists


def test_generate_from_ssid():
    words = generate_from_ssid("LabCam01", bssid="AA:BB:CC:DD:EE:FF")
    assert "LabCam01" in words
    assert any("labcam01" in w.lower() for w in words)


def test_build_combined_wordlist(tmp_path: Path):
    out = tmp_path / "wl.txt"
    count = build_combined_wordlist("TestAP", output=out)
    assert count > 5
    assert out.exists()
    assert "password" in out.read_text()


def test_stage_wordlists(tmp_path: Path):
    stages = stage_wordlists(
        "TestAP", bssid=None, work_dir=tmp_path, config_wordlist=None, ai_candidates=["TestAP2026!"]
    )
    names = [s[0] for s in stages]
    assert "SSID heuristics + lab common" in names
    assert "AI-assisted candidates" in names
