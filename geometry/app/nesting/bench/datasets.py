"""Benchmark datasets — load fixtures and generate synthetic jobs."""

from __future__ import annotations

import json
import math
import random
from pathlib import Path

from shapely.geometry import Polygon
from shapely.prepared import prep

from ..geometry.offsets import inflate_part
from ..geometry.preferred_edges import detect_preferred_edges
from ..geometry.transforms import apply_transform
from ..models import NestJob, PartSpec, SheetSpec, TransformSpec, VariantGeom

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "nesting"


def load_fixture(name: str) -> NestJob:
    """Load a regression fixture by name and return a NestJob."""
    path = FIXTURE_DIR / f"{name}.json"
    with open(path) as f:
        data = json.load(f)
    return _fixture_to_job(data)


def load_all_fixtures() -> dict[str, NestJob]:
    """Load all fixture JSON files from the fixtures directory."""
    jobs: dict[str, NestJob] = {}
    if not FIXTURE_DIR.exists():
        return jobs
    for path in sorted(FIXTURE_DIR.glob("*.json")):
        name = path.stem
        try:
            jobs[name] = load_fixture(name)
        except Exception:
            pass
    return jobs


def generate_synthetic_dataset(
    n_parts: int,
    complexity: str = "medium",
    seed: int = 42,
) -> NestJob:
    """
    Generate synthetic benchmark jobs.

    - simple: convex regular polygons
    - medium: one-flat-edge shapes with moderate curves
    - complex: high-vertex concave shapes with small features
    """
    rng = random.Random(seed)

    sheet = SheetSpec(width=96.0, height=48.0, edge_margin=0.75, grain_axis="x")
    clearance = 0.125
    parts: list[PartSpec] = []

    for i in range(n_parts):
        if complexity == "simple":
            poly = _random_convex(rng, w_range=(1, 8), h_range=(1, 4))
        elif complexity == "complex":
            poly = _random_concave(rng, n_verts=200, w=rng.uniform(2, 10), h=rng.uniform(1, 5))
        else:
            poly = _random_slat_like(rng, w=rng.uniform(3, 12), h=rng.uniform(1, 4))

        part = _poly_to_part(f"SYN{i:03d}", poly, clearance, [0.0, 90.0])
        parts.append(part)

    return NestJob(sheets=sheet, parts=parts, clearance=clearance, mode="balanced", seed=seed)


def _fixture_to_job(data: dict) -> NestJob:
    """Convert fixture JSON dict to NestJob."""
    from shapely import wkt

    sheet_data = data["sheet"]
    sheet = SheetSpec(
        width=sheet_data["width"],
        height=sheet_data["height"],
        edge_margin=sheet_data["edge_margin"],
        grain_axis=sheet_data.get("grain_axis"),
    )
    clearance = data["clearance"]

    parts: list[PartSpec] = []
    for pd in data["parts"]:
        poly = wkt.loads(pd["polygon_wkt"])
        allowed = pd.get("allowed_angles", [0.0])
        grain_locked = pd.get("grain_locked", False)
        allow_mirror = pd.get("allow_mirror", False)

        part = _poly_to_part(
            pd["part_id"], poly, clearance,
            allowed_angles=allowed,
            grain_locked=grain_locked,
            allow_mirror=allow_mirror,
        )
        parts.append(part)

    return NestJob(sheets=sheet, parts=parts, clearance=clearance, mode="balanced")


def _poly_to_part(
    part_id: str,
    poly: Polygon,
    clearance: float,
    allowed_angles: list[float] | None = None,
    grain_locked: bool = False,
    allow_mirror: bool = False,
) -> PartSpec:
    """Convert a Shapely Polygon to a PartSpec with variants."""
    from shapely import affinity

    # Centre at origin
    cx, cy = poly.centroid.x, poly.centroid.y
    centred = affinity.translate(poly, xoff=-cx, yoff=-cy)

    if allowed_angles is None:
        allowed_angles = [0.0]

    transforms = []
    mirror_flags = [False]
    if allow_mirror:
        mirror_flags.append(True)
    for m in mirror_flags:
        for a in allowed_angles:
            transforms.append(TransformSpec(angle_deg=a, mirrored=m))

    variants: list[VariantGeom] = []
    for t in transforms:
        transformed = apply_transform(centred, t)
        inflated = inflate_part(transformed, clearance)
        edges = detect_preferred_edges(transformed)
        variants.append(VariantGeom(
            transform=t,
            polygon=transformed,
            inflated=inflated,
            prepared_inflated=prep(inflated),
            aabb=inflated.bounds,
            preferred_edges=edges,
            area=transformed.area,
        ))

    return PartSpec(
        part_id=part_id,
        quantity=1,
        variants=variants,
        original_polygon=poly,
        grain_locked=grain_locked,
        allow_mirror=allow_mirror,
    )


def _random_convex(rng: random.Random, w_range=(1, 8), h_range=(1, 4)) -> Polygon:
    w = rng.uniform(*w_range)
    h = rng.uniform(*h_range)
    n = rng.randint(5, 8)
    angles = sorted(rng.uniform(0, 2 * math.pi) for _ in range(n))
    coords = [(w / 2 * math.cos(a), h / 2 * math.sin(a)) for a in angles]
    poly = Polygon(coords)
    if not poly.is_valid:
        poly = poly.buffer(0)
    return poly


def _random_slat_like(rng: random.Random, w: float, h: float) -> Polygon:
    """Slat-like: flat base, curved top."""
    n_top = 30
    top = [(w * i / (n_top - 1), h + h * 0.3 * math.sin(math.pi * i / (n_top - 1))) for i in range(n_top)]
    bottom = [(w, 0), (0, 0)]
    return Polygon(top + bottom)


def _random_concave(rng: random.Random, n_verts: int, w: float, h: float) -> Polygon:
    """High-vertex concave shape."""
    pts = []
    for i in range(n_verts):
        angle = 2 * math.pi * i / n_verts
        r_base = min(w, h) / 2
        wobble = rng.uniform(0.7, 1.0)
        x = w / 2 + r_base * wobble * math.cos(angle)
        y = h / 2 + r_base * wobble * (h / w) * math.sin(angle)
        pts.append((x, y))
    poly = Polygon(pts)
    if not poly.is_valid:
        poly = poly.buffer(0)
    return poly
