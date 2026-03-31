"""Sheet state manager — tracks placed parts, spatial index, usable bounds."""

from __future__ import annotations

from dataclasses import dataclass, field

from shapely import affinity
from shapely.geometry import Polygon

from ..models import Placement, SheetSpec, TransformSpec, VariantGeom
from .spatial_hash import SpatialIndex


@dataclass
class SheetState:
    """Mutable state for one material sheet during nesting."""

    index: int
    usable_bounds: Polygon          # contracted sheet polygon
    spatial_index: SpatialIndex = field(default_factory=SpatialIndex)
    placements: list[Placement] = field(default_factory=list)
    placed_inflated: list[Polygon] = field(default_factory=list)
    used_area: float = 0.0

    def place(
        self,
        variant: VariantGeom,
        x: float,
        y: float,
        part_id: str,
        transform: TransformSpec,
        anchor_tag: str,
        score: float,
    ) -> None:
        """Record a placement and update spatial index."""
        translated = affinity.translate(variant.inflated, xoff=x, yoff=y)
        self.placed_inflated.append(translated)
        self.spatial_index.add(translated)
        self.used_area += variant.area
        self.placements.append(
            Placement(
                part_id=part_id,
                sheet_index=self.index,
                transform=transform,
                x=x,
                y=y,
                anchor_tag=anchor_tag,
                score=score,
            )
        )
