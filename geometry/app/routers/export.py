"""
POST /export — assemble and return the export ZIP bundle.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from ..auth import require_api_key
from ..geometry.export.bundle import build_export_bundle
from ..geometry.validation import validate_config
from ..models import ExportRequest

router = APIRouter(prefix="/export", tags=["export"])


@router.post("", dependencies=[Depends(require_api_key)])
async def export(request: ExportRequest) -> Response:
    """Run the geometry pipeline and return a ZIP export bundle."""
    config = request.config

    config_issues = validate_config(config)
    errors = [i for i in config_issues if i.level == "error"]
    if errors:
        msgs = "; ".join(i.message for i in errors)
        raise HTTPException(status_code=422, detail=f"Config error: {msgs}")

    try:
        zip_bytes, filename = build_export_bundle(config)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(zip_bytes)),
        },
    )
