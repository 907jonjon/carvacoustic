"""
Reference PDF export — Milestone C.

Produces a two-page PDF:
  Page 1 — Project metadata, pattern settings, fabrication settings, part count,
            and a visual reference drawing of the design (boundary + cut geometry).
  Page 2 — Layer legend, Vectric import instructions, and file manifest notes.

Uses reportlab for PDF generation.
"""

from __future__ import annotations

import io
from datetime import datetime, timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.graphics.shapes import Drawing, Path, String, Line, Rect
from reportlab.graphics import renderPDF
from shapely.geometry import Polygon, MultiPolygon

from ...models import CanonicalConfig


# ---------------------------------------------------------------------------
# Colours matching the DXF/SVG layers
# ---------------------------------------------------------------------------
_COL_BOUNDARY = colors.HexColor("#d0d0d0")
_COL_SAFE_MARGIN = colors.HexColor("#b0b0ff")
_COL_CUT = colors.HexColor("#222222")
_COL_LABEL = colors.HexColor("#007700")
_COL_HEADER = colors.HexColor("#1e3a5f")


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def create_reference_pdf(
    config: CanonicalConfig,
    boundary_poly: Polygon,
    safe_poly: Polygon,
    bands: list[Polygon],
    labels: list[dict],
    generated_at: str,
) -> bytes:
    """
    Build a reference PDF and return the raw bytes.
    """
    buf = io.BytesIO()
    styles = getSampleStyleSheet()

    heading_style = ParagraphStyle(
        "Heading1CA",
        parent=styles["Heading1"],
        textColor=_COL_HEADER,
        fontSize=16,
        spaceAfter=6,
    )
    subheading_style = ParagraphStyle(
        "Heading2CA",
        parent=styles["Heading2"],
        textColor=_COL_HEADER,
        fontSize=12,
        spaceBefore=12,
        spaceAfter=4,
    )
    body_style = styles["Normal"]
    body_style.fontSize = 9

    page_w, page_h = letter
    margin = 0.75 * inch
    content_w = page_w - 2 * margin

    doc = BaseDocTemplate(
        buf,
        pagesize=letter,
        leftMargin=margin,
        rightMargin=margin,
        topMargin=margin,
        bottomMargin=margin,
    )

    frame = Frame(margin, margin, content_w, page_h - 2 * margin, id="normal")
    template = PageTemplate(id="main", frames=[frame])
    doc.addPageTemplates([template])

    story = []

    # ── Page 1 ────────────────────────────────────────────────────────────────

    story.append(Paragraph("CarvAcoustic — Reference Sheet", heading_style))
    story.append(Paragraph(
        f"<b>{config.project.name}</b> &nbsp;·&nbsp; "
        f"{config.project.mode.value.replace('_', ' ').title()} &nbsp;·&nbsp; "
        f"Generated {generated_at}",
        body_style,
    ))
    story.append(Spacer(1, 0.15 * inch))

    # Project + boundary table
    story.append(Paragraph("Project &amp; Boundary", subheading_style))
    minx, miny, maxx, maxy = boundary_poly.bounds
    bw = maxx - minx
    bh = maxy - miny
    units = config.project.units.value
    proj_data = [
        ["Mode", config.project.mode.value.replace("_", " ").title()],
        ["Units", units],
        ["Boundary type", config.boundary.type.value.replace("_", " ").title()],
        ["Width", f"{bw:.3f} {units}"],
        ["Height", f"{bh:.3f} {units}"],
        ["Safe margin", f"{config.boundary.safe_margin:.3f} {units}"],
        ["Part count", str(len(bands))],
    ]
    story.append(_two_col_table(proj_data, content_w))
    story.append(Spacer(1, 0.1 * inch))

    # Pattern table
    story.append(Paragraph("Pattern", subheading_style))
    pat = config.pattern
    pattern_data = [
        ["Family", pat.family.value.replace("_", " ").title()],
        ["Density", f"{pat.density:.2f}"],
        ["Spacing", f"{pat.spacing:.3f} {units}"],
        ["Line width", f"{pat.line_width:.3f} {units}"],
        ["Amplitude", f"{pat.amplitude:.3f} {units}"],
        ["Symmetry", pat.symmetry.value],
        ["Seed", str(pat.seed)],
    ]
    story.append(_two_col_table(pattern_data, content_w))
    story.append(Spacer(1, 0.1 * inch))

    # Fabrication table
    story.append(Paragraph("Fabrication", subheading_style))
    mat = config.fabrication.material
    tool = config.fabrication.tool
    fab_data = [
        ["Material thickness", f"{mat.thickness:.3f} {units}"],
        ["Sheet size", f"{mat.sheet_width:.0f} × {mat.sheet_height:.0f} {units}"],
        ["Grain direction", mat.grain_direction.value],
        ["Min bridge", f"{mat.min_bridge:.3f} {units}"],
        ["Tool diameter", f"{tool.tool_diameter:.4f} {units}"],
        ["Kerf allowance", f"{tool.kerf_allowance:.4f} {units}"],
        ["Min inside radius", f"{tool.min_inside_radius:.4f} {units}"],
        ["Dogbone style", tool.dogbone_style.value],
        ["Clearance", f"{tool.clearance:.3f} {units}"],
        ["Border gap", f"{tool.border_gap:.3f} {units}"],
    ]
    story.append(_two_col_table(fab_data, content_w))
    story.append(Spacer(1, 0.15 * inch))

    # Design preview drawing
    story.append(Paragraph("Design Preview (not to scale)", subheading_style))
    preview_drawing = _make_preview_drawing(
        boundary_poly, safe_poly, bands, labels, content_w, 3.5 * inch
    )
    story.append(preview_drawing)
    story.append(Spacer(1, 0.1 * inch))

    # ── Page 2 ────────────────────────────────────────────────────────────────

    from reportlab.platypus import PageBreak
    story.append(PageBreak())

    story.append(Paragraph("Layer Reference", heading_style))
    story.append(Spacer(1, 0.1 * inch))

    layer_data = [
        ["Layer name", "Colour", "Purpose"],
        ["CUT_OUTER", "Red", "Outer profile cuts — primary machining"],
        ["CUT_INNER", "Blue", "Inner pocket / relief cuts"],
        ["ENGRAVE_LABEL", "Green", "Part labels — engrave or mark"],
        ["REFERENCE_BOUNDARY", "White / Black", "Original panel boundary — reference only, do not cut"],
        ["SAFE_MARGIN_GUIDE", "Grey (dashed)", "Safe margin inset — reference only"],
    ]
    layer_tbl = Table(
        layer_data,
        colWidths=[1.8 * inch, 1.0 * inch, content_w - 2.8 * inch],
    )
    layer_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), _COL_HEADER),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(layer_tbl)
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("Vectric Import Instructions", subheading_style))
    vectric_steps = [
        "Open Vectric Aspire / VCarve Pro.",
        "File → Import Vectors → select <b>sheet-01.dxf</b> (or the appropriate sheet file).",
        "Verify the job size matches the sheet dimensions listed above.",
        "Confirm layers imported correctly: CUT_OUTER, CUT_INNER, ENGRAVE_LABEL.",
        "Set up toolpaths (profile, pocket, engraving) as needed for your job.",
        "Add tabs / hold-downs as required for your material and machine.",
        "Run simulation and verify, then post-process for your controller.",
        "<b>CarvAcoustic does NOT generate G-code.</b> All toolpath setup is done in Vectric.",
    ]
    for i, step in enumerate(vectric_steps, 1):
        story.append(Paragraph(f"{i}. {step}", body_style))
        story.append(Spacer(1, 0.04 * inch))

    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph("Export Bundle Contents", subheading_style))
    bundle_items = [
        ["manifest.json", "Machine-readable manifest with file list and metadata"],
        ["project-config.json", "Full canonical config used to generate this export"],
        ["sheet-XX.dxf", "Per-sheet DXF file for Vectric (R2010 format)"],
        ["sheet-XX.svg", "Per-sheet SVG for reference / web preview"],
        ["reference.pdf", "This document"],
    ]
    bundle_tbl = Table(
        bundle_items,
        colWidths=[1.8 * inch, content_w - 1.8 * inch],
    )
    bundle_tbl.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(bundle_tbl)

    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph(
        f"<i>Generated by CarvAcoustic · {generated_at} · Schema v{config.schema_version}</i>",
        body_style,
    ))

    doc.build(story)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _two_col_table(rows: list[list[str]], content_w: float) -> Table:
    tbl = Table(rows, colWidths=[2.0 * inch, content_w - 2.0 * inch])
    tbl.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return tbl


