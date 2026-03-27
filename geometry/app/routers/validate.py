"""
Validate router — stub for Milestone B.
POST /validate runs the validation engine against a config.
"""

from fastapi import APIRouter, Depends
from ..models import ValidateRequest, ValidationReport, ValidationIssue
from ..auth import require_api_key

router = APIRouter(prefix="/validate", tags=["validate"])


@router.post("", response_model=ValidationReport, dependencies=[Depends(require_api_key)])
async def validate(request: ValidateRequest) -> ValidationReport:
    """
    Config validation entry point.
    Phase 1 validation rules defined in spec 02-geometry-spec.md.
    Milestone B: implement boundary, pattern, fabrication, and layout validators.
    """
    # Stub — implementation in Milestone B
    return ValidationReport(
        valid=True,
        issues=[
            ValidationIssue(
                level="info",
                code="validation_not_implemented",
                message="Full validation will be implemented in Milestone B.",
            )
        ],
    )
