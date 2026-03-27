"use client";

import { useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

// useSearchParams() requires a Suspense boundary in Next.js 14 App Router.
// Without it the page fails during prerendering ("Load failed" in browser).
function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirectTo = searchParams.get("redirectTo") ?? "/app";

  const [mode, setMode] = useState<"signin" | "signup">("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [checkEmail, setCheckEmail] = useState(false);

  const supabase = createClient();

  async function handleEmailPassword(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (mode === "signup") {
        const { data, error } = await supabase.auth.signUp({ email, password });
        if (error) throw error;

        if (!data.session) {
          // Email confirmation is enabled — user must confirm before signing in.
          setCheckEmail(true);
          return;
        }
        // Confirmation disabled: signUp already returned a session — go straight in.
      } else {
        const { error } = await supabase.auth.signInWithPassword({
          email,
          password,
        });
        if (error) throw error;
      }
      router.push(redirectTo);
      router.refresh();
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : "Authentication failed.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  async function handleMagicLink(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const { error } = await supabase.auth.signInWithOtp({
        email,
        options: {
          emailRedirectTo: `${window.location.origin}${redirectTo}`,
        },
      });
      if (error) throw error;
      setCheckEmail(true);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to send link.");
    } finally {
      setLoading(false);
    }
  }

  if (checkEmail) {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center px-4">
        <div className="w-full max-w-sm rounded-lg border border-gray-200 bg-white p-8 text-center shadow-sm">
          <h1 className="text-xl font-semibold text-gray-900">Check your email</h1>
          <p className="mt-2 text-sm text-gray-500">
            We sent a link to <strong>{email}</strong>. Click it to continue.
          </p>
          <button
            onClick={() => setCheckEmail(false)}
            className="mt-4 text-sm text-brand-600 hover:underline"
          >
            Use a different email
          </button>
        </div>
      </main>
    );
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <Link href="/" className="text-sm font-semibold text-gray-900">
            CarvAcoustic
          </Link>
          <h1 className="mt-4 text-2xl font-bold text-gray-900">
            {mode === "signin" ? "Sign in" : "Create account"}
          </h1>
        </div>

        <div className="rounded-lg border border-gray-200 bg-white p-8 shadow-sm">
          <form onSubmit={handleEmailPassword} className="flex flex-col gap-4">
            <Input
              label="Email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            <Input
              label="Password"
              type="password"
              autoComplete={
                mode === "signup" ? "new-password" : "current-password"
              }
              required
              minLength={6}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />

            {error && (
              <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-600">
                {error}
              </p>
            )}

            <Button type="submit" loading={loading} className="w-full">
              {mode === "signin" ? "Sign in" : "Create account"}
            </Button>
          </form>

          <div className="mt-4 flex items-center gap-3">
            <div className="h-px flex-1 bg-gray-200" />
            <span className="text-xs text-gray-400">or</span>
            <div className="h-px flex-1 bg-gray-200" />
          </div>

          <form onSubmit={handleMagicLink} className="mt-4">
            <Button
              type="submit"
              variant="secondary"
              loading={loading}
              className="w-full"
              disabled={!email}
            >
              Send magic link
            </Button>
          </form>
        </div>

        <p className="mt-6 text-center text-sm text-gray-500">
          {mode === "signin" ? (
            <>
              No account?{" "}
              <button
                onClick={() => setMode("signup")}
                className="text-brand-600 hover:underline"
              >
                Create one
              </button>
            </>
          ) : (
            <>
              Already have an account?{" "}
              <button
                onClick={() => setMode("signin")}
                className="text-brand-600 hover:underline"
              >
                Sign in
              </button>
            </>
          )}
        </p>
      </div>
    </main>
  );
}

export default function LoginPage() {
  return (
    <Suspense>
      <LoginForm />
    </Suspense>
  );
}
