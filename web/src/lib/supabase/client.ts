import { createBrowserClient } from "@supabase/ssr";
import type { Database } from "@/types/database";

/**
 * Browser-side Supabase client.
 * Use this in Client Components ("use client").
 *
 * The guard is inside the function (not at module level) so that Next.js
 * can import this file during SSR without crashing — the throw only fires
 * when the client is actually instantiated in the browser.
 */
export function createClient() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  if (
    !url || !key ||
    url === "https://your-project.supabase.co" ||
    key === "your-anon-key"
  ) {
    throw new Error(
      "Supabase env vars are missing or still placeholder values. " +
      "Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY " +
      "in web/.env.local, then restart the dev server."
    );
  }

  return createBrowserClient<Database>(url, key);
}
