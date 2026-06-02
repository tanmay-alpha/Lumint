import { apiRequest } from "@/lib/api-client";
import { PhishingCheckResponse, PhishingExplainResponse, TriggeredRule, DomainSimilarityMatch } from "@/types";

export const phishingService = {
  check: async (url: string): Promise<PhishingCheckResponse> => {
    return apiRequest<PhishingCheckResponse>(
      "/api/phishing/check",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      },
      () => {
        // Fallback Mock URL Checker logic based on input
        let score = 15;
        let level: "CLEAN" | "SUSPICIOUS" | "HIGH" = "CLEAN";
        const cleanUrl = url.trim().toLowerCase();
        let domain = "unknown.com";
        try {
          const parsed = new URL(cleanUrl.startsWith("http") ? cleanUrl : `http://${cleanUrl}`);
          domain = parsed.hostname;
        } catch {
          domain = cleanUrl;
        }

        const triggeredRules: TriggeredRule[] = [];
        const domainSimilarity: DomainSimilarityMatch[] = [];
        const keywords: string[] = [];

        if (domain.includes("chase") && !domain.endsWith("chase.com")) {
          score = 94;
          level = "HIGH";
          triggeredRules.push(
            { rule: "Lookalike Domain (Typosquatting)", score: 45, detail: "Domain mimics reputable brand 'Chase' without originating from authorized domains." },
            { rule: "Keywords Match High Risk (chase)", score: 20, detail: "Presence of brand anchor term 'chase' combined with security alert cues." },
            { rule: "Suspicious Top Level Domain (.net)", score: 15, detail: "Non-standard finance domain suffix (.net or .org used instead of official brand TLD)." }
          );
          domainSimilarity.push({ bank: "Chase Bank", similarity: 0.92 });
          keywords.push("login", "chase", "secure", "verify", "account");
        } else if (domain.includes("paypal") && !domain.endsWith("paypal.com")) {
          score = 68;
          level = "SUSPICIOUS";
          triggeredRules.push(
            { rule: "Lookalike Domain (Typosquatting)", score: 40, detail: "Domain mimics PayPal brand structure." },
            { rule: "Brand Name Injection", score: 15, detail: "Paypal term detected in subdomain/domain prefix." }
          );
          domainSimilarity.push({ bank: "PayPal Inc.", similarity: 0.88 });
          keywords.push("paypal", "dispute", "resolution", "billing");
        } else if (domain.includes("-verify") || domain.includes("login-") || domain.includes("secure-")) {
          score = 55;
          level = "SUSPICIOUS";
          triggeredRules.push(
            { rule: "Brand Name Injection", score: 25, detail: "URL employs high-frequency security verification keywords." }
          );
          keywords.push("login", "verify", "secure");
        } else {
          // Standard clean domain
          score = 8;
          level = "CLEAN";
        }

        return {
          url,
          normalized_url: cleanUrl.startsWith("http") ? cleanUrl : `https://${cleanUrl}`,
          domain,
          risk_score: score,
          risk_level: level,
          triggered_rules: triggeredRules,
          domain_similarity_matches: domainSimilarity,
          phishing_fingerprint: null,
          message: "URL analyzed successfully (Demo Mock Mode)",
        };
      }
    );
  },

  checkBatch: async (urls: string[]): Promise<{ total: number; results: PhishingCheckResponse[] }> => {
    return apiRequest<{ total: number; results: PhishingCheckResponse[] }>(
      "/api/phishing/check/batch",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ urls }),
      },
      () => {
        // Fallback batch scan
        const results: PhishingCheckResponse[] = urls.map((url) => {
          if (url.includes("chase") || url.includes("paypal")) {
            return {
              url,
              normalized_url: url,
              domain: url,
              risk_score: 85,
              risk_level: "HIGH",
              triggered_rules: [],
              domain_similarity_matches: [],
              phishing_fingerprint: null,
              message: "High risk url match"
            };
          }
          return {
            url,
            normalized_url: url,
            domain: url,
            risk_score: 5,
            risk_level: "CLEAN",
            triggered_rules: [],
            domain_similarity_matches: [],
            phishing_fingerprint: null,
            message: "Clean url match"
          };
        });
        return {
          total: urls.length,
          results
        };
      }
    );
  },

  explainConfidence: async (riskScore: number): Promise<PhishingExplainResponse> => {
    return apiRequest<PhishingExplainResponse>(
      `/api/phishing/confidence/${riskScore}`,
      { method: "GET" },
      () => {
        let label: "CLEAN" | "SUSPICIOUS" | "HIGH" = "CLEAN";
        let confidence = "HIGH";
        let explanation = "";
        let recommendation = "";

        if (riskScore <= 30) {
          label = "CLEAN";
          confidence = "HIGH";
          explanation = "URL shows no significant phishing signals. Safe to proceed with normal caution.";
          recommendation = "Allow";
        } else if (riskScore <= 60) {
          label = "SUSPICIOUS";
          confidence = "MEDIUM";
          explanation = "URL has moderate risk signals. Verify the domain independently before entering credentials.";
          recommendation = "Review";
        } else {
          label = "HIGH";
          confidence = "HIGH";
          explanation = "URL shows strong phishing indicators. Do not interact with this URL. Report it immediately.";
          recommendation = "Block";
        }

        return {
          risk_score: riskScore,
          risk_level: label,
          model_confidence: confidence,
          explanation,
          recommendation
        };
      }
    );
  }
};
