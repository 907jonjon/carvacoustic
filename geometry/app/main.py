"""
CarvAcoustic Geometry Service
FastAPI application entry point.

Milestone A: scaffolding only — all routers are stubs.
Milestone B: implement generate + validate.
Milestone C: implement layout + export.
"""

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

# CORS — web app is the only permitted caller in production.
# Set ALLOWED_ORIGINS in .env for production deployments.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=False,
    allow_methods=["POST", "GET"],
    allow_headers=["X-API-Key", "Content-Type"],
)

app.include_router(generate.router)
app.include_router(validate.router)
app.include_router(layout.router)
app.include_router(export.router)


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "carvacoustic-geometry", "version": "0.1.0"}
