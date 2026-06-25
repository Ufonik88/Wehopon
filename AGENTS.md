# HandshakeLab — Agent Instructions

## Project

**HandshakeLab** — passive WiFi handshake capture + offline crack for **authorized product testing**.

**Repo:** [github.com/Ufonik88/Wehopon](https://github.com/Ufonik88/Wehopon)  
**Version:** 0.3.1  
**Status doc:** [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) — **read this first** for done vs remaining work.

## Original brief

Capture handshake passively (no WiFi join) → save locally → crack offline → show plaintext password.

## Read first (every session)

1. [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) — what's built, what's left
2. [`MASTER_TODO.md`](MASTER_TODO.md) — live task ledger
3. [`docs/LEGAL_AND_ETHICS.md`](docs/LEGAL_AND_ETHICS.md) — authorized use only

## Stack

- **Python 3.11+** — Typer CLI, FastAPI web UI
- **Built-in sniffer** — tcpdump, hcxdumptool, macOS airport (`sniffer.py`)
- **EAPOL detection** — `eapol.py` (no Wireshark GUI required)
- **Crack** — Hashcat offline + enhanced stages + optional AI wordlist
- **Vault** — SQLite + filesystem artifacts
- **Platforms** — Linux + macOS

## Key commands

```bash
sudo handshakelab ui      # recommended — web UI
sudo handshakelab doctor  # preflight
handshakelab scan -i wlan1
```

## What is done (v0.3.0)

- Full CLI, web UI, auto-crack pipeline, built-in sniffer, enhanced crack, tests, CI, docs

## What remains

- User bench verification (`docs/HIL_CHECKLIST.md`)
- Future: GPU doctor, WPA3, packaging, repo rename

## Rules

- Never commit captures, wordlists, passphrases, or real `lab.toml`
- Offline crack only — never online brute force against AP
- User does NOT join WiFi to capture — passive sniff only
- Verify with command output before marking tasks done

## 🚨 Hard rule: update TEST_CHECKLIST.md and MASTER_TODO.md after every task

**Every task — bug fix, feature, refactor, test addition, doc change — must end with an update to both:**

1. **`TEST_CHECKLIST.md`** (root) — move completed steps to the ✅ COMPLETED section, add bugs to the Bug Fixes table (with ID, file, fix description, verification evidence), update the Run Log, and add new test steps to the Outstanding section if the task introduces them.
2. **`MASTER_TODO.md`** (root) — append new items to §4 Active backlog (with owner tag), move completed items to §6 Done with date, append a row to §5 Decisions log if the task established a new convention.

**Why:** These are the live ledger of what's done and what's next. Skipping the update makes the docs lie and forces the next session to re-discover state.

**When:** At the **end** of the task, before reporting completion. Not optional, not deferred.

**Format conventions:**
- Bug IDs: `B<n>` for in-session fixes, `O<n>` for the open-issue sweep. Match the IDs already used in `TEST_CHECKLIST.md`.
- Status: ✅ done · ⚠️ partial · ⏳ pending · 🔵 future · N/A n/a
- Run Log entries: date, host, scope, outcome (one line each).

## GitHub CLI on this machine

```bash
export PATH="/home/linuxbrew/.linuxbrew/bin:$PATH"
```