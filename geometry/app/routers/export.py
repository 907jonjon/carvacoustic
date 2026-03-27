"""
POST /export — assemble and return the export ZIP bundle.

Returns a binary ZIP response containing:
  manifest.json, project-config.json, sheet-01.dxf, sheet-01.svg, README.txt

The web app streams this directly to the browser as a file download.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from ..models import ExportRequest
from ..auth import require_api_key
from ..geometry.boundary import build_boundary_polygon, compute_safe_boundary, normalize_boundary
from ..geometry.patterns.wave_field import generate_wave_field
from ..geometry.validation import validate_config
from ..geometry.pipeline import _place_labels, _collect_polygons
from ..geometry.export.bundle import build_export_bundle
from shapely.ops import unary_union

router = APIRouter(prefix="/export", tags=["export"])


@router.post("", dependencies=[Depends(require_api_key)])
async def export(request: ExportRequest) -> Response:
    """
    Run the geometry pipeline and return a ZIP export bundle.
    Raises 422 if config has blocking errors.
    """
    config = request.config

    # Boundary
    try:
        boundary_poly = build_boundary_polygon(config.boundary)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    boundary_poly, boundary_issues = normalize_boundary(boundary_poly)
    if any(i.level == "error" for i in boundary_issues):
        msgs = "; ".join(i.message for i in boundary_issues if i.level == "error")
        raise HTTPException(status_code=422, detail=f"Boundary error: {msgs}")

    safe_poly = compute_safe_boundary(boundary_poly, config.boundary.safe_margin)

    # Config validation — block on errors
    config_issues = validate_config(config)
    errors = [i for i in config_issues if i.level == "error"]
    if errors:
        msgs = "; ".join(i.message for i in errors)
        raise HTTPException(status_code=422, detail=f"Config error: {msgs}")

    # Pattern generation
    family = config.pattern.family.value
    if family == "wave_field":
        bands = generate_wave_field(safe_poly, config.pattern, config.fabrication)
    else:
        raise HTTPException(
            status_code=422,
            detail=f"Pattern family '{family}' not yet implemented (Milestone C).",
        )

    if bands:
        merged = unary_union(bands)
        bands = _collect_polygons(merged)

    labels = _place_labels(boundary_poly, config)

    zip_bytes, filename = build_export_bundle(
        config, boundary_poly, safe_poly, bands, labels
    )

    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(zip_bytes)),
        },
    )
