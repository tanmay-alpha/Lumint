import { CampaignsResponse, GraphResponse, ThreatSummary } from "../types";
import { apiBaseUrl } from "../config";

async function realFetch<T>(path: string, init?: RequestInit): Promise<T | null> {
  const base = apiBaseUrl();
  if (!base) {
    // Demo deployment: no backend configured. Fail soft.
    return null;
  }
  const url = `${base}${path}`;
  const apiKey = process.env.NEXT_PUBLIC_API_KEY;
  const requestHeaders: Record<string, string> = { ...(init?.headers as any) };
  if (apiKey) requestHeaders["Authorization"] = `Bearer ${apiKey}`;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 10000);
  try {
    const response = await fetch(url, { ...init, headers: requestHeaders, signal: controller.signal });
    if (!response.ok) {
      const errorObj: any = new Error(`API Error: ${response.status} ${response.statusText}`);
      errorObj.status = response.status;
      throw errorObj;
    }
    return (await response.json()) as T;
  } catch (error: any) {
    console.warn(`[Lumint FraudDNA] ${init?.method || "GET"} ${path} unreachable; returning null:`, error?.message);
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
