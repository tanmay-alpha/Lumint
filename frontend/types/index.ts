// Type declarations matching the Lumint FastAPI backend models

export interface IndicatorCount {
  indicator: string;
  count: number;
}

export type RiskLevel = "CLEAN" | "SUSPICIOUS" | "HIGH" | "CRITICAL" | "NONE" | "NORMAL" | "ELEVATED";

export interface StatsResponse {
  total_events: number;
  document_events: number;
  url_events: number;
  clean_count: number;
  suspicious_count: number;
  high_risk_count: number;
  active_campaigns: number;
  average_risk_score: number;
  top_indicators: IndicatorCount[];
  last_updated: string;
}

export interface RecentEvent {
  event_id: string;
  doc_id: string | null;
  source_type: "DOCUMENT" | "URL";
  original_filename: string | null;
  saved_filename: string | null;
  file_hash: string | null;
  metadata_hash: string | null;
  editor_tool: string | null;
  producer: string | null;
  creator: string | null;
  source_domain: string | null;
  top_keywords: string[];
  risk_indicators: string[];
  risk_score: number;
  risk_level: RiskLevel;
  document_type_hint: string;
  created_at: string;
}

export interface RecentEventsResponse {
  total: number;
  limit: number;
  events: RecentEvent[];
}

export interface RiskDistributionItem {
  risk_level: string;
  count: number;
}

export interface RiskDistributionResponse {
  distribution: RiskDistributionItem[];
}

export interface IndicatorSummaryResponse {
  indicators: IndicatorCount[];
}

// DocShield Forensics Types
export interface IndicatorDetail {
  rule: string;
  score: number;
  detail: string;
}

export interface DocumentMetadata {
  title: string | null;
  author: string | null;
  creator: string | null;
  producer: string | null;
  creation_date: string | null;
  modification_date: string | null;
  page_count: number | null;
  is_encrypted: boolean;
  file_size: number;
}

export interface ELAAnalysis {
  ela_discrepancy_score?: number;
  ela_score?: number;
  tampering_detected?: boolean;
  pages_analyzed?: number;
  [key: string]: unknown;
}

export interface LayoutAnalysis {
  font_discrepancies?: string[];
  layout_warnings?: string[];
  [key: string]: unknown;
}

export interface TextAnalysis {
  [key: string]: unknown;
}

export interface DocumentAnalysisResponse {
  doc_id: string;
  original_filename: string;
  saved_filename: string;
  file_path: string;
  file_size: number;
  content_type: string;
  analysis_status: string;
  risk_score: number | null;
  risk_level: RiskLevel | null;
  metadata: DocumentMetadata | null;
  text_analysis: TextAnalysis | null;
  layout_analysis: LayoutAnalysis | null;
  ela_analysis: ELAAnalysis | null;
  indicators: IndicatorDetail[] | null;
  explanation: string[] | null;
  analysis_warnings: string[] | null;
  message: string | null;
}

// PhishShield URL Analysis Types
export interface TriggeredRule {
  rule: string;
  score: number;
  detail: string;
}

export interface DomainSimilarityMatch {
  bank: string;
  similarity: number;
}

export interface PhishingCheckResponse {
  url: string;
  normalized_url: string;
  domain: string;
  risk_score: number;
  risk_level: RiskLevel;
  triggered_rules: TriggeredRule[];
  domain_similarity_matches: DomainSimilarityMatch[];
  phishing_fingerprint: RecentEvent | null;
  message: string;
}

export interface PhishingExplainResponse {
  risk_score: number;
  risk_level: RiskLevel;
  model_confidence: string;
  explanation: string;
  recommendation: string;
}

// Fraud DNA Clustering Types
export interface Campaign {
  campaign_id: string;
  name: string;
  threat_actor_hint: string;
  common_indicators: string[];
  common_keywords: string[];
  associated_domains: string[];
  associated_file_hashes: string[];
  event_ids: string[];
  risk_score: number;
  risk_level: RiskLevel;
  created_at: string;
  description: string;
}

