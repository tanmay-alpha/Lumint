"use client";

import React, { useState } from "react";
import UploadZone from "@/components/UploadZone";
import { documentApi } from "@/lib/api/documents";
import { DocumentAnalysisResult } from "@/lib/types";
import GlassCard from "@/components/ui/GlassCard";
import RiskBadge from "@/components/ui/RiskBadge";
import ScoreRing from "@/components/ui/ScoreRing";
import {
  FileText,
  FileCheck,
  AlertTriangle,
  Info,
  Calendar,
  Layers,
  Terminal,
  Sparkles,
  Brain,
  Cpu,
  ShieldAlert
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import aiApi from "@/lib/api/ai";
import { DocumentAIResult } from "@/lib/types";

type TabID = "metadata" | "indicators" | "explanation" | "tampering" | "ai_report";

export default function DocShieldPage() {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState<DocumentAnalysisResult | null>(null);
  const [activeTab, setActiveTab] = useState<TabID>("metadata");
  
  const [isAnalyzingAI, setIsAnalyzingAI] = useState(false);
  const [aiResult, setAiResult] = useState<DocumentAIResult | null>(null);

  const handleFileAccepted = async (acceptedFile: File) => {
    setIsAnalyzing(true);
    setResult(null);
    setAiResult(null);

    try {
      const response = await documentApi.analyzeDocument(acceptedFile);
      setResult(response);
      
      // Auto-trigger AI Analysis
      setIsAnalyzingAI(true);
      try {
        const aiResponse = await aiApi.analyzeDocument(response);
        setAiResult(aiResponse);
      } catch (aiErr) {
        console.error("DocShield AI report failure:", aiErr);
      } finally {
        setIsAnalyzingAI(false);
      }
    } catch (err) {
      console.error("Document analysis failed:", err);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const getRiskVariant = (level: string) => {
    switch (level) {
      case "CRITICAL":
        return "critical";
      case "HIGH":
        return "high";
      case "SUSPICIOUS":
        return "medium";
      case "LOW":
        return "low";
      default:
        return "safe";
    }
  };

  const tabs: { id: TabID; label: string }[] = [
    { id: "metadata", label: "File Metadata" },
    { id: "indicators", label: "Forensic Rules" },
    { id: "explanation", label: "Forensic Reasoning" },
    { id: "tampering", label: "Image Tampering (ELA)" },
    { id: "ai_report", label: "AI Forensic Report" },
  ];

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-text-primary">
          DocShield Document Forensics
        </h1>
        <p className="text-sm text-text-secondary font-medium">
          Analyze PDF and image document structures for spoofed creator tags, structural edits, and ELA tampering.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Upload Zone Panel */}
        <div className="lg:col-span-1 space-y-6">
          <GlassCard className="p-6">
            <h3 className="text-sm font-bold uppercase tracking-wider text-text-secondary mb-4">
              Select Forensic Entity
            </h3>
            <UploadZone onFileAccepted={handleFileAccepted} isLoading={isAnalyzing} />

            <div className="mt-6 border-t border-border/40 pt-4 text-xs text-text-secondary leading-relaxed font-semibold">
              <div className="flex items-start gap-2 mb-2">
                <Info className="h-4 w-4 text-accent-blue shrink-0 mt-0.5" />
                <span>Uploaded entities are verified in a secure sandbox. Metadata structures are hashed instantly.</span>
              </div>
            </div>
          </GlassCard>

          {/* Quick instructions box */}
          <GlassCard className="p-6 bg-surface/30">
            <h4 className="text-xs font-bold uppercase tracking-widest text-text-primary mb-3">Forensic Checkpoints</h4>
            <ul className="space-y-2.5 text-xs text-text-secondary font-semibold">
              <li className="flex items-center gap-2">
                <span className="h-1.5 w-1.5 rounded-full bg-accent-blue" />
                Magic-byte checking verifies actual mime header signatures
              </li>
              <li className="flex items-center gap-2">
                <span className="h-1.5 w-1.5 rounded-full bg-accent-blue" />
                Error Level Analysis highlights digital image layer edits
              </li>
              <li className="flex items-center gap-2">
                <span className="h-1.5 w-1.5 rounded-full bg-accent-blue" />
                Metadata field alignment checks creation vs modification times
              </li>
            </ul>
          </GlassCard>
        </div>

        {/* Results Panel */}
        <div className="lg:col-span-2">
          <AnimatePresence mode="wait">
            {isAnalyzing ? (
              <motion.div
                key="loading-box"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="h-full min-h-[400px] flex flex-col items-center justify-center text-center p-8 bg-surface/40 border border-border/60 rounded-3xl backdrop-blur"
              >
                <div className="relative flex items-center justify-center">
                  <div className="h-16 w-16 rounded-full border-4 border-slate-100 border-t-accent-blue animate-spin" />
                  <FileText className="absolute h-6 w-6 text-accent-blue animate-pulse" />
                </div>
                <h3 className="text-base font-bold text-text-primary mt-6">Parsing File Signatures</h3>
                <p className="text-xs text-text-secondary mt-1.5 max-w-sm font-semibold">
                  Extracting document stream layers, computing file hashes, and running forensic pattern scanners...
                </p>
              </motion.div>
            ) : result ? (
              <motion.div
                key="results-box"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="space-y-6"
              >
                {/* Result Hero Header */}
                <GlassCard className="p-6">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6">
                    <div className="flex items-start gap-4">
                      <div className="h-12 w-12 rounded-xl bg-accent-blue/10 border border-accent-blue/20 text-accent-blue flex items-center justify-center shrink-0">
                        <FileCheck className="h-6 w-6" />
                      </div>
                      <div>
                        <span className="text-[10px] font-mono font-bold text-text-secondary bg-bg-base border border-border/40 px-2 py-0.5 rounded uppercase">
                          UUID: {result.doc_id.slice(0, 8)}
                        </span>
                        <h3 className="text-lg font-bold text-text-primary mt-1 break-all pr-2">
                          {result.original_filename}
                        </h3>
                        <div className="flex flex-wrap items-center gap-3 mt-1.5 text-xs text-text-secondary font-semibold">
                          <span>{(result.file_size / 1024).toFixed(1)} KB</span>
                          <span className="h-1.5 w-1.5 rounded-full bg-border" />
                          <span>{result.content_type}</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-4 shrink-0 sm:border-l sm:border-border/40 sm:pl-6">
                      <div className="flex flex-col items-end gap-1">
                        <span className="text-[10px] font-bold text-text-secondary uppercase">
                          Platform Verdict
                        </span>
                        <RiskBadge variant={getRiskVariant(result.risk_level ?? "NONE")} />
                      </div>
                      <ScoreRing score={result.risk_score ?? 0} size={84} />
                    </div>
                  </div>
                </GlassCard>

                {/* Tab Menu */}
                <div className="flex border-b border-border/40 gap-1 overflow-x-auto">
                  {tabs.map((tab) => {
                    const isActive = activeTab === tab.id;
                    return (
                      <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`px-4 py-2.5 text-xs font-bold border-b-2 transition-all shrink-0 ${
                          isActive
                            ? "border-text-primary text-text-primary"
                            : "border-transparent text-text-secondary hover:text-text-primary"
                        }`}
                      >
                        {tab.label}
                      </button>
                    );
                  })}
                </div>

                {/* Tab Contents */}
                <div className="min-h-[250px]">
                  {activeTab === "metadata" && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="grid grid-cols-1 md:grid-cols-2 gap-6"
                    >
                      <GlassCard className="p-5 space-y-4">
                        <h4 className="text-xs font-bold text-text-secondary uppercase tracking-widest flex items-center gap-1.5">
                          <Layers className="h-3.5 w-3.5" /> File Identity
                        </h4>

                        <div className="space-y-3 font-semibold text-xs text-text-primary">
                          <div className="flex justify-between py-1 border-b border-border/20">
                            <span className="text-text-secondary">Original Name</span>
                            <span className="font-mono">{result.original_filename}</span>
                          </div>
                          <div className="flex justify-between py-1 border-b border-border/20">
                            <span className="text-text-secondary">Stored Name</span>
                            <span className="font-mono">{result.saved_filename}</span>
                          </div>
                          <div className="flex justify-between py-1 border-b border-border/20">
                            <span className="text-text-secondary">File Path</span>
                            <span className="font-mono text-right max-w-[200px] truncate select-all">{result.file_path}</span>
                          </div>
                          <div className="flex justify-between py-1">
                            <span className="text-text-secondary">Content Type</span>
                            <span className="font-mono">{result.content_type}</span>
                          </div>
                        </div>
                      </GlassCard>

                      <GlassCard className="p-5 space-y-4">
                        <h4 className="text-xs font-bold text-text-secondary uppercase tracking-widest flex items-center gap-1.5">
                          <Calendar className="h-3.5 w-3.5" /> Document Metadata
                        </h4>

                        {result.metadata ? (
                          <div className="space-y-3 font-semibold text-xs text-text-primary">
                            <div className="flex justify-between py-1 border-b border-border/20">
                              <span className="text-text-secondary">Author Creator</span>
                              <span>{result.metadata.creator || "Unknown"}</span>
                            </div>
                            <div className="flex justify-between py-1 border-b border-border/20">
                              <span className="text-text-secondary">Editor Signature</span>
                              <span>{result.metadata.producer || "Unknown"}</span>
                            </div>
                            <div className="flex justify-between py-1 border-b border-border/20">
                              <span className="text-text-secondary">Created Date</span>
                              <span className="font-mono text-[10px]">
                                {result.metadata.creation_date ? new Date(result.metadata.creation_date).toLocaleString() : "Unknown"}
                              </span>
                            </div>
                            <div className="flex justify-between py-1">
                              <span className="text-text-secondary">Modified Date</span>
                              <span className="font-mono text-[10px]">
                                {result.metadata.modification_date ? new Date(result.metadata.modification_date).toLocaleString() : "Unknown"}
                              </span>
                            </div>
                          </div>
                        ) : (
                          <div className="text-xs text-text-secondary italic">No nested document metadata metadata available.</div>
                        )}
                      </GlassCard>
                    </motion.div>
                  )}

                  {activeTab === "indicators" && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="space-y-4"
                    >
                      <GlassCard className="p-5">
                        <h4 className="text-xs font-bold text-text-secondary uppercase tracking-widest flex items-center gap-1.5 mb-4">
                          <AlertTriangle className="h-3.5 w-3.5" /> Checked Forensic Policy Rules
                        </h4>

                        <div className="space-y-3.5">
                          {result.indicators && result.indicators.length > 0 ? (
                            result.indicators.map((indicator, idx) => (
                              <div
                                key={idx}
                                className="flex items-start gap-4 p-3 rounded-xl bg-bg-base border border-border/40"
                              >
                                <span className="h-6 w-6 rounded-lg bg-risk-critical/10 text-risk-critical flex items-center justify-center font-mono font-bold text-xs shrink-0 mt-0.5">
                                  {indicator.score}
                                </span>
                                <div className="space-y-1">
                                  <div className="text-xs font-bold text-text-primary">{indicator.rule}</div>
                                  <div className="text-xs text-text-secondary leading-normal font-semibold">{indicator.detail}</div>
                                </div>
                              </div>
                            ))
                          ) : (
                            <div className="text-xs text-text-secondary italic">No forensic anomalies triggered. Document appears standard.</div>
                          )}
                        </div>
                      </GlassCard>
                    </motion.div>
                  )}

                  {activeTab === "explanation" && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="space-y-4"
                    >
                      <GlassCard className="p-5">
                        <h4 className="text-xs font-bold text-text-secondary uppercase tracking-widest flex items-center gap-1.5 mb-4">
                          <Terminal className="h-3.5 w-3.5" /> Chain of Forensic Reasoning
                        </h4>

                        <div className="space-y-4 font-semibold text-xs leading-relaxed text-text-secondary">
                          {result.explanation && result.explanation.length > 0 ? (
                            result.explanation.map((step, idx) => (
                              <div key={idx} className="flex gap-3">
                                <span className="h-5 w-5 shrink-0 rounded-full border border-border flex items-center justify-center font-mono text-[10px] text-text-primary bg-bg-base font-bold">
                                  {idx + 1}
                                </span>
                                <p className="pt-0.5">{step}</p>
                              </div>
                            ))
                          ) : (
                            <p className="italic">No forensic anomalies were flagged. The file matching signatures align with common standards.</p>
                          )}
                        </div>
                      </GlassCard>
                    </motion.div>
                  )}

                  {activeTab === "tampering" && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="space-y-4"
                    >
                      <GlassCard className="p-5">
                        <h4 className="text-xs font-bold text-text-secondary uppercase tracking-widest flex items-center gap-1.5 mb-4">
                          <Layers className="h-3.5 w-3.5" /> Error Level Analysis (ELA) Breakdown
                        </h4>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                          <div className="space-y-4.5">
                            <div className="p-4.5 rounded-xl border border-border/50 bg-bg-base">
                              <div className="text-[10px] font-bold text-text-secondary uppercase mb-1">
                                ELA Discrepancy Margin
                              </div>
                              <div className="flex items-baseline gap-2 font-mono">
                                <span className="text-2xl font-bold text-text-primary">
                                  {result.ela_analysis ? (
                                    typeof result.ela_analysis.ela_discrepancy_score === "number"
                                      ? (result.ela_analysis.ela_discrepancy_score * 100).toFixed(0)
                                      : typeof result.ela_analysis.ela_score === "number"
                                      ? result.ela_analysis.ela_score.toFixed(0)
                                      : "0"
                                  ) : "0"}%
                                </span>
                                <span className="text-xs text-text-secondary">discrepancy</span>
                              </div>
                            </div>

                            <div className="space-y-3 font-semibold text-xs text-text-primary">
                              <div className="flex justify-between py-1 border-b border-border/20">
                                <span className="text-text-secondary">Tampering Flagged</span>
                                <span className={
                                  result.ela_analysis?.tampering_detected || 
                                  (Array.isArray(result.ela_analysis?.suspicious_pages) && result.ela_analysis.suspicious_pages.length > 0) ||
                                  ((result.ela_analysis?.ela_score ?? 0) > 0)
                                    ? "text-risk-critical" 
                                    : "text-risk-safe"
                                }>
                                  {result.ela_analysis?.tampering_detected || 
                                  (Array.isArray(result.ela_analysis?.suspicious_pages) && result.ela_analysis.suspicious_pages.length > 0) ||
                                  ((result.ela_analysis?.ela_score ?? 0) > 0)
                                    ? "TAMPERING SIGNATURE FOUND" 
                                    : "CLEAN STRUCTURE"}
                                </span>
                              </div>
                              <div className="flex justify-between py-1">
                                <span className="text-text-secondary">Font Discrepancy Signature</span>
                                <span>
                                  {result.layout_analysis?.font_discrepancies && result.layout_analysis.font_discrepancies.length > 0
                                    ? result.layout_analysis.font_discrepancies.join(", ")
                                    : result.layout_analysis?.layout_warnings && result.layout_analysis.layout_warnings.length > 0
                                    ? result.layout_analysis.layout_warnings.join(", ")
                                    : "Standard Fonts / Layout"}
                                </span>
                              </div>
                            </div>
                          </div>

                          <div className="rounded-xl border border-border/50 bg-bg-base/30 p-4.5 flex flex-col justify-center text-xs leading-relaxed text-text-secondary font-semibold">
                            <span className="font-bold text-text-primary mb-2 flex items-center gap-1">
                              <Info className="h-4 w-4" /> Understanding ELA
                            </span>
                            Error Level Analysis (ELA) resaves the image at a known compression rate (e.g. 95%) and computes the pixel discrepancy difference. High contrast outlines or mismatching textures highlight areas inserted or graphical overrides added using Photoshop.
                          </div>
                        </div>
                      </GlassCard>
                    </motion.div>
                  )}

                  {activeTab === "ai_report" && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="space-y-4"
                    >
                      {isAnalyzingAI ? (
                        <div className="min-h-[250px] flex flex-col items-center justify-center text-center p-8 bg-surface/10 rounded-2xl border border-border/40">
                          <div className="h-10 w-10 rounded-full border-4 border-slate-100 border-t-accent-blue animate-spin mb-4" />
                          <h4 className="text-xs font-bold text-text-primary uppercase tracking-widest flex items-center gap-1.5 mb-2 justify-center">
                            <Sparkles className="h-4 w-4 animate-pulse text-accent-blue" /> Consulting AI Forensics Engine
                          </h4>
                          <p className="text-xs text-text-secondary max-w-sm leading-relaxed font-semibold">
                            Lumint LLM parser is analyzing layout geometries, looking for hidden document modifications, and assembling the analyst brief...
                          </p>
                        </div>
                      ) : aiResult ? (
                        <GlassCard className="p-6 space-y-6">
                          {/* Top Verdict Panel */}
                          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border/20 pb-5">
                            <div className="space-y-1.5">
                              <div className="text-[10px] font-bold text-text-secondary uppercase tracking-widest flex items-center gap-1 font-semibold">
                                <Brain className="h-3.5 w-3.5 text-accent-blue" /> Lumint AI Audit Verdict
                              </div>
                              <h3 className="text-lg font-bold text-text-primary flex items-center gap-2">
                                {aiResult.verdict === "GENUINE" ? (
                                  <span className="text-risk-safe">Genuine Structure Verified</span>
                                ) : aiResult.verdict === "SUSPICIOUS" ? (
                                  <span className="text-risk-medium">Suspicious Alterations Detected</span>
                                ) : (
                                  <span className="text-risk-critical">Fraudulent Modification Signature</span>
                                )}
                              </h3>
                            </div>
                            <div className="flex items-center gap-4">
                              <div className="text-right">
                                <div className="text-[10px] font-bold text-text-secondary uppercase">Confidence Score</div>
                                <div className="text-sm font-bold font-mono text-text-primary">{aiResult.confidence}%</div>
                              </div>
                              <span className={`h-8 px-3 rounded-lg flex items-center justify-center text-xs font-bold ${
                                aiResult.verdict === "GENUINE" 
                                  ? "bg-risk-safe/10 text-risk-safe border border-risk-safe/25" 
                                  : aiResult.verdict === "SUSPICIOUS"
                                  ? "bg-risk-medium/10 text-risk-medium border border-risk-medium/25"
                                  : "bg-risk-critical/10 text-risk-critical border border-risk-critical/25"
                              }`}>
                                {aiResult.verdict}
                              </span>
                            </div>
                          </div>

                          {/* Analysis Breakdown */}
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="space-y-4">
                              <div>
                                <h4 className="text-xs font-bold text-text-secondary uppercase tracking-widest mb-2 flex items-center gap-1.5">
                                  <ShieldAlert className="h-3.5 w-3.5 text-risk-high" /> Detected Threat Vectors & Anomalies
                                </h4>
                                <ul className="space-y-1.5">
                                  {aiResult.anomalies.map((anomaly, idx) => (
                                    <li key={idx} className="text-xs text-text-primary font-semibold flex items-start gap-2">
                                      <span className="h-1.5 w-1.5 rounded-full bg-risk-critical mt-1.5 shrink-0" />
                                      <span>{anomaly}</span>
                                    </li>
                                  ))}
                                  {aiResult.anomalies.length === 0 && (
                                    <li className="text-xs text-text-secondary italic font-semibold">No core structural anomalies found.</li>
                                  )}
                                </ul>
                              </div>

                              <div className="pt-2">
                                <div className="text-[10px] font-bold text-text-secondary uppercase mb-1">Inferred Attack Type</div>
                                <div className="text-xs font-bold text-text-primary bg-bg-base px-3 py-2 rounded-xl border border-border/40 inline-block">
                                  {aiResult.attack_type || "None Identified"}
                                </div>
                              </div>
                            </div>

                            <div className="space-y-4 md:border-l md:border-border/30 md:pl-6">
                              <div>
                                <h4 className="text-xs font-bold text-text-secondary uppercase tracking-widest mb-2">
                                  AI Analyst Brief
                                </h4>
                                <p className="text-xs text-text-secondary leading-relaxed font-semibold">
                                  {aiResult.analyst_note}
                                </p>
                              </div>

                              <div className="p-4 rounded-xl bg-bg-base/40 border border-border/50 space-y-1.5">
                                <div className="text-[10px] font-bold text-text-secondary uppercase">Recommended Action</div>
                                <p className="text-xs font-bold text-text-primary leading-normal">
                                  {aiResult.recommended_action}
                                </p>
                              </div>
                            </div>
                          </div>

                          {/* Footer Engine Details */}
                          <div className="flex items-center justify-between border-t border-border/20 pt-4 text-[10px] font-semibold text-text-secondary">
                            <div className="flex items-center gap-1.5">
                              <Cpu className="h-3 w-3 text-accent-blue" />
                              <span>Model: <span className="font-mono text-text-primary">{aiResult.model_used}</span></span>
                            </div>
                            {aiResult.latency_ms > 0 && (
                              <div>
                                Latency: <span className="font-mono text-text-primary">{aiResult.latency_ms}ms</span>
                              </div>
                            )}
                          </div>
                        </GlassCard>
                      ) : (
                        <div className="min-h-[250px] flex flex-col items-center justify-center text-center p-8 bg-surface/10 rounded-2xl border border-border/40">
                          <Brain className="h-8 w-8 text-text-secondary/60 mb-3" />
                          <p className="text-xs text-text-secondary font-semibold">AI report is only available after a forensic scan runs.</p>
                        </div>
                      )}
                    </motion.div>
                  )}
                </div>
              </motion.div>
            ) : (
              <motion.div
                key="empty-box"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="h-full min-h-[400px] flex flex-col items-center justify-center text-center p-8 bg-surface/30 border border-border/40 border-dashed rounded-3xl"
              >
                <div className="h-12 w-12 rounded-full border border-border flex items-center justify-center bg-bg-base text-text-secondary shadow-sm mb-4">
                  <FileText className="h-5 w-5" />
                </div>
                <h3 className="text-sm font-bold text-text-primary">Awaiting Forensic Scan</h3>
                <p className="text-xs text-text-secondary mt-1.5 max-w-xs font-semibold">
                  Upload an invoice, passport scan, identity document, or PDF file to run full layout, ELA, and metadata rule checks.
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
