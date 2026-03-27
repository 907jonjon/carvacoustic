"""
POST /validate — run config + geometry validation without returning SVG.
"""

from fastapi import APIRouter, Depends

from ..auth import require_api_key
from ..geometry.pipeline import run_pipeline_internal
from ..geometry.validation import validate_config
from ..models import ValidateRequest, ValidationReport, ValidationIssue

router = APIRouter(prefix="/validate", tags=["validate"])


@router.post("", response_model=ValidationReport, dependencies=[Depends(require_api_key)])
async def validate(request: ValidateRequest) -> ValidationReport:
    """Run all v2 validation rules. Config-level always runs; geometry-level runs if config is valid."""
    config = request.config
    issues: list[ValidationIssue] = []

    config_issues = validate_config(config)
    issues.extend(config_issues)

    if any(i.level == "error" for i in config_issues):
        return ValidationReport(valid=False, issues=issues)

    result = run_pipeline_internal(config)
    issues.extend(result["issues"])

    valid = not any(i.level == "error" for i in issues)
    return ValidationReport(valid=valid, issues=issues)