def _make_preview_drawing(
    boundary_poly: Polygon,
    safe_poly: Polygon,
    bands: list[Polygon],
    labels: list[dict],
    draw_w: float,
    draw_h: float,
) -> Drawing:
    """
    Render the design preview as a reportlab Drawing (not to scale).
    Y-axis is flipped (SVG convention) so the design appears upright.
    """
    minx, miny, maxx, maxy = boundary_poly.bounds
    design_w = maxx - minx
    design_h = maxy - miny

    if design_w < 1e-9 or design_h < 1e-9:
        return Drawing(draw_w, draw_h)

    # Scale to fit within draw area (leave small padding)
    pad = 12  # points
    scale = min(
        (draw_w - 2 * pad) / design_w,
        (draw_h - 2 * pad) / design_h,
    )
    offset_x = pad + ((draw_w - 2 * pad) - design_w * scale) / 2
    offset_y = pad + ((draw_h - 2 * pad) - design_h * scale) / 2

    def tx(x: float) -> float:
        return offset_x + (x - minx) * scale

    def ty(y: float) -> float:
        # Flip Y so design appears upright in PDF (PDF origin is bottom-left)
        return offset_y + (y - miny) * scale

    drawing = Drawing(draw_w, draw_h)

    # Background
    drawing.add(Rect(0, 0, draw_w, draw_h, fillColor=colors.HexColor("#f8f8f8"), strokeColor=None))

    # Boundary fill
    _add_polygon_to_drawing(drawing, boundary_poly, tx, ty, _COL_BOUNDARY, _COL_BOUNDARY, 0.5)

    # Safe margin outline
    _add_polygon_to_drawing(drawing, safe_poly, tx, ty, None, _COL_SAFE_MARGIN, 0.5)

    # Cut bands
    for band in bands:
        _add_polygon_to_drawing(drawing, band, tx, ty, _COL_CUT, None, 0)

    # Boundary outline on top
    _add_polygon_to_drawing(drawing, boundary_poly, tx, ty, None, colors.HexColor("#555555"), 0.75)

    # Labels
    for lbl in labels:
        lx = tx(lbl["x"])
        ly = ty(lbl["y"])
        font_size = max(lbl.get("height", 6) * scale, 6)
        drawing.add(String(lx, ly, lbl["text"], fontSize=font_size, fillColor=_COL_LABEL))

    return drawing


