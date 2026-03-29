"use client";

import { useState } from "react";

export function BillingActions({ mode }: { mode: "upgrade" | "manage" }) {
  const [loading, setLoading] = useState<string | null>(null);

  async function handleCheckout(interval: "month" | "year") {
    setLoading(interval);
    try {
      const res = await fetch("/api/billing/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ interval }),
      });
      const data = await res.json();
      if (data.url) {
        window.location.href = data.url;
      }
    } finally {
      setLoading(null);
    }
  }

  async function handlePortal() {
    setLoading("portal");
    try {
      const res = await fetch("/api/billing/portal", {
        method: "POST",
      });
      const data = await res.json();
      if (data.url) {
        window.location.href = data.url;
      }
    } finally {
      setLoading(null);
    }
  }

  if (mode === "manage") {
    return (
      <button
        onClick={handlePortal}
        disabled={loading === "portal"}
        className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
      >
        {loading === "portal" ? "Loading..." : "Manage Billing"}
      </button>
    );
  }

  return (
    <div className="flex flex-col gap-3 sm:flex-row">
      <button
        onClick={() => handleCheckout("month")}
        disabled={loading !== null}
        className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50"
      >
        {loading === "month" ? "Loading..." : "Upgrade — $19/mo"}
      </button>
      <button
        onClick={() => handleCheckout("year")}
        disabled={loading !== null}
        className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
      >
        {loading === "year" ? "Loading..." : "Upgrade — $149/yr"}
      </button>
    </div>
  );
}
