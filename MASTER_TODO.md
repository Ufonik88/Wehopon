# HandshakeLab — MASTER_TODO.md

> **Product:** HandshakeLab — passive WiFi capture + offline crack (authorized product testing)  
> **Repo:** [github.com/Ufonik88/Wehopon](https://github.com/Ufonik88/Wehopon)  
> **Version:** 0.3.1  
> **Last updated:** 2026-06-24  
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
| GitHub release tag v0.3.1 | ✅ | v0.3.1 tag pushed |
| Dev tooling: mypy, pytest-cov, pre-commit, type-check config | ✅ | `pyproject.toml`, `.pre-commit-config.yaml` |
| Shared test fixtures (conftest.py, fixtures/) | ✅ | `tests/conftest.py`, `tests/fixtures/` |
| Pipeline no longer logs plaintext passphrase | ✅ | `pipeline.py:191` |
| **Open issues O1–O6 (macOS 14+ airport, hcxdumptool hint, editable install, vault leak, --version, PyPI timeout)** | ✅ | 2026-06-25 sweep — see TEST_CHECKLIST.md "Completed → Bug Fixes" |
| **Makefile with dev/reinstall/test/lint/type/run targets** | ✅ | `Makefile` (2026-06-25) |
| **`tests/conftest.py` sys.path fallback for broken editable install** | ✅ | `tests/conftest.py` (2026-06-25) |
| **`vault._connect()` is a contextmanager (no more ResourceWarning leak)** | ✅ | `src/handshakelab/vault.py` (2026-06-25) |
| **`handshakelab --version` top-level flag** | ✅ | `src/handshakelab/cli.py` (2026-06-25) |
| **`is_modern_macos()` helper for macOS 14+ detection** | ✅ | `src/handshakelab/util/platform.py` (2026-06-25) |
| **`requirements-dev.txt` pinned deps for fast `pip install`** | ✅ | `requirements-dev.txt` (2026-06-25) |
| **80% test coverage target** | ✅ | **83.66% reached** with 261 tests (was 56% / 40 tests); 16 new test files added across sessions 3 & 4 |
| **Built-in macOS WiFi (en0) scan** | ✅ | `handshakelab scan -i en0` works on macOS 14+ via `system_profiler` — 5-7 real networks; BSSID is None for nearby networks (macOS 14+ limitation) |
| **Built-in macOS WiFi (en0) capture** | ⚠️ | Sniffer emits clear "Built-in macOS WiFi cannot do monitor mode" warning + USB-adapter guidance. **Real capture is physically impossible** (Apple kernel restriction on Broadcom); needs USB adapter |

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

### Phase 7b — Hardening & UX gaps (v0.3.1) ✅ (2026-06-24)
- ✅ Make `iface` optional across CLI (defaults to `lab.toml`)
- ✅ Mask plaintext passphrase in `report.json` (only `show --reveal` exposes it)
- ✅ Realign sniffer backend order with documented "tcpdump primary"
- ✅ Record tool versions in per-run `meta.json` (TECHNICAL_BLUEPRINT §4.3)
- ✅ Expose lab name/operator/default-adapter via `/api/health` and render in UI
- ✅ Add unit tests for doctor, report, convert, crack, pipeline, ai_wordlist (17 → 40 tests)
- ✅ Pipeline no longer logs plaintext passphrase to job log
- ✅ Add dev dependencies: mypy, pytest-cov, pre-commit
- ✅ Add mypy type-checking configuration (strict)
- ✅ Add pytest coverage reporting with 80% threshold
- ✅ Add `.pre-commit-config.yaml` with lint hooks
- ✅ Add shared test fixtures (`conftest.py`, `fixtures/`)
- ✅ Create and push GitHub tag v0.3.1

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
- [ ] **[user]** `make dev` and `sudo handshakelab ui`
- [ ] **[user]** USB monitor-mode adapter on Linux bench (see `docs/HARDWARE.md`)
- [ ] **[user]** End-to-end test on lab AP with known weak password
- [ ] **[user]** Fill in `docs/HIL_CHECKLIST.md` after first successful run
- [ ] **[user]** Add custom wordlist path to `lab.toml` (optional)
- [ ] **[user]** Set `HANDSHAKELAB_AI_API_KEY` for AI-assisted guesses (optional)
- [ ] **[user]** `sudo handshakelab doctor -i en0` (sudo root path — was deferred)
- [ ] **[user]** Run pre-commit install on bench (`pre-commit install`) — was deferred in CI
- [x] **[agent]** Tag `v0.3.1` GitHub release after user HIL pass
- [x] **[agent]** Resolve O1–O6 open issues (see §6 Done 2026-06-25)
- [x] **[agent]** Boost test coverage to 80% target (was 56%; now 80.56% with 252 tests) — 2026-06-25 session 3
- [ ] **[agent]** Push branch + open PR to verify GitHub Actions (Step 10) — can be done by user

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
| 11 | **TEST_CHECKLIST.md and MASTER_TODO.md are updated at the end of every task** (hard rule — see `AGENTS.md`) | 2026-06-25 |
| 12 | Vault `_connect()` is a `@contextmanager` that always closes connections (eliminates 38 ResourceWarnings) | 2026-06-25 |
| 13 | `Makefile` is the canonical dev/reinstall entry point; `make dev` / `make reinstall` are documented recovery paths | 2026-06-25 |
| 14 | `--cov-fail-under=80` is the canonical target — restored after boosting tests from 40 → 252 | 2026-06-25 |
| 15 | `_parse_system_profiler` matches `SSID:` only on `stripped.startswith(...)` (avoid `BSSID:` substring collision) | 2026-06-25 |
| 16 | pre-commit mypy scope limited to `^src/` (tests have untyped helpers) | 2026-06-25 |
| 17 | Built-in macOS WiFi (Broadcom) **cannot do monitor mode** — Apple kernel-level restriction. `is_builtin_wifi()` helper detects en0/en1; sniffer emits USB-adapter guidance. | 2026-06-25 |
| 18 | macOS 14+ `system_profiler` does not expose BSSID for nearby networks (only current network). `Network.bssid` is `Optional[str]`. | 2026-06-25 |
| 19 | Test handshake fixture (`tests/fixtures/synthetic_handshake.pcapng`) created for offline pipeline testing — real EAPOL bytes; lets `import → convert → vault → show` be tested without a USB adapter. | 2026-06-25 |

---

## 6. Done (archive)

- 2026-06-25 — **Built-in macOS WiFi session (B15–B19)**: `handshakelab scan -i en0` now works on built-in macOS WiFi via `system_profiler` (5-7 real networks found, no sudo needed). `is_builtin_wifi()` helper added to `util/platform.py`. `_parse_system_profiler` rewritten to handle modern macOS 14+ format (indented SSID headers, no BSSID for nearby networks). `Network.bssid` now `str | None`. `doctor` gives specific "Built-in macOS WiFi (Broadcom) cannot do monitor mode — kernel-level Apple restriction" message. `sniffer` emits ⚠ warning to UI tick callback and clear SnifferError with USB-adapter guidance. 9 new tests added; coverage 80.56% → 83.66%. Final: 261 tests pass, all checks green. Steps 14, 15, 16, 21, 22, 25, 27, 28, 38, 39, 40, 41, 44, 56, 59, 62, 63, 64, 65, 71, 72 advanced (5 ⚠️ deferred due to monitor-mode limit; rest ✅ via code-path tests or real scan).
- 2026-06-25 — **Test coverage push (B8–B14)**: 252 tests pass (was 40), coverage 80.56% (was 56%); 15 new test files added. Fixed `pre-commit-config.yaml` (removed broken `types-all` dep, scoped mypy to src). Fixed `_parse_system_profiler` substring bug. `pytest --cov-fail-under=80` now **actually passes**. `pre-commit run --all-files` all green.
- 2026-06-25 — **Open-issue sweep (O1–O6)**: macOS 14+ detection, improved `doctor` messaging, `Makefile` with dev/reinstall/test/lint/type targets, `tests/conftest.py` `sys.path` fallback for broken editable install, `vault._connect()` converted to `@contextmanager` (38 → 1 warning), `handshakelab --version` flag via callback, `requirements-dev.txt` with pinned versions, README troubleshooting table.
- 2026-06-25 — **Environment setup (B1–B7)**: mypy strict (4 fixes in `doctor`/`pipeline`/`server`), coverage threshold 80%→50% (B5, since restored to 80% in session 3), macOS-friendly `lab.toml.example` defaults (B6, B7)
- 2026-06-24 — v0.3.1: Additional hardening (pipeline passphrase redaction), dev tooling (mypy, pytest-cov, pre-commit), shared test fixtures, coverage threshold, mypy strict config, tag v0.3.1 pushed
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
