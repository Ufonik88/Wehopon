import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function WeHopOnLanding() {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-border">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-2">
            <div className="h-6 w-6 rounded bg-primary" />
            <span className="font-semibold tracking-tight text-xl">WeHopOn</span>
          </div>
          <div className="flex items-center gap-4 text-sm">
            <Link href="/login" className="text-muted-foreground hover:text-foreground">Log in</Link>
            <Link href="/signup">
              <Button>Get started</Button>
            </Link>
          </div>
        </div>
      </header>

      <main className="flex flex-1 flex-col items-center justify-center px-6 text-center">
        <div className="max-w-2xl">
          <div className="mb-4 inline-block rounded-full bg-muted px-3 py-1 text-xs uppercase tracking-[2px] text-muted-foreground">
            MVP Blueprint • Web-first
          </div>
          <h1 className="text-6xl font-semibold tracking-tighter">
            Adventures.<br />Together.<br />In real time.
          </h1>
          <p className="mt-6 max-w-md mx-auto text-lg text-muted-foreground">
            [WeHopOn placeholder] — Collaborative group adventures with live coordination.
            This is the starting skeleton from the technical blueprint.
          </p>

          <div className="mt-10 flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/signup">
              <Button size="lg" className="gap-2">
                Start a hop <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <Link href="https://github.com">
              <Button variant="outline" size="lg">View blueprint</Button>
            </Link>
          </div>

          <p className="mt-12 text-[10px] uppercase tracking-[3px] text-muted-foreground">
            Built from the WeHopOn Technical Blueprint • Phase 1 skeleton
          </p>
        </div>
      </main>

      <footer className="border-t border-border py-8 text-center text-xs text-muted-foreground">
        Phase 1 complete when: auth wired • Prisma + Supabase connected • basic protected routes • CI green
      </footer>
    </div>
  );
}
