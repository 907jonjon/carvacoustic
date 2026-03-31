"""NestResult -> JSON-serializable Pydantic models for API responses."""

from __future__ import annotations

from pydantic import BaseModel

from ..models import NestResult, Placement


class PlacementOut(BaseModel):
    part_id: str
    sheet_index: int
    angle_deg: float
    mirrored: bool
    x: float
    y: float
    anchor_tag: str


class NestResultOut(BaseModel):
    status: str                 # "ok" | "error"
    placements: list[PlacementOut]
    sheets_used: int
    utilization: float
    unplaced: list[str]
    warnings: list[str]
    elapsed_ms: float
    mode: str
    seed: int | None

    @classmethod
    def from_nest_result(
        cls,
        result: NestResult,
        mode: str = "balanced",
        seed: int | None = None,
    ) -> "NestResultOut":
        """Convert internal NestResult to the API-facing schema."""
        status = "ok" if not result.unplaced else "error"
        placements = [
            PlacementOut(
                part_id=p.part_id,
                sheet_index=p.sheet_index,
                angle_deg=p.transform.angle_deg,
                mirrored=p.transform.mirrored,
                x=round(p.x, 4),
                y=round(p.y, 4),
                anchor_tag=p.anchor_tag,
            )
            for p in result.placements
        ]
        return cls(
            status=status,
            placements=placements,
            sheets_used=result.sheets_used,
            utilization=round(result.utilization, 4),
            unplaced=result.unplaced,
            warnings=result.warnings,
            elapsed_ms=round(result.elapsed_ms, 1),
            mode=mode,
            seed=seed,
        )


def serialize_result(
    result: NestResult,
    mode: str = "balanced",
    seed: int | None = None,
) -> NestResultOut:
    """Convert internal NestResult to the API-facing schema."""
    return NestResultOut.from_nest_result(result, mode, seed)


def nest_result_to_dict(result: NestResult) -> dict:
    """Convert NestResult to a JSON-serializable dictionary."""
    return {
        "sheets_used": result.sheets_used,
        "utilization": round(result.utilization, 4),
        "elapsed_ms": round(result.elapsed_ms, 1),
        "unplaced": result.unplaced,
        "warnings": result.warnings,
        "placements": [
            _placement_to_dict(p) for p in result.placements
        ],
    }


def _placement_to_dict(p: Placement) -> dict:
    return {
        "part_id": p.part_id,
        "sheet_index": p.sheet_index,
        "x": round(p.x, 4),
        "y": round(p.y, 4),
        "angle_deg": p.transform.angle_deg,
        "mirrored": p.transform.mirrored,
        "anchor_tag": p.anchor_tag,
        "score": round(p.score, 4),
    }
