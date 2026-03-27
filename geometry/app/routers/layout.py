"""
Layout router — stub for Milestone C.
POST /layout runs the sheet-nesting layout engine.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from ..models import LayoutRequest
from ..auth import require_api_key

router = APIRouter(prefix="/layout", tags=["layout"])


class LayoutResult(BaseModel):
    status: str
    message: str
    sheet_count: int = 0


@router.post("", response_model=LayoutResult, dependencies=[Depends(require_api_key)])
async def layout(request: LayoutRequest) -> LayoutResult:
    """
    Sheet layout / nesting entry point.
    Phase 1 layout algorithm (spec 02-geometry-spec.md):
      1. rectangular footprints
      2. descending area sort
      3. first-fit decreasing placement
      4. optional 90° rotation
      5. spill to new sheet when needed
    Milestone C: full implementation.
    """
    # Stub — implementation in Milestone C
    return LayoutResult(
        status="error",
        message="Layout engine not yet implemented (Milestone C).",
    )
