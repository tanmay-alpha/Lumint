"use client";

import React from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  ArrowRight,
  Shield,
  FileSearch,
  ShieldAlert,
  Network,
  Smartphone,
  BookOpen,
  Check,
  Zap,
} from "lucide-react";
import { Button } from "@/components/ui/Button";

// ─── Animation helpers ─────────────────────────────────────────────────────
const fadeUpVariants = {
  hidden: { opacity: 0, y: 15 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.4,
      ease: "easeOut" as const,
    },
  },
};

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
};

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.08,
    },
  },
};

const noveltyContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
};

const noveltyItem = {
  hidden: { opacity: 0, x: -20 },
  visible: {
    opacity: 1,
    x: 0,
    transition: {
      duration: 0.4,
      ease: "easeOut" as const,
    },
  },
};

// ─── Floating hero preview card ───────────────────────────────────────────
const HeroPreviewCard = ({
  label,
  value,
  badgeText,
  badgeRisk,
  score,
  delay,
  rotate,
  topPos,
  leftPos,
  rightPos,
  floatYRange,
  floatDuration,
}: {
  label: string;
  value: string;
  badgeText: string;
  badgeRisk: "safe" | "warn" | "high" | "critical";
  score: number;
  delay: number;
  rotate: number;
  topPos?: string;
  leftPos?: string;
  rightPos?: string;
  floatYRange: number[];
  floatDuration: number;
}) => {
  return (
    <motion.div
      initial={{ opacity: 0, x: 40, rotate: 0 }}
      animate={{ opacity: 1, x: 0, rotate }}
      transition={{ duration: 0.4, ease: "easeOut", delay }}
      className="absolute select-none pointer-events-none"
      style={{
        top: topPos,
        left: leftPos,
        right: rightPos,
      }}
    >
      <motion.div
        animate={{ y: floatYRange }}
        transition={{
          duration: floatDuration,
          repeat: Infinity,
          ease: "easeInOut",
        }}
        className="card-elevated backdrop-blur-md bg-surface/85 border border-border-default/60 rounded-xl px-5 py-4 shadow-xl min-w-[290px] max-w-[320px]"
      >
        <div className="flex items-center justify-between gap-3 mb-2.5">
          <span className="text-[11px] font-sans font-semibold tracking-wider text-text-secondary uppercase">
            {label}
          </span>
          <div className="flex items-center gap-2">
            <span className="font-mono text-[12px] font-medium text-text-primary">
              Score: {score}
            </span>
            <span
              className={`inline-flex items-center px-1.5 py-0.5 rounded-[4px] text-[9px] font-bold tracking-wider uppercase ${
                badgeRisk === "safe"
                  ? "bg-risk-none-bg text-risk-none"
                  : badgeRisk === "warn"
                  ? "bg-risk-medium-bg text-risk-medium"
                  : badgeRisk === "high"
                  ? "bg-risk-high-bg text-risk-high"
                  : "bg-risk-critical-bg text-risk-critical"
              }`}
            >
              {badgeText}
            </span>
          </div>
        </div>
        <p className="text-[13px] text-text-primary font-mono tracking-tight font-medium truncate">
          {value}
        </p>
      </motion.div>
    </motion.div>
  );
};

// ─── Module display card ──────────────────────────────────────────────────
const ModuleCard = ({
  icon: Icon,
  title,
  description,
  href,
  colorClass,
}: {
  icon: React.ElementType;
  title: string;
  description: string;
  href: string;
  colorClass: string;
}) => (
  <motion.div
    variants={fadeUpVariants}
    className="card-elevated hover:shadow-xl transition-all duration-300 p-6 flex flex-col justify-between group cursor-pointer h-full border border-border-default/50"
  >
    <div className="space-y-4">
      <div className={`h-10 w-10 rounded-lg flex items-center justify-center ${colorClass}`}>
        <Icon className="h-5 w-5" />
      </div>
      <div>
        <h3 className="text-[16px] font-sans font-semibold text-text-primary mb-2">
          {title}
        </h3>
        <p className="text-[14px] text-text-secondary leading-relaxed line-clamp-3">
          {description}
        </p>
      </div>
    </div>
    <div className="mt-6 pt-4 border-t border-border-muted flex items-center justify-between">
      <span className="font-mono text-[10px] text-text-muted">
        Powered by LLaMA 3.3 70B · Groq
      </span>
      <Link href={href} className="flex items-center gap-1 text-[13px] font-semibold text-brand">
        <span className="group-hover:translate-x-0.5 transition-transform duration-200 flex items-center gap-1">
          Open module <ArrowRight className="h-3.5 w-3.5" />
        </span>
      </Link>
    </div>
  </motion.div>
);

