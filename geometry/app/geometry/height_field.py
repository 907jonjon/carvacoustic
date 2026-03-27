"""
Height field generator — core of the v2 3D surface pipeline.

Generates a 2D grid of Z heights that defines the 3D surface shape.
Each row corresponds to one slat; each column is a position along the slat length.

Surface types: wave, terrain, ripple, mountain
"""

from __future__ import annotations

import numpy as np
from scipy.ndimage import gaussian_filter

from ..models import SurfaceConfig


def generate_height_field(
    surface: SurfaceConfig,
    width: float,
    slat_count: int,
    points_per_slat: int = 200,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Generate a height field for the 3D surface.

    Returns:
        x_vals:  1D array of x positions along each slat (length = points_per_slat)
        heights: 2D array [slat_index, x_position] of Z heights

    heights[i, j] is the profile height of slat i at position x_vals[j].
    """
    rng = np.random.default_rng(surface.seed)

    x_vals = np.linspace(0, width, points_per_slat)
    slat_indices = np.arange(slat_count)

    # Normalize to 0–1 range
    slat_t = slat_indices / max(slat_count - 1, 1)
    x_t = x_vals / max(width, 0.001)

    X, S = np.meshgrid(x_t, slat_t)  # X varies along length, S varies across slats

    if surface.type == "wave":
        Z = _generate_wave(X, S, surface)
    elif surface.type == "terrain":
        Z = _generate_terrain(X, S, surface, rng)
    elif surface.type == "ripple":
        Z = _generate_ripple(X, S, surface)
    elif surface.type == "mountain":
        Z = _generate_mountain(X, S, surface, rng)
    else:
        Z = _generate_wave(X, S, surface)

    # Add organic noise
    if surface.noise_amount > 0:
        noise = rng.standard_normal(Z.shape) * surface.noise_amount
        sigma = max(3, int(points_per_slat * 0.05))
        noise = gaussian_filter(noise, sigma=sigma)
        Z = Z + noise

    # Smooth
    if surface.smoothness > 0:
        sigma = surface.smoothness * max(points_per_slat, slat_count) * 0.1
        Z = gaussian_filter(Z, sigma=sigma)

    # Apply symmetry
    if surface.symmetry in ("x", "xy"):
        Z = (Z + Z[:, ::-1]) / 2.0
    if surface.symmetry in ("y", "xy"):
        Z = (Z + Z[::-1, :]) / 2.0

    # Scale to depth range
    z_min, z_max = float(Z.min()), float(Z.max())
    if z_max - z_min > 1e-9:
        Z = (Z - z_min) / (z_max - z_min)
    else:
        Z = np.zeros_like(Z)

    Z = surface.min_depth + Z * (surface.max_depth - surface.min_depth)

    # Apply amplitude scaling (0–1 multiplier on the depth range)
    Z = Z * surface.amplitude

    return x_vals, Z


def _generate_wave(X: np.ndarray, S: np.ndarray, surface: SurfaceConfig) -> np.ndarray:
    """Smooth sinusoidal wave flowing across the surface."""
    freq = surface.frequency
    phase = surface.phase

    if surface.flow_direction == "x":
        Z = np.sin(freq * np.pi * X + phase) * np.cos(freq * 0.3 * np.pi * S)
    elif surface.flow_direction == "y":
        Z = np.sin(freq * np.pi * S + phase) * np.cos(freq * 0.3 * np.pi * X)
    else:  # radial
        R = np.sqrt((X - 0.5) ** 2 + (S - 0.5) ** 2)
        Z = np.sin(freq * np.pi * R * 2 + phase)

    return Z


def _generate_terrain(
    X: np.ndarray, S: np.ndarray, surface: SurfaceConfig, rng: np.random.Generator
) -> np.ndarray:
    """Organic terrain using layered (octave) Gaussian noise."""
    Z = np.zeros_like(X)
    freq = surface.frequency

    for octave in range(4):
        f = freq * (2 ** octave)
        amp = 1.0 / (2 ** octave)
        noise = rng.standard_normal(X.shape)
        sigma = max(1.0, X.shape[1] / (f * 2))
        noise = gaussian_filter(noise, sigma=sigma)
        Z = Z + noise * amp

    return Z


def _generate_ripple(X: np.ndarray, S: np.ndarray, surface: SurfaceConfig) -> np.ndarray:
    """Concentric ripples from centre (like a stone dropped in water)."""
    freq = surface.frequency
    phase = surface.phase
    R = np.sqrt((X - 0.5) ** 2 + (S - 0.5) ** 2)
    Z = np.cos(freq * np.pi * R * 3 + phase) * np.exp(-R * 2)
    return Z


def _generate_mountain(
    X: np.ndarray, S: np.ndarray, surface: SurfaceConfig, rng: np.random.Generator
) -> np.ndarray:
    """Gaussian peaks at random positions."""
    freq = surface.frequency
    Z = np.zeros_like(X)
    n_peaks = max(1, int(freq))
    peak_positions = rng.uniform(0.15, 0.85, size=(n_peaks, 2))

    for px, py in peak_positions:
        dist = np.sqrt((X - px) ** 2 + (S - py) ** 2)
        peak_width = 0.15 + rng.uniform(0, 0.15)
        Z = Z + np.exp(-dist ** 2 / (2 * peak_width ** 2))

    return Z
