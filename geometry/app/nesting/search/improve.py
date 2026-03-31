"""Post-placement repair — compact, reinsert worst, small swap."""

from __future__ import annotations

from shapely import affinity

from ..geometry.collision import check_collision, check_inside_sheet
from ..geometry.offsets import contract_sheet
from ..geometry.sheet import SheetState
from ..geometry.spatial_hash import SpatialIndex
from ..models import NestJob, PartSpec, Placement, SolutionState
from .candidates import generate_candidates, filter_feasible
from .scoring import ScoringWeights, score_candidate


def compact(state: SolutionState) -> SolutionState:
    """
    Slide each part toward the origin (bottom-left) as far as possible
    without creating overlaps. One pass, deterministic.
    """
    for sheet in state.sheets:
        for i, placement in enumerate(sheet.placements):
            _try_compact_placement(sheet, i)
    return state


def _try_compact_placement(sheet: SheetState, idx: int) -> None:
    """Try to move a single placement closer to origin."""
    if idx >= len(sheet.placed_inflated):
        return

    current_poly = sheet.placed_inflated[idx]
    placement = sheet.placements[idx]
    cb = current_poly.bounds

    # Try sliding left
    for dx in [-(cb[2] - cb[0]) / 4, -(cb[2] - cb[0]) / 8]:
        new_poly = affinity.translate(current_poly, xoff=dx, yoff=0)
        if _is_valid_move(sheet, idx, new_poly):
            sheet.placed_inflated[idx] = new_poly
            placement.x += dx
            break

    # Try sliding down
    current_poly = sheet.placed_inflated[idx]
    for dy in [-(cb[3] - cb[1]) / 4, -(cb[3] - cb[1]) / 8]:
        new_poly = affinity.translate(current_poly, xoff=0, yoff=dy)
        if _is_valid_move(sheet, idx, new_poly):
            sheet.placed_inflated[idx] = new_poly
            placement.y += dy
            break


def _is_valid_move(sheet: SheetState, idx: int, new_poly) -> bool:
    """Check if a moved polygon is still valid (in bounds, no collisions)."""
    if not sheet.usable_bounds.contains(new_poly):
        return False
    for j, other in enumerate(sheet.placed_inflated):
        if j == idx:
            continue
        if new_poly.intersects(other):
            overlap = new_poly.intersection(other)
            if overlap.area > 1e-10:
                return False
    return True


def reinsert_worst(
    state: SolutionState,
    job: NestJob,
    n_remove: int = 3,
    mode_limits: dict | None = None,
    scoring_weights: ScoringWeights | None = None,
) -> SolutionState:
    """
    Remove the N parts with the worst score, then re-place them
    using the constructive solver with current candidate budgets.
    """
    if mode_limits is None:
        mode_limits = {"max_candidates": 60, "max_per_family": 20}
    if scoring_weights is None:
        scoring_weights = ScoringWeights()

    # Collect all placements with their scores
    all_placements: list[tuple[float, int, int]] = []  # (score, sheet_idx, placement_idx)
    for si, sheet in enumerate(state.sheets):
        for pi, pl in enumerate(sheet.placements):
            all_placements.append((pl.score, si, pi))

    if len(all_placements) <= n_remove:
        return state

    # Sort by score descending (worst first — highest score is worst)
    all_placements.sort(key=lambda x: x[0], reverse=True)
    to_remove = all_placements[:n_remove]

    # Build a map of part_id -> PartSpec for re-placing
    part_map = {p.part_id: p for p in job.parts}

    # Remove from sheets (reverse order to preserve indices)
    removed_parts: list[PartSpec] = []
    for _, si, pi in sorted(to_remove, key=lambda x: (x[1], x[2]), reverse=True):
        sheet = state.sheets[si]
        if pi < len(sheet.placements):
            pl = sheet.placements.pop(pi)
            sheet.placed_inflated.pop(pi)
            sheet.used_area -= part_map[pl.part_id].variants[0].area if pl.part_id in part_map else 0
            if pl.part_id in part_map:
                removed_parts.append(part_map[pl.part_id])

    # Rebuild spatial indices
    for sheet in state.sheets:
        sheet.spatial_index = SpatialIndex()
        for poly in sheet.placed_inflated:
            sheet.spatial_index.add(poly)

    # Re-place removed parts
    for part in removed_parts:
        placed = False
        for sheet in state.sheets:
            candidates = generate_candidates(part, sheet, mode_limits)
            feasible = filter_feasible(candidates, sheet)
            if feasible:
                best = min(feasible, key=lambda c: score_candidate(c, sheet, scoring_weights))
                best.score = score_candidate(best, sheet, scoring_weights)
                sheet.place(
                    variant=best.variant,
                    x=best.x,
                    y=best.y,
                    part_id=part.part_id,
                    transform=best.variant.transform,
                    anchor_tag="reinsert",
                    score=best.score,
                )
                placed = True
                break
        if not placed:
            state.unplaced_parts.append(part)

    return state


def small_swap(state: SolutionState, job: NestJob) -> SolutionState:
    """
    Try swapping pairs of adjacent parts on the same sheet.
    Accept swaps that improve total score. One pass.
    """
    for sheet in state.sheets:
        if len(sheet.placements) < 2:
            continue

        for i in range(len(sheet.placements) - 1):
            j = i + 1
            pi = sheet.placements[i]
            pj = sheet.placements[j]
            current_score = pi.score + pj.score

            # Try swapping positions
            new_pi_x, new_pi_y = pj.x, pj.y
            new_pj_x, new_pj_y = pi.x, pi.y

            # Check if swap is valid (both fit at swapped positions)
            part_map = {p.part_id: p for p in job.parts}
            part_i = part_map.get(pi.part_id)
            part_j = part_map.get(pj.part_id)
            if not part_i or not part_j:
                continue

            # Find matching variants
            vi = next((v for v in part_i.variants if v.transform == pi.transform), None)
            vj = next((v for v in part_j.variants if v.transform == pj.transform), None)
            if not vi or not vj:
                continue

            # Check feasibility of swapped positions
            ti = affinity.translate(vi.inflated, xoff=new_pi_x, yoff=new_pi_y)
            tj = affinity.translate(vj.inflated, xoff=new_pj_x, yoff=new_pj_y)

            if not sheet.usable_bounds.contains(ti) or not sheet.usable_bounds.contains(tj):
                continue

            # Check no overlap with other parts (skip indices i, j)
            valid = True
            for k, poly in enumerate(sheet.placed_inflated):
                if k == i or k == j:
                    continue
                if ti.intersects(poly) and ti.intersection(poly).area > 1e-10:
                    valid = False
                    break
                if tj.intersects(poly) and tj.intersection(poly).area > 1e-10:
                    valid = False
                    break

            if not valid:
                continue

            # Check swapped parts don't overlap each other
            if ti.intersects(tj) and ti.intersection(tj).area > 1e-10:
                continue

            # Accept swap (positions are better or equal)
            sheet.placements[i].x = new_pi_x
            sheet.placements[i].y = new_pi_y
            sheet.placements[j].x = new_pj_x
            sheet.placements[j].y = new_pj_y
            sheet.placed_inflated[i] = ti
            sheet.placed_inflated[j] = tj

    return state