// ─────────────────────────────────────────────────────────────────────────────
// LANDING PAGE
// ─────────────────────────────────────────────────────────────────────────────
export default function LandingPage() {
  const [scrolled, setScrolled] = React.useState(false);

  React.useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 15);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <div className="relative min-h-screen bg-canvas text-text-primary flex flex-col font-sans overflow-x-hidden">
      {/* ── SECTION 1 — NAV ── */}
      <nav
        className={`fixed top-0 inset-x-0 z-50 h-[56px] transition-all duration-300 ${
          scrolled
            ? "bg-[rgba(244,246,249,0.85)] dark:bg-[rgba(12,14,20,0.85)] backdrop-blur-[12px] border-b border-border-default/40 shadow-sm"
            : "bg-transparent border-b border-transparent"
        }`}
      >
        <div className="max-w-7xl mx-auto px-6 h-full flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Shield className="h-4.5 w-4.5 text-brand" strokeWidth={2.5} />
            <span className="font-sans font-semibold text-[16px] text-text-primary tracking-tight leading-none">
              Lumint
            </span>
          </div>

          <div className="hidden md:flex items-center gap-6 text-[14px] text-text-secondary font-medium">
            <a href="#modules" className="hover:text-text-primary transition-colors">
              Modules
            </a>
            <a href="#research" className="hover:text-text-primary transition-colors">
              Research
            </a>
            <Link href="/dashboard/research" className="hover:text-text-primary transition-colors">
              Paper
            </Link>
            <a
              href="https://github.com/tanmay-alpha/lumint"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-text-primary transition-colors"
            >
              GitHub
            </a>
          </div>

          <Link href="/dashboard">
            <Button
              variant="solid"
              className="h-8 px-4 rounded-[8px] bg-brand text-white hover:bg-brand-hover text-[13px] font-semibold flex items-center justify-center transition-colors"
            >
              Launch Platform →
            </Button>
          </Link>
        </div>
      </nav>

      {/* ── SECTION 2 — HERO ── */}
      <section
        className="relative min-h-screen flex items-center justify-center pt-[56px] pb-16 overflow-hidden"
        style={{
          background: `
            radial-gradient(circle at 20% 50%, rgba(37,99,235,0.06) 0%, transparent 50%),
            radial-gradient(circle at 80% 20%, rgba(8,145,178,0.05) 0%, transparent 40%),
            radial-gradient(circle at 60% 80%, rgba(124,58,237,0.04) 0%, transparent 40%),
            var(--bg)
          `,
        }}
      >
        <div className="absolute inset-0 mesh-grid-bg opacity-[0.015] pointer-events-none" />

        <div className="max-w-7xl mx-auto px-6 w-full flex flex-col lg:flex-row items-center justify-between gap-16 relative z-10">
          {/* Centered content block */}
          <motion.div
            initial="hidden"
            animate="visible"
            variants={containerVariants}
            className="flex-1 flex flex-col items-center lg:items-start text-center lg:text-left space-y-6"
          >
            {/* Pill Badge */}
            <motion.div variants={fadeUpVariants} className="inline-block">
              <span className="inline-flex items-center gap-1.5 px-3.5 py-1 rounded-full bg-brand-subtle text-brand border border-brand-border/30 text-[12px] font-sans font-medium">
                <Zap className="h-3.5 w-3.5" strokeWidth={2.5} />
                Research Publication Platform · v1.0.0
              </span>
            </motion.div>

            {/* Headline */}
            <motion.h1
              variants={fadeUpVariants}
              className="font-serif text-[44px] md:text-[52px] text-text-primary tracking-tight leading-[1.1] max-w-xl"
            >
              Illuminate the threat.
              <span className="text-brand italic block mt-1 font-serif">
                Before it strikes.
              </span>
            </motion.h1>

            {/* Subheadline */}
            <motion.p
              variants={fadeUpVariants}
              className="font-sans text-[16px] text-text-secondary max-w-lg leading-relaxed"
            >
              Lumint is a unified multimodal fraud intelligence framework for India&apos;s digital
              payment ecosystem — combining document forensics, phishing detection, and UPI
              screenshot analysis with LLM explainability.
            </motion.p>

            {/* CTAs Row */}
            <motion.div
              variants={fadeUpVariants}
              className="flex items-center justify-center lg:justify-start gap-2 pt-2"
            >
              <Link href="/dashboard">
                <Button
                  variant="solid"
                  className="h-10 px-5 flex items-center justify-center rounded-[8px] bg-brand hover:bg-brand-hover text-white text-[14px] font-semibold transition-colors"
                >
                  Launch Platform →
                </Button>
              </Link>
              <Link href="/dashboard/research">
                <Button
                  variant="outline"
                  className="h-10 px-5 flex items-center justify-center rounded-[8px] border border-border-default hover:bg-surface-raised text-text-primary text-[14px] font-semibold transition-colors"
                >
                  📄 Read Research Paper
                </Button>
              </Link>
            </motion.div>

            {/* Trust stats row */}
            <motion.div
              variants={fadeUpVariants}
              className="pt-4 mt-6 border-t border-border-default/50 w-full max-w-md"
            >
              <div className="flex items-center justify-center lg:justify-start gap-2.5 text-[13px] text-text-secondary/80 font-sans">
                <span>4 detection modalities</span>
                <span className="text-text-muted font-bold">·</span>
                <span>LLaMA 3.3 70B AI engine</span>
                <span className="text-text-muted font-bold">·</span>
                <span>Open source</span>
              </div>
            </motion.div>
          </motion.div>

          {/* Floating preview cards (desktop only) */}
          <div className="hidden lg:flex flex-1 relative items-center justify-center h-[450px] w-full max-w-[420px]">
            {/* Card 1: top right, slightly tilted 2deg */}
            <HeroPreviewCard
              label="DocShield"
              score={87}
              badgeText="HIGH RISK"
              badgeRisk="high"
              value="invoice_9821.pdf · ELA anomaly detected"
              delay={0.1}
              rotate={2}
              topPos="20px"
              rightPos="10px"
              floatYRange={[0, -6, 0]}
              floatDuration={4}
            />

            {/* Card 2: middle, no tilt */}
            <HeroPreviewCard
              label="PhishShield"
              score={94}
              badgeText="PHISHING"
              badgeRisk="critical"
              value="hdfc-kyc-verify.com"
              delay={0.25}
              rotate={0}
              topPos="160px"
              leftPos="-10px"
              floatYRange={[-3, 3, -3]}
              floatDuration={4.5}
            />

            {/* Card 3: bottom right, tilted -1.5deg */}
            <HeroPreviewCard
              label="UPI Shield"
              score={12}
              badgeText="GENUINE"
              badgeRisk="safe"
              value="₹1,500 · UTR: 398273645192"
              delay={0.4}
              rotate={-1.5}
              topPos="290px"
              rightPos="0px"
              floatYRange={[2, -4, 2]}
              floatDuration={3.8}
            />
          </div>
        </div>
      </section>

      {/* ── SECTION 3 — FEATURE MODULES ── */}
      <section id="modules" className="py-24 px-6 max-w-7xl mx-auto border-t border-border-default/40 w-full">
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.15 }}
          variants={staggerContainer}
          className="space-y-16"
        >
          <div className="text-center space-y-3">
            <h2 className="font-sans text-[28px] md:text-[36px] font-bold text-text-primary tracking-tight">
              Four detection modalities. One platform.
            </h2>
            <p className="font-sans text-[15px] md:text-[16px] text-text-secondary max-w-xl mx-auto leading-relaxed">
              Each module operates independently but shares signals via the Fraud DNA graph.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-5xl mx-auto">
            <ModuleCard
              icon={FileSearch}
              title="DocShield"
              description="Detect tampered invoices, forged salary slips, and edited government IDs using ELA forensics and font analysis."
              href="/docshield"
              colorClass="bg-brand/10 text-brand"
            />
            <ModuleCard
              icon={ShieldAlert}
              title="PhishShield"
              description="Identify lookalike bank domains, UPI phishing URLs, and KYC scam links with SHAP-explained risk scores."
              href="/phishshield"
              colorClass="bg-warn/10 text-warn"
            />
            <ModuleCard
              icon={Network}
              title="Fraud DNA"
              description="Visualize fraud campaign networks — cluster events by shared indicators, domains, and file hashes."
              href="/fraud-dna"
              colorClass="bg-ai/10 text-ai-accent"
            />
            <ModuleCard
              icon={Smartphone}
              title="UPI Shield"
              description="Verify PhonePe, Google Pay, and Paytm payment screenshots using OCR, ELA, and LLM forensic analysis."
              href="/upi-shield"
              colorClass="bg-intel/10 text-intel"
            />
          </div>
        </motion.div>
      </section>

      {/* ── SECTION 4 — RESEARCH NOVELTY ── */}
      <section id="research" className="py-24 px-6 border-t border-border-default/40 bg-surface-raised w-full">
        <div className="max-w-5xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-start">
            {/* Left Column */}
            <div className="lg:col-span-5 space-y-4">
              <h2 className="font-serif text-[28px] md:text-[32px] text-text-primary leading-tight">
                Novel contributions confirmed by literature review
              </h2>
              <div className="h-1 w-12 bg-brand rounded-full" />
            </div>

            {/* Right Column */}
            <motion.div
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.2 }}
              variants={noveltyContainer}
              className="lg:col-span-7 space-y-4"
            >
              {[
                "First system combining doc + URL + UPI screenshot forensics in one pipeline",
                "First LLM-generated natural language explanations for fraud scores",
                "SHAP + LLM fusion — machine XAI to human analyst narrative",
                "Cross-modal CMFA: brand palette, font variance, ELA grid density correlation",
              ].map((claim, idx) => (
                <motion.div
                  key={idx}
                  variants={noveltyItem}
                  className="flex items-start gap-3.5 p-4 rounded-xl bg-surface border border-border-default/60 shadow-sm"
                >
                  <div className="h-5 w-5 rounded-full bg-safe-bg flex items-center justify-center text-safe mt-0.5 shrink-0">
                    <Check className="h-3.5 w-3.5" />
                  </div>
                  <span className="font-sans text-[14px] text-text-secondary leading-relaxed">
                    {claim}
                  </span>
                </motion.div>
              ))}
            </motion.div>
          </div>
        </div>
      </section>

      {/* ── SECTION 5 — CTA ── */}
      <section className="py-20 px-6 border-t border-brand-border/30 bg-brand-subtle/25 dark:bg-brand-subtle/5 w-full">
        <div className="max-w-4xl mx-auto text-center space-y-6">
          <h2 className="font-serif text-[32px] md:text-[38px] text-text-primary">
            Start analyzing threats
          </h2>
          <p className="text-[14px] md:text-[15px] font-sans text-text-secondary max-w-lg mx-auto leading-relaxed">
            Lumint is open-source and ready for research verification. Launch the dashboard to test
            multimodal fraud forensic analysis.
          </p>
          <div className="flex justify-center pt-2">
            <Link href="/dashboard">
              <Button
                variant="solid"
                className="h-10 px-5 flex items-center justify-center rounded-[8px] bg-brand hover:bg-brand-hover text-white text-[14px] font-semibold transition-colors"
              >
                Launch Platform →
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* ── SECTION 6 — FOOTER ── */}
      <footer className="border-t border-border-default/40 bg-surface h-16 flex items-center w-full mt-auto">
        <div className="max-w-7xl mx-auto px-6 w-full flex items-center justify-between text-[13px] text-text-secondary/80 font-sans">
          <div className="flex items-center gap-2 select-none">
            <span className="font-semibold text-text-primary">Lumint</span>
            <span className="font-mono text-[10px] px-1.5 py-0.2 bg-surface-raised border border-border-default/50 rounded text-text-muted">
              v1.0.0
            </span>
          </div>
          <div className="hidden md:block">
            Built for research publication
          </div>
          <div className="flex items-center gap-4">
            <a
              href="https://github.com/tanmay-alpha/lumint"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-text-primary transition-colors"
            >
              GitHub
            </a>
            <Link href="/dashboard/research" className="hover:text-text-primary transition-colors">
              Paper
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
