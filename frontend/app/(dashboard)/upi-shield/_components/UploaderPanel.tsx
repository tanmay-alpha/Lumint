"use client";

import React from "react";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  Check,
  Layers,
  Scan,
  Shield,
  Sparkles,
  Upload,
} from "lucide-react";
import { UploadZone } from "@/components/ui/UploadZone";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";

// ─── UploaderPanel ─────────────────────────────────────────────────────────
//
// Left column of the /upi-shield split layout. Owns the upload zone
// (animated empty state OR the populated `UploadZone`), the sample gallery,
// the analyze CTA, the live progress meter, and the "How it works" guide
// that hides once a result lands.
//
// All state lives in the parent page; this component is purely controlled.
export interface UploaderPanelProps {
  file: File | null;
  uploading: boolean;
  progress: number;
  result: boolean; // whether a result is currently shown (controls the "How it works" card)
  error: string | null;
  onFileSelected: (f: File) => void;
  onAnalyze: () => void;
  onLoadSample: (path: string) => void;
}

export function UploaderPanel({
  file,
  uploading,
  progress,
  result,
  error,
  onFileSelected,
  onAnalyze,
  onLoadSample,
}: UploaderPanelProps) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -16 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.4, delay: 0.1 }}
      className="space-y-4"
    >
      <Card className="p-6">
        <span className="text-[11px] font-bold text-[var(--text-3)] uppercase tracking-wider block mb-4">
          Upload Payment Screenshot
        </span>
        {!file && !uploading && !result ? (
          // Animated upload zone with pulsing dashed border
          <motion.div
            className="rounded-xl border-2 border-dashed border-[var(--border)] p-8 text-center cursor-pointer transition-colors hover:border-[var(--brand)]"
            animate={{
              borderColor: [
                "var(--border)",
                "var(--brand)",
                "var(--border)",
              ],
            }}
            transition={{ duration: 2.5, repeat: Infinity, ease: "easeInOut" }}
            onClick={() => document.getElementById("upi-file-input")?.click()}
          >
            <Upload className="h-10 w-10 mx-auto text-[var(--text-4)] mb-3" />
            <h3 className="text-[15px] font-semibold text-[var(--text-1)]">
              Drop a UPI transaction screenshot
            </h3>
            <p className="text-[12px] text-[var(--text-3)] mt-1">
              OCR runs in your browser. Nothing is uploaded.
            </p>
            <input
              id="upi-file-input"
              type="file"
              accept="image/png,image/jpeg"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) onFileSelected(f);
                e.target.value = "";
              }}
            />
          </motion.div>
        ) : (
          <UploadZone
            accept=".png,.jpg,.jpeg"
            maxSizeMB={10}
            label="Drop payment screenshot here"
            subLabel="PhonePe · Google Pay · Paytm · BHIM"
            onFileSelected={onFileSelected}
            disabled={uploading}
            progress={uploading ? progress : 0}
          />
        )}

        {/* Ghost preview of what the results panel will look like */}
        {!file && !uploading && !result && (
          <div className="mt-6 opacity-30 pointer-events-none select-none" aria-hidden="true">
            <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-1)] p-5">
              <div className="text-[10px] font-mono font-bold text-[var(--text-4)] uppercase tracking-wider">
                Verdict
              </div>
              <div className="h-7 bg-[var(--surface-2)] rounded mt-2 w-2/3" />
              <div className="grid grid-cols-3 gap-2 mt-4">
                <div className="h-14 bg-[var(--surface-2)] rounded" />
                <div className="h-14 bg-[var(--surface-2)] rounded" />
                <div className="h-14 bg-[var(--surface-2)] rounded" />
              </div>
            </div>
          </div>
        )}

        {/* Test gallery: 3 sample images for instant trial. */}
        {!file && !uploading && (
          <div className="mt-4 rounded-lg border border-[var(--border)] bg-[var(--surface-1)] p-4">
            <h3 className="mb-3 text-[11px] font-semibold uppercase tracking-wider text-[var(--text-3)]">
              Try a sample screenshot
            </h3>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => onLoadSample("/samples/genuine-phonepe.png")}
                className="rounded border border-[var(--border)] bg-[var(--surface-2)] p-2.5 text-[11px] font-semibold text-[var(--text-2)] hover:border-[var(--brand)] hover:text-[var(--brand)] transition-colors"
              >
                ✓ Genuine PhonePe
              </button>
              <button
                type="button"
                onClick={() => onLoadSample("/samples/tampered-screenshot.png")}
                className="rounded border border-[var(--border)] bg-[var(--surface-2)] p-2.5 text-[11px] font-semibold text-[var(--text-2)] hover:border-[var(--high)] hover:text-[var(--high)] transition-colors"
              >
                ⚠ Tampered
              </button>
              <button
                type="button"
                onClick={() => onLoadSample("/samples/college-id.png")}
                className="rounded border border-[var(--border)] bg-[var(--surface-2)] p-2.5 text-[11px] font-semibold text-[var(--text-2)] hover:border-[var(--warn)] hover:text-[var(--warn)] transition-colors"
              >
                ❌ College ID
              </button>
            </div>
          </div>
        )}

        {file && !uploading && !result && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-4"
          >
            <Button
              onClick={onAnalyze}
              variant="solid"
              className="w-full flex items-center justify-center gap-2"
            >
              <Shield className="h-4 w-4" />
              Analyze Screenshot
            </Button>
          </motion.div>
        )}

        {uploading && (
          <div className="mt-4 space-y-2">
            <div className="flex items-center justify-between text-[11px] font-bold text-[var(--text-3)]">
              <span className="uppercase tracking-wider">
                {progress < 15
                  ? "Loading AI engine…"
                  : progress < 30
                  ? "Pre-processing image…"
                  : progress < 90
                  ? "Reading text (OCR)…"
                  : progress < 100
                  ? "Analyzing patterns…"
                  : "Done!"}
              </span>
              <span className="text-[var(--brand)]">{progress}%</span>
            </div>
            <div className="h-1.5 bg-[var(--surface-3)] rounded-full overflow-hidden">
              <div
                className="h-full bg-[var(--brand)] transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
            <div className="text-center text-[10px] text-[var(--text-3)] font-medium">
              First run may take 10–20s while engine initializes
            </div>
          </div>
        )}

        {error && (
          <div
            role="alert"
            aria-live="assertive"
            className="mt-3 flex items-start gap-2 text-[12px] text-[var(--high)] bg-[var(--high-bg)] border border-[var(--high-border)]/30 rounded-lg px-4 py-3"
          >
            <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}
      </Card>

      {/* How it works card — collapses after result is loaded */}
      {!result && (
        <Card className="p-6">
          <span className="text-[11px] font-bold text-[var(--text-3)] uppercase tracking-wider block mb-4">
            How UPI Shield works
          </span>
          <div className="relative pl-8 space-y-6">
            <div className="absolute left-[11px] top-3 bottom-3 w-[1.5px] bg-[var(--border)]" />
            {[
              { icon: <Scan className="h-3.5 w-3.5 text-[var(--brand)]" />, label: "OCR extraction", desc: "Tesseract extracts UTR, VPA, and amount from the screenshot" },
              { icon: <Check className="h-3.5 w-3.5 text-[var(--brand)]" />, label: "Structural validation", desc: "UTR 12-digit format, VPA domain, and font consistency checks" },
              { icon: <Layers className="h-3.5 w-3.5 text-[var(--brand)]" />, label: "ELA forensics", desc: "Error Level Analysis detects pixel manipulation regions" },
              { icon: <Sparkles className="h-3.5 w-3.5 text-[var(--brand)]" />, label: "Groq LLM verdict", desc: "LLaMA 3.3 70B synthesizes a forensic analyst narrative" },
            ].map(({ icon, label, desc }, idx) => (
              <div key={idx} className="relative flex items-start gap-4">
                <div className="absolute -left-[32px] h-6 w-6 rounded-full bg-[var(--brand)] text-white text-[11px] font-bold flex items-center justify-center z-10 shadow-sm">
                  {idx + 1}
                </div>
                <div>
                  <div className="flex items-center gap-1.5 text-[13px] font-semibold text-[var(--text-1)] leading-tight">
                    {icon}
                    <span>{label}</span>
                  </div>
                  <p className="text-[12px] text-[var(--text-3)] font-semibold leading-relaxed mt-1">{desc}</p>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </motion.div>
  );
}

export default UploaderPanel;