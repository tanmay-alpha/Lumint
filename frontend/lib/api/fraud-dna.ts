import { CampaignsResponse, GraphResponse, ThreatSummary } from "../types";
import { apiBaseUrl } from "../config";

async function realFetch<T>(path: string, init?: RequestInit): Promise<T | null> {
  const base = apiBaseUrl();
  if (!base) {
    // Demo deployment: no backend configured. Fail soft.
    return null;
  }
  const url = `${base}${path}`;
  const requestHeaders: Record<string, string> = { ...(init?.headers as Record<string, string> | undefined) };

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 10000);
  try {
    const response = await fetch(url, { ...init, headers: requestHeaders, signal: controller.signal });
    if (!response.ok) {
      const errorObj = new Error(`API Error: ${response.status} ${response.statusText}`) as Error & { status?: number };
      errorObj.status = response.status;
      throw errorObj;
    }
    return (await response.json()) as T;
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : "network error";
    console.warn(`[Lumint FraudDNA] ${init?.method || "GET"} ${path} unreachable; returning null:`, message);
    // Network or server error — fail soft.
    return null;
  } finally {
    clearTimeout(timeoutId);
  }
}

export const fraudDnaApi = {
  getCampaigns: async (): Promise<CampaignsResponse | null> => {
    return realFetch<CampaignsResponse>("/api/fraud-dna/campaigns");
  },

  getGraph: async (): Promise<GraphResponse | null> => {
    return realFetch<GraphResponse>("/api/fraud-dna/graph");
  },

  getThreatSummary: async (): Promise<ThreatSummary | null> => {
    return realFetch<ThreatSummary>("/api/fraud-dna/threat-summary");
  },

  recluster: async (): Promise<CampaignsResponse | null> => {
    return realFetch<CampaignsResponse>("/api/fraud-dna/recluster", { method: "POST" });
  },
};

export default fraudDnaApi;
