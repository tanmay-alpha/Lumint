"use client";

import React, { useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { 
  ShieldAlert, 
  ArrowRight, 
  Search, 
  Binary, 
  Network, 
  Fingerprint, 
  CheckCircle,
  FileCheck,
  AlertTriangle,
  ExternalLink
} from "lucide-react";
import { GlassCard } from "@/components/GlassCard";

export default function Home() {
  const [activeTab, setActiveTab] = useState<"docshield" | "phishshield" | "fraud-dna">("docshield");

  return (
    <div className="min-h-screen bg-[#FBFBFC] relative overflow-hidden font-sans">
      
      {/* Decorative blurred background gradients */}
      <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] rounded-full bg-sky-100/40 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] rounded-full bg-teal-50/40 blur-[120px] pointer-events-none" />

      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-slate-100/80 bg-white/70 backdrop-blur-md px-6 py-4 transition-all">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="rounded-xl bg-slate-900 p-2 text-white">
              <ShieldAlert className="h-5 w-5" />
            </div>
            <span className="text-xl font-bold tracking-tight text-slate-900">
              Sentinel<span className="text-sky-600">X</span>
            </span>
          </div>

          <nav className="hidden md:flex items-center gap-8 text-sm font-semibold text-slate-600">
            <a href="#features" className="hover:text-slate-900 transition-colors">Forensic Suite</a>
            <a href="#workflow" className="hover:text-slate-900 transition-colors">Methodology</a>
            <a href="#why-sentinelx" className="hover:text-slate-900 transition-colors">Threat Intel</a>
          </nav>

          <div className="flex items-center gap-4">
            <Link 
              href="/dashboard"
              className="inline-flex items-center gap-1.5 rounded-full bg-slate-900 hover:bg-slate-800 px-5 py-2 text-sm font-semibold text-white shadow-sm transition-all"
            >
              Access Platform <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative pt-20 pb-24 px-6 grid-bg">
        <div className="max-w-7xl mx-auto flex flex-col items-center text-center">
          
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="inline-flex items-center gap-2 rounded-full border border-sky-100 bg-sky-50/50 px-4 py-1.5 text-xs font-bold text-sky-700 uppercase tracking-wider mb-8"
          >
            <Fingerprint className="h-4 w-4 text-sky-600" /> Enterprise Fraud Forensics Platform
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="text-4xl sm:text-6xl font-extrabold tracking-tight max-w-4xl leading-[1.1] text-slate-900"
          >
            Digital <span className="text-sky-600">Forensics</span> & AI Fraud Intelligence
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="mt-6 text-lg sm:text-xl text-slate-500 max-w-2xl font-medium leading-relaxed"
          >
            Screen documents for metadata alterations, verify lookalike domains, and map fraud fingerprint linkages on a single unified platform.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="mt-10 flex flex-wrap justify-center gap-4"
          >
            <Link
              href="/dashboard"
              className="inline-flex items-center gap-2 rounded-full bg-sky-600 hover:bg-sky-500 text-white font-semibold px-7 py-3.5 shadow-lg shadow-sky-500/10 hover:shadow-sky-500/20 transition-all text-base"
            >
              Launch Core Workspace <ArrowRight className="h-5 w-5" />
            </Link>
            <a
              href="#features"
              className="inline-flex items-center gap-2 rounded-full bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 font-semibold px-7 py-3.5 transition-all text-base"
            >
              Learn More
            </a>
          </motion.div>

          {/* Interactive Composition UI Showcase (3D Depth composition) */}
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.4 }}
            className="relative mt-20 w-full max-w-5xl aspect-[16/9] rounded-2xl border border-slate-200/60 bg-white/80 p-3 shadow-[0_32px_64px_rgba(0,0,0,0.06)] backdrop-blur-sm pointer-events-none select-none"
          >
            <div className="w-full h-full rounded-xl bg-slate-900/5 border border-slate-100 flex items-center justify-center relative overflow-hidden">
              
              {/* Main dashboard glass panel */}
              <div className="absolute inset-x-8 top-8 bottom-8 rounded-xl bg-white border border-slate-100 shadow-[0_4px_24px_rgba(0,0,0,0.02)] flex flex-col p-6 text-left">
                <div className="flex items-center justify-between border-b border-slate-100 pb-4">
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full bg-rose-400" />
                    <span className="w-3 h-3 rounded-full bg-amber-400" />
                    <span className="w-3 h-3 rounded-full bg-emerald-400" />
                    <span className="text-xs font-bold text-slate-400 uppercase tracking-widest ml-4">Workspace / DocShield</span>
                  </div>
                  <span className="text-xs font-semibold text-slate-400 bg-slate-50 border border-slate-100 px-2 py-0.5 rounded-full">Connected</span>
                </div>
                <div className="grid grid-cols-3 gap-6 flex-1 mt-6">
                  <div className="col-span-2 border border-slate-100 rounded-xl p-5 bg-[#FBFBFC] flex flex-col justify-between">
                    <div>
                      <h4 className="text-sm font-bold text-slate-800">Forensics Report: invoice_9821.pdf</h4>
                      <p className="text-xs text-slate-400 mt-1">Uploaded 12 mins ago • Size 2.4MB</p>
                    </div>
                    <div className="space-y-2 mt-4">
                      <div className="flex justify-between items-center bg-white p-2 rounded-lg border border-slate-100/80 text-xs">
                        <span className="text-slate-500">Metadata altered via Acrobat Pro</span>
                        <span className="text-rose-600 font-bold bg-rose-50 px-1.5 py-0.5 rounded">High Risk</span>
                      </div>
                      <div className="flex justify-between items-center bg-white p-2 rounded-lg border border-slate-100/80 text-xs">
                        <span className="text-slate-500">ELA Compression Anomalies detected</span>
                        <span className="text-amber-600 font-bold bg-amber-50 px-1.5 py-0.5 rounded">Suspicious</span>
                      </div>
                    </div>
                  </div>
                  <div className="border border-slate-100 rounded-xl p-5 bg-white flex flex-col items-center justify-center text-center">
                    <span className="text-xs font-bold text-slate-400">THREAT SCORE</span>
                    <span className="text-5xl font-black text-rose-500 mt-2">87</span>
                    <span className="text-xs font-bold text-rose-600 bg-rose-50 px-3 py-1 rounded-full mt-3">HIGH RISK</span>
                  </div>
                </div>
              </div>

              {/* Floating perspective cards (3D effects) */}
              <div className="absolute top-12 right-[-20px] w-64 p-5 rounded-xl border border-white/60 bg-white/70 backdrop-blur-xl shadow-2xl flex flex-col gap-3 transform rotate-2 hover:rotate-0 transition-transform duration-500">
                <div className="flex items-center gap-3">
                  <div className="rounded-lg bg-emerald-50 p-2 text-emerald-600">
                    <CheckCircle className="h-5 w-5" />
                  </div>
                  <div>
                    <h5 className="text-xs font-bold text-slate-800">PhishShield Check</h5>
                    <p className="text-[10px] text-emerald-600 font-medium">Domain match secure</p>
                  </div>
                </div>
              </div>

              <div className="absolute bottom-16 left-[-20px] w-72 p-5 rounded-xl border border-white/60 bg-white/70 backdrop-blur-xl shadow-2xl flex flex-col gap-3 transform -rotate-2 hover:rotate-0 transition-transform duration-500">
                <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                  <span className="text-[10px] font-bold text-slate-400">FRAUD DNA NETWORKS</span>
                  <span className="text-[10px] text-sky-600 font-bold bg-sky-50 px-1.5 rounded">4 active</span>
                </div>
                <div className="flex items-center gap-2 mt-1">
                  <div className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-pulse" />
                  <span className="text-xs font-bold text-slate-700">Campaign: Chase Spoofing</span>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Interactive Capabilities Segment */}
      <section id="features" className="py-24 px-6 bg-white border-y border-slate-100">
        <div className="max-w-7xl mx-auto">
          
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h2 className="text-3xl font-extrabold tracking-tight text-slate-900">
              Complete Forensic Capabilities Suite
            </h2>
            <p className="mt-4 text-slate-500 font-medium">
              Enterprise grade algorithms designed to isolate fraud elements and trace their source DNA networks.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <GlassCard delay={0.1} hoverEffect={true} className="flex flex-col justify-between">
              <div>
                <div className="h-12 w-12 rounded-xl bg-sky-50 text-sky-600 flex items-center justify-center border border-sky-100 mb-6">
                  <FileCheck className="h-6 w-6" />
                </div>
                <h3 className="text-xl font-bold text-slate-900">DocShield</h3>
                <p className="text-sm font-medium text-slate-500 mt-3 leading-relaxed">
                  Analyze invoice documents, passport scans, and corporate agreements. Uncovers hidden metadata modification logs, software signatures, structure anomalies, and localized compression anomalies (ELA) in image text.
                </p>
              </div>
              <Link 
                href="/dashboard/docshield" 
                className="mt-8 text-xs font-bold text-sky-600 hover:text-sky-700 flex items-center gap-1.5 group"
              >
                Launch DocShield <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
              </Link>
            </GlassCard>

            <GlassCard delay={0.2} hoverEffect={true} className="flex flex-col justify-between">
              <div>
                <div className="h-12 w-12 rounded-xl bg-teal-50 text-teal-600 flex items-center justify-center border border-teal-100 mb-6">
                  <Search className="h-6 w-6" />
                </div>
                <h3 className="text-xl font-bold text-slate-900">PhishShield</h3>
                <p className="text-sm font-medium text-slate-500 mt-3 leading-relaxed">
                  Real-time phishing URL inspection engine. Scores risk vectors by running similarity models against brand targets, identifies typosquatting anomalies, analyzes domain age metrics, and parses anchor threat phrases.
                </p>
              </div>
              <Link 
                href="/dashboard/phishshield" 
                className="mt-8 text-xs font-bold text-teal-600 hover:text-teal-700 flex items-center gap-1.5 group"
              >
                Launch PhishShield <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
              </Link>
            </GlassCard>

            <GlassCard delay={0.3} hoverEffect={true} className="flex flex-col justify-between">
              <div>
                <div className="h-12 w-12 rounded-xl bg-slate-100 text-slate-800 flex items-center justify-center border border-slate-200 mb-6">
                  <Network className="h-6 w-6" />
                </div>
                <h3 className="text-xl font-bold text-slate-900">Fraud DNA</h3>
                <p className="text-sm font-medium text-slate-500 mt-3 leading-relaxed">
                  Correlates distinct threat events using similarity clustering. Connects suspicious domains and modified document metadata points to construct interactive campaign graph nodes, helping expose coordinated threat clusters.
                </p>
              </div>
              <Link 
                href="/dashboard/fraud-dna" 
                className="mt-8 text-xs font-bold text-slate-800 hover:text-slate-900 flex items-center gap-1.5 group"
              >
                Launch Fraud DNA <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
              </Link>
            </GlassCard>
          </div>
        </div>
      </section>

      {/* Workflow methodology details */}
      <section id="workflow" className="py-24 px-6 bg-[#FAF9F6]">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <span className="text-xs font-bold text-sky-600 uppercase tracking-widest">Workflow Engine</span>
              <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-900 mt-3">
                How SentinelX Investigates Threats
              </h2>
              <p className="mt-4 text-slate-500 font-medium leading-relaxed">
                SentinelX works by parsing, extracting, analyzing, and correlating threat components to establish a transparent forensic path.
              </p>

              <div className="space-y-6 mt-8">
                <div className="flex gap-4">
                  <div className="w-8 h-8 rounded-full bg-slate-900 text-white flex items-center justify-center shrink-0 font-bold text-sm">1</div>
                  <div>
                    <h4 className="font-bold text-slate-800">Signal Extraction</h4>
                    <p className="text-sm text-slate-500 mt-1 font-medium">Extract raw indicators (EXIF, hashes, structural features, network addresses).</p>
                  </div>
                </div>
                <div className="flex gap-4">
                  <div className="w-8 h-8 rounded-full bg-slate-900 text-white flex items-center justify-center shrink-0 font-bold text-sm">2</div>
                  <div>
                    <h4 className="font-bold text-slate-800">Heuristics & AI Screening</h4>
                    <p className="text-sm text-slate-500 mt-1 font-medium">Compare indices against similarity benchmarks, active rulesets, and anomaly metrics.</p>
                  </div>
                </div>
                <div className="flex gap-4">
                  <div className="w-8 h-8 rounded-full bg-slate-900 text-white flex items-center justify-center shrink-0 font-bold text-sm">3</div>
                  <div>
                    <h4 className="font-bold text-slate-800">Fraud Clustering (DNA)</h4>
                    <p className="text-sm text-slate-500 mt-1 font-medium">Run DB clustering logic to map threats to coordinated attack campaigns.</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Premium layered visualization panel */}
            <div className="relative p-6 rounded-2xl bg-white border border-slate-100 shadow-xl overflow-hidden aspect-[4/3] flex flex-col justify-between">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <span className="text-xs font-bold text-slate-400">ANALYSIS FLOW LOG</span>
                <span className="text-xs font-bold text-sky-600 bg-sky-50 px-2.5 py-0.5 rounded-full">ACTIVE</span>
              </div>
              <div className="space-y-3 my-6 flex-1 overflow-y-auto">
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-100 font-mono text-[10px] text-slate-600 space-y-1">
                  <p className="text-sky-600 font-bold">[SYS] Parsing invoice_9821.pdf</p>
                  <p>[HASH] SHA256: 8f9a3e2b1c0d4e5f6a7b8c9d0...</p>
                  <p className="text-rose-600 font-bold">[WARN] Modification detected: Creator field spoofed</p>
                </div>
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-100 font-mono text-[10px] text-slate-600 space-y-1">
                  <p className="text-sky-600 font-bold">[NET] Verifying chase-security-verify.net</p>
                  <p>[TYPO] Similarity score to chase.com: 0.92</p>
                  <p className="text-rose-600 font-bold">[WARN] Suspicious URL: Block recommendation issued</p>
                </div>
              </div>
              <div className="border-t border-slate-100 pt-3 flex justify-between items-center">
                <span className="text-xs font-bold text-slate-500">Threat Cluster Connected</span>
                <span className="text-xs font-bold text-rose-600 bg-rose-50 px-2 py-0.5 rounded">Campaign #cmp-chase</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer CTA */}
      <footer className="bg-slate-900 text-white py-16 px-6 relative overflow-hidden">
        <div className="max-w-7xl mx-auto flex flex-col items-center text-center relative z-10">
          <div className="rounded-2xl bg-white/10 p-3.5 mb-6 text-white backdrop-blur-md border border-white/10">
            <ShieldAlert className="h-8 w-8 text-sky-400" />
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight max-w-2xl">
            Upgrade Your Cyber Forensics Operations
          </h2>
          <p className="mt-4 text-slate-400 max-w-md font-medium text-sm sm:text-base">
            Integrate real-time document validation, URL screening, and campaigns graphing into your response pipeline.
          </p>
          <div className="mt-10 flex gap-4">
            <Link
              href="/dashboard"
              className="inline-flex items-center gap-2 rounded-full bg-sky-600 hover:bg-sky-500 text-white font-bold px-8 py-3.5 shadow-lg shadow-sky-500/20 transition-all text-sm"
            >
              Open Console Dashboard <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
          <p className="mt-16 text-xs text-slate-500 font-semibold tracking-wider">
            SENTINELX FORENSICS © 2026. ALL RIGHTS RESERVED.
          </p>
        </div>
      </footer>
    </div>
  );
}
