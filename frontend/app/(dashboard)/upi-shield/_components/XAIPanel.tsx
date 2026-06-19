"use client";

import React from "react";
import { motion } from "framer-motion";
import type { Variants } from "framer-motion";
import { Badge } from "@/components/ui/Badge";
import { AIInsightCard } from "@/components/ui/AIInsightCard";
import { FeatureContribution } from "@/components/ui/FeatureContribution";
import type { UPIAnalysisResult } from "@/types";

// ─── XAI features for UPI ───────────────────────────────────────────────────
//
// Use the backend's real XAI contributions (feature_contributions) when the
// server has provided them. Fall back to client-side heuristics only for the
// structural case where the server response doesn't carry SHAP values (e.g.
// older API version or mock data).
function buildXAIFeatures(result: UPIAnalysisResult) {
  const backend = (result.feature_contributions || []).filter(
    (f) => f && (f.name || (f as any).feature)
  );
  if (backend.length > 0) {
    return backend.map((f) => {
      // Coerce value to a string|number (the FeatureContributionItem
      // type doesn't accept booleans/null — booleans become "Yes"/"No"
      // and null/undefined become "—").
      let value: string | number;
      const v = f.value;
      if (v === null || v === undefined) value = "—";
      else if (typeof v === "boolean") value = v ? "Yes" : "No";
      else value = v;
      return {
        name: f.name || (f as any).feature,
        value,
        contribution:
          typeof f.contribution === "number" ? f.contribution : Number(f.contribution ?? 0),
      };
    });
  }

  return [
    { name: "UTR format validity",      value: result.is_valid_utr ? "Valid" : "Invalid",     contribution: result.is_valid_utr ? -25.4 : 40.2 },
    { name: "Font consistency",          value: result.font_anomalies_detected ? "Anomaly" : "Consistent", contribution: result.font_anomalies_detected ? 35.8 : -20.3 },
    { name: "Receiver VPA suspicion",   value: result.suspicious_handle_flagged ? "Suspicious" : "Standard", contribution: result.suspicious_handle_flagged ? 30.1 : -15.6 },
    { name: "Amount plausibility",       value: result.amount != null ? `₹${result.amount.toLocaleString("en-IN")}` : "N/A", contribution: (result.amount ?? 0) > 25000 ? 15.2 : -10.5 },
    { name: "ELA tamper regions",        value: `${result.ela_tamper_regions ?? 0} regions`,  contribution: ((result.ela_tamper_regions ?? 0) * 12.3) + 1.2 },
    { name: "OCR confidence",            value: `${result.ocr_confidence ?? 90}%`,     contribution: (result.ocr_confidence ?? 90) > 80 ? -18.7 : 22.4 },
  ];
}

// ─── XAIPanel ──────────────────────────────────────────────────────────────
//
// Explainable-AI panel: feature contributions + evidence list + forensic
// verdict + recommended action. Renders only when a result is present.
//
// The XAI feature list is built from the result here so the parent page
// stays free of presentation-time shaping logic.
export interface XAIPanelProps {
  result: UPIAnalysisResult;
  itemVariants: Variants;
}

export function XAIPanel({ result, itemVariants }: XAIPanelProps) {
  const xaiFeatures = buildXAIFeatures(result);

  return (
    <motion.div variants={itemVariants}>
      <AIInsightCard
        isLoading={false}
        title="UPI FORENSIC ANALYSIS"
        className="border-2 border-dashed border-[var(--ai-border)] bg-[var(--ai-muted)]"
      >
        <div className="space-y-5 text-body text-[var(--text-1)]">
          <div className="flex items-center gap-4 flex-wrap pb-4 border-b border-[var(--ai-border)]/30">
            <div className="flex flex-col">
              <span className="text-[10px] text-[var(--text-3)] font-bold uppercase">
                Forensic Verdict
              </span>
              <span
                className={`font-mono text-[16px] font-bold mt-0.5 ${
                  result.risk_level === "HIGH_RISK"
                    ? "text-[var(--high)]"
                    : result.risk_level === "SUSPICIOUS"
                    ? "text-[var(--warn)]"
                    : result.risk_level === "NOT_UPI" || result.risk_level === "ERROR"
                    ? "text-[var(--text-3)]"
                    : "text-[var(--safe)]"
                }`}
              >
                {result.risk_level}
              </span>
            </div>
            <div className="flex flex-col">
              <span className="text-[10px] text-[var(--text-3)] font-bold uppercase">Risk Score</span>
              <div className="mt-0.5">
                <Badge variant={result.risk_score >= 75 ? "high" : result.risk_score >= 35 ? "warn" : "safe"} className="text-xs px-2.5 py-0.5">
                  {result.risk_score}
                </Badge>
              </div>
            </div>
          </div>

          <FeatureContribution features={xaiFeatures} title="Feature contributions (heuristic SHAP)" />

          <div>
            <span className="text-[11px] font-bold text-[var(--text-3)] uppercase tracking-wider block mb-2">
              Evidence points
            </span>
            <ul className="space-y-2">
              {result.feature_contributions && result.feature_contributions.length > 0 ? (
                result.feature_contributions.map((pt, i) => (
                  <li key={i} className="flex items-start gap-2 text-[12px] text-[var(--text-2)] leading-relaxed">
                    <span className="font-mono text-[10px] text-[var(--brand)] mt-0.5 shrink-0 font-bold">{i + 1}.</span>
                    <span><strong className="text-[var(--text-1)]">{pt.name}:</strong> {pt.value}</span>
                  </li>
                ))
              ) : (
                <li className="text-[12px] text-[var(--text-3)]">No feature-level evidence available for this scan.</li>
              )}
            </ul>
          </div>

          <div className="border-l-2 border-[var(--ai-border)] pl-4 bg-[var(--surface)]/50 py-2.5 pr-2 rounded-r-lg">
            <p className="text-[13px] italic font-serif text-[var(--text-2)] leading-relaxed">
              &ldquo;{result.ai_fraud_explanation || "Client-side heuristics completed. Verify directly with your bank using the UTR number."}&rdquo;
            </p>
          </div>

          <div className={`rounded-xl border px-4 py-3 ${
            result.risk_level === "HIGH_RISK"
              ? "bg-[var(--high-bg)] border-[var(--high-border)]/40 text-[var(--high)]"
              : result.risk_level === "SUSPICIOUS"
              ? "bg-[var(--warn-bg)] border-[var(--warn-border)]/40 text-[var(--warn)]"
              : "bg-[var(--safe-bg)] border-[var(--safe-border)]/40 text-[var(--safe)]"
          }`}>
            <span className="text-[11px] font-bold uppercase tracking-wider block mb-1">
              Recommended Action
            </span>
            <p className="text-[13px] font-semibold text-[var(--text-1)]">
              {result.risk_score >= 75
                ? "Do not trust this payment. Verify with your bank using the UTR number before sending goods or money."
                : result.risk_score >= 35
                ? "Treat with caution. Cross-check the UTR and amount with the sender before taking action."
                : "Looks consistent. Always verify high-value transfers via a second channel."}
            </p>
          </div>
        </div>
      </AIInsightCard>
    </motion.div>
  );
}

export default XAIPanel;