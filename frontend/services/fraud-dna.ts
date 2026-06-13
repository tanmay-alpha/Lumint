import { apiRequest } from "@/lib/api-client";
import { CampaignsResponse, GraphResponse, ThreatSummaryResponse, FraudDNAFingerprint } from "@/types";

export const fraudDNAService = {
  getFingerprints: async (): Promise<{ total: number; fingerprints: FraudDNAFingerprint[] }> => {
    return apiRequest<{ total: number; fingerprints: FraudDNAFingerprint[] }>(
      "/api/fraud-dna/fingerprints",
      { method: "GET" }
    );
  },

  getCampaigns: async (): Promise<CampaignsResponse> => {
    return apiRequest<CampaignsResponse>("/api/fraud-dna/campaigns", { method: "GET" });
  },

  getGraph: async (): Promise<GraphResponse> => {
    return apiRequest<GraphResponse>("/api/fraud-dna/graph", { method: "GET" });
  },

  recluster: async (): Promise<CampaignsResponse> => {
    return apiRequest<CampaignsResponse>("/api/fraud-dna/recluster", { method: "POST" });
  },

  getThreatSummary: async (): Promise<ThreatSummaryResponse> => {
    return apiRequest<ThreatSummaryResponse>("/api/fraud-dna/threat-summary", { method: "GET" });
  },
};
