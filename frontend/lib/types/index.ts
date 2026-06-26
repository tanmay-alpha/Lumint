// Strict TypeScript Interfaces for Lumint Frontend & Backend Contracts

export type RiskLevel = "CLEAN" | "SUSPICIOUS" | "HIGH" | "CRITICAL" | "NONE" | "NORMAL" | "ELEVATED";

export interface IndicatorCount {
  indicator: string;
  count: number;
}

export interface DashboardStats {
  total_events: number;
  document_events: number;
  url_events: number;
  clean_count: number;
  suspicious_count: number;
  high_risk_count: number;
  critical_count: number;
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

export interface RiskDistributionItem {
  risk_level: string;
  count: number;
}

export interface RiskDistribution {
  distribution: RiskDistributionItem[];
}

export interface IndicatorSummary {
  indicators: IndicatorCount[];
}

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

export interface DocumentAnalysisResult {
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

export interface TriggeredRule {
  rule: string;
  score: number;
  detail: string;
}

export interface DomainSimilarityMatch {
  brand: string;
  actual_domain: string;
  similarity: number;
}

export interface WhoisInfo {
  registrar: string | null;
  creation_date: string | null;
  expiration_date: string | null;
  country: string | null;
  age_days: number | null;
  is_recently_registered: boolean | null;
}

export interface SslInfo {
  issuer: string | null;
  subject: string | null;
  valid_from: string | null;
  valid_to: string | null;
  is_expired: boolean | null;
  is_self_signed: boolean | null;
  san_count: number | null;
  age_days: number | null;
}

export interface PhishingAnalysisResult {
  url: string;
  normalized_url: string;
  domain: string;
  risk_score: number;
  risk_level: RiskLevel;
  triggered_rules: TriggeredRule[];
  domain_similarity_matches: DomainSimilarityMatch[];
  phishing_fingerprint: RecentEvent | null;
  message: string;
  whois: WhoisInfo | null;
  ssl: SslInfo | null;
}

export interface FraudFingerprint {
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

export interface FraudCampaign {
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

export interface GraphNode {
  id: string;
  label: string;
  type: string;
  risk_score: number;
  risk_level: RiskLevel;
  details?: string;
  source_type?: string;
  doc_id?: string | null;
}

export interface GraphEdge {
  source: string;
  target: string;
  type?: string;
  weight?: number;
  reason?: string;
}

export interface FraudGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface CampaignEvent {
  event_id: string;
  doc_id: string | null;
  source_type: "DOCUMENT" | "URL";
  label: string;
  risk_score: number;
  risk_level: string;
  document_type_hint: string;
  created_at: string;
}

export interface FraudCampaignDetail {
  campaign_id: string;
  event_count: number;
  risk_level: string;
  avg_risk_score: number;
  common_indicators: string[];
  common_keywords: string[];
  first_seen: string;
  last_seen: string;
  events: CampaignEvent[];
}

export interface CampaignsResponse {
  total_campaigns: number;
  total_events: number;
  campaigns: FraudCampaignDetail[];
}

export interface GraphResponse {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface ThreatRiskSummary {
  indicator: string;
  frequency: number;
}

export interface ThreatSummary {
  total_events: number;
  threat_level: string;
  summary: string;
  top_risks: ThreatRiskSummary[];
  high_risk_count: number;
  suspicious_count: number;
}

export interface HealthResponse {
  status: string;
  timestamp: string;
  version: string;
}

export interface TimelinePoint {
  date: string;        // YYYY-MM-DD
  phishing: number;    // URL events on that day
  documents: number;   // DOCUMENT events on that day
  total: number;       // phishing + documents
}

export interface TimelineResponse {
  days: number;
  start_date: string;
  end_date: string;
  points: TimelinePoint[];
  total_scans: number;
}

export interface DocumentAIResult {
  verdict: "GENUINE" | "SUSPICIOUS" | "FRAUDULENT";
  confidence: number;
  anomalies: string[];
  attack_type: string;
  analyst_note: string;
  recommended_action: string;
  model_used: string;
  latency_ms: number;
}

export interface PhishingAIResult {
  verdict: "SAFE" | "SUSPICIOUS" | "PHISHING";
  target_brand: string | null;
  attack_vector: "credential_harvest" | "malware_delivery" | "financial_scam" | "account_takeover" | "brand_impersonation" | "unknown";
  confidence: number;
  analyst_note: string;
  ioc_summary: string[];
  model_used: string;
  latency_ms: number;
}

export interface CampaignAIResult {
  campaign_name: string;
  threat_level: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  pattern_summary: string;
  estimated_scale: string;
  analyst_brief: string;
  recommended_actions: string[];
  ttps: string[];
  model_used: string;
  latency_ms: number;
}
