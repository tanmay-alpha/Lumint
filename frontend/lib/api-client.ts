import {
  StatsResponse,
  RecentEventsResponse,
  CampaignsResponse,
  GraphResponse,
  ThreatSummaryResponse,
  RecentEvent
} from "@/types";
import { apiBaseUrl } from "./config";

// State to track if we are in live or mock mode
export let isLiveMode = false;
let modeListeners: ((live: boolean) => void)[] = [];

export function subscribeToModeChange(listener: (live: boolean) => void) {
  modeListeners.push(listener);
  listener(isLiveMode);
  return () => {
    modeListeners = modeListeners.filter(l => l !== listener);
  };
}

function setLiveMode(live: boolean) {
  if (isLiveMode !== live) {
    isLiveMode = live;
    modeListeners.forEach(listener => listener(live));
  }
}

// Generate realistic mock data
const mockEvents: RecentEvent[] = [
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
    created_at: new Date(Date.now() - 1000 * 60 * 25).toISOString() // 25 min ago
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
    created_at: new Date(Date.now() - 1000 * 60 * 75).toISOString() // 1.2 hours ago
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
    created_at: new Date(Date.now() - 1000 * 60 * 180).toISOString() // 3 hours ago
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
    created_at: new Date(Date.now() - 1000 * 60 * 320).toISOString() // 5 hours ago
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
    created_at: new Date(Date.now() - 1000 * 60 * 500).toISOString() // 8 hours ago
  }
];

