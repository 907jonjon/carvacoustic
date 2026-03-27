"""
wave_field pattern generator — Milestone B.

Spec intent:
- Build repeated guide lines across the usable boundary.
- Displace guides by a smooth wave function.
- Clip to boundary.
- Convert to line/band geometry based on fabrication settings (line_width).

Determinism rule: same config → same geometry. Achieved by seeding numpy's
Generator with pattern.seed and deriving per-line phases from it.
"""

from __future__ import annotations

import math

import numpy as np
from shapely import affinity
from shapely.geometry import LineString, MultiPolygon, Polygon, box
from shapely.ops import unary_union

from ...models import ConfigFabrication, ConfigPattern

# Sample points per spacing unit along each guide line.
# Higher values → smoother curves; 20 is sufficient for typical spacing.
_SAMPLE_DENSITY = 20


def generate_wave_field(
    safe_poly: Polygon,
    pattern: ConfigPattern,
    fabrication: ConfigFabrication,
) -> list[Polygon]:
    """
    Generate wave_field cut bands clipped to safe_poly.

    Returns a list of Polygon objects representing cut regions.
    Each polygon corresponds to one wave band (guide buffered by line_width/2).
    """
    minx, miny, maxx, maxy = safe_poly.bounds
    w = maxx - minx
    h = maxy - miny

    spacing = pattern.spacing
    line_width = pattern.line_width
    amplitude = pattern.amplitude
    symm = pattern.symmetry.value

    # Angular frequency: density=0 → straight lines, density=1 → one full cycle
    # per spacing unit.
    frequency = pattern.density * 2.0 * math.pi / max(spacing, 1e-9)

    # Determine y generation range based on symmetry
    if symm in ("y", "xy"):
        y_gen_start = miny
        y_gen_end = (miny + maxy) / 2.0
    else:
        y_gen_start = miny
        y_gen_end = maxy

    # Number of guide lines (extend one extra on each side to cover boundary)
    n_lines = max(int(math.ceil((y_gen_end - y_gen_start) / spacing)) + 2, 1)

    # All phases derived deterministically from seed
    rng = np.random.default_rng(pattern.seed)
    phases = rng.uniform(0.0, 2.0 * math.pi, n_lines)

    # X sample points — extend past boundary to avoid edge artifacts after clip
    n_pts = max(int(w * _SAMPLE_DENSITY / max(spacing, 1e-9)), 128)
    xs = np.linspace(minx - amplitude - line_width, maxx + amplitude + line_width, n_pts)

    raw_bands: list[Polygon] = []

    for i in range(n_lines):
        y_center = y_gen_start + i * spacing
        ys = y_center + amplitude * np.sin(frequency * (xs - minx) + phases[i])

        guide = LineString(list(zip(xs.tolist(), ys.tolist())))

        if line_width < 1e-9:
            continue  # degenerate — skip

        band = guide.buffer(line_width / 2.0, cap_style=2, join_style=2)
        if isinstance(band, Polygon) and not band.is_empty:
            raw_bands.append(band)

    # ── Symmetry mirroring ──────────────────────────────────────────────────
    cx = (minx + maxx) / 2.0
    cy = (miny + maxy) / 2.0

    if symm in ("y", "xy"):
        # Mirror generated (bottom) bands about the horizontal center line
        mirrored = [
            affinity.scale(b, xfact=1.0, yfact=-1.0, origin=(cx, cy))
            for b in raw_bands
        ]
        raw_bands = raw_bands + mirrored

    if symm in ("x", "xy"):
        # Clip all bands to right half, then mirror to left half
        right_box = box(
            cx,
            miny - amplitude - line_width,
            maxx + amplitude + line_width,
            maxy + amplitude + line_width,
        )
        right_half = [b.intersection(right_box) for b in raw_bands]
        right_half = [b for b in right_half if not b.is_empty and b.area > 1e-12]
        left_half = [
            affinity.scale(b, xfact=-1.0, yfact=1.0, origin=(cx, cy))
            for b in right_half
        ]
        raw_bands = right_half + left_half

    # ── Clip to safe boundary and normalise output ──────────────────────────
    result: list[Polygon] = []
    for band in raw_bands:
        clipped = band.intersection(safe_poly)
        if clipped.is_empty:
            continue
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
        # GeometryCollection
        for g in geom.geoms:
            _collect_polygons(g, out)
