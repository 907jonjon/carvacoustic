import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { canGenerate } from "@/lib/billing/access";
import { CanonicalConfigSchema } from "@/types/schema";
import type { ApiError } from "@/types/schema";
import { z } from "zod";

export const maxDuration = 60;

function apiError(code: string, message: string, status = 400): NextResponse<ApiError> {
  return NextResponse.json({ error: { code, message } }, { status });
}

const RequestSchema = z.object({ config: CanonicalConfigSchema });

/** POST /api/generate-stream — SSE proxy to geometry service */
export async function POST(request: Request) {
  const supabase = await createClient();
  const { data: { user }, error: authError } = await supabase.auth.getUser();
  if (authError || !user) return apiError("unauthenticated", "Authentication required.", 401);

  const genAccess = await canGenerate(user.id);
  if (!genAccess.allowed) {
    return apiError("rate_limit", genAccess.reason ?? "Rate limit reached.", 429);
  }

  let body: unknown;
  try { body = await request.json(); } catch {
    return apiError("invalid_json", "Request body must be valid JSON.");
  }

  const parsed = RequestSchema.safeParse(body);
  if (!parsed.success) {
    return apiError("validation_error", parsed.error.errors.map((e) => e.message).join("; "));
  }

  const geoUrl = process.env.GEOMETRY_SERVICE_URL ?? "http://localhost:8001";
  const geoKey = process.env.GEOMETRY_SERVICE_API_KEY ?? "";

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 55000);

  let geoRes: Response;
  try {
    geoRes = await fetch(`${geoUrl}/generate-stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": geoKey,
      },
      body: JSON.stringify(parsed.data),
      signal: controller.signal,
    });
  } catch (err) {
    clearTimeout(timeout);
    if (err instanceof DOMException && err.name === "AbortError") {
      return apiError("timeout", "Geometry service took too long to respond. Try again — the service may be warming up.", 504);
    }
    return apiError(
      "geometry_service_unavailable",
      "Geometry service is not reachable. Make sure it is running on port 8001.",
      503
    );
  } finally {
    clearTimeout(timeout);
  }

  if (!geoRes.ok) {
    const detail = await geoRes.text();
    console.error("Generate-stream service error:", geoRes.status, detail);
    return apiError("generate_failed", `Geometry service error (${geoRes.status}).`, geoRes.status);
  }

  // Record usage event
  await supabase.from("usage_events").insert({
    user_id: user.id,
    event_type: "generate",
    metadata: { project_name: parsed.data.config?.project?.name ?? "unknown" },
  });

  // Pipe the SSE stream through to the browser
  return new Response(geoRes.body, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      "Connection": "keep-alive",
    },
  });
}
