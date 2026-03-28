"use client";

import type { CanonicalConfig } from "@/types/schema";
import { Select } from "@/components/ui/select";
import { SectionHeader, FieldRow, Num, CheckboxRow } from "./FormControls";

export function SlatLayout({
  config,
  onSlatsChange,
  onBackingChange,
}: {
  config: CanonicalConfig;
  onSlatsChange: (p: Partial<CanonicalConfig["slats"]>) => void;
  onBackingChange: (p: Partial<CanonicalConfig["backing"]>) => void;
}) {
  const u = config.project.units;
  const mode = config.slats.distribution_mode ?? "fit_to_boundary";
  const isFit = mode === "fit_to_boundary";

  const computedSpacing = isFit
    ? (config.boundary.height - 2 * config.boundary.safe_margin) /
      Math.max(config.slats.count - 1, 1)
    : config.slats.spacing;

  return (
    <>
      {/* Slats */}
      <SectionHeader title="Slat Layout" />
      <FieldRow>
        <Num label="Slat count" value={config.slats.count}
          onChange={(v) => onSlatsChange({ count: Math.max(5, Math.min(200, Math.round(v))) })}
          min={5} max={200} step={1} hint="5-200 slats" />
        <Select
          label="Distribution mode"
          value={mode}
          onChange={(e) =>
            onSlatsChange({
              distribution_mode: e.target.value as "fit_to_boundary" | "manual",
            })
          }
        >
          <option value="fit_to_boundary">Fit to Panel</option>
          <option value="manual">Manual Spacing</option>
        </Select>
        {isFit ? (
          <div className="flex flex-col gap-1 text-sm text-gray-700">
            <span className="font-medium">Spacing ({u})</span>
            <span className="rounded bg-gray-100 px-3 py-1.5 tabular-nums">
              {computedSpacing.toFixed(3)}
            </span>
            <span className="text-xs text-gray-400">Auto-computed from panel height</span>
          </div>
        ) : (
          <Num label={`Spacing (${u})`} value={config.slats.spacing}
            onChange={(v) => onSlatsChange({ spacing: v })} min={0.25}
            hint="Center-to-center" />
        )}
        <Num label={`Base height (${u})`} value={config.slats.base_height}
          onChange={(v) => onSlatsChange({ base_height: v })} min={0.5}
          hint="Rectangular base below profile" />
        <Num label="Tab count" value={config.slats.tab_count}
          onChange={(v) => onSlatsChange({ tab_count: Math.max(2, Math.min(6, Math.round(v))) })}
          min={2} max={6} step={1} hint="Mounting tabs per slat" />
        <Num label={`Tab width (${u})`} value={config.slats.tab_width}
          onChange={(v) => onSlatsChange({ tab_width: v })} min={0.01}
          hint="Width of each tab" />
      </FieldRow>

      {/* Backing Board */}
      <SectionHeader title="Backing Board" />
      <FieldRow>
        <CheckboxRow label="Include backing board" checked={config.backing.enabled}
          onChange={(v) => onBackingChange({ enabled: v })} />
        {config.backing.enabled && (
          <CheckboxRow label="Mounting holes" checked={config.backing.mounting_holes}
            onChange={(v) => onBackingChange({ mounting_holes: v })} />
        )}
      </FieldRow>
    </>
  );
}
