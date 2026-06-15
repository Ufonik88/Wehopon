"""Tests for the AI wordlist helper (no live API call)."""

from handshakelab.ai_wordlist import ai_available, generate_ai_candidates


def test_ai_available_no_key(monkeypatch):
    monkeypatch.delenv("HANDSHAKELAB_AI_API_KEY", raising=False)
    assert ai_available() is False


def test_ai_available_with_key(monkeypatch):
    monkeypatch.setenv("HANDSHAKELAB_AI_API_KEY", "sk-test")
    assert ai_available() is True


def test_generate_ai_candidates_no_key(monkeypatch):
    monkeypatch.delenv("HANDSHAKELAB_AI_API_KEY", raising=False)
    assert generate_ai_candidates("LabAP") == []