export const mockStats: StatsResponse = {
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

export async function apiRequest<T>(
  path: string,
  options?: RequestInit,
  mockGenerator?: () => T
): Promise<T> {
  const base = apiBaseUrl();
  if (!base) {
    // No backend configured (e.g. deployed site without NEXT_PUBLIC_API_URL) —
    // skip the network round-trip and go straight to mock.
    if (mockGenerator) {
      await new Promise((resolve) => setTimeout(resolve, 800));
      setLiveMode(false);
      return mockGenerator();
    }
    throw new Error(`No API base URL configured; cannot reach ${path}`);
  }
  const url = `${base}${path}`;

  // Inject authorization header if API key is configured.
  const apiKey = process.env.NEXT_PUBLIC_API_KEY;
  const headers = new Headers(options?.headers);
  if (apiKey) {
    headers.set("Authorization", `Bearer ${apiKey}`);
  }

  // Build a composite signal: caller signal (for unmount cancellation)
  // + 3s timeout. If the caller passed their own AbortController (e.g.
  // on unmount), aborting it cancels the in-flight fetch.
  const callerSignal = options?.signal;
  const timeoutSignal = AbortSignal.timeout(3000)
  const signal = callerSignal
    ? AbortSignal.any([callerSignal, timeoutSignal])
    : timeoutSignal;

  try {
    const response = await fetch(url, {
      ...options,
      headers,
      signal,
    });

    if (!response.ok) {
      let errorMessage = `API Error: ${response.status} ${response.statusText}`;
      try {
        const errJson = await response.json();
        if (errJson && errJson.detail) {
          if (typeof errJson.detail === "string") {
            errorMessage = errJson.detail;
          } else if (Array.isArray(errJson.detail)) {
            errorMessage = errJson.detail.map((d: any) => d.msg || JSON.stringify(d)).join(", ");
          }
        }
      } catch (_) {}
      
      const errorObj = new Error(errorMessage);
      (errorObj as any).status = response.status;
      throw errorObj;
    }
    
    setLiveMode(true);
    return await response.json() as T;
  } catch (error) {
    console.warn(`Lumint API fallback to Mock on path ${path}:`, error);
    setLiveMode(false);
    
    // Do not fallback to mock for client/validation errors (400, 422) where the server is alive and gave a real rejection
    if (mockGenerator && (error as any).status !== 400 && (error as any).status !== 422) {
      // Simulate network lag for premium visual skeletons
      await new Promise(resolve => setTimeout(resolve, 800));
      return mockGenerator();
    }
    throw error;
  }
}

// Generate threat summary mock
export function getMockThreatSummary(): ThreatSummaryResponse {
  return {
    total_events: 148,
    threat_level: "ELEVATED",
    summary: "Active typosquatting campaigns mimicking financial institutions detected. DocShield scans indicate multiple suspicious PDF invoices modified with Acrobat Pro.",
    top_risks: [
      { indicator: "Lookalike Domain (Typosquatting)", frequency: 24 },
      { indicator: "ELA Discrepancy Found in Image Text", frequency: 18 },
      { indicator: "Metadata Modification Detected", frequency: 15 }
    ],
    high_risk_count: 25,
    suspicious_count: 31
  };
}

// Generate campaigns mock
export function getMockCampaigns(): CampaignsResponse {
  return {
    total_campaigns: 4,
    campaigns: [
      {
        campaign_id: "cmp-chase-spoof",
        name: "Chase Security Typosquats",
        threat_actor_hint: "UNC3429 (Financial Harvester)",
        common_indicators: ["Lookalike Domain (Typosquatting)", "Brand Name Injection"],
        common_keywords: ["chase", "verify", "secure", "banking"],
        associated_domains: ["chase-security-verify.net", "chase-mobile-alert.com", "chase-auth-login.org"],
        associated_file_hashes: [],
        event_ids: ["evt-12a839", "evt-chase-2", "evt-chase-3"],
        risk_score: 92,
        risk_level: "HIGH",
        created_at: new Date(Date.now() - 1000 * 60 * 60 * 24 * 3).toISOString(),
        description: "Phishing campaign utilizing typosquatted domains mimicking Chase verification portals to extract user credentials. High risk of immediate credential harvesting."
      },
      {
        campaign_id: "cmp-photoshop-invoice",
        name: "Invoice Ledger Forgeries",
        threat_actor_hint: "FIN7 (Invoicing Sub-group)",
        common_indicators: ["Metadata Modification Detected", "EXIF Data Mismatch (Photoshop Signature)"],
        common_keywords: ["invoice", "payment", "wire transfer", "routing"],
        associated_domains: [],
        associated_file_hashes: ["8f9a3e2b1c0d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f", "5e4d3c2b1a0f9e8d"],
        event_ids: ["evt-f89a23", "evt-invoice-2", "evt-invoice-3"],
        risk_score: 84,
        risk_level: "HIGH",
        created_at: new Date(Date.now() - 1000 * 60 * 60 * 24 * 5).toISOString(),
        description: "Forged commercial invoices edited using graphic design utilities to modify swift codes and destination bank details prior to accounts payable clearance."
      },
      {
        campaign_id: "cmp-paypal-alert",
        name: "PayPal Resolution Impersonation",
        threat_actor_hint: "ScamGroup-22",
        common_indicators: ["Brand Name Injection", "Suspicious Top Level Domain (.com)"],
        common_keywords: ["paypal", "resolution", "dispute", "billing"],
        associated_domains: ["paypal-resolution-center.com", "paypal-refund-claim.com"],
        associated_file_hashes: [],
        event_ids: ["evt-90a12c", "evt-paypal-2"],
        risk_score: 68,
        risk_level: "SUSPICIOUS",
        created_at: new Date(Date.now() - 1000 * 60 * 60 * 24 * 2).toISOString(),
        description: "Localized phishing campaign using PayPal branded elements to direct users towards fake dispute resolution portals."
      }
    ]
  };
}

// Generate graph mock
export function getMockGraph(): GraphResponse {
  const nodes: GraphResponse["nodes"] = [
    { id: "cmp-chase-spoof", label: "Chase Security Typosquats", type: "campaign", risk_score: 92, risk_level: "HIGH", details: "Financial harvesting typosquats" },
    { id: "evt-12a839", label: "chase-security-verify.net", type: "event", risk_score: 94, risk_level: "HIGH", details: "Phishing URL" },
    { id: "chase-mobile-alert.com", label: "chase-mobile-alert.com", type: "domain", risk_score: 88, risk_level: "HIGH", details: "Lookalike domain" },
    { id: "chase-auth-login.org", label: "chase-auth-login.org", type: "domain", risk_score: 90, risk_level: "HIGH", details: "Credential harvest portal" },
    { id: "typosquat-indicator", label: "Lookalike Domain", type: "indicator", risk_score: 80, risk_level: "SUSPICIOUS" },
    
    { id: "cmp-photoshop-invoice", label: "Invoice Ledger Forgeries", type: "campaign", risk_score: 84, risk_level: "HIGH", details: "Photoshop invoice modifications" },
    { id: "evt-f89a23", label: "invoice_9821.pdf", type: "event", risk_score: 87, risk_level: "HIGH", details: "Forged PDF invoice" },
    { id: "invoice_9822.pdf", label: "invoice_9822.pdf", type: "event", risk_score: 82, risk_level: "HIGH", details: "Photoshop altered PDF" },
    { id: "photoshop-signature", label: "Photoshop Signature", type: "indicator", risk_score: 70, risk_level: "SUSPICIOUS" }
  ];
  
  const edges: GraphResponse["edges"] = [
    { source: "evt-12a839", target: "cmp-chase-spoof", type: "belongs_to" },
    { source: "chase-mobile-alert.com", target: "cmp-chase-spoof", type: "associated_with" },
    { source: "chase-auth-login.org", target: "cmp-chase-spoof", type: "associated_with" },
    { source: "evt-12a839", target: "typosquat-indicator", type: "triggers" },
    { source: "chase-mobile-alert.com", target: "typosquat-indicator", type: "triggers" },
    
    { source: "evt-f89a23", target: "cmp-photoshop-invoice", type: "belongs_to" },
    { source: "invoice_9822.pdf", target: "cmp-photoshop-invoice", type: "belongs_to" },
    { source: "evt-f89a23", target: "photoshop-signature", type: "contains" },
    { source: "invoice_9822.pdf", target: "photoshop-signature", type: "contains" }
  ];

  return { nodes, edges };
}

export function getMockEvents(): RecentEventsResponse {
  return {
    total: mockEvents.length,
    limit: 20,
    events: mockEvents
  };
}