export interface CampaignsResponse {
  campaigns: Campaign[];
  total_campaigns: number;
}

export interface GraphNode {
  id: string;
  label: string;
  type: "event" | "campaign" | "indicator" | "domain" | "hash";
  risk_score: number;
  risk_level: RiskLevel;
  details?: string;
}

export interface GraphEdge {
  source: string;
  target: string;
  type: string;
}

export interface GraphResponse {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface ThreatSummaryResponse {
  total_events: number;
  threat_level: RiskLevel;
  summary: string;
  top_risks: { indicator: string; frequency: number }[];
  high_risk_count: number;
  suspicious_count: number;
}

export interface FraudDNAFingerprint {
  event_id: string;
  doc_id: string | null;
  source_type: string;
  original_filename: string | null;
  saved_filename: string | null;
  file_hash: string | null;
  metadata_hash: string | null;
  editor_tool: string | null;
  producer: string | null;
  creator: string | null;
  source_domain: string | null;
  top_keywords: string[];
  risk_indicators: string[];
  risk_score: number;
  risk_level: string;
  document_type_hint: string | null;
  created_at: string;
}

// ─── UPI Shield Types ────────────────────────────────────────────────────────

export interface UPIAnalysisResult {
  id: number;
  timestamp: string;
  event_type: string;
  utr_number: string | null;
  utr_valid: boolean;
  utr_format: "phonepay" | "googlepay" | "paytm" | "unknown";
  sender_upi_id: string;
  receiver_upi_id: string;
  amount: number;
  transaction_date: string | null;
  is_valid_utr: boolean;
  font_anomalies_detected: boolean;
  suspicious_handle_flagged: boolean;
  risk_score: number;
  risk_level: "GENUINE" | "SUSPICIOUS" | "HIGH_RISK" | "NOT_UPI" | "ERROR";
  ai_fraud_explanation: string;
  raw_ocr_text: string | null;
  metadata_json: Record<string, unknown> | null;
  // Real XAI contributions returned by the backend (preferred over the
  // client-side heuristic values below).
  feature_contributions?: Array<{
    name: string;
    value: string | number | boolean | null;
    contribution: number;
  }>;
  // Derived fields used in UI (computed client-side from heuristics)
  ela_tamper_regions?: number;
  font_consistent?: boolean;
  color_authentic?: boolean;
  ocr_confidence?: number;
  amount_extracted?: string | null;
  app_detected?: string | null;
  timestamp_extracted?: string | null;
}

export interface UTRVerificationResult {
  utr_number: string;
  is_valid: boolean;
  risk_score: number;
  risk_level: string;
  known_fraud_match: boolean;
  checks_passed: string[];
  checks_failed: string[];
  message: string;
}

export interface QRScanResult {
  raw_uri: string;
  pa: string | null;
  pn: string | null;
  am: string | null;
  cu: string | null;
  risk_score: number;
  risk_level: string;
  is_suspicious_handle: boolean;
  message: string;
}

export interface UPIAIResult {
  verdict: "GENUINE" | "SUSPICIOUS" | "FORGED";
  confidence: number;
  forgery_method: string | null;
  evidence_points: string[];
  analyst_note: string;
  recommended_action: string;
  model_used: string;
  latency_ms: number;
}

// ─── AI Analysis Common Types ────────────────────────────────────────────────

export interface AIAnalysisFeature {
  name: string;
  value: number;
  contribution: number; // -100 to +100
}

export interface DocumentAIResponse {
  verdict: string;
  confidence: number;
  risk_score: number;
  attack_type: string | null;
  analyst_note: string;
  anomalies: string[];
  recommended_action: string;
  explanation: string;
  features: AIAnalysisFeature[];
  model_used: string;
  latency_ms: number;
}

export interface PhishingAIResponse {
  verdict: string;
  confidence: number;
  risk_score: number;
  attack_vector: string | null;
  target_brand: string | null;
  ioc_list: string[];
  analyst_note: string;
  recommended_action: string;
  explanation: string;
  features: AIAnalysisFeature[];
  model_used: string;
  latency_ms: number;
}