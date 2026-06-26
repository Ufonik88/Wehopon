"""Optional AI-assisted password candidate generation (not hash cracking)."""

from __future__ import annotations

import json
import os
import re
from urllib import error, request


def ai_available() -> bool:
    return bool(os.environ.get("HANDSHAKELAB_AI_API_KEY"))


def generate_ai_candidates(
    ssid: str,
    *,
    bssid: str | None = None,
    lab_name: str = "",
    max_candidates: int = 80,
) -> list[str]:
    """
    Ask an OpenAI-compatible chat API for likely weak passwords.
    Uses HANDSHAKELAB_AI_API_KEY and optional HANDSHAKELAB_AI_BASE_URL.
    """
    api_key = os.environ.get("HANDSHAKELAB_AI_API_KEY")
    if not api_key:
        return []

    base_url = os.environ.get(
        "HANDSHAKELAB_AI_BASE_URL",
        "https://api.openai.com/v1",
    ).rstrip("/")
    model = os.environ.get("HANDSHAKELAB_AI_MODEL", "gpt-4o-mini")

    prompt = f"""You help authorized WiFi product QA engineers guess likely WEAK provisioning passwords.
Target SSID: {ssid}
BSSID: {bssid or 'unknown'}
Lab context: {lab_name or 'consumer IoT / security device testing'}

Generate {max_candidates} likely weak passwords (8-63 chars, WPA2 compatible).
Include: default vendor patterns, SSID-based variants, common IoT defaults, year suffixes.
One password per line. No explanation. No numbering. No quotes."""

    body = json.dumps(
        {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "Output only password candidates, one per line.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
        }
    ).encode()

    req = request.Request(
        f"{base_url}/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=45) as resp:
            payload = json.loads(resp.read().decode())
    except (error.URLError, error.HTTPError, json.JSONDecodeError, TimeoutError):
        return []

    try:
        content = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return []

    candidates: list[str] = []
    for line in content.splitlines():
        w = line.strip().strip('"').strip("'")
        w = re.sub(r"^\d+[\).\s]+", "", w)
        if 8 <= len(w) <= 63 and w not in candidates:
            candidates.append(w)
        if len(candidates) >= max_candidates:
            break
    return candidates
