"use client";

import { Input } from "@/components/ui/input";

export function SectionHeader({ title }: { title: string }) {
  return (
    <div className="border-b border-gray-100 bg-gray-50 px-4 py-2">
      <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500">{title}</h3>
    </div>
  );
}

export function FieldRow({ children }: { children: React.ReactNode }) {
  return <div className="flex flex-col gap-3 px-4 py-4">{children}</div>;
}

export function Num({
  label, value, onChange, min, max, step = 0.01, hint,
}: {
  label: string; value: number; onChange: (v: number) => void;
  min?: number; max?: number; step?: number; hint?: string;
}) {
  return (
    <Input
      label={label} type="number" value={value}
      min={min} max={max} step={step} hint={hint}
      onChange={(e) => { const v = parseFloat(e.target.value); if (!isNaN(v)) onChange(v); }}
    />
  );
}

export function CheckboxRow({ label, checked, onChange }: {
  label: string; checked: boolean; onChange: (v: boolean) => void;
}) {
  return (
    <label className="flex items-center gap-2 text-sm text-gray-700">
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        className="rounded border-gray-300 text-brand-600 focus:ring-brand-500"
      />
      {label}
    </label>
  );
}
