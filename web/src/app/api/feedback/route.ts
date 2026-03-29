import { NextResponse } from "next/server";
import { z } from "zod";
import { createClient } from "@/lib/supabase/server";
import type { ApiError } from "@/types/schema";

function apiError(code: string, message: string, status = 400): NextResponse<ApiError> {
  return NextResponse.json({ error: { code, message } }, { status });
}

const FeedbackSchema = z.object({
  category: z.string().min(1).max(50),
  message: z.string().min(1).max(2000),
  project_id: z.string().optional(),
  config_snapshot: z.record(z.unknown()).optional(),
});

/** POST /api/feedback */
export async function POST(request: Request) {
  const supabase = await createClient();

  const { data: { user }, error: authError } = await supabase.auth.getUser();
  if (authError || !user) return apiError("unauthenticated", "Authentication required.", 401);

  let body: unknown;
  try { body = await request.json(); } catch {
    return apiError("invalid_json", "Request body must be valid JSON.");
  }

  const parsed = FeedbackSchema.safeParse(body);
  if (!parsed.success) {
    return apiError("validation_error", parsed.error.errors.map((e) => e.message).join("; "));
  }

  const { data, error } = await supabase
    .from("feedback_submissions")
    .insert({
      user_id: user.id,
      category: parsed.data.category,
      message: parsed.data.message,
      project_id: parsed.data.project_id ?? null,
      config_snapshot: (parsed.data.config_snapshot as import("@/types/database").Json) ?? null,
    })
    .select()
    .single();

  if (error || !data) {
    console.error("Feedback insert failed:", error);
    return apiError("database_error", "Database error.", 500);
  }

  return NextResponse.json(data, { status: 201 });
}
