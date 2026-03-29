"""
v2 slat pipeline tests — spec DELTA-02 §Part D.
"""

from __future__ import annotations

import pytest

from app.geometry.height_field import generate_height_field
from app.geometry.pipeline import run_pipeline, run_pipeline_internal
from app.geometry.slat_profiler import generate_backing_board, generate_slat_profiles
from app.models import BackingConfig, CanonicalConfig, SlatConfig, SurfaceConfig


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def v2_config():
    return CanonicalConfig.model_validate({
        "schema_version": "2.0.0",
        "project": {"name": "Test Slat Panel", "mode": "wall_art", "units": "in"},
        "boundary": {
            "type": "rectangle", "width": 24, "height": 18,
            "corner_radius": 0, "asset_id": None, "safe_margin": 0.5,
        },
        "surface": {
            "type": "wave", "max_depth": 2.0, "min_depth": 0.0,
            "amplitude": 0.8, "frequency": 3.0, "phase": 0.0,
            "flow_direction": "x", "symmetry": "none",
            "smoothness": 0.3, "seed": 42, "noise_amount": 0.1,
        },
        "slats": {
            "count": 10, "spacing": 0.75, "thickness": 0.75,
            "base_height": 1.5, "tab_width": 0.5, "tab_depth": 0.75,
            "tab_count": 3, "tab_clearance": 0.01,
        },
        "backing": {
            "enabled": True, "width": 24.0, "height": 3.0,
            "slot_width": 0.76, "slot_depth": 0.75, "mounting_holes": True,
        },
        "fabrication": {
            "material": {
                "thickness": 0.75, "sheet_width": 48, "sheet_height": 24,
                "min_bridge": 0.3, "grain_direction": "x",
            },
            "tool": {
                "tool_diameter": 0.25, "kerf_allowance": 0.0,
                "min_inside_radius": 0.125, "dogbone_style": "classic",
                "clearance": 0.125, "border_gap": 0.5,
            },
        },
        "layout": {"enabled": True, "copies": 1, "rotation_mode": "90_only", "preserve_grain": False},
        "labeling": {"enabled": True, "prefix": "S", "position": "footer"},
        "export": {"formats": ["dxf", "svg"], "units": "in"},
        "reserved_acoustic": {
            "enabled": False, "room_use": None, "target_issue": None,
            "room_dimensions": None, "surface_summary": None,
            "installation_constraints": None, "attachments": [],
        },
    })


# ---------------------------------------------------------------------------
# Slat profiler tests
# ---------------------------------------------------------------------------

def test_slat_count(v2_config):
    """Correct number of slats generated."""
    surface = v2_config.surface
    x_vals, heights = generate_height_field(surface, v2_config.boundary.width, v2_config.slats.count)
    parts = generate_slat_profiles(x_vals, heights, v2_config.slats, v2_config.fabrication)
    assert len(parts) == v2_config.slats.count


def test_slat_polygons_valid(v2_config):
    """All slat polygons are valid and non-empty."""
    x_vals, heights = generate_height_field(v2_config.surface, v2_config.boundary.width, v2_config.slats.count)
    parts = generate_slat_profiles(x_vals, heights, v2_config.slats, v2_config.fabrication)
    for part in parts:
        poly = part["polygon"]
        assert not poly.is_empty
        assert poly.area > 0
        # is_valid or can be made valid with buffer(0)
        assert poly.is_valid or poly.buffer(0).is_valid


def test_slat_part_ids(v2_config):
    """Parts are labelled S001, S002, …"""
    x_vals, heights = generate_height_field(v2_config.surface, v2_config.boundary.width, v2_config.slats.count)
    parts = generate_slat_profiles(x_vals, heights, v2_config.slats, v2_config.fabrication)
    ids = [p["part_id"] for p in parts]
    assert ids[0] == "S001"
    assert ids[-1] == f"S{v2_config.slats.count:03d}"


