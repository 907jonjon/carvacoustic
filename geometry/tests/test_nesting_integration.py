"""
Tests for nesting engine Phase 2 — end-to-end integration.
5 test cases.
"""

from __future__ import annotations

import math

import numpy as np
import pytest
from shapely.geometry import box

from app.models import CanonicalConfig
from app.geometry.layout import LayoutResult
from app.nesting.ingest import (
    prepare_nest_job,
    nest_result_to_layout_result,
    run_nesting,
)
from app.nesting.solver.solve import solve_nest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_config() -> CanonicalConfig:
    """Minimal valid v2 config for testing."""
    return CanonicalConfig(**{
        "schema_version": "2.0.0",
        "project": {"name": "Test", "mode": "wall_art", "units": "in"},
        "boundary": {
            "type": "rectangle", "width": 48, "height": 36,
            "corner_radius": 0, "safe_margin": 1.0,
        },
        "surface": {
            "type": "wave", "max_depth": 3.0, "min_depth": 0.0,
            "amplitude": 0.7, "frequency": 3.0, "phase": 0.0,
            "flow_direction": "x", "symmetry": "none",
            "smoothness": 0.5, "seed": 42, "noise_amount": 0.2,
        },
        "slats": {
            "count": 10, "spacing": 3.5, "thickness": 0.75,
            "base_height": 1.5, "tab_width": 0.5, "tab_depth": 0.75,
            "tab_count": 3, "tab_clearance": 0.01,
        },
        "backing": {
            "enabled": True, "width": 48, "height": 3,
            "slot_width": 0.51, "slot_depth": 0.75, "mounting_holes": True,
        },
        "fabrication": {
            "material": {
                "thickness": 0.75, "sheet_width": 96, "sheet_height": 48,
                "min_bridge": 0.3, "grain_direction": "x",
            },
            "tool": {
                "tool_diameter": 0.25, "kerf_allowance": 0.0,
                "min_inside_radius": 0.125, "dogbone_style": "classic",
                "clearance": 0.125, "border_gap": 0.75,
            },
        },
        "layout": {
            "enabled": True, "copies": 1,
            "rotation_mode": "90_only", "preserve_grain": False,
        },
        "labeling": {"enabled": False, "prefix": "P", "position": "footer"},
        "export": {"formats": ["svg"], "units": "in"},
    })


def _make_slat_parts(config: CanonicalConfig, n: int = 5) -> list[dict]:
    """Create synthetic slat-profiler-style part dicts."""
    parts = []
    for i in range(n):
        # Simple slat-like shape: wide rectangle with a bump on top
        w = 10.0
        h = 3.0
        top_pts = [(w * j / 20.0, h + 0.5 * math.sin(math.pi * j / 20.0)) for j in range(21)]
        coords = top_pts + [(w, 0), (0, 0)]
        from shapely.geometry import Polygon
        poly = Polygon(coords)
        parts.append({
            "part_id": f"S{i + 1:03d}",
            "part_type": "slat",
            "polygon": poly,
            "profile_heights": np.zeros(21),
            "slat_index": i,
            "bounding_box": poly.bounds,
            "area": poly.area,
            "tab_positions": [2.5, 5.0, 7.5],
        })
    return parts


# ---------------------------------------------------------------------------
# 1. test_solve_nest_returns_nest_result
# ---------------------------------------------------------------------------


def test_solve_nest_returns_nest_result():
    config = _make_config()
    parts = _make_slat_parts(config, n=5)
    job = prepare_nest_job(parts, config, mode="fast")
    result = solve_nest(job, mode="fast", seed=42)

    from app.nesting.models import NestResult
    assert isinstance(result, NestResult)
    assert result.sheets_used >= 1
    assert result.elapsed_ms >= 0


# ---------------------------------------------------------------------------
# 2. test_nest_result_to_layout_result
# ---------------------------------------------------------------------------


def test_nest_result_to_layout_result():
    config = _make_config()
    parts = _make_slat_parts(config, n=5)
    job = prepare_nest_job(parts, config, mode="fast")
    result = solve_nest(job, mode="fast", seed=42)

    layout = nest_result_to_layout_result(result, parts, job)
    assert isinstance(layout, LayoutResult)
    assert len(layout.sheets) >= 1
    # Total placed parts should match
    total_placed = sum(len(s.placements) for s in layout.sheets)
    assert total_placed == len(result.placements)


# ---------------------------------------------------------------------------
# 3. test_run_nesting_returns_layout_result
# ---------------------------------------------------------------------------


def test_run_nesting_returns_layout_result():
    config = _make_config()
    parts = _make_slat_parts(config, n=5)
    layout = run_nesting(parts, config, mode="fast")

    assert isinstance(layout, LayoutResult)
    assert len(layout.sheets) >= 1
    total = sum(len(s.placements) for s in layout.sheets) + layout.overflow
    assert total == 5


# ---------------------------------------------------------------------------
# 4. test_full_pipeline_with_nesting
# ---------------------------------------------------------------------------


def test_full_pipeline_with_nesting():
    """Pipeline run_pipeline() should use the nesting engine and produce valid output."""
    pytest.importorskip("scipy", reason="scipy required for full pipeline test")
    config = _make_config()
    from app.geometry.pipeline import run_pipeline
    result = run_pipeline(config)

    assert result.status == "ok"
    assert result.sheet_count >= 1
    assert result.slat_count > 0


# ---------------------------------------------------------------------------
# 5. test_fallback_to_ffd
# ---------------------------------------------------------------------------


def test_fallback_to_ffd():
    """If nesting engine raises, run_nesting should fall back to FFD."""
    config = _make_config()
    parts = _make_slat_parts(config, n=3)

    # Monkey-patch solve_nest to raise
    import app.nesting.solver.solve as solve_mod
    original = solve_mod.solve_nest

    def _broken_solve(*a, **kw):
        raise RuntimeError("intentional test failure")

    solve_mod.solve_nest = _broken_solve
    try:
        layout = run_nesting(parts, config)
        assert isinstance(layout, LayoutResult)
        assert len(layout.sheets) >= 1
    finally:
        solve_mod.solve_nest = original
