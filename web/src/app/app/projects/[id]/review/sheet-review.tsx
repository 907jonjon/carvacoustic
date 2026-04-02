"use client";

/**
 * Sheet Layout Review — dedicated pre-export review step.
 *
 * Shows each material sheet with placed parts, per-sheet utilization,
 * and layout controls. Users can adjust nesting parameters and re-generate
 * before downloading cut files.
 */

import { useState, useCallback, useRef } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
import { ProgressBar } from "@/components/ui/progress-bar";
import { SlidingPuzzle } from "@/components/editor/SlidingPuzzle";
import { useGenerateStream } from "@/hooks/useGenerateStream";
import type { Database } from "@/types/database";
import type { CanonicalConfig } from "@/types/schema";
import { defaultConfig } from "@/types/schema";

type Project = Database["public"]["Tables"]["projects"]["Row"];

export function SheetReview({ project }: { project: Project }) {
  // Merge stored config with defaults (same pattern as project-editor)
  const [config] = useState<CanonicalConfig>(() => {
    const stored = project.draft_config as Partial<CanonicalConfig>;
    const defaults = defaultConfig(stored.project?.name ?? project.name);
    return {
      ...defaults,
      ...stored,
      surface: { ...defaults.surface, ...stored.surface },
      slats: { ...defaults.slats, ...stored.slats },
      backing: { ...defaults.backing, ...stored.backing },
    };
  });

  const { generating, progress, result, error, generate, clearError, setResult } = useGenerateStream();
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);

  // Layout overrides
  const [rotationMode, setRotationMode] = useState(
    config.layout.rotation_mode ?? "90_only"
  );
  const [preserveGrain, setPreserveGrain] = useState(
    config.layout.preserve_grain ?? false
  );
  const [copies, setCopies] = useState(config.layout.copies ?? 1);
  const [nestingMode, setNestingMode] = useState(
    config.layout.nesting_mode ?? "balanced"
  );

  // Feedback auto-fill ref
  const feedbackRef = useRef<HTMLTextAreaElement>(null);
  const [feedbackCategory, setFeedbackCategory] = useState("Bug");
  const [feedbackMsg, setFeedbackMsg] = useState("");
  const [feedbackStatus, setFeedbackStatus] = useState<"idle" | "sending" | "sent" | "error">("idle");
  const [showFeedback, setShowFeedback] = useState(false);

  // Build config with current layout overrides
  const currentConfig = useCallback((): CanonicalConfig => {
    return {
      ...config,
      layout: {
        ...config.layout,
        rotation_mode: rotationMode,
        preserve_grain: preserveGrain,
        copies,
        nesting_mode: nestingMode,
      },
    };
  }, [config, rotationMode, preserveGrain, copies, nestingMode]);

  function handleGenerate() {
    generate(currentConfig());
  }

  function handleSendFeedback(errorMessage: string, errorCode: string, errorStep?: string) {
    const details = [
      `Error: ${errorMessage}`,
      `Code: ${errorCode}`,
      errorStep ? `Failed at: ${errorStep}` : null,
      `Project: ${project.name}`,
      `Rotation: ${rotationMode}`,
      `Grain lock: ${preserveGrain}`,
      `Copies: ${copies}`,
      `Sheet: ${config.fabrication.material.sheet_width}x${config.fabrication.material.sheet_height}`,
    ].filter(Boolean).join("\n");

    setFeedbackMsg(details);
    setFeedbackCategory("Bug");
    setShowFeedback(true);
    setTimeout(() => feedbackRef.current?.focus(), 100);
  }

  async function submitFeedback() {
    setFeedbackStatus("sending");
    try {
      const res = await fetch("/api/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          category: feedbackCategory,
          message: feedbackMsg,
          project_id: project.id,
        }),
      });
      if (!res.ok) throw new Error("Submit failed.");
      setFeedbackStatus("sent");
      setTimeout(() => { setShowFeedback(false); setFeedbackStatus("idle"); }, 3000);
    } catch {
      setFeedbackStatus("error");
    }
  }

  // Export / download ZIP
  async function handleExport() {
    setExporting(true);
    setExportError(null);
    try {
      const res = await fetch("/api/export", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ config: currentConfig() }),
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
      setExportError(err instanceof Error ? err.message : "Export failed.");
    } finally {
      setExporting(false);
    }
  }

  const issues = result?.validation?.issues ?? [];
  const errors = issues.filter((i) => i.level === "error");
  const warnings = issues.filter((i) => i.level === "warning");
  const canExport =
    result?.status === "ok" && result.validation?.valid !== false;

  return (
    <div className="flex h-[calc(100vh-3.5rem)] flex-col">
      {/* Header */}
      <div className="border-b border-gray-200 bg-white px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link
              href={`/app/projects/${project.id}/edit`}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              ← Back to editor
            </Link>
            <div className="h-5 w-px bg-gray-300" />
            <h1 className="text-lg font-semibold text-gray-900">
              Sheet Layout Review
            </h1>
            <span className="text-sm text-gray-500">{project.name}</span>
          </div>
          <div className="flex items-center gap-3">
            <Button
              variant="secondary"
              onClick={handleGenerate}
              loading={generating}
            >
              {result ? "Re-nest" : "Generate Layout"}
            </Button>
            <Button
              onClick={handleExport}
              loading={exporting}
              disabled={!canExport}
              title={
                canExport ? "Download ZIP export bundle" : "Generate first"
              }
            >
              Download Cut Files
            </Button>
          </div>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Left panel — layout controls */}
        <div className="w-72 shrink-0 overflow-y-auto border-r border-gray-200 bg-gray-50 p-4">
          <h2 className="mb-4 text-xs font-semibold uppercase tracking-wide text-gray-500">
            Layout Settings
          </h2>

          <div className="flex flex-col gap-4">
            <Select
              label="Rotation"
              value={rotationMode}
              onChange={(e) => setRotationMode(e.target.value as "none" | "90_only" | "any")}
            >
              <option value="none">None</option>
              <option value="90_only">90° only</option>
              <option value="any">Any angle</option>
            </Select>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="grain-lock"
                checked={preserveGrain}
                onChange={(e) => setPreserveGrain(e.target.checked)}
                className="h-4 w-4 rounded border-gray-300 text-brand-600 focus:ring-brand-500"
              />
              <label htmlFor="grain-lock" className="text-sm text-gray-700">
                Lock grain direction
              </label>
            </div>

            <div className="flex flex-col gap-1">
              <label
                htmlFor="copies"
                className="text-sm font-medium text-gray-700"
              >
                Copies
              </label>
              <input
                id="copies"
                type="number"
                min={1}
                max={100}
                value={copies}
                onChange={(e) =>
                  setCopies(Math.max(1, parseInt(e.target.value, 10) || 1))
                }
                className="block w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
              />
            </div>

            <Select
              label="Nesting Engine"
              value={nestingMode}
              onChange={(e) => setNestingMode(e.target.value as "fast" | "balanced" | "max_yield" | "ffd")}
            >
              <option value="fast">Fast — quick placement, lower utilization</option>
              <option value="balanced">Balanced — good utilization, moderate time</option>
              <option value="max_yield">Max Yield — best utilization, slower</option>
              <option value="ffd">FFD (legacy) — simple row packing, fastest</option>
            </Select>

            {/* Material info (read-only) */}
            <div className="mt-4 border-t border-gray-200 pt-4">
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
                Material
              </h3>
              <dl className="flex flex-col gap-1 text-sm text-gray-600">
                <div className="flex justify-between">
                  <dt>Sheet</dt>
                  <dd className="font-medium text-gray-900">
                    {config.fabrication.material.sheet_width} ×{" "}
                    {config.fabrication.material.sheet_height}{" "}
                    {config.project.units}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt>Thickness</dt>
                  <dd className="font-medium text-gray-900">
                    {config.fabrication.material.thickness}{" "}
                    {config.project.units}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt>Border gap</dt>
                  <dd className="font-medium text-gray-900">
                    {config.fabrication.tool.border_gap} {config.project.units}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt>Clearance</dt>
                  <dd className="font-medium text-gray-900">
                    {config.fabrication.tool.clearance} {config.project.units}
                  </dd>
                </div>
              </dl>
            </div>

            {/* Validation issues */}
            {issues.length > 0 && (
              <div className="mt-4 border-t border-gray-200 pt-4">
                <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
                  Validation
                </h3>
                <ul className="flex flex-col gap-1.5">
                  {errors.map((issue, i) => (
                    <li
                      key={`e-${i}`}
                      className="rounded border border-red-200 bg-red-50 px-2 py-1.5 text-xs text-red-700"
                    >
                      {issue.message}
                    </li>
                  ))}
                  {warnings.map((issue, i) => (
                    <li
                      key={`w-${i}`}
                      className="rounded border border-amber-200 bg-amber-50 px-2 py-1.5 text-xs text-amber-700"
                    >
                      {issue.message}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>

        {/* Main area — sheet cards */}
        <div className="flex-1 overflow-y-auto bg-gray-100 p-6">
          {/* Export error */}
          {exportError && (
            <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {exportError}
            </div>
          )}

          {/* Generation error with Try Again / Send Feedback */}
          {error && !generating && (
            <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-4">
              <p className="text-sm font-medium text-red-700">Generation failed</p>
              <p className="mt-1 text-sm text-red-600">{error.message}</p>
              {error.step && (
                <p className="mt-1 text-xs text-red-500">
                  Failed during: {error.step} ({error.percent ?? 0}% complete)
                </p>
              )}
              <div className="mt-3 flex gap-2">
                <Button
                  size="sm"
                  onClick={() => { clearError(); handleGenerate(); }}
                >
                  Try Again
                </Button>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => handleSendFeedback(error.message, error.code, error.step)}
                >
                  Send Feedback
                </Button>
              </div>
            </div>
          )}

          {/* Feedback form (shown when Send Feedback is clicked) */}
          {showFeedback && (
            <div className="mb-4 rounded-lg border border-gray-200 bg-white p-4">
              <h3 className="mb-2 text-sm font-medium text-gray-900">Report Issue</h3>
              {feedbackStatus === "sent" ? (
                <p className="text-sm text-green-600">Feedback submitted. Thank you!</p>
              ) : (
                <>
                  <textarea
                    ref={feedbackRef}
                    value={feedbackMsg}
                    onChange={(e) => setFeedbackMsg(e.target.value)}
                    rows={5}
                    className="mb-2 block w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                  />
                  <div className="flex gap-2">
                    <Button size="sm" onClick={submitFeedback} loading={feedbackStatus === "sending"}>
                      Submit
                    </Button>
                    <Button size="sm" variant="ghost" onClick={() => setShowFeedback(false)}>
                      Cancel
                    </Button>
                  </div>
                  {feedbackStatus === "error" && (
                    <p className="mt-1 text-xs text-red-600">Failed to submit. Please try again.</p>
                  )}
                </>
              )}
            </div>
          )}

          {/* Empty state */}
          {!result && !generating && !error && (
            <div className="flex flex-col items-center justify-center gap-4 py-20 text-center">
              <div className="rounded-lg border-2 border-dashed border-gray-300 p-12">
                <svg
                  className="mx-auto h-16 w-16 text-gray-300"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={1}
                >
                  <rect x="2" y="2" width="20" height="20" rx="1" />
                  <path d="M2 8h20M8 2v20" />
                </svg>
              </div>
              <p className="text-sm text-gray-500">
                Click <strong>Generate Layout</strong> to see how parts will be
                arranged on your material sheets.
              </p>
            </div>
          )}

          {/* Generating state — progress bar + puzzle */}
          {generating && (
            <div className="flex flex-col items-center justify-center gap-6 py-10">
              <div className="w-full max-w-md">
                <ProgressBar
                  percent={progress?.percent ?? 0}
                  label={progress?.name ?? "Starting..."}
                  stepInfo={progress ? `Step ${progress.step} of ${progress.totalSteps}` : undefined}
                />
              </div>
              <SlidingPuzzle />
            </div>
          )}

          {/* Results */}
          {result && result.status === "ok" && !generating && (
            <>
              {/* Summary bar */}
              <div className="mb-6 flex items-center gap-6 rounded-lg border border-gray-200 bg-white px-5 py-3">
                <div className="flex flex-col">
                  <span className="text-xs text-gray-500">Sheets</span>
                  <span className="text-lg font-semibold text-gray-900">
                    {result.sheet_count ?? 0}
                  </span>
                </div>
                <div className="h-8 w-px bg-gray-200" />
                <div className="flex flex-col">
                  <span className="text-xs text-gray-500">Parts</span>
                  <span className="text-lg font-semibold text-gray-900">
                    {result.slat_count ?? 0}
                    {result.has_backing ? " + backing" : ""}
                  </span>
                </div>
                <div className="h-8 w-px bg-gray-200" />
                <div className="flex flex-col">
                  <span className="text-xs text-gray-500">Utilization</span>
                  <span className="text-lg font-semibold text-gray-900">
                    {Math.round((result.sheet_utilization ?? 0) * 100)}%
                  </span>
                </div>
                {result.layout_engine && (
                  <>
                    <div className="h-8 w-px bg-gray-200" />
                    <div className="flex flex-col">
                      <span className="text-xs text-gray-500">Engine</span>
                      <span className={`mt-0.5 inline-block rounded px-2 py-0.5 text-xs font-medium uppercase ${
                        result.layout_engine === "ffd"
                          ? "bg-amber-100 text-amber-700"
                          : "bg-green-100 text-green-700"
                      }`}>
                        {result.layout_engine === "ffd" ? "FFD (legacy)" : result.layout_engine}
                      </span>
                    </div>
                  </>
                )}
                <div className="h-8 w-px bg-gray-200" />
                <div className="flex flex-1 flex-col">
                  <span className="text-xs text-gray-500">
                    Material utilization
                  </span>
                  <div className="mt-1 h-2 w-full rounded-full bg-gray-200">
                    <div
                      className="h-2 rounded-full bg-brand-600 transition-all"
                      style={{
                        width: `${Math.round((result.sheet_utilization ?? 0) * 100)}%`,
                      }}
                    />
                  </div>
                </div>
              </div>

              {/* Cut preview SVG */}
              {result.cut_preview_svg ? (
                <div className="rounded-lg border border-gray-200 bg-white p-4">
                  <div className="mb-3 flex items-center justify-between">
                    <h3 className="text-sm font-medium text-gray-900">
                      Sheet Layout
                    </h3>
                    <div className="flex items-center gap-4 text-xs text-gray-500">
                      <span className="flex items-center gap-1.5">
                        <span
                          className="inline-block h-0.5 w-4"
                          style={{ backgroundColor: "#cc3333" }}
                        />
                        Slat cut paths
                      </span>
                      <span className="flex items-center gap-1.5">
                        <span
                          className="inline-block h-0.5 w-4"
                          style={{ backgroundColor: "#339933" }}
                        />
                        Backing / slot cuts
                      </span>
                      <span className="flex items-center gap-1.5">
                        <span className="inline-block h-3 w-4 border border-gray-400 bg-gray-200" />
                        Sheet boundary
                      </span>
                    </div>
                  </div>
                  <div
                    className="w-full"
                    dangerouslySetInnerHTML={{
                      __html: result.cut_preview_svg,
                    }}
                  />
                </div>
              ) : (
                <div className="rounded-lg border border-gray-200 bg-white p-8 text-center text-sm text-gray-500">
                  No cut preview available. The geometry service may not have
                  returned sheet layout data.
                </div>
              )}
            </>
          )}

          {result && result.status === "error" && !generating && (
            <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center">
              <p className="text-sm font-medium text-red-700">
                Generation failed
              </p>
              <p className="mt-1 text-sm text-red-600">
                {result.message ?? "Unknown error. Check validation issues."}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
