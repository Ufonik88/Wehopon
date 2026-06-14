# HandshakeLab — Project Plan

**Product:** HandshakeLab (offline WiFi credential recovery for authorized product testing)  
**Repository:** [github.com/Ufonik88/Wehopon](https://github.com/Ufonik88/Wehopon)  
**Owner:** Ufonik  
**Status:** Phase 0 — Planning (2026-06-14)  
**Platform:** Linux workstation (primary), lab APs under test

---

## 1. Executive summary

HandshakeLab is a **local-first WiFi security testing workstation** for product QA and penetration testing on **networks and equipment you own or have written authorization to test**.

The tool follows the workflow you described:

1. **Capture** a WPA/WPA2/WPA3 authentication handshake (or PMKID) from the air — one passive or controlled capture session.
2. **Save** the capture locally as a `.pcapng` file and a crack-ready hash file (`.22000` for Hashcat).
3. **Crack offline** on the workstation CPU/GPU — no repeated failed association attempts against the AP/router.
4. **Reveal** the recovered passphrase so a tester can **manually type it** into the device under test and verify join behavior.

This design deliberately **avoids online brute force** (repeated `wpa_supplicant` or PIN attempts), which triggers lockouts, pollutes lab logs, and can destabilize embedded AP firmware during product testing.

> **Scope boundary:** HandshakeLab is not a cloud service, not a phone app, and not a travel planner. The previous repo contents (Next.js travel skeleton) were built from the wrong brief and are being replaced.

---

## 2. Problem statement

### What product testers need

When validating WiFi-enabled hardware (cameras, hubs, sensors, routers, guest portals), testers often need to confirm:

- Default or provisioning passwords are not weak.
- WPA2/WPA3 PSK rotation works end-to-end.
- Devices join correctly once the correct passphrase is known.
- Firmware handles **correct** credentials (not hundreds of **wrong** ones).

### What goes wrong today

| Approach | Problem |
| --- | --- |
| Manual guessing | Slow, pollutes test notes, easy to typo |
| Online brute force against AP | Router lockouts, WIPS alerts, flaky embedded APs, illegal on third-party networks |
| Ad-hoc scripts | Fragile toolchain (aircrack vs hashcat formats), no audit trail, hard to repeat in QA |
| Full pentest distros (Kali) | Heavy, not tailored to repeatable product test runs |

### What success looks like

A tester can run a **single documented command sequence**, produce an **artifact folder** per AP under test, crack offline, and record: capture hash, crack method, recovered passphrase (encrypted at rest), verification timestamp, and adapter/firmware notes.

---

## 3. Users and use cases

### Primary persona: Product QA / Pre-sales lab engineer

- Tests Ajax Systems or customer-owned lab equipment.
- Has a dedicated Linux bench machine and a monitor-mode-capable USB adapter.
- Needs repeatable runs per firmware build.

### Core use cases

| ID | Use case | Outcome |
| --- | --- | --- |
| UC-1 | Capture handshake on lab AP `SSID-LAB-01` | `.pcapng` + `.22000` saved under `captures/` |
| UC-2 | Crack capture with company wordlist | Passphrase displayed once; copied manually into DUT |
| UC-3 | Import existing `.pcap` from external tool | Conversion + offline crack without re-capture |
| UC-4 | Generate QA report | JSON/Markdown summary: SSID, BSSID, crack time, method |
| UC-5 | Verify "weak password" policy | Confirm dictionary crack succeeds under N seconds |

### Explicit non-goals (v1)

- Attacking networks without authorization
- Distributed/cloud cracking
- Automated connection to cracked networks (manual entry only by design)
- Windows/macOS capture support (Linux first)
- WPS PIN online attack (out of scope; causes AP-side throttling)

---

## 4. Solution overview

### The four-stage pipeline

```
┌─────────────┐    ┌──────────────┐    ┌────────────────┐    ┌──────────────┐
│  1. CAPTURE │ -> │ 2. NORMALIZE │ -> │ 3. CRACK       │ -> │ 4. REVEAL    │
│  monitor    │    │ pcap -> hash │    │ hashcat offline│    │ show password│
│  mode sniff │    │ local vault  │    │ wordlist/rules │    │ manual join  │
└─────────────┘    └──────────────┘    └────────────────┘    └──────────────┘
```

### Design principles

1. **Offline cracking only** — the AP sees at most one controlled capture window, not a login storm.
2. **Artifacts are first-class** — every run produces a folder: `captures/<run-id>/`.
3. **CLI-first, UI optional** — scriptable for CI-style lab benches; optional local web dashboard later.
4. **Fail closed on legal guardrails** — require `--i-own-this-network` or signed lab config before capture modules load.
5. **Pluggable backends** — Hashcat primary; John the Ripper fallback; aircrack-ng for legacy `.hccapx`.

---

## 5. Technical approach

### Recommended stack (locked for v1)

| Layer | Choice | Rationale |
| --- | --- | --- |
| Language | Python 3.11+ | Orchestration, parsing, QA integration |
| CLI | `typer` + `rich` | Typed commands, readable lab output |
| Capture | `hcxdumptool` + `iw`/`nmcli` | Modern PMKID + handshake capture |
| Conversion | `hcxpcapngtool` (hcxtools) | Stable `.22000` export for Hashcat |
| Cracking | Hashcat (GPU optional) | Industry standard offline WPA-PBKDF2 |
| Storage | SQLite + local filesystem | No cloud; audit trail per run |
| Config | TOML lab profile | SSID allow-list, adapter name, wordlist paths |
| Packaging | `pip install -e .` | Simple bench setup |

### Why not Next.js / Supabase?

WiFi monitor mode requires **root**, **raw sockets**, and **Linux nl80211** APIs. A browser app cannot do this. The old stack is removed.

### Capture modes

| Mode | When to use | Notes |
| --- | --- | --- |
| **Passive handshake** | Client already associating | Safest; wait for natural 4-way handshake |
| **PMKID** | WPA2 APs with usable frames | Often faster than full handshake |
| **Controlled deauth** | Authorized lab only, no active clients | Documented in `LEGAL_AND_ETHICS.md`; disabled by default |

### Output formats

```
captures/
└── 2026-06-14T103000Z_lab-ap-01/
    ├── meta.json           # SSID, BSSID, channel, adapter, operator
    ├── capture.pcapng      # raw evidence
    ├── crack.22000         # hashcat input
    ├── crack.log           # hashcat stdout/stderr
    └── result.json         # status, passphrase (optional AES wrap)
```

---

## 6. System architecture (summary)

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for full detail and [`architecture.html`](architecture.html) for the visual diagram.

**Modules:**

- `handshakelab.scan` — passive SSID/BSSID enumeration
- `handshakelab.capture` — orchestrate hcxdumptool / airodump-ng
- `handshakelab.convert` — pcapng → 22000
- `handshakelab.crack` — invoke hashcat with job files
- `handshakelab.vault` — SQLite metadata + optional passphrase encryption
- `handshakelab.report` — Markdown/JSON QA report
- `handshakelab.cli` — `handshakelab capture|convert|crack|show|report`

---

## 7. Security, legal, and ethics

**Read [`LEGAL_AND_ETHICS.md`](LEGAL_AND_ETHICS.md) before any capture work.**

Minimum controls:

- Written authorization for every target SSID in lab config.
- Default deny for capture without lab profile.
- Passphrase displayed only to terminal user (or encrypted export).
- Audit log: who ran capture, when, which BSSID.
- No auto-join — manual entry prevents accidental production network joins.

Unauthorized access to computer networks is illegal in most jurisdictions (e.g., UK Computer Misuse Act, US CFAA, SA ECT Act). This tool is for **your lab**.

---

## 8. Hardware requirements

See [`HARDWARE.md`](HARDWARE.md).

Minimum lab setup:

- Linux host (kernel 6.x, your bench machine qualifies)
- USB WiFi adapter with **monitor mode** and **frame injection** (e.g., Alfa AWUS036ACH, AWUS036NHA — verify with `iw list`)
- Separate management interface for internet (do not use the same adapter)
- Optional: NVIDIA GPU for Hashcat acceleration

---

## 9. Implementation phases

See [`PHASE_ROADMAP.md`](PHASE_ROADMAP.md) for acceptance criteria per phase.

| Phase | Name | Duration (est.) |
| --- | --- | --- |
| 0 | Planning & documentation | 1–2 days ← **current** |
| 1 | Lab toolchain bootstrap | 1 day |
| 2 | Capture pipeline | 3–5 days |
| 3 | Convert + vault | 2 days |
| 4 | Offline crack engine | 2–3 days |
| 5 | CLI polish + reports | 2 days |
| 6 | Optional local web UI | 3–5 days |
| 7 | QA hardening + packaging | 2–3 days |

**Total to MVP:** ~2–3 weeks part-time on one bench.

---

## 10. Risks and mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Adapter lacks monitor mode | Cannot capture | Hardware compatibility matrix + preflight check |
| WPA3-only SA networks | Handshake crack harder | Document PMKID/SAE limitations; test AP downgrade in lab |
| GPU drivers missing | Slow cracks | CPU mode + small wordlists for CI smoke tests |
| Legal misuse | Criminal liability | Authorization gate + prominent docs |
| hcxdumptool permissions | Fails without root | `sudo` wrapper with capability check |
| False positives in capture | Wasted crack time | Validator: confirm EAPOL frames before convert |

---

## 11. Testing strategy

### Lab fixtures

- Dedicated test AP (open/WPA2/WPA3 profiles)
- Known password list: `LabTest2026!`, `ajax-qa-weak`, etc.
- Golden capture files checked into `tests/fixtures/` (synthetic, not from real deployments)

### Test layers

1. **Unit** — parsers, path layout, config validation
2. **Integration** — convert fixture pcap → crack with tiny wordlist
3. **Hardware-in-loop** — manual checklist per release on real adapter
4. **Regression** — hashcat version pinned in CI where GPU available

---

## 12. Deliverables checklist (Phase 0)

- [x] `docs/PROJECT_PLAN.md` (this file)
- [x] `docs/TECHNICAL_BLUEPRINT.md`
- [x] `docs/ARCHITECTURE.md`
- [x] `docs/LEGAL_AND_ETHICS.md`
- [x] `docs/HARDWARE.md`
- [x] `docs/PHASE_ROADMAP.md`
- [x] `MASTER_TODO.md` rewritten
- [x] `README.md` rewritten
- [x] Python package scaffold (`src/handshakelab/`)
- [ ] Phase 1: working `handshakelab doctor` preflight command

---

## 13. Open decisions (need your input)

| # | Decision | Default if no answer |
| --- | --- | --- |
| 1 | Product name on GitHub: keep repo `Wehopon` or rename to `HandshakeLab`? | Keep repo name; product branded HandshakeLab |
| 2 | GPU cracking in lab? | Hashcat with OpenCL; CPU fallback |
| 3 | Include controlled deauth module? | Off by default; lab flag only |
| 4 | Encrypt stored passphrases at rest? | Yes, optional GPG or local key file |
| 5 | Wordlist source | Ship none; point to your internal Ajax QA list |

---

## 14. References

- [Hashcat WPA mode 22000](https://hashcat.net/wiki/doku.php?id=cracking_wpawpa2)
- [hcxtools / hcxdumptool](https://github.com/ZerBea/hcxtools)
- [Aircrack-ng documentation](https://www.aircrack-ng.org/)
- [IEEE 802.11i 4-way handshake](https://en.wikipedia.org/wiki/IEEE_802.11i-2004)