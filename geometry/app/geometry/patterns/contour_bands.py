"""
contour_bands pattern generator — Milestone C.

Spec intent:
- Generate inward offset bands from boundary or center guide.
- Enforce spacing threshold.
- Clip and clean each band.

Approach:
- Start from the safe boundary's exterior ring.
- Successively erode inward by `spacing` steps.
- Each offset ring is buffered by `line_width / 2` on each side to produce a
  filled band polygon.
- Stop when the eroded shape becomes empty or below min feature size.

Determinism rule: same config → same geometry. No RNG is needed because
contour bands are fully deterministic from the boundary shape and spacing.
"""

from __future__ import annotations

from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import unary_union

from ...models import ConfigFabrication, ConfigPattern


def generate_contour_bands(
    safe_poly: Polygon,
    pattern: ConfigPattern,
    fabrication: ConfigFabrication,
) -> list[Polygon]:
    """
    Generate contour_bands cut bands clipped to safe_poly.

    Returns a list of Polygon objects representing cut regions.
    Each polygon is one concentric band at a given inset depth.
    """
    spacing = pattern.spacing
    line_width = pattern.line_width
    tool_diameter = fabrication.tool.tool_diameter

    # Minimum viable area — stop generating bands below this
    min_area = tool_diameter * tool_diameter

    bands: list[Polygon] = []

    # Walk inward: offset = half line_width (so the band centre is at multiples of spacing)
    offset = line_width / 2.0
    step = 0

    while True:
        step += 1
        # Centre line of this band
        center_inset = offset + (step - 1) * spacing
        inner_edge = center_inset + line_width / 2.0

        # The outer edge of this band
        outer_ring = safe_poly.buffer(-(center_inset - line_width / 2.0))
        if outer_ring.is_empty or outer_ring.area < min_area:
            break

        # The inner edge of this band
        inner_ring = safe_poly.buffer(-inner_edge)

        if inner_ring.is_empty:
            # Last band — just use the outer ring eroded slightly
            band = outer_ring
        else:
            # Band = outer_ring minus inner_ring
            band = outer_ring.difference(inner_ring)

        if band.is_empty or band.area < min_area:
            break

        # Clip to safe boundary (shouldn't be needed, but defensive)
        clipped = band.intersection(safe_poly)
        if clipped.is_empty:
            break

        _collect_polygons(clipped, bands)

        # If we've consumed the full interior, stop
        if inner_ring.is_empty:
            break

    return bands


def _collect_polygons(geom: object, out: list[Polygon]) -> None:
    """Recursively collect Polygon instances from any Shapely geometry."""
    if isinstance(geom, Polygon):
        if not geom.is_empty and geom.area > 1e-12:
            out.append(geom)
    elif isinstance(geom, MultiPolygon):
        for g in geom.geoms:
            _collect_polygons(g, out)
    elif hasattr(geom, "geoms"):
        for g in geom.geoms:  # type: ignore[union-attr]
            _collect_polygons(g, out)
