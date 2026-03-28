"use client";

import type { CanonicalConfig } from "@/types/schema";
import { SectionHeader, FieldRow } from "./FormControls";

export function ExportFormats({
  config,
  onExportChange,
}: {
  config: CanonicalConfig;
  onExportChange: (p: Partial<CanonicalConfig["export"]>) => void;
}) {
  return (
    <>
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
    </>
  );
}
