"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";

export function AppNav({ userEmail }: { userEmail: string | null }) {
  const router = useRouter();
  const supabase = createClient();

  async function handleSignOut() {
    await supabase.auth.signOut();
    router.push("/");
    router.refresh();
  }

  return (
    <nav className="flex h-14 items-center justify-between border-b border-gray-200 bg-white px-6">
      <Link
        href="/app"
        className="text-sm font-semibold text-gray-900 hover:text-brand-600"
      >
        CarvAcoustic
      </Link>
      <div className="flex items-center gap-4">
        <Link href="/pricing" className="text-sm text-gray-500 hover:text-gray-700">
          Pricing
        </Link>
        <Link href="/docs" className="text-sm text-gray-500 hover:text-gray-700">
          Docs
        </Link>
        {userEmail && (
          <Link href="/app/billing" className="text-sm text-gray-500 hover:text-gray-700">
            Billing
          </Link>
        )}
        {userEmail && (
          <span className="text-xs text-gray-500 hidden sm:block">
            {userEmail}
          </span>
        )}
        <button
          onClick={handleSignOut}
          className="text-sm text-gray-600 hover:text-gray-900"
        >
          Sign out
        </button>
      </div>
    </nav>
  );
}
