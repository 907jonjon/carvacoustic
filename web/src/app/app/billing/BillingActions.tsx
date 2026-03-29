"use client";

import { useState } from "react";

export function BillingActions({ mode }: { mode: "upgrade" | "manage" }) {
  const [loading, setLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleCheckout(interval: "monthly" | "yearly") {
    setLoading(interval);
    setError(null);
    try {
      const res = await fetch("/api/billing/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ interval }),
      });
      const data = await res.json();
      if (data.url) {
        window.location.href = data.url;
      } else {
        setError(data.error?.message ?? "Failed to start checkout.");
      }
    } catch {
      setError("Network error. Please try again.");
    } finally {
      setLoading(null);
    }
  }

  async function handlePortal() {
    setLoading("portal");
    setError(null);
    try {
      const res = await fetch("/api/billing/portal", {
        method: "POST",
      });
      const data = await res.json();
      if (data.url) {
        window.location.href = data.url;
      } else {
        setError(data.error?.message ?? "Failed to open billing portal.");
      }
    } catch {
      setError("Network error. Please try again.");
    } finally {
      setLoading(null);
    }
  }

  if (mode === "manage") {
    return (
      <div className="flex flex-col gap-2">
        <button
          onClick={handlePortal}
          disabled={loading === "portal"}
          className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
        >
          {loading === "portal" ? "Loading..." : "Manage Billing"}
        </button>
        {error && <p className="text-sm text-red-600">{error}</p>}
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      {error && <p className="text-sm text-red-600">{error}</p>}
      <div className="flex flex-col gap-3 sm:flex-row">
      <button
        onClick={() => handleCheckout("monthly")}
        disabled={loading !== null}
        className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50"
      >
        {loading === "monthly" ? "Loading..." : "Upgrade — $19/mo"}
      </button>
      <button
        onClick={() => handleCheckout("yearly")}
        disabled={loading !== null}
        className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
      >
        {loading === "yearly" ? "Loading..." : "Upgrade — $149/yr"}
      </button>
      </div>
    </div>
  );
}
