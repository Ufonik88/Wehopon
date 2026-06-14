import { redirect } from 'next/navigation'
import { createClient } from '@/lib/supabase/server'
import { Button } from '@/components/ui/button'
import Link from 'next/link'

export default async function DashboardPage() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) {
    redirect('/login')
  }

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-semibold tracking-tight">WeHopOn Dashboard</h1>
        <form action="/api/auth/signout" method="post">
          <Button variant="outline" type="submit">Sign out</Button>
        </form>
      </div>

      <div className="card mb-8">
        <p className="text-muted-foreground">Welcome, {user.email}</p>
        <p className="mt-2 text-sm">
          This is a Phase 1 placeholder dashboard.
        </p>
        <p className="mt-1 text-xs text-muted-foreground">
          TODO [WeHopOn]: Replace with real features (trips list, create new hop, live map, etc.) once you provide the specific concept.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="font-medium mb-2">Quick Start</h2>
          <ul className="text-sm space-y-1 text-muted-foreground">
            <li>• Your Prisma models are ready in <code>prisma/schema.prisma</code></li>
            <li>• Auth is wired via Supabase</li>
            <li>• Add your real entities (e.g. Trips, Stops, Groups)</li>
          </ul>
        </div>

        <div className="card">
          <h2 className="font-medium mb-2">Next Actions</h2>
          <div className="space-y-2">
            <Link href="/">
              <Button variant="secondary" className="w-full">Back to landing</Button>
            </Link>
            <p className="text-xs text-muted-foreground">
              Reply with your WeHopOn concept details to continue customization.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
