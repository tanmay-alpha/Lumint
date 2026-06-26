"use client";

import React, { useState } from "react";
import phishingApi from "@/lib/api/phishing";
import { PhishingAnalysisResult, PhishingAIResult } from "@/lib/types";
import aiApi from "@/lib/api/ai";
import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import RiskScore from "@/components/ui/RiskScore";
import DataPoint from "@/components/ui/DataPoint";
import { EmptyStateWithCTA } from "@/components/ui/EmptyStateWithCTA";
import { saveScan } from "@/lib/scan-history";
import {
  Link2,
  AlertTriangle,
  Globe,
  CheckCircle,
  Search,
  Sparkles,
  Cpu,
  ShieldAlert,
  Calendar,
  AlertCircle,
  Clipboard
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export default function PhishShieldPage() {
  const [urlInput, setUrlInput] = useState("");
  const [isScanning, setIsScanning] = useState(false);
  const [result, setResult] = useState<PhishingAnalysisResult | null>(null);
  const [aiResult, setAiResult] = useState<PhishingAIResult | null>(null);
  const [isAnalyzingAI, setIsAnalyzingAI] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"policies" | "domain" | "ai">("policies");

  const handleScan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!urlInput.trim()) {
      setError("Please enter a URL to analyze.");
      return;
    }
    if (!urlInput.includes(".")) {
      setError("Please enter a valid domain or hyperlink.");
      return;
    }

    setError(null);
    setIsScanning(true);
    setResult(null);
    setAiResult(null);

    try {
      const response = await phishingApi.checkUrl(urlInput);
      if (!response) {
        // Soft-fail path: backend not configured or unreachable.
        setError("PhishShield could not reach the backend. Check your connection and the LUMINT_API_KEY env var on Vercel.");
        return;
      }
      setResult(response);
      saveScan({
        shield: "phish",
        verdict: response.risk_level,
        label: response.message,
        score: response.risk_score,
        url: response.url,
      });

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
    } catch (err: any) {
      console.error("Phishing scan failed:", err);
      setError(err?.message || "An error occurred during URL audit.");
    } finally {
      setIsScanning(false);
    }
  };

  const getRiskVariant = (level: string): any => {
    switch (level?.toUpperCase()) {
      case "CRITICAL":
        return "critical";
      case "HIGH":
      case "HIGH RISK":
        return "high";
      case "SUSPICIOUS":
      case "WARN":
        return "warn";
      default:
        return "safe";
    }
  };

  const formatAge = (days: number | null | undefined): string => {
    if (days === null || days === undefined) return "Unknown";
    if (days < 0) return "Unknown";
    if (days < 30) return `${days} days (Newly registered)`;
    if (days < 365) return `${days} days`;
    const years = Math.floor(days / 365);
    const remaining = days % 365;
    if (remaining === 0) return `${years} year${years > 1 ? "s" : ""}`;
    return `${years}y ${Math.floor(remaining / 30)}mo`;
  };

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[var(--border)] pb-5">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="h-9 w-9 rounded-lg bg-[var(--brand-muted)] text-[var(--brand)] flex items-center justify-center shadow-sm">
              <Globe className="h-5 w-5" />
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-[var(--text-1)]">
              PhishShield Link Verification
            </h1>
          </div>
          <p className="text-sm text-[var(--text-3)] font-medium mt-1 pl-11">
            Verify target URLs against brand similarities, character entropy, typosquatting vectors, and known redirects.
          </p>
        </div>
        <div className="flex items-center gap-2.5 md:self-end">
          <Badge variant="neutral" dot size="sm">API Online</Badge>
          <Badge variant="ai" dot size="sm">AI Ready</Badge>
        </div>
      </div>

      {/* URL Input Form */}
      <Card variant="default" className="p-8 text-center max-w-4xl mx-auto">
        <h2 className="text-sm font-bold text-[var(--text-3)] tracking-wider uppercase mb-4">
          ENTER SUSPICIOUS HYPERLINK
        </h2>
        <form onSubmit={handleScan} className="mx-auto max-w-2xl">
          <div
            className={`relative flex items-center bg-[var(--surface-2)] border ${
              error ? "border-[var(--high)]" : "border-[var(--border)]"
            } rounded-[var(--r-3)] shadow-[var(--shadow-1)] focus-within:border-[var(--border-focus)] focus-within:bg-[var(--surface)] focus-within:ring-[3px] focus-within:ring-[rgba(37,99,235,0.12)] transition-all p-1`}
          >
            <Link2 className="absolute left-4 h-4 w-4 text-[var(--text-3)]" />
            <input
              type="text"
              value={urlInput}
              onChange={(e) => {
                setUrlInput(e.target.value);
                if (error) setError(null);
              }}
              placeholder="https://..."
              className="w-full bg-transparent pl-11 pr-36 py-3.5 text-sm font-sans text-[var(--text-1)] placeholder:text-[var(--text-4)] focus:outline-none"
              disabled={isScanning}
            />
            <button
              type="button"
              onClick={async () => {
                try {
                  const text = await navigator.clipboard.readText();
                  if (text) { setUrlInput(text.trim()); if (error) setError(null); }
                } catch {}
              }}
              title="Paste from clipboard"
              className="absolute right-[100px] top-1 bottom-1 px-2.5 rounded-[var(--r-2)] text-[var(--text-2)] hover:text-[var(--text-1)] hover:bg-[var(--surface-3)] font-bold text-[11px] flex items-center gap-1 cursor-pointer transition-all"
            >
              <Clipboard className="h-3.5 w-3.5" />
              Paste
            </button>
            <button
              type="submit"
              disabled={isScanning || !urlInput.trim()}
              className="absolute right-1 top-1 bottom-1 px-5 rounded-[var(--r-2)] bg-[var(--critical)] text-white hover:opacity-90 font-bold text-xs flex items-center gap-1.5 cursor-pointer disabled:opacity-50 transition-all select-none"
            >
              {isScanning ? (
                <>
                  <Search className="h-3.5 w-3.5 animate-spin text-[var(--intel-border)]" />
                  Scanning...
                </>
              ) : (
                <>
                  <Globe className="h-3.5 w-3.5" />
                  Scan URL
                </>
              )}
            </button>
          </div>
          {error && (
            <p className="mt-2 text-xs font-medium text-[var(--high)] text-left pl-2 flex items-center gap-1.5">
              <AlertCircle className="h-3.5 w-3.5 shrink-0" />
              {error}
            </p>
          )}
        </form>

        {/* Quick Test Chips */}
        <div className="flex flex-wrap items-center justify-center gap-2 mt-4">
          <span className="text-[11px] font-bold uppercase tracking-wider text-[var(--text-4)]">Try:</span>
          <button
            type="button"
            onClick={() => {
              setUrlInput("hdfc-secure-login.tk");
              setError(null);
            }}
            className="px-2.5 py-1 rounded-[var(--r-full)] bg-[var(--surface-3)] text-[var(--text-2)] hover:bg-[var(--border-2)] font-mono text-xs transition-all cursor-pointer"
          >
            hdfc-secure-login.tk
          </button>
          <button
            type="button"
            onClick={() => {
              setUrlInput("chase-security-verify.net");
              setError(null);
            }}
            className="px-2.5 py-1 rounded-[var(--r-full)] bg-[var(--surface-3)] text-[var(--text-2)] hover:bg-[var(--border-2)] font-mono text-xs transition-all cursor-pointer"
          >
            chase-security-verify.net
          </button>
        </div>
      </Card>

      {/* Dynamic Results Display */}
      <AnimatePresence mode="wait">
        {isScanning ? (
          <motion.div
            key="scanning-loader"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="min-h-[350px] flex flex-col items-center justify-center text-center p-8 bg-[var(--surface)] border border-[var(--border)] rounded-[var(--r-4)] shadow-[var(--shadow-2)]"
          >
            <div className="h-12 w-12 rounded-full border-4 border-[var(--surface-3)] border-t-[var(--intel)] animate-spin mb-4" />
            <h3 className="text-base font-bold text-[var(--text-1)]">Auditing URL Entropy</h3>
            <p className="text-xs text-[var(--text-3)] mt-1.5 max-w-sm font-semibold">
              Probing target host DNS patterns, resolving redirects, and verifying brand lookalikes...
            </p>
          </motion.div>
        ) : result ? (
          <div
            aria-live="polite"
            aria-atomic="true"
            role="region"
            aria-label="PhishShield analysis result"
            className="contents"
          >
          <motion.div
            key="scan-result"
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="grid grid-cols-1 lg:grid-cols-10 gap-8 items-start"
          >
            {/* Left 40% - Verdict Panel */}
            <div className="lg:col-span-4 space-y-6">
              <Card variant="elevated" className="p-6 flex flex-col items-center text-center">
                <span className="text-[10px] font-bold text-[var(--text-3)] uppercase tracking-widest mb-4 font-semibold">
                  Global Scorer Verdict
                </span>

                <RiskScore score={result.risk_score} size="md" className="mb-6" />

                <Badge variant={getRiskVariant(result.risk_level)} className="mb-5" dot>
                  {result.risk_level}
                </Badge>

                <p className="text-sm text-[var(--text-2)] leading-relaxed font-sans font-medium px-4">
                  {result.message}
                </p>

                {/* Phishing Impersonation brand chip */}
                {result.risk_score >= 50 && result.domain_similarity_matches?.[0] && (
                  <div className="mt-5 w-full pt-4 border-t border-[var(--border)]">
                    <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-[var(--r-2)] bg-[var(--warn-bg)] text-[var(--warn)] border border-[var(--warn-border)] text-xs font-semibold">
                      <ShieldAlert className="h-3.5 w-3.5" />
                      Impersonating: {result.domain_similarity_matches[0].brand}
                    </span>
                  </div>
                )}
              </Card>
            </div>

            {/* Right 60% - Details Panel */}
            <div className="lg:col-span-6 space-y-6">
              {/* Tab Navigation */}
              <div className="flex border-b border-[var(--border)] gap-6">
                {(["policies", "domain", "ai"] as const).map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={`pb-3 text-xs font-bold uppercase tracking-wider relative cursor-pointer ${
                      activeTab === tab
                        ? "text-[var(--brand)]"
                        : "text-[var(--text-3)] hover:text-[var(--text-2)]"
                    }`}
                  >
                    {tab === "policies"
                      ? "Triggered Policies"
                      : tab === "domain"
                      ? "Domain Analysis"
                      : "AI Analysis"}
                    {activeTab === tab && (
                      <motion.div
                        layoutId="activeTabUnderline"
                        className="absolute bottom-0 left-0 right-0 h-[2px] bg-[var(--brand)]"
                        transition={{ type: "spring", stiffness: 380, damping: 30 }}
                      />
                    )}
                  </button>
                ))}
              </div>

              {/* Tab Content */}
              <div>
                {activeTab === "policies" && (
                  <Card variant="default" className="p-6">
                    <div className="flex items-center justify-between mb-6 pb-4 border-b border-[var(--border)]">
                      <h3 className="text-xs font-bold text-[var(--text-3)] uppercase tracking-wider flex items-center gap-1.5">
                        <AlertTriangle className="h-4 w-4 text-[var(--high)]" /> Policy Engine Evaluation
                      </h3>
                      <Badge variant={result.triggered_rules.length > 0 ? "high" : "safe"} size="sm">
                        {result.triggered_rules.length} Flagged
                      </Badge>
                    </div>

                    {result.triggered_rules.length === 0 ? (
                      <div className="flex flex-col items-center justify-center py-10 text-center text-[var(--text-3)]">
                        <div className="h-12 w-12 rounded-full bg-[var(--safe-bg)] text-[var(--safe)] border border-[var(--safe-border)] flex items-center justify-center mb-3">
                          <CheckCircle className="h-6 w-6" />
                        </div>
                        <p className="font-bold text-sm text-[var(--text-1)]">No threat vectors identified</p>
                        <p className="text-xs mt-1.5 max-w-xs font-semibold">
                          The URL doesn&apos;t contain spoofed signatures or brand keyword redirects.
                        </p>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        {result.triggered_rules.map((rule, idx) => (
                          <div
                            key={idx}
                            className="flex items-start gap-4 p-4 rounded-xl bg-[var(--surface-2)] border border-[var(--border)]"
                          >
                            <span className="h-6 w-6 rounded-lg bg-[var(--high-bg)] text-[var(--high)] border border-[var(--high-border)] flex items-center justify-center font-mono font-bold text-xs shrink-0 mt-0.5">
                              {rule.score}
                            </span>
                            <div className="space-y-1">
                              <div className="text-xs font-bold text-[var(--text-1)]">{rule.rule}</div>
                              <div className="text-xs text-[var(--text-3)] leading-normal font-semibold">
                                {rule.detail}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </Card>
                )}

                {activeTab === "domain" && (
                  <Card variant="default" className="p-6 space-y-6">
                    <h3 className="text-xs font-bold text-[var(--text-3)] uppercase tracking-wider flex items-center gap-1.5 pb-4 border-b border-[var(--border)]">
                      <Globe className="h-4 w-4 text-[var(--brand)]" /> Registrant & Similarity Metrics
                    </h3>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <DataPoint
                        label="Scanned Domain"
                        value={
                          <span className="font-mono text-xs font-semibold text-[var(--text-1)]">
                            {result.domain}
                          </span>
                        }
                        mono={true}
                        copyable
                      />
                      <DataPoint
                        label="Normalized Target"
                        value={
                          <span className="font-mono text-xs font-semibold text-[var(--text-1)]">
                            {result.normalized_url}
                          </span>
                        }
                        mono={true}
                        copyable
                      />
                      <DataPoint
                        label="Domain Age"
                        value={
                          <span className="font-mono text-xs font-semibold text-[var(--text-1)] flex items-center gap-1.5">
                            <Calendar className="h-3.5 w-3.5 text-[var(--text-3)]" />
                            {formatAge(result.whois?.age_days)}
                          </span>
                        }
                        mono={true}
                      />
                      <DataPoint
                        label="Registrar"
                        value={
                          <span className="font-mono text-xs font-semibold text-[var(--text-1)]">
                            {result.whois?.registrar ?? <span className="text-[var(--text-4)] italic">Unknown</span>}
                          </span>
                        }
                        mono={true}
                      />
                      <DataPoint
                        label="SSL Issuer"
                        value={
                          <span className="font-mono text-xs font-semibold text-[var(--text-1)]">
                            {result.ssl?.issuer
                              ? result.ssl.issuer.split(",")[0].replace(/^[^=]*=/, "")
                              : <span className="text-[var(--text-4)] italic">No SSL / Unknown</span>}
                          </span>
                        }
                        mono={true}
                      />
                      <DataPoint
                        label="SSL Expiry"
                        value={
                          <span className={`font-mono text-xs font-semibold ${result.ssl?.is_expired ? "text-[var(--high)]" : "text-[var(--text-1)]"}`}>
                            {result.ssl?.valid_to
                              ? result.ssl.valid_to.split("T")[0]
                              : <span className="text-[var(--text-4)] italic">Unknown</span>}
                          </span>
                        }
                        mono={true}
                      />
                      <DataPoint
                        label="SSL Status"
                        value={
                          result.ssl?.is_expired ? (
                            <span className="font-mono text-xs font-semibold text-[var(--high)]">EXPIRED</span>
                          ) : result.ssl?.is_self_signed ? (
                            <span className="font-mono text-xs font-semibold text-[var(--warn)]">SELF-SIGNED</span>
                          ) : (
                            <span className="font-mono text-xs font-semibold text-[var(--safe)]">VALID</span>
                          )
                        }
                        mono={true}
                      />
                      <div>
                        <span className="t-label block mb-1.5 text-[var(--text-3)]">
                          Brand Similarity Score
                        </span>
                        {result.domain_similarity_matches && result.domain_similarity_matches.length > 0 ? (
                          <div className="space-y-2">
                            {result.domain_similarity_matches.map((match, idx) => {
                              const similarityPercent = Math.round(match.similarity * 100);
                              return (
                                <div key={idx} className="space-y-1">
                                  <div className="flex justify-between text-[11px] font-semibold text-[var(--text-2)]">
                                    <span>{match.brand} ({match.actual_domain})</span>
                                    <span>{similarityPercent}%</span>
                                  </div>
                                  <div className="h-2 w-full bg-[var(--surface-3)] rounded-full overflow-hidden">
                                    <div
                                      className="h-full rounded-full bg-[var(--warn)]"
                                      style={{ width: `${similarityPercent}%` }}
                                    />
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        ) : (
                          <div className="text-xs text-[var(--text-4)] italic font-semibold pt-1">
                            No matching corporate brand signature detected.
                          </div>
                        )}
                      </div>
                    </div>
                  </Card>
                )}

                {activeTab === "ai" && (
                  <Card variant="ai" className="p-6 space-y-6">
                    <div className="flex items-center justify-between pb-4 border-b border-[var(--ai-border)]">
                      <div className="flex items-center gap-2">
                        <Sparkles className="h-4 w-4 text-[var(--ai)]" />
                        <h3 className="text-xs font-bold text-[var(--ai-text)] uppercase tracking-wider">
                          AI Phishing Oracle Brief
                        </h3>
                      </div>
                      {aiResult && (
                        <div className="flex items-center gap-2">
                          <Badge variant="ai" size="sm">
                            CONFIDENCE {aiResult.confidence}%
                          </Badge>
                          <Badge variant={getRiskVariant(aiResult.verdict)} size="sm">
                            {aiResult.verdict}
                          </Badge>
                        </div>
                      )}
                    </div>

                    {isAnalyzingAI ? (
                      <div className="py-8 text-center space-y-2">
                        <div className="h-6 w-6 border-2 border-[var(--ai-border)] border-t-[var(--ai)] animate-spin rounded-full mx-auto" />
                        <p className="text-xs text-[var(--ai-text)] font-semibold animate-pulse">
                          Running predictive threat vector checks...
                        </p>
                      </div>
                    ) : aiResult ? (
                      <div className="space-y-4 text-xs">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <span className="t-label block mb-1 text-[var(--text-3)]">Attack Vector</span>
                            <span className="font-mono bg-[var(--surface)] border border-[var(--border)] px-2 py-0.5 rounded font-bold uppercase text-[var(--text-1)]">
                              {aiResult.attack_vector.replace("_", " ")}
                            </span>
                          </div>
                          {aiResult.target_brand && (
                            <div>
                              <span className="t-label block mb-1 text-[var(--text-3)]">Target Brand</span>
                              <span className="font-mono text-[var(--high)] font-bold bg-[var(--high-bg)] border border-[var(--high-border)] px-2 py-0.5 rounded">
                                {aiResult.target_brand}
                              </span>
                            </div>
                          )}
                        </div>

                        <div>
                          <span className="t-label block mb-1 text-[var(--text-3)]">Analyst Note</span>
                          <p className="text-[var(--text-2)] italic font-sans font-medium leading-relaxed bg-[var(--surface)]/50 p-3 rounded-lg border border-[var(--border)]/35">
                            &ldquo;{aiResult.analyst_note}&rdquo;
                          </p>
                        </div>

                        <div>
                          <span className="t-label block mb-2 text-[var(--text-3)]">
                            Indicators of Compromise (IOC)
                          </span>
                          <ol className="space-y-1.5 list-decimal pl-4 font-mono text-[var(--text-2)]">
                            {aiResult.ioc_summary.map((ioc, idx) => (
                              <li key={idx} className="leading-relaxed">
                                {ioc}
                              </li>
                            ))}
                            {aiResult.ioc_summary.length === 0 && (
                              <li className="text-[var(--text-4)] italic">
                                No indicators flagged by AI.
                              </li>
                            )}
                          </ol>
                        </div>

                        <div className="flex items-center justify-between border-t border-[var(--ai-border)] pt-4 text-[10px] text-[var(--text-3)]">
                          <div className="flex items-center gap-1">
                            <Cpu className="h-3.5 w-3.5 text-[var(--ai)]" />
                            <span>Model: <span className="font-mono font-bold text-[var(--text-1)]">{aiResult.model_used}</span></span>
                          </div>
                          {aiResult.latency_ms > 0 && (
                            <span>Latency: <span className="font-mono font-bold text-[var(--text-1)]">{aiResult.latency_ms}ms</span></span>
                          )}
                        </div>
                      </div>
                    ) : (
                      <div className="py-6 text-center text-[var(--text-3)] italic font-semibold">
                        No active link scan completed.
                      </div>
                    )}
                  </Card>
                )}
              </div>
            </div>
          </motion.div>
          </div>
        ) : (
          <motion.div
            key="empty-scan-state"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="space-y-4"
          >
            <EmptyStateWithCTA
              icon="alert"
              title="PhishShield requires a backend"
              description="URL analysis uses a database of known phishing patterns. Demo mode has limited local checks."
              technicalDetails="Backend not connected · Demo mode"
              primaryAction={{ label: "Try UPI Shield →", href: "/upi-shield" }}
            />
            <Card className="p-4 text-center text-xs font-semibold text-[var(--text-3)]">
              You can still enter a URL above to run local typosquatting heuristics — full backend checks are disabled.
            </Card>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
