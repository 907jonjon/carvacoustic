/**
 * CarvAcoustic shared TypeScript types — schema version 2.0.0.
 * The Python geometry service maintains equivalent Pydantic models in geometry/app/models.py.
 */

// ---------------------------------------------------------------------------
// Primitives
// ---------------------------------------------------------------------------

export type Units = "in" | "mm";

export type ProjectMode =
  | "wall_art"
  | "cabinet_front_panel"
  | "architectural_face_panel";

export type BoundaryType = "rectangle" | "rounded_rectangle" | "svg_import";

export type Symmetry = "none" | "x" | "y" | "xy";

export type GrainDirection = "x" | "y";

export type DogboneStyle = "classic" | "none";

export type RotationMode = "90_only" | "any" | "none";

export type LabelPosition = "footer" | "header" | "center" | "centroid" | "base";

export type ExportFormat = "dxf" | "svg" | "pdf" | "json";

export type SurfaceType = "wave" | "terrain" | "ripple" | "mountain";

export type NestingMode = "fast" | "balanced" | "max_yield" | "ffd";

export type SlatDistributionMode = "fit_to_boundary" | "manual";

export type FlowDirection = "x" | "y" | "radial";

// ---------------------------------------------------------------------------
// v2 config sections
// ---------------------------------------------------------------------------

export interface ConfigProject {
  name: string;
  mode: ProjectMode;
  units: Units;
}

export interface ConfigBoundary {
  type: BoundaryType;
  width: number;
  height: number;
  corner_radius: number;
  asset_id: string | null;
  safe_margin: number;
}

export interface SurfaceConfig {
  type: SurfaceType;
  max_depth: number;      // 0.5–12 (inches/mm), max height of surface protrusion
  min_depth: number;      // minimum depth (usually 0)
  amplitude: number;      // 0–1, intensity of variation
  frequency: number;      // 0.5–10, number of major undulations
  phase: number;          // 0–2π, shifts the wave pattern
  flow_direction: FlowDirection;
  symmetry: Symmetry;
  smoothness: number;     // 0–1, gaussian blur on height field
  seed: number;
  noise_amount: number;   // 0–1, organic randomness
}

export interface SlatConfig {
  count: number;          // number of slats (5–200)
  spacing: number;        // centre-to-centre spacing
  thickness: number;      // material thickness = sheet stock thickness
  base_height: number;    // height of rectangular base below profile curve
  tab_width: number;      // width of mounting tabs
  tab_depth: number;      // how far tabs extend below base
  tab_count: number;      // number of tabs per slat (2–6)
  tab_clearance: number;  // fit clearance around each tab
  distribution_mode?: SlatDistributionMode; // default: "fit_to_boundary"
}

export interface BackingConfig {
  enabled: boolean;
  width: number;
  height: number;
  slot_width: number;     // = slat thickness + clearance
  slot_depth: number;     // = tab depth
  mounting_holes: boolean;
}

export interface ConfigMaterial {
  thickness: number;
  sheet_width: number;
  sheet_height: number;
  min_bridge: number;
  grain_direction: GrainDirection;
}

export interface ConfigTool {
  tool_diameter: number;
  kerf_allowance: number;
  min_inside_radius: number;
  dogbone_style: DogboneStyle;
  clearance: number;
  border_gap: number;
}

export interface ConfigFabrication {
  material: ConfigMaterial;
  tool: ConfigTool;
}

export interface ConfigLayout {
  enabled: boolean;
  copies: number;
  rotation_mode: RotationMode;
  preserve_grain: boolean;
  nesting_mode: NestingMode;
  nest_backing: boolean;
}

export interface ConfigLabeling {
  enabled: boolean;
  prefix: string;
  position: LabelPosition;
}

export interface ConfigExport {
  formats: ExportFormat[];
  units: Units;
}

export interface ConfigReservedAcoustic {
  enabled: false;
  room_use: null;
  target_issue: null;
  room_dimensions: null;
  surface_summary: null;
  installation_constraints: null;
  attachments: [];
}

// ---------------------------------------------------------------------------
// Canonical config v2
// ---------------------------------------------------------------------------

export interface CanonicalConfig {
  schema_version: string;
  project: ConfigProject;
  boundary: ConfigBoundary;
  surface: SurfaceConfig;
  slats: SlatConfig;
  backing: BackingConfig;
  fabrication: ConfigFabrication;
  layout: ConfigLayout;
  labeling: ConfigLabeling;
  export: ConfigExport;
  reserved_acoustic: ConfigReservedAcoustic;
}

// ---------------------------------------------------------------------------
// Default config factory
// ---------------------------------------------------------------------------

export function defaultConfig(
  name: string,
  mode: ProjectMode = "wall_art",
  units: Units = "in"
): CanonicalConfig {
  return {
    schema_version: "2.0.0",
    project: { name, mode, units },
    boundary: {
      type: "rectangle",
      width: 48,
      height: 24,
      corner_radius: 0,
      asset_id: null,
      safe_margin: 0.5,
    },
    surface: {
      type: "wave",
      max_depth: 3.0,
      min_depth: 0.0,
      amplitude: 0.7,
      frequency: 3.0,
      phase: 0.0,
      flow_direction: "x",
      symmetry: "none",
      smoothness: 0.5,
      seed: 42,
      noise_amount: 0.2,
    },
    slats: {
      count: 30,
      spacing: 0.75,
      thickness: 0.75,
      base_height: 1.5,
      tab_width: 0.5,
      tab_depth: 0.75,
      tab_count: 3,
      tab_clearance: 0.01,
      distribution_mode: "fit_to_boundary",
    },
    backing: {
      enabled: true,
      width: 48,
      height: 3.0,
      slot_width: 0.76,
      slot_depth: 0.75,
      mounting_holes: true,
    },
    fabrication: {
      material: {
        thickness: 0.75,
        sheet_width: 96,
        sheet_height: 48,
        min_bridge: 0.3,
        grain_direction: "x",
      },
      tool: {
        tool_diameter: 0.25,
        kerf_allowance: 0.0,
        min_inside_radius: 0.125,
        dogbone_style: "classic",
        clearance: 0.125,
        border_gap: 0.75,
      },
    },
    layout: {
      enabled: true,
      copies: 1,
      rotation_mode: "90_only",
      preserve_grain: false,
      nesting_mode: "balanced",
      nest_backing: true,
    },
    labeling: {
      enabled: true,
      prefix: "S",
      position: "footer",
    },
    export: {
      formats: ["dxf", "svg", "pdf", "json"],
      units,
    },
    reserved_acoustic: {
      enabled: false,
      room_use: null,
      target_issue: null,
      room_dimensions: null,
      surface_summary: null,
      installation_constraints: null,
      attachments: [],
    },
  };
}

// ---------------------------------------------------------------------------
// API shape types
// ---------------------------------------------------------------------------

export interface CreateProjectBody {
  name: string;
  mode: ProjectMode;
  units: Units;
}

export interface UpdateProjectBody {
  name?: string;
  draft_config?: CanonicalConfig;
}

export interface CreateVersionBody {
  config: CanonicalConfig;
  notes?: string;
}

export interface ApiError {
  error: {
    code: string;
    message: string;
  };
}
