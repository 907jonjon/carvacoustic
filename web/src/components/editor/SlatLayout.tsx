"use client";

import type { CanonicalConfig } from "@/types/schema";
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

  return (
    <>
      {/* Slats */}
      <SectionHeader title="Slat Layout" />
      <FieldRow>
        <Num label="Slat count" value={config.slats.count}
          onChange={(v) => onSlatsChange({ count: Math.max(5, Math.min(200, Math.round(v))) })}
          min={5} max={200} step={1} hint="5-200 slats" />
        <Num label={`Spacing (${u})`} value={config.slats.spacing}
          onChange={(v) => onSlatsChange({ spacing: v })} min={0.25}
          hint="Center-to-center" />
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
