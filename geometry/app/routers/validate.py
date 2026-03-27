"""
POST /validate — run config + geometry validation without returning SVG.
Useful for quick config checks before committing to a full generate.
"""

from fastapi import APIRouter, Depends
from ..models import ValidateRequest, ValidationReport, ValidationIssue
from ..auth import require_api_key
from ..geometry.boundary import build_boundary_polygon, compute_safe_boundary, normalize_boundary
from ..geometry.validation import validate_config, validate_geometry
from ..geometry.patterns.wave_field import generate_wave_field
from ..geometry.patterns.contour_bands import generate_contour_bands
from ..geometry.patterns.slat_rib import generate_slat_rib

router = APIRouter(prefix="/validate", tags=["validate"])


@router.post("", response_model=ValidationReport, dependencies=[Depends(require_api_key)])
async def validate(request: ValidateRequest) -> ValidationReport:
    """
    Run all phase-1 validation rules from spec 02-geometry-spec.md.
    Config-level checks always run. Geometry-level checks run if the config is valid.
    """
    config = request.config
    issues: list[ValidationIssue] = []

    # Boundary
    try:
        raw_poly = build_boundary_polygon(config.boundary)
    except ValueError as exc:
        issues.append(ValidationIssue(
            level="error", code="invalid_boundary", message=str(exc)
        ))
        return ValidationReport(valid=False, issues=issues)

    _, boundary_issues = normalize_boundary(raw_poly)
    issues.extend(boundary_issues)

    if any(i.level == "error" for i in issues):
        return ValidationReport(valid=False, issues=issues)

    # Config-level
    config_issues = validate_config(config)
    issues.extend(config_issues)

    if any(i.level == "error" for i in config_issues):
        return ValidationReport(valid=False, issues=issues)

    # Geometry-level — run pattern to get bands
    safe_poly = compute_safe_boundary(raw_poly, config.boundary.safe_margin)
    family = config.pattern.family.value

    if family == "wave_field":
        bands = generate_wave_field(safe_poly, config.pattern, config.fabrication)
    elif family == "contour_bands":
        bands = generate_contour_bands(safe_poly, config.pattern, config.fabrication)
    elif family == "slat_rib":
        bands = generate_slat_rib(safe_poly, config.pattern, config.fabrication)
    else:
        issues.append(ValidationIssue(
            level="error",
            code="not_implemented",
            message=f"Pattern family '{family}' is not supported.",
        ))
        return ValidationReport(valid=False, issues=issues)

    geom_issues = validate_geometry(bands, raw_poly, safe_poly, config)
    issues.extend(geom_issues)

    valid = not any(i.level == "error" for i in issues)
    return ValidationReport(valid=valid, issues=issues)
