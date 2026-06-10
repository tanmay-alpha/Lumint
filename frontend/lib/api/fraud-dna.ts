import { CampaignsResponse, GraphResponse, ThreatSummary } from "../types";
import { apiBaseUrl } from "../config";

const MOCK_CAMPAIGNS: CampaignsResponse = {
  total_campaigns: 2,
  total_events: 5,
  campaigns: [
    {
      campaign_id: "cmp-a87f9b",
      event_count: 3,
      risk_level: "HIGH",
      avg_risk_score: 84.3,
      common_indicators: ["Metadata Modification Detected", "Spoofed Creator Field"],
      common_keywords: ["invoice", "payment", "wire transfer"],
      first_seen: new Date(Date.now() - 1000 * 60 * 1440 * 5).toISOString(),
      last_seen: new Date(Date.now() - 1000 * 60 * 25).toISOString(),
      events: [
        {
          event_id: "evt-f89a23",
          doc_id: "doc-89a12b",
          source_type: "DOCUMENT",
          label: "invoice_9821.pdf",
          risk_score: 87,
          risk_level: "HIGH",
          document_type_hint: "invoice_forgery",
          created_at: new Date(Date.now() - 1000 * 60 * 25).toISOString()
        },
        {
          event_id: "evt-a78b45",
          doc_id: "doc-12f56a",
          source_type: "DOCUMENT",
          label: "invoice_temp_v2.pdf",
          risk_score: 82,
          risk_level: "HIGH",
          document_type_hint: "invoice_forgery",
          created_at: new Date(Date.now() - 1000 * 60 * 600).toISOString()
        },
        {
          event_id: "evt-67d8f9",
          doc_id: "doc-34a90e",
          source_type: "DOCUMENT",
          label: "payment_instructions.png",
          risk_score: 84,
          risk_level: "HIGH",
          document_type_hint: "invoice_forgery",
          created_at: new Date(Date.now() - 1000 * 60 * 1440 * 2).toISOString()
        }
      ]
    },
    {
      campaign_id: "cmp-c12e56",
      event_count: 2,
      risk_level: "SUSPICIOUS",
      avg_risk_score: 68.0,
      common_indicators: ["ELA Discrepancy Found in Image Text", "EXIF Data Mismatch"],
      common_keywords: ["identity", "passport", "scan"],
      first_seen: new Date(Date.now() - 1000 * 60 * 1440 * 10).toISOString(),
      last_seen: new Date(Date.now() - 1000 * 60 * 180).toISOString(),
      events: [
        {
          event_id: "evt-87f12e",
          doc_id: "doc-12c89f",
          source_type: "DOCUMENT",
          label: "passport_scan_john.jpg",
          risk_score: 72,
          risk_level: "SUSPICIOUS",
          document_type_hint: "identity_forgery",
          created_at: new Date(Date.now() - 1000 * 60 * 180).toISOString()
        },
        {
          event_id: "evt-45b678",
          doc_id: "doc-56d12e",
          source_type: "DOCUMENT",
          label: "visa_john_doe.jpg",
          risk_score: 64,
          risk_level: "SUSPICIOUS",
          document_type_hint: "identity_forgery",
          created_at: new Date(Date.now() - 1000 * 60 * 1440 * 6).toISOString()
        }
      ]
    }
  ]
};

const MOCK_GRAPH: GraphResponse = {
  nodes: [
    { id: "evt-f89a23", label: "invoice_9821.pdf", type: "EVENT", risk_level: "HIGH", risk_score: 87, source_type: "DOCUMENT", doc_id: "doc-89a12b" },
    { id: "evt-a78b45", label: "invoice_temp_v2.pdf", type: "EVENT", risk_level: "HIGH", risk_score: 82, source_type: "DOCUMENT", doc_id: "doc-12f56a" },
    { id: "evt-67d8f9", label: "payment_instructions.png", type: "EVENT", risk_level: "HIGH", risk_score: 84, source_type: "DOCUMENT", doc_id: "doc-34a90e" },
    { id: "actor-invoice-spoofer", label: "Invoice Spoofer Template A", type: "ACTOR", risk_level: "HIGH", risk_score: 85, source_type: "DOCUMENT", doc_id: null },
    
    { id: "evt-87f12e", label: "passport_scan_john.jpg", type: "EVENT", risk_level: "SUSPICIOUS", risk_score: 72, source_type: "DOCUMENT", doc_id: "doc-12c89f" },
    { id: "evt-45b678", label: "visa_john_doe.jpg", type: "EVENT", risk_level: "SUSPICIOUS", risk_score: 64, source_type: "DOCUMENT", doc_id: "doc-56d12e" },
    { id: "actor-id-forge", label: "Photoshop Meta Modifier", type: "ACTOR", risk_level: "SUSPICIOUS", risk_score: 68, source_type: "DOCUMENT", doc_id: null }
  ],
  edges: [
    { source: "evt-f89a23", target: "actor-invoice-spoofer", weight: 0.9, reason: "Identical 'Adobe PDF Library 15.0' + metadata structure." },
    { source: "evt-a78b45", target: "actor-invoice-spoofer", weight: 0.85, reason: "Shared editor configuration hashes." },
    { source: "evt-67d8f9", target: "actor-invoice-spoofer", weight: 0.8, reason: "SWIFT routing number fonts template matches exactly." },
    
    { source: "evt-87f12e", target: "actor-id-forge", weight: 0.75, reason: "Matching Adobe Photoshop 2024 active layer EXIF headers." },
    { source: "evt-45b678", target: "actor-id-forge", weight: 0.7, reason: "Identical camera model override fields." }
  ]
};

