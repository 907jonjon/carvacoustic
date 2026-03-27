"use client";

import { useState, useTransition } from "react";
import Link from "next/link";
import type { Database } from "@/types/database";
import type { CanonicalConfig, ProjectMode, PatternFamily } from "@/types/schema";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";

type Project = Database["public"]["Tables"]["projects"]["Row"];

interface ProjectEditorProps {
  project: Project;
  latestVersionNumber: number;
}

const MODE_LABELS: Record<ProjectMode, string> = {
  wall_art: "Wall Art",
  cabinet_front_panel: "Cabinet Front Panel",
  architectural_face_panel: "Architectural Face Panel",
};

const PATTERN_LABELS: Record<PatternFamily, string> = {
  wave_field: "Wave Field",
  contour_bands: "Contour Bands",
  slat_rib: "Slat Rib",
};

export function ProjectEditor({
  project,
  latestVersionNumber,
}: ProjectEditorProps) {
  const [config, setConfig] = useState<CanonicalConfig>(project.draft_config);
  const [saveStatus, setSaveStatus] = useState<
    "idle" | "saving" | "saved" | "error"
  >("idle");
  const [saveError, setSaveError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  function updateConfig(patch: Partial<CanonicalConfig>) {
    setConfig((prev) => ({ ...prev, ...patch }));
    setSaveStatus("idle");
  }

  function updateProjectSection(patch: Partial<CanonicalConfig["project"]>) {
    updateConfig({ project: { ...config.project, ...patch } });
  }

  function updateBoundary(patch: Partial<CanonicalConfig["boundary"]>) {
    updateConfig({ boundary: { ...config.boundary, ...patch } });
  }

  function updatePattern(patch: Partial<CanonicalConfig["pattern"]>) {
    updateConfig({ pattern: { ...config.pattern, ...patch } });
  }

  function updateMaterial(
    patch: Partial<CanonicalConfig["fabrication"]["material"]>
  ) {
    updateConfig({
      fabrication: {
        ...config.fabrication,
        material: { ...config.fabrication.material, ...patch },
      },
    });
  }

  function updateTool(
    patch: Partial<CanonicalConfig["fabrication"]["tool"]>
  ) {
    updateConfig({
      fabrication: {
        ...config.fabrication,
        tool: { ...config.fabrication.tool, ...patch },
      },
    });
  }

  function updateLayout(patch: Partial<CanonicalConfig["layout"]>) {
    updateConfig({ layout: { ...config.layout, ...patch } });
  }

  function updateExport(patch: Partial<CanonicalConfig["export"]>) {
    updateConfig({ export: { ...config.export, ...patch } });
  }

  async function handleSaveDraft() {
    setSaveStatus("saving");
    setSaveError(null);
    try {
      const res = await fetch(`/api/projects/${project.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ draft_config: config }),
      });
      if (!res.ok) {
        const d = await res.json();
        throw new Error(d?.error?.message ?? "Save failed.");
      }
      setSaveStatus("saved");
    } catch (err: unknown) {
      setSaveStatus("error");
      setSaveError(err instanceof Error ? err.message : "Save failed.");
    }
  }

  async function handleSaveVersion(notes: string) {
    setSaveStatus("saving");
    setSaveError(null);
    try {
      const res = await fetch(`/api/projects/${project.id}/versions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ config, notes }),
      });
      if (!res.ok) {
        const d = await res.json();
        throw new Error(d?.error?.message ?? "Version save failed.");
      }
      setSaveStatus("saved");
    } catch (err: unknown) {
      setSaveStatus("error");
      setSaveError(err instanceof Error ? err.message : "Version save failed.");
    }
  }

  return (
    <div className="flex h-[calc(100vh-3.5rem)] flex-col">
      {/* Editor top bar */}
      <div className="flex h-10 items-center justify-between border-b border-gray-200 bg-white px-4">
        <div className="flex items-center gap-2 text-sm">
          <Link
            href="/app"
            className="text-gray-400 hover:text-gray-600"
          >
            Projects
          </Link>
          <span className="text-gray-300">/</span>
          <span className="text-gray-700">{project.name}</span>
        </div>
        <div className="flex items-center gap-2 text-xs text-gray-400">
          <span>{MODE_LABELS[config.project.mode]}</span>
          <span>&bull;</span>
          <span>{config.project.units}</span>
        </div>
      </div>

      {/* 3-panel layout */}
      <div className="flex flex-1 overflow-hidden">
        {/* ── LEFT PANEL: config ── */}
        <aside className="w-72 shrink-0 overflow-y-auto border-r border-gray-200 bg-white">
          <ConfigPanel
            config={config}
            onProjectChange={updateProjectSection}
            onBoundaryChange={updateBoundary}
            onPatternChange={updatePattern}
            onMaterialChange={updateMaterial}
            onToolChange={updateTool}
            onLayoutChange={updateLayout}
            onExportChange={updateExport}
          />
        </aside>

        {/* ── CENTER PANEL: preview ── */}
        <main className="flex flex-1 flex-col items-center justify-center bg-gray-50">
          <PreviewPlaceholder />
        </main>

        {/* ── RIGHT PANEL: actions ── */}
        <aside className="w-64 shrink-0 overflow-y-auto border-l border-gray-200 bg-white">
          <ActionsPanel
            saveStatus={saveStatus}
            saveError={saveError}
            latestVersionNumber={latestVersionNumber}
            onSaveDraft={handleSaveDraft}
            onSaveVersion={handleSaveVersion}
          />
        </aside>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Left panel — config form
// ---------------------------------------------------------------------------

function SectionHeader({ title }: { title: string }) {
  return (
    <div className="border-b border-gray-100 bg-gray-50 px-4 py-2">
      <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500">
        {title}
      </h3>
    </div>
  );
}

function FieldRow({ children }: { children: React.ReactNode }) {
  return <div className="flex flex-col gap-3 px-4 py-4">{children}</div>;
}

function NumberInput({
  label,
  value,
  onChange,
  min,
  max,
  step,
  hint,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  min?: number;
  max?: number;
  step?: number;
  hint?: string;
}) {
  return (
    <Input
      label={label}
      type="number"
      value={value}
      min={min}
      max={max}
      step={step ?? 0.01}
      hint={hint}
      onChange={(e) => {
        const v = parseFloat(e.target.value);
        if (!isNaN(v)) onChange(v);
      }}
    />
  );
}

function ConfigPanel({
  config,
  onProjectChange,
  onBoundaryChange,
  onPatternChange,
  onMaterialChange,
  onToolChange,
  onLayoutChange,
  onExportChange,
}: {
  config: CanonicalConfig;
  onProjectChange: (p: Partial<CanonicalConfig["project"]>) => void;
  onBoundaryChange: (p: Partial<CanonicalConfig["boundary"]>) => void;
  onPatternChange: (p: Partial<CanonicalConfig["pattern"]>) => void;
  onMaterialChange: (p: Partial<CanonicalConfig["fabrication"]["material"]>) => void;
  onToolChange: (p: Partial<CanonicalConfig["fabrication"]["tool"]>) => void;
  onLayoutChange: (p: Partial<CanonicalConfig["layout"]>) => void;
  onExportChange: (p: Partial<CanonicalConfig["export"]>) => void;
}) {
  return (
    <div>
      {/* Setup */}
      <SectionHeader title="Setup" />
      <FieldRow>
        <Input
          label="Project name"
          value={config.project.name}
          onChange={(e) => onProjectChange({ name: e.target.value })}
        />
        <Select
          label="Mode"
          value={config.project.mode}
          onChange={(e) =>
            onProjectChange({ mode: e.target.value as ProjectMode })
          }
        >
          <option value="wall_art">Wall Art</option>
          <option value="cabinet_front_panel">Cabinet Front Panel</option>
          <option value="architectural_face_panel">
            Architectural Face Panel
          </option>
        </Select>
        <Select
          label="Units"
          value={config.project.units}
          onChange={(e) =>
            onProjectChange({ units: e.target.value as "in" | "mm" })
          }
        >
          <option value="in">Inches (in)</option>
          <option value="mm">Millimetres (mm)</option>
        </Select>
      </FieldRow>

      {/* Boundary */}
      <SectionHeader title="Boundary" />
      <FieldRow>
        <Select
          label="Type"
          value={config.boundary.type}
          onChange={(e) =>
            onBoundaryChange({
              type: e.target.value as CanonicalConfig["boundary"]["type"],
            })
          }
        >
          <option value="rectangle">Rectangle</option>
          <option value="rounded_rectangle">Rounded Rectangle</option>
          <option value="svg_import">SVG Import</option>
        </Select>
        <NumberInput
          label={`Width (${config.project.units})`}
          value={config.boundary.width}
          onChange={(v) => onBoundaryChange({ width: v })}
          min={0.1}
        />
        <NumberInput
          label={`Height (${config.project.units})`}
          value={config.boundary.height}
          onChange={(v) => onBoundaryChange({ height: v })}
          min={0.1}
        />
        {config.boundary.type === "rounded_rectangle" && (
          <NumberInput
            label={`Corner radius (${config.project.units})`}
            value={config.boundary.corner_radius}
            onChange={(v) => onBoundaryChange({ corner_radius: v })}
            min={0}
          />
        )}
        <NumberInput
          label={`Safe margin (${config.project.units})`}
          value={config.boundary.safe_margin}
          onChange={(v) => onBoundaryChange({ safe_margin: v })}
          min={0}
          hint="Keep-out distance from boundary edge"
        />
      </FieldRow>

      {/* Pattern */}
      <SectionHeader title="Pattern" />
      <FieldRow>
        <Select
          label="Family"
          value={config.pattern.family}
          onChange={(e) =>
            onPatternChange({ family: e.target.value as PatternFamily })
          }
        >
          {(
            Object.entries(PATTERN_LABELS) as [PatternFamily, string][]
          ).map(([v, l]) => (
            <option key={v} value={v}>
              {l}
            </option>
          ))}
        </Select>
        <NumberInput
          label="Density"
          value={config.pattern.density}
          onChange={(v) => onPatternChange({ density: v })}
          min={0}
          max={1}
          step={0.05}
          hint="0 – 1"
        />
        <NumberInput
          label={`Spacing (${config.project.units})`}
          value={config.pattern.spacing}
          onChange={(v) => onPatternChange({ spacing: v })}
          min={0.01}
        />
        <NumberInput
          label={`Line width (${config.project.units})`}
          value={config.pattern.line_width}
          onChange={(v) => onPatternChange({ line_width: v })}
          min={0.01}
        />
        <NumberInput
          label={`Amplitude (${config.project.units})`}
          value={config.pattern.amplitude}
          onChange={(v) => onPatternChange({ amplitude: v })}
          min={0}
        />
        <Input
          label="Seed"
          type="number"
          value={config.pattern.seed}
          min={0}
          step={1}
          hint="Determinism seed"
          onChange={(e) => {
            const v = parseInt(e.target.value, 10);
            if (!isNaN(v)) onPatternChange({ seed: v });
          }}
        />
        <Select
          label="Symmetry"
          value={config.pattern.symmetry}
          onChange={(e) =>
            onPatternChange({
              symmetry: e.target.value as CanonicalConfig["pattern"]["symmetry"],
            })
          }
        >
          <option value="none">None</option>
          <option value="x">X axis</option>
          <option value="y">Y axis</option>
          <option value="xy">XY (both)</option>
        </Select>
      </FieldRow>

      {/* Fabrication — material */}
      <SectionHeader title="Material" />
      <FieldRow>
        <NumberInput
          label={`Thickness (${config.project.units})`}
          value={config.fabrication.material.thickness}
          onChange={(v) => onMaterialChange({ thickness: v })}
          min={0.01}
        />
        <NumberInput
          label={`Sheet width (${config.project.units})`}
          value={config.fabrication.material.sheet_width}
          onChange={(v) => onMaterialChange({ sheet_width: v })}
          min={1}
        />
        <NumberInput
          label={`Sheet height (${config.project.units})`}
          value={config.fabrication.material.sheet_height}
          onChange={(v) => onMaterialChange({ sheet_height: v })}
          min={1}
        />
        <NumberInput
          label={`Min bridge (${config.project.units})`}
          value={config.fabrication.material.min_bridge}
          onChange={(v) => onMaterialChange({ min_bridge: v })}
          min={0.01}
        />
        <Select
          label="Grain direction"
          value={config.fabrication.material.grain_direction}
          onChange={(e) =>
            onMaterialChange({
              grain_direction: e.target.value as "x" | "y",
            })
          }
        >
          <option value="x">X (horizontal)</option>
          <option value="y">Y (vertical)</option>
        </Select>
      </FieldRow>

      {/* Fabrication — tool */}
      <SectionHeader title="Tool" />
      <FieldRow>
        <NumberInput
          label={`Tool diameter (${config.project.units})`}
          value={config.fabrication.tool.tool_diameter}
          onChange={(v) => onToolChange({ tool_diameter: v })}
          min={0.001}
        />
        <NumberInput
          label={`Kerf allowance (${config.project.units})`}
          value={config.fabrication.tool.kerf_allowance}
          onChange={(v) => onToolChange({ kerf_allowance: v })}
          min={0}
        />
        <NumberInput
          label={`Min inside radius (${config.project.units})`}
          value={config.fabrication.tool.min_inside_radius}
          onChange={(v) => onToolChange({ min_inside_radius: v })}
          min={0}
        />
        <Select
          label="Dogbone style"
          value={config.fabrication.tool.dogbone_style}
          onChange={(e) =>
            onToolChange({
              dogbone_style: e.target.value as "classic" | "none",
            })
          }
        >
          <option value="none">None</option>
          <option value="classic">Classic</option>
        </Select>
        <NumberInput
          label={`Part clearance (${config.project.units})`}
          value={config.fabrication.tool.clearance}
          onChange={(v) => onToolChange({ clearance: v })}
          min={0}
        />
        <NumberInput
          label={`Border gap (${config.project.units})`}
          value={config.fabrication.tool.border_gap}
          onChange={(v) => onToolChange({ border_gap: v })}
          min={0}
        />
      </FieldRow>

      {/* Layout */}
      <SectionHeader title="Layout" />
      <FieldRow>
        <label className="flex items-center gap-2 text-sm text-gray-700">
          <input
            type="checkbox"
            checked={config.layout.enabled}
            onChange={(e) => onLayoutChange({ enabled: e.target.checked })}
            className="rounded border-gray-300 text-brand-600 focus:ring-brand-500"
          />
          Enable layout
        </label>
        <NumberInput
          label="Copies"
          value={config.layout.copies}
          onChange={(v) => onLayoutChange({ copies: Math.max(1, Math.round(v)) })}
          min={1}
          step={1}
        />
        <Select
          label="Rotation mode"
          value={config.layout.rotation_mode}
          onChange={(e) =>
            onLayoutChange({
              rotation_mode: e.target.value as CanonicalConfig["layout"]["rotation_mode"],
            })
          }
        >
          <option value="none">None</option>
          <option value="90_only">90° only</option>
          <option value="any">Any</option>
        </Select>
        <label className="flex items-center gap-2 text-sm text-gray-700">
          <input
            type="checkbox"
            checked={config.layout.preserve_grain}
            onChange={(e) => onLayoutChange({ preserve_grain: e.target.checked })}
            className="rounded border-gray-300 text-brand-600 focus:ring-brand-500"
          />
          Preserve grain direction
        </label>
      </FieldRow>

      {/* Export */}
      <SectionHeader title="Export" />
      <FieldRow>
        <div className="flex flex-col gap-2">
          <span className="text-sm font-medium text-gray-700">Formats</span>
          {(["dxf", "svg", "pdf", "json"] as const).map((fmt) => (
            <label key={fmt} className="flex items-center gap-2 text-sm text-gray-700">
              <input
                type="checkbox"
                checked={config.export.formats.includes(fmt)}
                onChange={(e) => {
                  const formats = e.target.checked
                    ? [...config.export.formats, fmt]
                    : config.export.formats.filter((f) => f !== fmt);
                  if (formats.length > 0) onExportChange({ formats });
                }}
                className="rounded border-gray-300 text-brand-600 focus:ring-brand-500"
              />
              {fmt.toUpperCase()}
            </label>
          ))}
        </div>
      </FieldRow>

      {/* Bottom padding */}
      <div className="h-8" />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Center panel — preview placeholder
// ---------------------------------------------------------------------------

function PreviewPlaceholder() {
  return (
    <div className="flex flex-col items-center gap-3 text-center">
      <div className="rounded-lg border-2 border-dashed border-gray-300 p-12">
        <svg
          className="mx-auto h-12 w-12 text-gray-300"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={1}
        >
          <rect x="2" y="2" width="20" height="20" rx="1" />
          <path d="M2 8 Q7 5 12 8 Q17 11 22 8" />
          <path d="M2 13 Q7 10 12 13 Q17 16 22 13" />
          <path d="M2 18 Q7 15 12 18 Q17 21 22 18" />
        </svg>
      </div>
      <p className="text-sm text-gray-400">
        Preview available in Milestone B
      </p>
      <p className="text-xs text-gray-300">
        Configure pattern and click Generate
      </p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Right panel — validation + actions
// ---------------------------------------------------------------------------

function ActionsPanel({
  saveStatus,
  saveError,
  latestVersionNumber,
  onSaveDraft,
  onSaveVersion,
}: {
  saveStatus: "idle" | "saving" | "saved" | "error";
  saveError: string | null;
  latestVersionNumber: number;
  onSaveDraft: () => void;
  onSaveVersion: (notes: string) => void;
}) {
  const [versionNotes, setVersionNotes] = useState("");
  const [showVersionForm, setShowVersionForm] = useState(false);

  return (
    <div className="flex flex-col gap-0">
      {/* Validation placeholder */}
      <div className="border-b border-gray-100 bg-gray-50 px-4 py-2">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500">
          Validation
        </h3>
      </div>
      <div className="px-4 py-4">
        <p className="text-xs text-gray-400">
          Run Generate to see validation results (Milestone B).
        </p>
      </div>

      {/* Generate / Export — disabled stubs */}
      <div className="border-b border-gray-100 bg-gray-50 px-4 py-2">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500">
          Actions
        </h3>
      </div>
      <div className="flex flex-col gap-2 px-4 py-4">
        <Button
          disabled
          title="Available in Milestone B"
          className="w-full"
        >
          Generate
        </Button>
        <Button
          variant="secondary"
          disabled
          title="Available in Milestone B"
          className="w-full"
        >
          Validate
        </Button>
        <Button
          variant="secondary"
          disabled
          title="Available in Milestone B"
          className="w-full"
        >
          Export
        </Button>
      </div>

      {/* Save */}
      <div className="border-b border-gray-100 bg-gray-50 px-4 py-2">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500">
          Save
        </h3>
      </div>
      <div className="flex flex-col gap-2 px-4 py-4">
        {saveStatus === "saved" && (
          <p className="text-xs text-green-600">Saved.</p>
        )}
        {saveStatus === "error" && saveError && (
          <p className="text-xs text-red-600">{saveError}</p>
        )}

        <Button
          variant="secondary"
          loading={saveStatus === "saving"}
          onClick={onSaveDraft}
          className="w-full"
        >
          Save draft
        </Button>

        {!showVersionForm ? (
          <Button
            variant="ghost"
            onClick={() => setShowVersionForm(true)}
            className="w-full text-xs"
          >
            Save checkpoint (v{latestVersionNumber + 1})
          </Button>
        ) : (
          <div className="flex flex-col gap-2">
            <Input
              label="Notes (optional)"
              value={versionNotes}
              onChange={(e) => setVersionNotes(e.target.value)}
              placeholder="e.g. adjusted spacing"
            />
            <div className="flex gap-2">
              <Button
                size="sm"
                loading={saveStatus === "saving"}
                onClick={() => {
                  onSaveVersion(versionNotes);
                  setShowVersionForm(false);
                  setVersionNotes("");
                }}
              >
                Save v{latestVersionNumber + 1}
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setShowVersionForm(false)}
              >
                Cancel
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
