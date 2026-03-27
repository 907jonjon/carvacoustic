"use client";

import { useState } from "react";
import Link from "next/link";
import type { Database } from "@/types/database";
import type { CanonicalConfig, ProjectMode, PatternFamily } from "@/types/schema";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";

type Project = Database["public"]["Tables"]["projects"]["Row"];

interface ValidationIssue {
  level: "error" | "warning" | "info";
  code: string;
  message: string;
  field?: string | null;
}

interface GenerateResult {
  status: "ok" | "error";
  message?: string;
  validation?: { valid: boolean; issues: ValidationIssue[] };
  svg_preview?: string;
  part_count?: number;
  generated_at?: string;
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
}: {
  project: Project;
  latestVersionNumber: number;
}) {
  const [config, setConfig] = useState<CanonicalConfig>(project.draft_config);

  // Save state
  const [saveStatus, setSaveStatus] = useState<"idle" | "saving" | "saved" | "error">("idle");
  const [saveError, setSaveError] = useState<string | null>(null);

  // Generate / validate / export state
  const [generating, setGenerating] = useState(false);
  const [validating, setValidating] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [generateResult, setGenerateResult] = useState<GenerateResult | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  // ── Config updaters ─────────────────────────────────────────────────────────

  function patch(p: Partial<CanonicalConfig>) {
    setConfig((prev) => ({ ...prev, ...p }));
    setSaveStatus("idle");
  }
  const patchProject = (p: Partial<CanonicalConfig["project"]>) =>
    patch({ project: { ...config.project, ...p } });
  const patchBoundary = (p: Partial<CanonicalConfig["boundary"]>) =>
    patch({ boundary: { ...config.boundary, ...p } });
  const patchPattern = (p: Partial<CanonicalConfig["pattern"]>) =>
    patch({ pattern: { ...config.pattern, ...p } });
  const patchMaterial = (p: Partial<CanonicalConfig["fabrication"]["material"]>) =>
    patch({ fabrication: { ...config.fabrication, material: { ...config.fabrication.material, ...p } } });
  const patchTool = (p: Partial<CanonicalConfig["fabrication"]["tool"]>) =>
    patch({ fabrication: { ...config.fabrication, tool: { ...config.fabrication.tool, ...p } } });
  const patchLayout = (p: Partial<CanonicalConfig["layout"]>) =>
    patch({ layout: { ...config.layout, ...p } });
  const patchExport = (p: Partial<CanonicalConfig["export"]>) =>
    patch({ export: { ...config.export, ...p } });

  // ── Actions ─────────────────────────────────────────────────────────────────

  async function handleGenerate() {
    setGenerating(true);
    setActionError(null);
    try {
      const res = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ config }),
      });
      const data: GenerateResult = await res.json();
      if (!res.ok) {
        const err = data as unknown as { error?: { message?: string } };
        throw new Error(err?.error?.message ?? "Generate failed.");
      }
      setGenerateResult(data);
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Generate failed.");
    } finally {
      setGenerating(false);
    }
  }

  async function handleValidate() {
    setValidating(true);
    setActionError(null);
    try {
      const res = await fetch("/api/validate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ config }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data?.error?.message ?? "Validate failed.");
      }
      // Merge validation result into generateResult if present, or create stub
      setGenerateResult((prev) => ({
        ...(prev ?? { status: "ok", svg_preview: "", part_count: 0, generated_at: "" }),
        validation: data,
        status: data.valid ? "ok" : "error",
      }));
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Validate failed.");
    } finally {
      setValidating(false);
    }
  }

  async function handleExport() {
    setExporting(true);
    setActionError(null);
    try {
      const res = await fetch("/api/export", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ config }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err?.error?.message ?? "Export failed.");
      }
      // Trigger browser download
      const disposition = res.headers.get("Content-Disposition") ?? "";
      const filenameMatch = disposition.match(/filename="?([^"]+)"?/);
      const filename = filenameMatch?.[1] ?? "carvacoustic-export.zip";
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Export failed.");
    } finally {
      setExporting(false);
    }
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
    } catch (err) {
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
    } catch (err) {
      setSaveStatus("error");
      setSaveError(err instanceof Error ? err.message : "Version save failed.");
    }
  }

  // ── Render ──────────────────────────────────────────────────────────────────

  return (
    <div className="flex h-[calc(100vh-3.5rem)] flex-col">
      {/* Top bar */}
      <div className="flex h-10 items-center justify-between border-b border-gray-200 bg-white px-4">
        <div className="flex items-center gap-2 text-sm">
          <Link href="/app" className="text-gray-400 hover:text-gray-600">
            Projects
          </Link>
          <span className="text-gray-300">/</span>
          <span className="text-gray-700 truncate max-w-48">{project.name}</span>
        </div>
        <div className="flex items-center gap-2 text-xs text-gray-400">
          <span>{MODE_LABELS[config.project.mode]}</span>
          <span>&bull;</span>
          <span>{config.project.units}</span>
          {generateResult?.generated_at && (
            <>
              <span>&bull;</span>
              <span>Generated {new Date(generateResult.generated_at).toLocaleTimeString()}</span>
            </>
          )}
          {saveStatus === "idle" && (
            <>
              <span>&bull;</span>
              <span className="text-amber-500">Unsaved changes</span>
            </>
          )}
          {saveStatus === "saved" && (
            <>
              <span>&bull;</span>
              <span className="text-green-600">Saved</span>
            </>
          )}
        </div>
      </div>

      {/* 3-panel layout */}
      <div className="flex flex-1 overflow-hidden">
        {/* ── LEFT: config form ── */}
        <aside className="w-72 shrink-0 overflow-y-auto border-r border-gray-200 bg-white">
          <ConfigPanel
            config={config}
            onProjectChange={patchProject}
            onBoundaryChange={patchBoundary}
            onPatternChange={patchPattern}
            onMaterialChange={patchMaterial}
            onToolChange={patchTool}
            onLayoutChange={patchLayout}
            onExportChange={patchExport}
          />
        </aside>

        {/* ── CENTER: SVG preview ── */}
        <main className="flex flex-1 flex-col bg-gray-50 overflow-hidden">
          <PreviewPanel result={generateResult} />
        </main>

        {/* ── RIGHT: validation + actions ── */}
        <aside className="w-64 shrink-0 overflow-y-auto border-l border-gray-200 bg-white">
          <ActionsPanel
            result={generateResult}
            actionError={actionError}
            generating={generating}
            validating={validating}
            exporting={exporting}
            saveStatus={saveStatus}
            saveError={saveError}
            latestVersionNumber={latestVersionNumber}
            onGenerate={handleGenerate}
            onValidate={handleValidate}
            onExport={handleExport}
            onSaveDraft={handleSaveDraft}
            onSaveVersion={handleSaveVersion}
          />
        </aside>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Center panel — SVG preview
// ─────────────────────────────────────────────────────────────────────────────

function PreviewPanel({ result }: { result: GenerateResult | null }) {
  if (!result?.svg_preview) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-3 text-center p-8">
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
        <p className="text-sm text-gray-400">Click Generate to preview</p>
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col">
      {result.part_count !== undefined && result.part_count > 0 && (
        <div className="flex items-center gap-3 border-b border-gray-100 bg-white px-4 py-2 text-xs text-gray-500">
          <span>{result.part_count} cut feature{result.part_count !== 1 ? "s" : ""}</span>
          {result.validation && (
            <>
              <span>&bull;</span>
              <span className={result.validation.valid ? "text-green-600" : "text-red-600"}>
                {result.validation.valid ? "Valid" : "Has errors"}
              </span>
            </>
          )}
        </div>
      )}
      <div
        className="flex-1 p-4"
        /* SVG from our own geometry service — safe to render inline */
        dangerouslySetInnerHTML={{ __html: result.svg_preview }}
      />
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Right panel — validation list + actions
// ─────────────────────────────────────────────────────────────────────────────

const ISSUE_COLOURS: Record<string, string> = {
  error:   "text-red-700 bg-red-50 border-red-200",
  warning: "text-amber-700 bg-amber-50 border-amber-200",
  info:    "text-blue-700 bg-blue-50 border-blue-200",
};

function ActionsPanel({
  result,
  actionError,
  generating,
  validating,
  exporting,
  saveStatus,
  saveError,
  latestVersionNumber,
  onGenerate,
  onValidate,
  onExport,
  onSaveDraft,
  onSaveVersion,
}: {
  result: GenerateResult | null;
  actionError: string | null;
  generating: boolean;
  validating: boolean;
  exporting: boolean;
  saveStatus: "idle" | "saving" | "saved" | "error";
  saveError: string | null;
  latestVersionNumber: number;
  onGenerate: () => void;
  onValidate: () => void;
  onExport: () => void;
  onSaveDraft: () => void;
  onSaveVersion: (notes: string) => void;
}) {
  const [versionNotes, setVersionNotes] = useState("");
  const [showVersionForm, setShowVersionForm] = useState(false);

  const issues = result?.validation?.issues ?? [];
  const errors = issues.filter((i) => i.level === "error");
  const warnings = issues.filter((i) => i.level === "warning");
  const infos = issues.filter((i) => i.level === "info");

  const canExport = result?.status === "ok" && result.validation?.valid !== false;

  return (
    <div className="flex flex-col">
      {/* Validation */}
      <SectionHeader title="Validation" />
      <div className="px-3 py-3">
        {actionError && (
          <div className="mb-2 rounded border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">
            {actionError.includes("not reachable") ? (
              <>
                <span className="font-semibold">Geometry service offline.</span>{" "}
                Make sure it is running on port 8001:{" "}
                <code className="text-xs">uvicorn app.main:app --port 8001</code>
              </>
            ) : (
              actionError
            )}
          </div>
        )}
        {issues.length === 0 && !actionError && (
          <p className="text-xs text-gray-400">
            Run Generate or Validate to see results.
          </p>
        )}
        {issues.length > 0 && (
          <ul className="flex flex-col gap-1.5">
            {[...errors, ...warnings, ...infos].map((issue, i) => (
              <li
                key={i}
                className={`rounded border px-2 py-1.5 text-xs ${ISSUE_COLOURS[issue.level]}`}
              >
                <span className="font-medium uppercase">{issue.level}</span>
                {" — "}
                {issue.message}
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Generate / Validate / Export */}
      <SectionHeader title="Actions" />
      <div className="flex flex-col gap-2 px-3 py-3">
        <Button
          onClick={onGenerate}
          loading={generating}
          className="w-full"
        >
          Generate
        </Button>
        <Button
          variant="secondary"
          onClick={onValidate}
          loading={validating}
          className="w-full"
        >
          Validate only
        </Button>
        <Button
          variant="secondary"
          onClick={onExport}
          loading={exporting}
          disabled={!canExport}
          title={canExport ? "Download ZIP export bundle" : "Generate first"}
          className="w-full"
        >
          Export ZIP
        </Button>
        {!canExport && result && (
          <p className="text-xs text-gray-400">
            Fix validation errors before exporting.
          </p>
        )}
      </div>

      {/* Save */}
      <SectionHeader title="Save" />
      <div className="flex flex-col gap-2 px-3 py-3">
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
              <Button size="sm" variant="ghost" onClick={() => setShowVersionForm(false)}>
                Cancel
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Left panel — config form
// ─────────────────────────────────────────────────────────────────────────────

function SectionHeader({ title }: { title: string }) {
  return (
    <div className="border-b border-gray-100 bg-gray-50 px-4 py-2">
      <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500">{title}</h3>
    </div>
  );
}

function FieldRow({ children }: { children: React.ReactNode }) {
  return <div className="flex flex-col gap-3 px-4 py-4">{children}</div>;
}

function Num({
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

function ConfigPanel({
  config, onProjectChange, onBoundaryChange, onPatternChange,
  onMaterialChange, onToolChange, onLayoutChange, onExportChange,
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
  const u = config.project.units;

  return (
    <div>
      {/* Setup */}
      <SectionHeader title="Setup" />
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
        <Select label="Type" value={config.boundary.type}
          onChange={(e) => onBoundaryChange({ type: e.target.value as CanonicalConfig["boundary"]["type"] })}>
          <option value="rectangle">Rectangle</option>
          <option value="rounded_rectangle">Rounded Rectangle</option>
          <option value="svg_import">SVG Import</option>
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

      {/* Pattern */}
      <SectionHeader title="Pattern" />
      <FieldRow>
        <Select label="Family" value={config.pattern.family}
          onChange={(e) => onPatternChange({ family: e.target.value as PatternFamily })}>
          {(Object.entries(PATTERN_LABELS) as [PatternFamily, string][]).map(([v, l]) => (
            <option key={v} value={v}>{l}</option>
          ))}
        </Select>
        <Num label="Density" value={config.pattern.density}
          onChange={(v) => onPatternChange({ density: v })} min={0} max={1} step={0.05} hint="0–1" />
        <Num label={`Spacing (${u})`} value={config.pattern.spacing}
          onChange={(v) => onPatternChange({ spacing: v })} min={0.01} />
        <Num label={`Line width (${u})`} value={config.pattern.line_width}
          onChange={(v) => onPatternChange({ line_width: v })} min={0.01} />
        <Num label={`Amplitude (${u})`} value={config.pattern.amplitude}
          onChange={(v) => onPatternChange({ amplitude: v })} min={0} />
        <Input label="Seed" type="number" value={config.pattern.seed}
          min={0} step={1} hint="Determinism seed"
          onChange={(e) => { const v = parseInt(e.target.value, 10); if (!isNaN(v)) onPatternChange({ seed: v }); }} />
        <Select label="Symmetry" value={config.pattern.symmetry}
          onChange={(e) => onPatternChange({ symmetry: e.target.value as CanonicalConfig["pattern"]["symmetry"] })}>
          <option value="none">None</option>
          <option value="x">X axis</option>
          <option value="y">Y axis</option>
          <option value="xy">XY (both)</option>
        </Select>
      </FieldRow>

      {/* Material */}
      <SectionHeader title="Material" />
      <FieldRow>
        <Num label={`Thickness (${u})`} value={config.fabrication.material.thickness}
          onChange={(v) => onMaterialChange({ thickness: v })} min={0.01} />
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
        <label className="flex items-center gap-2 text-sm text-gray-700">
          <input type="checkbox" checked={config.layout.enabled}
            onChange={(e) => onLayoutChange({ enabled: e.target.checked })}
            className="rounded border-gray-300 text-brand-600 focus:ring-brand-500" />
          Enable layout
        </label>
        <Num label="Copies" value={config.layout.copies}
          onChange={(v) => onLayoutChange({ copies: Math.max(1, Math.round(v)) })} min={1} step={1} />
        <Select label="Rotation mode" value={config.layout.rotation_mode}
          onChange={(e) => onLayoutChange({ rotation_mode: e.target.value as CanonicalConfig["layout"]["rotation_mode"] })}>
          <option value="none">None</option>
          <option value="90_only">90° only</option>
          <option value="any">Any</option>
        </Select>
        <label className="flex items-center gap-2 text-sm text-gray-700">
          <input type="checkbox" checked={config.layout.preserve_grain}
            onChange={(e) => onLayoutChange({ preserve_grain: e.target.checked })}
            className="rounded border-gray-300 text-brand-600 focus:ring-brand-500" />
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
              <input type="checkbox" checked={config.export.formats.includes(fmt)}
                onChange={(e) => {
                  const formats = e.target.checked
                    ? [...config.export.formats, fmt]
                    : config.export.formats.filter((f) => f !== fmt);
                  if (formats.length > 0) onExportChange({ formats });
                }}
                className="rounded border-gray-300 text-brand-600 focus:ring-brand-500" />
              {fmt.toUpperCase()}
            </label>
          ))}
        </div>
      </FieldRow>
      <div className="h-8" />
    </div>
  );
}
