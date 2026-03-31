"""Test nesting engine with realistic slat polygons."""
import pytest
from shapely.geometry import Polygon, box
from shapely import affinity

def make_wavy_slat(width=1.6, base_height=4.0, peak=8.0, n_points=50):
    """Create a realistic concave slat polygon with a wavy top profile."""
    import math
    bottom_pts = [(0, 0), (width, 0)]
    top_pts = []
    for i in range(n_points + 1):
        x = width * i / n_points
        y = base_height + (peak - base_height) * math.sin(math.pi * x / width)
        top_pts.append((x, y))
    top_pts.reverse()
    coords = bottom_pts + top_pts
    coords.append(coords[0])  # close ring
    return Polygon(coords)

def make_test_parts(n_slats=10, width=48.0):
    """Generate n_slats realistic slat parts spread across a panel width."""
    parts = []
    slat_width = width / n_slats
    for i in range(n_slats):
        import random
        random.seed(i)
        peak = 4.0 + random.random() * 6.0  # 4-10 inches
        poly = make_wavy_slat(width=slat_width, base_height=2.0, peak=peak)
        parts.append({
            "part_id": f"S{i+1:03d}",
            "part_type": "slat",
            "polygon": poly,
            "bounding_box": poly.bounds,
            "area": poly.area,
        })
    return parts

class FakeRotMode:
    value = "90_only"

class FakeConfig:
    class fabrication:
        class material:
            sheet_width = 48.0
            sheet_height = 96.0
            thickness = 0.75
            grain_direction = None
        class tool:
            clearance = 0.25
            border_gap = 1.0
            tool_diameter = 0.25
    class layout:
        rotation_mode = FakeRotMode()
        preserve_grain = False
        copies = 1
        enabled = True

def test_nesting_with_wavy_slats():
    from app.nesting.ingest import run_nesting
    parts = make_test_parts(n_slats=15)
    config = FakeConfig()
    result = run_nesting(parts, config)
    # Should not be empty
    assert result.sheets, "No sheets produced"
    # Check engine attribute
    engine = getattr(result, 'engine', 'unknown')
    print(f"Engine used: {engine}")
    print(f"Sheets: {len(result.sheets)}, Overflow: {result.overflow}")
    for s in result.sheets:
        print(f"  Sheet {s.sheet_index}: {len(s.placements)} parts, {s.utilization:.1%} util")
    # The real test: did the nesting engine run, or did it fall back?
    assert engine == "nesting", f"Expected nesting engine but got {engine}"

def test_nesting_inflate_concave():
    """Verify inflate_part handles concave polygons without producing MultiPolygon."""
    from app.nesting.geometry.offsets import inflate_part
    from shapely.geometry import MultiPolygon
    poly = make_wavy_slat(width=1.6, base_height=2.0, peak=8.0, n_points=100)
    inflated = inflate_part(poly, clearance=0.25)
    assert not isinstance(inflated, MultiPolygon), \
        f"inflate_part produced MultiPolygon with {len(inflated.geoms)} parts"
    assert inflated.is_valid, "Inflated polygon is invalid"

def test_nesting_contract_sheet():
    """Verify contract_sheet produces a valid polygon."""
    from app.nesting.geometry.offsets import contract_sheet
    from app.nesting.models import SheetSpec
    sheet = SheetSpec(width=48.0, height=96.0, edge_margin=1.0, grain_axis=None)
    contracted = contract_sheet(sheet, clearance=0.25)
    assert contracted.is_valid
    assert contracted.area > 0
    # Usable area should be smaller than full sheet
    assert contracted.area < 48.0 * 96.0

def test_nesting_candidate_generation_with_concave():
    """Verify candidates are generated for concave parts."""
    from app.nesting.ingest import prepare_nest_job
    from app.nesting.search.constructive import constructive_solve
    from app.nesting.search.modes import MODES
    from app.nesting.search.scoring import ScoringWeights

    parts = make_test_parts(n_slats=5)
    config = FakeConfig()
    job = prepare_nest_job(parts, config, mode="fast")

    mode_cfg = MODES["fast"]
    weights = ScoringWeights()

    # This is where it likely fails — let it throw naturally
    solution = constructive_solve(
        job, job.parts,
        {"max_candidates": mode_cfg.max_candidates, "max_per_family": mode_cfg.max_per_family},
        weights,
    )
    placed_count = sum(len(s.placements) for s in solution.sheets)
    print(f"Placed {placed_count} / {len(parts)} parts on {len(solution.sheets)} sheets")
    assert placed_count > 0, "No parts were placed by constructive solver"
