import { NextResponse } from "next/server";
import { z } from "zod";
import { createClient } from "@/lib/supabase/server";
import type { ApiError } from "@/types/schema";

function apiError(code: string, message: string, status = 400): NextResponse<ApiError> {
  return NextResponse.json({ error: { code, message } }, { status });
}

const CreateMaterialPresetSchema = z.object({
  name: z.string().min(1).max(100),
  thickness: z.number().positive(),
  sheet_width: z.number().positive(),
  sheet_height: z.number().positive(),
  min_bridge: z.number().positive(),
  grain_direction: z.enum(["x", "y"]).default("x"),
  is_default: z.boolean().default(false),
});

/** GET /api/presets/materials */
export async function GET() {
  const supabase = await createClient();

  const { data: { user }, error: authError } = await supabase.auth.getUser();
  if (authError || !user) return apiError("unauthenticated", "Authentication required.", 401);

  const { data, error } = await supabase
    .from("material_presets")
    .select("*")
    .or(`owner_id.eq.${user.id},is_default.eq.true`)
    .order("is_default", { ascending: false })
    .order("name");

  if (error) return apiError("database_error", error.message, 500);

  return NextResponse.json(data);
}

/** POST /api/presets/materials */
export async function POST(request: Request) {
  const supabase = await createClient();

  const { data: { user }, error: authError } = await supabase.auth.getUser();
  if (authError || !user) return apiError("unauthenticated", "Authentication required.", 401);

  let body: unknown;
  try { body = await request.json(); } catch {
    return apiError("invalid_json", "Request body must be valid JSON.");
  }

  const parsed = CreateMaterialPresetSchema.safeParse(body);
  if (!parsed.success) {
    return apiError("validation_error", parsed.error.errors.map((e) => e.message).join("; "));
  }

  const { data, error } = await supabase
    .from("material_presets")
    .insert({ ...parsed.data, owner_id: user.id })
    .select()
    .single();

  if (error || !data) return apiError("database_error", error?.message ?? "Insert failed.", 500);

  return NextResponse.json(data, { status: 201 });
}
