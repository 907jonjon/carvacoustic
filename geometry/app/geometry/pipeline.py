"""
Geometry pipeline (v2) — height-field → slat-profile flow.

Steps:
  1. Generate height field from surface config
  2. Generate slat profiles (2D cut polygons)
  3. Generate backing board (if enabled)
  4. Place labels
  5. Run validation
  6. Build SVG preview (2D layout of all slat profiles)
"""

from __future__ import annotations

from datetime import datetime, timezone

from shapely.geometry import Polygon

from ..models import (
    CanonicalConfig,
    GenerateResult,
    ValidationIssue,
    ValidationReport,
)
from .height_field import generate_height_field
from .slat_profiler import generate_backing_board, generate_slat_profiles
from .validation import validate_config, validate_geometry_v2
from .export.svg_export import generate_slat_preview_svg


def run_pipeline(config: CanonicalConfig) -> GenerateResult:
    """
    Run the full v2 geometry pipeline.
    Returns a GenerateResult with 2D SVG preview and validation report.
    """
    issues: list[ValidationIssue] = []

    # ── Step 1: Config-level validation ──────────────────────────────────────
    config_issues = validate_config(config)
    issues.extend(config_issues)

    if _has_errors(config_issues):
        return _error_result(
            "Config validation failed. Fix errors before generating.",
            issues,
        )

    # ── Step 2: Generate height field ─────────────────────────────────────────
    x_vals, heights = generate_height_field(
        surface=config.surface,
        width=config.boundary.width,
        slat_count=config.slats.count,
    )

    # ── Step 3: Generate slat profiles ────────────────────────────────────────
    slat_parts = generate_slat_profiles(
        x_vals=x_vals,
        heights=heights,
        slat_config=config.slats,
        fab_config=config.fabrication,
    )

    # ── Step 4: Generate backing board ────────────────────────────────────────
    backing_part = generate_backing_board(
        backing_config=config.backing,
        slat_config=config.slats,
        n_slats=config.slats.count,
    )

    all_parts = list(slat_parts)
    if backing_part:
        all_parts.append(backing_part)

    # ── Step 5: Place labels ──────────────────────────────────────────────────
    if config.labeling.enabled:
        for part in all_parts:
            centroid = part["polygon"].centroid
            part["label"] = {
                "text": part["part_id"],
                "x": float(centroid.x),
                "y": float(centroid.y),
            }

    # ── Step 6: Geometry validation ───────────────────────────────────────────
    geom_issues = validate_geometry_v2(all_parts, config)
    issues.extend(geom_issues)

    # ── Step 7: SVG preview ───────────────────────────────────────────────────
    svg_preview = generate_slat_preview_svg(slat_parts, backing_part, config)

    valid = not _has_errors(issues)
    status = "ok" if valid else "error"

    return GenerateResult(
        status=status,
        message="" if valid else "Generation completed with errors. See validation report.",
        validation=ValidationReport(valid=valid, issues=issues),
        svg_preview=svg_preview,
        part_count=len(all_parts),
        slat_count=len(slat_parts),
        has_backing=backing_part is not None,
        generated_at=_now(),
    )


def run_pipeline_internal(config: CanonicalConfig) -> dict:
    """
    Run geometry pipeline and return raw parts (including Shapely polygons).
    Used by export router and bundle assembler.

    Returns dict with:
      parts       — list of part dicts (polygon, part_id, etc.)
      slat_parts  — slat parts only
      backing     — backing board dict or None
      x_vals      — 1D array
      heights     — 2D array
      issues      — list[ValidationIssue]
    """
    config_issues = validate_config(config)
    if _has_errors(config_issues):
        return {"parts": [], "slat_parts": [], "backing": None,
                "issues": config_issues, "x_vals": None, "heights": None}

    x_vals, heights = generate_height_field(
        surface=config.surface,
        width=config.boundary.width,
        slat_count=config.slats.count,
    )
    slat_parts = generate_slat_profiles(x_vals, heights, config.slats, config.fabrication)
    backing_part = generate_backing_board(config.backing, config.slats, config.slats.count)

    all_parts = list(slat_parts)
    if backing_part:
        all_parts.append(backing_part)

    if config.labeling.enabled:
        for part in all_parts:
            centroid = part["polygon"].centroid
            part["label"] = {
                "text": part["part_id"],
                "x": float(centroid.x),
                "y": float(centroid.y),
            }

    geom_issues = validate_geometry_v2(all_parts, config)

    return {
        "parts": all_parts,
        "slat_parts": slat_parts,
        "backing": backing_part,
        "x_vals": x_vals,
        "heights": heights,
        "issues": config_issues + geom_issues,
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _has_errors(issues: list[ValidationIssue]) -> bool:
    return any(i.level == "error" for i in issues)


def _error_result(message: str, issues: list[ValidationIssue]) -> GenerateResult:
    return GenerateResult(
        status="error",
        message=message,
        validation=ValidationReport(valid=False, issues=issues),
        svg_preview="",
        part_count=0,
        generated_at=_now(),
    )


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── Kept for import compatibility with old tests (will be skipped) ────────────

def _place_labels(boundary_poly: Polygon, config: CanonicalConfig) -> list[dict]:
    return []


def _collect_polygons(geom: object) -> list[Polygon]:
    result: list[Polygon] = []
    if isinstance(geom, Polygon):
        if not geom.is_empty and geom.area > 1e-12:
            result.append(geom)
    elif hasattr(geom, "geoms"):
        for g in geom.geoms:
            result.extend(_collect_polygons(g))
    return result
