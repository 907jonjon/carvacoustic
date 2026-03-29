"use client";

import { useState, useEffect } from "react";
import type { CanonicalConfig } from "@/types/schema";
import type { Database } from "@/types/database";
import { Select } from "@/components/ui/select";
import { SectionHeader, FieldRow, Num, CheckboxRow } from "./FormControls";

type MaterialPreset = Database["public"]["Tables"]["material_presets"]["Row"];
type ToolPreset = Database["public"]["Tables"]["tool_presets"]["Row"];

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

  const [materialPresets, setMaterialPresets] = useState<MaterialPreset[]>([]);
  const [toolPresets, setToolPresets] = useState<ToolPreset[]>([]);

  useEffect(() => {
    fetch("/api/presets/materials")
      .then((r) => (r.ok ? r.json() : []))
      .then((d) => setMaterialPresets(Array.isArray(d) ? d : []))
      .catch(() => setMaterialPresets([]));

    fetch("/api/presets/tools")
      .then((r) => (r.ok ? r.json() : []))
      .then((d) => setToolPresets(Array.isArray(d) ? d : []))
      .catch(() => setToolPresets([]));
  }, []);

  function applyMaterialPreset(presetId: string) {
    const preset = materialPresets.find((p) => p.id === presetId);
    if (!preset) return;
    onMaterialChange({
      thickness: preset.thickness,
      sheet_width: preset.sheet_width,
      sheet_height: preset.sheet_height,
      min_bridge: preset.min_bridge,
      grain_direction: preset.grain_direction,
    });
  }

  function applyToolPreset(presetId: string) {
    const preset = toolPresets.find((p) => p.id === presetId);
    if (!preset) return;
    onToolChange({
      tool_diameter: preset.tool_diameter,
      kerf_allowance: preset.kerf_allowance,
      min_inside_radius: preset.min_inside_radius,
      dogbone_style: preset.dogbone_style,
      clearance: preset.clearance,
      border_gap: preset.border_gap,
    });
  }

  return (
    <>
      {/* Material */}
      <SectionHeader title="Material" />
      <FieldRow>
        {materialPresets.length > 0 && (
          <Select
            label="Preset"
            value=""
            onChange={(e) => {
              if (e.target.value) applyMaterialPreset(e.target.value);
            }}
          >
            <option value="">Custom</option>
            {materialPresets.map((p) => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </Select>
        )}
      </FieldRow>
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
        {toolPresets.length > 0 && (
          <Select
            label="Preset"
            value=""
            onChange={(e) => {
              if (e.target.value) applyToolPreset(e.target.value);
            }}
          >
            <option value="">Custom</option>
            {toolPresets.map((p) => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </Select>
        )}
      </FieldRow>
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
