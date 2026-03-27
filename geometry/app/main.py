"""
CarvAcoustic Geometry Service
FastAPI application entry point.

Milestone A: scaffolding only — all routers are stubs.
Milestone B: implement generate + validate.
Milestone C: implement layout + export.
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import generate, validate, layout, export

app = FastAPI(
    title="CarvAcoustic Geometry Service",
    version="0.1.0",
    description=(
        "Stateless geometry generation service for CarvAcoustic. "
        "Receives canonical config objects, returns geometry artifacts. "
        "No G-code. No acoustic calculations."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — always include localhost for dev; add production URL via env var.
# Fly.io: fly secrets set ALLOWED_ORIGIN=https://carvacoustic.com
_allowed_origins = [
    "http://localhost:3000",
    "http://localhost:3001",
]
_production_url = os.getenv("ALLOWED_ORIGIN")
if _production_url:
    _allowed_origins.append(_production_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(generate.router)
app.include_router(validate.router)
app.include_router(layout.router)
app.include_router(export.router)


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "carvacoustic-geometry", "version": "0.1.0"}
