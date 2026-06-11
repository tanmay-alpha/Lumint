import {
  DocumentAIResult,
  PhishingAIResult,
  CampaignAIResult,
  DocumentAnalysisResult,
  PhishingAnalysisResult,
  FraudCampaignDetail,
  IndicatorDetail,
  TriggeredRule,
} from "../types";
import { apiBaseUrl } from "../config";

export const aiApi = {
  analyzeDocument: async (forensicsResult: DocumentAnalysisResult): Promise<DocumentAIResult> => {
    const base = apiBaseUrl();
    if (!base) {
      return {
        verdict: (forensicsResult.risk_score ?? 0) >= 75 ? "FRAUDULENT" : (forensicsResult.risk_score ?? 0) >= 35 ? "SUSPICIOUS" : "GENUINE",
        confidence: forensicsResult.risk_score || 50,
        anomalies: forensicsResult.indicators?.map((i: IndicatorDetail) => i.detail) || ["Automatic heuristics analysis triggered warning flags."],
        attack_type: (forensicsResult.risk_score ?? 0) >= 75 ? "Heuristics Threat Detected" : "None Detected",
        analyst_note: "Unable to contact Lumint AI intelligence node. Local forensics engine indicators remain fully valid.",
        recommended_action: (forensicsResult.risk_score ?? 0) >= 75 ? "Escalate to manual fraud review." : "No immediate action required.",
        model_used: "Local Heuristics Engine (Fallback)",
        latency_ms: 0,
      };
    }
    const url = `${base}/api/ai/document`;

    // Inject authentication header (if NEXT_PUBLIC_API_KEY is set)
    const apiKey = process.env.NEXT_PUBLIC_API_KEY;
    const requestHeaders: Record<string, string> = {
      "Content-Type": "application/json",
    };
    if (apiKey) {
      requestHeaders["Authorization"] = `Bearer ${apiKey}`;
    }

    try {
      const response = await fetch(url, {
        method: "POST",
        headers: requestHeaders,
        body: JSON.stringify(forensicsResult),
        signal: AbortSignal.timeout(15000), // AI processing takes a little longer
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return (await response.json()) as DocumentAIResult;
    } catch (error) {
      console.warn("DocShield AI fallback due to error:", error);
      // Construct fallback locally on connection error
      return {
        verdict: (forensicsResult.risk_score ?? 0) >= 75 ? "FRAUDULENT" : (forensicsResult.risk_score ?? 0) >= 35 ? "SUSPICIOUS" : "GENUINE",
        confidence: forensicsResult.risk_score || 50,
        anomalies: forensicsResult.indicators?.map((i: IndicatorDetail) => i.detail) || ["Automatic heuristics analysis triggered warning flags."],
        attack_type: (forensicsResult.risk_score ?? 0) >= 75 ? "Heuristics Threat Detected" : "None Detected",
        analyst_note: "Unable to contact Lumint AI intelligence node. Local forensics engine indicators remain fully valid.",
        recommended_action: (forensicsResult.risk_score ?? 0) >= 75 ? "Escalate to manual fraud review." : "No immediate action required.",
        model_used: "Local Heuristics Engine (Fallback)",
        latency_ms: 0,
      };
    }
  },

  analyzePhishing: async (phishingResult: PhishingAnalysisResult): Promise<PhishingAIResult> => {
    const base = apiBaseUrl();
    if (!base) {
      return {
        verdict: phishingResult.risk_score >= 75 ? "PHISHING" : phishingResult.risk_score >= 35 ? "SUSPICIOUS" : "SAFE",
        target_brand: phishingResult.domain_similarity_matches?.[0]?.brand || null,
        attack_vector: phishingResult.risk_score >= 75 ? "credential_harvest" : "unknown",
        confidence: phishingResult.risk_score || 50,
        analyst_note: "Unable to contact Lumint AI intelligence node. Local domain lookalike check remains valid.",
        ioc_summary: phishingResult.triggered_rules?.map((r: TriggeredRule) => r.detail) || ["Local heuristic check failed."],
        model_used: "Local Heuristics Engine (Fallback)",
        latency_ms: 0,
      };
    }
    const url = `${base}/api/ai/phishing`;

    // Inject authentication header (if NEXT_PUBLIC_API_KEY is set)
    const apiKey = process.env.NEXT_PUBLIC_API_KEY;
    const requestHeaders: Record<string, string> = {
      "Content-Type": "application/json",
    };
    if (apiKey) {
      requestHeaders["Authorization"] = `Bearer ${apiKey}`;
    }

    try {
      const response = await fetch(url, {
        method: "POST",
        headers: requestHeaders,
        body: JSON.stringify(phishingResult),
        signal: AbortSignal.timeout(15000),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return (await response.json()) as PhishingAIResult;
    } catch (error) {
      console.warn("PhishShield AI fallback due to error:", error);
      return {
        verdict: phishingResult.risk_score >= 75 ? "PHISHING" : phishingResult.risk_score >= 35 ? "SUSPICIOUS" : "SAFE",
        target_brand: phishingResult.domain_similarity_matches?.[0]?.brand || null,
        attack_vector: phishingResult.risk_score >= 75 ? "credential_harvest" : "unknown",
        confidence: phishingResult.risk_score || 50,
        analyst_note: "Unable to contact Lumint AI intelligence node. Local domain lookalike check remains valid.",
        ioc_summary: phishingResult.triggered_rules?.map((r: TriggeredRule) => r.detail) || ["Local heuristic check failed."],
        model_used: "Local Heuristics Engine (Fallback)",
        latency_ms: 0,
      };
    }
  },

  analyzeCampaign: async (campaignResult: FraudCampaignDetail): Promise<CampaignAIResult> => {
    const base = apiBaseUrl();
    if (!base) {
      return {
        campaign_name: `Operation Local-${campaignResult.campaign_id?.slice(0, 6) || "Cluster"}`,
        threat_level: campaignResult.risk_level === "CRITICAL" || campaignResult.risk_level === "HIGH" ? "HIGH" : "MEDIUM",
        pattern_summary: "Local pattern matches suggest a campaign targeting user attributes.",
        estimated_scale: `${campaignResult.event_count || 1} related event cluster`,
        analyst_brief: "Unable to contact Lumint AI intelligence node. Base Fraud DNA campaign matching is operational.",
        recommended_actions: ["Analyze related document signatures manually", "Block associated indicators"],
        ttps: campaignResult.common_indicators || ["T1566 - Phishing"],
        model_used: "Local Campaign Engine (Fallback)",
        latency_ms: 0,
      };
    }
    const url = `${base}/api/ai/campaign`;

    // Inject authentication header (if NEXT_PUBLIC_API_KEY is set)
    const apiKey = process.env.NEXT_PUBLIC_API_KEY;
    const requestHeaders: Record<string, string> = {
      "Content-Type": "application/json",
    };
    if (apiKey) {
      requestHeaders["Authorization"] = `Bearer ${apiKey}`;
    }

    try {
      const response = await fetch(url, {
        method: "POST",
        headers: requestHeaders,
        body: JSON.stringify(campaignResult),
        signal: AbortSignal.timeout(15000),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return (await response.json()) as CampaignAIResult;
    } catch (error) {
      console.warn("Fraud DNA Campaign AI fallback due to error:", error);
      return {
        campaign_name: `Operation Local-${campaignResult.campaign_id?.slice(0, 6) || "Cluster"}`,
        threat_level: campaignResult.risk_level === "CRITICAL" || campaignResult.risk_level === "HIGH" ? "HIGH" : "MEDIUM",
        pattern_summary: "Local pattern matches suggest a campaign targeting user attributes.",
        estimated_scale: `${campaignResult.event_count || 1} related event cluster`,
        analyst_brief: "Unable to contact Lumint AI intelligence node. Base Fraud DNA campaign matching is operational.",
        recommended_actions: ["Analyze related document signatures manually", "Block associated indicators"],
        ttps: campaignResult.common_indicators || ["T1566 - Phishing"],
        model_used: "Local Campaign Engine (Fallback)",
        latency_ms: 0,
      };
    }
  },
};

export default aiApi;
