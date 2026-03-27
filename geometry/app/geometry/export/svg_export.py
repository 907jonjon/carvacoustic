"""
SVG export — two purposes:
  1. generate_preview_svg()  — inline SVG string for the browser preview panel
  2. generate_file_svg()     — standalone SVG file suitable for DXF comparison / Vectric import

Coordinate note: Shapely uses math coordinates (Y up). SVG uses screen coordinates
(Y down).  We apply a vertical flip transform so the preview matches the DXF.
"""

from __future__ import annotations

import math
from shapely.geometry import MultiPolygon, Polygon

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
    boundary_poly: Polygon,
    safe_poly: Polygon,
    bands: list[Polygon],
    labels: list[dict],
    units: str,
) -> str:
    """
    Return a standalone SVG file string with correct engineering orientation
    (Y-up, same as DXF). Includes unit metadata.
    """
    minx, miny, maxx, maxy = boundary_poly.bounds
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

    # Layers as <g> groups matching DXF layer names
    # REFERENCE_BOUNDARY
    bd = _geom_to_path_data(boundary_poly)
    if bd:
        lines.append(f'<g id="REFERENCE_BOUNDARY">')
        lines.append(
            f'<path d="{bd}" fill="none" stroke="#888888" '
            f'stroke-width="{sw_boundary:.5f}"/>'
        )
        lines.append("</g>")

    # SAFE_MARGIN_GUIDE
    sm = _geom_to_path_data(safe_poly)
    if sm:
        lines.append(f'<g id="SAFE_MARGIN_GUIDE">')
        lines.append(
            f'<path d="{sm}" fill="none" stroke="#aaaaff" '
            f'stroke-width="{sw_safe:.5f}" '
            f'stroke-dasharray="{dash:.4f} {dash*0.5:.4f}"/>'
        )
        lines.append("</g>")

    # CUT_OUTER
    lines.append(f'<g id="CUT_OUTER">')
    lines.append(
        f'<path d="{bd}" fill="none" stroke="#ff0000" '
        f'stroke-width="{sw_boundary:.5f}"/>'
    )
    lines.append("</g>")

    # CUT_INNER
    lines.append(f'<g id="CUT_INNER">')
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


def _escape_xml(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
