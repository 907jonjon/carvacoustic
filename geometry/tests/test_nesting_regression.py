"""
Regression tests — snapshot fixtures for representative nesting jobs.

Each fixture is loaded, solved, and validated. Sheet counts are snapshotted
so that a future change that increases sheets for any fixture triggers a failure.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.nesting.bench.datasets import load_fixture
from app.nesting.solver.solve import solve_nest
from app.nesting.solver.validate_result import validate_nest
from app.nesting.solver.result_schema import NestResultOut

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "nesting"

FIXTURES = [
    "simple_convex",
    "concave_slats",
    "grain_locked",
    "mirror_forbidden",
    "narrow_clearance",
    "high_vertex",
    "backing_with_slots",
]

# Snapshot: maximum expected sheet counts per fixture (balanced mode, seed=42).
# If a code change causes any fixture to need more sheets, the test fails.
SHEET_SNAPSHOTS = {
    "simple_convex": 2,
    "concave_slats": 2,
    "grain_locked": 2,
    "mirror_forbidden": 1,
    "narrow_clearance": 2,
    "high_vertex": 1,
    "backing_with_slots": 2,
}


# ---------------------------------------------------------------------------
# Feasibility tests — every fixture must produce a valid layout
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("fixture", FIXTURES)
def test_regression_feasible(fixture):
    """All regression fixtures produce feasible, valid layouts."""
    job = load_fixture(fixture)
    result = solve_nest(job, mode="balanced", seed=42)
    report = validate_nest(job, result)
    assert report.valid, f"Fixture {fixture} failed validation: {report.errors}"
    assert len(result.unplaced) == 0, f"Fixture {fixture} has unplaced parts: {result.unplaced}"
    assert result.utilization > 0, f"Fixture {fixture} has zero utilization"


# ---------------------------------------------------------------------------
# Sheet count snapshot — regression guard
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("fixture", FIXTURES)
def test_regression_sheet_count(fixture):
    """Sheet count should not increase vs. snapshot."""
    job = load_fixture(fixture)
    result = solve_nest(job, mode="balanced", seed=42)
    max_sheets = SHEET_SNAPSHOTS.get(fixture, 99)
    assert result.sheets_used <= max_sheets, (
        f"Fixture {fixture}: {result.sheets_used} sheets > snapshot {max_sheets}"
    )


# ---------------------------------------------------------------------------
# Determinism tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("fixture", ["simple_convex", "concave_slats"])
def test_regression_deterministic(fixture):
    """Same fixture + same seed = same result."""
    job = load_fixture(fixture)
    r1 = solve_nest(job, mode="balanced", seed=42)
    r2 = solve_nest(job, mode="balanced", seed=42)
    assert r1.sheets_used == r2.sheets_used
    assert abs(r1.utilization - r2.utilization) < 1e-6
    assert len(r1.placements) == len(r2.placements)


# ---------------------------------------------------------------------------
# Validation API tests
# ---------------------------------------------------------------------------


def test_validate_nest_valid():
    """validate_nest returns valid=True for a good solve."""
    job = load_fixture("simple_convex")
    result = solve_nest(job, mode="fast", seed=42)
    report = validate_nest(job, result)
    assert report.valid
    assert report.total_parts_placed == len(result.placements)
    assert report.sheets_used == result.sheets_used


def test_validate_nest_detects_overlap():
    """validate_nest returns valid=False when placements overlap."""
    from app.nesting.models import NestResult, Placement, TransformSpec

    job = load_fixture("simple_convex")
    # Create a bogus result with two parts at the same position
    t = TransformSpec(0, False)
    bad_result = NestResult(
        placements=[
            Placement("S001", 0, t, 10, 10, "boundary", 0),
            Placement("S002", 0, t, 10, 10, "boundary", 0),
        ],
        sheets_used=1, utilization=0.1, unplaced=["S003", "S004", "S005"],
        warnings=[], elapsed_ms=0,
    )
    report = validate_nest(job, bad_result)
    assert not report.valid
    assert len(report.errors) > 0


# ---------------------------------------------------------------------------
# Result schema tests
# ---------------------------------------------------------------------------


def test_result_schema_serializable():
    """NestResultOut can be serialized to JSON."""
    job = load_fixture("simple_convex")
    result = solve_nest(job, mode="fast", seed=42)
    out = NestResultOut.from_nest_result(result, mode="fast", seed=42)
    json_str = out.model_dump_json()
    assert "sheets_used" in json_str
    assert "placements" in json_str
    assert out.status == "ok"
