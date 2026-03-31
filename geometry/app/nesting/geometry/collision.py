"""Exact overlap testing using Shapely prepared geometry."""

from __future__ import annotations

from shapely import affinity
from shapely.geometry import Polygon
from shapely.prepared import PreparedGeometry


def check_collision(
    variant_inflated: PreparedGeometry,
    pose_x: float,
    pose_y: float,
    placed_inflated: list[Polygon],
) -> bool:
    """
    Return True if the variant at (pose_x, pose_y) overlaps any placed part.

    Uses the prepared geometry's context polygon, translates it, then
    tests intersection against each placed inflated polygon.
    """
    translated = affinity.translate(
        variant_inflated.context, xoff=pose_x, yoff=pose_y
    )
    for placed in placed_inflated:
        if translated.intersects(placed):
            # Filter out boundary-only touches (shared edge is OK)
            if not translated.intersection(placed).is_empty:
                overlap = translated.intersection(placed)
                if overlap.area > 1e-10:
                    return True
    return False


def check_inside_sheet(
    variant_inflated: Polygon,
    pose_x: float,
    pose_y: float,
    usable_bounds: Polygon,
) -> bool:
    """Return True if the variant at (pose_x, pose_y) fits inside the usable sheet."""
    translated = affinity.translate(variant_inflated, xoff=pose_x, yoff=pose_y)
    return usable_bounds.contains(translated)
