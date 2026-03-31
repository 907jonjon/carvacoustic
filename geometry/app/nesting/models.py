"""
Core data model for the nesting engine.

Uses plain dataclasses (not Pydantic) — these are internal solver types,
not API schema.  The bridge back to LayoutResult lives in ingest.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from shapely.geometry import Polygon
from shapely.prepared import PreparedGeometry


@dataclass
class SheetSpec:
    width: float
    height: float
    edge_margin: float          # from config.fabrication.tool.border_gap
    grain_axis: str | None      # "x" | "y" | None


@dataclass
class TransformSpec:
    angle_deg: float            # 0, 90, 180, 270
    mirrored: bool              # True = flipped along Y axis

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TransformSpec):
            return NotImplemented
        return self.angle_deg == other.angle_deg and self.mirrored == other.mirrored

    def __hash__(self) -> int:
        return hash((self.angle_deg, self.mirrored))


@dataclass
class VariantGeom:
    transform: TransformSpec
    polygon: Polygon                # exact transformed polygon
    inflated: Polygon               # polygon.buffer(clearance / 2)
    prepared_inflated: PreparedGeometry  # for fast intersection tests
    aabb: tuple[float, float, float, float]  # inflated.bounds
    preferred_edges: list[dict]
    area: float


@dataclass
class PartSpec:
    part_id: str
    quantity: int                    # usually 1 for slats
    variants: list[VariantGeom]      # one per legal transform
    original_polygon: Polygon        # unsimplified, for export
    grain_locked: bool
    allow_mirror: bool


@dataclass
class Placement:
    part_id: str
    sheet_index: int
    transform: TransformSpec
    x: float                         # translation X
    y: float                         # translation Y
    anchor_tag: str                  # "boundary", "flat-edge-contact", "generic-contact", "reinsert"
    score: float


@dataclass
class NestJob:
    sheets: SheetSpec                # all sheets are identical for now
    parts: list[PartSpec]
    clearance: float
    mode: str                        # "fast" | "balanced" | "max_yield"
    seed: int | None = None


@dataclass
class NestResult:
    placements: list[Placement]
    sheets_used: int
    utilization: float               # average across sheets
    unplaced: list[str]              # part_ids that couldn't be placed
    warnings: list[str]
    elapsed_ms: float
