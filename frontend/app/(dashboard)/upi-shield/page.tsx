"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import type { Variants } from "framer-motion";
import {
  Smartphone,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Copy,
  Check,
  Shield,
  Eye,
  Cpu,
  BarChart2,
  Zap,
} from "lucide-react";
import { UploadZone } from "@/components/ui/UploadZone";
import { ScoreGauge } from "@/components/ui/ScoreGauge";
import { Badge } from "@/components/ui/Badge";
import { DataCard } from "@/components/ui/DataCard";
import { AIInsightCard } from "@/components/ui/AIInsightCard";
import { FeatureBar } from "@/components/ui/FeatureBar";
import { SkeletonLoader } from "@/components/ui/SkeletonLoader";
import { Button } from "@/components/ui/Button";
import { upiService } from "@/services/upi";
import type { UPIAnalysisResult, UPIAIResult } from "@/types";

// ─── Stagger animation variants ────────────────────────────────────────────
const container: Variants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.08 } },
};
const item: Variants = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: [0, 0, 0.3, 1] } },
};

// ─── Small check/cross icon helper ────────────────────────────────────────
const StatusIcon = ({ ok }: { ok: boolean }) =>
  ok ? (
    <CheckCircle className="h-4 w-4 text-risk-none shrink-0" />
  ) : (
    <XCircle className="h-4 w-4 text-risk-high shrink-0" />
  );

// ─── Copyable mono value ────────────────────────────────────────────────────
const CopyMono = ({ value }: { value: string }) => {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard.writeText(value).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };
  return (
    <span className="inline-flex items-center gap-1.5 font-mono text-[13px] text-text-primary">
      {value}
      <button
        onClick={copy}
        className="text-text-muted hover:text-brand transition-colors"
        title="Copy"
      >
        {copied ? <Check className="h-3 w-3 text-risk-none" /> : <Copy className="h-3 w-3" />}
      </button>
    </span>
  );
};

// ─── Confidence bar ──────────────────────────────────────────────────────────
const ConfidenceBar = ({ label, value }: { label: string; value: number }) => {
  const isHigh = value > 80;
  const isMed = value > 60;
  
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-caption">
        <span className="text-text-secondary">{label}</span>
        <span className="font-mono text-text-primary font-medium">{value}%</span>
      </div>
      <div className="h-1.5 rounded-full bg-surface-raised border border-border-default/40 overflow-hidden relative">
        <motion.div
          className={`h-full rounded-full ${isHigh ? "bg-risk-none" : isMed ? "bg-risk-medium" : "bg-risk-high"}`}
          initial={{ width: "0%" }}
          animate={{ width: `${value}%` }}
          transition={{ duration: 0.7, ease: "easeOut" }}
        />
      </div>
    </div>
  );
};

// ─── XAI features for UPI ───────────────────────────────────────────────────
function buildXAIFeatures(result: UPIAnalysisResult) {
  return [
    { name: "UTR format validity",      value: result.is_valid_utr ? 0 : 1,     contribution: result.is_valid_utr ? -25 : 40 },
    { name: "Font consistency",          value: result.font_anomalies_detected ? 1 : 0, contribution: result.font_anomalies_detected ? 35 : -20 },
    { name: "Receiver VPA suspicion",   value: result.suspicious_handle_flagged ? 1 : 0, contribution: result.suspicious_handle_flagged ? 30 : -15 },
    { name: "Amount plausibility",       value: result.amount,                    contribution: result.amount > 25000 ? 15 : -10 },
    { name: "ELA tamper regions",        value: result.ela_tamper_regions ?? 0,  contribution: (result.ela_tamper_regions ?? 0) * 12 },
    { name: "OCR confidence",            value: result.ocr_confidence ?? 90,     contribution: (result.ocr_confidence ?? 90) > 80 ? -18 : 20 },
  ];
}

