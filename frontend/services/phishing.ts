import { apiRequest } from "@/lib/api-client";
import { PhishingCheckResponse, PhishingExplainResponse } from "@/types";

export const phishingService = {
  check: async (url: string): Promise<PhishingCheckResponse> => {
    return apiRequest<PhishingCheckResponse>("/api/phishing/check", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });
  },

  checkBatch: async (urls: string[]): Promise<{ total: number; results: PhishingCheckResponse[] }> => {
    return apiRequest<{ total: number; results: PhishingCheckResponse[] }>(
      "/api/phishing/check/batch",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ urls }),
      }
    );
  },

  explainConfidence: async (riskScore: number): Promise<PhishingExplainResponse> => {
    return apiRequest<PhishingExplainResponse>(`/api/phishing/confidence/${riskScore}`, {
      method: "GET",
    });
  },
};
