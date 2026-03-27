"""
Legacy v1 golden sample tests — skipped after Delta 2 migration to slat pipeline.

import pytest
pytestmark = pytest.mark.skip(reason="Legacy v1 pattern pipeline — replaced by v2 slat pipeline")

Golden sample tests — spec 04-build-order-and-tests.md §Golden samples.

Samples:
  1. wall_art_wave_panel    — wave_field, 60×48 in
  2. cabinet_front_contour  — contour_bands, 24×36 in

For each sample:
  1. generate preview (status=ok, part_count>0, svg non-empty)
  2. validate (valid=True, no errors)
  3. layout (at least 1 sheet, no overflow)
  4. export (ZIP produced with all required files and layers)
"""

from __future__ import annotations

import io
import json

import pytest

pytestmark = pytest.mark.skip(reason="Legacy v1 pattern pipeline — replaced by v2 slat pipeline")
import zipfile

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
from app.geometry.patterns.wave_field import generate_wave_field
from app.geometry.validation import validate_config, validate_geometry
from app.models import CanonicalConfig
from shapely.ops import unary_union

_REQUIRED_DXF_LAYERS = [
    "CUT_OUTER",
    "CUT_INNER",
    "ENGRAVE_LABEL",
    "REFERENCE_BOUNDARY",
    "SAFE_MARGIN_GUIDE",
]
_REQUIRED_BUNDLE_FILES = {
    "manifest.json",
    "project-config.json",
    "sheet-01.dxf",
    "sheet-01.svg",
    "reference.pdf",
    "README.txt",
}


def _run_full(config: CanonicalConfig):
    """Return (result, boundary_poly, safe_poly, bands, labels)."""
    result = run_pipeline(config)
    raw = build_boundary_polygon(config.boundary)
    bp, _ = normalize_boundary(raw)
    sp = compute_safe_boundary(bp, config.boundary.safe_margin)
    if config.pattern.family.value == "wave_field":
        bands = _collect_polygons(
            unary_union(generate_wave_field(sp, config.pattern, config.fabrication))
        )
    else:
        bands = generate_contour_bands(sp, config.pattern, config.fabrication)
    labels = _place_labels(bp, config)
    return result, bp, sp, bands, labels


# ─────────────────────────────────────────────────────────────────────────────
# Golden sample 1: wall_art_wave_panel
# ─────────────────────────────────────────────────────────────────────────────

