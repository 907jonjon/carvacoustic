"""Anchor-based candidate generation — the heart of V1 search performance."""

from __future__ import annotations

from dataclasses import dataclass

from shapely import affinity
from shapely.geometry import Polygon

from ..geometry.collision import check_collision, check_inside_sheet
from ..geometry.sheet import SheetState
from ..models import PartSpec, VariantGeom


@dataclass
class Candidate:
    variant: VariantGeom
    x: float
    y: float
    anchor_tag: str     # "left-boundary", "bottom-boundary", "flat-edge-contact", "generic-contact"
    score: float = 0.0  # filled in by scorer


MODE_LIMITS = {
    "fast":      {"max_candidates": 20,  "max_per_family": 8},
    "balanced":  {"max_candidates": 60,  "max_per_family": 20},
    "max_yield": {"max_candidates": 100, "max_per_family": 40},
}


def generate_candidates(
    part: PartSpec,
    sheet: SheetState,
    mode_limits: dict,
) -> list[Candidate]:
    """
    Generate placement candidates from three anchor families.
    Returns at most mode_limits["max_candidates"] candidates.
    """
    max_total = mode_limits.get("max_candidates", 60)
    max_per = mode_limits.get("max_per_family", 20)

    all_candidates: list[Candidate] = []

    for variant in part.variants:
        boundary = boundary_anchors(variant, sheet, max_per)
        flat_edge = flat_edge_contact_anchors(variant, sheet, max_per)
        generic = generic_contact_anchors(variant, sheet, max_per)
        all_candidates.extend(boundary)
        all_candidates.extend(flat_edge)
        all_candidates.extend(generic)

    return all_candidates[:max_total]


def boundary_anchors(
    variant: VariantGeom,
    sheet: SheetState,
    max_count: int,
) -> list[Candidate]:
    """
    Slide part along sheet boundaries (bottom, left).
    Place with lowest/leftmost point at boundary, slide in steps.
    """
    candidates: list[Candidate] = []
    bounds = sheet.usable_bounds.bounds  # (minx, miny, maxx, maxy)
    vb = variant.inflated.bounds  # variant bounds (centred)

    v_w = vb[2] - vb[0]
    v_h = vb[3] - vb[1]

    # Offset to place variant's min at sheet's min
    base_ox = bounds[0] - vb[0]
    base_oy = bounds[1] - vb[1]

    # Bottom boundary: slide X across sheet
    step_x = max(v_w / 4.0, 0.1)
    x = base_ox
    count = 0
    while x + vb[2] <= bounds[2] + 0.01 and count < max_count // 2:
        candidates.append(
            Candidate(variant=variant, x=x, y=base_oy, anchor_tag="bottom-boundary")
        )
        x += step_x
        count += 1

    # Left boundary: slide Y up the sheet
    step_y = max(v_h / 4.0, 0.1)
    y = base_oy
    count = 0
    while y + vb[3] <= bounds[3] + 0.01 and count < max_count // 2:
        candidates.append(
            Candidate(variant=variant, x=base_ox, y=y, anchor_tag="left-boundary")
        )
        y += step_y
        count += 1

    return candidates[:max_count]


def flat_edge_contact_anchors(
    variant: VariantGeom,
    sheet: SheetState,
    max_count: int,
) -> list[Candidate]:
    """
    Align part's preferred flat edge against exposed edges of placed parts.
    Slide along contact edge in steps.
    """
    if not variant.preferred_edges or not sheet.placed_inflated:
        return []

    candidates: list[Candidate] = []
    vb = variant.inflated.bounds

    for placed_poly in sheet.placed_inflated:
        pb = placed_poly.bounds
        # Place to the right of placed part, aligned at bottom
        x = pb[2] - vb[0]
        y = pb[1] - vb[1]
        candidates.append(
            Candidate(variant=variant, x=x, y=y, anchor_tag="flat-edge-contact")
        )

        # Place above placed part, aligned at left
        x = pb[0] - vb[0]
        y = pb[3] - vb[1]
        candidates.append(
            Candidate(variant=variant, x=x, y=y, anchor_tag="flat-edge-contact")
        )

        if len(candidates) >= max_count:
            break

    return candidates[:max_count]


def generic_contact_anchors(
    variant: VariantGeom,
    sheet: SheetState,
    max_count: int,
) -> list[Candidate]:
    """
    Touch candidate against bounding box corners of placed parts.
    Place at (placed_max_x, placed_y) and (placed_x, placed_max_y).
    """
    if not sheet.placed_inflated:
        return []

    candidates: list[Candidate] = []
    vb = variant.inflated.bounds

    for placed_poly in sheet.placed_inflated:
        pb = placed_poly.bounds

        # Right side of placed part
        x = pb[2] - vb[0]
        y = pb[1] - vb[1]
        candidates.append(
            Candidate(variant=variant, x=x, y=y, anchor_tag="generic-contact")
        )

        # Top of placed part
        x = pb[0] - vb[0]
        y = pb[3] - vb[1]
        candidates.append(
            Candidate(variant=variant, x=x, y=y, anchor_tag="generic-contact")
        )

        # Top-right corner
        x = pb[2] - vb[0]
        y = pb[3] - vb[1]
        candidates.append(
            Candidate(variant=variant, x=x, y=y, anchor_tag="generic-contact")
        )

        if len(candidates) >= max_count:
            break

    return candidates[:max_count]


def filter_feasible(
    candidates: list[Candidate],
    sheet: SheetState,
) -> list[Candidate]:
    """Filter candidates to those that are inside sheet and don't collide."""
    feasible: list[Candidate] = []
    for c in candidates:
        # Check sheet containment
        if not check_inside_sheet(c.variant.inflated, c.x, c.y, sheet.usable_bounds):
            continue
        # Broad phase: query spatial hash
        translated = affinity.translate(c.variant.inflated, xoff=c.x, yoff=c.y)
        nearby = sheet.spatial_index.query_nearby(translated)
        # Exact collision check against nearby
        if nearby and check_collision(c.variant.prepared_inflated, c.x, c.y, nearby):
            continue
        feasible.append(c)
    return feasible