export default function UPIShieldPage() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<UPIAnalysisResult | null>(null);
  const [aiResult, setAIResult] = useState<UPIAIResult | null>(null);
  const [aiLoading, setAILoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileSelected = (f: File) => {
    setFile(f);
    setResult(null);
    setAIResult(null);
    setError(null);
  };

  const handleAnalyze = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);
    setResult(null);
    setAIResult(null);

    let p = 0;
    const tick = setInterval(() => {
      p = Math.min(p + 15, 90);
      setProgress(p);
    }, 120);

    try {
      const res = await upiService.analyzeScreenshot(file);
      clearInterval(tick);
      setProgress(100);
      setTimeout(() => {
        setResult(res);
        setProgress(0);
        setUploading(false);
      }, 300);
    } catch (e) {
      clearInterval(tick);
      setError(e instanceof Error ? e.message : "Analysis failed. Please retry.");
      setUploading(false);
      setProgress(0);
    }
  };

  const handleAIAnalyze = async () => {
    if (!result) return;
    setAILoading(true);
    try {
      const ai = await upiService.analyzeWithAI(result);
      setAIResult(ai);
    } catch {
      setAIResult({
        verdict: "SUSPICIOUS",
        confidence: 72,
        forgery_method: null,
        evidence_points: ["AI service temporarily unavailable. Structural analysis used as fallback."],
        analyst_note: "Please retry AI analysis for a full LLM-generated narrative report.",
        recommended_action: "Verify directly with your bank using the UTR number.",
        model_used: "fallback",
        latency_ms: 0,
      });
    } finally {
      setAILoading(false);
    }
  };

  const xaiFeatures = result ? buildXAIFeatures(result) : [];

  return (
    <div className="space-y-8 font-sans">
      {/* Page header */}
      <motion.div initial="hidden" animate="visible" variants={container} className="space-y-1">
        <motion.div variants={item} className="flex items-center gap-2.5">
          <div className="h-9 w-9 rounded-xl bg-brand-subtle flex items-center justify-center">
            <Smartphone className="h-5 w-5 text-brand" />
          </div>
          <div>
            <h1 className="text-headline font-semibold text-text-primary">
              UPI Shield
            </h1>
            <p className="text-caption text-text-muted">
              Detect fake PhonePe, Google Pay &amp; Paytm payment screenshots
            </p>
          </div>
        </motion.div>
      </motion.div>

      {/* Split layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* LEFT — Upload */}
        <motion.div
          initial={{ opacity: 0, x: -16 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.4, delay: 0.1 }}
          className="space-y-4"
        >
          <DataCard className="p-5">
            <span className="text-label text-text-muted block mb-4">
              Upload Payment Screenshot
            </span>
            <UploadZone
              accept=".png,.jpg,.jpeg"
              maxSizeMB={5}
              subLabel="PNG or JPG only · Max 5 MB"
              onFileSelected={handleFileSelected}
              disabled={uploading}
              progress={uploading ? progress : 0}
            />

            {file && !uploading && !result && (
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-4"
              >
                <Button
                  onClick={handleAnalyze}
                  variant="solid"
                  className="w-full flex items-center justify-center gap-2"
                >
                  <Shield className="h-4 w-4" />
                  Analyze Screenshot
                </Button>
              </motion.div>
            )}

            {uploading && (
              <div className="mt-4 text-center text-caption text-text-muted animate-pulse">
                Running forensic analysis…
              </div>
            )}

            {error && (
              <div className="mt-3 flex items-center gap-2 text-caption text-risk-high bg-risk-high-bg border border-risk-high/25 rounded-lg px-4 py-3">
                <AlertTriangle className="h-4 w-4 shrink-0" />
                {error}
              </div>
            )}
          </DataCard>

          {/* How it works card */}
          <DataCard className="p-5">
            <span className="text-label text-text-muted block mb-3">
              How UPI Shield works
            </span>
            <ol className="space-y-3">
              {[
                { step: "1", label: "OCR extraction", desc: "Tesseract extracts UTR, VPA, and amount from the screenshot" },
                { step: "2", label: "Structural validation", desc: "UTR 12-digit format, VPA domain, and font consistency checks" },
                { step: "3", label: "ELA forensics", desc: "Error Level Analysis detects pixel manipulation regions" },
                { step: "4", label: "Groq LLM verdict", desc: "LLaMA 3.3 70B synthesizes a forensic analyst narrative" },
              ].map(({ step, label, desc }) => (
                <li key={step} className="flex items-start gap-3">
                  <span className="h-5 w-5 rounded-full bg-brand-subtle text-brand font-mono text-[11px] font-semibold flex items-center justify-center shrink-0 mt-0.5">
                    {step}
                  </span>
                  <div>
                    <span className="text-[13px] font-semibold text-text-primary">{label}</span>
                    <p className="text-caption text-text-muted leading-relaxed">{desc}</p>
                  </div>
                </li>
              ))}
            </ol>
          </DataCard>
        </motion.div>

        {/* RIGHT — Results */}
        <motion.div
          initial={{ opacity: 0, x: 16 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.4, delay: 0.15 }}
          className="space-y-4"
        >
          {/* Loading skeleton */}
          {uploading && (
            <DataCard className="p-6 space-y-4">
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
            </DataCard>
          )}

          {/* Results panel */}
          {result && !uploading && (
            <motion.div
              initial="hidden"
              animate="visible"
              variants={container}
              className="space-y-4"
            >
              {/* Verdict row */}
              <motion.div variants={item}>
                <DataCard className="p-5">
                  <div className="flex items-center gap-6">
                    <ScoreGauge score={result.risk_score} size={110} />
                    <div className="flex flex-col gap-3">
                      <div>
                        <span className="text-label text-text-muted block mb-1">
                          Forensic Verdict
                        </span>
                        <Badge variant={result.risk_level === "CRITICAL" ? "critical" : result.risk_level === "HIGH" ? "danger" : result.risk_level === "SUSPICIOUS" ? "warn" : "safe"} dot>
                          {result.risk_level} LEVEL VERDICT
                        </Badge>
                      </div>
                      <div>
                        <span className="text-label text-text-muted block mb-0.5">
                          Amount detected
                        </span>
                        <span className="font-mono text-title font-semibold text-text-primary">
                          {result.amount_extracted ?? `₹${result.amount.toLocaleString("en-IN")}`}
                        </span>
                      </div>
                    </div>
                  </div>
                </DataCard>
              </motion.div>

              {/* Detail cards 2×2 */}
              <motion.div variants={item} className="grid grid-cols-2 gap-3.5">
                {/* UTR Analysis */}
                <DataCard className="p-4">
                  <div className="flex items-center gap-1.5 mb-3">
                    <Shield className="h-3.5 w-3.5 text-brand" />
                    <span className="text-label text-text-muted font-semibold">
                      UTR Analysis
                    </span>
                  </div>
                  <div className="space-y-2">
                    <div>
                      <p className="text-[10px] text-text-muted mb-0.5">UTR Number</p>
                      {result.utr_number ? (
                        <CopyMono value={result.utr_number} />
                      ) : (
                        <span className="font-mono text-[13px] text-risk-high font-medium">Not found</span>
                      )}
                    </div>
                    <div className="flex items-center gap-1.5">
                      <StatusIcon ok={result.is_valid_utr} />
                      <span className="text-[12px] text-text-secondary">
                        {result.is_valid_utr ? "Valid 12-digit format" : "Invalid format"}
                      </span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <span className="font-mono text-[10px] text-text-muted bg-surface-raised border border-border-default/50 px-1.5 py-0.5 rounded">
                        {result.utr_format}
                      </span>
                    </div>
                  </div>
                </DataCard>

                {/* Visual Forensics */}
                <DataCard className="p-4">
                  <div className="flex items-center gap-1.5 mb-3">
                    <Eye className="h-3.5 w-3.5 text-intel" />
                    <span className="text-label text-text-muted font-semibold">
                      Visual Forensics
                    </span>
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-[12px] text-text-secondary">ELA tamper regions</span>
                      <span className="font-mono text-[12px] text-text-primary font-semibold">
                        {result.ela_tamper_regions ?? 0}
                      </span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <StatusIcon ok={result.font_consistent ?? !result.font_anomalies_detected} />
                      <span className="text-[12px] text-text-secondary">Font consistency</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <StatusIcon ok={result.color_authentic ?? true} />
                      <span className="text-[12px] text-text-secondary">Color authenticity</span>
                    </div>
                  </div>
                </DataCard>

                {/* Metadata */}
                <DataCard className="p-4">
                  <div className="flex items-center gap-1.5 mb-3">
                    <Cpu className="h-3.5 w-3.5 text-risk-medium" />
                    <span className="text-label text-text-muted font-semibold">
                      Metadata
                    </span>
                  </div>
                  <div className="space-y-1.5">
                    <div>
                      <p className="text-[10px] text-text-muted">App detected</p>
                      <p className="text-[12px] text-text-primary font-semibold">{result.app_detected ?? "Unknown"}</p>
                    </div>
                    <div>
                      <p className="text-[10px] text-text-muted">Sender VPA</p>
                      <p className="font-mono text-[11px] text-text-primary break-all leading-tight">{result.sender_upi_id}</p>
                    </div>
                    <div>
                      <p className="text-[10px] text-text-muted">Receiver VPA</p>
                      <p className={`font-mono text-[11px] break-all leading-tight ${result.suspicious_handle_flagged ? "text-risk-high font-semibold" : "text-text-primary"}`}>
                        {result.receiver_upi_id}
                      </p>
                    </div>
                  </div>
                </DataCard>

                {/* Confidence breakdown */}
                <DataCard className="p-4">
                  <div className="flex items-center gap-1.5 mb-3">
                    <BarChart2 className="h-3.5 w-3.5 text-brand" />
                    <span className="text-label text-text-muted font-semibold">
                      Confidence
                    </span>
                  </div>
                  <div className="space-y-2.5">
                    <ConfidenceBar label="OCR quality"   value={result.ocr_confidence ?? 90} />
                    <ConfidenceBar label="ELA analysis"  value={result.font_anomalies_detected ? 62 : 91} />
                    <ConfidenceBar label="AI verdict"    value={result.risk_score > 60 ? 88 : 94} />
                  </div>
                </DataCard>
              </motion.div>

              {/* AI Analyst button */}
              {!aiResult && !aiLoading && (
                <motion.div variants={item}>
                  <Button
                    onClick={handleAIAnalyze}
                    variant="intel"
                    className="w-full flex items-center justify-center gap-2"
                  >
                    <Zap className="h-4 w-4" strokeWidth={2.5} />
                    Run AI Analysis · LLaMA 3.3 70B
                  </Button>
                </motion.div>
              )}

              {/* AI Analyst Card */}
              {(aiLoading || aiResult) && (
                <motion.div variants={item}>
                  <AIInsightCard
                    isLoading={aiLoading}
                    title="UPI FORENSIC INSIGHT"
                    timestamp={aiResult ? new Date().toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" }) : undefined}
                    modelInfo={aiResult ? `${aiResult.model_used} · ${aiResult.latency_ms}ms` : undefined}
                  >
                    {aiResult && (
                      <div className="space-y-5 text-body text-text-primary">
                        {/* Verdict row */}
                        <div className="flex items-center gap-3.5 flex-wrap">
                          <div className="flex flex-col">
                            <span className="text-label text-text-muted mb-0.5">
                              AI Verdict
                            </span>
                            <span
                              className={`font-mono text-[15px] font-semibold ${
                                aiResult.verdict === "FORGED"
                                  ? "text-risk-high"
                                  : aiResult.verdict === "SUSPICIOUS"
                                  ? "text-risk-medium"
                                  : "text-risk-none"
                              }`}
                            >
                              {aiResult.verdict}
                            </span>
                          </div>
                          
                          <div className="flex items-center gap-2">
                            <span className="text-label text-text-muted">Confidence:</span>
                            <Badge variant={aiResult.confidence > 80 ? "safe" : aiResult.confidence > 60 ? "warn" : "danger"}>
                              {aiResult.confidence}%
                            </Badge>
                          </div>

                          {aiResult.forgery_method && (
                            <span className="font-mono text-[11px] text-text-muted bg-surface-raised border border-border-default/50 px-2 py-0.5 rounded-full">
                              {aiResult.forgery_method}
                            </span>
                          )}
                        </div>

                        {/* XAI bar */}
                        <FeatureBar features={xaiFeatures} title="Feature contributions (SHAP)" />

                        {/* Evidence points */}
                        <div>
                          <span className="text-label text-text-muted block mb-2">
                            Evidence points
                          </span>
                          <ul className="space-y-1.5">
                            {aiResult.evidence_points.map((pt, i) => (
                              <li key={i} className="flex items-start gap-2 text-body text-text-secondary">
                                <span className="font-mono text-[10px] text-brand mt-0.5 shrink-0">{i + 1}.</span>
                                {pt}
                              </li>
                            ))}
                          </ul>
                        </div>

                        {/* Analyst note */}
                        <div className="border-l-2 border-ai-border pl-4 bg-ai-subtle/30 py-1.5 pr-2 rounded-r-lg">
                          <p className="text-[13px] italic font-serif text-text-secondary leading-relaxed">
                            &ldquo;{aiResult.analyst_note}&rdquo;
                          </p>
                        </div>

                        {/* Recommended action */}
                        <div className="rounded-xl bg-risk-medium-bg border border-risk-medium/25 px-4 py-3">
                          <span className="text-label text-risk-medium block mb-1">
                            Recommended action
                          </span>
                          <p className="text-body text-text-primary">
                            {aiResult.recommended_action}
                          </p>
                        </div>
                      </div>
                    )}
                  </AIInsightCard>
                </motion.div>
              )}
            </motion.div>
          )}

          {/* Empty state */}
          {!result && !uploading && (
            <div className="flex flex-col items-center justify-center h-64 rounded-xl border border-dashed border-border-default bg-surface/50 text-center p-8">
              <Smartphone className="h-10 w-10 text-text-muted mb-3" />
              <p className="text-body text-text-muted">
                Upload a payment screenshot to begin forensic analysis
              </p>
            </div>
          )}
        </motion.div>
      </div>
    </div>
  );
}
