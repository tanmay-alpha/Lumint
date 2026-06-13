"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { UploadZone } from "@/components/ui/UploadZone";
import { documentApi } from "@/lib/api/documents";
import { DocumentAnalysisResult } from "@/lib/types";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { RiskScore } from "@/components/ui/RiskScore";
import { DataPoint } from "@/components/ui/DataPoint";
import { AIInsightCard } from "@/components/ui/AIInsightCard";
import { SkeletonLoader } from "@/components/ui/SkeletonLoader";
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
  ShieldAlert,
  Shield,
  Scan,
  Check,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import aiApi from "@/lib/api/ai";
import { DocumentAIResult } from "@/lib/types";

type TabID = "metadata" | "indicators" | "explanation" | "tampering" | "ai_report";

export default function DocShieldPage() {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [progressIdx, setProgressIdx] = useState(0);

  useEffect(() => {
    if (!isAnalyzing) { setProgressIdx(0); return; }
    const stages = [
      { title: "Parsing File Signatures", desc: "Extracting document stream layers, computing file hashes, and running forensic pattern scanners..." },
      { title: "Running Metadata & EXIF Scan", desc: "Checking author stamps, software fingerprints, and XMP inconsistencies..." },
      { title: "Error-Level Analysis (ELA)", desc: "Recompressing pixels to expose tampered regions at JPEG block boundaries..." },
      { title: "Layout & Text Geometry", desc: "Verifying baseline alignment, font consistency, and whitespace distribution..." },
      { title: "Compiling Forensic Report", desc: "Aggregating all evidence into a final risk verdict..." },
    ];
    setProgressIdx(0);
    const id = setInterval(() => {
      setProgressIdx((i) => (i + 1) % stages.length);
    }, 1400);
    return () => clearInterval(id);
  }, [isAnalyzing]);
  const [result, setResult] = useState<DocumentAnalysisResult | null>(null);
  const [activeTab, setActiveTab] = useState<TabID>("metadata");

  const [isAnalyzingAI, setIsAnalyzingAI] = useState(false);
  const [aiResult, setAiResult] = useState<DocumentAIResult | null>(null);
  const [error, setError] = useState<{ message: string; status?: number } | null>(null);

  const handleFileAccepted = async (acceptedFile: File) => {
    if (acceptedFile.size > 10 * 1024 * 1024) {
      setError({ message: "File too large. Please use an image under 10MB." });
      return;
    }
    if (!acceptedFile.type.startsWith("image/") && acceptedFile.type !== "application/pdf") {
      setError({ message: "Please upload an image or PDF file." });
      return;
    }
    setIsAnalyzing(true);
    setResult(null);
    setAiResult(null);
    setError(null);

    try {
      const response = await documentApi.analyzeDocument(acceptedFile);
      if (!response) {
        // Soft-fail path: backend not configured or unreachable. Show
        // friendly demo-mode message instead of a stack trace.
        setError({
          message: "DocShield requires a backend connection. This is a demo deployment — only UPI Shield is fully functional.",
        });
        return;
      }
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
    } catch (err: any) {
      console.error("Document analysis failed:", err);
      setError({
        message: err?.message || "DocShield analysis failed",
        status: err?.status,
      });
    } finally {
      setIsAnalyzing(false);
    }
  };

  const getRiskVariant = (level: string): any => {
    switch (level) {
      case "CRITICAL":
        return "critical";
      case "HIGH":
        return "high";
      case "SUSPICIOUS":
        return "warn";
      case "LOW":
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
    <div className="space-y-8 font-sans">
      {/* Page Header */}
      <div className="space-y-1">
        <div className="flex items-center gap-2.5">
          <div className="h-9 w-9 rounded-xl bg-[var(--brand-muted)] flex items-center justify-center shadow-sm">
            <Shield className="h-5 w-5 text-[var(--brand)]" />
          </div>
          <div>
            <h1 className="text-[20px] font-bold text-[var(--text-1)]">
              DocShield Document Forensics
            </h1>
            <p className="text-[12px] text-[var(--text-3)]">
              Analyze PDF and image document structures for spoofed creator tags, structural edits, and ELA tampering
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* LEFT COLUMN — Upload & Works guide */}
        <div className="lg:col-span-1 space-y-4">
          <Card className="p-5">
            <span className="text-[11px] font-semibold text-[var(--text-3)] uppercase tracking-wider block mb-4">
              Select Forensic Entity
            </span>
            <UploadZone
              accept=".pdf,.png,.jpg,.jpeg"
              maxSizeMB={10}
              label="Drop document file here"
              subLabel="PDF · PNG · JPG (Max 10MB)"
              onFileAccepted={handleFileAccepted}
              isLoading={isAnalyzing}
            />

            <div className="mt-4 border-t border-[var(--border)]/40 pt-4 text-[12px] text-[var(--text-3)] leading-relaxed font-semibold">
              <div className="flex items-start gap-2">
                <Info className="h-4 w-4 text-[var(--brand)] shrink-0 mt-0.5" />
                <span>Uploaded entities are verified in a secure sandbox. Metadata structures are hashed instantly.</span>
              </div>
            </div>
          </Card>

          {/* How DocShield Works list - collapses once result is loaded */}
          {!result && (
            <Card className="p-5">
              <span className="text-[11px] font-semibold text-[var(--text-3)] uppercase tracking-wider block mb-4">
                How DocShield works
              </span>
              <div className="relative pl-8 space-y-6">
                <div className="absolute left-[9px] top-2 bottom-2 w-[1.5px] bg-[var(--border)]" />
                {[
                  { icon: <Scan className="h-3.5 w-3.5 text-white" />, label: "Magic-byte verification", desc: "Verifies structural header authenticity to prevent spoofing" },
                  { icon: <Layers className="h-3.5 w-3.5 text-white" />, label: "Image tampering (ELA)", desc: "Error Level Analysis pinpoints graphic modification regions" },
                  { icon: <Calendar className="h-3.5 w-3.5 text-white" />, label: "Metadata audit", desc: "Analyzes creator timestamps, editor signatures, and versions" },
                  { icon: <Sparkles className="h-3.5 w-3.5 text-white" />, label: "AI synthesis", desc: "Collates deep evidence into a final threat brief via LLaMA" },
                ].map(({ icon, label, desc }, idx) => (
                  <div key={idx} className="relative flex items-start gap-4">
                    <div className="absolute -left-[32px] h-5 w-5 rounded-full bg-[var(--brand)] flex items-center justify-center z-10 shadow-sm">
                      {icon}
                    </div>
                    <div>
                      <span className="text-[13px] font-semibold text-[var(--text-1)] block leading-tight">{label}</span>
                      <p className="text-[12px] text-[var(--text-3)] leading-relaxed mt-1">{desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>

        {/* RIGHT COLUMN — Results & Analysis */}
        <div className="lg:col-span-2">
          {error && !isAnalyzing && !result && (
            <div
              role="alert"
              aria-live="assertive"
              className="mb-4 rounded-lg border border-[var(--warn-border)]/30 bg-[var(--warn-bg)] p-5"
            >
              <div className="flex items-start gap-3">
                <Info className="h-5 w-5 text-[var(--warn)] shrink-0 mt-0.5" />
                <div className="flex-1 space-y-1.5">
                  <h3 className="text-[14px] font-bold text-[var(--warn)]">DocShield is a demo module</h3>
                  <p className="text-[12px] text-[var(--text-1)] font-semibold leading-relaxed">
                    {error.message}
                  </p>
                  <p className="text-[11px] text-[var(--text-3)] font-semibold leading-relaxed pt-1">
                    The full DocShield analysis pipeline is currently unavailable in this deployment.
                    Try the fully-functional UPI Shield instead, which runs 100% in your browser.
                  </p>
                  <Link
                    href="/upi-shield"
                    className="inline-block mt-3 text-[11px] font-semibold text-[var(--brand)] hover:underline"
                  >
                    Try UPI Shield →
                  </Link>
                </div>
              </div>
            </div>
          )}
          <AnimatePresence mode="wait">
            {isAnalyzing ? (
              <motion.div
                key="loading-box"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              >
                <Card className="p-8 flex flex-col items-center justify-center text-center min-h-[400px]">
                  <div className="relative flex items-center justify-center mb-6">
                    <div className="h-16 w-16 rounded-full border-4 border-[var(--surface-3)] border-t-[var(--brand)] animate-spin" />
                    <FileText className="absolute h-6 w-6 text-[var(--brand)] animate-pulse" />
                  </div>
                  <h3 className="text-[15px] font-bold text-[var(--text-1)]">{[
                    "Parsing File Signatures",
                    "Running Metadata & EXIF Scan",
                    "Error-Level Analysis (ELA)",
                    "Layout & Text Geometry",
                    "Compiling Forensic Report",
                  ][progressIdx]}</h3>
                  <p className="text-[12px] text-[var(--text-3)] mt-1.5 max-w-sm font-semibold">
                    {[
                      "Extracting document stream layers, computing file hashes, and running forensic pattern scanners...",
                      "Checking author stamps, software fingerprints, and XMP inconsistencies...",
                      "Recompressing pixels to expose tampered regions at JPEG block boundaries...",
                      "Verifying baseline alignment, font consistency, and whitespace distribution...",
                      "Aggregating all evidence into a final risk verdict...",
                    ][progressIdx]}
                  </p>
                </Card>
              </motion.div>
            ) : !result ? (
              <motion.div
                key="empty-box"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="space-y-4"
              >
                <Card className="p-6 min-h-[300px] flex flex-col items-center justify-center text-center">
                  <div className="h-14 w-14 rounded-2xl bg-[var(--surface-3)] border border-[var(--border)]/40 flex items-center justify-center mb-4">
                    <FileText className="h-6 w-6 text-[var(--text-3)]" />
                  </div>
                  <h3 className="text-[14px] font-bold text-[var(--text-1)]">Awaiting Forensic Scan</h3>
                  <p className="text-[12px] text-[var(--text-3)] mt-1.5 max-w-sm leading-relaxed font-semibold">
                    Upload an invoice, passport scan, identity document, or PDF file to run full layout, ELA, and metadata rule checks.
                  </p>
                </Card>
                <div className="grid grid-cols-3 gap-3">
                  {[
                    { label: "Magic-byte", desc: "Header integrity" },
                    { label: "ELA", desc: "Pixel tampering" },
                    { label: "Metadata", desc: "Author & version" },
                  ].map((step) => (
                    <div key={step.label} className="rounded-xl border border-[var(--border)]/40 bg-[var(--surface-1)] p-3">
                      <div className="text-[10px] font-mono font-bold text-[var(--brand)] uppercase">{step.label}</div>
                      <div className="text-[11px] text-[var(--text-3)] mt-0.5 font-semibold">{step.desc}</div>
                    </div>
                  ))}
                </div>
              </motion.div>
            ) : result ? (
              <div
                aria-live="polite"
                aria-atomic="true"
                role="region"
                aria-label="DocShield analysis result"
              >
              <motion.div
                key="results-box"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="space-y-6"
              >
                {/* Result Hero Header */}
                <Card className="p-6">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6">
                    <div className="flex items-start gap-4">
                      <div className="h-12 w-12 rounded-xl bg-[var(--brand-muted)] border border-[var(--brand-border)]/20 text-[var(--brand)] flex items-center justify-center shrink-0">
                        <FileCheck className="h-6 w-6" />
                      </div>
                      <div>
                        <span className="text-[10px] font-mono font-bold text-[var(--text-3)] bg-[var(--surface-2)] border border-[var(--border)]/40 px-2 py-0.5 rounded uppercase">
                          UUID: {result.doc_id.slice(0, 8)}
                        </span>
                        <h3 className="text-[15px] font-bold text-[var(--text-1)] mt-1.5 break-all pr-2">
                          {result.original_filename}
                        </h3>
                        <div className="flex flex-wrap items-center gap-3 mt-1.5 text-[11px] text-[var(--text-3)] font-semibold">
                          <span>{(result.file_size / 1024).toFixed(1)} KB</span>
                          <span className="h-1.5 w-1.5 rounded-full bg-[var(--border)]" />
                          <span>{result.content_type}</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-4 shrink-0 sm:border-l sm:border-[var(--border)]/40 sm:pl-6">
                      <div className="flex flex-col items-end gap-1">
                        <span className="text-[10px] font-bold text-[var(--text-3)] uppercase">
                          Platform Verdict
                        </span>
                        <Badge variant={getRiskVariant(result.risk_level ?? "NONE")} dot className="text-xs px-2.5 py-0.5 uppercase font-semibold">
                          {result.risk_level}
                        </Badge>
                      </div>
                      <RiskScore score={result.risk_score ?? 0} size="sm" />
                    </div>
                  </div>
                </Card>

                {/* Tab Menu */}
                <div className="flex border-b border-[var(--border)]/40 gap-1 overflow-x-auto">
                  {tabs.map((tab) => {
                    const isActive = activeTab === tab.id;
                    return (
                      <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`px-4 py-2.5 text-[12px] font-bold border-b-2 transition-all shrink-0 ${
                          isActive
                            ? "border-[var(--brand)] text-[var(--brand)]"
                            : "border-transparent text-[var(--text-3)] hover:text-[var(--text-1)]"
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
                      <Card className="p-5 space-y-4">
                        <h4 className="text-[11px] font-bold text-[var(--text-3)] uppercase tracking-widest flex items-center gap-1.5">
                          <Layers className="h-3.5 w-3.5 text-[var(--brand)]" /> File Identity
                        </h4>

                        <div className="space-y-3 font-semibold text-[12px] text-[var(--text-1)]">
                          <div className="flex justify-between py-1 border-b border-[var(--border)]/20">
                            <span className="text-[var(--text-3)]">Original Name</span>
                            <span className="font-mono">{result.original_filename}</span>
                          </div>
                          <div className="flex justify-between py-1 border-b border-[var(--border)]/20">
                            <span className="text-[var(--text-3)]">Stored Name</span>
                            <span className="font-mono">{result.saved_filename}</span>
                          </div>
                          <div className="flex justify-between py-1 border-b border-[var(--border)]/20">
                            <span className="text-[var(--text-3)]">File Path</span>
                            <span className="font-mono text-right max-w-[200px] truncate select-all">{result.file_path}</span>
                          </div>
                          <div className="flex justify-between py-1">
                            <span className="text-[var(--text-3)]">Content Type</span>
                            <span className="font-mono">{result.content_type}</span>
                          </div>
                        </div>
                      </Card>

                      <Card className="p-5 space-y-4">
                        <h4 className="text-[11px] font-bold text-[var(--text-3)] uppercase tracking-widest flex items-center gap-1.5">
                          <Calendar className="h-3.5 w-3.5 text-[var(--intel)]" /> Document Metadata
                        </h4>

                        {result.metadata ? (
                          <div className="space-y-3 font-semibold text-[12px] text-[var(--text-1)]">
                            <div className="flex justify-between py-1 border-b border-[var(--border)]/20">
                              <span className="text-[var(--text-3)]">Author Creator</span>
                              <span>{result.metadata.creator || "Unknown"}</span>
                            </div>
                            <div className="flex justify-between py-1 border-b border-[var(--border)]/20">
                              <span className="text-[var(--text-3)]">Editor Signature</span>
                              <span>{result.metadata.producer || "Unknown"}</span>
                            </div>
                            <div className="flex justify-between py-1 border-b border-[var(--border)]/20">
                              <span className="text-[var(--text-3)]">Created Date</span>
                              <span className="font-mono text-[11px] text-[var(--text-2)]">
                                {result.metadata.creation_date ? new Date(result.metadata.creation_date).toLocaleString() : "Unknown"}
                              </span>
                            </div>
                            <div className="flex justify-between py-1">
                              <span className="text-[var(--text-3)]">Modified Date</span>
                              <span className="font-mono text-[11px] text-[var(--text-2)]">
                                {result.metadata.modification_date ? new Date(result.metadata.modification_date).toLocaleString() : "Unknown"}
                              </span>
                            </div>
                          </div>
                        ) : (
                          <div className="text-[12px] text-[var(--text-3)] italic">No nested document metadata available.</div>
                        )}
                      </Card>
                    </motion.div>
                  )}

                  {activeTab === "indicators" && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="space-y-4"
                    >
                      <Card className="p-5">
                        <h4 className="text-[11px] font-bold text-[var(--text-3)] uppercase tracking-widest flex items-center gap-1.5 mb-4">
                          <AlertTriangle className="h-3.5 w-3.5 text-[var(--warn)]" /> Checked Forensic Policy Rules
                        </h4>

                        <div className="space-y-3.5">
                          {result.indicators && result.indicators.length > 0 ? (
                            result.indicators.map((indicator, idx) => (
                              <div
                                key={idx}
                                className="flex items-start gap-4 p-3 rounded-xl bg-[var(--surface)] border border-[var(--border)]/40"
                              >
                                <span className="h-6 w-6 rounded-lg bg-[var(--high-bg)] text-[var(--high)] flex items-center justify-center font-mono font-bold text-xs shrink-0 mt-0.5">
                                  {indicator.score}
                                </span>
                                <div className="space-y-1">
                                  <div className="text-[12px] font-bold text-[var(--text-1)]">{indicator.rule}</div>
                                  <div className="text-[12px] text-[var(--text-3)] leading-normal font-semibold">{indicator.detail}</div>
                                </div>
                              </div>
                            ))
                          ) : (
                            <div className="text-[12px] text-[var(--text-3)] italic">No forensic anomalies triggered. Document appears standard.</div>
                          )}
                        </div>
                      </Card>
                    </motion.div>
                  )}

                  {activeTab === "explanation" && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="space-y-4"
                    >
                      <Card className="p-5">
                        <h4 className="text-[11px] font-bold text-[var(--text-3)] uppercase tracking-widest flex items-center gap-1.5 mb-4">
                          <Terminal className="h-3.5 w-3.5 text-[var(--brand)]" /> Chain of Forensic Reasoning
                        </h4>

                        <div className="space-y-4 font-semibold text-[12px] leading-relaxed text-[var(--text-3)]">
                          {result.explanation && result.explanation.length > 0 ? (
                            result.explanation.map((step, idx) => (
                              <div key={idx} className="flex gap-3">
                                <span className="h-5 w-5 shrink-0 rounded-full border border-[var(--border)] flex items-center justify-center font-mono text-[10px] text-[var(--text-1)] bg-[var(--surface-3)] font-bold">
                                  {idx + 1}
                                </span>
                                <p className="pt-0.5">{step}</p>
                              </div>
                            ))
                          ) : (
                            <p className="italic">No forensic anomalies were flagged. The file matching signatures align with common standards.</p>
                          )}
                        </div>
                      </Card>
                    </motion.div>
                  )}

                  {activeTab === "tampering" && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="space-y-4"
                    >
                      <Card className="p-5">
                        <h4 className="text-[11px] font-bold text-[var(--text-3)] uppercase tracking-widest flex items-center gap-1.5 mb-4">
                          <Layers className="h-3.5 w-3.5 text-[var(--brand)]" /> Error Level Analysis (ELA) Breakdown
                        </h4>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                          <div className="space-y-4.5">
                            <div className="p-4.5 rounded-xl border border-[var(--border)]/50 bg-[var(--surface-3)]">
                              <div className="text-[10px] font-bold text-[var(--text-3)] uppercase mb-1">
                                ELA Discrepancy Margin
                              </div>
                              <div className="flex items-baseline gap-2 font-mono">
                                <span className="text-2xl font-bold text-[var(--text-1)]">
                                  {result.ela_analysis ? (
                                    typeof result.ela_analysis.ela_discrepancy_score === "number"
                                      ? (result.ela_analysis.ela_discrepancy_score * 100).toFixed(0)
                                      : typeof result.ela_analysis.ela_score === "number"
                                      ? result.ela_analysis.ela_score.toFixed(0)
                                      : "0"
                                  ) : "0"}%
                                </span>
                                <span className="text-xs text-[var(--text-3)]">discrepancy</span>
                              </div>
                            </div>

                            <div className="space-y-3 font-semibold text-[12px] text-[var(--text-1)] mt-4">
                              <div className="flex justify-between py-1 border-b border-[var(--border)]/20">
                                <span className="text-[var(--text-3)]">Tampering Flagged</span>
                                <span className={
                                  result.ela_analysis?.tampering_detected || 
                                  (Array.isArray(result.ela_analysis?.suspicious_pages) && result.ela_analysis.suspicious_pages.length > 0) ||
                                  ((result.ela_analysis?.ela_score ?? 0) > 0)
                                    ? "text-[var(--high)] font-bold" 
                                    : "text-[var(--safe)] font-bold"
                                }>
                                  {result.ela_analysis?.tampering_detected || 
                                  (Array.isArray(result.ela_analysis?.suspicious_pages) && result.ela_analysis.suspicious_pages.length > 0) ||
                                  ((result.ela_analysis?.ela_score ?? 0) > 0)
                                    ? "TAMPERING SIGNATURE FOUND" 
                                    : "CLEAN STRUCTURE"}
                                </span>
                              </div>
                              <div className="flex justify-between py-1">
                                <span className="text-[var(--text-3)]">Font Discrepancy Signature</span>
                                <span className="font-semibold text-right max-w-[220px] truncate">
                                  {result.layout_analysis?.font_discrepancies && result.layout_analysis.font_discrepancies.length > 0
                                    ? result.layout_analysis.font_discrepancies.join(", ")
                                    : result.layout_analysis?.layout_warnings && result.layout_analysis.layout_warnings.length > 0
                                    ? result.layout_analysis.layout_warnings.join(", ")
                                    : "Standard Fonts / Layout"}
                                </span>
                              </div>
                            </div>
                          </div>

                          <div className="rounded-xl border border-[var(--border)]/50 bg-[var(--surface-2)] p-4 flex flex-col justify-center text-[12px] leading-relaxed text-[var(--text-3)] font-semibold">
                            <span className="font-bold text-[var(--text-1)] mb-2 flex items-center gap-1.5">
                              <Info className="h-4 w-4 text-[var(--brand)]" /> Understanding ELA
                            </span>
                            Error Level Analysis (ELA) resaves the image at a known compression rate (e.g. 95%) and computes the pixel discrepancy difference. High contrast outlines or mismatching textures highlight areas inserted or graphical overrides added using Photoshop.
                          </div>
                        </div>
                      </Card>
                    </motion.div>
                  )}

                  {activeTab === "ai_report" && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="space-y-4"
                    >
                      {isAnalyzingAI ? (
                        <Card className="p-8 flex flex-col items-center justify-center text-center min-h-[250px]">
                          <div className="h-10 w-10 rounded-full border-4 border-[var(--surface-3)] border-t-[var(--brand)] animate-spin mb-4" />
                          <h4 className="text-[11px] font-bold text-[var(--text-1)] uppercase tracking-widest flex items-center gap-1.5 mb-2 justify-center">
                            <Sparkles className="h-4 w-4 animate-pulse text-[var(--brand)]" /> Consulting AI Forensics Engine
                          </h4>
                          <p className="text-[12px] text-[var(--text-3)] max-w-sm leading-relaxed font-semibold">
                            Lumint LLM parser is analyzing layout geometries, looking for hidden document modifications, and assembling the analyst brief...
                          </p>
                        </Card>
                      ) : aiResult ? (
                        <AIInsightCard
                          isLoading={false}
                          title="DOCUMENT FORENSIC INSIGHT"
                          timestamp={new Date().toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" })}
                          modelInfo={`${aiResult.model_used} · ${aiResult.latency_ms}ms`}
                          className="border-2 border-dashed border-[var(--ai-border)] bg-[var(--ai-muted)]"
                        >
                          <div className="space-y-5 text-body text-[var(--text-1)]">
                            <div className="flex items-center gap-4 flex-wrap pb-4 border-b border-[var(--ai-border)]/30">
                              <div className="flex flex-col">
                                <span className="text-[10px] text-[var(--text-3)] font-semibold uppercase">Verdict</span>
                                <span className={`font-mono text-[16px] font-bold mt-0.5 uppercase ${
                                  aiResult.verdict === "FRAUDULENT"
                                    ? "text-[var(--high)]"
                                    : aiResult.verdict === "SUSPICIOUS"
                                    ? "text-[var(--warn)]"
                                    : "text-[var(--safe)]"
                                }`}>
                                  {aiResult.verdict}
                                </span>
                              </div>
                              <div className="flex flex-col">
                                <span className="text-[10px] text-[var(--text-3)] font-semibold uppercase">Confidence</span>
                                <div className="mt-0.5">
                                  <Badge variant={aiResult.confidence > 80 ? "safe" : aiResult.confidence > 60 ? "warn" : "high"} className="text-xs px-2.5 py-0.5">
                                    {aiResult.confidence}%
                                  </Badge>
                                </div>
                              </div>
                              {aiResult.attack_type && (
                                <div className="flex flex-col">
                                  <span className="text-[10px] text-[var(--text-3)] font-semibold uppercase">Attack Type</span>
                                  <span className="font-mono text-[11px] text-[var(--text-2)] bg-[var(--surface)] border border-[var(--border)] px-2 py-0.5 rounded-md mt-0.5">
                                    {aiResult.attack_type}
                                  </span>
                                </div>
                              )}
                            </div>

                            {/* Anomalies list */}
                            <div>
                              <span className="text-[11px] font-semibold text-[var(--text-3)] uppercase tracking-wider block mb-2">
                                Detected Threat Vectors & Anomalies
                              </span>
                              <ul className="space-y-2">
                                {aiResult.anomalies.map((pt, i) => (
                                  <li key={i} className="flex items-start gap-2 text-[12px] text-[var(--text-2)] leading-relaxed font-semibold">
                                    <span className="font-mono text-[10px] text-[var(--brand)] mt-0.5 shrink-0 font-bold">{i + 1}.</span>
                                    {pt}
                                  </li>
                                ))}
                                {aiResult.anomalies.length === 0 && (
                                  <li className="text-[12px] text-[var(--text-3)] italic font-semibold">No core structural anomalies found.</li>
                                )}
                              </ul>
                            </div>

                            {/* Analyst note */}
                            <div className="border-l-2 border-[var(--ai-border)] pl-4 bg-[var(--surface)]/50 py-2.5 pr-2 rounded-r-lg">
                              <p className="text-[13px] italic font-serif text-[var(--text-2)] leading-relaxed">
                                &ldquo;{aiResult.analyst_note}&rdquo;
                              </p>
                            </div>

                            {/* Recommended action */}
                            <div className="rounded-xl bg-[var(--warn-bg)] border border-[var(--warn-border)]/30 px-4 py-3">
                              <span className="text-[11px] font-semibold text-[var(--warn)] uppercase tracking-wider block mb-1">
                                Recommended action
                              </span>
                              <p className="text-[13px] font-semibold text-[var(--text-1)]">
                                {aiResult.recommended_action}
                              </p>
                            </div>
                          </div>
                        </AIInsightCard>
                      ) : (
                        <Card className="p-8 flex flex-col items-center justify-center text-center min-h-[250px]">
                          <Brain className="h-8 w-8 text-[var(--text-3)]/60 mb-3" />
                          <p className="text-[12px] text-[var(--text-3)] font-semibold">AI report is only available after a forensic scan runs.</p>
                        </Card>
                      )}
                    </motion.div>
                  )}
                </div>
              </motion.div>
              </div>
            ) : (
              <motion.div
                key="empty-box"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
              >
                <Card variant="default" className="flex flex-col items-center justify-center h-[400px] border-dashed text-center p-8">
                  <div className="h-12 w-12 rounded-xl bg-[var(--surface-3)] border border-[var(--border)] flex items-center justify-center text-[var(--text-3)] mb-4">
                    <FileText className="h-6 w-6" />
                  </div>
                  <h3 className="text-[15px] font-bold text-[var(--text-1)]">Awaiting Forensic Scan</h3>
                  <p className="text-[12px] text-[var(--text-3)] mt-1.5 max-w-xs leading-normal">
                    Upload an invoice, passport scan, identity document, or PDF file to run full layout, ELA, and metadata rule checks.
                  </p>
                </Card>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
