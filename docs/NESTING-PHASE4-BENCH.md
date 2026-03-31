# Nesting Engine — Phase 4: Benchmarks + Hardening

**Depends on:** Phase 1 (geometry) and Phase 2 (search)

**Goal:** Add a benchmark harness, regression test fixtures, the public `validate_nest()` interface, and ensure deterministic reproducibility. This phase makes the nesting engine production-safe.

**Guiding document:** `docs/carvacoustic_nesting_build_document.md` — sections 2.10–2.15 and 2.17.

---

## Package Structure to Create

```
geometry/app/nesting/
    bench/
        __init__.py
        datasets.py         # Load benchmark datasets (internal + synthetic)
        runner.py            # Run solver across datasets, collect metrics
        reports.py           # Generate comparison reports
    solver/
        validate_result.py   # Public validate_nest() entry point
        result_schema.py     # NestResult → JSON-serializable output
```

Add to existing:
```
geometry/tests/
    test_nesting_regression.py   # Snapshot fixtures for representative jobs
    fixtures/
        nesting/
            simple_convex.json
            concave_slats.json
            grain_locked.json
            mirror_forbidden.json
            narrow_clearance.json
            high_vertex.json
            backing_with_slots.json
```

---

## Implementation Spec

### 1. `solver/validate_result.py` — Public Validation API

```python
from ..models import NestJob, NestResult
from ..geometry.validate import validate_solution

def validate_nest(job: NestJob, result: NestResult) -> ValidationReport:
    """
    Validate a nesting result independently from the solver.
    Use this to check imported or manually edited placements.

    Returns:
        ValidationReport with:
        - valid: bool
        - errors: list[str]  (overlap, out-of-bounds, illegal transform)
        - warnings: list[str] (low utilization, unplaced parts)
    """
```

This must be callable without running the solver — it takes a job and result and returns a report.

### 2. `solver/result_schema.py` — JSON-Serializable Output

```python
from pydantic import BaseModel

class PlacementOut(BaseModel):
    part_id: str
    sheet_index: int
    angle_deg: float
    mirrored: bool
    x: float
    y: float
    anchor_tag: str

class NestResultOut(BaseModel):
    status: str                 # "ok" | "error"
    placements: list[PlacementOut]
    sheets_used: int
    utilization: float
    unplaced: list[str]
    warnings: list[str]
    elapsed_ms: float
    mode: str
    seed: int | None

def serialize_result(result: NestResult, mode: str, seed: int | None) -> NestResultOut:
    """Convert internal NestResult to the API-facing schema."""
```

### 3. `bench/datasets.py` — Benchmark Datasets

```python
from ..models import NestJob

def load_internal_dataset(name: str) -> NestJob:
    """
    Load a CarvAcoustic-specific benchmark job.

    Available datasets:
    - "wave_30_slats" — 30 wave-profile slats + backing, 96x48 sheet, inches
    - "wave_60_slats" — 60 slats, tighter packing challenge
    - "mountain_mixed" — mountain surface with high profile variation
    - "grain_locked_90" — grain locked, 90-only rotation
    - "no_grain_free_rotate" — particle board, all rotations allowed
    - "narrow_clearance" — 0.03" clearance (tight)
    - "wide_clearance" — 0.25" clearance (loose)
    """

def generate_synthetic_dataset(
    n_parts: int,
    complexity: str = "medium",    # "simple" | "medium" | "complex"
    seed: int = 42,
) -> NestJob:
    """
    Generate synthetic benchmark jobs for edge cases.

    - simple: convex regular polygons
    - medium: one-flat-edge shapes with moderate curves
    - complex: high-vertex concave shapes with small features
    """
```

Build internal datasets by running the actual CarvAcoustic pipeline (height field → profiler) with representative configs, then serializing the parts. This ensures benchmarks use real product geometry.

### 4. `bench/runner.py` — Benchmark Runner

```python
import time
from dataclasses import dataclass

@dataclass
class BenchmarkResult:
    dataset: str
    mode: str
    seed: int
    sheets_used: int
    utilization: float
    runtime_ms: float
    unplaced_count: int
    valid: bool
    validation_errors: list[str]
    sliver_count: int           # unusable narrow strips detected
    warnings: list[str]

def run_benchmark(
    dataset_name: str,
    mode: str = "balanced",
    seed: int = 42,
    n_runs: int = 1,
) -> list[BenchmarkResult]:
    """
    Run the solver on a dataset and collect metrics.
    Multiple runs with different seeds test variance.
    """

def run_all_benchmarks(
    modes: list[str] = ["fast", "balanced", "max_yield"],
    seed: int = 42,
) -> list[BenchmarkResult]:
    """Run all internal datasets across all modes."""
```

Track at minimum (per §2.15):
- Sheet count
- Utilization
- Runtime to first feasible result
- Runtime to best result
- Invalid-result rate
- Geometry repair failure rate
- Sliver count

### 5. `bench/reports.py` — Benchmark Reports

