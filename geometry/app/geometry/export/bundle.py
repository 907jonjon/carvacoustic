"""
Export bundle assembly — Milestone C.

Bundle contents:
  manifest.json        — metadata and file inventory
  project-config.json  — the canonical config that produced this bundle
  sheet-NN.dxf         — per-sheet DXF with all spec layers (one per layout sheet)
  sheet-NN.svg         — per-sheet standalone SVG
  reference.pdf        — reference sheet with project metadata and design preview
  README.txt           — human-readable handoff notes for Vectric
"""

from __future__ import annotations

import io
import json
import re
import zipfile
from datetime import datetime, timezone

from shapely import affinity
from shapely.geometry import Polygon

from ...models import CanonicalConfig, ExportManifest
from ..layout import LayoutResult, PartPlacement, run_layout
from .dxf_export import create_dxf
from .svg_export import generate_file_svg
from .pdf_export import create_reference_pdf

_README_TEMPLATE = """\
CarvAcoustic Export Bundle
==========================
Project : {project_name}
Mode    : {mode}
Units   : {units}
Generated: {generated_at}

Files
-----
{file_list}

DXF Layers
----------
  CUT_OUTER           Outer panel boundary cut
  CUT_INNER           Pattern cut paths
  ENGRAVE_LABEL       Part labels (engrave only)
  REFERENCE_BOUNDARY  Reference outline (do not cut)
  SAFE_MARGIN_GUIDE   Safe margin guide (do not cut)

Vectric Handoff
---------------
1. Import sheet-01.dxf into Vectric Aspire / VCarve Pro.
2. Confirm job size and material settings.
3. Assign toolpaths to CUT_OUTER and CUT_INNER layers.
4. Do NOT assign toolpaths to REFERENCE_BOUNDARY or SAFE_MARGIN_GUIDE.
5. Run simulation before cutting.

CarvAcoustic does NOT generate G-code. All toolpath setup is done in Vectric.
"""


def build_export_bundle(
    config: CanonicalConfig,
    boundary_poly: Polygon,
    safe_poly: Polygon,
    bands: list[Polygon],
    labels: list[dict],
) -> tuple[bytes, str]:
    """
    Assemble the full export ZIP bundle.

    Runs the layout engine to place copies on sheets, then generates per-sheet
    DXF/SVG files plus the reference PDF.

    Returns (zip_bytes, filename).
    """
    units = config.project.units.value
    generated_at = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    iso_ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    safe_name = _safe_filename(config.project.name)
    zip_filename = f"carvacoustic-{safe_name}-{generated_at}.zip"

    # ── Run layout engine ─────────────────────────────────────────────────────
    layout_result: LayoutResult = run_layout(boundary_poly, config)

    # If layout is disabled or returned no sheets, produce a single sheet with
    # the design at its natural position
    if not layout_result.sheets:
        layout_result = _single_sheet_fallback(boundary_poly)

    # ── Build per-sheet artifacts ─────────────────────────────────────────────
    sheet_files: list[str] = []
    sheet_artifacts: dict[str, bytes] = {}

    minx, miny, maxx, maxy = boundary_poly.bounds
    design_h = maxy - miny

    for sheet in layout_result.sheets:
        idx = sheet.sheet_index
        sheet_label = f"sheet-{idx:02d}"

        # Collect transformed geometry for this sheet
        s_boundaries: list[Polygon] = []
        s_safe_polys: list[Polygon] = []
        s_bands: list[Polygon] = []
        s_labels: list[dict] = []

        for placement in sheet.placements:
            tb = _transform_geom(boundary_poly, placement, minx, miny, design_h)
            ts = _transform_geom(safe_poly, placement, minx, miny, design_h)
            if isinstance(tb, Polygon) and not tb.is_empty:
                s_boundaries.append(tb)
            if isinstance(ts, Polygon) and not ts.is_empty:
                s_safe_polys.append(ts)
            for band in bands:
                tband = _transform_geom(band, placement, minx, miny, design_h)
                if isinstance(tband, Polygon) and not tband.is_empty:
                    s_bands.append(tband)
            for lbl in labels:
                s_labels.append(_transform_label(lbl, placement, minx, miny, design_h))

        if not s_boundaries:
            continue

        dxf_bytes = create_dxf(s_boundaries, s_safe_polys, s_bands, s_labels, units)
        svg_string = generate_file_svg(s_boundaries, s_safe_polys, s_bands, s_labels, units)

        dxf_name = f"{sheet_label}.dxf"
        svg_name = f"{sheet_label}.svg"

        sheet_artifacts[dxf_name] = dxf_bytes
        sheet_artifacts[svg_name] = svg_string.encode("utf-8")
        sheet_files += [dxf_name, svg_name]

    # ── Reference PDF ─────────────────────────────────────────────────────────
    pdf_bytes = create_reference_pdf(
        config=config,
        boundary_poly=boundary_poly,
        safe_poly=safe_poly,
        bands=bands,
        labels=labels,
        generated_at=iso_ts,
    )

    # ── Manifest ──────────────────────────────────────────────────────────────
    all_files = (
        ["manifest.json", "project-config.json"]
        + sheet_files
        + ["reference.pdf", "README.txt"]
    )
    manifest = ExportManifest(
        schema_version="1.0.0",
        project_name=config.project.name,
        mode=config.project.mode,
        units=config.project.units,
        generated_at=iso_ts,
        files=all_files,
    )

    # ── README ────────────────────────────────────────────────────────────────
    file_list_txt = "\n".join(f"  {f}" for f in all_files)
    readme = _README_TEMPLATE.format(
        project_name=config.project.name,
        mode=config.project.mode.value,
        units=units,
        generated_at=iso_ts,
        file_list=file_list_txt,
        schema_version=config.schema_version,
    )

    # ── Assemble ZIP ──────────────────────────────────────────────────────────
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", manifest.model_dump_json(indent=2))
        zf.writestr("project-config.json", config.model_dump_json(indent=2))
        for fname, fbytes in sheet_artifacts.items():
            zf.writestr(fname, fbytes)
        zf.writestr("reference.pdf", pdf_bytes)
        zf.writestr("README.txt", readme.encode("utf-8"))

    return buf.getvalue(), zip_filename


