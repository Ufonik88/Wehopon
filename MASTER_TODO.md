# WeHopOn — MASTER_TODO.md

> **Project:** WeHopOn (Collaborative Hop-On/Hop-Off Group Travel Planner)
> **Repo:** [github.com/Ufonik88/Wehopon](https://github.com/Ufonik88/Wehopon)
> **Owner:** Ufonik · Pre-Sales Manager (Ajax Systems SSA) · Randburg, Johannesburg · GMT+2
> **Maintained by:** Entropy (Hermes Agent)
> **Last updated:** 2026-06-14
>
> **Purpose of this file:** Single source of truth for the whole WeHopOn project.
> Read this first if you are a new agent / new session picking up the work. Anything
> the user wants added to the project (features, bugs, ideas, research, experiments)
> should be appended here so the next agent has full context.

---

## 0. How to use this document

- **Top of file = current plan and active work.** Bottom of file = history / archive.
- **Status legend:** ✅ done · 🟡 in progress · ⏳ blocked · ⬜ pending · ❌ cancelled
- **Owner / agent convention:** every actionable item should have at least one of:
  - `[user]` — needs Ufonik to decide / provide input
  - `[entropy]` — Entropy (this agent) will execute
  - `[researcher]` / `[coder]` / `[planner]` — delegated subagent profile (see Hermes delegation skill)
  - `[human]` — requires action outside Hermes
- **Verification rule:** every completed item must include the actual evidence (file path, command output, URL, screenshot path). "Should be done" is not done.
- **Living project rule:** append new tasks to the **Active Backlog** section. Move items up to "Phase X" when you start them. Move them to "Done" (with date) when verified.

---

## 1. Initial Plan (the big picture)

The full initial plan lives in [`docs/TECHNICAL_BLUEPRINT.md`](docs/TECHNICAL_BLUEPRINT.md).
Quick summary of what that plan commits to:

- **Approach:** Web-first MVP, no native mobile until validation.
- **Stack (locked):** Next.js 16 (App Router) · TypeScript strict · Tailwind 4 · shadcn-ready primitives · Supabase (Auth + Realtime + Storage + Postgres) · Prisma 7 ORM · Vercel hosting.
- **Phases (5):**
  1. MVP Scoping & Setup (repo, CI, boilerplate, auth shell) ← **we are here**
  2. Backend & Database Development (schema, migrations, API, RLS, Realtime)
  3. Frontend Integration (map, trip views, real-time, optimistic UI)
  4. Testing & QA (unit, integration, e2e, a11y, security)
  5. Deployment & Launch (Vercel, Supabase prod, monitoring, analytics)
- **Risk / non-negotiables:**
  - Always verify the build (`npm run build`) before claiming a phase complete.
  - Never commit secrets; use VaultKnox or platform env vars.
  - Keep `docs/TECHNICAL_BLUEPRINT.md` and `MASTER_TODO.md` in sync with reality.
  - No feature creep until the MVP flow is verified end-to-end against a real Supabase project.

---

## 2. Current Status Snapshot

| Area | State | Evidence |
| --- | --- | --- |
| Repo created on GitHub | ✅ | `github.com/Ufonik88/Wehopon` (public, MIT) |
| Phase 1 skeleton on disk | ✅ | `/home/ufonik/wehopon/` (Next.js 16, Tailwind 4, Prisma 7, Supabase SSR) |
| Supabase wiring (clients, middleware, login/signup, signout) | ✅ | `lib/`, `middleware.ts`, `app/(auth)/`, `app/api/auth/signout/route.ts` |
| Prisma schema + config (v7) | ✅ | `prisma/schema.prisma`, `prisma.config.ts` |
| `npx prisma generate` | ✅ | exit 0, client v7.8.0 generated |
| `npm run build` | 🟡 | One known CSS issue with `bg-primary` — fix = explicit `@theme inline` block in `app/globals.css`; re-run pending |
| `npm audit fix --force` | 🟡 | 5 moderate vulns pending; queued in background |
| shadcn init | ⬜ | Deferred until after build is clean |
| Specific WeHopOn concept from user | ⬜ | **Required to move to Phase 2** |
| Vercel deploy | ⬜ | After build is clean + `.env` filled |
| Branch protection + lockdown | ⬜ | After first push so we have a `main` to protect |

---

## 3. Phase Plan (live)

### Phase 1 — MVP Scoping & Setup 🟡
- ✅ Create GitHub repo `Wehopon` under `Ufonik88`, public, MIT
- ✅ Initial commit + push of Phase 1 skeleton + blueprint + diagram
- ✅ `docs/` folder with blueprint + architecture HTML
- ✅ `MASTER_TODO.md` at repo root
- 🟡 `npm run build` green (Tailwind v4 `@theme inline` fix + re-run)
- 🟡 `npm audit fix --force` (5 moderate vulns)
- ⬜ `npx shadcn@latest init` + add `card`, `input`, `form`, `dialog`
- ⬜ `README.md` polish for first-time visitors
- ⬜ `develop` branch + branch protection on `main` (1 review, linear history, no force-push)

### Phase 2 — Backend & Database ⬜ (gated on user concept)
- ⬜ User provides the specific WeHopOn concept → customize `prisma/schema.prisma`
- ⬜ `prisma migrate dev` first migration
- ⬜ Server Actions / Route Handlers for core entities
- ⬜ RLS policies on all tables
- ⬜ Supabase Realtime subscriptions wired in app
- ⬜ Invite flow (email via Resend or Supabase)

### Phase 3 — Frontend Integration ⬜
- ⬜ Map (Mapbox or Leaflet+OSM)
- ⬜ Trip list + detail views
- ⬜ Add/edit stop modal with geocode
- ⬜ Live member locations (opt-in)
- ⬜ Optimistic updates via TanStack Query

### Phase 4 — Testing & QA ⬜
- ⬜ Vitest unit tests for utils + Zod schemas (target >70% on core)
- ⬜ Playwright e2e for auth + core trip flow
- ⬜ Lighthouse pass (Core Web Vitals)
- ⬜ axe a11y check
- ⬜ Security review: RLS, no leaked keys, no XSS in map pins

### Phase 5 — Deployment & Launch ⬜
- ⬜ Vercel project + env vars (Supabase URL/anon/service)
- ⬜ Supabase production project + RLS enabled + domain allow-list
- ⬜ Sentry (or equivalent) error monitoring
- ⬜ PostHog (or Vercel Analytics) for product analytics
- ⬜ Soft launch to beta cohort + feedback loop

---

## 4. Active Backlog (append new tasks here)

> **Add new tasks to this section.** When you start one, move it to the matching Phase above. When verified, move it to "Done".

- [ ] **[user]** Provide the specific WeHopOn concept (e.g. "group hop-on/hop-off bus tours with live GPS sharing for 5-20 people") so Phase 2 schema + flows can be customized. Until provided, the schema stays generic (User / Trip / Membership / Stop / LocationPing).
- [ ] **[entropy]** Re-run `npm run build` and verify the `@theme inline` fix actually resolves the `bg-primary` CSS error in Turbopack/Next 16.
- [ ] **[entropy]** Run `npm audit fix --force` and document the resulting dependency changes.
- [ ] **[entropy]** `npx shadcn@latest init` (or hand-roll Button/Card/Input/Form/Dialog using already-installed cva + Radix).
- [ ] **[entropy]** Add `develop` branch and apply branch protection to `main` (1 review, linear history, lock-branch, no force-push, no direct admin push).
- [ ] **[entropy]** Wire a real Supabase project (user provides credentials into `.env.local`; never committed).
- [ ] **[entropy]** Add Sentry SDK + Vercel Analytics once we have a deploy target.
- [ ] **[user]** Decide map provider: Mapbox (fast, paid above free tier) vs Leaflet+OpenStreetMap (free, no key, slower tile servers). Default: Leaflet+OSM.
- [ ] **[user]** Decide invite delivery: Resend (simple, free tier) vs Supabase Auth email templates (no extra account).
- [ ] **[user]** Confirm auth providers needed at launch: email/password, magic link, Google, Apple. Default: email/password + Google.

---

## 5. Decisions Log (locked choices — don't relitigate without reason)

| # | Decision | Rationale | Date |
| --- | --- | --- | --- |
| 1 | Web-first MVP, not mobile-first | Faster validation of core loops; mobile (PWA or RN) deferred to Phase 2/3. | 2026-06-14 |
| 2 | Next.js 16 + App Router + TypeScript strict | SSR/RSC reduce client JS; mature Supabase SSR integration. | 2026-06-14 |
| 3 | Prisma 7 + Supabase Postgres | Type-safe queries + migrations; portable (not Supabase-locked). | 2026-06-14 |
| 4 | Tailwind 4 with `@theme inline` for design tokens | Required by Tailwind v4 to expose CSS variables as utility classes (`bg-primary` etc.). | 2026-06-14 |
| 5 | TanStack Query + React Hook Form + Zod + Sonner | Standard 2026 stack for typed forms, server state, toasts. | 2026-06-14 |
| 6 | Public GitHub repo, MIT license, no branch protection yet | Solo project at Phase 1; add protection when collaborators/agents start writing. | 2026-06-14 |
| 7 | Blueprint + architecture diagram versioned in `docs/` | Keeps plan + visual discoverable on GitHub, history preserved. | 2026-06-14 |
| 8 | `MASTER_TODO.md` is the single source of truth for project state | Lets any new agent/session resume with full context instantly. | 2026-06-14 |

---

## 6. Known Pitfalls / Lessons Learned (read before changing anything)

- **Prisma 7 breaking change:** the `url` and `directUrl` fields are **no longer** in `schema.prisma`. They live in `prisma.config.ts` only. Putting them back in `schema.prisma` causes a parse error on `prisma generate`.
- **Tailwind v4 + Turbopack + Next 16:** custom utilities like `bg-primary` are **not** auto-generated from `:root` CSS variables. You **must** declare them in an `@theme inline { ... }` block in `app/globals.css`, or the build fails with `Cannot apply unknown utility class bg-primary`. Same for `text-primary-foreground`, `bg-card`, `border-border`, etc.
- **Supabase connection URLs:** use the **pooled** transaction-pooler URL (port 6543, `?pgbouncer=true`) in `DATABASE_URL` (runtime). Use the **direct** connection (port 5432) in `DIRECT_URL` for migrations and Prisma Studio. Never use the pooler URL with Prisma CLI commands.
- **`gh` is shadowed on this machine** by a Python `gh` package. Always use the Linuxbrew `gh` directly: `export PATH="/home/linuxbrew/.linuxbrew/bin:$PATH"` or call `/home/linuxbrew/.linuxbrew/bin/gh` explicitly. (Reference: `github-repo-management` skill.)
- **VaultKnox master password** must never be echoed, stored in chat, or committed. It is for vault ops only.

---

## 7. Cross-Session Continuity

- **Memory:** durable user/environment facts are in the agent's persistent memory (Ufonik preferences, Ajax brand memory, model chain).
- **Session history:** search past conversations with `session_search` for "WeHopOn" / "wehopon" / "blueprint" before asking the user for context.
- **Project context:** this file is the first thing to read after `session_search`.
- **Skills to consult when working on this project:**
  - `hermes-agent` (always)
  - `github-repo-management` (for any repo ops)
  - `github-pr-workflow` (when first PR is opened)
  - `structured-planning-and-analysis` / `planforge` (re-plan if direction changes)
  - `architecture-diagram` (if the diagram needs to be re-rendered)
  - `requesting-code-review` (before each merge)
  - `systematic-debugging` (any time a build fails)
  - `karpathy-principles` (design quality bar)

---

## 8. Done (archive — keep for history)

- 2026-06-14 — Researched and produced the full Technical Blueprint (5 sections per user brief) and dark-themed architecture diagram.
- 2026-06-14 — Bootstrapped `/home/ufonik/wehopon` (Next.js 16 + TS + Tailwind 4 + Supabase SSR + Prisma 7 + Zod + RHF + TanStack Query + Sonner + lucide + date-fns).
- 2026-06-14 — Fixed Prisma 7 `url`/`directUrl` removal (moved to `prisma.config.ts`).
- 2026-06-14 — Fixed Tailwind v4 custom utility resolution with `@theme inline` in `app/globals.css`.
- 2026-06-14 — Installed UI deps: `class-variance-authority`, `@radix-ui/react-slot`, `clsx`, `tailwind-merge`.
- 2026-06-14 — Wired Supabase auth: server + browser clients, middleware session refresh, `(auth)/login` + `(auth)/signup` + `api/auth/signout`, protected `/dashboard`.
- 2026-06-14 — Added db helper scripts: `db:generate`, `db:migrate`, `db:push`, `db:studio`.
- 2026-06-14 — Created GitHub repo `Ufonik88/Wehopon` (public, MIT) and pushed Phase 1 skeleton + `docs/` + `MASTER_TODO.md`.
- 2026-06-14 — Security audit before push: no leaked secrets, no real API keys, only local home-path references in `.planning/STATE.md` (rewritten to be relative before push).
