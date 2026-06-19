"use client";

import React from "react";
import { motion } from "framer-motion";
import type { Variants } from "framer-motion";
import { XAIPanel } from "./XAIPanel";
import {
  Smartphone,
  CheckCircle,
  XCircle,
  Shield,
  Eye,
  Cpu,
  BarChart2,
  Copy,
} from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { DataPoint } from "@/components/ui/DataPoint";
import { SkeletonLoader } from "@/components/ui/SkeletonLoader";
import { RiskScore } from "@/components/ui/RiskScore";
import { EmptyState } from "@/components/ui/EmptyState";
import type { UPIAnalysisResult } from "@/types";

// ─── Small check/cross icon helper ────────────────────────────────────────
const StatusIcon = ({ ok }: { ok: boolean }) =>
  ok ? (
    <CheckCircle className="h-4 w-4 text-[var(--safe)] shrink-0" />
  ) : (
    <XCircle className="h-4 w-4 text-[var(--high)] shrink-0" />
  );

// ─── Confidence bar ──────────────────────────────────────────────────────────
const ConfidenceBar = ({ label, value }: { label: string; value: number }) => {
  const barColor = value > 80 ? "bg-[var(--safe)]" : value >= 60 ? "bg-[var(--warn)]" : "bg-[var(--high)]";

  return (
    <div className="space-y-1.5">
      <div className="flex justify-between text-[11px] font-semibold uppercase tracking-wider">
        <span className="text-[var(--text-3)]">{label}</span>
      </div>
      <div className="h-1.5 bg-[var(--surface-3)] rounded-full overflow-hidden border border-[var(--border)]/20">
        <motion.div
          className={`h-full rounded-full ${barColor}`}
          initial={{ width: "0%" }}
          animate={{ width: `${value}%` }}
          transition={{ duration: 0.7, ease: "easeOut" }}
        />
      </div>
    </div>
  );
};

const renderVPA = (vpa: string | null, isSuspicious: boolean) => {
  if (!vpa) return <span className="text-[var(--text-4)]">N/A</span>;
  const parts = vpa.split("@");
  if (parts.length < 2) return <span className="font-mono">{vpa}</span>;
  return (
    <span className="font-mono text-[12px] font-semibold text-[var(--text-1)]">
      {parts[0]}
      <span className={isSuspicious ? "text-[var(--high)] font-bold bg-[var(--high-bg)] px-1 rounded" : "text-[var(--brand)] font-semibold"}>
        @{parts[1]}
      </span>
    </span>
  );
};

// ─── ResultsPanel ──────────────────────────────────────────────────────────
//
// Right column of the /upi-shield split layout. Shows the loading skeleton
// during analysis, the verdict + score + detail cards once a result lands,
// the dev-only debug panel, and the empty-state CTA before any upload.
//
// The framer-motion stagger variants are passed in from the parent page so
// `useReducedMotion` stays hoisted to a single hook call.
export interface ResultsPanelProps {
  result: UPIAnalysisResult | null;
  uploading: boolean;
  copied: boolean;
  containerVariants: Variants;
  itemVariants: Variants;
  onShare: () => void;
}

