import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { CanonicalConfigSchema } from "@/types/schema";
import type { ApiError } from "@/types/schema";
import { z } from "zod";

function apiError(code: string, message: string, status = 400): NextResponse<ApiError> {
  return NextResponse.json({ error: { code, message } }, { status });
}

const RequestSchema = z.object({ config: CanonicalConfigSchema });

/** POST /api/validate — proxy to geometry service validate endpoint */
export async function POST(request: Request) {
  const supabase = await createClient();
  const { data: { user }, error: authError } = await supabase.auth.getUser();
  if (authError || !user) return apiError("unauthenticated", "Authentication required.", 401);

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

  let geoRes: Response;
  try {
    geoRes = await fetch(`${geoUrl}/validate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": geoKey,
      },
      body: JSON.stringify({ config: parsed.data }),
    });
  } catch {
    return apiError(
      "geometry_service_unavailable",
      "Geometry service is not reachable. Make sure it is running on port 8001.",
      503
    );
  }

  const data = await geoRes.json();
  return NextResponse.json(data, { status: geoRes.status });
}