# ---------------------------------------------------------------------------
# Geometry transform helpers
# ---------------------------------------------------------------------------


def _transform_geom(
    geom: Polygon,
    placement: PartPlacement,
    minx: float,
    miny: float,
    design_h: float,
) -> Polygon:
    """
    Transform a polygon from panel space to sheet space.

    Steps:
    1. Normalize panel origin to (0, 0) via translate(-minx, -miny).
    2. Optionally rotate 90° CCW around origin, then shift back to positive quadrant.
    3. Translate to placement position on sheet.
    """
    g = affinity.translate(geom, xoff=-minx, yoff=-miny)
    if placement.rotated_90:
        g = affinity.rotate(g, 90, origin=(0.0, 0.0), use_radians=False)
        # After 90° CCW: x in [-design_h, 0]; shift back to [0, design_h]
        g = affinity.translate(g, xoff=design_h, yoff=0.0)
    g = affinity.translate(g, xoff=placement.x, yoff=placement.y)
    return g  # type: ignore[return-value]


def _transform_label(
    lbl: dict,
    placement: PartPlacement,
    minx: float,
    miny: float,
    design_h: float,
) -> dict:
    """Apply the same transform as _transform_geom to a label dict."""
    x = lbl["x"] - minx
    y = lbl["y"] - miny
    if placement.rotated_90:
        x, y = -y + design_h, x
    return {**lbl, "x": x + placement.x, "y": y + placement.y}


def _single_sheet_fallback(boundary_poly: Polygon) -> LayoutResult:
    """
    When layout is disabled, place one copy at its natural origin on a
    single sheet so the export still produces a valid sheet-01 file.
    """
    from ..layout import LayoutResult, PartPlacement, SheetLayout
    minx, miny, _, _ = boundary_poly.bounds
    return LayoutResult(
        sheets=[
            SheetLayout(
                sheet_index=1,
                placements=[PartPlacement(copy_index=0, x=minx, y=miny, rotated_90=False)],
                utilization=1.0,
            )
        ]
    )


# ---------------------------------------------------------------------------
# Filename helper
# ---------------------------------------------------------------------------


def _safe_filename(name: str) -> str:
    """Sanitise project name for use in a filename."""
    sanitised = re.sub(r"[^a-zA-Z0-9_-]", "-", name)
    sanitised = re.sub(r"-{2,}", "-", sanitised).strip("-")
    return sanitised[:48] or "project"
