import { apiRequest } from "@/lib/api-client";
import {
  StatsResponse,
  RecentEventsResponse,
  RiskDistributionResponse,
  IndicatorSummaryResponse
} from "@/types";

export const dashboardService = {
  getStats: async (): Promise<StatsResponse> => {
    return apiRequest<StatsResponse>("/api/dashboard/stats", { method: "GET" });
  },

  getRecentEvents: async (limit: number = 20): Promise<RecentEventsResponse> => {
    return apiRequest<RecentEventsResponse>(
      `/api/dashboard/recent-events?limit=${limit}`,
      { method: "GET" }
    );
  },

  getRiskDistribution: async (): Promise<RiskDistributionResponse> => {
    return apiRequest<RiskDistributionResponse>(
      "/api/dashboard/risk-distribution",
      { method: "GET" }
    );
  },

  getIndicatorSummary: async (): Promise<IndicatorSummaryResponse> => {
    return apiRequest<IndicatorSummaryResponse>(
      "/api/dashboard/indicator-summary",
      { method: "GET" }
    );
  },
};
