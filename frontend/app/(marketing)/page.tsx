"use client";

import React from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  ArrowRight,
  Shield,
  Link2,
  GitBranch,
  Smartphone,
  FileText,
  Zap,
  BookOpen,
  CheckCircle,
} from "lucide-react";
import { DataCard } from "@/components/ui/DataCard";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";

// ─── Animation helpers ─────────────────────────────────────────────────────
const fadeUp = {
  hidden:  { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5 } },
};
const stagger = { visible: { transition: { staggerChildren: 0.08 } } };

// ─── Floating hero composition card ───────────────────────────────────────
const HeroPreviewCard = ({
  label,
  value,
  badge,
  badgeRisk,
  delay,
  rotate,
}: {
  label: string;
  value: string;
  badge: string;
  badgeRisk: "danger" | "warn" | "safe" | "critical" | "low" | "default";
  delay: number;
  rotate: number;
}) => (
  <motion.div
    initial={{ opacity: 0, y: 20, rotate: 0 }}
    animate={{ opacity: 1, y: 0, rotate }}
    transition={{ duration: 0.6, delay }}
    className="bg-surface/90 backdrop-blur-md border border-border-default rounded-xl px-4 py-3.5 shadow-md min-w-[200px]"
    style={{ transform: `rotate(${rotate}deg)` }}
  >
    <span className="text-label text-text-muted block mb-1">
      {label}
    </span>
    <span className="text-data text-text-primary block font-semibold truncate mb-2">{value}</span>
    <Badge variant={badgeRisk} dot>
      {badge}
    </Badge>
  </motion.div>
);

const FeatureCard = ({
  icon: Icon,
  title,
  description,
  href,
}: {
  icon: React.ElementType;
  title: string;
  description: string;
  href: string;
}) => (
  <DataCard className="flex flex-col gap-4 group cursor-pointer h-full border border-border-default/60 hover:border-brand/40 transition-all duration-300">
    <div className="h-11 w-11 rounded-xl bg-brand-subtle flex items-center justify-center text-brand">
      <Icon className="h-[22px] w-[22px]" />
    </div>
    <div>
      <h3 className="text-title text-text-primary mb-2">{title}</h3>
      <p className="text-body text-text-secondary leading-relaxed">{description}</p>
    </div>
    <div className="mt-auto pt-4 flex flex-col gap-3">
      <Link
        href={href}
        className="flex items-center gap-1 text-[13px] font-semibold text-brand hover:gap-2 transition-all"
      >
        Open module <ArrowRight className="h-3.5 w-3.5" />
      </Link>
      <div className="pt-3 border-t border-border-muted/65">
        <span className="font-mono text-[10px] text-text-muted">
          Powered by LLaMA 3.3 70B · Groq
        </span>
      </div>
    </div>
  </DataCard>
);

