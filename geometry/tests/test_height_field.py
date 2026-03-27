"""
v2 height field tests — spec DELTA-02 §Part D.
"""

from __future__ import annotations

import numpy as np
import pytest

from app.geometry.height_field import generate_height_field
from app.models import SurfaceConfig


@pytest.fixture
def wave_surface():
    return SurfaceConfig(type="wave", seed=42, amplitude=0.7, frequency=3.0)


def test_deterministic(wave_surface):
    """Same config produces identical height field."""
    _, h1 = generate_height_field(wave_surface, width=48, slat_count=30)
    _, h2 = generate_height_field(wave_surface, width=48, slat_count=30)
    np.testing.assert_array_equal(h1, h2)


def test_output_shape(wave_surface):
    """heights array has correct shape [slat_count, points_per_slat]."""
    x_vals, heights = generate_height_field(wave_surface, width=48, slat_count=30, points_per_slat=100)
    assert x_vals.shape == (100,)
    assert heights.shape == (30, 100)


def test_x_vals_range(wave_surface):
    """x_vals spans 0 to width."""
    x_vals, _ = generate_height_field(wave_surface, width=48, slat_count=30)
    assert abs(x_vals[0]) < 1e-9
    assert abs(x_vals[-1] - 48) < 1e-9


def test_symmetry_x():
    """X symmetry: left/right mirror."""
    surface = SurfaceConfig(type="wave", symmetry="x", seed=42, noise_amount=0)
    _, heights = generate_height_field(surface, width=48, slat_count=30)
    np.testing.assert_array_almost_equal(heights, heights[:, ::-1], decimal=10)


def test_symmetry_y():
    """Y symmetry: first/last slats mirror."""
    surface = SurfaceConfig(type="wave", symmetry="y", seed=42, noise_amount=0)
    _, heights = generate_height_field(surface, width=48, slat_count=30)
    np.testing.assert_array_almost_equal(heights, heights[::-1, :], decimal=10)


def test_depth_range():
    """Heights stay within amplitude * max_depth."""
    surface = SurfaceConfig(min_depth=0.0, max_depth=4.0, amplitude=1.0, noise_amount=0, smoothness=0)
    _, heights = generate_height_field(surface, width=48, slat_count=30)
    assert float(heights.min()) >= 0.0
    assert float(heights.max()) <= 4.01  # small tolerance for float arithmetic


def test_all_surface_types():
    """All four surface types generate non-empty, finite height fields."""
    for surf_type in ("wave", "terrain", "ripple", "mountain"):
        surface = SurfaceConfig(type=surf_type, seed=42)
        _, heights = generate_height_field(surface, width=48, slat_count=20)
        assert heights.shape == (20, 200)
        assert np.isfinite(heights).all()


def test_zero_noise_is_deterministic():
    """With noise_amount=0 and smoothness=0, two runs produce bit-identical results."""
    surface = SurfaceConfig(type="wave", noise_amount=0, smoothness=0, seed=7)
    _, h1 = generate_height_field(surface, width=24, slat_count=10)
    _, h2 = generate_height_field(surface, width=24, slat_count=10)
    np.testing.assert_array_equal(h1, h2)
