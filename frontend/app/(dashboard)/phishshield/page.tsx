"use client";

import React, { useState } from "react";
import phishingApi from "@/lib/api/phishing";
import { PhishingAnalysisResult, PhishingAIResult } from "@/lib/types";
import aiApi from "@/lib/api/ai";
import GlassCard from "@/components/ui/GlassCard";
import RiskBadge from "@/components/ui/RiskBadge";
import RiskScore from "@/components/ui/RiskScore";
import {
  Link2,
  AlertTriangle,
  Globe,
  CheckCircle,
  Search,
  Target,
  Sparkles,
  Cpu
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export default function PhishShieldPage() {
  const [urlInput, setUrlInput] = useState("");
  const [isScanning, setIsScanning] = useState(false);
  const [result, setResult] = useState<PhishingAnalysisResult | null>(null);
  const [aiResult, setAiResult] = useState<PhishingAIResult | null>(null);
  const [isAnalyzingAI, setIsAnalyzingAI] = useState(false);

  const handleScan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!urlInput.trim()) return;

    setIsScanning(true);
    setResult(null);
    setAiResult(null);

    try {
      const response = await phishingApi.checkUrl(urlInput);
      setResult(response);
      
      // Auto-trigger AI Analysis
      setIsAnalyzingAI(true);
      try {
        const aiResponse = await aiApi.analyzePhishing(response);
        setAiResult(aiResponse);
      } catch (aiErr) {
        console.error("PhishShield AI brief failure:", aiErr);
      } finally {
        setIsAnalyzingAI(false);
      }
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

                <RiskScore score={result.risk_score} size="md" className="mb-6" />

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
                    <p className="text-xs mt-1 max-w-xs font-semibold">The URL doesn&apos;t contain spoofed signatures or brand keyword redirects.</p>
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

            {/* AI Phishing Analyst Report */}
            <div className="lg:col-span-3">
              <GlassCard className="p-6 space-y-6">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border/20 pb-5">
                  <div className="space-y-1">
                    <div className="text-[10px] font-bold text-text-secondary uppercase tracking-widest flex items-center gap-1.5 font-semibold">
                      <Sparkles className="h-3.5 w-3.5 text-accent-teal" /> Lumint AI Analyst Brief
                    </div>
                    <h3 className="text-lg font-bold text-text-primary">
                      {isAnalyzingAI ? (
                        <span className="flex items-center gap-2">
                          <span className="h-4 w-4 rounded-full border-2 border-slate-100 border-t-accent-teal animate-spin shrink-0" />
                          Consulting AI Oracle...
                        </span>
                      ) : aiResult ? (
                        <>Inferred Threat Vector: <span className="font-mono text-xs bg-surface border border-border/60 px-2 py-0.5 rounded font-bold uppercase">{aiResult.attack_vector.replace('_', ' ')}</span></>
                      ) : (
                        "Awaiting AI Generation"
                      )}
                    </h3>
                  </div>
                  {aiResult && (
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <div className="text-[10px] font-bold text-text-secondary uppercase">Confidence</div>
                        <div className="text-sm font-bold font-mono text-text-primary">{aiResult.confidence}%</div>
                      </div>
                      <span className={`h-8 px-3 rounded-lg flex items-center justify-center text-xs font-bold ${
                        aiResult.verdict === "SAFE" 
                          ? "bg-risk-safe/10 text-risk-safe border border-risk-safe/25" 
                          : aiResult.verdict === "SUSPICIOUS"
                          ? "bg-risk-medium/10 text-risk-medium border border-risk-medium/25"
                          : "bg-risk-critical/10 text-risk-critical border border-risk-critical/25"
                      }`}>
                        {aiResult.verdict}
                      </span>
                    </div>
                  )}
                </div>

                {isAnalyzingAI ? (
                  <div className="py-8 flex flex-col items-center justify-center text-center">
                    <span className="text-xs text-text-secondary font-semibold animate-pulse">Running domain lookup heuristics and generating threat intelligence vectors...</span>
                  </div>
                ) : aiResult ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs">
                    <div className="space-y-4">
                      <div>
                        <h4 className="font-bold text-text-secondary uppercase tracking-widest mb-2">Analyst Executive Summary</h4>
                        <p className="text-text-secondary leading-relaxed font-semibold">{aiResult.analyst_note}</p>
                      </div>

                      {aiResult.target_brand && (
                        <div>
                          <div className="text-[10px] font-bold text-text-secondary uppercase mb-1">Target Brand Impersonation</div>
                          <span className="font-mono font-bold text-risk-high bg-risk-high/5 border border-risk-high/15 px-2 py-1 rounded inline-block">
                            {aiResult.target_brand}
                          </span>
                        </div>
                      )}
                    </div>

                    <div className="space-y-4 md:border-l md:border-border/30 md:pl-6">
                      <div>
                        <h4 className="font-bold text-text-secondary uppercase tracking-widest mb-2">Indicators of Compromise (IOC) Summary</h4>
                        <ul className="space-y-1.5">
                          {aiResult.ioc_summary.map((ioc, idx) => (
                            <li key={idx} className="text-text-primary font-semibold flex items-start gap-2">
                              <span className="h-1.5 w-1.5 rounded-full bg-accent-teal mt-1.5 shrink-0" />
                              <span>{ioc}</span>
                            </li>
                          ))}
                          {aiResult.ioc_summary.length === 0 && (
                            <li className="text-text-secondary italic font-semibold">No critical indicators of compromise flagged.</li>
                          )}
                        </ul>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="py-4 text-center text-text-secondary italic font-semibold">
                    No active link scan completed.
                  </div>
                )}

                {aiResult && (
                  <div className="flex items-center justify-between border-t border-border/20 pt-4 text-[10px] font-semibold text-text-secondary">
                    <div className="flex items-center gap-1.5">
                      <Cpu className="h-3 w-3 text-accent-teal" />
                      <span>Model: <span className="font-mono text-text-primary">{aiResult.model_used}</span></span>
                    </div>
                    {aiResult.latency_ms > 0 && (
                      <div>
                        Latency: <span className="font-mono text-text-primary">{aiResult.latency_ms}ms</span>
                      </div>
                    )}
                  </div>
                )}
              </GlassCard>
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
