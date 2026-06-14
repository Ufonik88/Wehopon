# HandshakeLab Current State

**Current Phase:** 5 — MVP implemented (v0.1.0); HIL verification next  
**Last Updated:** 2026-06-14  
**Product:** HandshakeLab (WiFi handshake capture + offline crack, Linux + macOS)

## Critical context

The repository previously contained a **WeHopOn travel planner** (Next.js + Supabase). That was built from the **wrong brief**. The project has been **completely redesigned** around the user's actual requirement:

> Capture WiFi handshake → save locally → crack offline → show password for manual device join.

## Completed (Phase 0)

- Full planning documentation in `docs/`
- `MASTER_TODO.md` rewritten
- Python package scaffold added
- Next.js travel skeleton removed

## Next up

- User HIL test on lab AP (Linux and/or Mac)
- Optional Phase 6 local web UI

## Key docs

- [`docs/PROJECT_PLAN.md`](../docs/PROJECT_PLAN.md)
- [`docs/TECHNICAL_BLUEPRINT.md`](../docs/TECHNICAL_BLUEPRINT.md)
- [`MASTER_TODO.md`](../MASTER_TODO.md)