def _add_polygon_to_drawing(
    drawing: Drawing,
    geom: object,
    tx: object,
    ty: object,
    fill_color: object,
    stroke_color: object,
    stroke_width: float,
) -> None:
    """Add a Shapely Polygon (or collection) as a reportlab Path to the drawing."""
    if isinstance(geom, Polygon):
        if geom.is_empty:
            return
        path = _polygon_to_rl_path(geom, tx, ty, fill_color, stroke_color, stroke_width)  # type: ignore[arg-type]
        if path is not None:
            drawing.add(path)
    elif isinstance(geom, MultiPolygon):
        for g in geom.geoms:
            _add_polygon_to_drawing(drawing, g, tx, ty, fill_color, stroke_color, stroke_width)
    elif hasattr(geom, "geoms"):
        for g in geom.geoms:  # type: ignore[union-attr]
            _add_polygon_to_drawing(drawing, g, tx, ty, fill_color, stroke_color, stroke_width)


def _polygon_to_rl_path(
    poly: Polygon,
    tx: object,
    ty: object,
    fill_color: object,
    stroke_color: object,
    stroke_width: float,
) -> Path | None:
    """Convert a Shapely Polygon to a reportlab Path shape."""
    from typing import Callable
    _tx: Callable[[float], float] = tx  # type: ignore[assignment]
    _ty: Callable[[float], float] = ty  # type: ignore[assignment]

    coords = list(poly.exterior.coords)
    if len(coords) < 3:
        return None

    path = Path(fillColor=fill_color, strokeColor=stroke_color, strokeWidth=stroke_width)

    pts = coords[:-1]  # exclude closing duplicate
    path.moveTo(_tx(pts[0][0]), _ty(pts[0][1]))
    for x, y in pts[1:]:
        path.lineTo(_tx(x), _ty(y))
    path.closePath()

    for interior in poly.interiors:
        icoords = list(interior.coords)[:-1]
        if len(icoords) < 2:
            continue
        path.moveTo(_tx(icoords[0][0]), _ty(icoords[0][1]))
        for x, y in icoords[1:]:
            path.lineTo(_tx(x), _ty(y))
        path.closePath()

    return path
