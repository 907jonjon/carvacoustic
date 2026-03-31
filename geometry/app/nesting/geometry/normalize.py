"""Polygon normalization — winding, dedup, spike collapse, collinear merge."""

from __future__ import annotations

from shapely.geometry import Polygon
from shapely.geometry.polygon import orient


def normalize_polygon(poly: Polygon, min_edge_length: float = 0.01) -> Polygon:
    """
    Normalize a polygon for nesting:
    - Ensure CCW exterior winding (CW holes)
    - Remove consecutive duplicate points (within 1e-10)
    - Collapse spikes shorter than *min_edge_length*
    - Final micro-simplify to merge nearly-collinear edges
    """
    # CCW exterior, CW holes
    poly = orient(poly, sign=1.0)

    # Remove duplicate consecutive points
    coords = list(poly.exterior.coords)
    deduped = _remove_consecutive_dupes(coords, tol=1e-10)

    # Collapse tiny spikes
    cleaned = _collapse_spikes(deduped, min_edge_length)

    # Rebuild polygon (with holes preserved)
    holes = [list(ring.coords) for ring in poly.interiors]
    result = Polygon(cleaned, holes)

    # Final micro-simplify
    result = result.simplify(1e-6, preserve_topology=True)

    if not result.is_valid:
        result = result.buffer(0)

    return result


def _remove_consecutive_dupes(
    coords: list[tuple[float, ...]], tol: float
) -> list[tuple[float, ...]]:
    if len(coords) < 2:
        return coords
    out = [coords[0]]
    for pt in coords[1:]:
        prev = out[-1]
        if abs(pt[0] - prev[0]) > tol or abs(pt[1] - prev[1]) > tol:
            out.append(pt)
    # Ensure ring closure
    if out[0] != out[-1]:
        out.append(out[0])
    return out


def _collapse_spikes(
    coords: list[tuple[float, ...]], min_len: float
) -> list[tuple[float, ...]]:
    """Remove vertices that create edges shorter than *min_len*."""
    if len(coords) < 4:
        return coords
    import math

    out = [coords[0]]
    for pt in coords[1:-1]:  # skip closing duplicate
        prev = out[-1]
        d = math.hypot(pt[0] - prev[0], pt[1] - prev[1])
        if d >= min_len:
            out.append(pt)
    # Close ring
    out.append(out[0])
    return out
