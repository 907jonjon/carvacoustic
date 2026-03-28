"use client";

import type { CanonicalConfig, ProjectMode } from "@/types/schema";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { SectionHeader, FieldRow, Num } from "./FormControls";

const MODE_LABELS: Record<ProjectMode, string> = {
  wall_art: "Wall Art",
  cabinet_front_panel: "Cabinet Front Panel",
  architectural_face_panel: "Architectural Face Panel",
};

export { MODE_LABELS };

export function ProjectSetup({
  config,
  onProjectChange,
  onBoundaryChange,
}: {
  config: CanonicalConfig;
  onProjectChange: (p: Partial<CanonicalConfig["project"]>) => void;
  onBoundaryChange: (p: Partial<CanonicalConfig["boundary"]>) => void;
}) {
  const u = config.project.units;

  return (
    <>
      {/* Project */}
      <SectionHeader title="Project Setup" />
      <FieldRow>
        <Input label="Project name" value={config.project.name}
          onChange={(e) => onProjectChange({ name: e.target.value })} />
        <Select label="Mode" value={config.project.mode}
          onChange={(e) => onProjectChange({ mode: e.target.value as ProjectMode })}>
          <option value="wall_art">Wall Art</option>
          <option value="cabinet_front_panel">Cabinet Front Panel</option>
          <option value="architectural_face_panel">Architectural Face Panel</option>
        </Select>
        <Select label="Units" value={u}
          onChange={(e) => onProjectChange({ units: e.target.value as "in" | "mm" })}>
          <option value="in">Inches (in)</option>
          <option value="mm">Millimetres (mm)</option>
        </Select>
      </FieldRow>

      {/* Boundary */}
      <SectionHeader title="Boundary" />
      <FieldRow>
        <Select label="Boundary type" value={config.boundary.type}
          onChange={(e) => onBoundaryChange({ type: e.target.value as CanonicalConfig["boundary"]["type"] })}>
          <option value="rectangle">Rectangle</option>
          <option value="rounded_rectangle">Rounded Rectangle</option>
        </Select>
        <Num label={`Width (${u})`} value={config.boundary.width}
          onChange={(v) => onBoundaryChange({ width: v })} min={0.1} />
        <Num label={`Height (${u})`} value={config.boundary.height}
          onChange={(v) => onBoundaryChange({ height: v })} min={0.1} />
        {config.boundary.type === "rounded_rectangle" && (
          <Num label={`Corner radius (${u})`} value={config.boundary.corner_radius}
            onChange={(v) => onBoundaryChange({ corner_radius: v })} min={0} />
        )}
        <Num label={`Safe margin (${u})`} value={config.boundary.safe_margin}
          onChange={(v) => onBoundaryChange({ safe_margin: v })} min={0}
          hint="Keep-out distance from edge" />
      </FieldRow>
    </>
  );
}
