"use client";

/**
 * Project Editor — thin orchestration shell.
 *
 * Workflow: Set panel size, shape the surface, review the cut layout,
 * then export CNC-ready files.
 */

import { useState } from "react";
import Link from "next/link";
import type { Database } from "@/types/database";
import type { CanonicalConfig } from "@/types/schema";
import { defaultConfig } from "@/types/schema";
import { Viewport } from "@/components/viewport/Viewport";

import { ProjectSetup, MODE_LABELS } from "@/components/editor/ProjectSetup";
import { SurfaceDesign } from "@/components/editor/SurfaceDesign";
import { SlatLayout } from "@/components/editor/SlatLayout";
import { MaterialTooling } from "@/components/editor/MaterialTooling";
import { ExportFormats } from "@/components/editor/ExportFormats";
import { ReviewExport } from "@/components/editor/ReviewExport";
import { SvgPreview } from "@/components/editor/SvgPreview";
import type { GenerateResult } from "@/components/editor/SvgPreview";

type Project = Database["public"]["Tables"]["projects"]["Row"];

export function ProjectEditor({
  project,
  latestVersionNumber,
}: {
  project: Project;
  latestVersionNumber: number;
}) {
  // Merge v2 defaults into stored config so v1 projects get surface/slats/backing
  const [config, setConfig] = useState<CanonicalConfig>(() => {
    const stored = project.draft_config as Partial<CanonicalConfig>;
    const defaults = defaultConfig(stored.project?.name ?? project.name);
    return { ...defaults, ...stored, surface: { ...defaults.surface, ...stored.surface }, slats: { ...defaults.slats, ...stored.slats }, backing: { ...defaults.backing, ...stored.backing } };
  });

  // View state
  const [viewMode, setViewMode] = useState<"3d" | "2d">("3d");
  const [showExploded, setShowExploded] = useState(false);
  const [showBacking, setShowBacking] = useState(true);

  // Save state
  const [saveStatus, setSaveStatus] = useState<"idle" | "saving" | "saved" | "error">("idle");
  const [saveError, setSaveError] = useState<string | null>(null);

  // 2D preview sub-tab
  const [previewTab, setPreviewTab] = useState<"design" | "cut">("design");

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
  const patchSurface = (p: Partial<CanonicalConfig["surface"]>) =>
    patch({ surface: { ...config.surface, ...p } });
  const patchSlats = (p: Partial<CanonicalConfig["slats"]>) =>
    patch({ slats: { ...config.slats, ...p } });
  const patchBacking = (p: Partial<CanonicalConfig["backing"]>) =>
    patch({ backing: { ...config.backing, ...p } });
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
        {/* LEFT: config form */}
        <aside className="w-72 shrink-0 overflow-y-auto border-r border-gray-200 bg-white">
          <div>
            <ProjectSetup
              config={config}
              onProjectChange={patchProject}
              onBoundaryChange={patchBoundary}
            />
            <SurfaceDesign
              config={config}
              onSurfaceChange={patchSurface}
            />
            <SlatLayout
              config={config}
              onSlatsChange={patchSlats}
              onBackingChange={patchBacking}
            />
            <MaterialTooling
              config={config}
              onMaterialChange={patchMaterial}
              onToolChange={patchTool}
              onLayoutChange={patchLayout}
            />
            <ExportFormats
              config={config}
              onExportChange={patchExport}
            />
            <div className="h-8" />
          </div>
        </aside>

        {/* CENTER: preview (3D or 2D) */}
        <main className="flex flex-1 flex-col bg-gray-50 overflow-hidden">
          {/* Toolbar */}
          <div className="flex items-center gap-2 border-b border-gray-100 bg-white px-4 py-1.5">
            <button
              onClick={() => setViewMode("3d")}
              className={`rounded px-3 py-1 text-xs font-medium transition-colors ${
                viewMode === "3d"
                  ? "bg-gray-900 text-white"
                  : "text-gray-500 hover:bg-gray-100"
              }`}
            >
              3D View
            </button>
            <button
              onClick={() => setViewMode("2d")}
              className={`rounded px-3 py-1 text-xs font-medium transition-colors ${
                viewMode === "2d"
                  ? "bg-gray-900 text-white"
                  : "text-gray-500 hover:bg-gray-100"
              }`}
            >
              2D Layout
            </button>

            {viewMode === "3d" && (
              <>
                <span className="ml-2 h-4 w-px bg-gray-200" />
                <label className="flex cursor-pointer items-center gap-1.5 text-xs text-gray-600">
                  <input
                    type="checkbox"
                    checked={showExploded}
                    onChange={(e) => setShowExploded(e.target.checked)}
                    className="rounded border-gray-300"
                  />
                  Exploded
                </label>
                <label className="flex cursor-pointer items-center gap-1.5 text-xs text-gray-600">
                  <input
                    type="checkbox"
                    checked={showBacking}
                    onChange={(e) => setShowBacking(e.target.checked)}
                    className="rounded border-gray-300"
                  />
                  Backing
                </label>
              </>
            )}

            {viewMode === "2d" && (
              <>
                <span className="ml-2 h-4 w-px bg-gray-200" />
                <button
                  onClick={() => setPreviewTab("design")}
                  className={`rounded px-2 py-0.5 text-xs font-medium transition-colors ${
                    previewTab === "design"
                      ? "bg-gray-200 text-gray-800"
                      : "text-gray-400 hover:bg-gray-100"
                  }`}
                >
                  Design Preview
                </button>
                <button
                  onClick={() => setPreviewTab("cut")}
                  className={`rounded px-2 py-0.5 text-xs font-medium transition-colors ${
                    previewTab === "cut"
                      ? "bg-gray-200 text-gray-800"
                      : "text-gray-400 hover:bg-gray-100"
                  }`}
                >
                  Cut Preview
                </button>
              </>
            )}

            {viewMode === "2d" && generateResult?.cut_preview_svg && (
              <span className="ml-auto flex items-center gap-2 text-xs text-gray-400">
                <span>{generateResult.sheet_count ?? 0} sheet{(generateResult.sheet_count ?? 0) !== 1 ? "s" : ""}</span>
                <span>&bull;</span>
                <span>{Math.round((generateResult.sheet_utilization ?? 0) * 100)}% utilization</span>
                <span>&bull;</span>
                <span>{generateResult.part_count ?? 0} parts</span>
                {generateResult.has_backing && (
                  <>
                    <span>&bull;</span>
                    <span>+ backing</span>
                  </>
                )}
              </span>
            )}
          </div>

          {/* Content */}
          <div className="flex-1 overflow-hidden">
            {viewMode === "3d" ? (
              <Viewport
                config={config}
                showExploded={showExploded}
                showBacking={showBacking}
              />
            ) : (
              <SvgPreview result={generateResult} previewMode={previewTab} />
            )}
          </div>
        </main>

        {/* RIGHT: review + export */}
        <aside className="w-64 shrink-0 overflow-y-auto border-l border-gray-200 bg-white">
          <ReviewExport
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
