"""
Validation engine — v2 slat-based pipeline.

Two entry points:
  validate_config(config)            — config-level checks before generation
  validate_geometry_v2(parts, config) — geometry-level checks after generation
"""

from __future__ import annotations

from shapely.geometry import Polygon

from ..models import CanonicalConfig, ValidationIssue


# ─────────────────────────────────────────────────────────────────────────────
# Config-level validators
# ─────────────────────────────────────────────────────────────────────────────

def validate_config(config: CanonicalConfig) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    slats = config.slats
    surface = config.surface
    fab = config.fabrication
    tool = fab.tool
    mat = fab.material
    boundary = config.boundary

    # ── Errors ────────────────────────────────────────────────────────────────

    # Boundary: safe_margin must leave usable area
    margin_ratio = (
        boundary.safe_margin * 2.0
        / min(boundary.width, boundary.height)
    )
    if margin_ratio > 0.9:
        issues.append(ValidationIssue(
            level="error",
            code="invalid_boundary",
            message=(
                f"safe_margin ({boundary.safe_margin:.4f}) consumes more than 90% "
                "of the smaller boundary dimension. No usable area remains."
            ),
            field="boundary.safe_margin",
        ))

    # Slat width vs sheet width
    slat_width = boundary.width
    usable_sheet_w = mat.sheet_width - 2.0 * tool.border_gap
    if slat_width > usable_sheet_w:
        issues.append(ValidationIssue(
            level="error",
            code="part_too_wide",
            message=(
                f"Slat width ({slat_width:.3f}) exceeds usable sheet width "
                f"({usable_sheet_w:.3f}). Reduce boundary width or border_gap."
            ),
            field="boundary.width",
        ))

    # Tab width must be cuttable
    if slats.tab_width < tool.tool_diameter:
        issues.append(ValidationIssue(
            level="error",
            code="feature_below_minimum",
            message=(
                f"tab_width ({slats.tab_width:.4f}) is smaller than "
                f"tool_diameter ({tool.tool_diameter:.4f}). Cannot cut tabs."
            ),
            field="slats.tab_width",
        ))

    # ── Warnings ──────────────────────────────────────────────────────────────

    # High slat count
    if slats.count > 80:
        issues.append(ValidationIssue(
            level="warning",
            code="high_part_count",
            message=(
                f"Slat count ({slats.count}) is high. "
                "Verify sheet count and assembly time."
            ),
            field="slats.count",
        ))

    # Slat spacing smaller than thickness (slats would overlap)
    if slats.spacing < slats.thickness:
        issues.append(ValidationIssue(
            level="warning",
            code="thin_bridge",
            message=(
                f"Slat spacing ({slats.spacing:.3f}) is less than slat thickness "
                f"({slats.thickness:.3f}). Slats may not fit on backing board."
            ),
            field="slats.spacing",
        ))

    # Dogbone info
    if tool.dogbone_style.value == "none":
        issues.append(ValidationIssue(
            level="info",
            code="dogbones_not_applied",
            message=(
                "Dogbone relief is not applied (dogbone_style='none'). "
                "Inside corners at tab roots may not clear fully."
            ),
        ))

    return issues


# ─────────────────────────────────────────────────────────────────────────────
# Geometry-level validators (run after generation)
# ─────────────────────────────────────────────────────────────────────────────

def validate_geometry_v2(
    parts: list[dict],
    config: CanonicalConfig,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    fab = config.fabrication
    tool = fab.tool
    mat = fab.material

    if not parts:
        issues.append(ValidationIssue(
            level="error",
            code="invalid_boundary",
            message="Pipeline produced no parts. Check slat count and boundary dimensions.",
        ))
        return issues

    for part in parts:
        poly: Polygon = part["polygon"]

        # Invalid geometry
        if not poly.is_valid:
            issues.append(ValidationIssue(
                level="error",
                code="open_cut_geometry",
                message=f"Part {part['part_id']} has invalid geometry.",
            ))

        # Self-intersection
        if not poly.is_simple:
            issues.append(ValidationIssue(
                level="error",
                code="self_intersection",
                message=f"Part {part['part_id']} has self-intersecting geometry.",
            ))

        # Thin section
        eroded = poly.buffer(-tool.tool_diameter / 2.0)
        if eroded.is_empty:
            issues.append(ValidationIssue(
                level="warning",
                code="thin_section",
                message=(
                    f"Part {part['part_id']} has sections thinner than "
                    f"tool_diameter ({tool.tool_diameter:.4f})."
                ),
            ))

        # Sheet overflow
        bbox = part["bounding_box"]
        part_w = bbox[2] - bbox[0]
        part_h = bbox[3] - bbox[1]
        usable_w = mat.sheet_width - 2.0 * tool.border_gap
        usable_h = mat.sheet_height - 2.0 * tool.border_gap
        if part_w > usable_w:
            issues.append(ValidationIssue(
                level="error",
                code="sheet_overflow",
                message=(
                    f"Part {part['part_id']} width ({part_w:.2f}) exceeds "
                    f"usable sheet width ({usable_w:.2f})."
                ),
            ))
        if part_h > usable_h:
            issues.append(ValidationIssue(
                level="error",
                code="sheet_overflow",
                message=(
                    f"Part {part['part_id']} height ({part_h:.2f}) exceeds "
                    f"usable sheet height ({usable_h:.2f})."
                ),
            ))

    # High part count
    if len(parts) > 60:
        issues.append(ValidationIssue(
            level="warning",
            code="high_part_count",
            message=f"Design has {len(parts)} parts — verify sheet count and material usage.",
        ))

    # Backing board info
    if any(p["part_type"] == "backing" for p in parts):
        issues.append(ValidationIssue(
            level="info",
            code="backing_included",
            message="Backing board with slots included in export.",
        ))

    return issues


# ─────────────────────────────────────────────────────────────────────────────
# Legacy stub — kept so old import paths don't break during test skip
# ─────────────────────────────────────────────────────────────────────────────

def validate_geometry(
    bands: list,
    boundary_poly: object,
    safe_poly: object,
    config: CanonicalConfig,
) -> list[ValidationIssue]:
    """Legacy v1 geometry validator — no longer called by the main pipeline."""
    return []
