"use client";

import React, { useState } from "react";
import phishingApi from "@/lib/api/phishing";
import { PhishingAnalysisResult } from "@/lib/types";
import GlassCard from "@/components/ui/GlassCard";
import RiskBadge from "@/components/ui/RiskBadge";
import ScoreRing from "@/components/ui/ScoreRing";
import {
  Link2,
  AlertTriangle,
  Globe,
  CheckCircle,
  ShieldCheck,
  Search,
  ExternalLink,
  Target,
  Sparkles
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export default function PhishShieldPage() {
  const [urlInput, setUrlInput] = useState("");
  const [isScanning, setIsScanning] = useState(false);
  const [result, setResult] = useState<PhishingAnalysisResult | null>(null);

  const handleScan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!urlInput.trim()) return;

    setIsScanning(true);
    setResult(null);

    try {
      const response = await phishingApi.checkUrl(urlInput);
      setResult(response);
    } catch (err) {
      console.error("Phishing scan failed:", err);
    } finally {
      setIsScanning(false);
    }
  };

  const getRiskVariant = (level: string) => {
    switch (level) {
      case "HIGH":
        return "high";
      case "SUSPICIOUS":
        return "medium";
      default:
        return "safe";
    }
  };

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-text-primary">
          PhishShield Link Verification
        </h1>
        <p className="text-sm text-text-secondary font-medium">
          Verify target URLs against brand similarities, character entropy, typosquatting vectors, and known redirects.
        </p>
      </div>

      {/* URL Input Form */}
      <GlassCard className="p-6">
        <form onSubmit={handleScan} className="flex flex-col sm:flex-row gap-4">
          <div className="relative flex-grow">
            <Link2 className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-text-secondary" />
            <input
              type="text"
              value={urlInput}
              onChange={(e) => setUrlInput(e.target.value)}
              placeholder="Enter URL to audit (e.g. http://chase-security-verify.net/login)"
              className="w-full bg-bg-base/70 border border-border/80 rounded-xl py-3.5 pl-12 pr-4 text-sm font-semibold placeholder:text-text-secondary/60 focus:outline-none focus:ring-2 focus:ring-accent-blue/30 focus:border-accent-blue/80 transition-all font-mono"
              disabled={isScanning}
            />
          </div>
          <button
            type="submit"
            disabled={isScanning || !urlInput.trim()}
            className="sm:w-36 inline-flex items-center justify-center gap-1.5 rounded-xl bg-text-primary hover:bg-text-primary/95 text-white font-bold px-6 py-3.5 transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50"
          >
            {isScanning ? (
              <>
                <Search className="h-4 w-4 animate-spin text-accent-teal" />
                Scanning
              </>
            ) : (
              "Scan URL"
            )}
          </button>
        </form>
      </GlassCard>

      {/* Dynamic Results Display */}
      <AnimatePresence mode="wait">
        {isScanning ? (
          <motion.div
            key="scanning-loader"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="min-h-[300px] flex flex-col items-center justify-center text-center p-8 bg-surface/40 border border-border/60 rounded-3xl backdrop-blur"
          >
            <div className="h-12 w-12 rounded-full border-4 border-slate-100 border-t-accent-teal animate-spin mb-4" />
            <h3 className="text-base font-bold text-text-primary">Auditing URL Entropy</h3>
            <p className="text-xs text-text-secondary mt-1.5 max-w-sm font-semibold">
              Probing target host DNS patterns, resolving redirects, and verifying brand lookalikes...
            </p>
          </motion.div>
        ) : result ? (
          <motion.div
            key="scan-result"
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="grid grid-cols-1 lg:grid-cols-3 gap-8"
          >
            {/* Left Result Overview */}
            <div className="lg:col-span-1 space-y-6">
              <GlassCard className="p-6 flex flex-col items-center text-center">
                <span className="text-[10px] font-bold text-text-secondary uppercase tracking-widest mb-4">
                  Global Scorer Verdict
                </span>

                <ScoreRing score={result.risk_score} size={130} className="mb-6" />

                <RiskBadge variant={getRiskVariant(result.risk_level)} className="mb-4" />

                <p className="text-xs text-text-secondary leading-relaxed font-semibold px-2">
                  {result.message}
                </p>
              </GlassCard>

              {/* Domain information card */}
              <GlassCard className="p-6 space-y-4">
                <h4 className="text-xs font-bold text-text-secondary uppercase tracking-widest flex items-center gap-1.5">
                  <Globe className="h-4 w-4 text-accent-blue" /> Domain Identity
                </h4>

                <div className="space-y-3 font-semibold text-xs text-text-primary">
                  <div className="flex justify-between py-1 border-b border-border/20">
                    <span className="text-text-secondary">Scanned Domain</span>
                    <span className="font-mono text-right truncate max-w-[170px]">{result.domain}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-border/20">
                    <span className="text-text-secondary">Normalized Target</span>
                    <span className="font-mono text-right truncate max-w-[170px]">{result.normalized_url}</span>
                  </div>
                </div>
              </GlassCard>
            </div>

            {/* Right Audit Details */}
            <div className="lg:col-span-2 space-y-6">
              {/* Triggered rules lists */}
              <GlassCard className="p-6">
                <h3 className="text-sm font-bold text-text-secondary uppercase tracking-wider mb-6 flex items-center gap-1.5">
                  <AlertTriangle className="h-4 w-4 text-risk-high" /> Triggered PhishShield Policies
                </h3>

                {result.triggered_rules.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-10 text-center text-text-secondary">
                    <CheckCircle className="h-10 w-10 text-risk-safe mb-3" />
                    <p className="font-bold text-sm">No threat vectors identified</p>
                    <p className="text-xs mt-1 max-w-xs font-semibold">The URL doesn't contain spoofed signatures or brand keyword redirects.</p>
                  </div>
                ) : (
                  <div className="space-y-4.5">
                    {result.triggered_rules.map((rule, idx) => (
                      <div
                        key={idx}
                        className="flex items-start gap-4 p-4 rounded-xl bg-bg-base border border-border/40"
                      >
                        <span className="h-6 w-6 rounded-lg bg-risk-critical/10 text-risk-critical flex items-center justify-center font-mono font-bold text-xs shrink-0 mt-0.5">
                          {rule.score}
                        </span>
                        <div className="space-y-1">
                          <div className="text-xs font-bold text-text-primary">{rule.rule}</div>
                          <div className="text-xs text-text-secondary leading-normal font-semibold">
                            {rule.detail}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </GlassCard>

              {/* Brand Lookalike Sim matches */}
              {result.domain_similarity_matches && result.domain_similarity_matches.length > 0 && (
                <GlassCard className="p-6">
                  <h3 className="text-sm font-bold text-text-secondary uppercase tracking-wider mb-4 flex items-center gap-1.5">
                    <Target className="h-4 w-4 text-accent-teal" /> Brand Imitation Index
                  </h3>

                  <div className="space-y-3.5">
                    {result.domain_similarity_matches.map((match, idx) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between p-3.5 rounded-xl border border-border/40 bg-bg-base/40 text-xs font-semibold"
                      >
                        <div className="space-y-1">
                          <div className="text-text-primary font-bold">{match.brand}</div>
                          <div className="text-text-secondary font-mono text-[11px]">
                            Official Domain: <span className="text-accent-blue">{match.actual_domain}</span>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="font-mono text-risk-high font-bold">
                            {(match.similarity * 100).toFixed(0)}% Similarity
                          </div>
                          <div className="text-[10px] text-text-secondary uppercase font-bold tracking-wider mt-0.5">
                            Lookalike Alert
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </GlassCard>
              )}
            </div>
          </motion.div>
        ) : (
          <motion.div
            key="empty-scan-state"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="min-h-[300px] flex flex-col items-center justify-center text-center p-8 bg-surface/30 border border-border/40 border-dashed rounded-3xl"
          >
            <div className="h-12 w-12 rounded-full border border-border flex items-center justify-center bg-bg-base text-text-secondary shadow-sm mb-4">
              <Link2 className="h-5 w-5" />
            </div>
            <h3 className="text-sm font-bold text-text-primary">Awaiting Link Scan</h3>
            <p className="text-xs text-text-secondary mt-1.5 max-w-xs font-semibold">
              Input a domain hyperlink above to verify character entropy, host registrars, and typosquatting signatures.
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
