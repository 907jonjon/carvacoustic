-- CarvAcoustic — initial schema
-- Run via: supabase db push
-- Or paste into the Supabase SQL editor.

-- ─────────────────────────────────────────────
-- PROFILES
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.profiles (
  id           UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email        TEXT,
  display_name TEXT,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own profile"
  ON public.profiles FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "Users can update their own profile"
  ON public.profiles FOR UPDATE
  USING (auth.uid() = id);

-- Auto-create profile on user sign-up
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER SET search_path = public
AS $$
BEGIN
  INSERT INTO public.profiles (id, email)
  VALUES (NEW.id, NEW.email)
  ON CONFLICT (id) DO NOTHING;
  RETURN NEW;
END;
$$;

CREATE OR REPLACE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ─────────────────────────────────────────────
-- PROJECTS
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.projects (
  id                UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_id          UUID        NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  name              TEXT        NOT NULL CHECK (char_length(name) BETWEEN 1 AND 200),
  mode              TEXT        NOT NULL CHECK (mode IN (
                                  'wall_art',
                                  'cabinet_front_panel',
                                  'architectural_face_panel'
                                )),
  units             TEXT        NOT NULL DEFAULT 'in' CHECK (units IN ('in', 'mm')),
  draft_config      JSONB       NOT NULL DEFAULT '{}',
  latest_version_id UUID,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can CRUD their own projects"
  ON public.projects FOR ALL
  USING (auth.uid() = owner_id)
  WITH CHECK (auth.uid() = owner_id);

-- ─────────────────────────────────────────────
-- PROJECT VERSIONS (immutable snapshots)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.project_versions (
  id             UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id     UUID        NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
  version_number INTEGER     NOT NULL,
  config         JSONB       NOT NULL,
  notes          TEXT,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (project_id, version_number)
);

ALTER TABLE public.project_versions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read versions of their projects"
  ON public.project_versions FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.projects p
      WHERE p.id = project_id AND p.owner_id = auth.uid()
    )
  );

CREATE POLICY "Users can insert versions for their projects"
  ON public.project_versions FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.projects p
      WHERE p.id = project_id AND p.owner_id = auth.uid()
    )
  );

-- No UPDATE or DELETE on versions — immutable by design.

-- ─────────────────────────────────────────────
-- MATERIAL PRESETS
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.material_presets (
  id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_id        UUID        REFERENCES public.profiles(id) ON DELETE SET NULL,
  name            TEXT        NOT NULL CHECK (char_length(name) BETWEEN 1 AND 100),
  thickness       NUMERIC     NOT NULL CHECK (thickness > 0),
  sheet_width     NUMERIC     NOT NULL CHECK (sheet_width > 0),
  sheet_height    NUMERIC     NOT NULL CHECK (sheet_height > 0),
  min_bridge      NUMERIC     NOT NULL CHECK (min_bridge > 0),
  grain_direction TEXT        NOT NULL DEFAULT 'x' CHECK (grain_direction IN ('x', 'y')),
  is_default      BOOLEAN     NOT NULL DEFAULT FALSE,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE public.material_presets ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own and default material presets"
  ON public.material_presets FOR SELECT
  USING (owner_id = auth.uid() OR is_default = TRUE);

CREATE POLICY "Users can manage their own material presets"
  ON public.material_presets FOR ALL
  USING (owner_id = auth.uid())
  WITH CHECK (owner_id = auth.uid());

-- ─────────────────────────────────────────────
-- TOOL PRESETS
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.tool_presets (
  id                UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_id          UUID        REFERENCES public.profiles(id) ON DELETE SET NULL,
  name              TEXT        NOT NULL CHECK (char_length(name) BETWEEN 1 AND 100),
  tool_diameter     NUMERIC     NOT NULL CHECK (tool_diameter > 0),
  kerf_allowance    NUMERIC     NOT NULL DEFAULT 0 CHECK (kerf_allowance >= 0),
  min_inside_radius NUMERIC     NOT NULL CHECK (min_inside_radius >= 0),
  dogbone_style     TEXT        NOT NULL DEFAULT 'classic' CHECK (dogbone_style IN ('classic', 'none')),
  clearance         NUMERIC     NOT NULL CHECK (clearance >= 0),
  border_gap        NUMERIC     NOT NULL CHECK (border_gap >= 0),
  is_default        BOOLEAN     NOT NULL DEFAULT FALSE,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE public.tool_presets ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own and default tool presets"
  ON public.tool_presets FOR SELECT
  USING (owner_id = auth.uid() OR is_default = TRUE);

CREATE POLICY "Users can manage their own tool presets"
  ON public.tool_presets FOR ALL
  USING (owner_id = auth.uid())
  WITH CHECK (owner_id = auth.uid());

-- ─────────────────────────────────────────────
-- ASSETS (uploaded boundary SVGs, future uploads)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.assets (
  id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_id     UUID        NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  name         TEXT        NOT NULL,
  type         TEXT        NOT NULL DEFAULT 'boundary_svg',
  storage_path TEXT        NOT NULL,
  file_size    INTEGER,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE public.assets ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can CRUD their own assets"
  ON public.assets FOR ALL
  USING (auth.uid() = owner_id)
  WITH CHECK (auth.uid() = owner_id);

-- ─────────────────────────────────────────────
-- EXPORT BUNDLES (immutable — never overwrite)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.export_bundles (
  id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id   UUID        NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
  version_id   UUID        REFERENCES public.project_versions(id) ON DELETE SET NULL,
  storage_path TEXT        NOT NULL,
  manifest     JSONB,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE public.export_bundles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read export bundles for their projects"
  ON public.export_bundles FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.projects p
      WHERE p.id = project_id AND p.owner_id = auth.uid()
    )
  );

CREATE POLICY "Users can insert export bundles for their projects"
  ON public.export_bundles FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.projects p
      WHERE p.id = project_id AND p.owner_id = auth.uid()
    )
  );

-- No UPDATE or DELETE — immutable by design.

-- ─────────────────────────────────────────────
-- STORAGE BUCKETS
-- (Run these after the tables, or via the Supabase dashboard)
-- ─────────────────────────────────────────────
-- INSERT INTO storage.buckets (id, name, public)
--   VALUES ('boundary-assets', 'boundary-assets', false)
--   ON CONFLICT (id) DO NOTHING;
--
-- INSERT INTO storage.buckets (id, name, public)
--   VALUES ('export-bundles', 'export-bundles', false)
--   ON CONFLICT (id) DO NOTHING;
--
-- INSERT INTO storage.buckets (id, name, public)
--   VALUES ('reserved-future-intake', 'reserved-future-intake', false)
--   ON CONFLICT (id) DO NOTHING;
