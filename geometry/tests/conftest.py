"""
Shared test fixtures — canonical configs for both golden samples.
"""

from __future__ import annotations

import os

os.environ.setdefault("API_KEY", "dev-secret")

import pytest  # noqa: E402
from app.models import CanonicalConfig  # noqa: E402


# ---------------------------------------------------------------------------
# Golden sample fixtures
# ---------------------------------------------------------------------------

WAVE_PANEL_CFG = {
    "schema_version": "1.0.0",
    "project": {"name": "Lobby Wave Panel", "mode": "wall_art", "units": "in"},
    "boundary": {
        "type": "rectangle",
        "width": 60,
        "height": 48,
        "corner_radius": 0,
        "asset_id": None,
        "safe_margin": 1.0,
    },
    "pattern": {
        "family": "wave_field",
        "density": 0.65,
        "spacing": 1.2,
        "line_width": 0.4,
        "amplitude": 0.8,
        "seed": 42,
        "symmetry": "none",
    },
    "fabrication": {
        "material": {
            "thickness": 0.75,
            "sheet_width": 96,
            "sheet_height": 48,
            "min_bridge": 0.3,
            "grain_direction": "x",
        },
        "tool": {
            "tool_diameter": 0.25,
            "kerf_allowance": 0.0,
            "min_inside_radius": 0.125,
            "dogbone_style": "classic",
            "clearance": 0.125,
            "border_gap": 0.75,
        },
    },
    "layout": {"enabled": True, "copies": 1, "rotation_mode": "90_only", "preserve_grain": False},
    "labeling": {"enabled": True, "prefix": "P", "position": "footer"},
    "export": {"formats": ["dxf", "svg", "pdf", "json"], "units": "in"},
    "reserved_acoustic": {
        "enabled": False,
        "room_use": None,
        "target_issue": None,
        "room_dimensions": None,
        "surface_summary": None,
        "installation_constraints": None,
        "attachments": [],
    },
}

CABINET_CONTOUR_CFG = {
    **WAVE_PANEL_CFG,
    "project": {"name": "Cabinet Contour Panel", "mode": "cabinet_front_panel", "units": "in"},
    "boundary": {
        "type": "rectangle",
        "width": 24,
        "height": 36,
        "corner_radius": 0,
        "asset_id": None,
        "safe_margin": 0.5,
    },
    "pattern": {
        "family": "contour_bands",
        "density": 0.5,
        "spacing": 1.0,
        "line_width": 0.3,
        "amplitude": 0.0,
        "seed": 7,
        "symmetry": "none",
    },
}


@pytest.fixture()
def wave_panel_config() -> CanonicalConfig:
    return CanonicalConfig(**WAVE_PANEL_CFG)


@pytest.fixture()
def cabinet_contour_config() -> CanonicalConfig:
    return CanonicalConfig(**CABINET_CONTOUR_CFG)
