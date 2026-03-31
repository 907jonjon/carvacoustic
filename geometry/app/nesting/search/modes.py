"""Mode presets — Fast / Balanced / Max Yield over one shared solver."""

from __future__ import annotations

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


MODES: dict[str, ModeConfig] = {
    "fast": ModeConfig(
        name="fast",
        n_seeds=3,
        max_candidates=20,
        max_per_family=8,
        compact_passes=1,
        reinsert_rounds=0,
        reinsert_remove_n=0,
        swap_passes=0,
    ),
    "balanced": ModeConfig(
        name="balanced",
        n_seeds=8,
        max_candidates=60,
        max_per_family=20,
        compact_passes=1,
        reinsert_rounds=1,
        reinsert_remove_n=3,
        swap_passes=1,
    ),
    "max_yield": ModeConfig(
        name="max_yield",
        n_seeds=16,
        max_candidates=100,
        max_per_family=40,
        compact_passes=1,
        reinsert_rounds=3,
        reinsert_remove_n=5,
        swap_passes=2,
    ),
}
