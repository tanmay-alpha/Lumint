"use client";

import React, { useState } from "react";
import { useReducedMotion } from "framer-motion";
import type { Variants } from "framer-motion";
import { analyzeUPIClientSide } from "@/lib/upi-client-analyzer";
import { saveScan } from "@/lib/scan-history";
import type { UPIAnalysisResult } from "@/types";
import { HeroPanel } from "./_components/HeroPanel";
import { UploaderPanel } from "./_components/UploaderPanel";
import { ResultsPanel } from "./_components/ResultsPanel";

// ─── Stagger animation variants ────────────────────────────────────────────
const container: Variants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.08 } },
};
const item: Variants = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: [0, 0, 0.3, 1] } },
};

// No-op variants for users who prefer reduced motion: skips the stagger
// orchestration so children render in their resting state with no animation.
const reducedVariants: Variants = {};

export default function UPIShieldPage() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<UPIAnalysisResult | null>(null);

  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const reduced = useReducedMotion();
  const containerVariants = reduced ? reducedVariants : container;
  const itemVariants = reduced ? reducedVariants : item;

  const handleShare = () => {
    if (!result) return;
    const summary = `Lumint ${result.ai_fraud_explanation || result.risk_level}\nScore: ${result.risk_score}/100\nRisk: ${result.risk_level}`;
    navigator.clipboard.writeText(summary).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }).catch(() => {
      // Fallback for non-secure contexts
      const ta = document.createElement("textarea");
      ta.value = summary;
      document.body.appendChild(ta);
      ta.select();
      try { document.execCommand("copy"); setCopied(true); setTimeout(() => setCopied(false), 2000); } catch {}
      document.body.removeChild(ta);
    });
  };

  const handleFileSelected = (f: File) => {
    if (f.size > 10 * 1024 * 1024) {
      setError("File too large. Please use an image under 10MB.");
      return;
    }
    if (!f.type.startsWith("image/")) {
      setError("Please upload an image file (PNG or JPEG).");
      return;
    }
    setFile(f);
    setResult(null);
    setError(null);
  };

  // Load a sample image from /public/samples and pipe it through the same
  // selection path as a real upload. Lets users try the analyzer without
  // having to find a screenshot on disk.
  const loadSampleImage = async (path: string) => {
    try {
      const res = await fetch(path);
      const blob = await res.blob();
      const name = path.split("/").pop() || "sample.png";
      const file = new File([blob], name, { type: blob.type || "image/png" });
      handleFileSelected(file);
    } catch (e) {
      console.error("Failed to load sample:", e);
    }
  };

  const handleAnalyze = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);
    setResult(null);

    let p = 0;
    const tick = setInterval(() => {
      p = Math.min(p + 10, 90);
      setProgress(p);
    }, 200);

    try {
      // Client-side analyzer: Tesseract.js OCR + Canvas ELA, no backend.
      const res = await analyzeUPIClientSide(file, (ocrProgress, stage) => {
        // Real Tesseract progress: 0.0–1.0, scale to 0–100
        const scaled = Math.round(ocrProgress * 100);
        setProgress((prev) => Math.max(prev, Math.min(scaled, 95)));
        // stage is reported by the analyzer for diagnostics; the progress bar
        // already surfaces progress to the user, so we don't render a separate
        // status line. Silence the unused-parameter warning.
        void stage;
      });
      clearInterval(tick);
      setProgress(100);
      // Map the analyzer result into the page's UPIAnalysisResult shape.
      const mapped: UPIAnalysisResult = {
        ...(res as any),
        id: typeof crypto !== "undefined" && "randomUUID" in crypto ? crypto.randomUUID() : `id-${Date.now()}-${Math.floor(Math.random() * 1e9)}`,
        timestamp: new Date().toISOString(),
        event_type: "screenshot",
        utr_number: res.extracted.utr,
        utr_valid: !!res.extracted.utr,
        utr_format: res.extracted.app ? res.extracted.app.toLowerCase() : "unknown",
        sender_upi_id: null,
        receiver_upi_id: res.extracted.vpa,
        amount: res.extracted.amount,
        transaction_date: res.extracted.timestamp || new Date().toISOString(),
        is_valid_utr: !!res.extracted.utr,
        font_anomalies_detected: res.signals.some((s) => s.check.toLowerCase().includes("tampering") && !s.passed),
        suspicious_handle_flagged: false,
        risk_score: res.score,
        risk_level: res.verdict,
        ai_fraud_explanation: res.label,
        raw_ocr_text: res.ocr_text,
        metadata_json: { file_name: file.name, file_size: file.size, model_version: res.model_version },
        ela_tamper_regions: res.signals.find((s) => s.check.toLowerCase().includes("tampering"))?.detail?.match(/\d+/)?.[0]
          ? parseInt(res.signals.find((s) => s.check.toLowerCase().includes("tampering"))!.detail!.match(/\d+/)![0])
          : 0,
        font_consistent: !res.signals.some((s) => s.check.toLowerCase().includes("tampering") && !s.passed),
        color_authentic: true,
        ocr_confidence: Math.round(res.confidence * 100),
        amount_extracted: res.extracted.amount != null ? `Rs ${res.extracted.amount.toLocaleString("en-IN")}` : null,
        app_detected: res.extracted.app,
        timestamp_extracted: res.extracted.timestamp || new Date().toLocaleString("en-IN"),
        feature_contributions: res.signals.map((s) => ({
          name: s.check,
          value: s.passed ? "Pass" : "Fail",
          contribution: s.passed ? -10 : 15,
        })),
      };
      setTimeout(() => {
        setResult(mapped);
        saveScan({
          shield: 'upi',
          verdict: mapped.risk_level,
          label: mapped.ai_fraud_explanation,
          score: mapped.risk_score,
          fileName: file.name,
        });
        setProgress(0);
        setUploading(false);
      }, 200);
    } catch (e: any) {
      clearInterval(tick);
      setError(e?.message || "Analysis failed. Please retry.");
      setUploading(false);
      setProgress(0);
    }
  };

  return (
    <div className="space-y-8 font-sans">
      <HeroPanel containerVariants={containerVariants} itemVariants={itemVariants} />

      {/* Split layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <UploaderPanel
          file={file}
          uploading={uploading}
          progress={progress}
          result={!!result}
          error={error}
          onFileSelected={handleFileSelected}
          onAnalyze={handleAnalyze}
          onLoadSample={loadSampleImage}
        />

        <ResultsPanel
          result={result}
          uploading={uploading}
          copied={copied}
          containerVariants={containerVariants}
          itemVariants={itemVariants}
          onShare={handleShare}
        />
      </div>
    </div>
  );
}
