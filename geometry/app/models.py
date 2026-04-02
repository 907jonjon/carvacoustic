"""
CarvAcoustic geometry service — Pydantic models (schema v2.0.0).

v2 replaces the flat pattern section (wave_field / contour_bands / slat_rib)
with a height-field based surface + profiled slats pipeline.

Backward compatibility: v1 configs (schema_version "1.0.0") are automatically
migrated to v2 via CanonicalConfig's model_validator.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class Units(str, Enum):
    inches = "in"
    mm = "mm"


class ProjectMode(str, Enum):
    wall_art = "wall_art"
    cabinet_front_panel = "cabinet_front_panel"
    architectural_face_panel = "architectural_face_panel"


class BoundaryType(str, Enum):
    rectangle = "rectangle"
    rounded_rectangle = "rounded_rectangle"
    svg_import = "svg_import"


class PatternFamily(str, Enum):
    """Legacy v1 pattern families — kept for migration only."""
    wave_field = "wave_field"
    contour_bands = "contour_bands"
    slat_rib = "slat_rib"


class Symmetry(str, Enum):
    none = "none"
    x = "x"
    y = "y"
    xy = "xy"


class GrainDirection(str, Enum):
    x = "x"
    y = "y"


class DogboneStyle(str, Enum):
    classic = "classic"
    none = "none"


class RotationMode(str, Enum):
    none = "none"
    ninety_only = "90_only"
    any = "any"


class LabelPosition(str, Enum):
    footer = "footer"
    header = "header"
    center = "center"
    centroid = "centroid"
    base = "base"


class ExportFormat(str, Enum):
    dxf = "dxf"
    svg = "svg"
    pdf = "pdf"
    json = "json"


# ---------------------------------------------------------------------------
# v1 legacy config sections (kept for migration)
# ---------------------------------------------------------------------------


class ConfigPattern(BaseModel):
    """Legacy v1 pattern config — used only during v1→v2 migration."""
    family: PatternFamily
    density: float = Field(ge=0, le=1)
    spacing: float = Field(gt=0)
    line_width: float = Field(gt=0)
    amplitude: float = Field(ge=0)
    seed: int = Field(ge=0)
    symmetry: Symmetry


# ---------------------------------------------------------------------------
# Shared config sections (unchanged from v1)
# ---------------------------------------------------------------------------


class ConfigProject(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    mode: ProjectMode
    units: Units


class ConfigBoundary(BaseModel):
    type: BoundaryType
    width: float = Field(gt=0, le=1000)
    height: float = Field(gt=0, le=1000)
    corner_radius: float = Field(ge=0, le=100)
    asset_id: str | None = None
    safe_margin: float = Field(ge=0, le=100)


class ConfigMaterial(BaseModel):
    thickness: float = Field(gt=0, le=100)
    sheet_width: float = Field(gt=0, le=1000)
    sheet_height: float = Field(gt=0, le=1000)
    min_bridge: float = Field(gt=0)
    grain_direction: GrainDirection


class ConfigTool(BaseModel):
    tool_diameter: float = Field(gt=0)
    kerf_allowance: float = Field(ge=0)
    min_inside_radius: float = Field(ge=0)
    dogbone_style: DogboneStyle
    clearance: float = Field(ge=0)
    border_gap: float = Field(ge=0)


class ConfigFabrication(BaseModel):
    material: ConfigMaterial
    tool: ConfigTool


class NestingMode(str, Enum):
    fast = "fast"
    balanced = "balanced"
    max_yield = "max_yield"
    ffd = "ffd"


class ConfigLayout(BaseModel):
    enabled: bool
    copies: int = Field(ge=1)
    rotation_mode: RotationMode
    preserve_grain: bool
    nesting_mode: NestingMode = NestingMode.balanced
    nest_backing: bool = True


class ConfigLabeling(BaseModel):
    enabled: bool
    prefix: str = Field(max_length=10)
    position: LabelPosition


class ConfigExport(BaseModel):
    formats: list[ExportFormat] = Field(min_length=1)
    units: Units


class ConfigReservedAcoustic(BaseModel):
    """Must be present but remains inert in phase 1."""
    enabled: Literal[False] = False
    room_use: None = None
    target_issue: None = None
    room_dimensions: None = None
    surface_summary: None = None
    installation_constraints: None = None
    attachments: list = Field(default_factory=list, max_length=0)


# ---------------------------------------------------------------------------
# v2 config sections — surface + slats + backing
# ---------------------------------------------------------------------------


class SurfaceConfig(BaseModel):
    type: Literal["wave", "terrain", "ripple", "mountain"] = "wave"
    max_depth: float = Field(ge=0.5, le=12.0, default=3.0)
    min_depth: float = Field(ge=0, default=0.0)
    amplitude: float = Field(ge=0, le=1, default=0.7)
    frequency: float = Field(ge=0.5, le=10, default=3.0)
    phase: float = Field(ge=0, le=6.284, default=0.0)
    flow_direction: Literal["x", "y", "radial"] = "x"
    symmetry: Literal["none", "x", "y", "xy"] = "none"
    smoothness: float = Field(ge=0, le=1, default=0.5)
    seed: int = 42
    noise_amount: float = Field(ge=0, le=1, default=0.2)


SlatDistributionMode = Literal["fit_to_boundary", "manual"]


class SlatConfig(BaseModel):
    count: int = Field(ge=5, le=200, default=30)
    spacing: float = Field(ge=0.25, le=100, default=0.75)
    thickness: float = Field(ge=0.125, default=0.75)
    base_height: float = Field(ge=0.5, default=1.5)
    tab_width: float = Field(ge=0.01, default=0.5)
    tab_depth: float = Field(ge=0.25, default=0.75)
    tab_count: int = Field(ge=2, le=6, default=3)
    tab_clearance: float = Field(ge=0, default=0.01)
    distribution_mode: SlatDistributionMode = "fit_to_boundary"


class BackingConfig(BaseModel):
    enabled: bool = True
    width: float = Field(default=48.0, le=1000)
    height: float = Field(default=3.0, le=1000)
    slot_width: float = 0.51  # tab_width + clearance
    slot_depth: float = 0.75
    mounting_holes: bool = True


# ---------------------------------------------------------------------------
# Migration helper
# ---------------------------------------------------------------------------


def migrate_config_v1_to_v2(old: dict) -> dict:
    """Convert a v1 pattern-based config dict to v2 surface+slat config dict."""
    pattern = old.get("pattern", {})
    fab = old.get("fabrication", {})
    mat = fab.get("material", {})
    tool = fab.get("tool", {})

    amplitude = float(pattern.get("amplitude", 0.8))
    density = float(pattern.get("density", 0.65))
    spacing = float(pattern.get("spacing", 0.75))
    thickness = float(mat.get("thickness", 0.75))
    seed = int(pattern.get("seed", 42))
    symmetry = pattern.get("symmetry", "none")

    new = dict(old)
    new["schema_version"] = "2.0.0"
    new["surface"] = {
        "type": "wave",
        "max_depth": max(0.5, amplitude * 4),
        "min_depth": 0.0,
        "amplitude": min(1.0, amplitude),
        "frequency": max(0.5, density * 6),
        "phase": 0.0,
        "flow_direction": "x",
        "symmetry": symmetry if symmetry in ("none", "x", "y", "xy") else "none",
        "smoothness": 0.5,
        "seed": seed,
        "noise_amount": 0.2,
    }
    new["slats"] = {
        "count": 30,
        "spacing": max(0.25, spacing),
        "thickness": thickness,
        "base_height": 1.5,
        "tab_width": 0.5,
        "tab_depth": 0.75,
        "tab_count": 3,
        "tab_clearance": 0.01,
    }
    new["backing"] = {
        "enabled": True,
        "width": float(old.get("boundary", {}).get("width", 48.0)),
        "height": 3.0,
        "slot_width": 0.5 + 0.01,  # tab_width + clearance
        "slot_depth": 0.75,
        "mounting_holes": True,
    }
    # Keep pattern for reference but it won't be used in v2 pipeline
    return new


# ---------------------------------------------------------------------------
# Canonical config (v2)
# ---------------------------------------------------------------------------


class CanonicalConfig(BaseModel):
    schema_version: str = "2.0.0"
    project: ConfigProject
    boundary: ConfigBoundary
    # v2 surface/slats/backing — always present after migration
    surface: SurfaceConfig = Field(default_factory=SurfaceConfig)
    slats: SlatConfig = Field(default_factory=SlatConfig)
    backing: BackingConfig = Field(default_factory=BackingConfig)
    # v1 pattern — optional, kept for migration reference
    pattern: ConfigPattern | None = None
    fabrication: ConfigFabrication
    layout: ConfigLayout
    labeling: ConfigLabeling
    export: ConfigExport
    reserved_acoustic: ConfigReservedAcoustic = Field(default_factory=ConfigReservedAcoustic)

    @model_validator(mode="before")
    @classmethod
    def auto_migrate_v1(cls, data: Any) -> Any:
        if isinstance(data, dict) and data.get("schema_version", "1.0.0") != "2.0.0":
            return migrate_config_v1_to_v2(data)
        return data


# ---------------------------------------------------------------------------
# Config normalizer — single source of truth for derived values
# ---------------------------------------------------------------------------


def normalize_config(config: CanonicalConfig) -> CanonicalConfig:
    """
    Derive dependent values so the rest of the pipeline sees a consistent config.

    - fit_to_boundary mode: recompute spacing from boundary height
    - Always sync slat thickness to material thickness
    - Always derive backing dimensions from boundary/slat config
    """
    updates: dict[str, Any] = {}

    # -- Slat spacing ----------------------------------------------------------
    slat_updates: dict[str, Any] = {}
    mode = config.slats.distribution_mode
    if mode == "fit_to_boundary":
        effective_spacing = (
            (config.boundary.height - 2 * config.boundary.safe_margin)
            / max(config.slats.count - 1, 1)
        )
        slat_updates["spacing"] = effective_spacing

    # -- Sync thickness from material ------------------------------------------
    slat_updates["thickness"] = config.fabrication.material.thickness

    if slat_updates:
        updates["slats"] = config.slats.model_copy(update=slat_updates)

    # -- Derive backing dimensions ---------------------------------------------
    resolved_slats = updates.get("slats", config.slats)
    backing_updates: dict[str, Any] = {
        "width": config.boundary.width,
        "slot_width": resolved_slats.tab_width + resolved_slats.tab_clearance,
        "slot_depth": resolved_slats.tab_depth,
    }
    updates["backing"] = config.backing.model_copy(update=backing_updates)

    return config.model_copy(update=updates)


# ---------------------------------------------------------------------------
# Request / response shapes
# ---------------------------------------------------------------------------


class GenerateRequest(BaseModel):
    config: CanonicalConfig


class ValidateRequest(BaseModel):
    config: CanonicalConfig


class LayoutRequest(BaseModel):
    config: CanonicalConfig


class ExportRequest(BaseModel):
    config: CanonicalConfig
    version_id: str | None = None


class ValidationIssue(BaseModel):
    level: Literal["error", "warning", "info"]
    code: str
    message: str
    field: str | None = None


class ValidationReport(BaseModel):
    valid: bool
    issues: list[ValidationIssue] = Field(default_factory=list)


class PartGeometry(BaseModel):
    """Serialized polygon for 3D rendering — full accurate cut geometry."""
    part_id: str
    part_type: str                              # "slat" | "backing"
    exterior: list[list[float]]                 # [[x, y], ...] exterior ring
    holes: list[list[list[float]]] = []         # [[[x, y], ...], ...] interior rings
    bounding_box: list[float]                   # [minx, miny, maxx, maxy]


class GenerateResult(BaseModel):
    status: Literal["ok", "error"]
    message: str = ""
    validation: ValidationReport = Field(default_factory=lambda: ValidationReport(valid=True))
    svg_preview: str = ""
    part_count: int = 0
    slat_count: int = 0
    has_backing: bool = False
    cut_preview_svg: str = ""          # Sheet layout SVG showing actual cut paths
    sheet_count: int = 0               # Number of material sheets needed
    sheet_utilization: float = 0.0     # Average utilization across sheets (0-1)
    layout_engine: str = ""            # "nesting" or "ffd" — which engine produced the layout
    part_geometries: list[PartGeometry] = Field(default_factory=list)
    generated_at: str = ""


class ExportResult(BaseModel):
    status: Literal["ok", "error"]
    message: str = ""
    filename: str = ""


class ExportManifest(BaseModel):
    schema_version: str = "2.0.0"
    project_name: str
    mode: ProjectMode
    units: Units
    generated_at: str
    files: list[str] = Field(default_factory=list)
