import {
  DashboardStats,
  RecentEvent,
  RiskDistribution,
  IndicatorSummary,
  HealthResponse
} from "../types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Mock Fallback generators to simulate responses when backend is offline
const MOCK_STATS: DashboardStats = {
  total_events: 148,
  document_events: 64,
  url_events: 84,
  clean_count: 92,
  suspicious_count: 31,
  high_risk_count: 25,
  active_campaigns: 4,
  average_risk_score: 34.6,
  top_indicators: [
    { indicator: "Lookalike Domain (Typosquatting)", count: 24 },
    { indicator: "ELA Discrepancy Found in Image Text", count: 18 },
    { indicator: "Metadata Modification Detected", count: 15 },
    { indicator: "EXIF Data Mismatch (Photoshop Signature)", count: 12 },
    { indicator: "Brand Name Injection", count: 11 }
  ],
  last_updated: new Date().toISOString()
};

const MOCK_EVENTS: RecentEvent[] = [
  {
    event_id: "evt-f89a23",
    doc_id: "doc-89a12b",
    source_type: "DOCUMENT",
    original_filename: "invoice_9821.pdf",
    saved_filename: "doc-89a12b.pdf",
    file_hash: "8f9a3e2b1c0d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f",
    metadata_hash: "2b9a7c3d1e2f5a6b",
    editor_tool: "Adobe Acrobat Pro 2023",
    producer: "Adobe PDF Library 15.0",
    creator: "Accounts Payable Manager",
    source_domain: null,
    top_keywords: ["invoice", "payment", "wire transfer", "bank routing"],
    risk_indicators: ["Metadata Modification Detected", "Spoofed Creator Field"],
    risk_score: 87,
    risk_level: "HIGH",
    document_type_hint: "invoice_forgery",
    created_at: new Date(Date.now() - 1000 * 60 * 25).toISOString()
  },
  {
    event_id: "evt-12a839",
    doc_id: null,
    source_type: "URL",
    original_filename: null,
    saved_filename: null,
    file_hash: null,
    metadata_hash: null,
    editor_tool: null,
    producer: null,
    creator: null,
    source_domain: "chase-security-verify.net",
    top_keywords: ["login", "chase", "banking"],
    risk_indicators: ["Lookalike Domain (Typosquatting)", "Keywords Match High Risk (chase)"],
    risk_score: 94,
    risk_level: "HIGH",
    document_type_hint: "phishing_url",
    created_at: new Date(Date.now() - 1000 * 60 * 75).toISOString()
  },
  {
    event_id: "evt-87f12e",
    doc_id: "doc-12c89f",
    source_type: "DOCUMENT",
    original_filename: "passport_scan_john.jpg",
    saved_filename: "doc-12c89f.jpg",
    file_hash: "f3a2b1c0d4e5f6a7b8c9d0e1f2a3b4c5",
    metadata_hash: "8c7d6e5f4a3b2c1d",
    editor_tool: "Photoshop 2024",
    producer: "Adobe Photoshop CC",
    creator: "John Doe",
    source_domain: null,
    top_keywords: ["passport", "identity", "travel document"],
    risk_indicators: ["ELA Discrepancy Found in Image Text", "EXIF Data Mismatch"],
    risk_score: 72,
    risk_level: "SUSPICIOUS",
    document_type_hint: "identity_forgery",
    created_at: new Date(Date.now() - 1000 * 60 * 180).toISOString()
  }
];

const MOCK_RISK_DISTRIBUTION: RiskDistribution = {
  distribution: [
    { risk_level: "CLEAN", count: 92 },
    { risk_level: "SUSPICIOUS", count: 31 },
    { risk_level: "HIGH", count: 25 }
  ]
};

const MOCK_INDICATOR_SUMMARY: IndicatorSummary = {
  indicators: [
    { indicator: "Lookalike Domain (Typosquatting)", count: 24 },
    { indicator: "ELA Discrepancy Found in Image Text", count: 18 },
    { indicator: "Metadata Modification Detected", count: 15 },
    { indicator: "EXIF Data Mismatch", count: 12 },
    { indicator: "Brand Name Injection", count: 11 }
  ]
};

export async function fetchApi<T>(
  path: string,
  options?: RequestInit,
  mockFallback?: T
): Promise<T> {
  const url = `${BASE_URL}${path}`;
  try {
    const response = await fetch(url, {
      ...options,
      signal: AbortSignal.timeout(3000)
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return (await response.json()) as T;
  } catch (error) {
    console.warn(`SentinelX API fallback to mock on path: ${path}`, error);
    if (mockFallback !== undefined) {
      // Simulate artificial latency
      await new Promise((resolve) => setTimeout(resolve, 800));
      return mockFallback;
    }
    throw error;
  }
}

// API methods
export const client = {
  getHealth: async (): Promise<HealthResponse> => {
    return fetchApi<HealthResponse>("/api/health", {}, {
      status: "ok",
      timestamp: new Date().toISOString(),
      version: "1.0.0"
    });
  },

  getStats: async (): Promise<DashboardStats> => {
    return fetchApi<DashboardStats>("/api/dashboard/stats", {}, MOCK_STATS);
  },

  getRecentEvents: async (limit: number = 20): Promise<RecentEvent[]> => {
    // Note: API returns RecentEventsResponse which contains { events: RecentEvent[] }
    const response = await fetchApi<{ events: RecentEvent[] }>(
      `/api/dashboard/recent-events?limit=${limit}`,
      {},
      { events: MOCK_EVENTS }
    );
    return response.events;
  },

  getRiskDistribution: async (): Promise<RiskDistribution> => {
    return fetchApi<RiskDistribution>("/api/dashboard/risk-distribution", {}, MOCK_RISK_DISTRIBUTION);
  },

  getIndicatorSummary: async (): Promise<IndicatorSummary> => {
    return fetchApi<IndicatorSummary>("/api/dashboard/indicator-summary", {}, MOCK_INDICATOR_SUMMARY);
  }
};

export default client;
