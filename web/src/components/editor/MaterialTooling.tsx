"use client";

import type { CanonicalConfig } from "@/types/schema";
import { Select } from "@/components/ui/select";
import { SectionHeader, FieldRow, Num, CheckboxRow } from "./FormControls";

export function MaterialTooling({
  config,
  onMaterialChange,
  onToolChange,
  onLayoutChange,
}: {
  config: CanonicalConfig;
  onMaterialChange: (p: Partial<CanonicalConfig["fabrication"]["material"]>) => void;
  onToolChange: (p: Partial<CanonicalConfig["fabrication"]["tool"]>) => void;
  onLayoutChange: (p: Partial<CanonicalConfig["layout"]>) => void;
}) {
  const u = config.project.units;

  return (
    <>
      {/* Material */}
      <SectionHeader title="Material" />
      <FieldRow>
        <Num label={`Thickness (${u})`} value={config.fabrication.material.thickness}
          onChange={(v) => onMaterialChange({ thickness: v })} min={0.01}
          hint="Material thickness drives slat thickness" />
        <Num label={`Sheet width (${u})`} value={config.fabrication.material.sheet_width}
          onChange={(v) => onMaterialChange({ sheet_width: v })} min={1} />
        <Num label={`Sheet height (${u})`} value={config.fabrication.material.sheet_height}
          onChange={(v) => onMaterialChange({ sheet_height: v })} min={1} />
        <Num label={`Min bridge (${u})`} value={config.fabrication.material.min_bridge}
          onChange={(v) => onMaterialChange({ min_bridge: v })} min={0.01} />
        <Select label="Grain direction" value={config.fabrication.material.grain_direction}
          onChange={(e) => onMaterialChange({ grain_direction: e.target.value as "x" | "y" })}>
          <option value="x">X (horizontal)</option>
          <option value="y">Y (vertical)</option>
        </Select>
      </FieldRow>

      {/* Tool */}
      <SectionHeader title="Tool" />
      <FieldRow>
        <Num label={`Tool diameter (${u})`} value={config.fabrication.tool.tool_diameter}
          onChange={(v) => onToolChange({ tool_diameter: v })} min={0.001} />
        <Num label={`Kerf allowance (${u})`} value={config.fabrication.tool.kerf_allowance}
          onChange={(v) => onToolChange({ kerf_allowance: v })} min={0} />
        <Num label={`Min inside radius (${u})`} value={config.fabrication.tool.min_inside_radius}
          onChange={(v) => onToolChange({ min_inside_radius: v })} min={0} />
        <Select label="Dogbone style" value={config.fabrication.tool.dogbone_style}
          onChange={(e) => onToolChange({ dogbone_style: e.target.value as "classic" | "none" })}>
          <option value="none">None</option>
          <option value="classic">Classic</option>
        </Select>
        <Num label={`Part clearance (${u})`} value={config.fabrication.tool.clearance}
          onChange={(v) => onToolChange({ clearance: v })} min={0} />
        <Num label={`Border gap (${u})`} value={config.fabrication.tool.border_gap}
          onChange={(v) => onToolChange({ border_gap: v })} min={0} />
      </FieldRow>

      {/* Layout */}
      <SectionHeader title="Layout" />
      <FieldRow>
        <CheckboxRow label="Enable layout" checked={config.layout.enabled}
          onChange={(v) => onLayoutChange({ enabled: v })} />
        <Num label="Copies" value={config.layout.copies}
          onChange={(v) => onLayoutChange({ copies: Math.max(1, Math.round(v)) })} min={1} step={1} />
        <Select label="Rotation mode" value={config.layout.rotation_mode}
          onChange={(e) => onLayoutChange({ rotation_mode: e.target.value as CanonicalConfig["layout"]["rotation_mode"] })}>
          <option value="none">None</option>
          <option value="90_only">90° only</option>
          <option value="any">Any</option>
        </Select>
        <CheckboxRow label="Preserve grain direction" checked={config.layout.preserve_grain}
          onChange={(v) => onLayoutChange({ preserve_grain: v })} />
      </FieldRow>
    </>
  );
}
