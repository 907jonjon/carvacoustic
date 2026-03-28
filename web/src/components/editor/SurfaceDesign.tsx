"use client";

import type {
  CanonicalConfig,
  SurfaceType,
  FlowDirection,
  Symmetry,
} from "@/types/schema";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { SectionHeader, FieldRow, Num } from "./FormControls";

export function SurfaceDesign({
  config,
  onSurfaceChange,
}: {
  config: CanonicalConfig;
  onSurfaceChange: (p: Partial<CanonicalConfig["surface"]>) => void;
}) {
  const u = config.project.units;

  return (
    <>
      <SectionHeader title="Surface Design" />
      <FieldRow>
        <Select label="Surface Type" value={config.surface.type}
          onChange={(e) => onSurfaceChange({ type: e.target.value as SurfaceType })}>
          <option value="wave">Wave</option>
          <option value="terrain">Terrain</option>
          <option value="ripple">Ripple</option>
          <option value="mountain">Mountain</option>
        </Select>
        <Num label={`Peak Height (${u})`} value={config.surface.max_depth}
          onChange={(v) => onSurfaceChange({ max_depth: v })} min={0.5} max={12} step={0.1}
          hint="Tallest slat height" />
        <Num label="Wave Height" value={config.surface.amplitude}
          onChange={(v) => onSurfaceChange({ amplitude: v })} min={0} max={1} step={0.05}
          hint="0-1, intensity of variation" />
        <Num label="Wave Density" value={config.surface.frequency}
          onChange={(v) => onSurfaceChange({ frequency: v })} min={0.5} max={10} step={0.1}
          hint="0.5-10, undulations across width" />
        <Num label="Pattern Offset" value={Math.round(config.surface.phase * 180 / Math.PI)}
          onChange={(v) => onSurfaceChange({ phase: (v * Math.PI) / 180 })}
          min={0} max={360} step={5} hint="Shifts the wave pattern" />
        <Select label="Direction" value={config.surface.flow_direction}
          onChange={(e) => onSurfaceChange({ flow_direction: e.target.value as FlowDirection })}>
          <option value="x">X (horizontal)</option>
          <option value="y">Y (vertical)</option>
          <option value="radial">Radial</option>
        </Select>
        <Select label="Symmetry" value={config.surface.symmetry}
          onChange={(e) => onSurfaceChange({ symmetry: e.target.value as Symmetry })}>
          <option value="none">None</option>
          <option value="x">X mirror</option>
          <option value="y">Y mirror</option>
          <option value="xy">Both</option>
        </Select>
        <Num label="Smoothness" value={config.surface.smoothness}
          onChange={(v) => onSurfaceChange({ smoothness: v })} min={0} max={1} step={0.05}
          hint="0-1, blur across height field" />
        <Num label="Organic Variation" value={config.surface.noise_amount}
          onChange={(v) => onSurfaceChange({ noise_amount: v })} min={0} max={1} step={0.05}
          hint="0-1, organic randomness" />
        <div className="flex gap-2 items-end">
          <div className="flex-1">
            <Input label="Seed" type="number" value={config.surface.seed} step={1}
              hint="Determinism seed"
              onChange={(e) => {
                const v = parseInt(e.target.value, 10);
                if (!isNaN(v)) onSurfaceChange({ seed: v });
              }} />
          </div>
          <button
            type="button"
            onClick={() => onSurfaceChange({ seed: Math.floor(Math.random() * 100000) })}
            className="mb-0 rounded border border-gray-300 px-2 py-1.5 text-xs text-gray-600 hover:bg-gray-50"
            title="Randomize seed"
          >
            ↺
          </button>
        </div>
      </FieldRow>
    </>
  );
}
