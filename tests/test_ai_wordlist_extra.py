"""Tests for handshakelab.ai_wordlist — AI candidate generation."""

from __future__ import annotations

import json
from unittest.mock import patch


from handshakelab.ai_wordlist import ai_available, generate_ai_candidates


def test_ai_available_false_when_no_key(monkeypatch):
    """ai_available returns False when HANDSHAKELAB_AI_API_KEY is unset."""
    monkeypatch.delenv("HANDSHAKELAB_AI_API_KEY", raising=False)
    assert ai_available() is False


def test_ai_available_true_when_key_set(monkeypatch):
    """ai_available returns True when HANDSHAKELAB_AI_API_KEY is set."""
    monkeypatch.setenv("HANDSHAKELAB_AI_API_KEY", "test-key-12345")
    assert ai_available() is True


def test_generate_ai_candidates_no_key_returns_empty(monkeypatch):
    """generate_ai_candidates returns empty list when no API key."""
    monkeypatch.delenv("HANDSHAKELAB_AI_API_KEY", raising=False)
    result = generate_ai_candidates("LAB-AP")
    assert result == []


def test_generate_ai_candidates_success(monkeypatch):
    """generate_ai_candidates parses successful API response."""
    monkeypatch.setenv("HANDSHAKELAB_AI_API_KEY", "test-key")

    fake_response = {
        "choices": [
            {
                "message": {
                    "content": "password123\nadmin2024\ntest1234\nshort\ntoolongpasswordthatiswayoverthelimitof63charsokkkkkkkkkkk"
                }
            }
        ]
    }

    class FakeResponse:
        def __init__(self, data):
            self.data = data

        def __enter__(self):
            return self

        def __exit__(self, *a):
            pass

        def read(self):
            return json.dumps(self.data).encode()

    with patch("handshakelab.ai_wordlist.request.urlopen", return_value=FakeResponse(fake_response)):
        result = generate_ai_candidates("LAB-AP", max_candidates=80)
    # 4 valid passwords (8-63 chars): password123, admin2024, test1234
    # "short" is 5 chars (filtered), "toolong..." is > 63 (filtered)
    assert "password123" in result
    assert "admin2024" in result
    assert "test1234" in result
    assert "short" not in result


def test_generate_ai_candidates_dedup(monkeypatch):
    """Duplicate candidates are removed."""
    monkeypatch.setenv("HANDSHAKELAB_AI_API_KEY", "test-key")

    fake_response = {
        "choices": [
            {"message": {"content": "password123\npassword123\nadmin2024"}}
        ]
    }

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            pass

        def read(self):
            return json.dumps(fake_response).encode()

    with patch("handshakelab.ai_wordlist.request.urlopen", return_value=FakeResponse()):
        result = generate_ai_candidates("LAB-AP")
    # Should be 2 unique items
    assert len(result) == 2


def test_generate_ai_candidates_handles_numbered_lines(monkeypatch):
    """Numbered list prefixes (1. 2. 3)) are stripped."""
    monkeypatch.setenv("HANDSHAKELAB_AI_API_KEY", "test-key")

    fake_response = {
        "choices": [
            {
                "message": {
                    "content": "1. password123\n2) admin2024\n3 test1234"
                }
            }
        ]
    }

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            pass

        def read(self):
            return json.dumps(fake_response).encode()

    with patch("handshakelab.ai_wordlist.request.urlopen", return_value=FakeResponse()):
        result = generate_ai_candidates("LAB-AP")
    assert "password123" in result
    assert "admin2024" in result
    assert "test1234" in result


def test_generate_ai_candidates_handles_quotes(monkeypatch):
    """Quoted candidates have quotes stripped."""
    monkeypatch.setenv("HANDSHAKELAB_AI_API_KEY", "test-key")

    fake_response = {
        "choices": [
            {"message": {"content": '"password123"\n"admin2024"'}}
        ]
    }

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            pass

        def read(self):
            return json.dumps(fake_response).encode()

    with patch("handshakelab.ai_wordlist.request.urlopen", return_value=FakeResponse()):
        result = generate_ai_candidates("LAB-AP")
    assert "password123" in result
    assert "admin2024" in result


def test_generate_ai_candidates_handles_url_error(monkeypatch):
    """URL errors return empty list gracefully."""
    from urllib import error

    monkeypatch.setenv("HANDSHAKELAB_AI_API_KEY", "test-key")

    with patch(
        "handshakelab.ai_wordlist.request.urlopen",
        side_effect=error.URLError("network down"),
    ):
        result = generate_ai_candidates("LAB-AP")
    assert result == []


def test_generate_ai_candidates_handles_bad_json(monkeypatch):
    """Invalid JSON in response returns empty list."""
    monkeypatch.setenv("HANDSHAKELAB_AI_API_KEY", "test-key")

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            pass

        def read(self):
            return b"not json{"

    with patch("handshakelab.ai_wordlist.request.urlopen", return_value=FakeResponse()):
        result = generate_ai_candidates("LAB-AP")
    assert result == []


def test_generate_ai_candidates_handles_malformed_payload(monkeypatch):
    """Malformed payload (no 'choices') returns empty list."""
    monkeypatch.setenv("HANDSHAKELAB_AI_API_KEY", "test-key")

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            pass

        def read(self):
            return json.dumps({"error": "rate limited"}).encode()

    with patch("handshakelab.ai_wordlist.request.urlopen", return_value=FakeResponse()):
        result = generate_ai_candidates("LAB-AP")
    assert result == []


def test_generate_ai_candidates_respects_max(monkeypatch):
    """max_candidates limits the result count."""
    monkeypatch.setenv("HANDSHAKELAB_AI_API_KEY", "test-key")

    lines = "\n".join(f"password{i:04d}" for i in range(100))
    fake_response = {
        "choices": [{"message": {"content": lines}}]
    }

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            pass

        def read(self):
            return json.dumps(fake_response).encode()

    with patch("handshakelab.ai_wordlist.request.urlopen", return_value=FakeResponse()):
        result = generate_ai_candidates("LAB-AP", max_candidates=10)
    assert len(result) == 10
