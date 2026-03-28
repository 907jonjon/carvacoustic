"""
Tests for normalize_config — Prompt 03: Geometry Source of Truth Fix.
"""

from __future__ import annotations

import math

import pytest

from app.geometry.pipeline import run_pipeline
from app.models import CanonicalConfig, normalize_config


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_config(**overrides) -> CanonicalConfig:
    """Build a valid v2 config with optional overrides merged into slats/boundary/fabrication."""
    base = {
        "schema_version": "2.0.0",
        "project": {"name": "SoT Test", "mode": "wall_art", "units": "in"},
        "boundary": {
            "type": "rectangle", "width": 48, "height": 24,
            "corner_radius": 0, "asset_id": None, "safe_margin": 0.5,
        },
        "surface": {
            "type": "wave", "max_depth": 3.0, "min_depth": 0.0,
            "amplitude": 0.7, "frequency": 3.0, "phase": 0.0,
            "flow_direction": "x", "symmetry": "none",
            "smoothness": 0.5, "seed": 42, "noise_amount": 0.2,
        },
        "slats": {
            "count": 30, "spacing": 0.75, "thickness": 0.75,
            "base_height": 1.5, "tab_width": 0.5, "tab_depth": 0.75,
            "tab_count": 3, "tab_clearance": 0.01,
            "distribution_mode": "fit_to_boundary",
        },
        "backing": {
            "enabled": True, "width": 48.0, "height": 3.0,
            "slot_width": 0.76, "slot_depth": 0.75, "mounting_holes": True,
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
        "layout": {"enabled": True, "copies": 1, "rotation_mode": "90_only", "preserve_grain": False},
        "labeling": {"enabled": True, "prefix": "S", "position": "footer"},
        "export": {"formats": ["dxf", "svg"], "units": "in"},
        "reserved_acoustic": {
            "enabled": False, "room_use": None, "target_issue": None,
            "room_dimensions": None, "surface_summary": None,
            "installation_constraints": None, "attachments": [],
        },
    }
    # Apply overrides
    for key, val in overrides.items():
        if key in base and isinstance(base[key], dict) and isinstance(val, dict):
            base[key].update(val)
        else:
            base[key] = val
    return CanonicalConfig.model_validate(base)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_fit_to_boundary_spacing():
    """fit_to_boundary mode recomputes spacing from boundary height."""
    cfg = _make_config(
        boundary={
            "type": "rectangle", "width": 48, "height": 24,
            "corner_radius": 0, "asset_id": None, "safe_margin": 0.5,
        },
        slats={
            "count": 30, "spacing": 0.75, "thickness": 0.75,
            "base_height": 1.5, "tab_width": 0.5, "tab_depth": 0.75,
            "tab_count": 3, "tab_clearance": 0.01,
            "distribution_mode": "fit_to_boundary",
        },
    )
    normalized = normalize_config(cfg)
    expected = (24 - 1.0) / 29
    assert math.isclose(normalized.slats.spacing, expected, rel_tol=1e-9)


def test_manual_spacing_preserved():
    """Manual mode keeps the user-supplied spacing value."""
    cfg = _make_config(
        slats={
            "count": 30, "spacing": 1.5, "thickness": 0.75,
            "base_height": 1.5, "tab_width": 0.5, "tab_depth": 0.75,
            "tab_count": 3, "tab_clearance": 0.01,
            "distribution_mode": "manual",
        },
    )
    normalized = normalize_config(cfg)
    assert normalized.slats.spacing == 1.5


def test_thickness_synced_from_material():
    """Slat thickness is always synced from fabrication.material.thickness."""
    cfg = _make_config(
        slats={
            "count": 30, "spacing": 0.75, "thickness": 0.9,
            "base_height": 1.5, "tab_width": 0.5, "tab_depth": 0.75,
            "tab_count": 3, "tab_clearance": 0.01,
            "distribution_mode": "manual",
        },
        fabrication={
            "material": {
                "thickness": 0.5, "sheet_width": 96, "sheet_height": 48,
                "min_bridge": 0.3, "grain_direction": "x",
            },
            "tool": {
                "tool_diameter": 0.25, "kerf_allowance": 0.0,
                "min_inside_radius": 0.125, "dogbone_style": "classic",
                "clearance": 0.125, "border_gap": 0.75,
            },
        },
    )
    normalized = normalize_config(cfg)
    assert normalized.slats.thickness == 0.5


def test_backing_auto_derived():
    """Backing board dimensions are derived from boundary and slat config."""
    cfg = _make_config()
    normalized = normalize_config(cfg)
    assert normalized.backing.width == cfg.boundary.width
    assert normalized.backing.slot_width == normalized.slats.thickness + normalized.slats.tab_clearance
    assert normalized.backing.slot_depth == normalized.slats.tab_depth


def test_pipeline_with_fit_to_boundary():
    """Full pipeline runs successfully with fit_to_boundary mode."""
    cfg = _make_config(
        slats={
            "count": 20, "spacing": 0.75, "thickness": 0.75,
            "base_height": 1.5, "tab_width": 0.5, "tab_depth": 0.75,
            "tab_count": 3, "tab_clearance": 0.01,
            "distribution_mode": "fit_to_boundary",
        },
    )
    result = run_pipeline(cfg)
    assert result.status == "ok"


def test_changing_slat_count_preserves_panel_size():
    """Different slat counts with same boundary produce different spacings but same boundary.height."""
    cfg_20 = _make_config(
        slats={
            "count": 20, "spacing": 0.75, "thickness": 0.75,
            "base_height": 1.5, "tab_width": 0.5, "tab_depth": 0.75,
            "tab_count": 3, "tab_clearance": 0.01,
            "distribution_mode": "fit_to_boundary",
        },
    )
    cfg_40 = _make_config(
        slats={
            "count": 40, "spacing": 0.75, "thickness": 0.75,
            "base_height": 1.5, "tab_width": 0.5, "tab_depth": 0.75,
            "tab_count": 3, "tab_clearance": 0.01,
            "distribution_mode": "fit_to_boundary",
        },
    )
    n20 = normalize_config(cfg_20)
    n40 = normalize_config(cfg_40)
    # Same boundary height
    assert n20.boundary.height == n40.boundary.height == 24
    # Different spacings
    assert n20.slats.spacing != n40.slats.spacing
    # Both spacings are positive
    assert n20.slats.spacing > 0
    assert n40.slats.spacing > 0
