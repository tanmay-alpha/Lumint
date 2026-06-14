import {
  DashboardStats,
  RecentEvent,
  RiskDistribution,
  IndicatorSummary,
  HealthResponse
} from "../types";
import { apiBaseUrl } from "../config";

/**
 * The single network entry point for dashboard widgets.
 *
 * Fails soft (returns `null`) when no backend is configured or the request
 * errors. The dashboard pages render empty states in that case, so users
 * on the demo deployment see a friendly placeholder instead of a stack
 * trace. When a real backend is configured, normal `T` returns work as
 * expected.
 */
export async function fetchApi<T>(path: string, options?: RequestInit): Promise<T | null> {
  const base = apiBaseUrl();
  if (!base) {
    // No backend configured. Emit a one-time error so the user can see
    // *why* requests are returning null in the browser console.
    if (typeof console !== "undefined") {
      console.error(
        "[Lumint API] NEXT_PUBLIC_API_URL is not set. " +
        "Add it in Vercel → Project → Settings → Environment Variables " +
        "(Production) and redeploy. Backend calls will fail until then."
      );
    }
    return null;
  }
  const url = `${base}${path}`;

  const apiKey = process.env.NEXT_PUBLIC_API_KEY;
  const headers = new Headers(options?.headers);
  if (apiKey) {
    headers.set("Authorization", `Bearer ${apiKey}`);
  }

  // 10s for normal JSON, 30s for uploads.
  const isUpload = options?.body instanceof FormData;
  const timeoutMs = isUpload ? 30000 : 10000;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      ...options,
      headers,
      signal: controller.signal,
    });
    if (!response.ok) {
      let errorMessage = `API Error: ${response.status} ${response.statusText}`;
      try {
        const errJson = await response.json();
        if (errJson && errJson.detail) {
          if (typeof errJson.detail === "string") errorMessage = errJson.detail;
        }
      } catch (_) {}
      const errorObj: any = new Error(errorMessage);
      errorObj.status = response.status;
      errorObj.path = path;
      throw errorObj;
    }
    return (await response.json()) as T;
  } catch (error: any) {
    // Surface CORS and network errors prominently so the user can
    // diagnose without digging into the Network tab.
    const msg = error?.message || "network error";
    if (
      typeof console !== "undefined" &&
      (msg === "Failed to fetch" || msg.includes("CORS") || msg.includes("NetworkError"))
    ) {
      console.error(
        `[Lumint API CORS] ${options?.method || "GET"} ${path} failed.\n` +
        `  Base URL: ${base}\n` +
        `  Error:    ${msg}\n` +
        `  Fix:      Ensure ALLOWED_ORIGINS in Render includes https://lumint-pi.vercel.app`
      );
    }
    console.warn(`[Lumint API] ${options?.method || "GET"} ${path} unreachable; returning null:`, error?.message);
    return null;
  } finally {
    clearTimeout(timeoutId);
  }
}

// API methods
export const client = {
  getHealth: async (): Promise<HealthResponse | null> => {
    return fetchApi<HealthResponse>("/health", {});
  },

  getStats: async (): Promise<DashboardStats | null> => {
    return fetchApi<DashboardStats>("/api/dashboard/stats", {});
  },

  getRecentEvents: async (limit: number = 20): Promise<RecentEvent[] | null> => {
    return fetchApi<{ events: RecentEvent[] }>(
      `/api/dashboard/recent-events?limit=${limit}`,
      {}
    ).then(r => r?.events ?? null);
  },

  getRiskDistribution: async (): Promise<RiskDistribution | null> => {
    return fetchApi<RiskDistribution>("/api/dashboard/risk-distribution", {});
  },

  getIndicatorSummary: async (): Promise<IndicatorSummary | null> => {
    return fetchApi<IndicatorSummary>("/api/dashboard/indicator-summary", {});
  },

  // Research endpoints — real backend, no mock fallback.
  // Returned as `any` because the schema is rich; downstream rendering
  // tolerates undefined fields and surfaces them as '—'.
  getResearchMetrics: async (): Promise<any> => {
    return fetchApi<any>("/api/research/metrics", {});
  },

  getResearchAblation: async (): Promise<any> => {
    return fetchApi<any>("/api/research/ablation", {});
  },

  getResearchShap: async (): Promise<any> => {
    return fetchApi<any>("/api/research/shap", {});
  },

  getResearchDatasets: async (): Promise<any> => {
    return fetchApi<any>("/api/research/datasets", {});
  },
};

export default client;
