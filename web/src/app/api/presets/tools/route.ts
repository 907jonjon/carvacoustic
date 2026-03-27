import { NextResponse } from "next/server";
import { z } from "zod";
import { createClient } from "@/lib/supabase/server";
import type { ApiError } from "@/types/schema";

function apiError(code: string, message: string, status = 400): NextResponse<ApiError> {
  return NextResponse.json({ error: { code, message } }, { status });
}

const CreateToolPresetSchema = z.object({
  name: z.string().min(1).max(100),
  tool_diameter: z.number().positive(),
  kerf_allowance: z.number().min(0).default(0),
  min_inside_radius: z.number().min(0),
  dogbone_style: z.enum(["classic", "none"]).default("classic"),
  clearance: z.number().min(0),
  border_gap: z.number().min(0),
  is_default: z.boolean().default(false),
});

/** GET /api/presets/tools */
export async function GET() {
  const supabase = await createClient();

  const { data: { user }, error: authError } = await supabase.auth.getUser();
  if (authError || !user) return apiError("unauthenticated", "Authentication required.", 401);

  const { data, error } = await supabase
    .from("tool_presets")
    .select("*")
    .or(`owner_id.eq.${user.id},is_default.eq.true`)
    .order("is_default", { ascending: false })
    .order("name");

  if (error) return apiError("database_error", error.message, 500);

  return NextResponse.json(data);
}

/** POST /api/presets/tools */
export async function POST(request: Request) {
  const supabase = await createClient();

  const { data: { user }, error: authError } = await supabase.auth.getUser();
  if (authError || !user) return apiError("unauthenticated", "Authentication required.", 401);

  let body: unknown;
  try { body = await request.json(); } catch {
    return apiError("invalid_json", "Request body must be valid JSON.");
  }

  const parsed = CreateToolPresetSchema.safeParse(body);
  if (!parsed.success) {
    return apiError("validation_error", parsed.error.errors.map((e) => e.message).join("; "));
  }

  const { data, error } = await supabase
    .from("tool_presets")
    .insert({ ...parsed.data, owner_id: user.id })
    .select()
    .single();

  if (error || !data) return apiError("database_error", error?.message ?? "Insert failed.", 500);

  return NextResponse.json(data, { status: 201 });
}
