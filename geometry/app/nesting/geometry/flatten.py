"""Polygon simplification for nesting — reduce vertex count while preserving cut-relevant features."""

from __future__ import annotations

import logging

from shapely.geometry import Polygon

logger = logging.getLogger(__name__)


def simplify_polygon(poly: Polygon, tool_diameter: float) -> Polygon:
    """
    Simplify polygon to reduce vertex count for nesting.

    Uses Shapely's topology-preserving simplify with tolerance = tool_diameter / 4.
    Features smaller than half the kerf can't be cut, so they're safe to remove.

    Returns the simplified polygon, or the original if simplification produces
    an invalid result.
    """
    tolerance = tool_diameter / 4.0
    simplified = poly.simplify(tolerance, preserve_topology=True)

    if not simplified.is_valid or simplified.is_empty:
        logger.warning("Simplification produced invalid polygon; using original")
        return poly

    orig_count = len(poly.exterior.coords)
    new_count = len(simplified.exterior.coords)
    if new_count < orig_count:
        logger.debug(
            "Simplified polygon: %d -> %d vertices (%.0f%% reduction)",
            orig_count,
            new_count,
            100.0 * (1.0 - new_count / orig_count),
        )

    return simplified
