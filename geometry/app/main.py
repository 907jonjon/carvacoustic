"""
CarvAcoustic Geometry Service
FastAPI application entry point.

Milestone A: scaffolding only — all routers are stubs.
Milestone B: implement generate + validate.
Milestone C: implement layout + export.
"""

import os

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .routers import generate, validate, layout, export, preview

_environment = os.getenv("ENVIRONMENT", "development")
_is_production = _environment == "production"

app = FastAPI(
    title="CarvAcoustic Geometry Service",
    version="0.1.0",
    description=(
        "Stateless geometry generation service for CarvAcoustic. "
        "Receives canonical config objects, returns geometry artifacts. "
        "No G-code. No acoustic calculations."
    ),
    docs_url=None if _is_production else "/docs",
    redoc_url=None if _is_production else "/redoc",
)

# CORS — only include localhost origins when ALLOWED_ORIGIN is not set.
_production_url = os.getenv("ALLOWED_ORIGIN")
_allowed_origins: list[str] = []
if _production_url:
    _allowed_origins.append(_production_url)
else:
    _allowed_origins.extend([
        "http://localhost:3000",
        "http://localhost:3001",
    ])

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-Key", "Authorization"],
)


# Body size limit middleware (1 MB)
MAX_BODY_SIZE = 1_048_576


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_BODY_SIZE:
            return JSONResponse(
                status_code=413, content={"detail": "Request body too large"}
            )
        return await call_next(request)


app.add_middleware(BodySizeLimitMiddleware)


# Security headers middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


app.add_middleware(SecurityHeadersMiddleware)

app.include_router(generate.router)
app.include_router(validate.router)
app.include_router(layout.router)
app.include_router(export.router)
app.include_router(preview.router)


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "carvacoustic-geometry", "version": "0.1.0"}


@app.get("/nesting-health", tags=["system"])
async def nesting_health() -> dict:
    """
    Diagnostic endpoint: test that the nesting engine import chain works
    and can run a trivial placement. Returns error details if anything fails.
    """
    result: dict = {"imports": {}, "test_run": None}

    # Test each import in the chain
    imports_to_test = [
        ("shapely", "import shapely; shapely.__version__"),
        ("shapely.STRtree", "from shapely import STRtree"),
        ("nesting.models", "from app.nesting.models import NestJob, PartSpec, TransformSpec, VariantGeom, SheetSpec"),
        ("nesting.geometry.flatten", "from app.nesting.geometry.flatten import simplify_polygon"),
        ("nesting.geometry.normalize", "from app.nesting.geometry.normalize import normalize_polygon"),
        ("nesting.geometry.offsets", "from app.nesting.geometry.offsets import inflate_part, contract_sheet"),
        ("nesting.geometry.transforms", "from app.nesting.geometry.transforms import enumerate_transforms, apply_transform"),
        ("nesting.geometry.preferred_edges", "from app.nesting.geometry.preferred_edges import detect_preferred_edges"),
        ("nesting.geometry.collision", "from app.nesting.geometry.collision import check_collision, check_inside_sheet"),
        ("nesting.geometry.spatial_hash", "from app.nesting.geometry.spatial_hash import SpatialIndex"),
        ("nesting.geometry.sheet", "from app.nesting.geometry.sheet import SheetState"),
        ("nesting.geometry.validate", "from app.nesting.geometry.validate import validate_solution"),
        ("nesting.search.ordering", "from app.nesting.search.ordering import generate_orderings"),
        ("nesting.search.candidates", "from app.nesting.search.candidates import generate_candidates"),
        ("nesting.search.scoring", "from app.nesting.search.scoring import score_candidate"),
        ("nesting.search.constructive", "from app.nesting.search.constructive import constructive_solve"),
        ("nesting.search.improve", "from app.nesting.search.improve import compact"),
        ("nesting.search.modes", "from app.nesting.search.modes import MODES"),
        ("nesting.solver.solve", "from app.nesting.solver.solve import solve_nest"),
        ("nesting.ingest", "from app.nesting.ingest import prepare_nest_job, run_nesting"),
    ]

    all_ok = True
    for name, code in imports_to_test:
        try:
            exec(code)
            result["imports"][name] = "ok"
        except Exception as e:
            result["imports"][name] = f"FAIL: {type(e).__name__}: {e}"
            all_ok = False

    # Try a minimal test run
    if all_ok:
        try:
            from shapely.geometry import box as shapely_box
            from app.nesting.ingest import prepare_nest_job
            from app.nesting.solver.solve import solve_nest

            test_poly = shapely_box(0, 0, 5, 20)
            test_parts = [{
                "part_id": "TEST_001",
                "part_type": "slat",
                "polygon": test_poly,
                "bounding_box": test_poly.bounds,
                "area": test_poly.area,
            }]

            # Minimal config-like object
            class _Obj:
                def __init__(self, **kw):
                    for k, v in kw.items():
                        setattr(self, k, v)

            class _RotMode:
                value = "90_only"

            test_config = _Obj(
                fabrication=_Obj(
                    material=_Obj(sheet_width=48, sheet_height=96, thickness=0.75, grain_direction=None),
                    tool=_Obj(clearance=0.25, border_gap=1.0, tool_diameter=0.25),
                ),
                layout=_Obj(rotation_mode=_RotMode(), preserve_grain=False, copies=1),
            )

            job = prepare_nest_job(test_parts, test_config, mode="fast")
            nest_result = solve_nest(job, mode="fast")
            result["test_run"] = {
                "status": "ok",
                "sheets_used": nest_result.sheets_used,
                "utilization": round(nest_result.utilization, 3),
                "placed": len(nest_result.placements),
                "elapsed_ms": round(nest_result.elapsed_ms, 1),
            }
        except Exception as e:
            import traceback
            result["test_run"] = {
                "status": "FAIL",
                "error": f"{type(e).__name__}: {e}",
                "traceback": traceback.format_exc(),
            }

    result["overall"] = "ok" if all_ok and result.get("test_run", {}).get("status") == "ok" else "FAIL"
    return result
