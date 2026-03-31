"""Post-solve validation — independently verify a nesting result."""

from __future__ import annotations

from shapely import affinity
from shapely.geometry import Polygon

from ..models import NestJob, NestResult, PartSpec, TransformSpec
from .offsets import contract_sheet, inflate_part
from .transforms import apply_transform


def validate_solution(
    job: NestJob,
    result: NestResult,
    parts: list[PartSpec],
) -> list[str]:
    """
    Independently validate a nesting result. Returns list of error strings.
    Empty list = valid.

    Checks:
    1. No overlaps between any pair of placed inflated polygons
    2. All placed parts inside contracted sheet bounds
    3. All transforms are from the part's legal transform set
    4. All parts accounted for (placed + unplaced = total)
    """
    errors: list[str] = []
    usable_bounds = contract_sheet(job.sheets, job.clearance)

    # Build lookup: part_id -> PartSpec
    part_map = {p.part_id: p for p in parts}

    # Materialise placed inflated polygons
    placed_polys: list[tuple[str, Polygon]] = []
    placed_ids: list[str] = []

    for pl in result.placements:
        spec = part_map.get(pl.part_id)
        if spec is None:
            errors.append(f"Unknown part_id in placement: {pl.part_id}")
            continue

        # Find the matching variant
        matching = [v for v in spec.variants if v.transform == pl.transform]
        if not matching:
            errors.append(
                f"Illegal transform for {pl.part_id}: "
                f"angle={pl.transform.angle_deg}, mirrored={pl.transform.mirrored}"
            )
            continue

        variant = matching[0]
        translated = affinity.translate(variant.inflated, xoff=pl.x, yoff=pl.y)

        # Check 2: inside sheet bounds
        if not usable_bounds.contains(translated):
            errors.append(
                f"{pl.part_id} at ({pl.x:.2f}, {pl.y:.2f}) is outside sheet bounds"
            )

        placed_polys.append((pl.part_id, translated))
        placed_ids.append(pl.part_id)

    # Check 1: pairwise overlap
    for i in range(len(placed_polys)):
        for j in range(i + 1, len(placed_polys)):
            id_a, poly_a = placed_polys[i]
            id_b, poly_b = placed_polys[j]
            if poly_a.intersects(poly_b):
                overlap = poly_a.intersection(poly_b)
                if overlap.area > 1e-10:
                    errors.append(
                        f"Overlap between {id_a} and {id_b} "
                        f"(area={overlap.area:.6f})"
                    )

    # Check 4: all parts accounted for
    total_expected = sum(p.quantity for p in parts)
    total_placed = len(result.placements)
    total_unplaced = len(result.unplaced)
    if total_placed + total_unplaced != total_expected:
        errors.append(
            f"Part count mismatch: {total_placed} placed + {total_unplaced} unplaced "
            f"!= {total_expected} expected"
        )

    return errors
