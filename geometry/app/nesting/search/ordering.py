"""Seeded part orderings for diversified constructive search."""

from __future__ import annotations

import random

from ..models import PartSpec


def generate_orderings(
    parts: list[PartSpec],
    mode: str,
    seed: int | None = None,
) -> list[list[PartSpec]]:
    """
    Generate multiple seeded part orderings for the constructive solver.

    Orderings:
    1. Area descending (largest parts first)
    2. Longest extent descending (max of width, height of bounding box)
    3. Awkwardness descending (bounding box area / polygon area — less regular = higher)
    4+ Randomized perturbations of ordering #1

    Number of orderings by mode:
    - fast: 3
    - balanced: 8
    - max_yield: 16
    """
    n_seeds = {"fast": 3, "balanced": 8, "max_yield": 16}.get(mode, 3)

    orderings: list[list[PartSpec]] = []

    # 1. Area descending
    by_area = sorted(parts, key=lambda p: _part_area(p), reverse=True)
    orderings.append(by_area)

    # 2. Longest extent descending
    by_extent = sorted(parts, key=lambda p: _part_extent(p), reverse=True)
    orderings.append(by_extent)

    # 3. Awkwardness descending (bbox area / polygon area)
    by_awkward = sorted(parts, key=lambda p: _part_awkwardness(p), reverse=True)
    orderings.append(by_awkward)

    # 4+ Randomized perturbations of area-descending
    rng = random.Random(seed if seed is not None else 42)
    while len(orderings) < n_seeds:
        shuffled = list(by_area)
        rng.shuffle(shuffled)
        orderings.append(shuffled)

    return orderings[:n_seeds]


def _part_area(p: PartSpec) -> float:
    if p.variants:
        return p.variants[0].area
    return p.original_polygon.area


def _part_extent(p: PartSpec) -> float:
    poly = p.variants[0].polygon if p.variants else p.original_polygon
    b = poly.bounds
    return max(b[2] - b[0], b[3] - b[1])


def _part_awkwardness(p: PartSpec) -> float:
    poly = p.variants[0].polygon if p.variants else p.original_polygon
    b = poly.bounds
    bbox_area = (b[2] - b[0]) * (b[3] - b[1])
    poly_area = poly.area
    return bbox_area / poly_area if poly_area > 0 else float("inf")
