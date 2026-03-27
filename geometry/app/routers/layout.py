"""
POST /layout — run the sheet-nesting layout engine.
Returns sheet count, per-sheet utilization, and placement details.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..auth import require_api_key
from ..geometry.boundary import build_boundary_polygon, compute_safe_boundary, normalize_boundary
from ..models import LayoutRequest, ValidationIssue

router = APIRouter(prefix="/layout", tags=["layout"])


class PlacementInfo(BaseModel):
    copy_index: int
    sheet: int
    x: float
    y: float
    rotated_90: bool


class LayoutResponse(BaseModel):
    status: str
    message: str = ""
    sheet_count: int = 0
    overflow: int = 0
    utilization: list[float] = []
    placements: list[PlacementInfo] = []
    issues: list[ValidationIssue] = []


@router.post("", response_model=LayoutResponse, dependencies=[Depends(require_api_key)])
async def layout(request: LayoutRequest) -> LayoutResponse:
    """
    Run the phase-1 layout algorithm (spec 02-geometry-spec.md §Layout / nesting):
      1. Rectangular footprints
      2. Descending area sort
      3. First-fit decreasing placement
      4. Optional 90° rotation
      5. Spill to new sheet when needed
    """
    from ..geometry.layout import run_layout

    config = request.config
    issues: list[ValidationIssue] = []

    # Build and normalize boundary
    try:
        raw_poly = build_boundary_polygon(config.boundary)
    except ValueError as exc:
        return LayoutResponse(
            status="error",
            message=str(exc),
            issues=[ValidationIssue(level="error", code="invalid_boundary", message=str(exc))],
        )

    boundary_poly, boundary_issues = normalize_boundary(raw_poly)
    issues.extend(boundary_issues)

    if any(i.level == "error" for i in issues):
        return LayoutResponse(
            status="error",
            message="Boundary normalization failed.",
            issues=issues,
        )

    result = run_layout(boundary_poly, config)

    placements: list[PlacementInfo] = []
    for sheet in result.sheets:
        for p in sheet.placements:
            placements.append(
                PlacementInfo(
                    copy_index=p.copy_index,
                    sheet=sheet.sheet_index,
                    x=p.x,
                    y=p.y,
                    rotated_90=p.rotated_90,
                )
            )

    if result.overflow:
        issues.append(ValidationIssue(
            level="warning",
            code="layout_overflow",
            message=f"{result.overflow} copy(ies) could not be placed on any sheet.",
        ))

    return LayoutResponse(
        status="ok" if not result.overflow else "warning",
        sheet_count=len(result.sheets),
        overflow=result.overflow,
        utilization=[s.utilization for s in result.sheets],
        placements=placements,
        issues=issues,
    )
