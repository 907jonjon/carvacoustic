"""Broad-phase spatial index using Shapely STRtree."""

from __future__ import annotations

from shapely import STRtree
from shapely.geometry import Polygon


class SpatialIndex:
    """Wrapper around Shapely STRtree for fast AABB-based broad-phase checks."""

    def __init__(self) -> None:
        self._polys: list[Polygon] = []
        self._tree: STRtree | None = None

    def add(self, inflated_poly: Polygon) -> None:
        """Add an inflated polygon to the index. Invalidates the tree cache."""
        self._polys.append(inflated_poly)
        self._tree = None  # invalidate

    def query_nearby(self, candidate_inflated: Polygon) -> list[Polygon]:
        """Return placed polygons whose AABBs overlap the candidate's AABB."""
        if not self._polys:
            return []
        if self._tree is None:
            self._tree = STRtree(self._polys)
        indices = self._tree.query(candidate_inflated)
        return [self._polys[i] for i in indices]

    @property
    def count(self) -> int:
        return len(self._polys)
