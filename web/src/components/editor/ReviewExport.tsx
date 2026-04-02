"use client";

import { useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { SectionHeader } from "./FormControls";
import { enableBilling } from "@/lib/flags";
import type { GenerateResult } from "./SvgPreview";
import type { CanonicalConfig } from "@/types/schema";

const ISSUE_COLOURS: Record<string, string> = {
  error:   "text-red-700 bg-red-50 border-red-200",
  warning: "text-amber-700 bg-amber-50 border-amber-200",
  info:    "text-blue-700 bg-blue-50 border-blue-200",
};

const FEEDBACK_CATEGORIES = ["Bug", "Feature Request", "Usability", "Other"] as const;

export function ReviewExport({
  result,
  actionError,
  generating,
  validating,
  exporting,
  saveStatus,
  saveError,
  latestVersionNumber,
  projectId,
  config,
  hasReviewedCutLayout,
  onGenerate,
  onValidate,
  onExport,
  onSaveDraft,
  onSaveVersion,
  onViewCutLayout,
}: {
  result: GenerateResult | null;
  actionError: string | null;
  generating: boolean;
  validating: boolean;
  exporting: boolean;
  saveStatus: "idle" | "saving" | "saved" | "error";
  saveError: string | null;
  latestVersionNumber: number;
  projectId: string;
  config: CanonicalConfig;
  hasReviewedCutLayout: boolean;
  onGenerate: () => void;
  onValidate: () => void;
  onExport: () => void;
  onSaveDraft: () => void;
  onSaveVersion: (notes: string) => void;
  onViewCutLayout: () => void;
}) {
  const [versionNotes, setVersionNotes] = useState("");
  const [showVersionForm, setShowVersionForm] = useState(false);

  // Feedback state
  const [fbCategory, setFbCategory] = useState<string>(FEEDBACK_CATEGORIES[0]);
  const [fbMessage, setFbMessage] = useState("");
  const [fbStatus, setFbStatus] = useState<"idle" | "sending" | "sent" | "error">("idle");
  const [fbError, setFbError] = useState<string | null>(null);

  const issues = result?.validation?.issues ?? [];
  const errors = issues.filter((i) => i.level === "error");
  const warnings = issues.filter((i) => i.level === "warning");
  const infos = issues.filter((i) => i.level === "info");

  const resultValid = result?.status === "ok" && result.validation?.valid !== false;
  const canExport = resultValid && hasReviewedCutLayout;

  // Export button tooltip
  const exportTitle = !result
    ? "Generate design first"
    : !resultValid
      ? "Fix errors above before exporting"
      : !hasReviewedCutLayout
        ? "Review the cut layout before exporting"
        : "Export ZIP bundle";

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
            Adjust your design on the left, then click Generate Design.
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
          Generate Design
        </Button>
        <Button
          variant="secondary"
          onClick={onValidate}
          loading={validating}
          className="w-full"
        >
          Validate Design
        </Button>
        <Link
          href={`/app/projects/${projectId}/review`}
          className="w-full"
          onClick={onViewCutLayout}
        >
          <Button variant="secondary" className="w-full">
            View Cut Layout →
          </Button>
        </Link>
        <Button
          variant="secondary"
          onClick={onExport}
          loading={exporting}
          disabled={!canExport}
          title={exportTitle}
          className="w-full"
        >
          Export Cut Files
        </Button>
        {!canExport && result && resultValid && !hasReviewedCutLayout && (
          <p className="text-xs text-gray-400">
            Review the cut layout before exporting.
          </p>
        )}
        {!canExport && result && !resultValid && (
          <p className="text-xs text-gray-400">
            Fix errors above before exporting.
          </p>
        )}
        {!canExport && enableBilling && (
          <p className="text-xs text-gray-500">
            Free plan: 3 exports per month. Upgrade to Pro for unlimited
            exports.{" "}
            <Link
              href="/app/billing"
              className="font-medium text-brand-600 hover:text-brand-700"
            >
              Upgrade
            </Link>
          </p>
        )}
        {result && result.status === "ok" && (
          <p className="mt-1 rounded bg-gray-50 px-2 py-1.5 text-xs text-gray-500">
            {result.slat_count ?? 0} slats, {result.sheet_count ?? 0} sheet{(result.sheet_count ?? 0) !== 1 ? "s" : ""}, {Math.round((result.sheet_utilization ?? 0) * 100)}% utilization
            {result.layout_engine && (
              <span className={`ml-2 inline-block rounded px-1.5 py-0.5 text-[10px] font-medium uppercase ${
                result.layout_engine === "nesting"
                  ? "bg-green-100 text-green-700"
                  : "bg-amber-100 text-amber-700"
              }`}>
                {result.layout_engine === "nesting" ? "nesting engine" : "FFD fallback"}
              </span>
            )}
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

      {/* Feedback */}
      <SectionHeader title="Send Feedback" />
      <div className="flex flex-col gap-2 px-3 py-3">
        {fbStatus === "sent" && (
          <p className="text-xs text-green-600">Feedback submitted. Thank you!</p>
        )}
        {fbStatus === "error" && fbError && (
          <p className="text-xs text-red-600">{fbError}</p>
        )}
        <select
          value={fbCategory}
          onChange={(e) => setFbCategory(e.target.value)}
          className="block w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
        >
          {FEEDBACK_CATEGORIES.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
        <textarea
          value={fbMessage}
          onChange={(e) => setFbMessage(e.target.value)}
          placeholder="Describe the issue or suggestion..."
          rows={3}
          maxLength={2000}
          className="block w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
        />
        <Button
          size="sm"
          variant="secondary"
          loading={fbStatus === "sending"}
          disabled={!fbMessage.trim()}
          onClick={async () => {
            setFbStatus("sending");
            setFbError(null);
            try {
              const res = await fetch("/api/feedback", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                  category: fbCategory,
                  message: fbMessage,
                  project_id: projectId,
                  config_snapshot: config,
                }),
              });
              if (!res.ok) {
                const d = await res.json();
                throw new Error(d?.error?.message ?? "Submit failed.");
              }
              setFbStatus("sent");
              setFbMessage("");
              setTimeout(() => setFbStatus("idle"), 3000);
            } catch (err) {
              setFbStatus("error");
              setFbError(err instanceof Error ? err.message : "Submit failed.");
            }
          }}
          className="w-full"
        >
          Submit Feedback
        </Button>
      </div>
    </div>
  );
}
