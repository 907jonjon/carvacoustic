"""
SVG export — three purposes:
  1. generate_preview_svg()       — inline SVG for the browser (legacy v1)
  2. generate_slat_preview_svg()  — inline SVG showing slat profiles (v2)
  3. generate_file_svg()          — standalone SVG for DXF comparison / Vectric import

Coordinate note: Shapely uses math coordinates (Y up). SVG uses screen coordinates
(Y down).  We apply a vertical flip transform so the preview matches the DXF.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from shapely.geometry import MultiPolygon, Polygon

if TYPE_CHECKING:
    from ...models import CanonicalConfig

# SVG colours per layer role
_COLOUR_BOUNDARY = "#d0d0d0"
_COLOUR_SAFE_MARGIN = "#b0b0ff"
_COLOUR_CUT = "#222222"
_COLOUR_LABEL = "#007700"


def _polygon_to_path_data(poly: Polygon) -> str:
    """Convert a Shapely Polygon to an SVG path 'd' attribute string."""
    parts: list[str] = []

    def ring_to_path(coords: list[tuple[float, float]]) -> str:
        pts = list(coords)
        if pts and pts[0] == pts[-1]:
            pts = pts[:-1]
        if len(pts) < 2:
            return ""
        tokens = [f"M {pts[0][0]:.5f},{pts[0][1]:.5f}"]
        for x, y in pts[1:]:
            tokens.append(f"L {x:.5f},{y:.5f}")
        tokens.append("Z")
        return " ".join(tokens)

    ext = ring_to_path(list(poly.exterior.coords))
    if ext:
        parts.append(ext)
    for interior in poly.interiors:
        inn = ring_to_path(list(interior.coords))
        if inn:
            parts.append(inn)

    return " ".join(parts)


def _geom_to_path_data(geom: object) -> str:
    """Convert Polygon or MultiPolygon to path data."""
    if isinstance(geom, Polygon):
        return _polygon_to_path_data(geom)
    if isinstance(geom, MultiPolygon):
        return " ".join(_polygon_to_path_data(g) for g in geom.geoms)
    if hasattr(geom, "geoms"):
        return " ".join(_geom_to_path_data(g) for g in geom.geoms)
    return ""


def generate_preview_svg(
    boundary_poly: Polygon,
    safe_poly: Polygon,
    bands: list[Polygon],
    labels: list[dict],
) -> str:
    """
    Return an inline SVG string for the browser preview panel.
    Uses fill-rule='evenodd' for correct hole rendering.
    Applies Y-flip so the image orientation matches the DXF.
    """
    minx, miny, maxx, maxy = boundary_poly.bounds
    w = maxx - minx
    h = maxy - miny

    # Padding around the geometry
    pad = max(w, h) * 0.03
    vb_x = minx - pad
    vb_y = miny - pad
    vb_w = w + pad * 2
    vb_h = h + pad * 2

    lines: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="{vb_x:.4f} {vb_y:.4f} {vb_w:.4f} {vb_h:.4f}" '
        f'width="100%" height="100%">',
        # Y-flip group: translate down by (2*miny + h), scale Y by -1
        f'<g transform="translate(0,{(2*miny + h):.4f}) scale(1,-1)">',
    ]

    # Background
    lines.append(
        f'<rect x="{vb_x:.4f}" y="{vb_y:.4f}" width="{vb_w:.4f}" height="{vb_h:.4f}" '
        f'fill="#f8f8f8"/>'
    )

    # Boundary fill
    bd = _geom_to_path_data(boundary_poly)
    if bd:
        lines.append(
            f'<path d="{bd}" fill="{_COLOUR_BOUNDARY}" stroke="#888888" '
            f'stroke-width="{max(w, h) * 0.003:.4f}" fill-rule="evenodd"/>'
        )

    # Safe margin guide (dashed stroke, no fill)
    sm = _geom_to_path_data(safe_poly)
    if sm:
        dash = max(w, h) * 0.015
        lines.append(
            f'<path d="{sm}" fill="none" stroke="{_COLOUR_SAFE_MARGIN}" '
            f'stroke-width="{max(w, h) * 0.002:.4f}" '
            f'stroke-dasharray="{dash:.4f} {dash * 0.5:.4f}"/>'
        )

    # Cut bands
    for band in bands:
        pd = _geom_to_path_data(band)
        if pd:
            lines.append(
                f'<path d="{pd}" fill="{_COLOUR_CUT}" fill-rule="evenodd" '
                f'stroke="none"/>'
            )

    # Labels (text is un-flipped via nested transform)
    lh = max(w, h) * 0.025
    for lbl in labels:
        lx, ly = lbl["x"], lbl["y"]
        text = lbl["text"]
        # Counter-flip text so it reads correctly
        lines.append(
            f'<text x="{lx:.4f}" y="{ly:.4f}" '
            f'transform="scale(1,-1) translate(0,{-2*ly:.4f})" '
            f'font-size="{lh:.4f}" fill="{_COLOUR_LABEL}" '
            f'font-family="monospace" text-anchor="middle">'
            f'{_escape_xml(text)}</text>'
        )

    lines.append("</g>")
    lines.append("</svg>")
    return "\n".join(lines)


def generate_file_svg(
    boundary_poly: Polygon | list[Polygon],
    safe_poly: Polygon | list[Polygon],
    bands: list[Polygon],
    labels: list[dict],
    units: str,
) -> str:
    """
    Return a standalone SVG file string with correct engineering orientation
    (Y-up, same as DXF). Includes unit metadata.
    Accepts single Polygon or list of Polygons for boundary/safe_poly
    to support multi-copy sheet layouts.
    """
    boundary_list = boundary_poly if isinstance(boundary_poly, list) else [boundary_poly]
    safe_list = safe_poly if isinstance(safe_poly, list) else [safe_poly]

    # Compute overall bounds across all boundaries
    all_xs = [x for bp in boundary_list for x, _ in bp.exterior.coords]
    all_ys = [y for bp in boundary_list for _, y in bp.exterior.coords]
    minx, miny = min(all_xs), min(all_ys)
    maxx, maxy = max(all_xs), max(all_ys)
    w = maxx - minx
    h = maxy - miny
    pad = max(w, h) * 0.02

    unit_label = "in" if units == "in" else "mm"
    sw_boundary = max(w, h) * 0.004
    sw_safe = max(w, h) * 0.002
    dash = max(w, h) * 0.02

    lines: list[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="{minx - pad:.4f} {miny - pad:.4f} {w + pad*2:.4f} {h + pad*2:.4f}" '
        f'data-units="{unit_label}">',
        f'<!-- CarvAcoustic export — units: {unit_label} -->',
        # Y-flip to match DXF (Y-up)
        f'<g transform="translate(0,{(2*miny + h):.4f}) scale(1,-1)">',
    ]

    # REFERENCE_BOUNDARY
    lines.append('<g id="REFERENCE_BOUNDARY">')
    for bp in boundary_list:
        bd = _geom_to_path_data(bp)
        if bd:
            lines.append(
                f'<path d="{bd}" fill="none" stroke="#888888" '
                f'stroke-width="{sw_boundary:.5f}"/>'
            )
    lines.append("</g>")

    # SAFE_MARGIN_GUIDE
    lines.append('<g id="SAFE_MARGIN_GUIDE">')
    for sp in safe_list:
        sm = _geom_to_path_data(sp)
        if sm:
            lines.append(
                f'<path d="{sm}" fill="none" stroke="#aaaaff" '
                f'stroke-width="{sw_safe:.5f}" '
                f'stroke-dasharray="{dash:.4f} {dash*0.5:.4f}"/>'
            )
    lines.append("</g>")

    # CUT_OUTER
    lines.append('<g id="CUT_OUTER">')
    for bp in boundary_list:
        bd = _geom_to_path_data(bp)
        if bd:
            lines.append(
                f'<path d="{bd}" fill="none" stroke="#ff0000" '
                f'stroke-width="{sw_boundary:.5f}"/>'
            )
    lines.append("</g>")

    # CUT_INNER
    lines.append('<g id="CUT_INNER">')
    for band in bands:
        pd = _geom_to_path_data(band)
        if pd:
            lines.append(
                f'<path d="{pd}" fill="none" stroke="#0000ff" '
                f'stroke-width="{sw_safe:.5f}" fill-rule="evenodd"/>'
            )
    lines.append("</g>")

    # ENGRAVE_LABEL
    if labels:
        lh = max(w, h) * 0.025
        lines.append('<g id="ENGRAVE_LABEL">')
        for lbl in labels:
            lines.append(
                f'<text x="{lbl["x"]:.4f}" y="{lbl["y"]:.4f}" '
                f'font-size="{lh:.4f}" fill="#00aa00" '
                f'font-family="monospace" text-anchor="middle">'
                f'{_escape_xml(lbl["text"])}</text>'
            )
        lines.append("</g>")

    lines.append("</g>")
    lines.append("</svg>")
    return "\n".join(lines)


def generate_slat_preview_svg(
    slat_parts: list[dict],
    backing_part: dict | None,
    config: "CanonicalConfig",
) -> str:
    """
    Inline SVG showing all slat profiles arranged side by side for the browser
    preview panel (v2 pipeline).

    Layout: slats are shown in a row (stacked top-to-bottom in SVG space) with a
    small gap between them, so the viewer can see each unique profile.
    The backing board is shown below all slats if present.
    """
    if not slat_parts:
        return "<svg xmlns='http://www.w3.org/2000/svg' width='100%' height='100%'></svg>"

    # Collect all polygons to compute overall bounds
    all_polys = [p["polygon"] for p in slat_parts]
    if backing_part:
        all_polys.append(backing_part["polygon"])

    # Arrange slats vertically for the preview with a gap between each
    # Get single slat bounds
    sample = slat_parts[0]["polygon"]
    sb_minx, sb_miny, sb_maxx, sb_maxy = sample.bounds
    slat_w = sb_maxx - sb_minx
    slat_h = sb_maxy - sb_miny
    gap = slat_h * 0.2

    # We show at most 20 slats in the preview to keep SVG fast
    preview_slats = slat_parts[:20]
    n_preview = len(preview_slats)

    total_h = n_preview * (slat_h + gap) - gap
    total_w = slat_w

    if backing_part:
        bb = backing_part["polygon"].bounds
        back_h = bb[3] - bb[1]
        total_h += gap * 2 + back_h

    pad = max(total_w, total_h) * 0.03
    vb_x = -pad
    vb_y = -(total_h + pad)
    vb_w = total_w + pad * 2
    vb_h = total_h + pad * 2

    lines: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="{vb_x:.4f} {vb_y:.4f} {vb_w:.4f} {vb_h:.4f}" '
        f'width="100%" height="100%">',
        f'<rect x="{vb_x:.4f}" y="{vb_y:.4f}" width="{vb_w:.4f}" height="{vb_h:.4f}" fill="#f8f8f8"/>',
        # Y-flip group
        f'<g transform="translate(0,0) scale(1,-1)">',
    ]

    # Draw slats stacked downward (in math coords, each slat is shifted down)
    for idx, part in enumerate(preview_slats):
        y_offset = -(idx * (slat_h + gap))
        poly = part["polygon"]

        # Translate polygon to stacked position
        from shapely import affinity
        shifted = affinity.translate(poly, xoff=0, yoff=y_offset)
        pd = _geom_to_path_data(shifted)
        if pd:
            lines.append(
                f'<path d="{pd}" fill="#8B6914" fill-opacity="0.85" '
                f'stroke="#5a3e0a" stroke-width="{slat_w * 0.004:.4f}" fill-rule="evenodd"/>'
            )

        # Label
        if config.labeling.enabled:
            lx = slat_w / 2.0
            ly = y_offset + slat_h * 0.3
            lh = slat_h * 0.12
            lines.append(
                f'<text x="{lx:.4f}" y="{ly:.4f}" '
                f'transform="scale(1,-1) translate(0,{-2*ly:.4f})" '
                f'font-size="{lh:.4f}" fill="#fff" '
                f'font-family="monospace" text-anchor="middle">'
                f'{_escape_xml(part["part_id"])}</text>'
            )

    # Draw backing board
    if backing_part:
        base_y = -(n_preview * (slat_h + gap) + gap)
        bb_poly = backing_part["polygon"]
        bb_minx2, bb_miny2, bb_maxx2, bb_maxy2 = bb_poly.bounds
        from shapely import affinity
        shifted_back = affinity.translate(bb_poly, xoff=0, yoff=base_y - bb_miny2)
        pd = _geom_to_path_data(shifted_back)
        if pd:
            lines.append(
                f'<path d="{pd}" fill="#A0522D" fill-opacity="0.8" '
                f'stroke="#5a2e0a" stroke-width="{slat_w * 0.003:.4f}" fill-rule="evenodd"/>'
            )

    if n_preview < len(slat_parts):
        lines.append(
            f'<text x="{slat_w/2:.4f}" y="-{total_h + pad*0.5:.4f}" '
            f'transform="scale(1,-1) translate(0,{2*(total_h + pad*0.5):.4f})" '
            f'font-size="{slat_h * 0.15:.4f}" fill="#888" font-family="sans-serif" text-anchor="middle">'
            f'…and {len(slat_parts) - n_preview} more slats</text>'
        )

    lines.append("</g>")
    lines.append("</svg>")
    return "\n".join(lines)


def generate_cut_preview_svg(
    slat_parts: list[dict],
    backing_part: dict | None,
    layout_result: object | None,
    config: "CanonicalConfig",
) -> str:
    """
    Inline SVG showing actual cut paths arranged on material sheets.

    Each sheet is rendered as a gray-bordered rectangle. Slat cut paths use
    red (#cc3333) stroke; backing/slot paths use green (#339933) stroke.
    Sheets are stacked vertically with a gap between them.
    """
    from ..layout import LayoutResult  # local import to avoid circular

    if layout_result is None or not isinstance(layout_result, LayoutResult):
        return ""
    if not layout_result.sheets:
        return ""

    mat = config.fabrication.material
    sheet_w = mat.sheet_width
    sheet_h = mat.sheet_height
    sheet_gap = sheet_h * 0.15

    all_parts = list(slat_parts)
    if backing_part:
        all_parts.append(backing_part)

    n_sheets = len(layout_result.sheets)
    total_h = n_sheets * sheet_h + (n_sheets - 1) * sheet_gap
    pad = max(sheet_w, total_h) * 0.03

    vb_x = -pad
    vb_y = -pad
    vb_w = sheet_w + pad * 2
    vb_h = total_h + pad * 2

    sw = max(sheet_w, sheet_h) * 0.002  # stroke width

    lines: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="{vb_x:.4f} {vb_y:.4f} {vb_w:.4f} {vb_h:.4f}" '
        f'width="100%" height="100%">',
        f'<rect x="{vb_x:.4f}" y="{vb_y:.4f}" width="{vb_w:.4f}" height="{vb_h:.4f}" fill="#f8f8f8"/>',
    ]

    for si, sheet in enumerate(layout_result.sheets):
        y_offset = si * (sheet_h + sheet_gap)

        # Sheet border
        lines.append(
            f'<rect x="0" y="{y_offset:.4f}" width="{sheet_w:.4f}" height="{sheet_h:.4f}" '
            f'fill="#fafafa" stroke="#999999" stroke-width="{sw:.4f}"/>'
        )

        # Sheet label
        label_size = sheet_h * 0.04
        lines.append(
            f'<text x="{sheet_w * 0.01:.4f}" y="{y_offset + label_size * 1.5:.4f}" '
            f'font-size="{label_size:.4f}" fill="#666666" font-family="sans-serif">'
            f'Sheet {sheet.sheet_index}</text>'
        )

        # Draw placed parts
        for pl in sheet.placements:
            if pl.part_index < 0 or pl.part_index >= len(all_parts):
                continue

            part = all_parts[pl.part_index]
            poly = part["polygon"]
            bbox = part["bounding_box"]

            # Translate part from its local coordinate space to the sheet
            # placement position.  placement (x, y) is the target for the
            # part's bounding-box origin (bbox[0], bbox[1]).
            from shapely import affinity

            dx = pl.x - bbox[0]
            dy = pl.y - bbox[1]
            moved = affinity.translate(poly, xoff=dx, yoff=dy)

            if pl.rotated_90:
                # Rotate 90° CCW around the placed part's centre
                part_w = bbox[2] - bbox[0]
                part_h = bbox[3] - bbox[1]
                cx = pl.x + part_w / 2.0
                cy = pl.y + part_h / 2.0
                moved = affinity.rotate(moved, 90, origin=(cx, cy))

            # Determine colour: backing is green, slats are red
            is_backing = part.get("part_id", "").startswith("BACK")
            stroke_colour = "#339933" if is_backing else "#cc3333"

            pd = _geom_to_path_data(moved)
            if pd:
                # Single Y-flip group per part, scoped to this sheet's
                # vertical offset.  No nested translate — the Shapely
                # transform already placed the part correctly.
                lines.append(
                    f'<g transform="translate(0,{y_offset + sheet_h:.4f}) scale(1,-1)">'
                    f'<path d="{pd}" fill="{stroke_colour}" fill-opacity="0.15" '
                    f'stroke="{stroke_colour}" stroke-width="{sw * 0.8:.4f}" fill-rule="evenodd"/>'
                    f'</g>'
                )

    lines.append("</svg>")
    return "\n".join(lines)


def _escape_xml(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
