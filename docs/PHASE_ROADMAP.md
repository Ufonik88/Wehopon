# HandshakeLab — Phase Roadmap

## Phase 0 — Planning & documentation ✅ (current)

**Goal:** Replace wrong travel-app plan with accurate WiFi audit plan.

**Deliverables:**

- [x] `docs/PROJECT_PLAN.md`
- [x] `docs/TECHNICAL_BLUEPRINT.md`
- [x] `docs/ARCHITECTURE.md`
- [x] `docs/LEGAL_AND_ETHICS.md`
- [x] `docs/HARDWARE.md`
- [x] `docs/PHASE_ROADMAP.md`
- [x] `MASTER_TODO.md` rewritten
- [x] Python package scaffold

**Exit criteria:** Docs pushed to GitHub; user confirms plan matches brief.

---

## Phase 1 — Lab toolchain bootstrap

**Goal:** Bench machine can run external tools; `handshakelab doctor` passes.

**Tasks:**

- [ ] Document apt/brew packages: `hcxdumptool`, `hcxtools`, `hashcat`, `iw`, `wireshark-common`
- [ ] Implement `doctor.py` with version checks
- [ ] Add `lab.toml.example`
- [ ] Verify adapter monitor mode on bench hardware

**Exit criteria:**

```bash
sudo handshakelab doctor
# All checks green
```

---

## Phase 2 — Capture pipeline

**Goal:** Authorized capture saves valid `capture.pcapng`.

**Tasks:**

- [ ] `config.py` + `legal.py` authorization gate
- [ ] `scan.py` passive SSID/BSSID listing
- [ ] `capture.py` hcxdumptool wrapper
- [ ] Monitor mode set/restore helpers
- [ ] EAPOL validation via tshark filter

**Exit criteria:**

```bash
sudo handshakelab capture -i wlan1 --ssid LAB-TEST --channel 6 --duration 120 --ack-authorized
# capture.pcapng exists, EAPOL frames confirmed
```

---

## Phase 3 — Convert + vault

**Goal:** PCAP converts to `.22000`; metadata in SQLite.

**Tasks:**

- [ ] `vault.py` run directories + DB migrations
- [ ] `convert.py` hcxpcapngtool integration
- [ ] `meta.json` with SHA-256 of capture
- [ ] `handshakelab list`

**Exit criteria:**

```bash
handshakelab convert latest
# crack.22000 has ≥1 hash; vault status=converted
```

---

## Phase 4 — Offline crack engine

**Goal:** Hashcat cracks lab AP with known weak password; zero online auth attempts.

**Tasks:**

- [ ] `crack.py` hashcat wrapper
- [ ] Potfile parser
- [ ] Wordlist + rules path from config
- [ ] Progress logging to `crack.log`

**Exit criteria:**

```bash
handshakelab crack latest --wordlist ./wordlists/lab-known.txt
handshakelab show latest --reveal
# Correct passphrase printed
```

---

## Phase 5 — CLI polish + QA reports

**Goal:** Single workflow usable by QA without reading source code.

**Tasks:**

- [ ] `report.py` Markdown + JSON export
- [ ] Rich terminal output (progress, colors, masked secrets)
- [ ] `HIL_CHECKLIST.md` for hardware releases
- [ ] User-facing `docs/USER_GUIDE.md`

**Exit criteria:** QA engineer completes full run from README quick start.

---

## Phase 6 — Optional local web UI

**Goal:** Browser dashboard on `127.0.0.1` for viewing runs (no capture from browser).

**Tasks:**

- [ ] FastAPI app listing vault runs
- [ ] Download artifacts
- [ ] Reveal passphrase behind confirmation modal

**Exit criteria:** `handshakelab serve` shows run table locally.

---

## Phase 7 — Packaging & CI

**Goal:** Reproducible installs; lint in CI; manual HIL for releases.

**Tasks:**

- [ ] `pyproject.toml` extras `[dev]`
- [ ] GitHub Actions: ruff + pytest (unit only)
- [ ] Tag v0.1.0 MVP

**Exit criteria:** `pip install -e .` on clean Ubuntu VM; CI green.

---

## Timeline estimate

| Phase | Effort |
| --- | --- |
| 0 | 1–2 days |
| 1 | 1 day |
| 2 | 3–5 days |
| 3 | 2 days |
| 4 | 2–3 days |
| 5 | 2 days |
| 6 | 3–5 days (optional) |
| 7 | 2–3 days |

**MVP (Phases 1–5):** ~2–3 weeks part-time.