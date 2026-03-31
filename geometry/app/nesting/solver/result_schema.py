"""NestResult -> JSON-serializable output for API responses."""

from __future__ import annotations

from ..models import NestResult, Placement


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
