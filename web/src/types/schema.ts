/**
 * Re-export canonical types from shared/types.ts.
 * Also provides Zod schemas for runtime validation in API routes.
 */

export type {
  Units,
  ProjectMode,
  ReservedFutureMode,
  BoundaryType,
  PatternFamily,
  Symmetry,
  GrainDirection,
  DogboneStyle,
  RotationMode,
  LabelPosition,
  ExportFormat,
  ConfigProject,
  ConfigBoundary,
  ConfigPattern,
  ConfigMaterial,
  ConfigTool,
  ConfigFabrication,
  ConfigLayout,
  ConfigLabeling,
  ConfigExport,
  ConfigReservedAcoustic,
  CanonicalConfig,
  CreateProjectBody,
  UpdateProjectBody,
  CreateVersionBody,
  ApiError,
} from "../../../shared/types";

export { defaultConfig } from "../../../shared/types";

// ---------------------------------------------------------------------------
// Zod runtime validators
// ---------------------------------------------------------------------------

import { z } from "zod";

export const ProjectModeSchema = z.enum([
  "wall_art",
  "cabinet_front_panel",
  "architectural_face_panel",
]);

export const UnitsSchema = z.enum(["in", "mm"]);

export const BoundaryTypeSchema = z.enum([
  "rectangle",
  "rounded_rectangle",
  "svg_import",
]);

export const PatternFamilySchema = z.enum([
  "wave_field",
  "contour_bands",
  "slat_rib",
]);

export const SymmetrySchema = z.enum(["none", "x", "y", "xy"]);

export const GrainDirectionSchema = z.enum(["x", "y"]);

export const DogboneStyleSchema = z.enum(["classic", "none"]);

export const RotationModeSchema = z.enum(["90_only", "any", "none"]);

export const LabelPositionSchema = z.enum(["footer", "header", "center"]);

export const ExportFormatSchema = z.enum(["dxf", "svg", "pdf", "json"]);

export const ConfigProjectSchema = z.object({
  name: z.string().min(1).max(200),
  mode: ProjectModeSchema,
  units: UnitsSchema,
});

export const ConfigBoundarySchema = z.object({
  type: BoundaryTypeSchema,
  width: z.number().positive(),
  height: z.number().positive(),
  corner_radius: z.number().min(0),
  asset_id: z.string().nullable(),
  safe_margin: z.number().min(0),
});

export const ConfigPatternSchema = z.object({
  family: PatternFamilySchema,
  density: z.number().min(0).max(1),
  spacing: z.number().positive(),
  line_width: z.number().positive(),
  amplitude: z.number().min(0),
  seed: z.number().int().min(0),
  symmetry: SymmetrySchema,
});

export const ConfigMaterialSchema = z.object({
  thickness: z.number().positive(),
  sheet_width: z.number().positive(),
  sheet_height: z.number().positive(),
  min_bridge: z.number().positive(),
  grain_direction: GrainDirectionSchema,
});

export const ConfigToolSchema = z.object({
  tool_diameter: z.number().positive(),
  kerf_allowance: z.number().min(0),
  min_inside_radius: z.number().min(0),
  dogbone_style: DogboneStyleSchema,
  clearance: z.number().min(0),
  border_gap: z.number().min(0),
});

export const ConfigFabricationSchema = z.object({
  material: ConfigMaterialSchema,
  tool: ConfigToolSchema,
});

export const ConfigLayoutSchema = z.object({
  enabled: z.boolean(),
  copies: z.number().int().min(1),
  rotation_mode: RotationModeSchema,
  preserve_grain: z.boolean(),
});

export const ConfigLabelingSchema = z.object({
  enabled: z.boolean(),
  prefix: z.string().max(10),
  position: LabelPositionSchema,
});

export const ConfigExportSchema = z.object({
  formats: z.array(ExportFormatSchema).min(1),
  units: UnitsSchema,
});

export const ConfigReservedAcousticSchema = z.object({
  enabled: z.literal(false),
  room_use: z.null(),
  target_issue: z.null(),
  room_dimensions: z.null(),
  surface_summary: z.null(),
  installation_constraints: z.null(),
  attachments: z.array(z.never()),
});

export const CanonicalConfigSchema = z.object({
  schema_version: z.string().regex(/^\d+\.\d+\.\d+$/),
  project: ConfigProjectSchema,
  boundary: ConfigBoundarySchema,
  pattern: ConfigPatternSchema,
  fabrication: ConfigFabricationSchema,
  layout: ConfigLayoutSchema,
  labeling: ConfigLabelingSchema,
  export: ConfigExportSchema,
  reserved_acoustic: ConfigReservedAcousticSchema,
});

export const CreateProjectBodySchema = z.object({
  name: z.string().min(1).max(200),
  mode: ProjectModeSchema,
  units: UnitsSchema.default("in"),
});

export const UpdateProjectBodySchema = z.object({
  name: z.string().min(1).max(200).optional(),
  draft_config: CanonicalConfigSchema.optional(),
});

export const CreateVersionBodySchema = z.object({
  config: CanonicalConfigSchema,
  notes: z.string().max(500).optional(),
});