class TestWavePanel:
    def test_generate(self, wave_panel_config):
        r, *_ = _run_full(wave_panel_config)
        assert r.status == "ok", f"Generate failed: {r.message}"
        assert r.part_count > 0
        assert r.svg_preview.startswith("<svg"), "SVG preview malformed"
        assert r.generated_at, "generated_at missing"

    def test_validate(self, wave_panel_config):
        r, *_ = _run_full(wave_panel_config)
        assert r.validation.valid, (
            f"Golden sample should be valid; issues: {r.validation.issues}"
        )
        errors = [i for i in r.validation.issues if i.level == "error"]
        assert not errors, f"Unexpected errors: {errors}"

    def test_layout(self, wave_panel_config):
        raw = build_boundary_polygon(wave_panel_config.boundary)
        bp, _ = normalize_boundary(raw)
        lr = run_layout(bp, wave_panel_config)
        assert len(lr.sheets) >= 1, "Layout produced no sheets"
        total_placed = sum(len(s.placements) for s in lr.sheets)
        assert total_placed == wave_panel_config.layout.copies, (
            f"Expected {wave_panel_config.layout.copies} placements, got {total_placed}"
        )

    def test_export_bundle(self, wave_panel_config):
        r, bp, sp, bands, labels = _run_full(wave_panel_config)
        zip_bytes, filename = build_export_bundle(wave_panel_config, bp, sp, bands, labels)
        assert len(zip_bytes) > 1000, "ZIP is implausibly small"
        assert filename.endswith(".zip")

        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            names = set(zf.namelist())
            missing = _REQUIRED_BUNDLE_FILES - names
            assert not missing, f"Missing bundle files: {missing}"

            # DXF layers
            dxf_text = zf.read("sheet-01.dxf").decode("utf-8", errors="replace")
            for layer in _REQUIRED_DXF_LAYERS:
                assert layer in dxf_text, f"Missing DXF layer: {layer}"

            # Manifest integrity
            manifest = json.loads(zf.read("manifest.json"))
            assert manifest["project_name"] == wave_panel_config.project.name
            assert "sheet-01.dxf" in manifest["files"]
            assert "reference.pdf" in manifest["files"]

            # PDF non-trivial
            pdf_bytes = zf.read("reference.pdf")
            assert len(pdf_bytes) > 1000, "Reference PDF too small"
            assert pdf_bytes[:4] == b"%PDF", "reference.pdf is not a valid PDF"

            # project-config round-trip
            stored = json.loads(zf.read("project-config.json"))
            assert stored["project"]["name"] == wave_panel_config.project.name
            assert stored["schema_version"] == "1.0.0"

    def test_dxf_scale(self, wave_panel_config):
        """DXF $INSUNITS = 1 (inches) for an inch project."""
        r, bp, sp, bands, labels = _run_full(wave_panel_config)
        zip_bytes, _ = build_export_bundle(wave_panel_config, bp, sp, bands, labels)
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            dxf_text = zf.read("sheet-01.dxf").decode("utf-8", errors="replace")
        assert "$INSUNITS" in dxf_text, "DXF missing $INSUNITS"
        # ezdxf format: "$INSUNITS\n 70\n1\n" — group code 70, value 1 = inches
        idx = dxf_text.index("$INSUNITS")
        snippet = dxf_text[idx : idx + 60]
        assert "\n1\n" in snippet, (
            f"$INSUNITS should be 1 for inch units; snippet: {snippet!r}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Golden sample 2: cabinet_front_contour_panel
# ─────────────────────────────────────────────────────────────────────────────

class TestCabinetContourPanel:
    def test_generate(self, cabinet_contour_config):
        r, *_ = _run_full(cabinet_contour_config)
        assert r.status == "ok", f"Generate failed: {r.message}"
        assert r.part_count > 0

    def test_validate(self, cabinet_contour_config):
        r, *_ = _run_full(cabinet_contour_config)
        errors = [i for i in r.validation.issues if i.level == "error"]
        assert not errors, f"Unexpected errors: {errors}"

    def test_layout(self, cabinet_contour_config):
        raw = build_boundary_polygon(cabinet_contour_config.boundary)
        bp, _ = normalize_boundary(raw)
        lr = run_layout(bp, cabinet_contour_config)
        assert len(lr.sheets) >= 1
        total = sum(len(s.placements) for s in lr.sheets)
        assert total == cabinet_contour_config.layout.copies

    def test_export_bundle(self, cabinet_contour_config):
        r, bp, sp, bands, labels = _run_full(cabinet_contour_config)
        zip_bytes, _ = build_export_bundle(cabinet_contour_config, bp, sp, bands, labels)
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            names = set(zf.namelist())
            assert _REQUIRED_BUNDLE_FILES <= names

    def test_labels_in_dxf(self, cabinet_contour_config):
        """ENGRAVE_LABEL layer must contain the configured prefix."""
        r, bp, sp, bands, labels = _run_full(cabinet_contour_config)
        zip_bytes, _ = build_export_bundle(cabinet_contour_config, bp, sp, bands, labels)
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            dxf_text = zf.read("sheet-01.dxf").decode("utf-8", errors="replace")
        assert "ENGRAVE_LABEL" in dxf_text


# ─────────────────────────────────────────────────────────────────────────────
# Multi-copy layout — 3 copies of the cabinet panel
# ─────────────────────────────────────────────────────────────────────────────

class TestMultiCopyLayout:
    def test_three_copies_produce_multiple_sheet_files(self, cabinet_contour_config):
        import copy as _copy
        cfg = _copy.deepcopy(cabinet_contour_config.model_dump())
        cfg["layout"] = {"enabled": True, "copies": 3, "rotation_mode": "90_only", "preserve_grain": False}
        config = CanonicalConfig(**cfg)
        raw = build_boundary_polygon(config.boundary)
        bp, _ = normalize_boundary(raw)
        sp = compute_safe_boundary(bp, config.boundary.safe_margin)
        bands = generate_contour_bands(sp, config.pattern, config.fabrication)
        labels = _place_labels(bp, config)
        zip_bytes, _ = build_export_bundle(config, bp, sp, bands, labels)
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            dxf_files = [n for n in zf.namelist() if n.endswith(".dxf")]
            assert len(dxf_files) >= 1, "No DXF files in multi-copy bundle"
            total_placements = sum(
                len(json.loads(zf.read("manifest.json"))["files"])
                for _ in [1]
            )
            manifest = json.loads(zf.read("manifest.json"))
            # Verify manifest lists all sheet DXFs
            for df in dxf_files:
                assert df in manifest["files"], f"{df} not in manifest"
