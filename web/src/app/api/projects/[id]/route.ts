import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { UpdateProjectBodySchema } from "@/types/schema";
import type { ApiError } from "@/types/schema";

function apiError(code: string, message: string, status = 400): NextResponse<ApiError> {
  return NextResponse.json({ error: { code, message } }, { status });
}

async function getAuthedProject(supabase: Awaited<ReturnType<typeof createClient>>, userId: string, projectId: string) {
  const { data, error } = await supabase
    .from("projects")
    .select("*")
    .eq("id", projectId)
    .eq("owner_id", userId)
    .single();
  return { project: data, error };
}

/** GET /api/projects/:id */
export async function GET(
  _request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const supabase = await createClient();

  const { data: { user }, error: authError } = await supabase.auth.getUser();
  if (authError || !user) return apiError("unauthenticated", "Authentication required.", 401);

  const { project, error } = await getAuthedProject(supabase, user.id, id);
  if (error || !project) return apiError("not_found", "Project not found.", 404);

  return NextResponse.json(project);
}

/** PATCH /api/projects/:id — update name and/or draft_config */
export async function PATCH(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const supabase = await createClient();

  const { data: { user }, error: authError } = await supabase.auth.getUser();
  if (authError || !user) return apiError("unauthenticated", "Authentication required.", 401);

  const { project, error: fetchError } = await getAuthedProject(supabase, user.id, id);
  if (fetchError || !project) return apiError("not_found", "Project not found.", 404);

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return apiError("invalid_json", "Request body must be valid JSON.");
  }

  const parsed = UpdateProjectBodySchema.safeParse(body);
  if (!parsed.success) {
    return apiError("validation_error", parsed.error.errors.map((e) => e.message).join("; "));
  }

  const updates: Record<string, unknown> = { updated_at: new Date().toISOString() };
  if (parsed.data.name !== undefined) updates.name = parsed.data.name;
  if (parsed.data.draft_config !== undefined) updates.draft_config = parsed.data.draft_config;

  const { data: updated, error: updateError } = await supabase
    .from("projects")
    .update(updates)
    .eq("id", id)
    .eq("owner_id", user.id)
    .select()
    .single();

  if (updateError || !updated) {
    console.error("Project update failed:", updateError);
    return apiError("database_error", "Database error.", 500);
  }

  return NextResponse.json(updated);
}

/** DELETE /api/projects/:id */
export async function DELETE(
  _request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const supabase = await createClient();

  const { data: { user }, error: authError } = await supabase.auth.getUser();
  if (authError || !user) return apiError("unauthenticated", "Authentication required.", 401);

  const { project, error: fetchError } = await getAuthedProject(supabase, user.id, id);
  if (fetchError || !project) return apiError("not_found", "Project not found.", 404);

  const { error: deleteError } = await supabase
    .from("projects")
    .delete()
    .eq("id", id)
    .eq("owner_id", user.id);

  if (deleteError) {
    console.error("Project delete failed:", deleteError);
    return apiError("database_error", "Database error.", 500);
  }

  return new NextResponse(null, { status: 204 });
}
