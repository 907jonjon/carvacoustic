"""
Tests for nesting engine Phase 1 — geometry foundation.

16 test cases covering simplification, normalization, offsets, transforms,
collision, spatial index, preferred edges, and validation.
"""

from __future__ import annotations

import math

import pytest
from shapely.geometry import Polygon, box
from shapely.geometry.polygon import orient
from shapely.prepared import prep

from app.nesting.geometry.collision import check_collision, check_inside_sheet
from app.nesting.geometry.flatten import simplify_polygon
from app.nesting.geometry.normalize import normalize_polygon
from app.nesting.geometry.offsets import contract_sheet, inflate_part
from app.nesting.geometry.preferred_edges import detect_preferred_edges
from app.nesting.geometry.sheet import SheetState
from app.nesting.geometry.spatial_hash import SpatialIndex
from app.nesting.geometry.transforms import apply_transform, enumerate_transforms
from app.nesting.geometry.validate import validate_solution
from app.nesting.models import (
    NestJob,
    NestResult,
    Placement,
    PartSpec,
    SheetSpec,
    TransformSpec,
    VariantGeom,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_layout_config(rotation_mode="none", preserve_grain=False):
    """Minimal mock for ConfigLayout fields used by enumerate_transforms."""

    class _Rotation:
        def __init__(self, v):
            self.value = v

    class _Layout:
        def __init__(self, rm, pg):
            self.rotation_mode = _Rotation(rm)
            self.preserve_grain = pg

    return _Layout(rotation_mode, preserve_grain)


def _slat_like_polygon() -> Polygon:
    """
    A slat-like polygon: wide flat base with a curved top profile.
    Roughly 10 units wide, ~3 units tall, with many vertices on top.
    """
    n = 50
    top_pts = [
        (10.0 * i / (n - 1), 1.5 + 1.5 * math.sin(math.pi * i / (n - 1)))
        for i in range(n)
    ]
    bottom_pts = [(10.0, 0.0), (0.0, 0.0)]
    coords = top_pts + bottom_pts
    return Polygon(coords)


def _simple_rect(w: float = 4.0, h: float = 2.0) -> Polygon:
    return box(0, 0, w, h)


def _make_variant(poly: Polygon, clearance: float = 0.0) -> VariantGeom:
    t = TransformSpec(angle_deg=0, mirrored=False)
    inflated = inflate_part(poly, clearance) if clearance else poly
    return VariantGeom(
        transform=t,
        polygon=poly,
        inflated=inflated,
        prepared_inflated=prep(inflated),
        aabb=inflated.bounds,
        preferred_edges=[],
        area=poly.area,
    )


# ---------------------------------------------------------------------------
# 1. test_simplify_preserves_validity
# ---------------------------------------------------------------------------


def test_simplify_preserves_validity():
    poly = _slat_like_polygon()
    simplified = simplify_polygon(poly, tool_diameter=0.25)
    assert simplified.is_valid
    area_delta = abs(simplified.area - poly.area) / poly.area
    assert area_delta < 0.05, f"Area delta {area_delta:.2%} exceeds 5%"


# ---------------------------------------------------------------------------
# 2. test_normalize_ccw_winding
# ---------------------------------------------------------------------------


def test_normalize_ccw_winding():
    # Create a CW polygon (opposite of expected)
    cw = Polygon([(0, 0), (0, 2), (3, 2), (3, 0)])  # CW
    result = normalize_polygon(cw)
    # CCW exterior should have positive signed area
    ring = result.exterior
    signed = sum(
        (ring.coords[i][0] * ring.coords[i + 1][1]
         - ring.coords[i + 1][0] * ring.coords[i][1])
        for i in range(len(ring.coords) - 1)
    )
    assert signed > 0, "Exterior should be CCW (positive signed area)"


# ---------------------------------------------------------------------------
# 3. test_inflate_clearance
# ---------------------------------------------------------------------------


def test_inflate_clearance():
    rect = _simple_rect(4.0, 2.0)
    clearance = 2.0
    inflated = inflate_part(rect, clearance)
    # Inflated area should be larger
    assert inflated.area > rect.area
    # Bounds should be expanded by clearance/2 = 1.0 on each side
    orig_bounds = rect.bounds
    inf_bounds = inflated.bounds
    for i in range(2):  # minx, miny
        assert inf_bounds[i] < orig_bounds[i] - 0.9  # ~1.0 expansion
    for i in range(2, 4):  # maxx, maxy
        assert inf_bounds[i] > orig_bounds[i] + 0.9


# ---------------------------------------------------------------------------
# 4. test_contract_sheet
# ---------------------------------------------------------------------------


def test_contract_sheet():
    sheet = SheetSpec(width=100.0, height=50.0, edge_margin=5.0, grain_axis=None)
    clearance = 4.0
    contracted = contract_sheet(sheet, clearance)
    # Inset should be edge_margin + clearance/2 = 5 + 2 = 7
    bounds = contracted.bounds
    assert abs(bounds[0] - 7.0) < 1e-10
    assert abs(bounds[1] - 7.0) < 1e-10
    assert abs(bounds[2] - 93.0) < 1e-10
    assert abs(bounds[3] - 43.0) < 1e-10


# ---------------------------------------------------------------------------
# 5. test_enumerate_transforms_none
# ---------------------------------------------------------------------------


def test_enumerate_transforms_none():
    cfg = _make_layout_config(rotation_mode="none")
    transforms = enumerate_transforms(cfg, grain_direction="x")
    assert len(transforms) == 1
    assert transforms[0] == TransformSpec(0.0, False)


# ---------------------------------------------------------------------------
# 6. test_enumerate_transforms_90
# ---------------------------------------------------------------------------


def test_enumerate_transforms_90():
    cfg = _make_layout_config(rotation_mode="90_only")
    transforms = enumerate_transforms(cfg, grain_direction="x")
    assert len(transforms) == 2
    angles = {t.angle_deg for t in transforms}
    assert angles == {0.0, 90.0}


# ---------------------------------------------------------------------------
# 7. test_enumerate_transforms_grain_locked
# ---------------------------------------------------------------------------


def test_enumerate_transforms_grain_locked():
    cfg = _make_layout_config(rotation_mode="any", preserve_grain=True)
    transforms = enumerate_transforms(cfg, grain_direction="x")
    # Only 0 and 180 should survive grain lock
    angles = {t.angle_deg for t in transforms}
    assert angles == {0.0, 180.0}


# ---------------------------------------------------------------------------
# 8. test_apply_transform_rotate
# ---------------------------------------------------------------------------


def test_apply_transform_rotate():
    rect = box(-2, -1, 2, 1)  # centred at origin, 4x2
    t90 = TransformSpec(angle_deg=90.0, mirrored=False)
    rotated = apply_transform(rect, t90)
    # After 90deg CCW rotation, 4x2 becomes ~2x4
    b = rotated.bounds
    width = b[2] - b[0]
    height = b[3] - b[1]
    assert abs(width - 2.0) < 1e-6, f"Expected width ~2, got {width}"
    assert abs(height - 4.0) < 1e-6, f"Expected height ~4, got {height}"


# ---------------------------------------------------------------------------
# 9. test_collision_overlapping
# ---------------------------------------------------------------------------


def test_collision_overlapping():
    placed = box(0, 0, 4, 2)
    candidate = prep(box(0, 0, 4, 2))
    # Place at same position — should collide
    assert check_collision(candidate, 1.0, 0.0, [placed])


# ---------------------------------------------------------------------------
# 10. test_collision_non_overlapping
# ---------------------------------------------------------------------------


def test_collision_non_overlapping():
    placed = box(0, 0, 4, 2)
    candidate = prep(box(0, 0, 4, 2))
    # Place far away — no collision
    assert not check_collision(candidate, 100.0, 100.0, [placed])


# ---------------------------------------------------------------------------
# 11. test_inside_sheet_yes
# ---------------------------------------------------------------------------


def test_inside_sheet_yes():
    sheet_bounds = box(5, 5, 95, 45)
    part = box(0, 0, 4, 2)
    # Place at (10, 10) — well inside
    assert check_inside_sheet(part, 10.0, 10.0, sheet_bounds)


# ---------------------------------------------------------------------------
# 12. test_inside_sheet_no
# ---------------------------------------------------------------------------


def test_inside_sheet_no():
    sheet_bounds = box(5, 5, 95, 45)
    part = box(0, 0, 4, 2)
    # Place at (93, 44) — overflows right/top
    assert not check_inside_sheet(part, 93.0, 44.0, sheet_bounds)


# ---------------------------------------------------------------------------
# 13. test_spatial_index_query
# ---------------------------------------------------------------------------


def test_spatial_index_query():
    idx = SpatialIndex()
    p1 = box(0, 0, 5, 5)
    p2 = box(50, 50, 55, 55)
    idx.add(p1)
    idx.add(p2)

    # Query near p1 — should find p1 but not p2
    candidate = box(3, 3, 8, 8)
    nearby = idx.query_nearby(candidate)
    assert p1 in nearby
    assert p2 not in nearby


# ---------------------------------------------------------------------------
# 14. test_preferred_edge_detection
# ---------------------------------------------------------------------------


def test_preferred_edge_detection():
    slat = _slat_like_polygon()
    edges = detect_preferred_edges(slat, min_length_ratio=0.3)
    # Should find at least the flat base edge (~10 units long)
    assert len(edges) >= 1
    # The longest detected edge should be close to 10 units (the base)
    longest = max(edges, key=lambda e: e["length"])
    assert longest["length"] > 5.0, f"Expected long flat edge, got {longest['length']}"
    assert longest["confidence"] > 0.9, "Base edge should be very straight"


# ---------------------------------------------------------------------------
# 15. test_validate_solution_clean
# ---------------------------------------------------------------------------


def test_validate_solution_clean():
    sheet = SheetSpec(width=100, height=50, edge_margin=5, grain_axis=None)
    clearance = 2.0

    rect = box(-2, -1, 2, 1)  # 4x2 centred
    t = TransformSpec(0, False)
    inflated = inflate_part(rect, clearance)

    variant = VariantGeom(
        transform=t, polygon=rect, inflated=inflated,
        prepared_inflated=prep(inflated),
        aabb=inflated.bounds, preferred_edges=[], area=rect.area,
    )
    part = PartSpec(
        part_id="P1", quantity=1, variants=[variant],
        original_polygon=rect, grain_locked=False, allow_mirror=False,
    )

    # Place at (20, 20) — well inside contracted sheet
    result = NestResult(
        placements=[Placement("P1", 0, t, 20.0, 20.0, "boundary", 1.0)],
        sheets_used=1, utilization=0.1, unplaced=[], warnings=[], elapsed_ms=0,
    )
    job = NestJob(sheets=sheet, parts=[part], clearance=clearance, mode="fast")

    errors = validate_solution(job, result, [part])
    assert errors == [], f"Expected no errors, got: {errors}"


# ---------------------------------------------------------------------------
# 16. test_validate_solution_overlap
# ---------------------------------------------------------------------------


def test_validate_solution_overlap():
    sheet = SheetSpec(width=100, height=50, edge_margin=5, grain_axis=None)
    clearance = 2.0

    rect = box(-2, -1, 2, 1)
    t = TransformSpec(0, False)
    inflated = inflate_part(rect, clearance)

    variant = VariantGeom(
        transform=t, polygon=rect, inflated=inflated,
        prepared_inflated=prep(inflated),
        aabb=inflated.bounds, preferred_edges=[], area=rect.area,
    )
    part_a = PartSpec(
        part_id="PA", quantity=1, variants=[variant],
        original_polygon=rect, grain_locked=False, allow_mirror=False,
    )
    part_b = PartSpec(
        part_id="PB", quantity=1, variants=[variant],
        original_polygon=rect, grain_locked=False, allow_mirror=False,
    )

    # Place both at same position — should overlap
    result = NestResult(
        placements=[
            Placement("PA", 0, t, 20.0, 20.0, "boundary", 1.0),
            Placement("PB", 0, t, 20.0, 20.0, "boundary", 1.0),
        ],
        sheets_used=1, utilization=0.2, unplaced=[], warnings=[], elapsed_ms=0,
    )
    job = NestJob(sheets=sheet, parts=[part_a, part_b], clearance=clearance, mode="fast")

    errors = validate_solution(job, result, [part_a, part_b])
    assert len(errors) > 0, "Should detect overlap"
    assert any("Overlap" in e for e in errors)
