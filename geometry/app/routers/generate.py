"""
Generate router — stub for Milestone B.
POST /generate will invoke the geometry pipeline.
"""

from fastapi import APIRouter, Depends
from ..models import GenerateRequest, GenerateResult, ValidationReport
from ..auth import require_api_key

router = APIRouter(prefix="/generate", tags=["generate"])


@router.post("", response_model=GenerateResult, dependencies=[Depends(require_api_key)])
async def generate(request: GenerateRequest) -> GenerateResult:
    """
    Geometry generation entry point.
    Milestone B: boundary normalization → pattern generation → validation → parts list.
    """
    # Stub — implementation in Milestone B
    return GenerateResult(
        status="error",
        message="Geometry generation not yet implemented (Milestone B).",
        validation=ValidationReport(
            valid=False,
            issues=[
                {
                    "level": "info",
                    "code": "not_implemented",
                    "message": "Geometry generation will be implemented in Milestone B.",
                    "field": None,
                }
            ],
        ),
    )
