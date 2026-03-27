"""
CarvAcoustic geometry service — Pydantic models.
These mirror the canonical config schema in shared/config-schema.json.
The web app's TypeScript types in shared/types.ts are the authoritative source.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


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
    """Approved phase-1 pattern families. Do not add more without approval."""
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


class ExportFormat(str, Enum):
    dxf = "dxf"
    svg = "svg"
    pdf = "pdf"
    json = "json"


# ---------------------------------------------------------------------------
# Config sections
# ---------------------------------------------------------------------------


class ConfigProject(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    mode: ProjectMode
    units: Units


class ConfigBoundary(BaseModel):
    type: BoundaryType
    width: float = Field(gt=0)
    height: float = Field(gt=0)
    corner_radius: float = Field(ge=0)
    asset_id: str | None
    safe_margin: float = Field(ge=0)


class ConfigPattern(BaseModel):
    family: PatternFamily
    density: float = Field(ge=0, le=1)
    spacing: float = Field(gt=0)
    line_width: float = Field(gt=0)
    amplitude: float = Field(ge=0)
    seed: int = Field(ge=0)
    symmetry: Symmetry


class ConfigMaterial(BaseModel):
    thickness: float = Field(gt=0)
    sheet_width: float = Field(gt=0)
    sheet_height: float = Field(gt=0)
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


class ConfigLayout(BaseModel):
    enabled: bool
    copies: int = Field(ge=1)
    rotation_mode: RotationMode
    preserve_grain: bool


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
# Canonical config
# ---------------------------------------------------------------------------


class CanonicalConfig(BaseModel):
    schema_version: str = "1.0.0"
    project: ConfigProject
    boundary: ConfigBoundary
    pattern: ConfigPattern
    fabrication: ConfigFabrication
    layout: ConfigLayout
    labeling: ConfigLabeling
    export: ConfigExport
    reserved_acoustic: ConfigReservedAcoustic = Field(default_factory=ConfigReservedAcoustic)


# ---------------------------------------------------------------------------
# Request / response shapes (stubs for Milestone B+)
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


class GenerateResult(BaseModel):
    """Placeholder — populated in Milestone B."""
    status: Literal["ok", "error"]
    message: str = ""
    validation: ValidationReport | None = None


class ExportManifest(BaseModel):
    schema_version: str = "1.0.0"
    project_name: str
    mode: ProjectMode
    units: Units
    generated_at: str
    files: list[str] = Field(default_factory=list)
