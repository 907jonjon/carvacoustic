"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import type { ProjectMode, Units } from "@/types/schema";

const MODE_OPTIONS: { value: ProjectMode; label: string }[] = [
  { value: "wall_art", label: "Wall Art" },
  { value: "cabinet_front_panel", label: "Cabinet Front Panel" },
  { value: "architectural_face_panel", label: "Architectural Face Panel" },
];

const UNIT_OPTIONS: { value: Units; label: string }[] = [
  { value: "in", label: "Inches (in)" },
  { value: "mm", label: "Millimetres (mm)" },
];

export default function NewProjectPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [mode, setMode] = useState<ProjectMode>("wall_art");
  const [units, setUnits] = useState<Units>("in");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const res = await fetch("/api/projects", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, mode, units }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data?.error?.message ?? "Failed to create project.");
      }

      router.push(`/app/projects/${data.id}/edit`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto w-full max-w-lg px-6 py-10">
      <div className="mb-6">
        <Link
          href="/app"
          className="text-sm text-gray-500 hover:text-gray-700"
        >
          ← Projects
        </Link>
        <h1 className="mt-3 text-2xl font-bold text-gray-900">New project</h1>
      </div>

      <div className="rounded-lg border border-gray-200 bg-white p-8 shadow-sm">
        <form onSubmit={handleSubmit} className="flex flex-col gap-5">
          <Input
            label="Project name"
            type="text"
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. Lobby Wave Panel"
          />

          <Select
            label="Panel mode"
            value={mode}
            onChange={(e) => setMode(e.target.value as ProjectMode)}
          >
            {MODE_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </Select>

          <Select
            label="Units"
            value={units}
            onChange={(e) => setUnits(e.target.value as Units)}
          >
            {UNIT_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </Select>

          {error && (
            <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-600">
              {error}
            </p>
          )}

          <div className="flex gap-3 pt-2">
            <Button type="submit" loading={loading}>
              Create project
            </Button>
            <Link href="/app">
              <Button type="button" variant="secondary">
                Cancel
              </Button>
            </Link>
          </div>
        </form>
      </div>
    </main>
  );
}