const MOCK_SUMMARY: ThreatSummary = {
  total_events: 5,
  threat_level: "ELEVATED",
  summary: "3 of 5 events show suspicious or high-risk signals. Coordinated invoicing forgery campaign detected.",
  top_risks: [
    { indicator: "Metadata Modification Detected", frequency: 3 },
    { indicator: "Spoofed Creator Field", frequency: 3 },
    { indicator: "ELA Discrepancy Found in Image Text", frequency: 2 },
    { indicator: "EXIF Data Mismatch", frequency: 2 }
  ],
  high_risk_count: 3,
  suspicious_count: 2
};

export const fraudDnaApi = {
  getCampaigns: async (): Promise<CampaignsResponse> => {
    const base = apiBaseUrl();
    if (!base) {
      await new Promise((resolve) => setTimeout(resolve, 800));
      return MOCK_CAMPAIGNS;
    }
    const url = `${base}/api/fraud-dna/campaigns`;
    try {
      const response = await fetch(url, { signal: AbortSignal.timeout(4000) });
      if (!response.ok) throw new Error("HTTP Error");
      return (await response.json()) as CampaignsResponse;
    } catch (error) {
      console.warn("Fraud DNA Campaigns API fallback to mock:", error);
      await new Promise((resolve) => setTimeout(resolve, 800));
      return MOCK_CAMPAIGNS;
    }
  },

  getGraph: async (): Promise<GraphResponse> => {
    const base = apiBaseUrl();
    if (!base) {
      await new Promise((resolve) => setTimeout(resolve, 800));
      return MOCK_GRAPH;
    }
    const url = `${base}/api/fraud-dna/graph`;
    try {
      const response = await fetch(url, { signal: AbortSignal.timeout(4000) });
      if (!response.ok) throw new Error("HTTP Error");
      return (await response.json()) as GraphResponse;
    } catch (error) {
      console.warn("Fraud DNA Graph API fallback to mock:", error);
      await new Promise((resolve) => setTimeout(resolve, 800));
      return MOCK_GRAPH;
    }
  },

  getThreatSummary: async (): Promise<ThreatSummary> => {
    const base = apiBaseUrl();
    if (!base) {
      await new Promise((resolve) => setTimeout(resolve, 800));
      return MOCK_SUMMARY;
    }
    const url = `${base}/api/fraud-dna/threat-summary`;
    try {
      const response = await fetch(url, { signal: AbortSignal.timeout(4000) });
      if (!response.ok) throw new Error("HTTP Error");
      return (await response.json()) as ThreatSummary;
    } catch (error) {
      console.warn("Fraud DNA Threat Summary API fallback to mock:", error);
      await new Promise((resolve) => setTimeout(resolve, 800));
      return MOCK_SUMMARY;
    }
  },

  recluster: async (): Promise<CampaignsResponse> => {
    const base = apiBaseUrl();
    if (!base) {
      await new Promise((resolve) => setTimeout(resolve, 1500));
      return MOCK_CAMPAIGNS;
    }
    const url = `${base}/api/fraud-dna/recluster`;
    try {
      const response = await fetch(url, { method: "POST", signal: AbortSignal.timeout(4000) });
      if (!response.ok) throw new Error("HTTP Error");
      return (await response.json()) as CampaignsResponse;
    } catch (error) {
      console.warn("Fraud DNA Recluster API fallback to mock:", error);
      await new Promise((resolve) => setTimeout(resolve, 1500));
      return MOCK_CAMPAIGNS;
    }
  }
};

export default fraudDnaApi;
