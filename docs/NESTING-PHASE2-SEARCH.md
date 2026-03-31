# Nesting Engine — Phase 2: Search Engine + Constructive Solver

**Depends on:** Phase 1 (geometry foundation in `geometry/app/nesting/geometry/`)

**Goal:** Build the search engine that uses the Phase 1 geometry subsystem to produce real nested layouts. Replaces the FFD packer in `geometry/app/geometry/layout.py` as the primary layout engine.

**Guiding document:** `docs/carvacoustic_nesting_build_document.md` — sections 2.6–2.13 and 2.16.

---

## Prerequisite: Phase 1 Must Be Complete

Before starting this phase, verify:
1. `geometry/app/nesting/geometry/` package exists with collision.py, offsets.py, transforms.py, spatial_hash.py, preferred_edges.py, sheet.py, validate.py
2. `geometry/app/nesting/models.py` has NestJob, PartSpec, VariantGeom, SheetState, Placement, NestResult
3. `geometry/app/nesting/ingest.py` has `prepare_nest_job()` and `nest_result_to_layout_result()`
4. All Phase 1 tests pass

---

## Package Structure to Create

```
geometry/app/nesting/
    search/
        __init__.py
        ordering.py         # Seeded part orderings
        candidates.py       # Anchor-based candidate generation
        scoring.py          # Weighted placement scorer
        constructive.py     # Main constructive placement loop
        improve.py          # Post-placement repair: compact, reinsert, swap
        modes.py            # Fast / Balanced / Max Yield config presets
    solver/
        __init__.py
        solve.py            # Top-level solve_nest() entry point
        validate_result.py  # Wraps geometry/validate.py for public API
        result_schema.py    # NestResult → JSON-serializable output
```

---

## Implementation Spec

### 1. `search/ordering.py` — Seeded Part Orders

```python
import random

def generate_orderings(
    parts: list[PartSpec],
    mode: str,
    seed: int | None = None,
) -> list[list[PartSpec]]:
    """
    Generate multiple seeded part orderings for the constructive solver.

    Orderings:
    1. Area descending (largest parts first)
    2. Longest extent descending (max of width, height)
    3. Awkwardness descending (ratio of bounding box area to polygon area — less regular = higher)
    4+ Randomized perturbations of ordering #1

    Number of orderings by mode:
    - fast: 2-3
    - balanced: 6-12
    - max_yield: 12-20
    """
```

Mode seed counts (from build document §2.9):
- `fast`: 3 orderings
- `balanced`: 8 orderings
- `max_yield`: 16 orderings

Use `random.Random(seed)` for deterministic shuffles.

### 2. `search/candidates.py` — Anchor-Based Candidate Generation

This is the heart of V1 performance. Every candidate must carry an `anchor_tag`.

```python
@dataclass
class Candidate:
    variant: VariantGeom
    x: float
    y: float
    anchor_tag: str     # "left-boundary", "bottom-boundary", "flat-edge-contact", "generic-contact"
    score: float = 0.0  # filled in by scorer

def generate_candidates(
    part: PartSpec,
    sheet: SheetState,
    mode_limits: dict,
) -> list[Candidate]:
    """
    Generate placement candidates from three anchor families.
    Returns at most mode_limits["max_candidates"] candidates.
    """
```

**Three anchor families:**

**A. Boundary anchors** (`boundary_anchors()`):
- Slide the part's preferred edge (or bounding edge) against each sheet boundary
- For bottom boundary: place part with its lowest point at `y = 0` (contracted sheet coords), slide X in steps
- For left boundary: place part with its leftmost point at `x = 0`, slide Y in steps
- Step size: `part_width / 4` or `part_height / 4`
- Generate ~4-8 candidates per boundary edge

**B. Flat-edge contact anchors** (`flat_edge_contact_anchors()`):
- For each placed part on the sheet, find exposed near-straight edges
- Align the current part's preferred flat edge against each exposed flat edge
- Slide along the contact edge in steps
- This is the product-specific bias from §1.7 of the build document

**C. Generic contact anchors** (`generic_contact_anchors()`):
- Touch the candidate against the top-right envelope of placed parts
- Use bounding box corners of placed parts as anchor points
- Place at `(placed_max_x + gap, placed_y)` and `(placed_x, placed_max_y + gap)`

**Mode limits (from §2.9):**
```python
MODE_LIMITS = {
    "fast":      {"max_candidates": 20,  "max_per_family": 8},
    "balanced":  {"max_candidates": 60,  "max_per_family": 20},
    "max_yield": {"max_candidates": 100, "max_per_family": 40},
}
```

### 3. `search/scoring.py` — Weighted Placement Scorer

