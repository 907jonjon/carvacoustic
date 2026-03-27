"""
Regression tests — spec 04-build-order-and-tests.md §Regression tests.

Rules verified:
  1. same config => same part count
  2. same config => same sheet count
  3. same config => same part geometry fingerprints (proxy for part IDs)
  4. invalid boundary remains invalid across repeated calls
  5. warnings do not silently disappear between versions
"""

from __future__ import annotations

import copy

import pytest

from app.geometry.boundary import (
    build_boundary_polygon,
    compute_safe_boundary,
    normalize_boundary,
)
from app.geometry.export.bundle import build_export_bundle
from app.geometry.layout import run_layout
from app.geometry.pipeline import _collect_polygons, _place_labels, run_pipeline
from app.geometry.patterns.contour_bands import generate_contour_bands
from app.geometry.patterns.slat_rib import generate_slat_rib
from app.geometry.patterns.wave_field import generate_wave_field
from app.geometry.validation import validate_config, validate_geometry
from app.models import CanonicalConfig
from shapely.ops import unary_union


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fingerprint(bands: list) -> tuple:
    """Sort bands by centroid for a stable per-run fingerprint."""
    return tuple(
        sorted(
            (round(b.centroid.x, 4), round(b.centroid.y, 4), round(b.area, 4))
            for b in bands
        )
    )


def _run(config: CanonicalConfig):
    """Run the full pipeline and return result."""
    return run_pipeline(config)


# ── Test 1: same config => same part count ────────────────────────────────────

def test_wave_field_part_count_stable(wave_panel_config):
    r1 = _run(wave_panel_config)
    r2 = _run(wave_panel_config)
    assert r1.part_count == r2.part_count, (
        f"wave_field part count unstable: {r1.part_count} vs {r2.part_count}"
    )


def test_contour_bands_part_count_stable(cabinet_contour_config):
    r1 = _run(cabinet_contour_config)
    r2 = _run(cabinet_contour_config)
    assert r1.part_count == r2.part_count


def test_slat_rib_part_count_stable(wave_panel_config):
    cfg = copy.deepcopy(wave_panel_config.model_dump())
    cfg["pattern"]["family"] = "slat_rib"
    config = CanonicalConfig(**cfg)
    r1 = _run(config)
    r2 = _run(config)
    assert r1.part_count == r2.part_count


# ── Test 2: same config => same sheet count ───────────────────────────────────

def test_wave_panel_sheet_count_stable(wave_panel_config):
    raw = build_boundary_polygon(wave_panel_config.boundary)
    bp, _ = normalize_boundary(raw)
    lr1 = run_layout(bp, wave_panel_config)
    lr2 = run_layout(bp, wave_panel_config)
    assert len(lr1.sheets) == len(lr2.sheets), (
        f"Sheet count unstable: {len(lr1.sheets)} vs {len(lr2.sheets)}"
    )
    # Both sheets must have placements (no overflow in stable run)
    assert lr1.overflow == lr2.overflow


def test_multi_copy_sheet_count_stable(wave_panel_config):
    cfg = wave_panel_config.model_dump()
    cfg["layout"] = {**cfg["layout"], "copies": 3}
    config = CanonicalConfig(**cfg)
    raw = build_boundary_polygon(config.boundary)
    bp, _ = normalize_boundary(raw)
    lr1 = run_layout(bp, config)
    lr2 = run_layout(bp, config)
    assert len(lr1.sheets) == len(lr2.sheets)


# ── Test 3: same config => same part geometry fingerprints ────────────────────

def test_wave_field_geometry_fingerprint_stable(wave_panel_config):
    raw = build_boundary_polygon(wave_panel_config.boundary)
    bp, _ = normalize_boundary(raw)
    sp = compute_safe_boundary(bp, wave_panel_config.boundary.safe_margin)
    bands1 = generate_wave_field(sp, wave_panel_config.pattern, wave_panel_config.fabrication)
    bands2 = generate_wave_field(sp, wave_panel_config.pattern, wave_panel_config.fabrication)
    assert _fingerprint(bands1) == _fingerprint(bands2), "wave_field geometry not deterministic"


