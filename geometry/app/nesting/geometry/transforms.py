"""Transform enumeration and application — legal discrete transforms for nesting."""

from __future__ import annotations

from shapely import affinity
from shapely.geometry import Polygon

from ..models import TransformSpec


def enumerate_transforms(
    layout_config,              # ConfigLayout
    grain_direction: str | None,  # "x" | "y" | None
    allow_mirror: bool = False,
) -> list[TransformSpec]:
    """
    Return all legal discrete transforms based on rotation_mode,
    preserve_grain, and grain_direction.

    Mirroring variants are only added when *allow_mirror* is True on the part.
    """
    rotation_mode = layout_config.rotation_mode.value  # "none" | "90_only" | "any"

    if rotation_mode == "none":
        angles = [0.0]
    elif rotation_mode == "90_only":
        angles = [0.0, 90.0]
    else:  # "any"
        angles = [0.0, 90.0, 180.0, 270.0]

    # Grain lock: only allow angles where angle % 180 == 0
    if layout_config.preserve_grain and grain_direction is not None:
        angles = [a for a in angles if a % 180 == 0]

    transforms: list[TransformSpec] = []
    mirror_flags = [False]
    if allow_mirror:
        mirror_flags.append(True)

    for m in mirror_flags:
        for a in angles:
            transforms.append(TransformSpec(angle_deg=a, mirrored=m))

    return transforms


def apply_transform(poly: Polygon, t: TransformSpec) -> Polygon:
    """Apply a TransformSpec to a polygon centred at origin."""
    result = poly
    if t.mirrored:
        result = affinity.scale(result, xfact=-1, yfact=1, origin=(0, 0))
    if t.angle_deg != 0:
        result = affinity.rotate(result, t.angle_deg, origin=(0, 0))
    return result