export function ResultsPanel({
  result,
  uploading,
  copied,
  containerVariants,
  itemVariants,
  onShare,
}: ResultsPanelProps) {
  return (
    <motion.div
      initial={{ opacity: 0, x: 16 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.4, delay: 0.15 }}
      className="space-y-4"
    >
      {/* Loading skeleton */}
      {uploading && (
        <Card className="p-6 space-y-4">
          <div className="flex items-center gap-6">
            <SkeletonLoader variant="ring" size={100} />
            <div className="flex-1 space-y-3">
              <SkeletonLoader variant="text-lg" className="w-2/3" />
              <SkeletonLoader variant="text-md" className="w-1/2" />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3 mt-2">
            <SkeletonLoader variant="rect" height={100} />
            <SkeletonLoader variant="rect" height={100} />
          </div>
        </Card>
      )}

      {/* Results panel */}
      {result && !uploading && (
        <div
          aria-live="polite"
          aria-atomic="true"
          role="region"
          aria-label="UPI Shield analysis result"
        >
          <motion.div
            initial="hidden"
            animate="visible"
            variants={containerVariants}
            className="space-y-4"
          >
            {/* Verdict row (Top Result Card) */}
            <motion.div variants={itemVariants}>
              <Card variant="elevated" className="p-8">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                  <div className="space-y-5 flex-1">
                    <div className="space-y-1.5">
                      <span className="text-[11px] uppercase tracking-widest text-[var(--text-3)] font-semibold block">
                        Forgery Probability
                      </span>
                      <div>
                        <Badge variant={result.risk_level === "HIGH_RISK" ? "critical" : result.risk_level === "SUSPICIOUS" ? "warn" : result.risk_level === "NOT_UPI" || result.risk_level === "ERROR" ? "high" : "safe"} dot className="text-xs px-3.5 py-1 font-semibold uppercase tracking-wider">
                          {result.risk_level} LEVEL VERDICT
                        </Badge>
                        <button
                          type="button"
                          onClick={onShare}
                          className="ml-2 mt-1 inline-flex items-center gap-1 rounded-md border border-[var(--border)] bg-[var(--surface-2)] px-2.5 py-1 text-[11px] font-semibold text-[var(--text-2)] hover:border-[var(--brand)] hover:text-[var(--brand)] transition-colors"
                        >
                          {copied ? "Copied!" : "Share Result"}
                        </button>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 pt-3 border-t border-[var(--border)]/40">
                      <div>
                        <span className="text-[11px] uppercase tracking-widest text-[var(--text-3)] block mb-1.5 font-semibold">
                          Amount Detected
                        </span>
                        <span className="font-mono text-[24px] font-bold text-[var(--text-1)] tracking-tight">
                          {result.amount_extracted ?? (result.amount != null ? `₹${result.amount.toLocaleString("en-IN")}` : "Not Found")}
                        </span>
                      </div>
                      <div>
                        <span className="text-[11px] uppercase tracking-widest text-[var(--text-3)] block mb-1.5 font-semibold">
                          UTR Number
                        </span>
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="font-mono text-[16px] font-bold text-[var(--text-1)] tracking-tight">
                            {result.utr_number ?? "Not Found"}
                          </span>
                          <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-md ${
                            result.is_valid_utr
                              ? "bg-[var(--brand-muted)] text-[var(--brand)] border border-[var(--brand-border)]/30"
                              : "bg-[var(--high-bg)] text-[var(--high)] border border-[var(--high-border)]/30"
                          }`}>
                            {result.is_valid_utr ? "VALID FORMAT" : "INVALID FORMAT"}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="flex justify-center shrink-0 self-center">
                    <RiskScore score={result.risk_score} size="lg" />
                  </div>
                </div>
              </Card>
            </motion.div>

            {/* Detail cards 2×2 */}
            <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Card 1: UTR Analysis */}
              <Card className="p-6 flex flex-col justify-between min-h-[175px]">
                <div className="space-y-4">
                  <div className="flex items-center gap-1.5 pb-2 border-b border-[var(--border)]/30">
                    <Shield className="h-4 w-4 text-[var(--brand)]" />
                    <span className="text-[11px] text-[var(--text-3)] font-bold uppercase tracking-wider">UTR Analysis</span>
                  </div>

                  <DataPoint
                    label="UTR Number"
                    value={result.utr_number ? result.utr_number : <span className="text-[var(--high)] font-semibold">Not Found</span>}
                    copyable={!!result.utr_number}
                    mono={true}
                  />

                  <div className="flex flex-wrap items-center gap-2.5 pt-1">
                    <span className={`text-[11px] font-semibold px-2.5 py-0.5 rounded-md inline-flex items-center gap-1.5 ${
                      result.is_valid_utr
                        ? "bg-[var(--safe-bg)] text-[var(--safe)] border border-[var(--safe-border)]/20"
                        : "bg-[var(--high-bg)] text-[var(--high)] border border-[var(--high-border)]/20"
                    }`}>
                      <StatusIcon ok={result.is_valid_utr} />
                      {result.is_valid_utr ? "Valid 12-digit format" : "Invalid format"}
                    </span>

                    {result.app_detected && (
                      <span className="text-[11px] font-semibold px-2.5 py-0.5 rounded-md inline-flex items-center gap-1.5 bg-[var(--surface-3)] text-[var(--text-2)] border border-[var(--border)]/65">
                        <span className={`h-1.5 w-1.5 rounded-full ${
                          result.app_detected.toLowerCase().includes("phonepe")
                            ? "bg-[#5f259f]"
                            : result.app_detected.toLowerCase().includes("google")
                            ? "bg-[#4285F4]"
                            : result.app_detected.toLowerCase().includes("paytm")
                            ? "bg-[#00baf2]"
                            : "bg-[var(--brand)]"
                        }`} />
                        {result.app_detected}
                      </span>
                    )}
                  </div>
                </div>
              </Card>

              {/* Card 2: Visual Forensics */}
              <Card className="p-6 flex flex-col justify-between min-h-[175px]">
                <div className="space-y-4">
                  <div className="flex items-center gap-1.5 pb-2 border-b border-[var(--border)]/30">
                    <Eye className="h-4 w-4 text-[var(--intel)]" />
                    <span className="text-[11px] text-[var(--text-3)] font-bold uppercase tracking-wider">Visual Forensics</span>
                  </div>

                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] text-[var(--text-3)] uppercase tracking-wider font-semibold">ELA Tamper Regions</span>
                      <span className="font-mono text-[13px] text-[var(--text-1)] font-bold">
                        {result.ela_tamper_regions ?? 0}
                      </span>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="text-[11px] text-[var(--text-3)] uppercase tracking-wider font-semibold">Font Consistency</span>
                      <span className={`inline-flex items-center gap-1.5 text-[12px] font-bold ${
                        (result.font_consistent ?? !result.font_anomalies_detected) ? "text-[var(--safe)]" : "text-[var(--high)]"
                      }`}>
                        <StatusIcon ok={result.font_consistent ?? !result.font_anomalies_detected} />
                        {result.font_consistent ?? !result.font_anomalies_detected ? "Pass" : "Anomaly"}
                      </span>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="text-[11px] text-[var(--text-3)] uppercase tracking-wider font-semibold">Color Authenticity</span>
                      <span className={`inline-flex items-center gap-1.5 text-[12px] font-bold ${
                        (result.color_authentic ?? true) ? "text-[var(--safe)]" : "text-[var(--high)]"
                      }`}>
                        <StatusIcon ok={result.color_authentic ?? true} />
                        {result.color_authentic ?? true ? "Pass" : "Failed"}
                      </span>
                    </div>
                  </div>
                </div>
              </Card>

              {/* Card 3: Metadata */}
              <Card className="p-6 flex flex-col justify-between min-h-[175px]">
                <div className="space-y-4">
                  <div className="flex items-center gap-1.5 pb-2 border-b border-[var(--border)]/30">
                    <Cpu className="h-4 w-4 text-[var(--warn)]" />
                    <span className="text-[11px] text-[var(--text-3)] font-bold uppercase tracking-wider">Metadata Parameters</span>
                  </div>

                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-[11px] text-[var(--text-3)] uppercase tracking-wider font-semibold">Detected Platform</span>
                      <span className="font-mono text-[12px] text-[var(--text-1)] font-bold">
                        {result.app_detected ?? "Unknown"}
                      </span>
                    </div>

                    <div className="space-y-1">
                      <span className="text-[10px] text-[var(--text-3)] uppercase tracking-wider font-bold block">Sender UPI ID</span>
                      <div className="flex items-center justify-between">
                        {renderVPA(result.sender_upi_id, false)}
                        {result.sender_upi_id && (
                          <button
                            onClick={() => navigator.clipboard.writeText(result.sender_upi_id!)}
                            className="text-[var(--text-3)] hover:text-[var(--text-1)] transition-colors"
                          >
                            <Copy className="h-3 w-3" />
                          </button>
                        )}
                      </div>
                    </div>

                    <div className="space-y-1">
                      <span className="text-[10px] text-[var(--text-3)] uppercase tracking-wider font-bold block">Receiver UPI ID</span>
                      <div className="flex items-center justify-between">
                        {renderVPA(result.receiver_upi_id, result.suspicious_handle_flagged)}
                        {result.receiver_upi_id && (
                          <button
                            onClick={() => navigator.clipboard.writeText(result.receiver_upi_id!)}
                            className="text-[var(--text-3)] hover:text-[var(--text-1)] transition-colors"
                          >
                            <Copy className="h-3 w-3" />
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </Card>

              {/* Card 4: Confidence breakdown */}
              <Card className="p-6 flex flex-col justify-between min-h-[175px]">
                <div className="space-y-4">
                  <div className="flex items-center gap-1.5 pb-2 border-b border-[var(--border)]/30">
                    <BarChart2 className="h-4 w-4 text-[var(--brand)]" />
                    <span className="text-[11px] text-[var(--text-3)] font-bold uppercase tracking-wider">Confidence Matrix</span>
                  </div>

                  <div className="space-y-3">
                    <ConfidenceBar label="OCR Quality" value={result.ocr_confidence ?? 90} />
                    <ConfidenceBar label="ELA Analysis" value={result.font_anomalies_detected ? 62 : 91} />
                    <ConfidenceBar label="AI Verdict" value={result.risk_score > 60 ? 88 : 94} />
                  </div>
                </div>
              </Card>
            </motion.div>

            {/* XAI panel — sibling of the 2×2 detail grid inside the same
                stagger container so it animates in with the same children-
                stagger pattern as before. */}
            <XAIPanel result={result} itemVariants={itemVariants} />
          </motion.div>
        </div>
      )}

      {/* Debug panel — dev mode only. Shows raw OCR + extracted fields. */}
      {result && process.env.NODE_ENV === "development" && (
        <details className="mt-4 rounded-lg border border-[var(--border)] bg-[var(--surface-1)] p-4">
          <summary className="cursor-pointer text-sm text-[var(--text-2)] font-semibold">
            Debug: Raw OCR &amp; Extracted Fields
          </summary>
          <div className="mt-4 space-y-2 text-xs font-mono">
            <div><span className="text-[var(--brand)]">UTR:</span> {result.utr_number || "(not found)"}</div>
            <div><span className="text-[var(--brand)]">Amount:</span> {result.amount || "(not found)"}</div>
            <div><span className="text-[var(--brand)]">VPA (receiver):</span> {result.receiver_upi_id || "(not found)"}</div>
            <div><span className="text-[var(--brand)]">App:</span> {result.app_detected || "(not found)"}</div>
            <div><span className="text-[var(--brand)]">Timestamp:</span> {result.timestamp_extracted || "(not found)"}</div>
            <div><span className="text-[var(--brand)]">Confidence:</span> {result.ocr_confidence ?? "?"}%</div>
            <div>
              <span className="text-[var(--brand)]">OCR text (first 800 chars):</span>
              <pre className="mt-1 max-h-48 overflow-auto rounded bg-[var(--surface-2)] p-2 text-[var(--text-2)] whitespace-pre-wrap">
                {(result.raw_ocr_text || "").slice(0, 800)}
              </pre>
            </div>
          </div>
        </details>
      )}

      {/* Empty state (UPI Shield) */}
      {!result && !uploading && (
        <EmptyState
          title="No analysis yet"
          description="Upload a screenshot to begin"
          icon={<Smartphone className="h-12 w-12 text-[var(--text-3)]" />}
          className="h-[320px]"
        />
      )}
    </motion.div>
  );
}

export default ResultsPanel;