"""
Validation engine — all phase-1 validation rules from spec 02-geometry-spec.md.

Two entry points:
  validate_config(config)         — config-level checks before generation
  validate_geometry(...)          — geometry-level checks after generation

Returns lists of ValidationIssue.  level='error' blocks export.
"""

from __future__ import annotations

from shapely.geometry import Polygon

from ..models import CanonicalConfig, ValidationIssue


# ─────────────────────────────────────────────────────────────────────────────
# Config-level validators (run before geometry generation)
# ─────────────────────────────────────────────────────────────────────────────

def validate_config(config: CanonicalConfig) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    pat = config.pattern
    mat = config.fabrication.material
    tool = config.fabrication.tool

    # ── Errors ────────────────────────────────────────────────────────────────

    # Feature below minimum: line_width must be ≥ tool_diameter
    if pat.line_width < tool.tool_diameter:
        issues.append(ValidationIssue(
            level="error",
            code="feature_below_minimum",
            message=(
                f"Pattern line_width ({pat.line_width:.4f}) is smaller than "
                f"tool_diameter ({tool.tool_diameter:.4f}). "
                "The tool cannot cut this feature."
            ),
            field="pattern.line_width",
        ))

    # Impossible inside radius: wave bands have curved edges; the sharpest inside
    # radius is approximately line_width / 2.  Warn if tool cannot clear it.
    tightest_radius = pat.line_width / 2.0
    if tightest_radius < tool.min_inside_radius:
        issues.append(ValidationIssue(
            level="error",
            code="impossible_inside_radius",
            message=(
                f"Tightest inside radius ({tightest_radius:.4f}) is less than "
                f"min_inside_radius ({tool.min_inside_radius:.4f}). "
                "Reduce line_width or increase min_inside_radius."
            ),
            field="pattern.line_width",
        ))

    # Boundary: safe_margin must leave usable area
    # (hard error is caught in boundary.py; warn here if margin is very large)
    margin_ratio = (
        config.boundary.safe_margin * 2.0
        / min(config.boundary.width, config.boundary.height)
    )
    if margin_ratio > 0.9:
        issues.append(ValidationIssue(
            level="error",
            code="invalid_boundary",
            message=(
                f"safe_margin ({config.boundary.safe_margin:.4f}) consumes "
                "more than 90% of the smaller boundary dimension. "
                "No usable area remains."
            ),
            field="boundary.safe_margin",
        ))

    # ── Warnings ──────────────────────────────────────────────────────────────

    # Thin bridge: gap between wave bands
    bridge = pat.spacing - pat.line_width
    if bridge <= 0:
        issues.append(ValidationIssue(
            level="error",
            code="thin_bridge",
            message=(
                f"spacing ({pat.spacing:.4f}) ≤ line_width ({pat.line_width:.4f}). "
                "Bands overlap — no material bridge remains between cuts."
            ),
            field="pattern.spacing",
        ))
    elif bridge < mat.min_bridge:
        issues.append(ValidationIssue(
            level="warning",
            code="thin_bridge",
            message=(
                f"Bridge width ({bridge:.4f}) is less than min_bridge "
                f"({mat.min_bridge:.4f}). Part may be fragile."
            ),
            field="pattern.spacing",
        ))

    # Wave amplitude exceeds safe margin — waves may touch boundary edge
    if pat.amplitude > config.boundary.safe_margin > 0:
        issues.append(ValidationIssue(
            level="warning",
            code="amplitude_exceeds_margin",
            message=(
                f"Wave amplitude ({pat.amplitude:.4f}) exceeds safe_margin "
                f"({config.boundary.safe_margin:.4f}). "
                "Some wave peaks will be clipped at the safe boundary."
            ),
            field="pattern.amplitude",
        ))

    # ── Info ──────────────────────────────────────────────────────────────────

    # Dogbones not applied
    if tool.dogbone_style.value == "none":
        issues.append(ValidationIssue(
            level="info",
            code="dogbones_not_applied",
            message=(
                "Dogbone relief is not applied (dogbone_style='none'). "
                "Inside corners may not be fully cleared by the tool. "
                "Acceptable for purely decorative surface panels."
            ),
        ))

    return issues


# ─────────────────────────────────────────────────────────────────────────────
# Geometry-level validators (run after generation)
# ─────────────────────────────────────────────────────────────────────────────

def validate_geometry(
    bands: list[Polygon],
    boundary_poly: Polygon,
    safe_poly: Polygon,
    config: CanonicalConfig,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    tool = config.fabrication.tool
    mat = config.fabrication.material

    if not bands:
        issues.append(ValidationIssue(
            level="error",
            code="invalid_boundary",
            message=(
                "Pattern generation produced no cut geometry. "
                "Check boundary dimensions, safe_margin, spacing, and amplitude."
            ),
        ))
        return issues

    # ── Errors ────────────────────────────────────────────────────────────────

    # Open cut geometry — all wave bands should be closed polygons
    open_count = sum(1 for b in bands if not b.exterior.is_closed)
    if open_count:
        issues.append(ValidationIssue(
            level="error",
            code="open_cut_geometry",
            message=f"{open_count} cut feature(s) have open geometry.",
        ))

    # Duplicate part check — bands are derived, so check for identical bounding boxes
    bboxes = [b.bounds for b in bands]
    if len(bboxes) != len(set(bboxes)):
        issues.append(ValidationIssue(
            level="error",
            code="duplicate_part_id",
            message="Duplicate cut features detected. Check pattern seed and symmetry.",
        ))

    # ── Warnings ──────────────────────────────────────────────────────────────

    # High part count
    if len(bands) > 200:
        issues.append(ValidationIssue(
            level="warning",
            code="high_part_count",
            message=(
                f"Pattern produced {len(bands)} cut features. "
                "This may significantly increase machining time."
            ),
        ))

    # Very small parts (area < tool_diameter²)
    min_area = tool.tool_diameter ** 2
    small = [b for b in bands if b.area < min_area]
    if small:
        issues.append(ValidationIssue(
            level="warning",
            code="very_small_part",
            message=(
                f"{len(small)} cut feature(s) have area smaller than "
                f"tool_diameter² ({min_area:.5f}). These may not cut cleanly."
            ),
        ))

    # Low material utilization
    cut_area = sum(b.area for b in bands)
    boundary_area = boundary_poly.area
    utilization = cut_area / boundary_area if boundary_area > 0 else 0
    if utilization < 0.05:
        issues.append(ValidationIssue(
            level="warning",
            code="low_material_utilization",
            message=(
                f"Cut area is only {utilization:.1%} of panel area. "
                "Consider increasing density or reducing spacing."
            ),
        ))

    return issues
