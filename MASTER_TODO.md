# HandshakeLab — MASTER_TODO.md

> **Product:** HandshakeLab — passive WiFi capture + offline crack (authorized product testing)  
> **Repo:** [github.com/Ufonik88/Wehopon](https://github.com/Ufonik88/Wehopon)  
> **Version:** 0.3.0  
> **Last updated:** 2026-06-14  
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

## 2. Current status snapshot (v0.3.0)

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
| Unit tests (17) + CI | ✅ | `tests/`, `.github/workflows/ci.yml` |
| Project status documentation | ✅ | `docs/PROJECT_STATUS.md` |
| HIL checklist template | ✅ | `docs/HIL_CHECKLIST.md` |
| **Bench HIL verification on real adapter** | ⬜ | User must run |
| **End-to-end crack on owned lab AP** | ⬜ | User must run |
| GPU hashcat in doctor | ⬜ | Future |
| WPA3-SAE support | ⬜ | Future |
| GitHub release tag v0.3.0 | ⬜ | Optional |

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

### Phase 8 — Bench verification ⬜ (current)
- ⬜ User installs tcpdump + hcxtools + hashcat
- ⬜ User runs `sudo handshakelab doctor`
- ⬜ User completes `docs/HIL_CHECKLIST.md` on lab AP
- ⬜ Evidence recorded (adapter model, capture path, crack time)

### Phase 9 — Future enhancements ⬜
- ⬜ Optional controlled deauth (lab-only, off by default)
- ⬜ WPA3 notes / tooling
- ⬜ GPU detection in doctor
- ⬜ Artifact download in web UI
- ⬜ `.deb` / Homebrew packaging
- ⬜ Rename repo to `HandshakeLab`

---

## 4. Active backlog

- [ ] **[user]** `sudo apt install tcpdump hcxdumptool hcxtools hashcat` (or brew on Mac)
- [ ] **[user]** `pip install -e .` and `sudo handshakelab ui`
- [ ] **[user]** USB monitor-mode adapter on Linux bench (see `docs/HARDWARE.md`)
- [ ] **[user]** End-to-end test on lab AP with known weak password
- [ ] **[user]** Fill in `docs/HIL_CHECKLIST.md` after first successful run
- [ ] **[user]** Add custom wordlist path to `lab.toml` (optional)
- [ ] **[user]** Set `HANDSHAKELAB_AI_API_KEY` for AI-assisted guesses (optional)
- [ ] **[agent]** Tag `v0.3.0` GitHub release after user HIL pass

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

---

## 6. Done (archive)

- 2026-06-14 — v0.3.0: built-in sniffer, EAPOL detection, live UI counters
- 2026-06-14 — v0.2.0: web UI, auto-crack pipeline, enhanced crack, AI wordlist
- 2026-06-14 — v0.1.0: full CLI, vault, Linux/macOS capture, tests, CI
- 2026-06-14 — Redesigned from wrong WeHopOn travel app to HandshakeLab
- 2026-06-14 — Full planning docs in `docs/`
- 2026-06-14 — `docs/PROJECT_STATUS.md` + `docs/HIL_CHECKLIST.md` written