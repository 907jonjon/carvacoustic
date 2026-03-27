"""
wave_field pattern generator.

Spec intent:
- Build repeated guide lines across the usable boundary.
- Displace guides by a smooth wave function.
- Clip to boundary.
- Convert to line/band geometry based on fabrication settings (line_width).

Visual goal: gentle rippling waves / flowing contours across the panel —
organic and flowing, not interlocked or chaotic.

Approach:
- All guide lines share the same base phase (drawn once from the seeded RNG).
  This makes every wave crest and trough align, producing the "flowing ripple"
  look of water waves or wood grain.
- An optional slow phase drift between adjacent lines (phase_drift) adds subtle
  organic variation without breaking the overall flow direction.
- density controls wave frequency (cycles per unit length across the panel).
- amplitude controls wave height (lateral displacement of each guide line).

Determinism rule: same config → same geometry.
"""

from __future__ import annotations

import math

import numpy as np
from shapely import affinity
from shapely.geometry import LineString, MultiPolygon, Polygon, box

from ...models import ConfigFabrication, ConfigPattern

# Number of sample points along each guide line.
_N_PTS = 256

# Slow phase drift between adjacent lines (radians per line).
# Small enough to keep the overall wave flow coherent; large enough for
# organic variation. Roughly 1 full extra cycle spread across the panel.
_PHASE_DRIFT_PER_LINE = 0.18


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

    spacing = max(pattern.spacing, 1e-6)
    line_width = pattern.line_width
    amplitude = pattern.amplitude
    symm = pattern.symmetry.value

    # Wave frequency: density controls how many cycles fit across the panel width.
    # density=0 → straight lines; density=1 → ~1 full cycle across the panel.
    frequency = pattern.density * 2.0 * math.pi / max(w, spacing)

    # Single base phase from seed — all lines share this foundation, giving a
    # coherent flowing wave rather than random independent wiggles.
    rng = np.random.default_rng(pattern.seed)
    base_phase = rng.uniform(0.0, 2.0 * math.pi)

    # Determine Y generation range (symmetry halving)
    if symm in ("y", "xy"):
        y_gen_start = miny
        y_gen_end = (miny + maxy) / 2.0
    else:
        y_gen_start = miny
        y_gen_end = maxy

    # Guide line count — extend one extra on each side to avoid edge artifacts
    n_lines = max(int(math.ceil((y_gen_end - y_gen_start) / spacing)) + 2, 1)

    # X sample points — extend past boundary to cover full clip after wave displacement
    xs = np.linspace(minx - amplitude - line_width, maxx + amplitude + line_width, _N_PTS)

    raw_bands: list[Polygon] = []

    for i in range(n_lines):
        y_center = y_gen_start + i * spacing
        # Slow drift accumulates across lines, keeping waves coherent but not identical
        phase = base_phase + i * _PHASE_DRIFT_PER_LINE
        ys = y_center + amplitude * np.sin(frequency * (xs - minx) + phase)

        guide = LineString(list(zip(xs.tolist(), ys.tolist())))

        if line_width < 1e-9:
            continue

        band = guide.buffer(line_width / 2.0, cap_style=2, join_style=2)
        if isinstance(band, Polygon) and not band.is_empty:
            raw_bands.append(band)

    # ── Symmetry mirroring ──────────────────────────────────────────────────
    cx = (minx + maxx) / 2.0
    cy = (miny + maxy) / 2.0

    if symm in ("y", "xy"):
        mirrored = [
            affinity.scale(b, xfact=1.0, yfact=-1.0, origin=(cx, cy))
            for b in raw_bands
        ]
        raw_bands = raw_bands + mirrored

    if symm in ("x", "xy"):
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
        for g in geom.geoms:  # type: ignore[union-attr]
            _collect_polygons(g, out)
