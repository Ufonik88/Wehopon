"""Smart wordlist generation from SSID context and lab patterns."""

from __future__ import annotations

import itertools
import re
from pathlib import Path

_DATA = Path(__file__).parent / "data" / "common-lab.txt"


def load_common_passwords() -> list[str]:
    if _DATA.exists():
        return [ln.strip() for ln in _DATA.read_text().splitlines() if ln.strip()]
    return ["password", "12345678", "admin123", "changeme"]


def generate_from_ssid(ssid: str, *, bssid: str | None = None) -> list[str]:
    """Heuristic candidates from SSID/BSSID (product-test patterns)."""
    base = ssid.strip()
    if not base:
        return []

    variants: set[str] = set()
    lowers = base.lower()
    uppers = base.upper()
    title = base.title()
    nospace = re.sub(r"[^a-zA-Z0-9]", "", base)
    digits_only = re.sub(r"\D", "", base)

    for stem in {base, lowers, uppers, title, nospace}:
        if stem:
            variants.add(stem)
            for suffix in ("", "1", "12", "123", "1234", "!", "!!", "@123", "2024", "2025", "2026"):
                variants.add(f"{stem}{suffix}")
            for prefix in ("", "wifi", "ajax", "lab", "test"):
                if prefix:
                    variants.add(f"{prefix}{stem}")
                    variants.add(f"{prefix}_{stem}")
                    variants.add(f"{prefix}-{stem}")

    if digits_only:
        variants.add(digits_only)
        variants.add(digits_only + "123")

    if bssid:
        tail = bssid.replace(":", "")[-6:].lower()
        variants.add(tail)
        variants.add(f"wifi{tail}")

    # Common substitutions
    extra: set[str] = set()
    for v in list(variants):
        extra.add(v.replace("a", "@").replace("i", "1").replace("o", "0"))
        extra.add(v.replace("e", "3").replace("s", "$"))
    variants |= extra

    return sorted(variants, key=len)


def build_combined_wordlist(
    ssid: str,
    *,
    bssid: str | None = None,
    extra_paths: list[Path] | None = None,
    ai_candidates: list[str] | None = None,
    output: Path,
) -> int:
    """Write deduplicated wordlist; return line count."""
    seen: set[str] = set()
    lines: list[str] = []

    def add_many(items: list[str]) -> None:
        for item in items:
            w = item.strip()
            if w and w not in seen:
                seen.add(w)
                lines.append(w)

    add_many(generate_from_ssid(ssid, bssid=bssid))
    add_many(load_common_passwords())

    if ai_candidates:
        add_many(ai_candidates)

    for path in extra_paths or []:
        if path.exists():
            add_many(
                [ln.strip() for ln in path.read_text(errors="ignore").splitlines() if ln.strip()]
            )

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n")
    return len(lines)


def stage_wordlists(
    ssid: str,
    *,
    bssid: str | None,
    work_dir: Path,
    config_wordlist: Path | None,
    ai_candidates: list[str] | None,
) -> list[tuple[str, Path]]:
    """Return ordered crack stages: (name, wordlist_path)."""
    stages: list[tuple[str, Path]] = []

    quick = work_dir / "wl-ssid-quick.txt"
    build_combined_wordlist(ssid, bssid=bssid, output=quick)
    stages.append(("SSID heuristics + lab common", quick))

    if ai_candidates:
        ai_path = work_dir / "wl-ai.txt"
        build_combined_wordlist(ssid, bssid=bssid, ai_candidates=ai_candidates, output=ai_path)
        stages.append(("AI-assisted candidates", ai_path))

    if config_wordlist and config_wordlist.exists():
        stages.append(("lab.toml wordlist", config_wordlist))

    # Mutations file: cartesian light suffix pass on top SSID stems
    mut = work_dir / "wl-mutations.txt"
    stems = generate_from_ssid(ssid, bssid=bssid)[:40]
    muts: set[str] = set()
    for stem in stems:
        for a, b in itertools.product(["", "!", "@", "#"], ["", "1", "123", "2026"]):
            muts.add(f"{stem}{a}{b}")
    mut.write_text("\n".join(sorted(muts)) + "\n")
    stages.append(("SSID mutations", mut))

    return stages
