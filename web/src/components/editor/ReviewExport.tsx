"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { SectionHeader } from "./FormControls";
import type { GenerateResult } from "./SvgPreview";

const ISSUE_COLOURS: Record<string, string> = {
  error:   "text-red-700 bg-red-50 border-red-200",
  warning: "text-amber-700 bg-amber-50 border-amber-200",
  info:    "text-blue-700 bg-blue-50 border-blue-200",
};

export function ReviewExport({
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
        {issues.length === 0 && !actionError && !result && (
          <p className="text-xs text-gray-400">
            Click Prepare Review to generate design and cut previews.
          </p>
        )}
        {issues.length === 0 && !actionError && result && (
          <p className="text-xs text-gray-400">
            No validation issues found.
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
          Prepare Review
        </Button>
        <Button
          variant="secondary"
          onClick={onValidate}
          loading={validating}
          className="w-full"
        >
          Fabrication Check
        </Button>
        <Button
          variant="secondary"
          onClick={onExport}
          loading={exporting}
          disabled={!canExport}
          title={canExport ? "Download ZIP export bundle" : "Generate first"}
          className="w-full"
        >
          Download Cut Files
        </Button>
        {!canExport && result && (
          <p className="text-xs text-gray-400">
            Fix errors above before downloading cut files.
          </p>
        )}
        {result && result.status === "ok" && (
          <p className="mt-1 rounded bg-gray-50 px-2 py-1.5 text-xs text-gray-500">
            {result.slat_count ?? 0} slats, {result.sheet_count ?? 0} sheet{(result.sheet_count ?? 0) !== 1 ? "s" : ""}, {Math.round((result.sheet_utilization ?? 0) * 100)}% utilization
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
