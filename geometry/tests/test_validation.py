"""
Legacy v1 validation tests — skipped after Delta 2 migration to slat pipeline.

import pytest
pytestmark = pytest.mark.skip(reason="Legacy v1 pattern pipeline — replaced by v2 slat pipeline")

Validation engine tests — spec 02-geometry-spec.md §Validation rules.

Verifies that every named error/warning/info code fires under the correct conditions.
"""

from __future__ import annotations

import copy

import pytest

pytestmark = pytest.mark.skip(reason="Legacy v1 pattern pipeline — replaced by v2 slat pipeline")

from app.geometry.boundary import (
    build_boundary_polygon,
    compute_safe_boundary,
    normalize_boundary,
)
from app.geometry.patterns.wave_field import generate_wave_field
from app.geometry.validation import validate_config, validate_geometry
from app.models import CanonicalConfig


def _issues_dict(config: CanonicalConfig) -> dict[str, list]:
    """Return {code: [issues...]} for validate_config."""
    issues = validate_config(config)
    result: dict[str, list] = {}
    for i in issues:
        result.setdefault(i.code, []).append(i)
    return result


def _geom_issues(config: CanonicalConfig) -> dict[str, list]:
    """Run boundary + pattern + validate_geometry, return {code: [issues]}."""
    raw = build_boundary_polygon(config.boundary)
    bp, _ = normalize_boundary(raw)
    sp = compute_safe_boundary(bp, config.boundary.safe_margin)
    bands = generate_wave_field(sp, config.pattern, config.fabrication)
    issues = validate_geometry(bands, bp, sp, config)
    result: dict[str, list] = {}
    for i in issues:
        result.setdefault(i.code, []).append(i)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Config-level errors
# ─────────────────────────────────────────────────────────────────────────────

class TestConfigErrors:
    def test_feature_below_minimum(self, wave_panel_config):
        cfg = wave_panel_config.model_dump()
        cfg["pattern"]["line_width"] = 0.1  # < tool_diameter=0.25
        config = CanonicalConfig(**cfg)
        d = _issues_dict(config)
        assert "feature_below_minimum" in d
        assert d["feature_below_minimum"][0].level == "error"
        assert d["feature_below_minimum"][0].field == "pattern.line_width"

    def test_impossible_inside_radius(self, wave_panel_config):
        cfg = wave_panel_config.model_dump()
        cfg["pattern"]["line_width"] = 0.2   # tightest_radius = 0.1
        cfg["fabrication"]["tool"]["min_inside_radius"] = 0.15  # > 0.1
        config = CanonicalConfig(**cfg)
        d = _issues_dict(config)
        assert "impossible_inside_radius" in d
        assert d["impossible_inside_radius"][0].level == "error"

    def test_invalid_boundary_margin_too_large(self, wave_panel_config):
        cfg = wave_panel_config.model_dump()
        cfg["boundary"]["safe_margin"] = 25.0  # consumes > 90% of 48
        config = CanonicalConfig(**cfg)
        d = _issues_dict(config)
        assert "invalid_boundary" in d
        assert d["invalid_boundary"][0].level == "error"

    def test_thin_bridge_error_when_bands_overlap(self, wave_panel_config):
        """spacing <= line_width → no bridge → error."""
        cfg = wave_panel_config.model_dump()
        cfg["pattern"]["spacing"] = 0.3   # = line_width
        cfg["pattern"]["line_width"] = 0.4
        config = CanonicalConfig(**cfg)
        d = _issues_dict(config)
        assert "thin_bridge" in d
        assert d["thin_bridge"][0].level == "error"


# ─────────────────────────────────────────────────────────────────────────────
# Config-level warnings
# ─────────────────────────────────────────────────────────────────────────────

class TestConfigWarnings:
    def test_thin_bridge_warning(self, wave_panel_config):
        """Bridge < min_bridge but > 0 → warning."""
        cfg = wave_panel_config.model_dump()
        # spacing=0.55, line_width=0.4 → bridge=0.15 < min_bridge=0.3
        cfg["pattern"]["spacing"] = 0.55
        cfg["pattern"]["line_width"] = 0.4
        cfg["fabrication"]["material"]["min_bridge"] = 0.3
        config = CanonicalConfig(**cfg)
        d = _issues_dict(config)
        assert "thin_bridge" in d
        assert d["thin_bridge"][0].level == "warning"

    def test_amplitude_exceeds_margin(self, wave_panel_config):
        cfg = wave_panel_config.model_dump()
        cfg["pattern"]["amplitude"] = 2.0   # > safe_margin=1.0
        config = CanonicalConfig(**cfg)
        d = _issues_dict(config)
        assert "amplitude_exceeds_margin" in d
        assert d["amplitude_exceeds_margin"][0].level == "warning"

    def test_no_amplitude_warning_when_margin_zero(self, wave_panel_config):
        """If safe_margin is 0, amplitude check should not warn."""
        cfg = wave_panel_config.model_dump()
        cfg["boundary"]["safe_margin"] = 0.0
        cfg["pattern"]["amplitude"] = 2.0
        config = CanonicalConfig(**cfg)
        d = _issues_dict(config)
        assert "amplitude_exceeds_margin" not in d


