"use client";

import { useState, useCallback } from "react";
import type { GenerateResult } from "@/components/editor/SvgPreview";
import type { CanonicalConfig } from "@/types/schema";

export interface GenerateProgress {
  step: number;
  totalSteps: number;
  name: string;
  percent: number;
}

export interface GenerateError {
  code: string;
  message: string;
  traceback?: string;
  step?: string;
  percent?: number;
}

function specificErrorMessage(
  code: string,
  fallback: string,
  lastStep?: string,
  lastPercent?: number,
): string {
  switch (code) {
    case "timeout_no_data":
      return "The geometry service is starting up. This usually takes 5-10 seconds on first request. Please try again.";
    case "timeout":
    case "timeout_stalled":
      if (lastStep) {
        return `Generation timed out during "${lastStep}" (${lastPercent ?? 0}% complete). The layout may be too complex — try reducing the number of slats or simplifying rotation settings.`;
      }
      return "The geometry service took too long to respond. It may be starting up — please try again.";
    case "geometry_service_unavailable":
      return "Could not connect to the geometry service. It may be offline or unreachable.";
    case "network_error":
      return "Could not connect to the geometry service. Check your internet connection and try again.";
    default:
      return fallback;
  }
}

export function useGenerateStream() {
  const [generating, setGenerating] = useState(false);
  const [progress, setProgress] = useState<GenerateProgress | null>(null);
  const [result, setResult] = useState<GenerateResult | null>(null);
  const [error, setError] = useState<GenerateError | null>(null);

  const generate = useCallback(async (config: CanonicalConfig) => {
    setGenerating(true);
    setProgress(null);
    setError(null);

    let lastProgressName: string | undefined;
    let lastProgressPercent: number | undefined;

    try {
      const res = await fetch("/api/generate-stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ config }),
      });

      // Non-streaming error (auth, validation, timeout)
      if (!res.ok || !res.body) {
        let msg = "Generate failed.";
        let code = "generate_failed";
        try {
          const errData = await res.json();
          msg = errData?.error?.message ?? msg;
          code = errData?.error?.code ?? code;
        } catch { /* ignore parse errors */ }
        // Provide specific user-facing messages based on error code
        const userMsg = specificErrorMessage(code, msg, lastProgressName, lastProgressPercent);
        setError({ code, message: userMsg, step: lastProgressName, percent: lastProgressPercent });
        return;
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let currentEvent = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop()!;

        for (const line of lines) {
          if (line.startsWith("event: ")) {
            currentEvent = line.slice(7).trim();
          } else if (line.startsWith("data: ")) {
            const raw = line.slice(6);
            try {
              const data = JSON.parse(raw);
              if (currentEvent === "progress") {
                lastProgressName = data.name;
                lastProgressPercent = data.percent;
                setProgress(data);
              } else if (currentEvent === "result") {
                setResult(data);
                return;
              } else if (currentEvent === "error") {
                setError({
                  code: data.code ?? "pipeline_error",
                  message: data.message ?? "Pipeline failed.",
                  traceback: data.traceback,
                  step: lastProgressName,
                  percent: lastProgressPercent,
                });
                return;
              }
            } catch { /* skip malformed JSON */ }
            currentEvent = "";
          }
        }
      }

      // Stream ended without result or error event — stalled pipeline
      const stallMsg = lastProgressName
        ? `Generation stalled during "${lastProgressName}" (${lastProgressPercent ?? 0}% complete). The layout may be too complex — try reducing the number of slats or simplifying rotation settings.`
        : "The geometry service stopped responding. Please try again.";
      setError({
        code: "stream_incomplete",
        message: stallMsg,
        step: lastProgressName,
        percent: lastProgressPercent,
      });
    } catch (err) {
      // Network error — fall back to non-streaming endpoint
      try {
        const res = await fetch("/api/generate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ config }),
        });
        const data = await res.json();
        if (!res.ok) {
          const code = data?.error?.code ?? "generate_failed";
          const msg = data?.error?.message ?? "Generate failed.";
          setError({
            code,
            message: specificErrorMessage(code, msg, lastProgressName, lastProgressPercent),
          });
        } else {
          setResult(data);
        }
      } catch {
        setError({
          code: "network_error",
          message: "Could not connect to the geometry service. Check your internet connection and try again.",
        });
      }
    } finally {
      setGenerating(false);
    }
  }, []);

  const clearError = useCallback(() => setError(null), []);
  const clearResult = useCallback(() => setResult(null), []);

  return { generating, progress, result, error, generate, clearError, clearResult, setResult };
}
