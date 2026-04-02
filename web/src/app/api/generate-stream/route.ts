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

/**
 * Wait for the geometry service to become reachable by polling /health.
 * Retries every 2s for up to `maxWaitMs`. Returns true if healthy.
 */
async function waitForService(geoUrl: string, maxWaitMs = 20000): Promise<boolean> {
  const start = Date.now();
  while (Date.now() - start < maxWaitMs) {
    try {
      const controller = new AbortController();
      const t = setTimeout(() => controller.abort(), 5000);
      const res = await fetch(`${geoUrl}/health`, { signal: controller.signal });
      clearTimeout(t);
      if (res.ok) return true;
    } catch {
      // Not ready yet — wait and retry
    }
    await new Promise((r) => setTimeout(r, 2000));
  }
  return false;
}

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

  // Wait for the geometry service to be reachable (handles Fly.io cold starts).
  // Polls /health every 2s for up to 20s before giving up.
  const serviceReady = await waitForService(geoUrl, 20000);
  if (!serviceReady) {
    return apiError(
      "timeout_no_data",
      "The geometry service is still starting up. Please wait a few seconds and try again.",
      504
    );
  }

  // Service is reachable — open the SSE stream.
  // Use a 90s timeout for the initial connection (generous, since we
  // already confirmed the service is up via health check).
  const controller = new AbortController();
  const connectTimeout = setTimeout(() => controller.abort(), 90000);

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
        "The geometry service accepted the connection but did not respond in time. Please try again.",
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
    return apiError("generate_failed", `Geometry service error (${geoRes.status}): ${detail.slice(0, 200)}`, geoRes.status);
  }

  // Record usage event
  await supabase.from("usage_events").insert({
    user_id: user.id,
    event_type: "generate",
    metadata: { project_name: parsed.data.config?.project?.name ?? "unknown" },
  });

  // Pipe SSE stream through with a heartbeat-based inactivity timeout.
  // Reset a 45s timer each time data arrives. If the service goes silent
  // for 45s (stuck pipeline), the stream closes.
  const inactivityMs = 45000;
  let inactivityTimer: ReturnType<typeof setTimeout>;

  function resetInactivity() {
    clearTimeout(inactivityTimer);
    inactivityTimer = setTimeout(() => {
      // Nothing to abort here — the stream will just end
    }, inactivityMs);
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

  return new Response(pipedStream, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      "Connection": "keep-alive",
    },
  });
}