```python
def generate_report(results: list[BenchmarkResult]) -> str:
    """
    Generate a markdown benchmark report.

    Format:
    | Dataset | Mode | Sheets | Util% | Runtime(ms) | Valid | Slivers |
    |---------|------|--------|-------|-------------|-------|---------|
    """

def compare_reports(
    baseline: list[BenchmarkResult],
    current: list[BenchmarkResult],
) -> str:
    """
    Generate a comparison report showing deltas between baseline and current.
    Highlights regressions (more sheets or lower utilization).
    """
```

---

## Regression Test Fixtures

### Test file: `geometry/tests/test_nesting_regression.py`

Each fixture is a JSON file containing a serialized `NestJob` and expected outcomes:

```python
import json
import pytest
from geometry.app.nesting.solver.solve import solve_nest
from geometry.app.nesting.solver.validate_result import validate_nest

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "nesting"

@pytest.mark.parametrize("fixture", [
    "simple_convex",
    "concave_slats",
    "grain_locked",
    "mirror_forbidden",
    "narrow_clearance",
    "high_vertex",
    "backing_with_slots",
])
def test_regression_feasible(fixture):
    """All regression fixtures produce feasible, valid layouts."""
    job = load_fixture(fixture)
    result = solve_nest(job, mode="balanced", seed=42)
    report = validate_nest(job, result)
    assert report.valid, f"Fixture {fixture} failed validation: {report.errors}"
    assert len(result.unplaced) == 0, f"Fixture {fixture} has unplaced parts"

@pytest.mark.parametrize("fixture", [
    "simple_convex",
    "concave_slats",
])
def test_regression_deterministic(fixture):
    """Same fixture + same seed = same result."""
    job = load_fixture(fixture)
    r1 = solve_nest(job, mode="balanced", seed=42)
    r2 = solve_nest(job, mode="balanced", seed=42)
    assert r1.sheets_used == r2.sheets_used
    assert abs(r1.utilization - r2.utilization) < 1e-6
    assert len(r1.placements) == len(r2.placements)
```

### Fixture format (`fixtures/nesting/simple_convex.json`):

```json
{
  "sheet": {"width": 96.0, "height": 48.0, "edge_margin": 0.75, "grain_axis": "x"},
  "clearance": 0.125,
  "parts": [
    {
      "part_id": "S001",
      "polygon_wkt": "POLYGON ((0 0, 48 0, 48 3, 0 3, 0 0))",
      "quantity": 1,
      "grain_locked": false,
      "allow_mirror": false,
      "allowed_angles": [0, 90, 180, 270]
    }
  ],
  "expected": {
    "max_sheets": 1,
    "min_utilization": 0.01
  }
}
```

Generate fixtures by running the profiler with known configs and serializing the output. Include a script:

```python
# geometry/tests/fixtures/nesting/generate_fixtures.py
"""
Run this once to generate regression fixtures from known configs.
Usage: python -m geometry.tests.fixtures.nesting.generate_fixtures
"""
```

---

## Deliverables Checklist (from §2.17)

After Phase 4 is complete, the following must exist:

1. **Code review memo** — `docs/NESTING-REVIEW-MEMO.md` describing what was reused from the existing codebase, what was added, and what was intentionally deferred.

2. **Production code** — The full `geometry/app/nesting/` package with:
   - Preprocessing (flatten, normalize, offsets, transforms)
   - Candidate generation (boundary, flat-edge contact, generic contact)
   - Search (constructive loop, scoring, improvement passes)
   - Validation (independent post-solve checker)
   - Mode configs (fast, balanced, max_yield)

3. **Tests** — Covering:
   - Geometry repair, transform legality, feasibility (Phase 1 tests)
   - Search correctness, scoring, determinism (Phase 2 tests)
   - Regression fixtures for representative jobs (Phase 4 tests)

4. **Benchmark runner** — `geometry/app/nesting/bench/` with:
   - Internal dataset loader
   - Benchmark runner with metrics collection
   - At least one benchmark report artifact

5. **Developer README** — `geometry/app/nesting/README.md` describing:
   - Solver flow (ingest → geometry → search → validate → result)
   - How to add a new benchmark dataset
   - How to tune scoring weights
   - How to run benchmarks
   - Mode differences and expected behavior

---

## Acceptance Criteria (from §2.14)

| Category | Criterion |
|----------|-----------|
| Feasibility | No overlaps on inflated geometry; no part outside contracted sheet; validator agrees with solver |
| Transform legality | Every placement uses a transform from the explicit allowed set |
| Determinism | Same job + same seed + same mode = same layout and score |
| Robust input | Dirty/invalid geometry is repaired or rejected with a clear reason |
| Mode behavior | Fast, Balanced, Max Yield all produce feasible layouts with predictable quality differences |
| Benchmarks | Runner records runtime, utilization, sheet count, warnings, failure reasons |
| Regression safety | Snapshot fixtures pass for all representative job types |

---

## What NOT to Do

- Do not implement V2 features (ruin-and-recreate, cross-sheet moves, overlap-minimization) — those are a separate future phase
- Do not add compiled backend or NFP caching
- Do not switch to GA or SA optimization
- Do not break the fallback path to FFD
- Do not modify the export pipeline