def test_contour_bands_geometry_fingerprint_stable(cabinet_contour_config):
    raw = build_boundary_polygon(cabinet_contour_config.boundary)
    bp, _ = normalize_boundary(raw)
    sp = compute_safe_boundary(bp, cabinet_contour_config.boundary.safe_margin)
    bands1 = generate_contour_bands(sp, cabinet_contour_config.pattern, cabinet_contour_config.fabrication)
    bands2 = generate_contour_bands(sp, cabinet_contour_config.pattern, cabinet_contour_config.fabrication)
    assert _fingerprint(bands1) == _fingerprint(bands2)


def test_slat_rib_geometry_fingerprint_stable(wave_panel_config):
    cfg = copy.deepcopy(wave_panel_config.model_dump())
    cfg["pattern"]["family"] = "slat_rib"
    config = CanonicalConfig(**cfg)
    raw = build_boundary_polygon(config.boundary)
    bp, _ = normalize_boundary(raw)
    sp = compute_safe_boundary(bp, config.boundary.safe_margin)
    bands1 = generate_slat_rib(sp, config.pattern, config.fabrication)
    bands2 = generate_slat_rib(sp, config.pattern, config.fabrication)
    assert _fingerprint(bands1) == _fingerprint(bands2)


def test_svg_preview_is_identical_for_same_config(wave_panel_config):
    r1 = _run(wave_panel_config)
    r2 = _run(wave_panel_config)
    assert r1.svg_preview == r2.svg_preview, "SVG preview not deterministic"


# ── Test 4: invalid boundary remains invalid ──────────────────────────────────

def test_svg_import_always_raises(wave_panel_config):
    cfg = wave_panel_config.model_dump()
    cfg["boundary"]["type"] = "svg_import"
    config = CanonicalConfig(**cfg)
    for _ in range(3):
        try:
            build_boundary_polygon(config.boundary)
            assert False, "Expected ValueError for svg_import"
        except (ValueError, NotImplementedError):
            pass  # expected


def test_zero_area_boundary_is_always_invalid(wave_panel_config):
    cfg = wave_panel_config.model_dump()
    cfg["boundary"]["width"] = 0.0001
    cfg["boundary"]["height"] = 0.0001
    config = CanonicalConfig(**cfg)
    for _ in range(3):
        r = _run(config)
        assert r.status == "error", "Degenerate boundary must always fail"


def test_invalid_margin_is_always_invalid(wave_panel_config):
    """safe_margin that consumes > 90% of boundary is always an error."""
    cfg = wave_panel_config.model_dump()
    cfg["boundary"]["safe_margin"] = 25.0  # larger than half of 48
    config = CanonicalConfig(**cfg)
    for _ in range(3):
        r = _run(config)
        assert r.status == "error"


# ── Test 5: warnings do not silently disappear between versions ───────────────

def test_thin_bridge_warning_stable(wave_panel_config):
    """A config that produces a thin_bridge warning always produces it."""
    cfg = wave_panel_config.model_dump()
    cfg["pattern"]["spacing"] = 0.35  # spacing < min_bridge (0.3 bridge)
    config = CanonicalConfig(**cfg)
    for _ in range(3):
        issues = validate_config(config)
        codes = [i.code for i in issues]
        assert "thin_bridge" in codes, f"thin_bridge warning disappeared; got {codes}"


def test_amplitude_warning_stable(wave_panel_config):
    """Amplitude > safe_margin always warns."""
    cfg = wave_panel_config.model_dump()
    cfg["pattern"]["amplitude"] = 5.0  # >> safe_margin=1.0
    config = CanonicalConfig(**cfg)
    for _ in range(3):
        issues = validate_config(config)
        codes = [i.code for i in issues]
        assert "amplitude_exceeds_margin" in codes, (
            f"amplitude_exceeds_margin warning disappeared; got {codes}"
        )


def test_feature_below_minimum_stable(wave_panel_config):
    """line_width < tool_diameter always errors."""
    cfg = wave_panel_config.model_dump()
    cfg["pattern"]["line_width"] = 0.1  # < tool_diameter=0.25
    config = CanonicalConfig(**cfg)
    for _ in range(3):
        issues = validate_config(config)
        errors = [i for i in issues if i.level == "error"]
        assert any(i.code == "feature_below_minimum" for i in errors)
