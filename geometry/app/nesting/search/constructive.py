"""Main constructive placement loop — contact-biased search."""

from __future__ import annotations

from ..geometry.offsets import contract_sheet
from ..geometry.sheet import SheetState
from ..geometry.spatial_hash import SpatialIndex
from ..models import NestJob, PartSpec, SolutionState
from .candidates import Candidate, filter_feasible, generate_candidates
from .scoring import ScoringWeights, score_candidate


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
    2. Filter: inside_contracted_sheet → broad_phase → exact_collision
    3. Score feasible candidates
    4. Place the best candidate
    5. If no candidate works, open a new sheet and retry
    """
    usable = contract_sheet(job.sheets, job.clearance)

    state = SolutionState(seed=job.seed)
    state.sheets.append(_new_sheet(0, usable))

    for part in part_order:
        placed = _try_place_part(part, state, job, mode_limits, scoring_weights, usable)

        if not placed:
            # Open new sheet and retry
            new_idx = len(state.sheets)
            state.sheets.append(_new_sheet(new_idx, usable))
            placed = _try_place_part(part, state, job, mode_limits, scoring_weights, usable)

        if not placed:
            state.unplaced_parts.append(part)

    return state


def _try_place_part(
    part: PartSpec,
    state: SolutionState,
    job: NestJob,
    mode_limits: dict,
    weights: ScoringWeights,
    usable: object,
) -> bool:
    """Try to place a part on any existing sheet. Returns True if placed."""
    best_candidate: Candidate | None = None
    best_score = float("inf")
    best_sheet: SheetState | None = None

    for sheet in state.sheets:
        candidates = generate_candidates(part, sheet, mode_limits)
        feasible = filter_feasible(candidates, sheet)

        for c in feasible:
            c.score = score_candidate(c, sheet, weights)
            if c.score < best_score:
                best_score = c.score
                best_candidate = c
                best_sheet = sheet

    if best_candidate is not None and best_sheet is not None:
        best_sheet.place(
            variant=best_candidate.variant,
            x=best_candidate.x,
            y=best_candidate.y,
            part_id=part.part_id,
            transform=best_candidate.variant.transform,
            anchor_tag=best_candidate.anchor_tag,
            score=best_candidate.score,
        )
        return True

    return False


def _new_sheet(index: int, usable_bounds) -> SheetState:
    """Create a fresh SheetState."""
    return SheetState(
        index=index,
        usable_bounds=usable_bounds,
        spatial_index=SpatialIndex(),
    )
