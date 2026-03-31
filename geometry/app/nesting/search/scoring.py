"""Weighted placement scorer — normalized, configurable weights."""

from __future__ import annotations

from dataclasses import dataclass

from shapely import affinity

from ..geometry.sheet import SheetState
from .candidates import Candidate


@dataclass
class ScoringWeights:
    """Scoring weights — lower total score = better placement."""
    envelope_growth: float = 1.0     # penalty for expanding used envelope
    max_x_growth: float = 0.5        # penalty for rightward expansion
    max_y_growth: float = 0.5        # penalty for upward expansion
    contact_length: float = -0.8     # bonus for flush contact with sheet/parts
    preferred_edge: float = -0.6     # bonus for flat-edge alignment


def score_candidate(
    candidate: Candidate,
    sheet: SheetState,
    weights: ScoringWeights | None = None,
) -> float:
    """
    Score a feasible candidate placement. Lower score = better.
    All geometric measures normalized by sheet dimensions.
    """
    if weights is None:
        weights = ScoringWeights()

    bounds = sheet.usable_bounds.bounds
    sheet_w = bounds[2] - bounds[0]
    sheet_h = bounds[3] - bounds[1]

    translated = affinity.translate(
        candidate.variant.inflated, xoff=candidate.x, yoff=candidate.y
    )
    cb = translated.bounds

    # Current envelope of placed parts
    if sheet.placed_inflated:
        cur_max_x = max(p.bounds[2] for p in sheet.placed_inflated)
        cur_max_y = max(p.bounds[3] for p in sheet.placed_inflated)
    else:
        cur_max_x = bounds[0]
        cur_max_y = bounds[1]

    # Envelope growth after placing this candidate
    new_max_x = max(cur_max_x, cb[2])
    new_max_y = max(cur_max_y, cb[3])

    dx = (new_max_x - cur_max_x) / sheet_w if sheet_w > 0 else 0
    dy = (new_max_y - cur_max_y) / sheet_h if sheet_h > 0 else 0

    envelope = (dx * dy)  # normalized area growth

    score = 0.0
    score += weights.envelope_growth * envelope
    score += weights.max_x_growth * dx
    score += weights.max_y_growth * dy

    # Contact length bonus: shared boundary with placed parts
    contact_ratio = 0.0
    if sheet.placed_inflated:
        perimeter = translated.length
        for placed in sheet.placed_inflated:
            if translated.distance(placed) < 1e-6:
                shared = translated.intersection(placed)
                if hasattr(shared, "length"):
                    contact_ratio += shared.length / perimeter if perimeter > 0 else 0
    score += weights.contact_length * min(contact_ratio, 1.0)

    # Preferred edge bonus
    if candidate.variant.preferred_edges:
        if candidate.anchor_tag in ("bottom-boundary", "left-boundary", "flat-edge-contact"):
            score += weights.preferred_edge * 0.5

    return score
