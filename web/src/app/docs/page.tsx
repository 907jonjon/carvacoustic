import Link from "next/link";

export const metadata = { title: "Docs — CarvAcoustic" };

export default function DocsPage() {
  return (
    <main className="mx-auto w-full max-w-3xl px-6 py-12">
      <h1 className="text-3xl font-bold text-gray-900">CarvAcoustic Docs</h1>
      <p className="mt-2 text-gray-500">
        How to use CarvAcoustic to design and export decorative CNC panels.
      </p>

      <nav className="mt-8 flex flex-col gap-1 rounded-lg border border-gray-200 bg-gray-50 p-4 text-sm">
        <p className="font-semibold text-gray-700">On this page</p>
        <a href="#overview" className="text-brand-600 hover:underline">Overview</a>
        <a href="#workflow" className="text-brand-600 hover:underline">Workflow</a>
        <a href="#patterns" className="text-brand-600 hover:underline">Pattern families</a>
        <a href="#fabrication" className="text-brand-600 hover:underline">Fabrication settings</a>
        <a href="#export" className="text-brand-600 hover:underline">Export bundle</a>
        <a href="#vectric" className="text-brand-600 hover:underline">Vectric handoff</a>
        <a href="#validation" className="text-brand-600 hover:underline">Validation reference</a>
      </nav>

      <Section id="overview" title="Overview">
        <p>
          CarvAcoustic generates Vectric-ready DXF, SVG, and PDF output for decorative
          CNC panels. You configure the design in the browser, click Generate to preview,
          then Export to download a ZIP bundle ready to import into Vectric Aspire or VCarve Pro.
        </p>
        <p className="mt-2">
          CarvAcoustic covers the design side only — toolpath setup, simulation, tabs, and
          G-code are done in Vectric as usual.
        </p>
        <div className="mt-3 rounded border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
          Phase 1 scope: wall art, cabinet front panels, architectural face panels.
          Acoustic panels are not yet supported.
        </div>
      </Section>

      <Section id="workflow" title="Workflow">
        <ol className="flex flex-col gap-3 text-sm text-gray-700">
          {[
            ["Create a project", "From the dashboard, click New project. Choose a mode and units (inches or mm)."],
            ["Configure the design", "In the editor, set your boundary dimensions, choose a pattern family, and tune the pattern and fabrication settings."],
            ["Generate", "Click Generate in the right panel. The centre panel shows an SVG preview with the boundary, safe margin, and cut geometry."],
            ["Validate", "Click Validate only to check the config without re-generating. Errors block export; warnings are advisory."],
            ["Save a draft", "Click Save draft to persist your current settings. Your work is stored in the cloud."],
            ["Save a checkpoint", "Click Save checkpoint to create an immutable version snapshot. Checkpoints are never overwritten."],
            ["Export", "Once there are no errors, click Export ZIP to download the bundle. The button is disabled until the design validates."],
            ["Import into Vectric", "Open the DXF in Vectric, confirm job size and layers, set up toolpaths, and run simulation."],
          ].map(([step, desc], i) => (
            <li key={i} className="flex gap-3">
              <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-brand-600 text-xs font-bold text-white">
                {i + 1}
              </span>
              <span>
                <strong>{step}.</strong> {desc}
              </span>
            </li>
          ))}
        </ol>
      </Section>

      <Section id="patterns" title="Pattern families">
        <p className="text-sm text-gray-600 mb-4">
          Three pattern families are available in phase 1. Choose via the Pattern → Family field.
        </p>
        <div className="flex flex-col gap-4">
          <PatternCard
            name="Wave Field"
            value="wave_field"
            description="Repeated horizontal guide lines displaced by a sine wave. Controls: density (wave frequency), amplitude (wave height), spacing (line separation), line_width (cut width), symmetry (mirror mode), seed (determinism)."
          />
          <PatternCard
            name="Contour Bands"
            value="contour_bands"
            description="Concentric offset rings inset from the panel boundary. Natural fit for oval or shaped panels. Controls: spacing (ring separation), line_width (band width). Amplitude is not used."
          />
          <PatternCard
            name="Slat Rib"
            value="slat_rib"
            description="Parallel slat members running horizontally (grain X) or vertically (grain Y). Lightly curved when amplitude > 0. Controls: spacing, line_width, amplitude, density, seed."
          />
        </div>
      </Section>

      <Section id="fabrication" title="Fabrication settings">
        <p className="text-sm text-gray-600 mb-3">
          Fabrication settings are used for validation and sheet layout. They are passed
          through to the export for reference in Vectric.
        </p>
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="border-b border-gray-200 text-left">
              <th className="py-2 pr-4 font-semibold text-gray-700">Setting</th>
              <th className="py-2 font-semibold text-gray-700">Purpose</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 text-gray-600">
            {[
              ["Thickness", "Material thickness — reference only, not used in geometry."],
              ["Sheet width / height", "Physical sheet size for layout engine."],
              ["Min bridge", "Minimum safe material bridge between cuts. Triggers warning if bridging is thinner."],
              ["Grain direction", "Affects slat_rib orientation and rotation lock."],
              ["Tool diameter", "Minimum feature size. line_width must be ≥ tool_diameter."],
              ["Kerf allowance", "Extra offset to compensate for tool kerf. Currently informational only."],
              ["Min inside radius", "Smallest inside corner the tool can clear. Triggers error if geometry is tighter."],
              ["Dogbone style", "Classic or none. Info message shown when none."],
              ["Clearance", "Gap between copies when multiple copies are laid out on sheets."],
              ["Border gap", "Gap between the sheet edge and the nearest panel boundary."],
            ].map(([s, d]) => (
              <tr key={s}>
                <td className="py-1.5 pr-4 font-mono text-xs">{s}</td>
                <td className="py-1.5">{d}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>

      <Section id="export" title="Export bundle">
        <p className="text-sm text-gray-600 mb-3">
          The Export ZIP contains all files needed for Vectric and your own records.
        </p>
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="border-b border-gray-200 text-left">
              <th className="py-2 pr-4 font-semibold text-gray-700">File</th>
              <th className="py-2 font-semibold text-gray-700">Contents</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 text-gray-600">
            {[
              ["sheet-NN.dxf", "Cut geometry — import into Vectric. One file per sheet."],
              ["sheet-NN.svg", "SVG version of the same geometry for reference."],
              ["reference.pdf", "Two-page reference sheet: settings summary + layer legend + Vectric instructions."],
              ["manifest.json", "Machine-readable file list with project metadata."],
              ["project-config.json", "Full canonical config that produced this bundle. Reproducible."],
              ["README.txt", "Plain-text handoff instructions."],
            ].map(([f, d]) => (
              <tr key={f}>
                <td className="py-1.5 pr-4 font-mono text-xs">{f}</td>
                <td className="py-1.5">{d}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="mt-3 text-sm text-gray-600">
          DXF layers in every sheet file:
        </p>
        <table className="mt-2 w-full text-sm border-collapse">
          <tbody className="divide-y divide-gray-100 text-gray-600">
            {[
              ["CUT_OUTER", "Red", "Panel boundary — outer profile cut"],
              ["CUT_INNER", "Blue", "Pattern cut paths"],
              ["ENGRAVE_LABEL", "Green", "Part labels — engrave or surface mark"],
              ["REFERENCE_BOUNDARY", "White/Black", "Original boundary — do not cut"],
              ["SAFE_MARGIN_GUIDE", "Grey (dashed)", "Safe margin inset — do not cut"],
            ].map(([l, c, d]) => (
              <tr key={l}>
                <td className="py-1.5 pr-3 font-mono text-xs">{l}</td>
                <td className="py-1.5 pr-3 text-xs text-gray-400">{c}</td>
                <td className="py-1.5">{d}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>

      <Section id="vectric" title="Vectric handoff">
        <ol className="flex flex-col gap-2 text-sm text-gray-700">
          {[
            "Open Vectric Aspire or VCarve Pro.",
            "File → Import Vectors → select sheet-01.dxf.",
            "Verify the job size matches your sheet dimensions.",
            "Confirm all five layers imported correctly.",
            "Assign toolpaths to CUT_OUTER and CUT_INNER layers only.",
            "Do not assign toolpaths to REFERENCE_BOUNDARY or SAFE_MARGIN_GUIDE.",
            "Add tabs and hold-downs as needed for your material and machine.",
            "Run simulation, then post-process for your controller.",
          ].map((s, i) => (
            <li key={i} className="flex gap-2">
              <span className="text-gray-400 tabular-nums">{i + 1}.</span>
              {s}
            </li>
          ))}
        </ol>
        <div className="mt-4 rounded border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-600">
          <strong>CarvAcoustic does not generate G-code.</strong> All toolpath
          setup, simulation, and post-processing are done in Vectric as usual.
        </div>
      </Section>

      <Section id="validation" title="Validation reference">
        <p className="text-sm text-gray-600 mb-3">
          Errors block export. Warnings are advisory. Info messages are for your reference.
        </p>
        <div className="flex flex-col gap-4">
          <IssueGroup
            level="error"
            colour="red"
            items={[
              ["feature_below_minimum", "line_width is smaller than tool_diameter. The tool cannot cut this feature. Increase line_width or use a smaller tool."],
              ["impossible_inside_radius", "The tightest inside radius is smaller than min_inside_radius. Increase line_width or reduce min_inside_radius."],
              ["invalid_boundary", "The boundary shape is invalid, self-intersecting, or the safe_margin consumes too much area."],
              ["thin_bridge", "Pattern spacing ≤ line_width — bands overlap and no material bridge remains."],
              ["open_cut_geometry", "One or more cut features have open (non-closed) geometry."],
            ]}
          />
          <IssueGroup
            level="warning"
            colour="amber"
            items={[
              ["thin_bridge", "Bridge width is less than min_bridge. The part may be fragile. Increase spacing or reduce line_width."],
              ["amplitude_exceeds_margin", "Wave amplitude is larger than safe_margin. Some peaks will be clipped."],
              ["high_part_count", "More than 200 cut features. Machining time may be very long."],
              ["very_small_part", "One or more features are smaller than tool_diameter². They may not cut cleanly."],
              ["low_material_utilization", "Cut area is less than 5% of panel area. Consider increasing density."],
            ]}
          />
          <IssueGroup
            level="info"
            colour="blue"
            items={[
              ["dogbones_not_applied", "Dogbone relief is off. Acceptable for decorative surface panels."],
            ]}
          />
        </div>
      </Section>

      <div className="mt-12 border-t border-gray-100 pt-6 text-sm text-gray-400">
        <Link href="/app" className="text-brand-600 hover:underline">
          ← Back to dashboard
        </Link>
      </div>
    </main>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Sub-components
// ─────────────────────────────────────────────────────────────────────────────

function Section({
  id,
  title,
  children,
}: {
  id: string;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section id={id} className="mt-10 scroll-mt-6">
      <h2 className="text-xl font-bold text-gray-900">{title}</h2>
      <div className="mt-3">{children}</div>
    </section>
  );
}

function PatternCard({
  name,
  value,
  description,
}: {
  name: string;
  value: string;
  description: string;
}) {
  return (
    <div className="rounded-lg border border-gray-200 p-4">
      <div className="flex items-center gap-2">
        <span className="font-semibold text-gray-900">{name}</span>
        <code className="rounded bg-gray-100 px-1.5 py-0.5 text-xs text-gray-600">
          {value}
        </code>
      </div>
      <p className="mt-1 text-sm text-gray-600">{description}</p>
    </div>
  );
}

function IssueGroup({
  level,
  colour,
  items,
}: {
  level: string;
  colour: "red" | "amber" | "blue";
  items: [string, string][];
}) {
  const header: Record<string, string> = {
    error: "bg-red-50 border-red-200 text-red-800",
    warning: "bg-amber-50 border-amber-200 text-amber-800",
    info: "bg-blue-50 border-blue-200 text-blue-800",
  };
  return (
    <div>
      <p className={`mb-2 inline-block rounded border px-2 py-0.5 text-xs font-semibold uppercase ${header[level]}`}>
        {level}
      </p>
      <div className="flex flex-col gap-2">
        {items.map(([code, desc]) => (
          <div key={code} className="flex gap-3 text-sm">
            <code className="shrink-0 w-48 text-xs text-gray-500 mt-0.5">{code}</code>
            <span className="text-gray-700">{desc}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
