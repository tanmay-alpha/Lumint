import { CampaignsResponse, GraphResponse, ThreatSummary } from "../types";
import { apiBaseUrl } from "../config";

async function realFetch<T>(path: string, init?: RequestInit): Promise<T> {
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
    console.error(`[Lumint FraudDNA] ${init?.method || "GET"} ${path} failed:`, error);
    throw {
      message: error?.message || "Fraud DNA request failed",
      status: error?.status || 0,
      path,
      isNetworkError: !error?.status,
    };
  } finally {
    clearTimeout(timeoutId);
  }
}

export const fraudDnaApi = {
  getCampaigns: async (): Promise<CampaignsResponse> => {
    return realFetch<CampaignsResponse>("/api/fraud-dna/campaigns");
  },

  getGraph: async (): Promise<GraphResponse> => {
    return realFetch<GraphResponse>("/api/fraud-dna/graph");
  },

  getThreatSummary: async (): Promise<ThreatSummary> => {
    return realFetch<ThreatSummary>("/api/fraud-dna/threat-summary");
  },

  recluster: async (): Promise<CampaignsResponse> => {
    return realFetch<CampaignsResponse>("/api/fraud-dna/recluster", { method: "POST" });
  },
};

export default fraudDnaApi;
