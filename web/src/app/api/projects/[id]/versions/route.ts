import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { CreateVersionBodySchema } from "@/types/schema";
import type { ApiError, CanonicalConfig } from "@/types/schema";

function apiError(code: string, message: string, status = 400): NextResponse<ApiError> {
  return NextResponse.json({ error: { code, message } }, { status });
}

/** POST /api/projects/:id/versions — create an immutable checkpoint */
export async function POST(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const supabase = await createClient();

  const { data: { user }, error: authError } = await supabase.auth.getUser();
  if (authError || !user) return apiError("unauthenticated", "Authentication required.", 401);

  // Verify ownership
  const { data: project, error: fetchError } = await supabase
    .from("projects")
    .select("id, owner_id")
    .eq("id", id)
    .eq("owner_id", user.id)
    .single();

  if (fetchError || !project) return apiError("not_found", "Project not found.", 404);

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return apiError("invalid_json", "Request body must be valid JSON.");
  }

  const parsed = CreateVersionBodySchema.safeParse(body);
  if (!parsed.success) {
    return apiError("validation_error", parsed.error.errors.map((e) => e.message).join("; "));
  }

  // Determine next version number
  const { data: latest } = await supabase
    .from("project_versions")
    .select("version_number")
    .eq("project_id", id)
    .order("version_number", { ascending: false })
    .limit(1)
    .single();

  const nextVersion = (latest?.version_number ?? 0) + 1;

  const { data: version, error: insertError } = await supabase
    .from("project_versions")
    .insert({
      project_id: id,
      version_number: nextVersion,
      config: parsed.data.config as unknown as CanonicalConfig,
      notes: parsed.data.notes ?? null,
    })
    .select()
    .single();

  if (insertError || !version) {
    return apiError("database_error", insertError?.message ?? "Insert failed.", 500);
  }

  // Update project's latest_version_id and sync draft_config to the saved config
  await supabase
    .from("projects")
    .update({
      latest_version_id: version.id,
      draft_config: parsed.data.config as unknown as CanonicalConfig,  // Zod output is structurally compatible; surface is optional for v1 compat
      updated_at: new Date().toISOString(),
    })
    .eq("id", id);

  return NextResponse.json(version, { status: 201 });
}

/** GET /api/projects/:id/versions — list all versions */
export async function GET(
  _request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const supabase = await createClient();

  const { data: { user }, error: authError } = await supabase.auth.getUser();
  if (authError || !user) return apiError("unauthenticated", "Authentication required.", 401);

  // Verify ownership
  const { data: project, error: fetchError } = await supabase
    .from("projects")
    .select("id")
    .eq("id", id)
    .eq("owner_id", user.id)
    .single();

  if (fetchError || !project) return apiError("not_found", "Project not found.", 404);

  const { data: versions, error } = await supabase
    .from("project_versions")
    .select("*")
    .eq("project_id", id)
    .order("version_number", { ascending: false });

  if (error) return apiError("database_error", error.message, 500);

  return NextResponse.json(versions);
}
