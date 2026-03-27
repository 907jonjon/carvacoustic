"""
slat_rib pattern generator.

Spec intent:
- Generate repeated linear members (slats/ribs).
- Straight guide lines — like cabinet door louvers or wood slats.
- Clip to boundary.
- Preserve edge-safe margin.

Approach:
- Generate parallel straight guide lines at `spacing` intervals.
- Buffer each guide by `line_width / 2` to produce a filled slat rectangle.
- Clip to the safe boundary.
- No wave displacement — slats are strictly straight.

grain_direction controls orientation:
  "x" → slats run horizontally (span X axis)
  "y" → slats run vertically (span Y axis)

Determinism: no RNG needed; geometry is fully determined by the config.
The seed parameter is accepted for API consistency but unused.
"""

from __future__ import annotations

import math

from shapely.geometry import LineString, MultiPolygon, Polygon

from ...models import ConfigFabrication, ConfigPattern


def generate_slat_rib(
    safe_poly: Polygon,
    pattern: ConfigPattern,
    fabrication: ConfigFabrication,
) -> list[Polygon]:
    """
    Generate slat_rib cut bands clipped to safe_poly.

    Returns a list of Polygon objects representing cut slat regions.
    Each polygon is one straight slat member buffered by line_width/2.
    """
    minx, miny, maxx, maxy = safe_poly.bounds
    w = maxx - minx
    h = maxy - miny

    spacing = max(pattern.spacing, 1e-6)
    line_width = pattern.line_width
    grain = fabrication.material.grain_direction.value  # "x" or "y"

    if line_width < 1e-9:
        return []

    result: list[Polygon] = []

    if grain == "y":
        # Slats run vertically — evenly spaced along X
        n_slats = max(int(math.ceil(w / spacing)) + 1, 1)
        for i in range(n_slats):
            x_center = minx + i * spacing
            # Straight vertical line spanning the full height (plus overhang)
            guide = LineString([(x_center, miny - line_width), (x_center, maxy + line_width)])
            slat = guide.buffer(line_width / 2.0, cap_style=2, join_style=2)
            if not slat.is_empty:
                clipped = slat.intersection(safe_poly)
                if not clipped.is_empty:
                    _collect_polygons(clipped, result)
    else:
        # Default: slats run horizontally — evenly spaced along Y
        n_slats = max(int(math.ceil(h / spacing)) + 1, 1)
        for i in range(n_slats):
            y_center = miny + i * spacing
            # Straight horizontal line spanning the full width (plus overhang)
            guide = LineString([(minx - line_width, y_center), (maxx + line_width, y_center)])
            slat = guide.buffer(line_width / 2.0, cap_style=2, join_style=2)
            if not slat.is_empty:
                clipped = slat.intersection(safe_poly)
                if not clipped.is_empty:
                    _collect_polygons(clipped, result)

    return result


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