```python
@dataclass
class ScoringWeights:
    envelope_growth: float = 1.0     # penalty for expanding used envelope
    max_x_growth: float = 0.5        # penalty for rightward expansion
    max_y_growth: float = 0.5        # penalty for upward expansion
    contact_length: float = -0.8     # bonus for flush contact with sheet/parts
    preferred_edge: float = -0.6     # bonus for flat-edge alignment
    sliver_penalty: float = 1.2      # penalty for creating narrow unusable strips
    cavity_penalty: float = 0.8      # penalty for trapped pockets

def score_candidate(
    candidate: Candidate,
    sheet: SheetState,
    weights: ScoringWeights | None = None,
) -> float:
    """
    Score a feasible candidate placement.
    Lower score = better placement.
    All geometric measures normalized by sheet dimensions.
    """
```

Implementation notes:
- **Envelope growth:** measure increase in bounding box of all placed parts
- **Contact length:** compute shared boundary length between candidate polygon and placed polygons using `intersection()` — normalize by part perimeter
- **Preferred edge bonus:** if the part's preferred edge is within 5° and 0.5mm of a sheet boundary or placed part edge, apply bonus
- **Sliver detection:** after hypothetical placement, check if any gap between parts is < `2 * tool_diameter` wide — if so, apply penalty
- **Cavity detection:** simplified — check if the placement creates an enclosed pocket smaller than the smallest remaining unplaced part

Put weights in `ScoringWeights` dataclass so they can be tuned without code edits (per §2.8).

### 4. `search/constructive.py` — Main Placement Loop

This implements the pseudocode from §2.13 of the build document:

```python
def constructive_solve(
    job: NestJob,
    part_order: list[PartSpec],
    mode_limits: dict,
    scoring_weights: ScoringWeights,
) -> SolutionState:
    """
    Place all parts using contact-biased constructive search.

    For each part in order:
    1. Generate candidates across all open sheets
    2. Filter: inside_contracted_sheet? → broad_phase (spatial hash) → exact_collision
    3. Score feasible candidates
    4. Place the best candidate
    5. If no candidate works, open a new sheet and retry
    """
```

Key implementation details:
- Maintain a list of `SheetState` objects
- Start with one empty sheet
- For each unplaced part, iterate its legal variants (transforms)
- For each variant, generate candidates on each sheet
- Filter pipeline: `check_inside_sheet()` → `spatial_index.query_nearby()` → `check_collision()`
- Score survivors, pick the best across all sheets
- If nothing fits anywhere, open a new sheet and retry once
- If still no fit, record as unplaced

### 5. `search/improve.py` — Post-Placement Repair

```python
def compact(state: SolutionState) -> SolutionState:
    """
    Slide each part toward the origin (bottom-left) as far as possible
    without creating overlaps. One pass, deterministic.
    """

def reinsert_worst(
    state: SolutionState,
    job: NestJob,
    n_remove: int = 3,
    mode_limits: dict = None,
    scoring_weights: ScoringWeights = None,
) -> SolutionState:
    """
    Remove the N parts with the worst score (most wasteful placements),
    then re-place them using the constructive solver with larger candidate
    budgets. Repeat for a few iterations.
    """

def small_swap(state: SolutionState, job: NestJob) -> SolutionState:
    """
    Try swapping pairs of adjacent parts on the same sheet.
    Accept swaps that improve total score. One pass.
    """
```

Repair budget by mode:
- `fast`: compact only
- `balanced`: compact + 1 round reinsert (remove 3) + 1 swap pass
- `max_yield`: compact + 3 rounds reinsert (remove 5) + 2 swap passes

### 6. `search/modes.py` — Mode Presets

```python
from dataclasses import dataclass

@dataclass
class ModeConfig:
    name: str
    n_seeds: int
    max_candidates: int
    max_per_family: int
    compact_passes: int
    reinsert_rounds: int
    reinsert_remove_n: int
    swap_passes: int

MODES = {
    "fast": ModeConfig(
        name="fast", n_seeds=3,
        max_candidates=20, max_per_family=8,
        compact_passes=1, reinsert_rounds=0, reinsert_remove_n=0, swap_passes=0,
    ),
    "balanced": ModeConfig(
        name="balanced", n_seeds=8,
        max_candidates=60, max_per_family=20,
        compact_passes=1, reinsert_rounds=1, reinsert_remove_n=3, swap_passes=1,
    ),
    "max_yield": ModeConfig(
        name="max_yield", n_seeds=16,
        max_candidates=100, max_per_family=40,
        compact_passes=1, reinsert_rounds=3, reinsert_remove_n=5, swap_passes=2,
    ),
}
```

### 7. `solver/solve.py` — Top-Level Entry Point

