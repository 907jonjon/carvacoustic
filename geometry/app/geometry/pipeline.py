"""
Geometry pipeline — orchestrates all Milestone B steps.

Steps (spec 02-geometry-spec.md):
  1.  Normalize boundary
  2.  Apply safe margin
  3.  Generate raw pattern guides
  4.  Clip guides to boundary        ← done inside pattern generators
  5.  Convert guides to cut geometry ← done inside pattern generators
  6.  Merge and clean geometry
  7.  Place labels
  8.  Generate parts list
  9.  Run validation
  10. Layout to sheets               ← Milestone C
  11. Assemble export-ready artifacts ← called separately via /export
"""

from __future__ import annotations

from datetime import datetime, timezone

from shapely.geometry import Polygon
from shapely.ops import unary_union

from ..models import (
    CanonicalConfig,
    GenerateResult,
    ValidationIssue,
    ValidationReport,
)
from .boundary import build_boundary_polygon, compute_safe_boundary, normalize_boundary
from .patterns.wave_field import generate_wave_field
from .validation import validate_config, validate_geometry
from .export.svg_export import generate_preview_svg


def run_pipeline(config: CanonicalConfig) -> GenerateResult:
    """
    Run the full Milestone-B geometry pipeline.
    Returns a GenerateResult with SVG preview and validation report.
    """
    issues: list[ValidationIssue] = []

    # ── Step 1: Build & normalize boundary ───────────────────────────────────
    try:
        raw_poly = build_boundary_polygon(config.boundary)
    except ValueError as exc:
        return _error_result(str(exc), [
            ValidationIssue(
                level="error",
                code="invalid_boundary",
                message=str(exc),
            )
        ])

    boundary_poly, boundary_issues = normalize_boundary(raw_poly)
    issues.extend(boundary_issues)

    if _has_errors(issues):
        return _error_result("Boundary normalization failed.", issues)

    # ── Step 2: Apply safe margin ─────────────────────────────────────────────
    safe_poly = compute_safe_boundary(boundary_poly, config.boundary.safe_margin)

    # ── Step 3 & 9a: Config-level validation ──────────────────────────────────
    config_issues = validate_config(config)
    issues.extend(config_issues)

    if _has_errors(config_issues):
        # Still return an SVG showing just the boundary
        svg = generate_preview_svg(boundary_poly, safe_poly, [], [])
        return GenerateResult(
            status="error",
            message="Config validation failed. Fix errors before generating.",
            validation=ValidationReport(valid=False, issues=issues),
            svg_preview=svg,
            part_count=0,
            generated_at=_now(),
        )

    # ── Steps 3–5: Generate pattern ───────────────────────────────────────────
    family = config.pattern.family.value

    if family == "wave_field":
        bands = generate_wave_field(safe_poly, config.pattern, config.fabrication)
    else:
        return _error_result(
            f"Pattern family '{family}' is not yet implemented (Milestone C).",
            issues + [
                ValidationIssue(
                    level="error",
                    code="not_implemented",
                    message=f"Pattern family '{family}' not yet implemented.",
                )
            ],
        )

    # ── Step 6: Merge and clean (dissolve overlapping bands) ─────────────────
    if bands:
        merged = unary_union(bands)
        bands = _collect_polygons(merged)

    # ── Step 7: Place labels ──────────────────────────────────────────────────
    labels = _place_labels(boundary_poly, config)

    # ── Step 8: Parts list ────────────────────────────────────────────────────
    part_count = len(bands)

    # ── Step 9b: Geometry-level validation ────────────────────────────────────
    geom_issues = validate_geometry(bands, boundary_poly, safe_poly, config)
    issues.extend(geom_issues)

    # ── Build SVG preview ─────────────────────────────────────────────────────
    svg_preview = generate_preview_svg(boundary_poly, safe_poly, bands, labels)

    valid = not _has_errors(issues)
    status = "ok" if valid else "error"

    return GenerateResult(
        status=status,
        message="" if valid else "Generation completed with errors. See validation report.",
        validation=ValidationReport(valid=valid, issues=issues),
        svg_preview=svg_preview,
        part_count=part_count,
        generated_at=_now(),
    )


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


def _place_labels(boundary_poly: Polygon, config: CanonicalConfig) -> list[dict]:
    """
    Place a single label per the labeling config.
    Position: footer = bottom centre, header = top centre, center = centroid.
    Labels are on ENGRAVE_LABEL layer — separate from cut geometry.
    """
    if not config.labeling.enabled:
        return []

    minx, miny, maxx, maxy = boundary_poly.bounds
    cx = (minx + maxx) / 2.0
    w = maxx - minx
    h = maxy - miny
    label_height = min(w, h) * 0.025

    pos = config.labeling.position.value
    if pos == "footer":
        lx, ly = cx, miny + label_height
    elif pos == "header":
        lx, ly = cx, maxy - label_height
    else:  # center
        lx, ly = boundary_poly.centroid.x, boundary_poly.centroid.y

    text = f"{config.labeling.prefix}1"

    return [{"text": text, "x": lx, "y": ly, "height": label_height}]


def _collect_polygons(geom: object) -> list[Polygon]:
    """Flatten any Shapely geometry into a list of Polygons."""
    result: list[Polygon] = []
    if isinstance(geom, Polygon):
        if not geom.is_empty and geom.area > 1e-12:
            result.append(geom)
    elif hasattr(geom, "geoms"):
        for g in geom.geoms:
            result.extend(_collect_polygons(g))
    return result
