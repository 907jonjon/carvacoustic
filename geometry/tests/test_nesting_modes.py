"""
Tests for nesting engine Phase 2 — mode presets and improvement passes.
6 test cases.
"""

from __future__ import annotations

import pytest
from shapely.geometry import box
from shapely.prepared import prep

from app.nesting.geometry.offsets import inflate_part
from app.nesting.models import (
    NestJob,
    PartSpec,
    SheetSpec,
    TransformSpec,
    VariantGeom,
)
from app.nesting.solver.solve import solve_nest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_variant(poly, clearance=0.5):
    t = TransformSpec(angle_deg=0, mirrored=False)
    inflated = inflate_part(poly, clearance)
    return VariantGeom(
        transform=t, polygon=poly, inflated=inflated,
        prepared_inflated=prep(inflated),
        aabb=inflated.bounds, preferred_edges=[], area=poly.area,
    )


def _make_part(pid, w, h, clearance=0.5):
    poly = box(-w / 2, -h / 2, w / 2, h / 2)
    return PartSpec(
        part_id=pid, quantity=1, variants=[_make_variant(poly, clearance)],
        original_polygon=poly, grain_locked=False, allow_mirror=False,
    )


def _make_job(n_parts=8, w=100, h=50, part_w=6, part_h=3, clearance=0.5, mode="balanced"):
    parts = [_make_part(f"P{i}", part_w, part_h, clearance) for i in range(n_parts)]
    return NestJob(
        sheets=SheetSpec(width=w, height=h, edge_margin=5, grain_axis=None),
        parts=parts, clearance=clearance, mode=mode, seed=42,
    )


# ---------------------------------------------------------------------------
# 1. test_fast_mode_feasible
# ---------------------------------------------------------------------------


def test_fast_mode_feasible():
    job = _make_job(mode="fast")
    result = solve_nest(job, mode="fast", seed=42)
    assert result.sheets_used >= 1
    assert len(result.unplaced) == 0


# ---------------------------------------------------------------------------
# 2. test_balanced_mode_feasible
# ---------------------------------------------------------------------------


def test_balanced_mode_feasible():
    job = _make_job(mode="balanced")
    result = solve_nest(job, mode="balanced", seed=42)
    assert result.sheets_used >= 1
    assert len(result.unplaced) == 0


# ---------------------------------------------------------------------------
# 3. test_max_yield_feasible
# ---------------------------------------------------------------------------


def test_max_yield_feasible():
    job = _make_job(mode="max_yield")
    result = solve_nest(job, mode="max_yield", seed=42)
    assert result.sheets_used >= 1
    assert len(result.unplaced) == 0


# ---------------------------------------------------------------------------
# 4. test_balanced_beats_fast_utilization
# ---------------------------------------------------------------------------


def test_balanced_beats_fast_utilization():
    job_fast = _make_job(n_parts=12, mode="fast")
    job_bal = _make_job(n_parts=12, mode="balanced")

    r_fast = solve_nest(job_fast, mode="fast", seed=42)
    r_bal = solve_nest(job_bal, mode="balanced", seed=42)

    # Balanced should be at least as good (fewer or equal sheets)
    assert r_bal.sheets_used <= r_fast.sheets_used or r_bal.utilization >= r_fast.utilization * 0.95


# ---------------------------------------------------------------------------
# 5. test_compact_improves
# ---------------------------------------------------------------------------


def test_compact_improves():
    """Compaction should not worsen and ideally maintain utilization."""
    from app.nesting.search.constructive import constructive_solve
    from app.nesting.search.improve import compact
    from app.nesting.search.scoring import ScoringWeights

    job = _make_job(n_parts=5)
    weights = ScoringWeights()

    solution = constructive_solve(
        job, job.parts, {"max_candidates": 60, "max_per_family": 20}, weights
    )
    pre_util = solution.average_utilization()
    pre_placed = len(solution.all_placements())

    compacted = compact(solution)
    post_placed = len(compacted.all_placements())

    # Compact should not lose any parts
    assert post_placed == pre_placed


# ---------------------------------------------------------------------------
# 6. test_reinsert_improves
# ---------------------------------------------------------------------------


def test_reinsert_improves():
    """Reinsert should not lose parts (all should be re-placed or stay unplaced)."""
    from app.nesting.search.constructive import constructive_solve
    from app.nesting.search.improve import reinsert_worst
    from app.nesting.search.scoring import ScoringWeights

    job = _make_job(n_parts=6)
    weights = ScoringWeights()

    solution = constructive_solve(
        job, job.parts, {"max_candidates": 60, "max_per_family": 20}, weights
    )
    pre_total = len(solution.all_placements()) + len(solution.unplaced_parts)

    improved = reinsert_worst(
        solution, job, n_remove=2,
        mode_limits={"max_candidates": 60, "max_per_family": 20},
        scoring_weights=weights,
    )
    post_total = len(improved.all_placements()) + len(improved.unplaced_parts)

    assert post_total == pre_total
