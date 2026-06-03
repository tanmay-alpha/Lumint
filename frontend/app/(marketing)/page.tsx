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
import { GlassCard } from "@/components/ui/GlassCard";

// ─── Animation helpers ─────────────────────────────────────────────────────
const fadeUp = {
  hidden:  { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5 } },
};
const stagger = { visible: { transition: { staggerChildren: 0.1 } } };

// ─── Floating hero composition card ───────────────────────────────────────
const HeroPreviewCard = ({
  label,
  value,
  badge,
  badgeColor,
  delay,
  rotate,
}: {
  label: string;
  value: string;
  badge: string;
  badgeColor: string;
  delay: number;
  rotate: number;
}) => (
  <motion.div
    initial={{ opacity: 0, y: 20, rotate: 0 }}
    animate={{ opacity: 1, y: 0, rotate }}
    transition={{ duration: 0.6, delay }}
    className="glass rounded-[14px] px-4 py-3 shadow-2 min-w-[180px]"
    style={{ transform: `rotate(${rotate}deg)` }}
  >
    <p className="text-[10px] font-semibold tracking-wider text-[var(--color-text-muted)] uppercase mb-1">
      {label}
    </p>
    <p className="font-mono text-[15px] font-semibold text-[var(--color-text-primary)]">{value}</p>
    <span
      className="inline-block mt-2 rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider"
      style={{ background: badgeColor + "22", color: badgeColor }}
    >
      {badge}
    </span>
  </motion.div>
);

// ─── Module feature card ───────────────────────────────────────────────────
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
  <GlassCard elevated className="p-6 flex flex-col gap-4 group cursor-pointer">
    <div className="h-11 w-11 rounded-xl bg-[var(--color-accent-subtle)] flex items-center justify-center text-[var(--color-accent)]">
      <Icon className="h-5.5 w-5.5" />
    </div>
    <div>
      <h3 className="text-[16px] font-semibold text-[var(--color-text-primary)] mb-1.5">{title}</h3>
      <p className="text-[13px] text-[var(--color-text-secondary)] leading-relaxed">{description}</p>
    </div>
    <Link
      href={href}
      className="mt-auto flex items-center gap-1 text-[12px] font-semibold text-[var(--color-accent)] hover:gap-2 transition-all"
    >
      Open module <ArrowRight className="h-3 w-3" />
    </Link>
    <div className="mt-3 pt-3 border-t border-[var(--color-border)]">
      <span className="font-mono text-[10px] text-[var(--color-text-muted)]">
        Powered by LLaMA 3.3 70B · Groq
      </span>
    </div>
  </GlassCard>
);

