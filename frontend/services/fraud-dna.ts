import { apiRequest, getMockCampaigns, getMockGraph, getMockThreatSummary } from "@/lib/api-client";
import { CampaignsResponse, GraphResponse, ThreatSummaryResponse, FraudDNAFingerprint } from "@/types";

export const fraudDNAService = {
  getFingerprints: async (): Promise<{ total: number; fingerprints: FraudDNAFingerprint[] }> => {
    return apiRequest<{ total: number; fingerprints: FraudDNAFingerprint[] }>(
      "/api/fraud-dna/fingerprints",
      { method: "GET" },
      () => {
        return {
          total: 5,
          fingerprints: [
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
            }
          ]
        };
      }
    );
  },

  getCampaigns: async (): Promise<CampaignsResponse> => {
    return apiRequest<CampaignsResponse>(
      "/api/fraud-dna/campaigns",
      { method: "GET" },
      getMockCampaigns
    );
  },

  getGraph: async (): Promise<GraphResponse> => {
    return apiRequest<GraphResponse>(
      "/api/fraud-dna/graph",
      { method: "GET" },
      getMockGraph
    );
  },

  recluster: async (): Promise<CampaignsResponse> => {
    return apiRequest<CampaignsResponse>(
      "/api/fraud-dna/recluster",
      { method: "POST" },
      getMockCampaigns
    );
  },

  getThreatSummary: async (): Promise<ThreatSummaryResponse> => {
    return apiRequest<ThreatSummaryResponse>(
      "/api/fraud-dna/threat-summary",
      { method: "GET" },
      getMockThreatSummary
    );
  }
};