```python
import time
from ..models import NestJob, NestResult
from ..search.ordering import generate_orderings
from ..search.constructive import constructive_solve
from ..search.improve import compact, reinsert_worst, small_swap
from ..search.modes import MODES
from ..search.scoring import ScoringWeights
from ..geometry.validate import validate_solution

def solve_nest(
    job: NestJob,
    mode: str = "balanced",
    seed: int | None = None,
) -> NestResult:
    """
    Solve a nesting job. Returns the best solution across all seed orderings.

    Flow:
    1. Get mode config
    2. Generate seed orderings
    3. For each ordering: constructive_solve → compact → reinsert → swap
    4. Validate best solution
    5. Return NestResult
    """
    t0 = time.monotonic()
    mode_cfg = MODES[mode]
    weights = ScoringWeights()

    orderings = generate_orderings(job.parts, mode, seed)

    best = None
    for order in orderings:
        solution = constructive_solve(job, order, mode_cfg.__dict__, weights)
        solution = compact(solution)
        if mode_cfg.reinsert_rounds > 0:
            for _ in range(mode_cfg.reinsert_rounds):
                solution = reinsert_worst(solution, job, mode_cfg.reinsert_remove_n, mode_cfg.__dict__, weights)
        for _ in range(mode_cfg.swap_passes):
            solution = small_swap(solution, job)

        if best is None or solution_score(solution) < solution_score(best):
            best = solution

    # Validate
    errors = validate_solution(job, best, job.parts)
    warnings = errors if errors else []

    elapsed = (time.monotonic() - t0) * 1000

    return NestResult(
        placements=best.all_placements(),
        sheets_used=best.sheet_count(),
        utilization=best.average_utilization(),
        unplaced=[p.part_id for p in best.unplaced_parts],
        warnings=warnings,
        elapsed_ms=elapsed,
    )
```

---

## Integration with Existing Pipeline

### In `geometry/app/geometry/pipeline.py`

Replace the `run_slat_layout()` call with:
```python
# Try the nesting engine, fall back to FFD
try:
    from ..nesting.ingest import prepare_nest_job, nest_result_to_layout_result
    from ..nesting.solver.solve import solve_nest
    nest_job = prepare_nest_job(all_parts, config, mode="balanced")
    nest_result = solve_nest(nest_job, mode="balanced")
    layout_result = nest_result_to_layout_result(nest_result, all_parts, nest_job)
except Exception as exc:
    import logging
    logging.getLogger(__name__).warning("Nesting engine failed, falling back to FFD: %s", exc)
    layout_result = run_slat_layout(all_parts, config)
```

Same pattern in `bundle.py::build_export_bundle()`.

### In `geometry/app/geometry/layout.py`

Keep `run_slat_layout()` and `run_layout()` intact as fallbacks. Do not modify them.

---

## Tests to Write

File: `geometry/tests/test_nesting_search.py`

1. **test_ordering_area_descending** — first element is largest
2. **test_ordering_deterministic** — same seed produces same order
3. **test_ordering_mode_count** — fast gives 3, balanced gives 8, max_yield gives 16
4. **test_boundary_candidates_count** — generates expected number
5. **test_boundary_candidates_inside_sheet** — all candidates within sheet bounds
6. **test_scoring_prefers_compact** — compact placement scores better than spread
7. **test_scoring_prefers_contact** — adjacent placement scores better than gap
8. **test_constructive_all_placed** — simple job places all parts
9. **test_constructive_opens_new_sheet** — large job spills to sheet 2
10. **test_constructive_deterministic** — same seed = same result

File: `geometry/tests/test_nesting_modes.py`

1. **test_fast_mode_feasible** — fast produces valid layout
2. **test_balanced_mode_feasible** — balanced produces valid layout
3. **test_max_yield_feasible** — max_yield produces valid layout
4. **test_balanced_beats_fast_utilization** — balanced >= fast utilization on test job
5. **test_compact_improves** — compaction doesn't worsen and ideally improves utilization
6. **test_reinsert_improves** — reinsert doesn't worsen score

File: `geometry/tests/test_nesting_integration.py`

1. **test_solve_nest_returns_nest_result** — correct return type
2. **test_nest_result_to_layout_result** — converts correctly to LayoutResult
3. **test_full_pipeline_with_nesting** — pipeline.run_pipeline() uses nesting engine
4. **test_export_bundle_with_nesting** — bundle.build_export_bundle() produces valid ZIP
5. **test_fallback_to_ffd** — if nesting fails, FFD fallback works

---

## What NOT to Do

- Do not modify Phase 1 geometry modules (they're the stable foundation)
- Do not implement continuous free-angle rotation (discrete angles only)
- Do not implement GA or SA optimizers (constructive + repair only in V1)
- Do not add hole nesting / part-in-part
- Do not let search bypass exact validation or transform legality
- Do not create separate code paths per mode — use config presets over one solver
- Do not introduce new dependencies beyond what's in pyproject.toml (shapely, numpy are sufficient)
