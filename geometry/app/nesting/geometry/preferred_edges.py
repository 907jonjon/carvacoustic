"""Flat-edge detection — find nearly-straight edge chains for placement bias."""

from __future__ import annotations

import math

from shapely.geometry import Polygon


def detect_preferred_edges(
    poly: Polygon, min_length_ratio: float = 0.3
) -> list[dict]:
    """
    Detect nearly-straight edge chains on a polygon.

    Returns list of dicts with keys:
        start_idx, end_idx, length, angle (degrees),
        confidence (0-1, higher = straighter), midpoint (x, y)

    A "preferred edge" is a chain of consecutive edges where the total
    angular deviation is < 5 degrees and the chain length is
    > min_length_ratio of the polygon's longest dimension.
    """
    coords = list(poly.exterior.coords)[:-1]  # drop closing duplicate
    n = len(coords)
    if n < 3:
        return []

    # Polygon's longest dimension
    bounds = poly.bounds
    longest_dim = max(bounds[2] - bounds[0], bounds[3] - bounds[1])
    min_length = longest_dim * min_length_ratio

    # Compute edge vectors and angles
    edges: list[tuple[float, float, float, float]] = []  # dx, dy, length, angle_deg
    for i in range(n):
        j = (i + 1) % n
        dx = coords[j][0] - coords[i][0]
        dy = coords[j][1] - coords[i][1]
        length = math.hypot(dx, dy)
        angle = math.degrees(math.atan2(dy, dx))
        edges.append((dx, dy, length, angle))

    # Find chains of nearly-collinear edges
    preferred: list[dict] = []
    max_deviation_deg = 5.0

    i = 0
    while i < n:
        chain_start = i
        chain_length = edges[i][2]
        base_angle = edges[i][3]

        j = i + 1
        while j < n:
            edge_angle = edges[j][3]
            deviation = abs(_angle_diff(edge_angle, base_angle))
            if deviation > max_deviation_deg:
                break
            chain_length += edges[j][2]
            j += 1

        if chain_length >= min_length:
            chain_end = j % n
            # Compute midpoint of chain
            mid_idx = (chain_start + (j - chain_start) // 2) % n
            mid_next = (mid_idx + 1) % n
            midpoint = (
                (coords[mid_idx][0] + coords[mid_next][0]) / 2.0,
                (coords[mid_idx][1] + coords[mid_next][1]) / 2.0,
            )
            # Confidence: ratio of chain length to straight-line distance
            sx, sy = coords[chain_start]
            ex, ey = coords[j % n]
            straight = math.hypot(ex - sx, ey - sy)
            confidence = straight / chain_length if chain_length > 0 else 0.0

            preferred.append({
                "start_idx": chain_start,
                "end_idx": chain_end,
                "length": chain_length,
                "angle": base_angle,
                "confidence": min(confidence, 1.0),
                "midpoint": midpoint,
            })

        i = j if j > i else i + 1

    return preferred


def _angle_diff(a: float, b: float) -> float:
    """Signed angular difference in degrees, normalized to [-180, 180]."""
    d = a - b
    while d > 180.0:
        d -= 360.0
    while d < -180.0:
        d += 360.0
    return d
