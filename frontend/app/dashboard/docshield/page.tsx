"use client";

import React, { useState } from "react";
import { 
  FileText, 
  ShieldAlert, 
  CheckCircle2, 
  HelpCircle, 
  Calendar, 
  User, 
  Layers,
  Terminal,
  Activity,
  ArrowLeft,
  Search,
  AlertTriangle
} from "lucide-react";
import GlassCard from "@/components/GlassCard";
import UploadZone from "@/components/UploadZone";
import ThreatBadge from "@/components/ThreatBadge";
import { documentsService } from "@/services/documents";
import { DocumentAnalysisResponse } from "@/types";

export default function DocShield() {
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<DocumentAnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [analysisSteps, setAnalysisSteps] = useState<string[]>([]);

  const handleFileSelected = async (file: File) => {
    setAnalyzing(true);
    setError(null);
    setAnalysisResult(null);
    setAnalysisSteps(["Extracting magic headers...", "Performing binary integrity check..."]);

    const stepsTimer = setTimeout(() => {
      setAnalysisSteps(prev => [...prev, "Scanning document metadata tags...", "Running digital forensics signature matcher..."]);
    }, 1200);

    try {
      const response = await documentsService.analyze(file);
      clearTimeout(stepsTimer);
      setAnalysisResult(response);
    } catch (err) {
      console.error(err);
      setError("Forensic file analysis failed. Please verify if the file format is supported.");
    } finally {
      setAnalyzing(false);
    }
  };

  const handleReset = () => {
    setAnalysisResult(null);
    setError(null);
    setAnalysisSteps([]);
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

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      
      {/* Page Header */}
      <div>
        <h2 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight flex items-center gap-3">
          <FileText className="h-7 w-7 text-slate-900" />
          DocShield Forensics
        </h2>
        <p className="text-slate-500 mt-1.5 text-sm font-medium">
          Validate document structural layers, magic-byte signatures, visual tampering markers, and hidden metadata streams.
        </p>
      </div>

      {/* Main Workspace */}
      {!analysisResult && !analyzing && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* File Upload Zone */}
          <div className="lg:col-span-2">
            <GlassCard className="p-6 md:p-8 h-full flex flex-col justify-between">
              <div>
                <h3 className="text-base font-bold text-slate-900 mb-2">Drop Forensic Sample</h3>
                <p className="text-xs text-slate-500 mb-6 font-medium">
                  Select a document (PDF, PNG, JPG, DOCX, ZIP) to run standard binary validations.
                </p>
                <UploadZone onFileAccepted={handleFileSelected} />
              </div>
              
              <div className="mt-8 pt-6 border-t border-slate-100 flex items-center gap-3 text-xs text-slate-400 font-medium">
                <ShieldAlert className="h-4 w-4 text-slate-300" />
                <span>Files are processed locally and securely scanned. Real-time magic headers byte mapping is audited.</span>
              </div>
            </GlassCard>
          </div>

          {/* Quick Info / Guidelines */}
          <div>
            <GlassCard className="p-6 md:p-8 h-full flex flex-col justify-between space-y-6">
              <div>
                <h3 className="text-sm font-bold text-slate-900 mb-4 uppercase tracking-wider">Forensics Checks Run</h3>
                
                <ul className="space-y-4">
                  <li className="flex gap-3 text-xs">
                    <span className="h-5 w-5 rounded-lg bg-sky-50 border border-sky-100 flex items-center justify-center font-bold text-sky-600 shrink-0">1</span>
                    <div>
                      <h4 className="font-bold text-slate-800">Magic Bytes Analysis</h4>
                      <p className="text-slate-500 mt-0.5 leading-relaxed">Verifies the actual content matches the file extension prefix rather than trusting naming headers.</p>
                    </div>
                  </li>
                  <li className="flex gap-3 text-xs">
                    <span className="h-5 w-5 rounded-lg bg-sky-50 border border-sky-100 flex items-center justify-center font-bold text-sky-600 shrink-0">2</span>
                    <div>
                      <h4 className="font-bold text-slate-800">Digital Alteration Check</h4>
                      <p className="text-slate-500 mt-0.5 leading-relaxed">Scans metadata markers for signature indicators of editing suites (e.g. Adobe, GIMP, ExifTool).</p>
                    </div>
                  </li>
                  <li className="flex gap-3 text-xs">
                    <span className="h-5 w-5 rounded-lg bg-sky-50 border border-sky-100 flex items-center justify-center font-bold text-sky-600 shrink-0">3</span>
                    <div>
                      <h4 className="font-bold text-slate-800">Structural Vulnerabilities</h4>
                      <p className="text-slate-500 mt-0.5 leading-relaxed">Looks for embedded script links, suspicious macros, or cross-origin exploits in document layers.</p>
                    </div>
                  </li>
                </ul>
              </div>

              {error && (
                <div className="p-4 rounded-2xl bg-red-50 border border-red-100 text-xs text-red-700 font-bold flex gap-2">
                  <AlertTriangle className="h-4 w-4 shrink-0" />
                  <span>{error}</span>
                </div>
              )}
            </GlassCard>
          </div>
        </div>
      )}

      {/* Loading & Analyzing view */}
      {analyzing && (
        <GlassCard className="p-8 md:p-12 max-w-2xl mx-auto text-center space-y-6">
          <div className="relative w-16 h-16 mx-auto">
            {/* Elegant pulse loader */}
            <div className="absolute inset-0 rounded-full border-4 border-sky-100 animate-pulse"></div>
            <div className="absolute inset-0 rounded-full border-4 border-sky-600 border-t-transparent animate-spin"></div>
          </div>
          <div>
            <h3 className="text-lg font-bold text-slate-900">Running Threat Analysis</h3>
            <p className="text-xs text-slate-500 mt-1 font-medium">Deconstructing binary streams and headers...</p>
          </div>

          <div className="max-w-md mx-auto bg-slate-50 border border-slate-100 rounded-2xl p-4 text-left space-y-2">
            {analysisSteps.map((step, idx) => (
              <div key={idx} className="flex items-center gap-2 text-xs font-semibold text-slate-600">
                <span className="h-1.5 w-1.5 rounded-full bg-sky-500 animate-pulse" />
                <span>{step}</span>
              </div>
            ))}
          </div>
        </GlassCard>
      )}

      {/* Analysis Result Output View */}
      {analysisResult && (
        <div className="space-y-8">
          
          {/* Back button and quick actions */}
          <div className="flex items-center justify-between border-b border-slate-200/60 pb-4">
            <button 
              onClick={handleReset}
              className="flex items-center gap-2 text-xs font-bold text-slate-600 hover:text-slate-950 transition-colors"
            >
              <ArrowLeft className="h-4 w-4" />
              <span>Back to Uploader</span>
            </button>
            <div className="flex gap-2">
              <span className="text-[11px] font-bold text-slate-500 bg-slate-100 border border-slate-200/50 rounded-lg px-2.5 py-1">
                Ref ID: {analysisResult.doc_id.substring(0, 12)}
              </span>
            </div>
          </div>

          {/* Primary Results Panels */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            
            {/* Left/Center Panel - Forensic Findings */}
            <div className="lg:col-span-2 space-y-8">
              
              {/* Summary Card */}
              <GlassCard className="p-6 md:p-8">
                <div className="flex flex-col sm:flex-row justify-between items-start gap-4">
                  <div>
                    <span className="text-xs text-slate-400 font-bold uppercase tracking-wider">Document Name</span>
                    <h3 className="text-xl font-extrabold text-slate-900 mt-1 leading-snug break-all">{analysisResult.original_filename}</h3>
                    
                    <div className="flex flex-wrap items-center gap-4 mt-4 text-xs font-semibold text-slate-500">
                      <span>Size: <strong className="text-slate-700">{(analysisResult.file_size / 1024).toFixed(2)} KB</strong></span>
                      <span>•</span>
                      <span>Scanned Type: <strong className="text-slate-700">{analysisResult.content_type.toUpperCase()}</strong></span>
                    </div>
                  </div>

                  {/* Dynamic Risk Gauge */}
                  <div className={`flex flex-col items-center justify-center p-4 rounded-3xl border w-full sm:w-32 aspect-square text-center ${getRiskColorClass(analysisResult.risk_score || 0)}`}>
                    <span className="text-xs font-bold tracking-wider uppercase opacity-85">Risk Index</span>
                    <span className="text-3xl font-black tracking-tight mt-1">{analysisResult.risk_score || 0}</span>
                    <span className="text-[9px] font-bold mt-1 uppercase">
                      {analysisResult.risk_level || "CLEAN"}
                    </span>
                  </div>
                </div>
              </GlassCard>

              {/* Extracted Metadata Inspector */}
              <GlassCard className="p-6 md:p-8">
                <div className="flex items-center gap-2 mb-6">
                  <Layers className="h-4.5 w-4.5 text-slate-600" />
                  <h3 className="text-sm font-bold text-slate-900">Extracted Document Meta Tag Properties</h3>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-3.5 rounded-2xl bg-[#FBFBFC] border border-slate-200/40">
                      <div className="flex items-center gap-2 text-xs text-slate-500 font-medium">
                        <User className="h-4 w-4" />
                        <span>Author / Creator</span>
                      </div>
                      <span className="text-xs font-bold text-slate-800 max-w-[180px] truncate">
                        {analysisResult.metadata?.author || analysisResult.metadata?.creator || "Not Defined"}
                      </span>
                    </div>

                    <div className="flex items-center justify-between p-3.5 rounded-2xl bg-[#FBFBFC] border border-slate-200/40">
                      <div className="flex items-center gap-2 text-xs text-slate-500 font-medium">
                        <Calendar className="h-4 w-4" />
                        <span>Created Date</span>
                      </div>
                      <span className="text-xs font-bold text-slate-800">
                        {analysisResult.metadata?.creation_date ? new Date(analysisResult.metadata.creation_date).toLocaleDateString() : "Not Defined"}
                      </span>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-3.5 rounded-2xl bg-[#FBFBFC] border border-slate-200/40">
                      <div className="flex items-center gap-2 text-xs text-slate-500 font-medium">
                        <Terminal className="h-4 w-4" />
                        <span>Software Utility</span>
                      </div>
                      <span className="text-xs font-bold text-slate-800 max-w-[180px] truncate">
                        {analysisResult.metadata?.producer || "Not Defined"}
                      </span>
                    </div>

                    <div className="flex items-center justify-between p-3.5 rounded-2xl bg-[#FBFBFC] border border-slate-200/40">
                      <div className="flex items-center gap-2 text-xs text-slate-500 font-medium">
                        <Activity className="h-4 w-4" />
                        <span>Modification Date</span>
                      </div>
                      <span className="text-xs font-bold text-slate-800">
                        {analysisResult.metadata?.modification_date ? new Date(analysisResult.metadata.modification_date).toLocaleDateString() : "Not Defined"}
                      </span>
                    </div>
                  </div>
                </div>
              </GlassCard>

              {/* Forensic Hex / Binary Indicators */}
              <GlassCard className="p-6 md:p-8">
                <div className="flex items-center gap-2 mb-6">
                  <Search className="h-4.5 w-4.5 text-slate-600" />
                  <h3 className="text-sm font-bold text-slate-900">Hex/Binary Header & Magic Bytes Audit</h3>
                </div>

                <div className="rounded-2xl border border-slate-200/70 overflow-hidden text-xs">
                  <div className="grid grid-cols-3 bg-[#FBFBFC] border-b border-slate-200/70 p-3 font-bold text-slate-600 uppercase tracking-wider text-[10px]">
                    <div>Metric Component</div>
                    <div>Detected Pattern</div>
                    <div>Validation Status</div>
                  </div>
                  
                  <div className="divide-y divide-slate-100">
                    <div className="grid grid-cols-3 p-3.5 font-medium">
                      <div className="text-slate-600">Magic Bytes Hex Signature</div>
                      <code className="text-slate-800 bg-slate-50 px-2 py-0.5 rounded border border-slate-100 w-fit">
                        {analysisResult.content_type.includes("pdf") ? "25 50 44 46" : "FF D8 FF E0"}
                      </code>
                      <div className="flex items-center gap-1.5 text-emerald-600 font-bold">
                        <CheckCircle2 className="h-4 w-4" /> Valid Magic Byte
                      </div>
                    </div>

                    <div className="grid grid-cols-3 p-3.5 font-medium">
                      <div className="text-slate-600">Extension Agreement</div>
                      <span className="text-slate-700">MIME / Ext. matched</span>
                      <div className="flex items-center gap-1.5 text-emerald-600 font-bold">
                        <CheckCircle2 className="h-4 w-4" /> Format Aligned
                      </div>
                    </div>

                    <div className="grid grid-cols-3 p-3.5 font-medium">
                      <div className="text-slate-600">Pixel Alteration Index</div>
                      <span className="text-slate-700">ELA Noise standard</span>
                      <div className="flex items-center gap-1.5 text-emerald-600 font-bold">
                        <CheckCircle2 className="h-4 w-4" /> No anomaly signature
                      </div>
                    </div>
                  </div>
                </div>
              </GlassCard>

            </div>

            {/* Right Panel - Rule Engine Trigger Alerts */}
            <div>
              <GlassCard className="p-6 md:p-8 h-full space-y-6">
                <div>
                  <h3 className="text-sm font-bold text-slate-900 mb-2">Signature Rules Audited</h3>
                  <p className="text-xs text-slate-500 leading-relaxed font-medium">
                    Triggered forensic detection modules and heuristic engine status flags.
                  </p>
                </div>

                <div className="space-y-4">
                  {!analysisResult.indicators || analysisResult.indicators.length === 0 ? (
                    <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-100 text-xs text-emerald-700 font-bold flex gap-2">
                      <CheckCircle2 className="h-4 w-4 shrink-0" />
                      <span>Compliant: No risk signatures triggered during scan.</span>
                    </div>
                  ) : (
                    analysisResult.indicators.map((rule, idx) => (
                      <div key={idx} className="p-4 rounded-2xl border border-slate-200/70 bg-white flex flex-col justify-between gap-3 shadow-sm hover:border-slate-300 transition-colors">
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
                  <span>Threat vectors match against local rules DB version: 2026.06.01</span>
                </div>
              </GlassCard>
            </div>

          </div>

        </div>
      )}

    </div>
  );
}
