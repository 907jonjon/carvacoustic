"""Top-level solve_nest() entry point — runs mode-configured solver."""

from __future__ import annotations

import time

from ..geometry.validate import validate_solution
from ..models import NestJob, NestResult, SolutionState
from ..search.constructive import constructive_solve
from ..search.improve import compact, reinsert_worst, small_swap
from ..search.modes import MODES
from ..search.ordering import generate_orderings
from ..search.scoring import ScoringWeights


def solve_nest(
    job: NestJob,
    mode: str | None = None,
    seed: int | None = None,
) -> NestResult:
    """
    Solve a nesting job. Returns the best solution across all seed orderings.

    Flow:
    1. Get mode config
    2. Generate seed orderings
    3. For each ordering: constructive_solve -> compact -> reinsert -> swap
    4. Validate best solution
    5. Return NestResult
    """
    t0 = time.monotonic()

    effective_mode = mode or job.mode or "balanced"
    effective_seed = seed if seed is not None else job.seed

    mode_cfg = MODES.get(effective_mode, MODES["balanced"])
    weights = ScoringWeights()

    orderings = generate_orderings(job.parts, effective_mode, effective_seed)

    best: SolutionState | None = None

    for order in orderings:
        solution = constructive_solve(
            job, order,
            {"max_candidates": mode_cfg.max_candidates, "max_per_family": mode_cfg.max_per_family},
            weights,
        )

        # Improvement passes
        for _ in range(mode_cfg.compact_passes):
            solution = compact(solution)

        for _ in range(mode_cfg.reinsert_rounds):
            solution = reinsert_worst(
                solution, job, mode_cfg.reinsert_remove_n,
                {"max_candidates": mode_cfg.max_candidates, "max_per_family": mode_cfg.max_per_family},
                weights,
            )

        for _ in range(mode_cfg.swap_passes):
            solution = small_swap(solution, job)

        if best is None or _solution_score(solution) < _solution_score(best):
            best = solution

    assert best is not None

    # Validate
    errors = validate_solution(job, _to_nest_result(best, 0), job.parts)
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


def _solution_score(state: SolutionState) -> tuple[int, float]:
    """
    Score for comparing solutions: prefer fewer sheets, then higher utilization.
    Returns (sheets, -utilization) so lower is better.
    """
    return (state.sheet_count(), -state.average_utilization())


def _to_nest_result(state: SolutionState, elapsed_ms: float) -> NestResult:
    """Convert SolutionState to NestResult for validation."""
    return NestResult(
        placements=state.all_placements(),
        sheets_used=state.sheet_count(),
        utilization=state.average_utilization(),
        unplaced=[p.part_id for p in state.unplaced_parts],
        warnings=[],
        elapsed_ms=elapsed_ms,
    )
