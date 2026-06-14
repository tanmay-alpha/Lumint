"use client";
import { useEffect, useState, useCallback } from "react";
import client from "@/lib/api/client";
import { apiBaseUrl } from "@/lib/config";

/**
 * Polls the backend /health endpoint on a fixed interval and exposes the
 * current connection status. Used by the dashboard layout (to drive the
 * demo-mode banner) and the topbar (to render the green/red status pill).
 *
 * Three states:
 *   - "unknown" — no API URL is configured, or the first probe is in flight
 *   - "online"  — most recent probe returned 2xx
 *   - "offline" — most recent probe failed or returned non-2xx
 */
export type ApiHealthStatus = "unknown" | "online" | "offline";

export function useApiHealth(intervalMs: number = 60_000): ApiHealthStatus {
  const [status, setStatus] = useState<ApiHealthStatus>("unknown");

  const check = useCallback(async () => {
    const base = apiBaseUrl();
    if (!base) {
      // No backend configured. Don't even probe — sit in "unknown" so the UI
      // can render the demo-mode banner and the topbar can hide the pill.
      setStatus("unknown");
      return;
    }
    try {
      const result = await client.getHealth();
      setStatus(result ? "online" : "offline");
    } catch {
      setStatus("offline");
    }
  }, []);

  useEffect(() => {
    // Kick off the first probe immediately, then on the requested interval.
    check();
    const id = setInterval(check, intervalMs);
    return () => clearInterval(id);
  }, [check, intervalMs]);

  return status;
}
