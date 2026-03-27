"""
slat_rib pattern generator — Milestone C.

Spec intent:
- Generate repeated linear members (slats/ribs).
- Allow straight or lightly curved guide path.
- Clip to boundary.
- Preserve edge-safe margin.

Approach:
- Generate parallel guide lines across the safe boundary at `spacing` intervals.
- Each guide is a straight horizontal line (or optionally gently curved with
  amplitude > 0, same sine wave technique as wave_field but with lower default
  density for a subtler effect).
- Buffer each guide by `line_width / 2` to create a filled slat rectangle.
- Clip to the safe boundary.

Slats run horizontally (along X) by default. The grain_direction setting
influences whether slats are horizontal (x) or vertical (y).

Determinism rule: same config → same geometry. Phases use seeded RNG
(identical pattern to wave_field so the seed parameter behaves consistently).
"""

from __future__ import annotations

import math

import numpy as np
from shapely.geometry import LineString, MultiPolygon, Polygon
from shapely.ops import unary_union

from ...models import ConfigFabrication, ConfigPattern

_SAMPLE_DENSITY = 20  # sample points per spacing unit


def generate_slat_rib(
    safe_poly: Polygon,
    pattern: ConfigPattern,
    fabrication: ConfigFabrication,
) -> list[Polygon]:
    """
    Generate slat_rib cut bands clipped to safe_poly.

    Returns a list of Polygon objects representing cut slat regions.
    Each polygon is one slat member (guide buffered by line_width/2).
    """
    minx, miny, maxx, maxy = safe_poly.bounds
    w = maxx - minx
    h = maxy - miny

    spacing = pattern.spacing
    line_width = pattern.line_width
    amplitude = pattern.amplitude
    grain = fabrication.material.grain_direction.value  # "x" or "y"

    # Angular frequency — reuse density parameter same way wave_field does
    frequency = pattern.density * 2.0 * math.pi / max(spacing, 1e-9)

    # Seeded RNG for per-slat phase offsets (determinism)
    rng = np.random.default_rng(pattern.seed)

    if grain == "y":
        # Slats run vertically (along Y axis) — generate along X
        n_slats = max(int(math.ceil(w / spacing)) + 2, 1)
        phases = rng.uniform(0.0, 2.0 * math.pi, n_slats)

        n_pts = max(int(h * _SAMPLE_DENSITY / max(spacing, 1e-9)), 128)
        ys = np.linspace(miny - amplitude - line_width, maxy + amplitude + line_width, n_pts)

        result: list[Polygon] = []
        for i in range(n_slats):
            x_center = minx + i * spacing
            xs = x_center + amplitude * np.sin(frequency * (ys - miny) + phases[i])
            guide = LineString(list(zip(xs.tolist(), ys.tolist())))

            if line_width < 1e-9:
                continue

            slat = guide.buffer(line_width / 2.0, cap_style=2, join_style=2)
            if isinstance(slat, Polygon) and not slat.is_empty:
                clipped = slat.intersection(safe_poly)
                if not clipped.is_empty:
                    _collect_polygons(clipped, result)

    else:
        # Default: slats run horizontally (along X axis) — generate along Y
        n_slats = max(int(math.ceil(h / spacing)) + 2, 1)
        phases = rng.uniform(0.0, 2.0 * math.pi, n_slats)

        n_pts = max(int(w * _SAMPLE_DENSITY / max(spacing, 1e-9)), 128)
        xs = np.linspace(minx - amplitude - line_width, maxx + amplitude + line_width, n_pts)

        result = []
        for i in range(n_slats):
            y_center = miny + i * spacing
            ys = y_center + amplitude * np.sin(frequency * (xs - minx) + phases[i])
            guide = LineString(list(zip(xs.tolist(), ys.tolist())))

            if line_width < 1e-9:
                continue

            slat = guide.buffer(line_width / 2.0, cap_style=2, join_style=2)
            if isinstance(slat, Polygon) and not slat.is_empty:
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
