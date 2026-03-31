"""
Export bundle assembly (v2 — slat pipeline).

Bundle contents:
  manifest.json        — metadata and file inventory
  project-config.json  — the canonical config that produced this bundle
  sheet-NN.dxf         — per-sheet DXF (slat profiles on CUT_OUTER, slots on CUT_SLOT)
  sheet-NN.svg         — per-sheet standalone SVG
  reference.pdf        — reference sheet with project metadata and design preview
  README.txt           — human-readable handoff notes for Vectric
"""

from __future__ import annotations

import io
import logging
import re
import zipfile
from datetime import datetime, timezone

from shapely import affinity
from shapely.geometry import Polygon

from ...models import CanonicalConfig, ExportManifest
from ..layout import LayoutResult, PartPlacement, SheetLayout
from ..pipeline import run_pipeline_internal
from ...nesting.ingest import run_nesting
from .dxf_export import _add_geometry, create_dxf
from .svg_export import generate_file_svg
from .pdf_export import create_reference_pdf

_log = logging.getLogger(__name__)

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
  CUT_OUTER           Slat profile outlines — assign outer cut toolpath
  CUT_SLOT            Backing board slot cuts — assign slot toolpath
  ENGRAVE_LABEL       Part labels (engrave only)
  REFERENCE_BOUNDARY  Reference outline (do not cut)
  SAFE_MARGIN_GUIDE   Safe margin guide (do not cut)

Assembly Notes
--------------
  Slats are numbered S001, S002, … from left to right.
  Mount slats in order onto the backing board.
  Tab direction: slats insert DOWN into backing board slots.

Vectric Handoff
---------------
1. Import sheet-01.dxf into Vectric Aspire / VCarve Pro.
2. Confirm job size and material settings.
3. Assign toolpaths to CUT_OUTER (profile) and CUT_SLOT (slots) layers.
4. Do NOT assign toolpaths to REFERENCE_BOUNDARY or SAFE_MARGIN_GUIDE.
5. Run simulation before cutting.

