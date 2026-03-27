/**
 * CarvAcoustic shared TypeScript types.
 * These are the canonical types derived from config-schema.json (schema version 1.0.0).
 * Import into the web app from web/src/types/schema.ts which re-exports these.
 * The Python geometry service maintains equivalent Pydantic models in geometry/app/models.py.
 */

// ---------------------------------------------------------------------------
// Primitives
// ---------------------------------------------------------------------------

export type Units = "in" | "mm";

/** Phase-1 decorative modes only. Acoustic modes are reserved for future phases. */
export type ProjectMode =
  | "wall_art"
  | "cabinet_front_panel"
  | "architectural_face_panel";

/** Reserved — do not use in phase 1. */
export type ReservedFutureMode =
  | "acoustic_wall_absorber"
  | "acoustic_cloud"
  | "acoustic_resonant_panel";

export type BoundaryType = "rectangle" | "rounded_rectangle" | "svg_import";

/** Approved phase-1 pattern families. Do not add more without approval. */
export type PatternFamily = "wave_field" | "contour_bands" | "slat_rib";

export type Symmetry = "none" | "x" | "y" | "xy";

export type GrainDirection = "x" | "y";

export type DogboneStyle = "classic" | "none";

export type RotationMode = "90_only" | "any" | "none";

export type LabelPosition = "footer" | "header" | "center";

export type ExportFormat = "dxf" | "svg" | "pdf" | "json";

// ---------------------------------------------------------------------------
// Canonical config sections
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

export interface ConfigPattern {
  family: PatternFamily;
  density: number;
  spacing: number;
  line_width: number;
  amplitude: number;
  seed: number;
  symmetry: Symmetry;
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

/**
 * Reserved acoustic intake block.
 * Must be present in every config but must remain inert in phase 1.
 * enabled is always false; all fields are null/empty.
 */
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
// Canonical config — source of truth
// ---------------------------------------------------------------------------

export interface CanonicalConfig {
  schema_version: string;
  project: ConfigProject;
  boundary: ConfigBoundary;
  pattern: ConfigPattern;
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
    schema_version: "1.0.0",
    project: { name, mode, units },
    boundary: {
      type: "rectangle",
      width: 48,
      height: 24,
      corner_radius: 0,
      asset_id: null,
      safe_margin: 1.0,
    },
    pattern: {
      family: "wave_field",
      density: 0.65,
      spacing: 1.2,
      line_width: 0.4,
      amplitude: 0.8,
      seed: 42,
      symmetry: "none",
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
    },
    labeling: {
      enabled: true,
      prefix: "P",
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

/** POST /api/projects request body */
export interface CreateProjectBody {
  name: string;
  mode: ProjectMode;
  units: Units;
}

/** PATCH /api/projects/:id request body */
export interface UpdateProjectBody {
  name?: string;
  draft_config?: CanonicalConfig;
}

/** POST /api/projects/:id/versions request body */
export interface CreateVersionBody {
  config: CanonicalConfig;
  notes?: string;
}

/** Standard error response shape */
export interface ApiError {
  error: {
    code: string;
    message: string;
  };
}
