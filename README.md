# WeHopOn

**Status:** Phase 1 skeleton (from the Technical Blueprint in [`docs/TECHNICAL_BLUEPRINT.md`](docs/TECHNICAL_BLUEPRINT.md))

> A collaborative hop-on/hop-off group travel planner.
> Built with Next.js 16 + Supabase + Prisma + Tailwind 4.

## Architecture

System architecture diagram (dark theme, generated via the `architecture-diagram` skill):
[`docs/architecture.html`](docs/architecture.html) — open in a browser for the full colour-coded flow.

## Quick Start

```bash
cp .env.example .env.local   # Fill in Supabase + DATABASE_URL values
npm install                   # Already done if you cloned the repo
npx prisma generate
npm run dev
```

Visit <http://localhost:3000> → `/login` or `/signup` → protected `/dashboard`.

## Current Stack (per blueprint, web-first)

- **Frontend:** Next.js 16 (App Router) · TypeScript strict · Tailwind 4 · shadcn-ready primitives (cva + Radix Slot + lucide)
- **Backend:** Next.js Server Actions + Route Handlers · Supabase (Auth + Realtime + Storage) · Prisma 7 ORM
- **Database:** Supabase Postgres (pooler URL for runtime, direct URL for migrations)
- **Forms / Data:** React Hook Form · Zod · TanStack Query · Sonner toasts
- **Hosting (target):** Vercel + Supabase
- **CI:** GitHub Actions (see `.github/workflows/`)

## Commands

| Script | Purpose |
| --- | --- |
| `npm run dev` | Local dev server (Turbopack) |
| `npm run build` | Production build |
| `npm run start` | Run production build |
| `npm run lint` | ESLint |
| `npm run db:generate` | `prisma generate` |
| `npm run db:migrate` | `prisma migrate dev` |
| `npm run db:push` | `prisma db push` (skip migrations) |
| `npm run db:studio` | Open Prisma Studio |

## Project Layout

```
wehopon/
├── app/                    # Next.js App Router
│   ├── (auth)/             # login / signup (group route)
│   ├── api/                # route handlers (auth, signout)
│   ├── dashboard/          # protected dashboard
│   ├── globals.css         # Tailwind v4 + @theme inline tokens
│   ├── layout.tsx
│   └── page.tsx            # landing
├── components/             # shared UI (Button, etc.)
├── lib/                    # clients (supabase server/browser), utils
├── prisma/
│   └── schema.prisma       # Prisma 7 schema (generic, ready to specialize)
├── docs/
│   ├── TECHNICAL_BLUEPRINT.md
│   └── architecture.html
├── .planning/              # STATE.md + project tracking
├── middleware.ts           # Supabase session refresh
├── prisma.config.ts        # Prisma 7 config (DATABASE_URL + DIRECT_URL)
├── .env.example
├── .github/workflows/      # CI
└── package.json
```

## Documentation

- [`docs/TECHNICAL_BLUEPRINT.md`](docs/TECHNICAL_BLUEPRINT.md) — full Discovery / Architecture / Design / Roadmap plan
- [`docs/architecture.html`](docs/architecture.html) — system architecture diagram
- [`.planning/STATE.md`](.planning/STATE.md) — current execution state
- [`MASTER_TODO.md`](MASTER_TODO.md) — project-wide task ledger (use this for cross-agent context)

## Security

- **Never commit real secrets.** `.env*` is git-ignored. Use VaultKnox or platform env vars in production.
- Supabase RLS policies must be enabled before exposing any table to the client.
- Service-role key (`SUPABASE_SERVICE_ROLE_KEY`) is server-only.

## License

MIT