CarvAcoustic does NOT generate G-code. All toolpath setup is done in Vectric.
"""


def build_export_bundle(config: CanonicalConfig) -> tuple[bytes, str]:
    """
    Assemble the full export ZIP bundle for the v2 slat pipeline.
    Returns (zip_bytes, filename).
    """
    units = config.project.units.value
    generated_at = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    iso_ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    safe_name = _safe_filename(config.project.name)
    zip_filename = f"carvacoustic-{safe_name}-{generated_at}.zip"

    # ── Run geometry pipeline ─────────────────────────────────────────────────
    result = run_pipeline_internal(config)
    all_parts: list[dict] = result["parts"]
    slat_parts: list[dict] = result["slat_parts"]
    backing_part: dict | None = result["backing"]

    if not all_parts:
        raise ValueError("Pipeline produced no parts — cannot build export bundle.")

    # ── Layout slat parts onto sheets ─────────────────────────────────────────
    layout_result = run_nesting(all_parts, config)
    if not layout_result.sheets:
        layout_result = _single_part_fallback(all_parts)

    # ── Build per-sheet DXF/SVG ───────────────────────────────────────────────
    sheet_files: list[str] = []
    sheet_artifacts: dict[str, bytes] = {}
    sheet_warnings: list[str] = []

    for sheet in layout_result.sheets:
        idx = sheet.sheet_index
        sheet_label = f"sheet-{idx:02d}"

        try:
            s_slat_polys: list[Polygon] = []
            s_slot_polys: list[Polygon] = []
            s_labels: list[dict] = []

            for placement in sheet.placements:
                part = all_parts[placement.part_index]
                poly = part["polygon"]

                # Translate polygon from local space to sheet position
                minx, miny = poly.bounds[0], poly.bounds[1]
                tp = affinity.translate(poly, xoff=-minx + placement.x, yoff=-miny + placement.y)

                if placement.rotated_90:
                    tp = affinity.rotate(tp, 90, origin=(placement.x, placement.y), use_radians=False)

                if part["part_type"] == "backing":
                    s_slot_polys.append(tp)
                else:
                    s_slat_polys.append(tp)

                if "label" in part:
                    lbl = part["label"]
                    lx = lbl["x"] - minx + placement.x
                    ly = lbl["y"] - miny + placement.y
                    h = (poly.bounds[3] - poly.bounds[1]) * 0.05
                    s_labels.append({"text": lbl["text"], "x": lx, "y": ly, "height": h})

            if not s_slat_polys and not s_slot_polys:
                continue

            dxf_bytes = _create_slat_dxf(s_slat_polys, s_slot_polys, s_labels, units)
            svg_string = _create_slat_svg(s_slat_polys, s_slot_polys, s_labels, units)

            dxf_name = f"{sheet_label}.dxf"
            svg_name = f"{sheet_label}.svg"
            sheet_artifacts[dxf_name] = dxf_bytes
            sheet_artifacts[svg_name] = svg_string.encode("utf-8")
            sheet_files += [dxf_name, svg_name]

        except Exception as exc:
            _log.warning("Sheet %s export failed: %s", sheet_label, exc, exc_info=True)
            sheet_warnings.append(f"Sheet {idx} skipped: {exc}")
            continue

    if not sheet_artifacts:
        raise ValueError(
            "All sheets failed to export. "
            + (" | ".join(sheet_warnings) if sheet_warnings else "No sheet data produced.")
        )

    # ── Reference PDF ─────────────────────────────────────────────────────────
    from shapely.geometry import box as shapely_box

    preview_poly = (
        slat_parts[0]["polygon"]
        if slat_parts
        else shapely_box(0, 0, config.boundary.width, config.slats.base_height + 2)
    )

    pdf_bytes = create_reference_pdf(
        config=config,
        boundary_poly=preview_poly,
        safe_poly=preview_poly,
        bands=slat_parts[:5],  # show first 5 slat polygons as preview
        labels=[p.get("label") for p in slat_parts[:5] if "label" in p],
        generated_at=iso_ts,
    )

    # ── Manifest ──────────────────────────────────────────────────────────────
    all_files = (
        ["manifest.json", "project-config.json"]
        + sheet_files
        + ["reference.pdf", "README.txt"]
    )
    manifest = ExportManifest(
        schema_version="2.0.0",
        project_name=config.project.name,
        mode=config.project.mode,
        units=config.project.units,
        generated_at=iso_ts,
        files=all_files,
    )

    # ── README ────────────────────────────────────────────────────────────────
    readme = _README_TEMPLATE.format(
        project_name=config.project.name,
        mode=config.project.mode.value,
        units=units,
        generated_at=iso_ts,
        file_list="\n".join(f"  {f}" for f in all_files),
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
# DXF/SVG helpers for slat layout
# ---------------------------------------------------------------------------


def _create_slat_dxf(
    slat_polys: list[Polygon],
    slot_polys: list[Polygon],
    labels: list[dict],
    units: str,
) -> bytes:
    """Create a DXF with slats on CUT_OUTER, backing slots on CUT_SLOT."""
    import io as _io
    import ezdxf
    from ..export.dxf_export import _LAYERS, _INSUNITS, _add_geometry, _add_ring, _default_label_height

    doc = ezdxf.new("R2010")
    doc.header["$INSUNITS"] = _INSUNITS.get(units, 1)
    if "DASHED" not in doc.linetypes:
        doc.linetypes.new("DASHED", dxfattribs={"description": "Dashed"})
    msp = doc.modelspace()
    for name, attrs in _LAYERS.items():
        doc.layers.new(name=name, dxfattribs=attrs)

    for poly in slat_polys:
        _add_geometry(msp, poly, "CUT_OUTER")

    for poly in slot_polys:
        _add_geometry(msp, poly, "CUT_SLOT")
        # Also add slots as CUT_INNER on backing polygons
        if poly.interiors:
            for interior in poly.interiors:
                _add_ring(msp, list(interior.coords), "CUT_SLOT")

    ref_poly = slat_polys[0] if slat_polys else (slot_polys[0] if slot_polys else None)
    for lbl in labels:
        h = lbl.get("height", _default_label_height(ref_poly) if ref_poly else 0.1)
        text = msp.add_text(
            lbl["text"],
            dxfattribs={"layer": "ENGRAVE_LABEL", "height": h, "halign": 1},
        )
        text.dxf.insert = (lbl["x"], lbl["y"])
        text.dxf.align_point = (lbl["x"], lbl["y"])

    buf = _io.StringIO()
    doc.write(buf)
    return buf.getvalue().encode("utf-8")


def _create_slat_svg(
    slat_polys: list[Polygon],
    slot_polys: list[Polygon],
    labels: list[dict],
    units: str,
) -> str:
    """Create an SVG with slats and backing board in engineering orientation."""
    from ..export.svg_export import _geom_to_path_data, _escape_xml

    all_polys = slat_polys + slot_polys
    if not all_polys:
        return '<svg xmlns="http://www.w3.org/2000/svg"></svg>'

    all_xs = [c[0] for p in all_polys for c in p.exterior.coords]
    all_ys = [c[1] for p in all_polys for c in p.exterior.coords]
    minx, miny = min(all_xs), min(all_ys)
    maxx, maxy = max(all_xs), max(all_ys)
    w, h = maxx - minx, maxy - miny
    pad = max(w, h) * 0.02
    sw = max(w, h) * 0.003

    unit_label = "in" if units == "in" else "mm"
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="{minx-pad:.4f} {miny-pad:.4f} {w+pad*2:.4f} {h+pad*2:.4f}" '
        f'data-units="{unit_label}">',
        f'<g transform="translate(0,{(2*miny+h):.4f}) scale(1,-1)">',
        '<g id="CUT_OUTER">',
    ]
    for poly in slat_polys:
        pd = _geom_to_path_data(poly)
        if pd:
            lines.append(f'<path d="{pd}" fill="none" stroke="#ff0000" stroke-width="{sw:.5f}" fill-rule="evenodd"/>')
    lines.append("</g>")
    lines.append('<g id="CUT_SLOT">')
    for poly in slot_polys:
        pd = _geom_to_path_data(poly)
        if pd:
            lines.append(f'<path d="{pd}" fill="none" stroke="#00aa00" stroke-width="{sw:.5f}" fill-rule="evenodd"/>')
    lines.append("</g>")
    if labels:
        lh = max(w, h) * 0.02
        lines.append('<g id="ENGRAVE_LABEL">')
        for lbl in labels:
            lines.append(
                f'<text x="{lbl["x"]:.4f}" y="{lbl["y"]:.4f}" '
                f'font-size="{lh:.4f}" fill="#007700" font-family="monospace" text-anchor="middle">'
                f'{_escape_xml(lbl["text"])}</text>'
            )
        lines.append("</g>")
    lines.append("</g></svg>")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _single_part_fallback(parts: list[dict]) -> LayoutResult:
    """Place all parts at (0, 0) on a single sheet when layout is disabled."""
    sheet = SheetLayout(sheet_index=1, utilization=1.0)
    for i, part in enumerate(parts):
        bbox = part["bounding_box"]
        sheet.placements.append(PartPlacement(
            copy_index=0, x=-bbox[0], y=-bbox[1], rotated_90=False, part_index=i
        ))
    return LayoutResult(sheets=[sheet])


def _safe_filename(name: str) -> str:
    sanitised = re.sub(r"[^a-zA-Z0-9_-]", "-", name)
    sanitised = re.sub(r"-{2,}", "-", sanitised).strip("-")
    return sanitised[:48] or "project"
