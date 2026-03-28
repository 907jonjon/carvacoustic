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

from .routers import generate, validate, layout, export

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


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "carvacoustic-geometry", "version": "0.1.0"}