def test_tab_count(v2_config):
    """Each slat has the correct number of tab positions."""
    x_vals, heights = generate_height_field(v2_config.surface, v2_config.boundary.width, v2_config.slats.count)
    parts = generate_slat_profiles(x_vals, heights, v2_config.slats, v2_config.fabrication)
    for part in parts:
        assert len(part["tab_positions"]) == v2_config.slats.tab_count


def test_backing_board_generated(v2_config):
    """Backing board is generated when enabled."""
    x_vals, heights = generate_height_field(v2_config.surface, v2_config.boundary.width, v2_config.slats.count)
    backing = generate_backing_board(v2_config.backing, v2_config.slats, v2_config.slats.count)
    assert backing is not None
    assert backing["part_id"] == "BACK-01"
    assert backing["slot_count"] == v2_config.slats.count
    assert backing["polygon"].area > 0


def test_backing_disabled():
    """No backing board when disabled."""
    backing_cfg = BackingConfig(enabled=False)
    slat_cfg = SlatConfig()
    result = generate_backing_board(backing_cfg, slat_cfg, 10)
    assert result is None


# ---------------------------------------------------------------------------
# Pipeline tests
# ---------------------------------------------------------------------------

def test_pipeline_returns_ok(v2_config):
    """run_pipeline returns status=ok for a valid v2 config."""
    result = run_pipeline(v2_config)
    assert result.status == "ok"
    assert result.part_count > 0
    assert result.slat_count == v2_config.slats.count
    assert result.has_backing is True
    assert result.svg_preview.startswith("<svg")


def test_pipeline_deterministic(v2_config):
    """Same config always produces the same part count and SVG."""
    r1 = run_pipeline(v2_config)
    r2 = run_pipeline(v2_config)
    assert r1.part_count == r2.part_count
    assert r1.svg_preview == r2.svg_preview


def test_pipeline_internal_parts(v2_config):
    """run_pipeline_internal returns parts list with slat polygons."""
    result = run_pipeline_internal(v2_config)
    assert len(result["slat_parts"]) == v2_config.slats.count
    assert result["backing"] is not None
    assert len(result["parts"]) == v2_config.slats.count + 1  # slats + backing


def test_pipeline_returns_cut_preview(v2_config):
    """run_pipeline returns a cut preview SVG with sheet layout info."""
    result = run_pipeline(v2_config)
    assert result.cut_preview_svg.startswith("<svg")
    assert result.sheet_count >= 1
    assert result.sheet_utilization > 0


def test_v1_config_auto_migrates():
    """A v1 config sent to run_pipeline is auto-migrated and still produces output."""
    v1_dict = {
        "schema_version": "1.0.0",
        "project": {"name": "Legacy Panel", "mode": "wall_art", "units": "in"},
        "boundary": {
            "type": "rectangle", "width": 24, "height": 18,
            "corner_radius": 0, "asset_id": None, "safe_margin": 0.5,
        },
        "pattern": {
            "family": "wave_field", "density": 0.5, "spacing": 1.2,
            "line_width": 0.4, "amplitude": 0.8, "seed": 42, "symmetry": "none",
        },
        "fabrication": {
            "material": {
                "thickness": 0.75, "sheet_width": 48, "sheet_height": 24,
                "min_bridge": 0.3, "grain_direction": "x",
            },
            "tool": {
                "tool_diameter": 0.25, "kerf_allowance": 0.0,
                "min_inside_radius": 0.125, "dogbone_style": "classic",
                "clearance": 0.125, "border_gap": 0.5,
            },
        },
        "layout": {"enabled": True, "copies": 1, "rotation_mode": "90_only", "preserve_grain": False},
        "labeling": {"enabled": True, "prefix": "P", "position": "footer"},
        "export": {"formats": ["dxf"], "units": "in"},
        "reserved_acoustic": {
            "enabled": False, "room_use": None, "target_issue": None,
            "room_dimensions": None, "surface_summary": None,
            "installation_constraints": None, "attachments": [],
        },
    }
    config = CanonicalConfig.model_validate(v1_dict)
    assert config.schema_version == "2.0.0"
    assert config.surface is not None
    assert config.slats is not None

    result = run_pipeline(config)
    assert result.status == "ok"
    assert result.slat_count > 0
