"""
Tests for nesting engine Phase 2 — search: ordering, candidates, scoring.
10 test cases.
"""

from __future__ import annotations

import math

import pytest
from shapely.geometry import Polygon, box
from shapely.prepared import prep

from app.nesting.geometry.offsets import contract_sheet, inflate_part
from app.nesting.geometry.sheet import SheetState
from app.nesting.geometry.spatial_hash import SpatialIndex
from app.nesting.models import (
    NestJob,
    PartSpec,
    SheetSpec,
    SolutionState,
    TransformSpec,
    VariantGeom,
)
from app.nesting.search.candidates import (
    Candidate,
    boundary_anchors,
    filter_feasible,
    generate_candidates,
)
from app.nesting.search.constructive import constructive_solve
from app.nesting.search.ordering import generate_orderings
from app.nesting.search.scoring import ScoringWeights, score_candidate


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_variant(poly: Polygon, clearance: float = 0.5) -> VariantGeom:
    t = TransformSpec(angle_deg=0, mirrored=False)
    inflated = inflate_part(poly, clearance)
    return VariantGeom(
        transform=t,
        polygon=poly,
        inflated=inflated,
        prepared_inflated=prep(inflated),
        aabb=inflated.bounds,
        preferred_edges=[],
        area=poly.area,
    )


def _make_part(part_id: str, w: float, h: float, clearance: float = 0.5) -> PartSpec:
    poly = box(-w / 2, -h / 2, w / 2, h / 2)
    variant = _make_variant(poly, clearance)
    return PartSpec(
        part_id=part_id,
        quantity=1,
        variants=[variant],
        original_polygon=poly,
        grain_locked=False,
        allow_mirror=False,
    )


def _make_sheet_state(w: float = 100, h: float = 50, margin: float = 5, clearance: float = 0.5) -> SheetState:
    sheet_spec = SheetSpec(width=w, height=h, edge_margin=margin, grain_axis=None)
    usable = contract_sheet(sheet_spec, clearance)
    return SheetState(index=0, usable_bounds=usable, spatial_index=SpatialIndex())


def _make_job(parts: list[PartSpec], w: float = 100, h: float = 50) -> NestJob:
    return NestJob(
        sheets=SheetSpec(width=w, height=h, edge_margin=5, grain_axis=None),
        parts=parts,
        clearance=0.5,
        mode="balanced",
        seed=42,
    )


# ---------------------------------------------------------------------------
# 1. test_ordering_area_descending
# ---------------------------------------------------------------------------


def test_ordering_area_descending():
    parts = [_make_part("A", 2, 2), _make_part("B", 5, 5), _make_part("C", 3, 3)]
    orderings = generate_orderings(parts, "fast", seed=0)
    # First ordering should be area descending
    first = orderings[0]
    areas = [p.variants[0].area for p in first]
    assert areas == sorted(areas, reverse=True)


# ---------------------------------------------------------------------------
# 2. test_ordering_deterministic
# ---------------------------------------------------------------------------


def test_ordering_deterministic():
    parts = [_make_part(f"P{i}", i + 1, i + 1) for i in range(5)]
    o1 = generate_orderings(parts, "balanced", seed=123)
    o2 = generate_orderings(parts, "balanced", seed=123)
    for a, b in zip(o1, o2):
        assert [p.part_id for p in a] == [p.part_id for p in b]


# ---------------------------------------------------------------------------
# 3. test_ordering_mode_count
# ---------------------------------------------------------------------------


def test_ordering_mode_count():
    parts = [_make_part(f"P{i}", 2, 2) for i in range(5)]
    assert len(generate_orderings(parts, "fast")) == 3
    assert len(generate_orderings(parts, "balanced")) == 8
    assert len(generate_orderings(parts, "max_yield")) == 16


# ---------------------------------------------------------------------------
# 4. test_boundary_candidates_count
# ---------------------------------------------------------------------------


def test_boundary_candidates_count():
    variant = _make_variant(box(-2, -1, 2, 1), 0.5)
    sheet = _make_sheet_state()
    candidates = boundary_anchors(variant, sheet, max_count=16)
    assert len(candidates) > 0
    assert len(candidates) <= 16


