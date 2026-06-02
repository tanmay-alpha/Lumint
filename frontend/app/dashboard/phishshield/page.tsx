"use client";

import React, { useState } from "react";
import { 
  Globe, 
  Search, 
  ArrowRight, 
  ShieldAlert, 
  CheckCircle2, 
  HelpCircle, 
  Clock, 
  Server,
  Fingerprint,
  Link as LinkIcon,
  AlertTriangle
} from "lucide-react";
import GlassCard from "@/components/GlassCard";
import ThreatBadge from "@/components/ThreatBadge";
import { phishingService } from "@/services/phishing";
import { PhishingCheckResponse } from "@/types";

export default function PhishShield() {
  const [urlInput, setUrlInput] = useState("");
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState<PhishingCheckResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleScan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!urlInput.trim()) return;

    setAnalyzing(true);
    setError(null);
    setResult(null);

    try {
      const scanResult = await phishingService.check(urlInput);
      setResult(scanResult);
    } catch (err) {
      console.error(err);
      setError("Hostname scan failed. Verify network connectivity or URL syntax.");
    } finally {
      setAnalyzing(false);
    }
  };

  const getRiskColorClass = (score: number) => {
    if (score >= 70) return "text-red-600 bg-red-50 border-red-200";
    if (score >= 35) return "text-amber-600 bg-amber-50 border-amber-200";
    return "text-emerald-600 bg-emerald-50 border-emerald-200";
  };

  const getScoreSeverity = (score: number) => {
    if (score >= 30) return "HIGH";
    if (score >= 15) return "SUSPICIOUS";
    return "CLEAN";
  };

  const hasBrandMatch = result?.domain_similarity_matches && result.domain_similarity_matches.length > 0;
  const brandMatch = hasBrandMatch ? result.domain_similarity_matches[0] : null;
  const homoglyphsDetected = result?.triggered_rules.some(r => r.rule.toLowerCase().includes("homoglyph") || r.rule.toLowerCase().includes("deceptive") || r.rule.toLowerCase().includes("lookalike")) || false;

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      
      {/* Header */}
      <div>
        <h2 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight flex items-center gap-3">
          <Globe className="h-7 w-7 text-slate-900" />
          PhishShield Scanner
        </h2>
        <p className="text-slate-500 mt-1.5 text-sm font-medium">
          Audit hostnames and landing URLs for typosquatting, character mimicry, registry age, and active phishing vectors.
        </p>
      </div>

      {/* Main Form Box */}
      <GlassCard className="p-6 md:p-8">
        <form onSubmit={handleScan} className="space-y-4">
          <label htmlFor="url-input" className="block text-xs font-bold text-slate-500 uppercase tracking-wider">
            Enter target URL / Domain Name to vet
          </label>
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <LinkIcon className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
              <input
                id="url-input"
                type="text"
                value={urlInput}
                onChange={(e) => setUrlInput(e.target.value)}
                placeholder="e.g. secure-login-paypa1.com"
                className="w-full pl-12 pr-4 py-3.5 bg-white border border-slate-200/80 rounded-2xl text-slate-800 text-sm font-semibold tracking-wide placeholder-slate-400 focus:outline-none focus:border-sky-500 focus:ring-4 focus:ring-sky-500/5 transition-all"
                disabled={analyzing}
              />
            </div>
            <button
              type="submit"
              disabled={analyzing || !urlInput.trim()}
              className="px-6 py-3.5 bg-slate-900 hover:bg-slate-800 text-white rounded-2xl text-sm font-bold shadow-md hover:shadow-lg disabled:opacity-50 transition-all flex items-center justify-center gap-2"
            >
              {analyzing ? "Vetting..." : "Analyze URL"}
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </form>

        {error && (
          <div className="mt-4 p-4 rounded-2xl bg-red-50 border border-red-200 text-xs text-red-700 font-bold flex gap-2">
            <AlertTriangle className="h-4.5 w-4.5 shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </GlassCard>

      {/* Analyzing state */}
      {analyzing && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 animate-pulse">
          <div className="md:col-span-2 h-72 bg-slate-200/60 rounded-3xl"></div>
          <div className="h-72 bg-slate-200/60 rounded-3xl"></div>
        </div>
      )}

      {/* Results View */}
      {result && !analyzing && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Main details card */}
          <div className="lg:col-span-2 space-y-8">
            
            {/* Top overview metrics */}
            <GlassCard className="p-6 md:p-8">
              <div className="flex flex-col sm:flex-row justify-between items-start gap-4">
                <div className="min-w-0 flex-1">
                  <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Audited Address</span>
                  <h3 className="text-xl font-extrabold text-slate-900 mt-1 truncate leading-snug break-all" title={result.url}>
                    {result.url}
                  </h3>
                  
                  <div className="flex flex-wrap items-center gap-4 mt-4 text-xs font-semibold text-slate-500">
                    <span className="flex items-center gap-1">
                      <Server className="h-3.5 w-3.5 text-slate-400" />
                      Domain: <strong className="text-slate-700">{result.domain}</strong>
                    </span>
                    <span>•</span>
                    <span className="flex items-center gap-1">
                      <Clock className="h-3.5 w-3.5 text-slate-400" />
                      Protocol: <strong className="text-slate-700">{result.normalized_url.split(":")[0].toUpperCase()}</strong>
                    </span>
                  </div>
                </div>

                <div className={`flex flex-col items-center justify-center p-4 rounded-3xl border w-full sm:w-32 aspect-square text-center shrink-0 ${getRiskColorClass(result.risk_score)}`}>
                  <span className="text-xs font-bold tracking-wider uppercase opacity-85">Risk Index</span>
                  <span className="text-3xl font-black tracking-tight mt-1">{result.risk_score}</span>
                  <span className="text-[9px] font-bold mt-1 uppercase">
                    {result.risk_level}
                  </span>
                </div>
              </div>
            </GlassCard>

            {/* Brand Mimicry & Homoglyphs Audit */}
            <GlassCard className="p-6 md:p-8">
              <div className="flex items-center gap-2 mb-6">
                <Fingerprint className="h-4.5 w-4.5 text-slate-600" />
                <h3 className="text-sm font-bold text-slate-900">Brand Likeness & Deceptive Glyphs</h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Brand mimicry */}
                <div className="p-4 rounded-2xl bg-[#FBFBFC] border border-slate-200/50 space-y-2">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Brand Mimicry</span>
                  <div className="flex justify-between items-center mt-1">
                    <span className="text-xs font-bold text-slate-800">
                      {brandMatch ? `Likeness: ${brandMatch.bank}` : "No match detected"}
                    </span>
                    {brandMatch && (
                      <span className="text-xs font-bold text-red-600 bg-red-55/10 border border-red-200/60 rounded-lg px-2 py-0.5">
                        {Math.round(brandMatch.similarity * 100)}% Match
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-slate-500 leading-normal">
                    Matches string characters with top global brand identity strings for character swaps.
                  </p>
                </div>

                {/* Homoglyph characters */}
                <div className="p-4 rounded-2xl bg-[#FBFBFC] border border-slate-200/50 space-y-2">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Homoglyph Check</span>
                  <div className="flex justify-between items-center mt-1">
                    <span className="text-xs font-bold text-slate-800">
                      {homoglyphsDetected ? "Suspicious Swaps Found" : "No deceptive glyphs"}
                    </span>
                    <span className={`text-[10px] font-bold rounded-lg px-2 py-0.5 border ${
                      homoglyphsDetected 
                        ? "text-amber-700 bg-amber-50 border-amber-100" 
                        : "text-emerald-700 bg-emerald-50 border-emerald-100"
                    }`}>
                      {homoglyphsDetected ? "Active" : "Clean"}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-500 leading-normal">
                    Checks for non-Latin symbols (e.g. Cyrillic `а` instead of English `a`) spoofing spelling.
                  </p>
                </div>
              </div>
            </GlassCard>

          </div>

          {/* Right Rules panel */}
          <div>
            <GlassCard className="p-6 md:p-8 h-full space-y-6">
              <div>
                <h3 className="text-sm font-bold text-slate-900 mb-2">Vetted Phish Check Rules</h3>
                <p className="text-xs text-slate-500 leading-relaxed font-medium">
                  Triggered domain registry alerts and active honeypot matches.
                </p>
              </div>

              <div className="space-y-4">
                {!result.triggered_rules || result.triggered_rules.length === 0 ? (
                  <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-100 text-xs text-emerald-700 font-bold flex gap-2">
                    <CheckCircle2 className="h-4 w-4 shrink-0" />
                    <span>Domain compliant. No phishing indicators triggered.</span>
                  </div>
                ) : (
                  result.triggered_rules.map((rule, idx) => (
                    <div key={idx} className="p-4 rounded-2xl border border-slate-200/70 bg-white flex flex-col gap-2.5 shadow-sm hover:border-slate-300 transition-colors">
                      <div className="flex justify-between items-start">
                        <span className="text-xs font-bold text-slate-800 leading-snug">{rule.rule}</span>
                        <ThreatBadge level={getScoreSeverity(rule.score)} />
                      </div>
                      <p className="text-[11px] text-slate-500 leading-normal font-medium">{rule.detail}</p>
                    </div>
                  ))
                )}
              </div>

              <div className="pt-6 border-t border-slate-100 text-[10px] text-slate-400 font-semibold flex items-center gap-1">
                <HelpCircle className="h-3.5 w-3.5" />
                <span>Registry cache sync: Active</span>
              </div>
            </GlassCard>
          </div>

        </div>
      )}

    </div>
  );
}
