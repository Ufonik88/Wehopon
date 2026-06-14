import { defineConfig } from "prisma/config"

export default defineConfig({
  schema: "prisma/schema.prisma",
  // Connection strings are now provided via environment variables at runtime / CLI
  // For migrations, set DATABASE_URL to your direct (non-pooled) connection string
  // For app runtime with Supabase, use the pooled transaction URL in DATABASE_URL
})