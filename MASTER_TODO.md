# HandshakeLab — MASTER_TODO.md

> **Product:** HandshakeLab — offline WiFi handshake capture & crack workstation for authorized product testing  
> **Repo:** [github.com/Ufonik88/Wehopon](https://github.com/Ufonik88/Wehopon)  
> **Owner:** Ufonik  
> **Last updated:** 2026-06-14  
>
> **Purpose:** Single source of truth. Read this first in every new session.
> The previous travel-planner content was built from the wrong brief and has been removed.

---

## 0. How to use this document

- **Status legend:** ✅ done · 🟡 in progress · ⏳ blocked · ⬜ pending · ❌ cancelled
- **Owners:** `[user]` · `[agent]` · `[human]`
- **Verification rule:** completed items need evidence (file path, command output).
- Append new tasks to **Active Backlog**.

---

## 1. Original brief (source of truth)

Build an app for **authorized product testing** that:

1. Captures WiFi authentication material (handshake / PMKID) from the air
2. Saves it locally (`.pcapng` + crack-ready hash)
3. Cracks **offline** — no repeated failed logins against the AP/router
4. Shows the recovered password so the tester can **manually enter it** and join the network on the device under test

---

## 2. Current status snapshot

| Area | State | Evidence |
| --- | --- | --- |
| Wrong travel app removed | 🟡 | In progress this session |
| Planning docs written | ✅ | `docs/PROJECT_PLAN.md`, blueprint, architecture, legal, hardware, roadmap |
| Python scaffold | 🟡 | `src/handshakelab/` |
| Capture pipeline | ⬜ | Phase 2 |
| Offline crack | ⬜ | Phase 4 |
| Lab hardware verified | ⬜ | Needs USB adapter check on bench |

**Current phase:** 0 — Planning complete, starting Phase 1 next.

---

## 3. Phase plan (live)

### Phase 0 — Planning & documentation 🟡
- ✅ Rewrite all docs to match WiFi audit brief
- ✅ Replace `MASTER_TODO.md`, `README.md`, `AGENTS.md`
- 🟡 Remove Next.js travel skeleton from repo
- 🟡 Push redesigned plan to GitHub
- ⬜ User confirms plan + open decisions (repo rename, deauth module, wordlist source)

### Phase 1 — Lab toolchain bootstrap ⬜
- ⬜ `handshakelab doctor` preflight command
- ⬜ `lab.toml.example` with allow-list template
- ⬜ `docs/USER_GUIDE.md` install section
- ⬜ Verify monitor-mode adapter on bench

### Phase 2 — Capture pipeline ⬜
- ⬜ Authorization gate (`lab.toml` + `--ack-authorized`)
- ⬜ `handshakelab scan`
- ⬜ `handshakelab capture` (hcxdumptool)
- ⬜ EAPOL validation

### Phase 3 — Convert + vault ⬜
- ⬜ SQLite vault + `captures/<run-id>/` layout
- ⬜ `handshakelab convert` (pcapng → .22000)
- ⬜ `handshakelab list`

### Phase 4 — Offline crack ⬜
- ⬜ `handshakelab crack` (hashcat -m 22000)
- ⬜ `handshakelab show --reveal`
- ⬜ Confirm zero online auth attempts during crack

### Phase 5 — CLI polish + reports ⬜
- ⬜ `handshakelab report` (Markdown/JSON)
- ⬜ `docs/HIL_CHECKLIST.md`
- ⬜ End-to-end QA run from README

### Phase 6 — Optional local web UI ⬜
- ⬜ FastAPI on 127.0.0.1 for run history

### Phase 7 — Packaging & CI ⬜
- ⬜ GitHub Actions (ruff + pytest)
- ⬜ Tag v0.1.0

---

## 4. Active backlog

- [ ] **[user]** Confirm: keep GitHub repo name `Wehopon` or rename to `HandshakeLab`?
- [ ] **[user]** Confirm: include optional controlled deauth module (lab-only, off by default)?
- [ ] **[user]** Provide/path to internal QA wordlist (not committed to git).
- [ ] **[user]** Confirm USB WiFi adapter model on bench (or purchase from HARDWARE.md list).
- [ ] **[agent]** Implement `doctor.py` + CLI entrypoint (Phase 1).
- [ ] **[agent]** Add `lab.toml.example` and authorization gate stubs.
- [ ] **[agent]** Update GitHub Actions for Python project.

---

## 5. Decisions log

| # | Decision | Rationale | Date |
| --- | --- | --- | --- |
| 1 | Product name: **HandshakeLab** | Describes capture→offline crack workflow | 2026-06-14 |
| 2 | Stack: Python CLI + hcxtools + Hashcat | Linux-native; needs root/monitor mode | 2026-06-14 |
| 3 | Remove Next.js / Supabase / Prisma skeleton | Wrong project entirely | 2026-06-14 |
| 4 | Offline crack only; no auto-join | Matches brief; avoids AP lockouts | 2026-06-14 |
| 5 | `lab.toml` allow-list required | Legal/ethical guardrail | 2026-06-14 |
| 6 | Deauth disabled by default | Disruptive; lab-only opt-in | 2026-06-14 |
| 7 | WPA2-PSK first; WPA3 later | MVP feasibility | 2026-06-14 |

---

## 6. Pitfalls / lessons

- **Previous repo was wrong:** WeHopOn travel planner ≠ WiFi testing tool. Always validate brief against `MASTER_TODO.md` §1.
- **Browser apps cannot capture WiFi:** monitor mode requires native Linux + root.
- **Never commit:** captures, potfiles, wordlists, recovered passphrases.
- **`gh` shadowed on bench:** use `/home/linuxbrew/.linuxbrew/bin/gh` if pushing from this machine.

---

## 7. Done (archive)

- 2026-06-14 — User clarified actual brief: WiFi handshake capture + offline crack for product testing.
- 2026-06-14 — Wrote full planning doc set under `docs/`.
- 2026-06-14 — Rewrote `MASTER_TODO.md` to reflect HandshakeLab.