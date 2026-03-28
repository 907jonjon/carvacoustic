import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { CreateProjectBodySchema, defaultConfig } from "@/types/schema";
import type { ApiError } from "@/types/schema";

function apiError(code: string, message: string, status = 400): NextResponse<ApiError> {
  return NextResponse.json({ error: { code, message } }, { status });
}

/** POST /api/projects — create a new project */
export async function POST(request: Request) {
  const supabase = await createClient();

  const { data: { user }, error: authError } = await supabase.auth.getUser();
  if (authError || !user) {
    return apiError("unauthenticated", "Authentication required.", 401);
  }

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return apiError("invalid_json", "Request body must be valid JSON.");
  }

  const parsed = CreateProjectBodySchema.safeParse(body);
  if (!parsed.success) {
    return apiError(
      "validation_error",
      parsed.error.errors.map((e) => e.message).join("; ")
    );
  }

  const { name, mode, units } = parsed.data;
  const draft_config = defaultConfig(name, mode, units);

  const { data: project, error: insertError } = await supabase
    .from("projects")
    .insert({ owner_id: user.id, name, mode, units, draft_config })
    .select()
    .single();

  if (insertError || !project) {
    console.error("Project insert failed:", insertError);
    return apiError("database_error", "Database error.", 500);
  }

  return NextResponse.json(project, { status: 201 });
}

/** GET /api/projects — list projects for the authenticated user */
export async function GET() {
  const supabase = await createClient();

  const { data: { user }, error: authError } = await supabase.auth.getUser();
  if (authError || !user) {
    return apiError("unauthenticated", "Authentication required.", 401);
  }

  const { data: projects, error } = await supabase
    .from("projects")
    .select("id, name, mode, units, draft_config, latest_version_id, created_at, updated_at")
    .eq("owner_id", user.id)
    .order("updated_at", { ascending: false });

  if (error) {
    return apiError("database_error", error.message, 500);
  }

  return NextResponse.json(projects);
}
