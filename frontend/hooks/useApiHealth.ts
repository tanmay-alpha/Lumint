"use client";
import { useState, useEffect, useCallback } from "react";
import { apiBaseUrl } from "@/lib/config";

/**
 * Connection status reported by `useApiHealth`. Three states:
 *   - "unknown" — no API URL is configured, or the first probe is in flight
 *   - "online"  — most recent probe returned 2xx
 *   - "offline" — most recent probe failed (timeout, CORS, non-2xx, network)
 *
 * The hook is deliberately resilient to Render free-tier cold starts (which
 * can take 30–60s to wake a sleeping web service) by using a 60s per-fetch
 * timeout and a 60s poll interval. Latency is exposed for diagnostics.
 */
export type ApiHealthStatus = "unknown" | "online" | "offline";

export interface UseApiHealth {
  status: ApiHealthStatus;
  /** Most recent probe round-trip in ms, or null if no probe has succeeded. */
  latency: number | null;
  /** Most recent error message, or null if the last probe succeeded. */
  lastError: string | null;
  /** Manually re-run the probe (e.g. on a "retry" button click). */
  recheck: () => void;
}

const PROBE_TIMEOUT_MS = 60_000; // free-tier cold start budget
const POLL_INTERVAL_MS = 60_000;

export function useApiHealth(): UseApiHealth {
  const [status, setStatus] = useState<ApiHealthStatus>("unknown");
  const [latency, setLatency] = useState<number | null>(null);
  const [lastError, setLastError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    let cancelled = false;

    const probe = async () => {
      const base = apiBaseUrl();
      if (!base) {
        // No API configured. Don't even try.
        if (!cancelled) {
          setStatus("unknown");
          setLastError("NEXT_PUBLIC_API_URL is not set");
        }
        return;
      }

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), PROBE_TIMEOUT_MS);
      const start = Date.now();

      try {
        const res = await fetch(`${base}/health`, {
          signal: controller.signal,
          cache: "no-store",
          // `mode: "cors"` is the default, but we keep it explicit so the
          // intent is obvious in the code review.
          mode: "cors",
        });
        clearTimeout(timeoutId);

        if (cancelled) return;
        if (res.ok) {
          setStatus("online");
          setLatency(Date.now() - start);
          setLastError(null);
        } else {
          setStatus("offline");
          setLastError(`HTTP ${res.status} ${res.statusText}`);
        }
      } catch (err: any) {
        clearTimeout(timeoutId);
        if (cancelled) return;
        // CORS errors surface as a TypeError with no message in many
        // browsers; network errors are also TypeError. Be explicit about
        // both so the user can debug.
        if (err?.name === "AbortError") {
          setStatus("offline");
          setLastError(`timeout after ${PROBE_TIMEOUT_MS / 1000}s (cold start?)`);
        } else {
          setStatus("offline");
          setLastError(err?.message || "network error (CORS or unreachable)");
        }
      }
    };

    probe();
    const id = setInterval(probe, POLL_INTERVAL_MS);

    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [tick]);

  const recheck = useCallback(() => setTick((t) => t + 1), []);

  return { status, latency, lastError, recheck };
}
