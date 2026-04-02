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
        setError({ code, message: msg, step: lastProgressName, percent: lastProgressPercent });
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

      // Stream ended without result or error event — treat as error
      setError({
        code: "stream_incomplete",
        message: "Connection closed before generation completed.",
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
          setError({
            code: data?.error?.code ?? "generate_failed",
            message: data?.error?.message ?? "Generate failed.",
          });
        } else {
          setResult(data);
        }
      } catch (fallbackErr) {
        setError({
          code: "network_error",
          message: fallbackErr instanceof Error ? fallbackErr.message : "Network error.",
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
