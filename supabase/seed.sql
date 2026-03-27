-- CarvAcoustic seed data
-- Inserts default material and tool presets for all users.
-- Run after migrations.

-- Default material presets
INSERT INTO public.material_presets
  (name, thickness, sheet_width, sheet_height, min_bridge, grain_direction, is_default)
VALUES
  ('3/4" MDF (48×96)',   0.75, 96, 48, 0.30, 'x', TRUE),
  ('1/2" MDF (48×96)',   0.50, 96, 48, 0.25, 'x', TRUE),
  ('1/4" MDF (48×96)',   0.25, 96, 48, 0.20, 'x', TRUE),
  ('3/4" Plywood (48×96)', 0.75, 96, 48, 0.35, 'x', TRUE),
  ('3/4" MDF (48×96) mm', 19.05, 2438.4, 1219.2, 7.62, 'x', TRUE)
ON CONFLICT DO NOTHING;

-- Default tool presets
INSERT INTO public.tool_presets
  (name, tool_diameter, kerf_allowance, min_inside_radius, dogbone_style, clearance, border_gap, is_default)
VALUES
  ('1/4" Upcut Spiral',  0.250, 0.0, 0.125, 'classic', 0.125, 0.75, TRUE),
  ('1/8" Upcut Spiral',  0.125, 0.0, 0.063, 'classic', 0.063, 0.50, TRUE),
  ('3/8" Upcut Spiral',  0.375, 0.0, 0.188, 'classic', 0.188, 1.00, TRUE),
  ('6mm Upcut Spiral mm', 6.0,  0.0, 3.0,   'classic', 3.0,   19.0, TRUE)
ON CONFLICT DO NOTHING;
