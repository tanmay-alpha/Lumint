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
 * No mock fallback. If the backend is unreachable, the real error is
 * thrown to the caller so the UI can show a meaningful error state.
 */
export async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const base = apiBaseUrl();
  if (!base) {
    throw {
      message: "Backend not configured. Set NEXT_PUBLIC_API_URL to your FastAPI host.",
      status: 0,
      path,
      isNetworkError: true,
    };
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
    console.error(`[Lumint API] ${options?.method || "GET"} ${path} failed:`, error);
    throw {
      message: error?.message || "Backend unavailable",
      status: error?.status || 0,
      path,
      isNetworkError: !error?.status,
    };
  } finally {
    clearTimeout(timeoutId);
  }
}

// API methods
export const client = {
  getHealth: async (): Promise<HealthResponse> => {
    return fetchApi<HealthResponse>("/api/health", {});
  },

  getStats: async (): Promise<DashboardStats> => {
    return fetchApi<DashboardStats>("/api/dashboard/stats", {});
  },

  getRecentEvents: async (limit: number = 20): Promise<RecentEvent[]> => {
    const response = await fetchApi<{ events: RecentEvent[] }>(
      `/api/dashboard/recent-events?limit=${limit}`,
      {}
    );
    return response.events;
  },

  getRiskDistribution: async (): Promise<RiskDistribution> => {
    return fetchApi<RiskDistribution>("/api/dashboard/risk-distribution", {});
  },

  getIndicatorSummary: async (): Promise<IndicatorSummary> => {
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
