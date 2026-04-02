"""POST /preview — lightweight geometry preview (no nesting, no SVG)."""

from fastapi import APIRouter, Depends

from ..auth import require_api_key
from ..geometry.pipeline import run_preview_pipeline
from ..models import GenerateRequest, PreviewResult

router = APIRouter(prefix="/preview", tags=["preview"])


@router.post("", response_model=PreviewResult, dependencies=[Depends(require_api_key)])
async def preview(request: GenerateRequest) -> PreviewResult:
    """Run the lightweight preview pipeline — geometry only."""
    return run_preview_pipeline(request.config)
