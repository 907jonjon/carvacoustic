"use client";

export interface ValidationIssue {
  level: "error" | "warning" | "info";
  code: string;
  message: string;
  field?: string | null;
}

export interface GenerateResult {
  status: "ok" | "error";
  message?: string;
  validation?: { valid: boolean; issues: ValidationIssue[] };
  svg_preview?: string;
  cut_preview_svg?: string;
  sheet_count?: number;
  sheet_utilization?: number;
  part_count?: number;
  slat_count?: number;
  has_backing?: boolean;
  layout_engine?: string;
  generated_at?: string;
}

export function SvgPreview({
  result,
  previewMode = "design",
}: {
  result: GenerateResult | null;
  previewMode?: "design" | "cut";
}) {
  const svgContent =
    previewMode === "cut" ? result?.cut_preview_svg : result?.svg_preview;

  if (!svgContent) {
    const emptyMessage =
      previewMode === "cut"
        ? "Click Prepare Review to see sheet cut layout"
        : "Click Prepare Review to see slat design preview";
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-3 text-center p-8 h-full">
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
        <p className="text-sm text-gray-400">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col h-full">
      {result?.validation && (
        <div className="flex items-center gap-3 border-b border-gray-100 bg-white px-4 py-2 text-xs text-gray-500">
          <span className={result.validation.valid ? "text-green-600" : "text-red-600"}>
            {result.validation.valid ? "Valid" : "Has errors"}
          </span>
        </div>
      )}
      <div
        className="flex-1 p-4"
        /* SVG from our own geometry service -- safe to render inline */
        dangerouslySetInnerHTML={{ __html: svgContent }}
      />
      {previewMode === "cut" && (
        <div className="flex items-center gap-4 border-t border-gray-100 bg-white px-4 py-2 text-xs text-gray-500">
          <span className="flex items-center gap-1.5">
            <span className="inline-block h-0.5 w-4" style={{ backgroundColor: "#cc3333" }} />
            Slat cut paths
          </span>
          <span className="flex items-center gap-1.5">
            <span className="inline-block h-0.5 w-4" style={{ backgroundColor: "#339933" }} />
            Backing / slot cuts
          </span>
          <span className="flex items-center gap-1.5">
            <span className="inline-block h-3 w-4 border border-gray-400 bg-gray-200" />
            Sheet boundary
          </span>
        </div>
      )}
    </div>
  );
}
