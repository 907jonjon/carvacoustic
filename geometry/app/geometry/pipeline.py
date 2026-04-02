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
from typing import Callable

from shapely.geometry import Polygon

from ..models import (
    CanonicalConfig,
    GenerateResult,
    PartGeometry,
    PreviewResult,
    ValidationIssue,
    ValidationReport,
    normalize_config,
)
from .height_field import generate_height_field
from .slat_profiler import generate_backing_board, generate_slat_profiles
from .validation import validate_config, validate_geometry_v2
from .export.svg_export import generate_slat_preview_svg, generate_cut_preview_svg
from .layout import run_slat_layout
from ..nesting.ingest import run_nesting

ProgressCallback = Callable[[int, int, str], None]


def run_pipeline(
    config: CanonicalConfig,
    on_progress: ProgressCallback | None = None,
) -> GenerateResult:
    """
    Run the full v2 geometry pipeline.
    Returns a GenerateResult with 2D SVG preview and validation report.
    """
    config = normalize_config(config)
    issues: list[ValidationIssue] = []

    def _progress(step: int, name: str) -> None:
        if on_progress:
            on_progress(step, 10, name)

    # ── Step 1: Config-level validation ──────────────────────────────────────
    _progress(1, "Validating configuration")
    config_issues = validate_config(config)
    issues.extend(config_issues)

    if _has_errors(config_issues):
        return _error_result(
            "Config validation failed. Fix errors before generating.",
            issues,
        )

    # ── Step 2: Generate height field ─────────────────────────────────────────
    _progress(2, "Generating height field")
    x_vals, heights = generate_height_field(
        surface=config.surface,
        width=config.boundary.width,
        slat_count=config.slats.count,
    )

    # ── Step 3: Generate slat profiles ────────────────────────────────────────
    _progress(3, "Generating slat profiles")
    slat_parts = generate_slat_profiles(
        x_vals=x_vals,
        heights=heights,
        slat_config=config.slats,
        fab_config=config.fabrication,
    )

    # ── Step 4: Generate backing board ────────────────────────────────────────
    _progress(4, "Generating backing board")
    backing_part = generate_backing_board(
        backing_config=config.backing,
        slat_config=config.slats,
        n_slats=config.slats.count,
    )

    all_parts = list(slat_parts)
    if backing_part:
        all_parts.append(backing_part)

    # ── Step 5: Place labels ──────────────────────────────────────────────────
    _progress(5, "Placing labels")
    if config.labeling.enabled:
        for part in all_parts:
            centroid = part["polygon"].centroid
            part["label"] = {
                "text": part["part_id"],
                "x": float(centroid.x),
                "y": float(centroid.y),
            }

    # ── Serialize full polygons for 3D rendering ────────────────────────────
    part_geometries: list[PartGeometry] = []
    for part in all_parts:
        poly = part["polygon"]
        part_geometries.append(PartGeometry(
            part_id=part["part_id"],
            part_type=part["part_type"],
            exterior=[[float(x), float(y)] for x, y in poly.exterior.coords],
            holes=[
                [[float(x), float(y)] for x, y in ring.coords]
                for ring in poly.interiors
            ],
            bounding_box=[float(v) for v in poly.bounds],
        ))

    # ── Step 6: Geometry validation ───────────────────────────────────────────
    _progress(6, "Validating geometry")
    geom_issues = validate_geometry_v2(all_parts, config)
    issues.extend(geom_issues)

    # ── Step 7: SVG preview ───────────────────────────────────────────────────
    _progress(7, "Generating design preview")
    svg_preview = generate_slat_preview_svg(slat_parts, backing_part, config)

    # ── Step 8: Cut preview (layout on material sheets) ────────────────────
    nesting_mode = config.layout.nesting_mode.value if hasattr(config.layout, "nesting_mode") else "balanced"
    nest_backing = getattr(config.layout, "nest_backing", True)
    parts_to_nest = all_parts if nest_backing else list(slat_parts)

    # Sub-progress: nesting runs from 65% to 90%, then SVG gen to 95%
    _progress(8, f"Nesting parts on sheets ({nesting_mode})")

    def _nesting_progress(seed_idx: int, total_seeds: int) -> None:
        pct = 65 + int(25 * seed_idx / max(total_seeds, 1))
        if on_progress:
            on_progress(8, 10, f"Nesting: seed {seed_idx + 1} of {total_seeds}")

    if nesting_mode == "ffd":
        layout_result = run_slat_layout(parts_to_nest, config)
        layout_result.engine = "ffd"  # type: ignore[attr-defined]
    else:
        layout_result = run_nesting(parts_to_nest, config, mode=nesting_mode, on_progress=_nesting_progress)

    _progress(9, "Generating cut preview")
    backing_for_svg = backing_part if nest_backing else None
    cut_preview_svg = generate_cut_preview_svg(slat_parts, backing_for_svg, layout_result, config)
    sheet_count = len(layout_result.sheets) if layout_result else 0
    sheet_utilization = (
        sum(s.utilization for s in layout_result.sheets) / len(layout_result.sheets)
        if layout_result and layout_result.sheets
        else 0.0
    )

    _progress(10, "Finalizing")
    valid = not _has_errors(issues)
    status = "ok" if valid else "error"

    # Which layout engine produced the result?
    layout_engine = getattr(layout_result, "engine", "ffd")

    return GenerateResult(
        status=status,
        message="" if valid else "Generation completed with errors. See validation report.",
        validation=ValidationReport(valid=valid, issues=issues),
        svg_preview=svg_preview,
        part_count=len(all_parts),
        slat_count=len(slat_parts),
        has_backing=backing_part is not None,
        cut_preview_svg=cut_preview_svg,
        sheet_count=sheet_count,
        sheet_utilization=sheet_utilization,
        layout_engine=layout_engine,
        part_geometries=part_geometries,
        generated_at=_now(),
    )


def run_preview_pipeline(config: CanonicalConfig) -> PreviewResult:
    """
    Lightweight preview pipeline — geometry only, no nesting or SVG.
    Returns part_geometries for 3D rendering.
    """
    config = normalize_config(config)

    config_issues = validate_config(config)
    if _has_errors(config_issues):
        return PreviewResult(
            status="error",
            message="Config validation failed. " + "; ".join(i.message for i in config_issues if i.level == "error"),
        )

    x_vals, heights = generate_height_field(
        surface=config.surface,
        width=config.boundary.width,
        slat_count=config.slats.count,
    )

    slat_parts = generate_slat_profiles(
        x_vals=x_vals,
        heights=heights,
        slat_config=config.slats,
        fab_config=config.fabrication,
    )

    backing_part = generate_backing_board(
        backing_config=config.backing,
        slat_config=config.slats,
        n_slats=config.slats.count,
    )

    all_parts = list(slat_parts)
    if backing_part:
        all_parts.append(backing_part)

    part_geometries: list[PartGeometry] = []
    for part in all_parts:
        poly = part["polygon"]
        part_geometries.append(PartGeometry(
            part_id=part["part_id"],
            part_type=part["part_type"],
            exterior=[[float(x), float(y)] for x, y in poly.exterior.coords],
            holes=[
                [[float(x), float(y)] for x, y in ring.coords]
                for ring in poly.interiors
            ],
            bounding_box=[float(v) for v in poly.bounds],
        ))

    return PreviewResult(
        status="ok",
        part_geometries=part_geometries,
        part_count=len(all_parts),
        slat_count=len(slat_parts),
        has_backing=backing_part is not None,
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
    config = normalize_config(config)
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
