"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import { useTheme } from "@/components/theme/ThemeProvider";

function ModeToggle() {
  const { mode, setMode } = useTheme();
  return (
    <div
      style={{
        display: 'flex',
        border: '1px solid var(--border)',
        borderRadius: 7,
        overflow: 'hidden',
      }}
    >
      <button
        onClick={() => setMode('light')}
        style={{
          padding: '4px 10px',
          fontSize: 11,
          background: mode === 'light' ? 'var(--accent)' : 'transparent',
          border: 'none',
          cursor: 'pointer',
          fontFamily: "'JetBrains Mono', monospace",
          color: mode === 'light' ? 'var(--btn-fg)' : 'var(--text3)',
          fontWeight: mode === 'light' ? 600 : 400,
          lineHeight: 1,
          transition: 'background 0.15s, color 0.15s',
        }}
      >
        ☀ Light
      </button>
      <button
        onClick={() => setMode('dark')}
        style={{
          padding: '4px 10px',
          fontSize: 11,
          background: mode === 'dark' ? 'var(--accent)' : 'transparent',
          border: 'none',
          cursor: 'pointer',
          fontFamily: "'JetBrains Mono', monospace",
          color: mode === 'dark' ? 'var(--btn-fg)' : 'var(--text3)',
          fontWeight: mode === 'dark' ? 600 : 400,
          lineHeight: 1,
          transition: 'background 0.15s, color 0.15s',
        }}
      >
        ☽ Dark
      </button>
    </div>
  );
}

export function AppNav({ userEmail }: { userEmail: string | null }) {
  const router = useRouter();
  const supabase = createClient();

  async function handleSignOut() {
    await supabase.auth.signOut();
    router.push("/");
    router.refresh();
  }

  return (
    <header
      style={{
        position: 'sticky',
        top: 0,
        zIndex: 20,
        height: 52,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 28px',
        borderBottom: '1px solid var(--border)',
        background: 'var(--header-bg)',
        backdropFilter: 'blur(10px)',
        transition: 'background 0.25s, border-color 0.25s',
      }}
    >
      <Link
        href={userEmail ? "/app" : "/"}
        style={{
          color: 'var(--accent)',
          fontSize: 11,
          letterSpacing: '0.22em',
          textTransform: 'uppercase',
          fontWeight: 600,
          textDecoration: 'none',
          fontFamily: "'JetBrains Mono', monospace",
        }}
      >
        CarvAcoustic
      </Link>
      <nav style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <Link
          href="/pricing"
          style={{ color: 'var(--text3)', fontSize: 10, letterSpacing: '0.1em', textDecoration: 'none', transition: 'color 0.15s' }}
        >
          Pricing
        </Link>
        <Link
          href="/docs"
          style={{ color: 'var(--text3)', fontSize: 10, letterSpacing: '0.1em', textDecoration: 'none', transition: 'color 0.15s' }}
        >
          Docs
        </Link>
        {userEmail && (
          <Link
            href="/app/billing"
            style={{ color: 'var(--text3)', fontSize: 10, letterSpacing: '0.1em', textDecoration: 'none', transition: 'color 0.15s' }}
          >
            Billing
          </Link>
        )}
        <ModeToggle />
        {userEmail && (
          <span style={{ color: 'var(--text4)', fontSize: 9, letterSpacing: '0.05em' }}>
            {userEmail}
          </span>
        )}
        <button
          onClick={handleSignOut}
          style={{
            color: 'var(--text3)',
            fontSize: 10,
            letterSpacing: '0.1em',
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            fontFamily: "'JetBrains Mono', monospace",
            transition: 'color 0.15s',
          }}
        >
          Sign out
        </button>
      </nav>
    </header>
  );
}