// ─────────────────────────────────────────────────────────────────────────────
// LANDING PAGE
// ─────────────────────────────────────────────────────────────────────────────
export default function LandingPage() {
  return (
    <>
      {/* ── NAVBAR ── */}
      <nav className="fixed top-0 inset-x-0 z-50 border-b border-[var(--color-border)] bg-[rgba(247,248,250,0.82)] backdrop-blur-[12px]">
        <div className="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="h-7 w-7 rounded-lg bg-[var(--color-text-primary)] flex items-center justify-center">
              <Zap className="h-4 w-4 text-white" strokeWidth={2.5} />
            </div>
            <span className="font-display text-[20px] text-[var(--color-text-primary)]">Lumint</span>
          </div>
          <div className="hidden md:flex items-center gap-6 text-[13px] text-[var(--color-text-secondary)]">
            <a href="#modules" className="hover:text-[var(--color-text-primary)] transition-colors">Modules</a>
            <a href="#research" className="hover:text-[var(--color-text-primary)] transition-colors">Research</a>
            <a
              href="https://github.com/tanmay-alpha/Lumint"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-[var(--color-text-primary)] transition-colors"
            >
              GitHub
            </a>
          </div>
          <Link
            href="/dashboard"
            className="flex items-center gap-1.5 text-[13px] font-semibold px-4 py-2 rounded-xl bg-[var(--color-text-primary)] text-white hover:bg-[var(--color-text-primary)]/90 transition-colors"
          >
            Launch Platform <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>
      </nav>

      <main className="flex-grow pt-14">
        {/* ── HERO ── */}
        <section className="relative min-h-[92vh] flex items-center hero-mesh grid-bg overflow-hidden">
          {/* Decorative blobs */}
          <div className="absolute top-20 right-20 w-80 h-80 rounded-full bg-[var(--color-accent)] opacity-5 blur-3xl pointer-events-none" />
          <div className="absolute bottom-20 left-10 w-60 h-60 rounded-full bg-[var(--color-teal)] opacity-5 blur-3xl pointer-events-none" />

          <div className="max-w-7xl mx-auto px-6 w-full grid grid-cols-1 lg:grid-cols-2 items-center gap-16 py-24">
            {/* Left — copy */}
            <motion.div
              initial="hidden"
              animate="visible"
              variants={stagger}
              className="space-y-6"
            >
              {/* Badge */}
              <motion.div variants={fadeUp}>
                <span className="inline-flex items-center gap-1.5 text-[12px] font-semibold px-3 py-1 rounded-full bg-[var(--color-accent-subtle)] text-[var(--color-accent)]">
                  <Zap className="h-3 w-3" strokeWidth={2.5} />
                  Research · v1.0.0
                </span>
              </motion.div>

              {/* Headline */}
              <motion.h1 variants={fadeUp} className="font-display leading-[1.05]" style={{ fontSize: 52 }}>
                Illuminate the threat.{" "}
                <span className="text-[var(--color-accent)] italic">Before it strikes.</span>
              </motion.h1>

              {/* Body */}
              <motion.p
                variants={fadeUp}
                className="text-[17px] text-[var(--color-text-secondary)] leading-relaxed max-w-lg"
              >
                Lumint is a unified multimodal fraud intelligence platform built for India&apos;s
                digital payment ecosystem — detecting fraud across documents, URLs, UPI screenshots,
                and campaign networks using LLM-powered explainability.
              </motion.p>

              {/* CTAs */}
              <motion.div variants={fadeUp} className="flex items-center gap-4 flex-wrap">
                <Link
                  href="/dashboard"
                  className="flex items-center gap-2 px-7 py-3.5 rounded-xl bg-[var(--color-accent)] hover:bg-[var(--color-accent-dark)] text-white font-semibold text-[15px] shadow-2 transition-all hover:shadow-3"
                >
                  Launch Platform <ArrowRight className="h-4 w-4" />
                </Link>
                <a
                  href="#research"
                  className="flex items-center gap-2 px-7 py-3.5 rounded-xl border border-[var(--color-border)] text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] hover:border-[var(--color-border-strong)] font-semibold text-[15px] transition-all"
                >
                  <BookOpen className="h-4 w-4" />
                  Read Research
                </a>
              </motion.div>

              {/* Trust stats */}
              <motion.div variants={fadeUp} className="flex items-center gap-4 flex-wrap pt-2">
                {[
                  { value: "4 modules",     label: "Detection modalities" },
                  { value: "LLaMA 3.3 70B", label: "AI engine" },
                  { value: "Open source",   label: "Research ready" },
                ].map(({ value, label }) => (
                  <div key={label} className="flex items-center gap-2 text-[12px]">
                    <CheckCircle className="h-3.5 w-3.5 text-[var(--color-safe)]" />
                    <span className="font-semibold text-[var(--color-text-primary)]">{value}</span>
                    <span className="text-[var(--color-text-muted)]">{label}</span>
                  </div>
                ))}
              </motion.div>
            </motion.div>

            {/* Right — floating preview cards */}
            <div className="relative hidden lg:flex items-center justify-center h-[420px]">
              <div className="relative w-full h-full">
                <motion.div
                  animate={{ y: [0, -8, 0] }}
                  transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
                  className="absolute top-8 right-8"
                >
                  <HeroPreviewCard
                    label="DocShield result"
                    value="Risk Score: 87"
                    badge="HIGH RISK"
                    badgeColor="var(--color-danger)"
                    delay={0.3}
                    rotate={2}
                  />
                </motion.div>
                <motion.div
                  animate={{ y: [0, -6, 0] }}
                  transition={{ duration: 3.5, repeat: Infinity, ease: "easeInOut", delay: 0.5 }}
                  className="absolute top-1/2 left-4 -translate-y-1/2"
                >
                  <HeroPreviewCard
                    label="PhishShield verdict"
                    value="hdfc-kyc-verify.com"
                    badge="PHISHING"
                    badgeColor="var(--color-warn)"
                    delay={0.5}
                    rotate={-2}
                  />
                </motion.div>
                <motion.div
                  animate={{ y: [0, -10, 0] }}
                  transition={{ duration: 4, repeat: Infinity, ease: "easeInOut", delay: 1 }}
                  className="absolute bottom-12 right-4"
                >
                  <HeroPreviewCard
                    label="UPI Shield"
                    value="UTR: fake123abc ✗"
                    badge="FORGED"
                    badgeColor="var(--color-critical)"
                    delay={0.7}
                    rotate={1.5}
                  />
                </motion.div>
              </div>
            </div>
          </div>
        </section>

        {/* ── MODULES ── */}
        <section id="modules" className="py-24 px-6 max-w-7xl mx-auto">
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.3 }}
            variants={stagger}
            className="space-y-12"
          >
            <motion.div variants={fadeUp} className="max-w-2xl">
              <h2 className="font-display text-[40px] text-[var(--color-text-primary)] mb-4">
                Four detection modalities. One platform.
              </h2>
              <p className="text-[15px] text-[var(--color-text-secondary)] leading-relaxed">
                Each module is independently capable yet designed to work as a unified pipeline —
                cross-correlating signals across all modalities via the Fraud DNA graph.
              </p>
            </motion.div>

            <motion.div variants={stagger} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
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
        <section id="research" className="py-20 px-6 bg-[var(--color-surface-2)] border-y border-[var(--color-border)]">
          <div className="max-w-7xl mx-auto">
            <motion.div
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.3 }}
              variants={stagger}
              className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-start"
            >
              <motion.div variants={fadeUp} className="space-y-4">
                <span className="inline-flex items-center gap-1.5 text-[12px] font-semibold px-3 py-1 rounded-full bg-[var(--color-accent-subtle)] text-[var(--color-accent)]">
                  <BookOpen className="h-3 w-3" />
                  Built for research publication
                </span>
                <h2 className="font-display text-[36px] text-[var(--color-text-primary)] leading-tight">
                  Novelty claims confirmed by literature review
                </h2>
                <p className="text-[14px] text-[var(--color-text-secondary)] leading-relaxed">
                  Three confirmed research gaps from systematic review of 2024–2025 papers make Lumint
                  a strong candidate for ACM CIKM, IEEE Access, and AMLTA conference tracks.
                </p>
              </motion.div>
              <motion.div variants={stagger} className="space-y-3">
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
                    className="flex items-start gap-3 p-3 rounded-xl bg-[var(--color-surface)] border border-[var(--color-border)]"
                  >
                    <CheckCircle className="h-4 w-4 text-[var(--color-safe)] mt-0.5 shrink-0" />
                    <span className="text-[13px] text-[var(--color-text-secondary)] leading-relaxed">{claim}</span>
                  </motion.div>
                ))}
              </motion.div>
            </motion.div>
          </div>
        </section>

        {/* ── CTA ── */}
        <section className="py-24 px-6">
          <div className="max-w-4xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5 }}
              className="rounded-[24px] bg-[var(--color-text-primary)] p-12 text-center text-white"
            >
              <div className="inline-flex items-center justify-center h-14 w-14 rounded-2xl bg-white/10 mb-6">
                <Shield className="h-7 w-7 text-white" />
              </div>
              <h2 className="font-display text-[40px] text-white mb-4">
                Start analyzing threats
              </h2>
              <p className="text-[15px] text-white/70 mb-8 max-w-xl mx-auto leading-relaxed">
                Lumint is open-source and ready to use. Launch the platform, upload a document or URL,
                and get an AI-powered forensic report in seconds.
              </p>
              <div className="flex items-center justify-center gap-4 flex-wrap">
                <Link
                  href="/dashboard"
                  className="flex items-center gap-2 px-8 py-4 rounded-xl bg-[var(--color-accent)] hover:bg-[var(--color-accent-dark)] text-white font-semibold text-[15px] transition-colors shadow-2"
                >
                  Launch Platform <ArrowRight className="h-4 w-4" />
                </Link>
                <a
                  href="https://github.com/tanmay-alpha/Lumint"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 px-8 py-4 rounded-xl bg-white/10 hover:bg-white/20 text-white font-semibold text-[15px] transition-colors"
                >
                  View on GitHub
                </a>
              </div>
            </motion.div>
          </div>
        </section>
      </main>

      {/* ── FOOTER ── */}
      <footer className="border-t border-[var(--color-border)] bg-[var(--color-surface)] py-10 px-6">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-5 text-[13px] text-[var(--color-text-muted)]">
          <div className="flex items-center gap-2.5">
            <div className="h-6 w-6 rounded-lg bg-[var(--color-text-primary)] flex items-center justify-center">
              <Zap className="h-3.5 w-3.5 text-white" strokeWidth={2.5} />
            </div>
            <span className="font-display text-[18px] text-[var(--color-text-primary)]">Lumint</span>
            <span className="font-mono text-[10px] border border-[var(--color-border)] px-1.5 py-0.5 rounded text-[var(--color-text-muted)]">
              v1.0.0
            </span>
          </div>
          <div className="flex items-center gap-6">
            <a href="#modules" className="hover:text-[var(--color-text-primary)] transition-colors">Modules</a>
            <a href="#research" className="hover:text-[var(--color-text-primary)] transition-colors">Research</a>
            <a
              href="https://github.com/tanmay-alpha/Lumint"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-[var(--color-text-primary)] transition-colors"
            >
              GitHub
            </a>
          </div>
          <span>© {new Date().getFullYear()} Lumint Research. All rights reserved.</span>
        </div>
      </footer>
    </>
  );
}
