"""
POST /generate — full geometry pipeline for Milestone B.
Returns SVG preview, validation report, and part count.
"""

from fastapi import APIRouter, Depends
from ..models import GenerateRequest, GenerateResult
from ..auth import require_api_key
from ..geometry.pipeline import run_pipeline

router = APIRouter(prefix="/generate", tags=["generate"])


@router.post("", response_model=GenerateResult, dependencies=[Depends(require_api_key)])
async def generate(request: GenerateRequest) -> GenerateResult:
    """
    Run the geometry pipeline (steps 1–9 of spec 02-geometry-spec.md).
    Returns SVG preview string and validation report.
    Layout (step 10) and export bundle assembly (step 11) are separate endpoints.
    """
    return run_pipeline(request.config)
