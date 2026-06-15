# HandshakeLab — MASTER_TODO.md

> **Product:** HandshakeLab — passive WiFi capture + offline crack (authorized product testing)  
> **Repo:** [github.com/Ufonik88/Wehopon](https://github.com/Ufonik88/Wehopon)  
> **Version:** 0.3.1  
> **Last updated:** 2026-06-15  
>
> **Full status doc:** [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) — read this for complete done/remaining list.

---

## 0. How to use this document

- **Status legend:** ✅ done · 🟡 in progress · ⬜ pending · ❌ cancelled
- **Owners:** `[user]` · `[agent]`
- Append new tasks to **Active Backlog**. Move completed items to **Done** with date + evidence.

---

## 1. Original brief

1. Capture WiFi handshake from the air (passive — **no joining the network**)
2. Save locally
3. Crack offline (no failed logins against AP)
4. Show plaintext password for manual device join

**Platforms:** Linux + macOS.

---

## 2. Current status snapshot (v0.3.1)

| Area | State | Evidence |
| --- | --- | --- |
| Built-in passive sniffer (tcpdump/hcxdumptool/airport) | ✅ | `src/handshakelab/sniffer.py` |
| EAPOL handshake detection (no Wireshark GUI) | ✅ | `src/handshakelab/eapol.py` |
| Web UI: scan → select → auto-crack → plaintext | ✅ | `handshakelab ui`, `src/handshakelab/web/` |
| Auto pipeline with live SSE progress | ✅ | `src/handshakelab/pipeline.py` |
| Enhanced multi-stage crack + optional AI wordlist | ✅ | `crack_enhanced.py`, `ai_wordlist.py` |
| Full CLI (doctor, scan, capture, import, convert, crack, show, report, list) | ✅ | `src/handshakelab/cli.py` |
| SQLite vault + artifact dirs | ✅ | `src/handshakelab/vault.py` |
| Authorization gate + UI trust checkbox | ✅ | `src/handshakelab/legal.py` |
| Unit tests (40) + CI | ✅ | `tests/`, `.github/workflows/ci.yml` |
| Project status documentation | ✅ | `docs/PROJECT_STATUS.md` |
| HIL checklist template | ✅ | `docs/HIL_CHECKLIST.md` |
| Tool versions recorded in `meta.json` per run | ✅ | `capture.py:_tool_versions()` |
| Lab context (name/operator/adapter) exposed in `/api/health` + UI | ✅ | `server.py`, `web/app.js` |
| Passphrase masked in `report.json` (security) | ✅ | `report.py:_safe_crack_payload()` |
| `iface` defaults to `lab.toml` in scan/capture/import | ✅ | `cli.py` |
| Sniffer backend order = docs (tcpdump first) | ✅ | `sniffer.py:_available_backends()` |
| **Bench HIL verification on real adapter** | ⬜ | User must run |
| **End-to-end crack on owned lab AP** | ⬜ | User must run |
| GPU hashcat in doctor | ⬜ | Future |
| WPA3-SAE support | ⬜ | Future |
| GitHub release tag v0.3.1 | ⬜ | Optional |

---

## 3. Phase plan

### Phase 0 — Planning ✅
### Phase 1 — Toolchain bootstrap ✅
### Phase 2 — Capture ✅
### Phase 3 — Convert + vault ✅
### Phase 4 — Offline crack ✅
### Phase 5 — CLI + reports ✅
### Phase 6 — Web UI + auto-crack ✅
### Phase 7 — Built-in sniffer + EAPOL (v0.3.0) ✅

### Phase 7b — Hardening & UX gaps (v0.3.1) ✅ (2026-06-15)
- ✅ Make `iface` optional across CLI (defaults to `lab.toml`)
- ✅ Mask plaintext passphrase in `report.json` (only `show --reveal` exposes it)
- ✅ Realign sniffer backend order with documented "tcpdump primary"
- ✅ Record tool versions in per-run `meta.json` (TECHNICAL_BLUEPRINT §4.3)
- ✅ Expose lab name/operator/default-adapter via `/api/health` and render in UI
- ✅ Add unit tests for doctor, report, convert, crack, pipeline, ai_wordlist (17 → 40 tests)

### Phase 8 — Bench verification ⬜ (current)
- ⬜ User installs tcpdump + hcxtools + hashcat
- ⬜ User runs `sudo handshakelab doctor`
- ⬜ User completes `docs/HIL_CHECKLIST.md` on lab AP
- ⬜ Evidence recorded (adapter model, capture path, crack time)

### Phase 9 — Future enhancements ⬜
See **§7 Future Enhancements & Roadmap** below for prioritized backlog.

---

## 4. Active backlog

- [ ] **[user]** `sudo apt install tcpdump hcxdumptool hcxtools hashcat` (or brew on Mac)
- [ ] **[user]** `pip install -e .` and `sudo handshakelab ui`
- [ ] **[user]** USB monitor-mode adapter on Linux bench (see `docs/HARDWARE.md`)
- [ ] **[user]** End-to-end test on lab AP with known weak password
- [ ] **[user]** Fill in `docs/HIL_CHECKLIST.md` after first successful run
- [ ] **[user]** Add custom wordlist path to `lab.toml` (optional)
- [ ] **[user]** Set `HANDSHAKELAB_AI_API_KEY` for AI-assisted guesses (optional)
- [ ] **[agent]** Tag `v0.3.1` GitHub release after user HIL pass

---

## 5. Decisions log

| # | Decision | Date |
| --- | --- | --- |
| 1 | Product name: HandshakeLab (repo still `Wehopon`) | 2026-06-14 |
| 2 | Python CLI + FastAPI web UI | 2026-06-14 |
| 3 | Offline crack only; no auto-join | 2026-06-14 |
| 4 | Built-in sniffer (tcpdump primary) — no Wireshark GUI required | 2026-06-14 |
| 5 | Unknown password OK — passive capture, never join WiFi | 2026-06-14 |
| 6 | AI generates wordlist candidates, Hashcat verifies | 2026-06-14 |
| 7 | `ui.trust_operator_ack = true` — UI checkbox satisfies auth for ad-hoc lab | 2026-06-14 |
| 8 | Plaintext passphrase never appears in QA reports — only `show --reveal` exposes it | 2026-06-15 |
| 9 | Per-run `meta.json` records installed tool versions for forensic auditability | 2026-06-15 |
| 10 | Web UI surfaces lab name + operator + default adapter from `lab.toml` | 2026-06-15 |

---

## 6. Done (archive)

- 2026-06-15 — v0.3.1: CLI/UX hardening, security (passphrase masking), audit (tool versions), test coverage 17 → 40
- 2026-06-14 — v0.3.0: built-in sniffer, EAPOL detection, live UI counters
- 2026-06-14 — v0.2.0: web UI, auto-crack pipeline, enhanced crack, AI wordlist
- 2026-06-14 — v0.1.0: full CLI, vault, Linux/macOS capture, tests, CI
- 2026-06-14 — Redesigned from wrong WeHopOn travel app to HandshakeLab
- 2026-06-14 — Full planning docs in `docs/`
- 2026-06-14 — `docs/PROJECT_STATUS.md` + `docs/HIL_CHECKLIST.md` written

---

## 7. Future Enhancements & Roadmap

The items below were identified during the v0.3.1 audit (2026-06-15). They are
not regressions — they are explicit, scoped improvements that will land in
later releases. Each item lists the file/module it touches and an acceptance
signal so it can be marked ✅ when shipped.

### 7.1 High priority — must-have for v0.4.0

| # | Item | Module / file | Why it matters | Acceptance signal |
| --- | --- | --- | --- | --- |
| H1 | **GPU hashcat detection in `doctor`** — probe OpenCL/CUDA/Metal and report compute devices | `doctor.py` | Labs with NVIDIA/AMD/M-series GPUs waste time on CPU mode. Detect & surface in UI. | `handshakelab doctor` shows `hashcat_gpu:NVIDIA…` row; `crack` defaults to GPU device |
| H2 | **Artifact download in web UI** — `/api/run/<id>/artifacts` lists files, `/api/run/<id>/artifact/<name>` streams them | `server.py`, `web/app.js` | Avoids SSH/SCP for sharing `capture.pcapng` + `crack.22000` with QA ticket systems | UI shows “Download” buttons next to each artifact; headers return `Content-Disposition` |
| H3 | **Controlled deauth module (lab-only, off by default)** — opt-in via `capture.deauth_enabled = true` in `lab.toml` | new `deauth.py`; config flag already exists | APs with no active clients never produce a handshake; deauth forces re-association. Must require double-ack in UI. | `deauth.py` ships with tests; UI shows extra “I will only deauth my lab AP” checkbox; `meta.json` records `deauth=true` |
| H4 | **Encrypted passphrase at rest** — wrap `crack_results.passphrase` with Fernet (key from `HANDSHAKELAB_VAULT_KEY`) | `vault.py`, `crack.py`, `report.py` | DB file may be exfiltrated; the passphrase is the highest-value secret | `vault.db` stores ciphertext; `--reveal` decrypts; test asserts plaintext never written to disk |

### 7.2 Medium priority — v0.5.0 backlog

| # | Item | Module / file | Why it matters | Acceptance signal |
| --- | --- | --- | --- | --- |
| M1 | **WPA3-SAE capture + tooling notes** — research `hcxdumptool --sae` and document a WPA3 lab procedure | `docs/WPA3_NOTES.md` (new), `sniffer.py` | Roadmap item carried from v0.3.0; common in modern APs | Doc published; sniffer backend accepts `--sae` flag and tags `meta.json.wpa3=true` |
| M2 | **`convert_file` registers standalone runs in vault** so they appear in `list` and `crack latest` | `convert.py` | Today, a one-off `convert file.pcapng` creates a DB-less run that `crack latest` cannot pick up | `convert_file` calls `insert_run` with a synthetic run id; `list` shows it |
| M3 | **Auto-channel discovery during scan** — prefer the channel of the strongest BSSID matching the SSID | `pipeline.py` | Operators often run capture without `--channel` and rely on the scan loop. Make it explicit. | `pipeline.on_capture_tick` includes `channel: N`; no manual `--channel` needed for the common case |
| M4 | **Run export (zip) command** — `handshakelab export <run>` produces a self-contained evidence bundle (capture + hashes + logs + report) | new `export.py` and CLI command | Easier QA ticket attachments | `handshakelab export latest` writes `run-<id>.zip` |
| M5 | **AI candidates cache** — memoize by `(ssid, bssid, lab_name)` for 24h on disk | `ai_wordlist.py` | Avoids re-paying API costs across runs against the same AP | `~/.local/share/handshakelab/ai_cache/` JSON files; tests assert hit/miss |

### 7.3 Low priority — opportunistic / nice-to-have

| # | Item | Module / file | Why it matters | Acceptance signal |
| --- | --- | --- | --- | --- |
| L1 | **Repository rename** `Wehopon` → `HandshakeLab` | GitHub repo settings | Cosmetic; reduces user confusion | `git@github.com:HandshakeLab/handshakelab.git` is the canonical clone URL; redirect in place |
| L2 | **`.deb` package** with `pip` shim and `dpkg`-managed deps | new `packaging/deb/` | One-command install on Ubuntu | `apt install ./handshakelab_0.4.0.deb` works in CI image |
| L3 | **Homebrew formula** | `packaging/homebrew/handshakelab.rb` | One-command install on macOS | `brew install handshakelab/tap/handshakelab` works |
| L4 | **CI matrix expansion** — add Python 3.12 and 3.13, add macOS runner for smoke test | `.github/workflows/ci.yml` | Future-proof Python support; macOS smoke covers airport path | Workflow badge green on all combos |
| L5 | **Structured JSON logging** to `~/.local/share/handshakelab/logs/handshakelab.log` | new `logging.py` | Helpdesk support when a customer hits an error | `journalctl`-style rotation; tests assert log line shape |
| L6 | **Type-checking with `mypy --strict`** in CI | `pyproject.toml`, CI | Catch dataclass drift before release | `mypy` step added to CI; zero errors on `src/` |
| L7 | **Plugin system for capture backends** (e.g. airodump-ng shim) | `sniffer.py` | Long-term extensibility without forking | `CaptureBackend` Protocol + registry in `util/backends.py` |
| L8 | **i18n / l10n of UI strings** (English default) | `web/app.js` | Multi-region QA teams | `data-i18n` attributes; `lang` toggle in header |
| L9 | **Run status badge in `handshakelab list`** with last-touched timestamp | `cli.py`, `vault.py` | Quick audit of stale runs | `list` shows `last_status_change` column |
| L10 | **Persistent UI preferences** (last-selected interface, last AI toggle) in `localStorage` | `web/app.js` | One less click on repeat sessions | `init()` hydrates from `localStorage`; tests assert fallback when empty |

### 7.4 Out of scope — explicitly rejected

| Item | Reason |
| --- | --- |
| Online brute force against the AP | Violates the core “offline crack only” principle and `LEGAL_AND_ETHICS.md` |
| Cloud / distributed cracking | Out of scope by design; not aligned with lab-on-laptop model |
| WPS PIN online attack | Causes AP-side throttling; banned by policy |
| Automatic connection to cracked networks | By design, the operator types the password manually on the DUT |
| Mobile app | Out of scope; CLI + web UI cover the workflow |

### 7.5 How to use this section

- New ideas go to **§7.2 Medium** or **§7.3 Low** with a one-line rationale.
- Promote to **§7.1 High** when a release blocks on it.
- Move to **§6 Done** with date + PR/issue link when shipped.
