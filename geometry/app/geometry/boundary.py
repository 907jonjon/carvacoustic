"""
Boundary normalization — step 1 and 2 of the geometry pipeline.

Builds a Shapely Polygon from a ConfigBoundary, validates it,
and computes the inner safe-margin boundary.
"""

from __future__ import annotations

import math
from shapely.geometry import Polygon, MultiPolygon, box
from shapely.validation import make_valid

from ..models import ConfigBoundary, ValidationIssue


# Segments ignored when simplifying micro-segments
MICRO_SEGMENT_THRESHOLD = 1e-6


def build_boundary_polygon(cfg: ConfigBoundary) -> Polygon:
    """
    Build a Shapely Polygon from boundary config.
    Raises ValueError for unsupported or invalid configs.
    """
    btype = cfg.type.value

    if btype == "rectangle":
        return box(0.0, 0.0, cfg.width, cfg.height)

    if btype == "rounded_rectangle":
        return _rounded_rect(cfg.width, cfg.height, cfg.corner_radius)

    if btype == "svg_import":
        raise ValueError(
            "SVG import boundary is not yet implemented. "
            "Use 'rectangle' or 'rounded_rectangle'."
        )

    raise ValueError(f"Unknown boundary type: {btype!r}")


def _rounded_rect(w: float, h: float, r: float) -> Polygon:
    """
    Construct a rounded rectangle via inward shrink + outward buffer.
    Resolution=32 gives smooth quarter-circle corners.
    """
    r = min(r, w / 2.0, h / 2.0)
    if r <= 0:
        return box(0.0, 0.0, w, h)
    inner = box(r, r, w - r, h - r)
    return inner.buffer(r, resolution=32, cap_style=1, join_style=1)


def normalize_boundary(poly: Polygon) -> tuple[Polygon, list[ValidationIssue]]:
    """
    Normalize and validate a boundary polygon.

    Spec requirements:
    - ensure closed outer shape
    - remove duplicate points
    - simplify micro-segments below threshold
    - normalize winding/orientation
    - reject: self-intersection, multiple disconnected outer loops, zero-area

    Returns (normalized_poly, issues).
    Any issue with level='error' means the boundary is unusable.
    """
    issues: list[ValidationIssue] = []

    if poly.is_empty:
        issues.append(ValidationIssue(
            level="error",
            code="invalid_boundary",
            message="Boundary is empty.",
        ))
        return poly, issues

    if poly.area < MICRO_SEGMENT_THRESHOLD:
        issues.append(ValidationIssue(
            level="error",
            code="invalid_boundary",
            message="Boundary has zero or negligible area.",
        ))
        return poly, issues

    # Attempt repair
    if not poly.is_valid:
        poly = make_valid(poly)

    # After repair, might have become a MultiPolygon
    if isinstance(poly, MultiPolygon):
        issues.append(ValidationIssue(
            level="error",
            code="invalid_boundary",
            message=(
                "Boundary contains multiple disconnected outer loops. "
                "Only a single closed outer shape is supported."
            ),
        ))
        return poly, issues

    if not isinstance(poly, Polygon):
        issues.append(ValidationIssue(
            level="error",
            code="invalid_boundary",
            message="Boundary geometry could not be resolved to a single polygon.",
        ))
        return poly, issues

    # Self-intersection check (exterior ring must be simple)
    if not poly.exterior.is_simple:
        issues.append(ValidationIssue(
            level="error",
            code="self_intersection",
            message="Boundary outer ring self-intersects.",
        ))
        return poly, issues

    # Simplify micro-segments
    poly = poly.simplify(MICRO_SEGMENT_THRESHOLD, preserve_topology=True)

    # Ensure CCW exterior winding (Shapely convention)
    from shapely.geometry.polygon import orient
    poly = orient(poly, sign=1.0)

    return poly, issues


def compute_safe_boundary(poly: Polygon, margin: float) -> Polygon:
    """
    Inward buffer (erosion) by safe_margin.
    Falls back to the original polygon if the margin is too large.
    """
    if margin <= 0:
        return poly

    safe = poly.buffer(-margin, resolution=32)

    if safe.is_empty or safe.area < MICRO_SEGMENT_THRESHOLD:
        # Margin consumes the entire boundary — return original and let
        # validation catch the resulting empty pattern.
        return poly

    # If erosion produced a MultiPolygon, take the largest piece
    if isinstance(safe, MultiPolygon):
        safe = max(safe.geoms, key=lambda g: g.area)

    return safe
