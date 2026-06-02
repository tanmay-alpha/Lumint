import { apiRequest } from "@/lib/api-client";
import { 
  StatsResponse, 
  RecentEventsResponse, 
  RiskDistributionResponse, 
  IndicatorSummaryResponse 
} from "@/types";

export const dashboardService = {
  getStats: async (): Promise<StatsResponse> => {
    return apiRequest<StatsResponse>("/api/dashboard/stats", { method: "GET" }, () => {
      // Mock stats fallback
      return {
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
    });
  },

  getRecentEvents: async (limit: number = 20): Promise<RecentEventsResponse> => {
    return apiRequest<RecentEventsResponse>(
      `/api/dashboard/recent-events?limit=${limit}`,
      { method: "GET" },
      () => {
        // Mock recent events fallback
        return {
          total: 5,
          limit,
          events: [
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
              top_keywords: ["invoice", "payment", "wire transfer", "bank routing", "swift"],
              risk_indicators: ["Metadata Modification Detected", "Spoofed Creator Field", "Swift Code Alteration Hint"],
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
              top_keywords: ["login", "chase", "banking", "secure", "verify"],
              risk_indicators: ["Lookalike Domain (Typosquatting)", "Keywords Match High Risk (chase)", "Suspicious Top Level Domain (.net)"],
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
              top_keywords: ["passport", "identity", "travel document", "united states"],
              risk_indicators: ["ELA Discrepancy Found in Image Text", "EXIF Data Mismatch (Photoshop Signature)"],
              risk_score: 72,
              risk_level: "SUSPICIOUS",
              document_type_hint: "identity_forgery",
              created_at: new Date(Date.now() - 1000 * 60 * 180).toISOString()
            },
            {
              event_id: "evt-90a12c",
              doc_id: null,
              source_type: "URL",
              original_filename: null,
              saved_filename: null,
              file_hash: null,
              metadata_hash: null,
              editor_tool: null,
              producer: null,
              creator: null,
              source_domain: "paypal-resolution-center.com",
              top_keywords: ["paypal", "resolution", "billing", "dispute"],
              risk_indicators: ["Lookalike Domain (Typosquatting)", "Brand Name Injection"],
              risk_score: 68,
              risk_level: "SUSPICIOUS",
              document_type_hint: "phishing_url",
              created_at: new Date(Date.now() - 1000 * 60 * 320).toISOString()
            },
            {
              event_id: "evt-34b89a",
              doc_id: "doc-34f9a1",
              source_type: "DOCUMENT",
              original_filename: "compliance_checklist.pdf",
              saved_filename: "doc-34f9a1.pdf",
              file_hash: "5e4d3c2b1a0f9e8d7c6b5a4f3e2d1c0b",
              metadata_hash: "9e8d7c6b5a4f3e2d",
              editor_tool: "Microsoft Word 365",
              producer: "Microsoft PDF Library",
              creator: "Compliance Office",
              source_domain: null,
              top_keywords: ["compliance", "audit", "checklist", "security"],
              risk_indicators: [],
              risk_score: 12,
              risk_level: "CLEAN",
              document_type_hint: "clean_pdf",
              created_at: new Date(Date.now() - 1000 * 60 * 500).toISOString()
            }
          ]
        };
      }
    );
  },

  getRiskDistribution: async (): Promise<RiskDistributionResponse> => {
    return apiRequest<RiskDistributionResponse>(
      "/api/dashboard/risk-distribution",
      { method: "GET" },
      () => {
        return {
          distribution: [
            { risk_level: "CLEAN", count: 92 },
            { risk_level: "SUSPICIOUS", count: 31 },
            { risk_level: "HIGH", count: 25 }
          ]
        };
      }
    );
  },

  getIndicatorSummary: async (): Promise<IndicatorSummaryResponse> => {
    return apiRequest<IndicatorSummaryResponse>(
      "/api/dashboard/indicator-summary",
      { method: "GET" },
      () => {
        return {
          indicators: [
            { indicator: "Lookalike Domain (Typosquatting)", count: 24 },
            { indicator: "ELA Discrepancy Found in Image Text", count: 18 },
            { indicator: "Metadata Modification Detected", count: 15 },
            { indicator: "EXIF Data Mismatch (Photoshop Signature)", count: 12 },
            { indicator: "Brand Name Injection", count: 11 }
          ]
        };
      }
    );
  }
};
