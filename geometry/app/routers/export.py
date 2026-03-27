"""
Export router — stub for Milestone C.
POST /export assembles the DXF/SVG/PDF/JSON export bundle.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from ..models import ExportRequest
from ..auth import require_api_key

router = APIRouter(prefix="/export", tags=["export"])


class ExportResult(BaseModel):
    status: str
    message: str
    bundle_path: str | None = None


@router.post("", response_model=ExportResult, dependencies=[Depends(require_api_key)])
async def export(request: ExportRequest) -> ExportResult:
    """
    Export bundle assembly entry point.
    Output (spec 02-geometry-spec.md):
      - manifest.json
      - project-config.json
      - per-sheet DXF (layers: CUT_OUTER, CUT_INNER, ENGRAVE_LABEL, REFERENCE_BOUNDARY, SAFE_MARGIN_GUIDE)
      - per-sheet SVG
      - reference PDF
      - package README
    Milestone C: full implementation.
    """
    # Stub — implementation in Milestone C
    return ExportResult(
        status="error",
        message="Export not yet implemented (Milestone C).",
    )