# ---------------------------------------------------------------------------
# 5. test_boundary_candidates_inside_sheet
# ---------------------------------------------------------------------------


def test_boundary_candidates_inside_sheet():
    variant = _make_variant(box(-2, -1, 2, 1), 0.5)
    sheet = _make_sheet_state()
    candidates = boundary_anchors(variant, sheet, max_count=16)
    feasible = filter_feasible(candidates, sheet)
    # All feasible candidates should be inside sheet
    assert len(feasible) > 0


# ---------------------------------------------------------------------------
# 6. test_scoring_prefers_compact
# ---------------------------------------------------------------------------


def test_scoring_prefers_compact():
    sheet = _make_sheet_state()
    variant = _make_variant(box(-2, -1, 2, 1), 0.5)
    weights = ScoringWeights()

    # Compact placement (near origin)
    c_compact = Candidate(variant=variant, x=8, y=8, anchor_tag="bottom-boundary")
    # Spread placement (far from origin)
    c_spread = Candidate(variant=variant, x=60, y=30, anchor_tag="bottom-boundary")

    s_compact = score_candidate(c_compact, sheet, weights)
    s_spread = score_candidate(c_spread, sheet, weights)
    assert s_compact < s_spread, "Compact placement should score better (lower)"


# ---------------------------------------------------------------------------
# 7. test_scoring_prefers_contact
# ---------------------------------------------------------------------------


def test_scoring_prefers_contact():
    sheet = _make_sheet_state()
    # Place a part first
    variant = _make_variant(box(-2, -1, 2, 1), 0.5)
    sheet.place(variant, 8, 8, "P0", variant.transform, "boundary", 0.0)

    weights = ScoringWeights()

    # Adjacent placement (touching placed part)
    inflated_w = variant.inflated.bounds[2] - variant.inflated.bounds[0]
    c_adjacent = Candidate(variant=variant, x=8 + inflated_w, y=8, anchor_tag="generic-contact")
    # Gap placement (far from placed part)
    c_gap = Candidate(variant=variant, x=60, y=30, anchor_tag="generic-contact")

    s_adj = score_candidate(c_adjacent, sheet, weights)
    s_gap = score_candidate(c_gap, sheet, weights)
    assert s_adj <= s_gap, "Adjacent placement should score at least as well as gap"


# ---------------------------------------------------------------------------
# 8. test_constructive_all_placed
# ---------------------------------------------------------------------------


def test_constructive_all_placed():
    parts = [_make_part(f"P{i}", 4, 2, clearance=0.5) for i in range(3)]
    job = _make_job(parts)
    weights = ScoringWeights()
    order = parts[:]

    solution = constructive_solve(
        job, order, {"max_candidates": 60, "max_per_family": 20}, weights
    )
    assert len(solution.unplaced_parts) == 0
    assert len(solution.all_placements()) == 3


# ---------------------------------------------------------------------------
# 9. test_constructive_opens_new_sheet
# ---------------------------------------------------------------------------


def test_constructive_opens_new_sheet():
    # Create parts that won't all fit on one small sheet
    parts = [_make_part(f"P{i}", 20, 15, clearance=0.5) for i in range(6)]
    job = _make_job(parts, w=50, h=40)
    weights = ScoringWeights()
    order = parts[:]

    solution = constructive_solve(
        job, order, {"max_candidates": 60, "max_per_family": 20}, weights
    )
    assert solution.sheet_count() > 1, "Should have opened additional sheets"


# ---------------------------------------------------------------------------
# 10. test_constructive_deterministic
# ---------------------------------------------------------------------------


def test_constructive_deterministic():
    parts = [_make_part(f"P{i}", 4, 2, clearance=0.5) for i in range(5)]
    job = _make_job(parts)
    weights = ScoringWeights()
    order = parts[:]

    s1 = constructive_solve(job, order, {"max_candidates": 60, "max_per_family": 20}, weights)
    s2 = constructive_solve(job, order, {"max_candidates": 60, "max_per_family": 20}, weights)

    placements_1 = [(p.part_id, p.x, p.y) for p in s1.all_placements()]
    placements_2 = [(p.part_id, p.x, p.y) for p in s2.all_placements()]
    assert placements_1 == placements_2