// ─────────────────────────────────────────────────────────────────────────────
// LANDING PAGE
// ─────────────────────────────────────────────────────────────────────────────
export default function LandingPage() {
  return (
    <div className="relative min-h-screen bg-canvas text-text-primary flex flex-col font-sans">
      {/* ── NAVBAR ── */}
      <nav className="fixed top-0 inset-x-0 z-50 border-b border-border-default bg-surface/80 backdrop-blur-[12px]">
        <div className="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="h-8 w-8 rounded-lg bg-brand flex items-center justify-center shadow-sm">
              <Zap className="h-4.5 w-4.5 text-white" strokeWidth={2.5} />
            </div>
            <span className="text-display text-[22px] tracking-tight font-semibold text-text-primary leading-none">Lumint</span>
          </div>
          <div className="hidden md:flex items-center gap-6 text-[13px] text-text-secondary font-medium">
            <a href="#modules" className="hover:text-text-primary transition-colors">Modules</a>
            <a href="#research" className="hover:text-text-primary transition-colors">Research</a>
            <a
              href="https://github.com/tanmay-alpha"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-text-primary transition-colors"
            >
              GitHub
            </a>
            <a
              href="https://www.linkedin.com/in/tanmaymangal/"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-text-primary transition-colors"
            >
              LinkedIn
            </a>
          </div>
          <Link href="/dashboard">
            <Button variant="solid" size="sm" className="flex items-center gap-1.5 font-semibold text-[13px]">
              Launch Platform <ArrowRight className="h-3.5 w-3.5" />
            </Button>
          </Link>
        </div>
      </nav>

      <main className="flex-grow pt-14">
        {/* ── HERO ── */}
        <section className="relative min-h-[92vh] flex items-center overflow-hidden">
          {/* Decorative grid & background patterns */}
          <div className="absolute inset-0 mesh-grid-bg opacity-[0.018] pointer-events-none" />
          <div className="absolute inset-0 hero-mesh-bg pointer-events-none" />
          
          <div className="absolute top-20 right-20 w-96 h-96 rounded-full bg-brand/5 dark:bg-brand/10 opacity-30 blur-3xl pointer-events-none" />
          <div className="absolute bottom-20 left-10 w-80 h-80 rounded-full bg-intel/5 dark:bg-intel/10 opacity-30 blur-3xl pointer-events-none" />

          <div className="max-w-7xl mx-auto px-6 w-full grid grid-cols-1 lg:grid-cols-2 items-center gap-16 py-20 relative z-10">
            {/* Left — copy */}
            <motion.div
              initial="hidden"
              animate="visible"
              variants={stagger}
              className="space-y-6"
            >
              {/* Badge */}
              <motion.div variants={fadeUp}>
                <span className="inline-flex items-center gap-1.5 px-3.5 py-1 rounded-full bg-brand-subtle text-brand text-[12px] font-semibold">
                  <Zap className="h-3.5 w-3.5" strokeWidth={2.5} />
                  Research Publication Platform · v1.0.0
                </span>
              </motion.div>

              {/* Headline */}
              <motion.h1 variants={fadeUp} className="text-display tracking-tight leading-[1.05] text-text-primary" style={{ fontSize: 54 }}>
                Illuminate the threat.{" "}
                <span className="text-brand italic font-serif">Before it strikes.</span>
              </motion.h1>

              {/* Body */}
              <motion.p
                variants={fadeUp}
                className="text-body text-text-secondary leading-relaxed max-w-lg"
                style={{ fontSize: 16 }}
              >
                Lumint is a unified multimodal fraud intelligence platform built for India&apos;s
                digital payment ecosystem — detecting fraud across documents, URLs, UPI screenshots,
                and campaign networks using LLM-powered explainability.
              </motion.p>

              {/* CTAs */}
              <motion.div variants={fadeUp} className="flex items-center gap-4 flex-wrap">
                <Link href="/dashboard">
                  <Button variant="solid" size="lg" className="flex items-center gap-2 font-semibold">
                    Launch Platform <ArrowRight className="h-4.5 w-4.5" />
                  </Button>
                </Link>
                <a href="#research">
                  <Button variant="outline" size="lg" className="flex items-center gap-2 font-semibold">
                    <BookOpen className="h-4.5 w-4.5" />
                    Read Research
                  </Button>
                </a>
              </motion.div>

              {/* Trust stats */}
              <motion.div variants={fadeUp} className="flex items-center gap-5 flex-wrap pt-4 border-t border-border-muted/70">
                {[
                  { value: "4 modules",     label: "Detection modalities" },
                  { value: "LLaMA 3.3 70B", label: "AI engine" },
                  { value: "Open source",   label: "Research ready" },
                ].map(({ value, label }) => (
                  <div key={label} className="flex items-center gap-2 text-caption">
                    <CheckCircle className="h-4.5 w-4.5 text-risk-none shrink-0" />
                    <span className="font-semibold text-text-primary">{value}</span>
                    <span className="text-text-muted">{label}</span>
                  </div>
                ))}
              </motion.div>
            </motion.div>

            {/* Right — floating preview cards */}
            <div className="relative hidden lg:flex items-center justify-center h-[420px]">
              <div className="relative w-full h-full max-w-[400px]">
                <motion.div
                  animate={{ y: [0, -8, 0] }}
                  transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
                  className="absolute top-8 right-0"
                >
                  <HeroPreviewCard
                    label="DocShield result"
                    value="Invoiced forgery detected"
                    badge="HIGH THREAT"
                    badgeRisk="danger"
                    delay={0.3}
                    rotate={2}
                  />
                </motion.div>
                <motion.div
                  animate={{ y: [0, -6, 0] }}
                  transition={{ duration: 3.5, repeat: Infinity, ease: "easeInOut", delay: 0.5 }}
                  className="absolute top-1/2 left-0 -translate-y-1/2"
                >
                  <HeroPreviewCard
                    label="PhishShield verdict"
                    value="hdfc-kyc-verify.com"
                    badge="PHISHING LINK"
                    badgeRisk="critical"
                    delay={0.5}
                    rotate={-3}
                  />
                </motion.div>
                <motion.div
                  animate={{ y: [0, -10, 0] }}
                  transition={{ duration: 4, repeat: Infinity, ease: "easeInOut", delay: 1 }}
                  className="absolute bottom-6 right-4"
                >
                  <HeroPreviewCard
                    label="UPI Shield scan"
                    value="UTR Format invalid ✗"
                    badge="FORGED SCREENSHOT"
                    badgeRisk="danger"
                    delay={0.7}
                    rotate={1.5}
                  />
                </motion.div>
              </div>
            </div>
          </div>
        </section>

        {/* ── MODULES ── */}
        <section id="modules" className="py-24 px-6 max-w-7xl mx-auto border-t border-border-muted/50">
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.2 }}
            variants={stagger}
            className="space-y-14"
          >
            <motion.div variants={fadeUp} className="max-w-2xl">
              <h2 className="text-headline text-text-primary mb-4" style={{ fontSize: 38 }}>
                Four detection modalities. One platform.
              </h2>
              <p className="text-body text-text-secondary leading-relaxed" style={{ fontSize: 16 }}>
                Each module is independently capable yet designed to work as a unified pipeline —
                cross-correlating signals across all modalities via the Fraud DNA graph.
              </p>
            </motion.div>

            <motion.div variants={stagger} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              <motion.div variants={fadeUp}>
                <FeatureCard
                  icon={FileText}
                  title="DocShield"
                  description="Detect tampered invoices, forged salary slips, and edited government IDs using ELA forensics and font analysis."
                  href="/docshield"
                />
              </motion.div>
              <motion.div variants={fadeUp}>
                <FeatureCard
                  icon={Link2}
                  title="PhishShield"
                  description="Identify lookalike bank domains, UPI phishing URLs, and KYC scam links with SHAP-explained risk scores."
                  href="/phishshield"
                />
              </motion.div>
              <motion.div variants={fadeUp}>
                <FeatureCard
                  icon={GitBranch}
                  title="Fraud DNA"
                  description="Visualize fraud campaign networks — cluster events by shared indicators, domains, and file hashes."
                  href="/fraud-dna"
                />
              </motion.div>
              <motion.div variants={fadeUp}>
                <FeatureCard
                  icon={Smartphone}
                  title="UPI Shield"
                  description="Verify PhonePe, Google Pay, and Paytm payment screenshots using OCR, ELA, and LLM forensic analysis."
                  href="/upi-shield"
                />
              </motion.div>
            </motion.div>
          </motion.div>
        </section>

        {/* ── RESEARCH ── */}
        <section id="research" className="py-24 px-6 bg-surface-raised border-y border-border-default">
          <div className="max-w-7xl mx-auto">
            <motion.div
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.2 }}
              variants={stagger}
              className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-start"
            >
              <motion.div variants={fadeUp} className="space-y-4">
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-brand-subtle text-brand text-[12px] font-semibold">
                  <BookOpen className="h-3.5 w-3.5" />
                  Academic Excellence
                </span>
                <h2 className="text-headline text-text-primary leading-tight" style={{ fontSize: 38 }}>
                  Novelty claims confirmed by literature review
                </h2>
                <p className="text-body text-text-secondary leading-relaxed" style={{ fontSize: 15 }}>
                  Three confirmed research gaps from systematic review of 2024–2025 papers make Lumint
                  a strong candidate for ACM CIKM, IEEE Access, and AMLTA conference tracks.
                </p>
              </motion.div>
              <motion.div variants={stagger} className="space-y-3.5">
                {[
                  "First system combining document forensics + URL phishing + UPI screenshot detection in one pipeline",
                  "First use of LLM (Groq/LLaMA) to generate natural-language explanations for fraud scores — not just scores",
                  "SHAP + LLM fusion: machine explainability + human-readable narrative in the same system",
                  "India-specific: UTR format validation, PhonePe/GPay screenshot forensics — no paper covers this combination",
                  "Cross-modal correlation: same attacker's document + phishing domain linked via Fraud DNA graph",
                  "Working open-source system (GitHub) — most papers are theoretical; this has a real demo",
                ].map((claim, i) => (
                  <motion.div
                    key={i}
                    variants={fadeUp}
                    className="flex items-start gap-3.5 p-4 rounded-xl bg-surface border border-border-default/60 shadow-sm"
                  >
                    <CheckCircle className="h-5 w-5 text-risk-none mt-0.5 shrink-0" />
                    <span className="text-body text-text-secondary leading-relaxed">{claim}</span>
                  </motion.div>
                ))}
              </motion.div>
            </motion.div>
          </div>
        </section>

        {/* ── CTA ── */}
        <section className="py-28 px-6">
          <div className="max-w-4xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5 }}
              className="rounded-[24px] bg-text-primary p-12 text-center text-text-inverse relative overflow-hidden"
            >
              <div className="absolute inset-0 bg-gradient-to-tr from-brand/20 to-transparent pointer-events-none" />
              
              <div className="relative z-10">
                <div className="inline-flex items-center justify-center h-14 w-14 rounded-2xl bg-white/10 mb-6 border border-white/10">
                  <Shield className="h-7 w-7 text-white" />
                </div>
                <h2 className="text-display text-white mb-4" style={{ fontSize: 38 }}>
                  Start analyzing threats
                </h2>
                <p className="text-body text-white/70 mb-8 max-w-xl mx-auto leading-relaxed" style={{ fontSize: 15 }}>
                  Lumint is open-source and ready to use. Launch the platform, upload a document or URL,
                  and get an AI-powered forensic report in seconds.
                </p>
                <div className="flex items-center justify-center gap-4 flex-wrap">
                  <Link href="/dashboard">
                    <Button variant="solid" size="lg" className="bg-brand text-white border-transparent hover:bg-brand-hover">
                      Launch Platform <ArrowRight className="h-4.5 w-4.5" />
                    </Button>
                  </Link>
                </div>
              </div>
            </motion.div>
          </div>
        </section>
      </main>

      {/* ── FOOTER ── */}
      <footer className="border-t border-border-default bg-surface py-10 px-6 mt-auto">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-5 text-caption text-text-muted">
          <div className="flex items-center gap-2.5 select-none">
            <div className="h-7 w-7 rounded-lg bg-text-primary flex items-center justify-center">
              <Zap className="h-4 w-4 text-white" strokeWidth={2.5} />
            </div>
            <span className="text-display text-[18px] font-semibold text-text-primary leading-none">Lumint</span>
            <span className="font-mono text-[10px] border border-border-default px-1.5 py-0.5 rounded text-text-muted">
              v1.0.0
            </span>
          </div>
          <div className="flex items-center gap-6 font-medium">
            <a href="#modules" className="hover:text-text-primary transition-colors">Modules</a>
            <a href="#research" className="hover:text-text-primary transition-colors">Research</a>
            <a
              href="https://github.com/tanmay-alpha"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-text-primary transition-colors"
            >
              GitHub
            </a>
            <a
              href="https://www.linkedin.com/in/tanmaymangal/"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-text-primary transition-colors"
            >
              LinkedIn
            </a>
          </div>
          <span>© {new Date().getFullYear()} Lumint Research. All rights reserved.</span>
        </div>
      </footer>
    </div>
  );
}
