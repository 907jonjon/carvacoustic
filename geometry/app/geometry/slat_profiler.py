"""
Slat profiler — converts a height field into individual slat cut profiles.

Each slat is a closed 2D Shapely Polygon with:
  - Top edge:    profile curve derived from the height field row
  - Base:        rectangular section below the profile for structural rigidity
  - Tabs:        rectangular protrusions below the base for mounting to backing board

The polygon's coordinate space:
  x: 0 → boundary_width (slat length)
  y: -tab_depth → base_height + max_profile_height
"""

from __future__ import annotations

import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from ..models import BackingConfig, ConfigFabrication, SlatConfig


def generate_slat_profiles(
    x_vals: np.ndarray,
    heights: np.ndarray,
    slat_config: SlatConfig,
    fab_config: ConfigFabrication,
) -> list[dict]:
    """
    Generate flat 2D Shapely polygons for each slat.

    Returns list of dicts:
      part_id        — "S001", "S002", …
      part_type      — "slat"
      polygon        — Shapely Polygon
      profile_heights — 1D array of Z heights for this slat
      slat_index     — int (0-based)
      bounding_box   — (minx, miny, maxx, maxy)
      area           — float
      tab_positions  — list of float (x-centres of tabs)
    """
    parts = []
    n_slats = heights.shape[0]
    base_h = slat_config.base_height
    tab_w = slat_config.tab_width
    tab_d = slat_config.tab_depth

    tab_positions = _compute_tab_positions(
        total_width=float(x_vals[-1]),
        tab_count=slat_config.tab_count,
        tab_width=tab_w,
        border_inset=float(x_vals[-1]) * 0.1,
    )

    for i in range(n_slats):
        profile = heights[i]

        # Top edge: profile curve left → right
        top_points = [
            (float(x_vals[j]), base_h + float(profile[j]))
            for j in range(len(x_vals))
        ]

        # Right edge: down to baseline
        right_x = float(x_vals[-1])
        left_x = float(x_vals[0])

        # Bottom edge with tab notches, traversed right → left
        bottom: list[tuple[float, float]] = [(right_x, 0.0)]
        for tx_center in sorted(tab_positions, reverse=True):
            tx_left = tx_center - tab_w / 2.0
            tx_right = tx_center + tab_w / 2.0
            bottom.append((tx_right, 0.0))
            bottom.append((tx_right, -tab_d))
            bottom.append((tx_left, -tab_d))
            bottom.append((tx_left, 0.0))
        bottom.append((left_x, 0.0))

        # Assemble: top (L→R), right down to base, bottom (R→L), left up to start
        all_points = (
            top_points
            + [(right_x, base_h), (right_x, 0.0)]
            + bottom[1:]
            + [(left_x, base_h), top_points[0]]
        )

        try:
            polygon = Polygon(all_points)
            if not polygon.is_valid:
                polygon = polygon.buffer(0)
        except Exception:
            polygon = box(left_x, -tab_d, right_x, base_h + float(profile.max()))

        parts.append({
            "part_id": f"S{i + 1:03d}",
            "part_type": "slat",
            "polygon": polygon,
            "profile_heights": profile,
            "slat_index": i,
            "bounding_box": polygon.bounds,
            "area": polygon.area,
            "tab_positions": tab_positions,
        })

    return parts


def generate_backing_board(
    backing_config: BackingConfig,
    slat_config: SlatConfig,
    n_slats: int,
) -> dict | None:
    """
    Generate the backing board polygon with slots for slat tabs.
    Returns None if backing is disabled.
    """
    if not backing_config.enabled:
        return None

    w = backing_config.width
    h = backing_config.height
    board = box(0.0, 0.0, w, h)

    total_slat_span = (n_slats - 1) * slat_config.spacing
    start_x = (w - total_slat_span) / 2.0

    slots = []
    for i in range(n_slats):
        cx = start_x + i * slat_config.spacing
        slot = box(
            cx - backing_config.slot_width / 2.0,
            0.0,
            cx + backing_config.slot_width / 2.0,
            backing_config.slot_depth,
        )
        slots.append(slot)

    if slots:
        board = board.difference(unary_union(slots))

    return {
        "part_id": "BACK-01",
        "part_type": "backing",
        "polygon": board,
        "bounding_box": board.bounds,
        "area": board.area,
        "slot_count": n_slats,
    }


def _compute_tab_positions(
    total_width: float,
    tab_count: int,
    tab_width: float,
    border_inset: float,
) -> list[float]:
    """Evenly-spaced tab centre positions along the slat bottom."""
    usable = total_width - 2.0 * border_inset
    if tab_count <= 1:
        return [total_width / 2.0]
    return [
        border_inset + i * usable / (tab_count - 1)
        for i in range(tab_count)
    ]
