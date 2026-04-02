import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { canGenerate } from "@/lib/billing/access";
import { CanonicalConfigSchema } from "@/types/schema";
import type { ApiError } from "@/types/schema";
import { z } from "zod";

export const maxDuration = 120;

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

  // Pre-warm: trigger Fly.io auto-start so cold-start time doesn't eat
  // into the pipeline timeout. Fire-and-forget with a short timeout.
  try {
    await fetch(`${geoUrl}/health`, { signal: AbortSignal.timeout(15000) });
  } catch {
    // Machine may still be starting — proceed anyway
  }

  // Open SSE stream to geometry service with a generous initial timeout.
  // Once connected, we switch to heartbeat-based timeout below.
  const controller = new AbortController();
  const connectTimeout = setTimeout(() => controller.abort(), 30000);

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
    clearTimeout(connectTimeout);
    if (err instanceof DOMException && err.name === "AbortError") {
      return apiError(
        "timeout_no_data",
        "The geometry service is starting up. This usually takes 5-10 seconds on first request. Please try again.",
        504
      );
    }
    return apiError(
      "geometry_service_unavailable",
      "Could not connect to the geometry service. It may be offline or unreachable.",
      503
    );
  } finally {
    clearTimeout(connectTimeout);
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

  // Pipe SSE stream through with a heartbeat-based inactivity timeout.
  // Reset a 30s timer each time data arrives. If the service goes silent
  // for 30s (stuck pipeline), abort and close the stream.
  const inactivityMs = 30000;
  const streamController = new AbortController();
  let inactivityTimer: ReturnType<typeof setTimeout>;

  function resetInactivity() {
    clearTimeout(inactivityTimer);
    inactivityTimer = setTimeout(() => streamController.abort(), inactivityMs);
  }

  resetInactivity();

  const passthrough = new TransformStream({
    transform(chunk, ctrl) {
      resetInactivity();
      ctrl.enqueue(chunk);
    },
    flush() {
      clearTimeout(inactivityTimer);
    },
  });

  const pipedStream = geoRes.body!.pipeThrough(passthrough);

  // If the inactivity timer fires, the streamController aborts, which
  // will cause the piped stream to error. The browser sees the stream end.

  return new Response(pipedStream, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      "Connection": "keep-alive",
    },
  });
}