# ─────────────────────────────────────────────────────────────────────────────
# Config-level info
# ─────────────────────────────────────────────────────────────────────────────

class TestConfigInfo:
    def test_dogbones_not_applied_info(self, wave_panel_config):
        cfg = wave_panel_config.model_dump()
        cfg["fabrication"]["tool"]["dogbone_style"] = "none"
        config = CanonicalConfig(**cfg)
        d = _issues_dict(config)
        assert "dogbones_not_applied" in d
        assert d["dogbones_not_applied"][0].level == "info"

    def test_no_dogbone_info_when_style_classic(self, wave_panel_config):
        d = _issues_dict(wave_panel_config)
        assert "dogbones_not_applied" not in d


# ─────────────────────────────────────────────────────────────────────────────
# Geometry-level errors
# ─────────────────────────────────────────────────────────────────────────────

class TestGeometryErrors:
    def test_no_geometry_when_spacing_too_large(self, wave_panel_config):
        """Spacing much larger than boundary → no bands → error."""
        cfg = wave_panel_config.model_dump()
        cfg["pattern"]["spacing"] = 999.0
        cfg["pattern"]["line_width"] = 0.4
        config = CanonicalConfig(**cfg)
        # Config validation passes; geometry should produce zero or error
        raw = build_boundary_polygon(config.boundary)
        bp, _ = normalize_boundary(raw)
        sp = compute_safe_boundary(bp, config.boundary.safe_margin)
        from app.geometry.patterns.wave_field import generate_wave_field
        bands = generate_wave_field(sp, config.pattern, config.fabrication)
        # May produce 0 bands; geometry validation should flag it
        if not bands:
            issues = validate_geometry(bands, bp, sp, config)
            codes = [i.code for i in issues]
            assert "invalid_boundary" in codes or any(i.level == "error" for i in issues)


# ─────────────────────────────────────────────────────────────────────────────
# Geometry-level warnings
# ─────────────────────────────────────────────────────────────────────────────

class TestGeometryWarnings:
    def test_high_part_count_warning(self, wave_panel_config):
        """Very small spacing produces many parts → high_part_count warning."""
        cfg = wave_panel_config.model_dump()
        cfg["pattern"]["spacing"] = 0.28  # close spacing
        cfg["pattern"]["line_width"] = 0.26  # slightly above tool_diameter
        cfg["pattern"]["amplitude"] = 0.0
        # Use a large boundary to ensure many parts
        cfg["boundary"]["width"] = 60
        cfg["boundary"]["height"] = 60
        config = CanonicalConfig(**cfg)
        raw = build_boundary_polygon(config.boundary)
        bp, _ = normalize_boundary(raw)
        sp = compute_safe_boundary(bp, config.boundary.safe_margin)
        bands = generate_wave_field(sp, config.pattern, config.fabrication)
        issues = validate_geometry(bands, bp, sp, config)
        if len(bands) > 200:
            codes = [i.code for i in issues]
            assert "high_part_count" in codes

    def test_low_utilization_warning(self, wave_panel_config):
        """Very large spacing → tiny cut area → low_material_utilization."""
        cfg = wave_panel_config.model_dump()
        cfg["pattern"]["spacing"] = 20.0
        cfg["pattern"]["line_width"] = 0.26
        cfg["pattern"]["amplitude"] = 0.0
        config = CanonicalConfig(**cfg)
        d = _geom_issues(config)
        assert "low_material_utilization" in d
        assert d["low_material_utilization"][0].level == "warning"


# ─────────────────────────────────────────────────────────────────────────────
# Clean config produces no errors
# ─────────────────────────────────────────────────────────────────────────────

def test_golden_wave_panel_no_config_errors(wave_panel_config):
    issues = validate_config(wave_panel_config)
    errors = [i for i in issues if i.level == "error"]
    assert not errors, f"Golden sample has config errors: {errors}"


def test_golden_cabinet_contour_no_config_errors(cabinet_contour_config):
    issues = validate_config(cabinet_contour_config)
    errors = [i for i in issues if i.level == "error"]
    assert not errors, f"Golden sample has config errors: {errors}"
