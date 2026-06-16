import type { Metadata } from "next";
import Link from "next/link";
import {
  ArrowRight,
  Shield,
  FileSearch,
  ShieldAlert,
  Network,
  Smartphone,
  Upload,
  Brain,
  FileCheck2,
  Lock,
  Code2,
  Eye,
  ServerOff,
  Sparkles,
  GraduationCap,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Footer } from "@/components/Footer";

// ─── Inline brand icons (lucide-react doesn't ship brand marks) ──────────
const Github = ({ className }: { className?: string }) => (
  <svg
    className={className}
    viewBox="0 0 24 24"
    fill="currentColor"
    aria-hidden="true"
  >
    <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12Z" />
  </svg>
);

const Linkedin = ({ className }: { className?: string }) => (
  <svg
    className={className}
    viewBox="0 0 24 24"
    fill="currentColor"
    aria-hidden="true"
  >
    <path d="M20.45 20.45h-3.555v-5.569c0-1.328-.025-3.038-1.852-3.038-1.853 0-2.137 1.447-2.137 2.94v5.667H9.351V9h3.414v1.561h.05c.476-.9 1.637-1.852 3.37-1.852 3.602 0 4.266 2.37 4.266 5.455v6.286ZM5.337 7.433a2.063 2.063 0 1 1 0-4.126 2.063 2.063 0 0 1 0 4.126ZM7.116 20.45H3.555V9h3.561v11.45ZM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003Z" />
  </svg>
);

export const metadata: Metadata = {
  title: "About · Lumint",
  description:
    "Privacy-first multimodal fraud intelligence for India's digital payment ecosystem.",
  openGraph: {
    title: "About Lumint",
    description:
      "Open-source fraud detection for UPI screenshots, documents, and suspicious URLs.",
  },
};


// ─── Reusable card ─────────────────────────────────────────────────────
function Panel({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <div
      className={`card-elevated rounded-2xl border border-border-default/50 bg-surface/60 backdrop-blur-sm ${className}`}
    >
      {children}
    </div>
  );
}

// ─── Section header ────────────────────────────────────────────────────
function SectionHeader({
  eyebrow,
  title,
  subtitle,
}: {
  eyebrow: string;
  title: string;
  subtitle?: string;
}) {
  return (
    <div className="text-center space-y-3 max-w-2xl mx-auto">
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-brand-subtle text-brand border border-brand-border/30 text-[11px] font-sans font-semibold tracking-wider uppercase">
        {eyebrow}
      </span>
      <h2 className="font-sans font-bold text-[28px] md:text-[36px] text-text-primary tracking-tight leading-[1.1]">
        {title}
      </h2>
      {subtitle ? (
        <p className="font-sans text-[15px] md:text-[16px] text-text-secondary leading-relaxed">
          {subtitle}
        </p>
      ) : null}
    </div>
  );
}

export default function AboutPage() {
  return (
    <div className="relative min-h-screen bg-canvas text-text-primary flex flex-col font-sans overflow-x-hidden">
      {/* ── TOP NAV (mirrors marketing, adds About) ── */}
      <nav className="sticky top-0 inset-x-0 z-50 h-[56px] bg-[rgba(10,14,26,0.6)] backdrop-blur-sm border-b border-border-default/40">
        <div className="max-w-7xl mx-auto px-6 h-full flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <Shield className="h-4.5 w-4.5 text-brand" strokeWidth={2.5} />
            <span className="font-sans font-semibold text-[16px] text-text-primary tracking-tight leading-none">
              Lumint
            </span>
          </Link>

          <div className="hidden md:flex items-center gap-6 text-[14px] text-text-secondary font-medium">
            <Link href="/" className="hover:text-text-primary transition-colors">
              Home
            </Link>
            <Link
              href="/about"
              className="text-text-primary font-semibold transition-colors"
              aria-current="page"
            >
              About
            </Link>
            <Link
              href="/dashboard/research"
              className="hover:text-text-primary transition-colors"
            >
              Research
            </Link>
            <a
              href="https://github.com/tanmay-alpha/lumint"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-text-primary transition-colors flex items-center gap-1.5"
            >
              <Github className="h-3.5 w-3.5" />
              GitHub
            </a>
            <a
              href="https://www.linkedin.com/in/tanmaymangal/"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-text-primary transition-colors flex items-center gap-1.5"
            >
              <Linkedin className="h-3.5 w-3.5" />
              LinkedIn
            </a>
          </div>

          <Link href="/dashboard" className="md:hidden">
            <Button
              variant="solid"
              className="h-8 px-3 text-[12px] rounded-md bg-brand text-white font-semibold"
            >
              Try
            </Button>
          </Link>
        </div>
      </nav>

      {/* ── HERO ── */}
      <section
        className="relative pt-20 pb-16 md:pt-28 md:pb-24 px-6 overflow-hidden"
        style={{
          background: `
            radial-gradient(circle at 20% 30%, rgba(220,38,38,0.08) 0%, transparent 50%),
            radial-gradient(circle at 80% 70%, rgba(8,145,178,0.06) 0%, transparent 40%),
            var(--bg)
          `,
        }}
      >
        <div className="max-w-4xl mx-auto text-center space-y-6 relative z-10">
          <span className="inline-flex items-center gap-1.5 px-3.5 py-1 rounded-full bg-brand-subtle text-brand border border-brand-border/30 text-[12px] font-sans font-semibold">
            <Sparkles className="h-3.5 w-3.5" strokeWidth={2.5} />
            About Lumint
          </span>

          <h1 className="font-sans font-bold text-[40px] md:text-[56px] text-text-primary tracking-tight leading-[1.05]">
            Privacy-first fraud intelligence.
            <span className="block mt-2 text-brand" style={{ textShadow: "0 0 18px rgba(220, 38, 38, 0.35)" }}>
              Built in your browser.
            </span>
          </h1>

          <p className="font-sans text-[16px] md:text-[18px] text-text-secondary max-w-2xl mx-auto leading-relaxed">
            Lumint is a free, open-source fraud detection platform for India&apos;s
            digital payment ecosystem. It analyzes UPI screenshots, documents, and
            suspicious URLs — all without your data ever leaving your device.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
            <Link href="/dashboard">
              <Button
                variant="solid"
                className="h-11 px-6 flex items-center justify-center gap-2 rounded-[8px] bg-brand hover:bg-brand-hover text-white text-[14px] font-semibold transition-colors shadow-[0_0_30px_rgba(220,38,38,0.3)]"
              >
                Try Lumint Now
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <a
              href="https://github.com/tanmay-alpha/lumint"
              target="_blank"
              rel="noopener noreferrer"
            >
              <Button
                variant="outline"
                className="h-11 px-6 flex items-center justify-center gap-2 rounded-[8px] border border-border-default hover:bg-surface-raised text-text-primary text-[14px] font-semibold transition-colors"
              >
                <Github className="h-4 w-4" />
                View on GitHub
              </Button>
            </a>
          </div>

          {/* Trust strip */}
          <div className="pt-6 mt-4 border-t border-border-default/40 max-w-xl mx-auto">
            <div className="flex flex-wrap items-center justify-center gap-x-4 gap-y-2 text-[13px] text-text-secondary/80 font-sans">
              <span className="flex items-center gap-1.5">
                <Lock className="h-3.5 w-3.5 text-risk-none" />
                100% client-side
              </span>
              <span className="text-text-muted font-bold">·</span>
              <span>4 detection modules</span>
              <span className="text-text-muted font-bold">·</span>
              <span>MIT licensed</span>
              <span className="text-text-muted font-bold">·</span>
              <span>No accounts required</span>
            </div>
          </div>
        </div>
      </section>

      {/* ── HOW IT WORKS ── */}
      <section className="py-20 md:py-24 px-6 border-t border-border-default/40">
        <div className="max-w-7xl mx-auto space-y-12">
          <SectionHeader
            eyebrow="How it works"
            title="Three steps. Zero servers."
            subtitle="Lumint runs the entire analysis pipeline in your browser. No uploads, no accounts, no telemetry."
          />

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
            {[
              {
                n: "01",
                icon: Upload,
                title: "Upload locally",
                body: "Drop a UPI screenshot, document, or paste a suspicious URL. Files never leave your device — they stay in browser memory.",
                color: "bg-brand/10 text-brand",
              },
              {
                n: "02",
                icon: Brain,
                title: "Analyze in-browser",
                body: "Tesseract.js extracts text, Canvas-based ELA surfaces pixel tampering, and a rule engine weighs every signal.",
                color: "bg-ai/10 text-ai-accent",
              },
              {
                n: "03",
                icon: FileCheck2,
                title: "Get a verdict",
                body: "A risk score (0–100) with a plain-English explanation of every signal that contributed. Copy, share, or re-run instantly.",
                color: "bg-risk-none-bg text-risk-none",
              },
            ].map((step) => (
              <Panel key={step.n} className="p-6 md:p-7 h-full flex flex-col">
                <div className="flex items-center justify-between mb-5">
                  <div className={`h-11 w-11 rounded-lg flex items-center justify-center ${step.color}`}>
                    <step.icon className="h-5 w-5" strokeWidth={2.2} />
                  </div>
                  <span className="font-mono text-[12px] font-semibold text-text-muted tracking-wider">
                    STEP {step.n}
                  </span>
                </div>
                <h3 className="font-sans text-[16px] font-semibold text-text-primary mb-2">
                  {step.title}
                </h3>
                <p className="text-[14px] text-text-secondary leading-relaxed flex-1">
                  {step.body}
                </p>
              </Panel>
            ))}
          </div>
        </div>
      </section>

      {/* ── THE 4 SHIELDS ── */}
      <section
        id="shields"
        className="py-20 md:py-24 px-6 border-t border-border-default/40 bg-surface-raised/40"
      >
        <div className="max-w-7xl mx-auto space-y-12">
          <SectionHeader
            eyebrow="The four shields"
            title="Specialized detectors. One platform."
            subtitle="Each module targets a specific fraud surface. Run any one independently or chain them through Fraud DNA."
          />

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-5xl mx-auto">
            {[
              {
                icon: Smartphone,
                title: "UPI Shield",
                blurb: "Verify PhonePe, Google Pay, Paytm, and BHIM payment screenshots.",
                body: "Reads UTR, amount, sender/receiver VPA, and payment app via Tesseract.js OCR. Cross-checks 4-of-5 signal heuristics (payment keywords, app name, @VPA, UTR pattern, rupee symbol) to reject non-UPI inputs like college IDs or random photos.",
                href: "/upi-shield",
                color: "bg-intel/10 text-intel",
              },
              {
                icon: FileSearch,
                title: "DocShield",
                blurb: "Detect tampered Aadhaar, PAN, invoices, and certificates.",
                body: "Runs Error Level Analysis (ELA) by recompressing pixels in-browser to expose JPEG-block tampering, plus metadata/EXIF inspection and font-baseline checks. Flags both crude edits and subtle redactions.",
                href: "/docshield",
                color: "bg-brand/10 text-brand",
              },
              {
                icon: ShieldAlert,
                title: "PhishShield",
                blurb: "Identify lookalike bank domains and UPI phishing links.",
                body: "Analyzes URLs for typosquatting (paypa1.com), suspicious TLDs (.tk, .ml, .ga), IP-address hosting, HTTPS misuse, and brand impersonation. Each signal gets its own weighted contribution to the final risk score.",
                href: "/phishshield",
                color: "bg-warn/10 text-warn",
              },
              {
                icon: Network,
                title: "Fraud DNA",
                blurb: "Visualize fraud campaign networks and shared infrastructure.",
                body: "Clusters threat events by shared indicators — domains, file hashes, VPA patterns, text fingerprints — and renders the resulting graph. Useful for spotting the same attacker across multiple reports.",
                href: "/fraud-dna",
                color: "bg-ai/10 text-ai-accent",
              },
            ].map((shield) => (
              <Panel key={shield.title} className="p-6 md:p-7 h-full flex flex-col">
                <div className="flex items-start gap-4 mb-4">
                  <div className={`h-10 w-10 shrink-0 rounded-lg flex items-center justify-center ${shield.color}`}>
                    <shield.icon className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="font-sans text-[17px] font-semibold text-text-primary leading-tight">
                      {shield.title}
                    </h3>
                    <p className="text-[13px] text-brand font-semibold mt-0.5">
                      {shield.blurb}
                    </p>
                  </div>
                </div>
                <p className="text-[14px] text-text-secondary leading-relaxed flex-1">
                  {shield.body}
                </p>
                <Link
                  href={shield.href}
                  className="mt-5 pt-4 border-t border-border-default/50 flex items-center justify-end text-[13px] font-semibold text-brand group"
                >
                  Open {shield.title}
                  <ArrowRight className="h-3.5 w-3.5 ml-1 group-hover:translate-x-0.5 transition-transform" />
                </Link>
              </Panel>
            ))}
          </div>
        </div>
      </section>

      {/* ── PRIVACY ── */}
      <section
        id="privacy"
        className="py-20 md:py-24 px-6 border-t border-border-default/40"
      >
        <div className="max-w-5xl mx-auto space-y-10">
          <SectionHeader
            eyebrow="Privacy"
            title="Your data never leaves your device."
            subtitle="Lumint is built around a single principle: a fraud tool that ships your data to a server is itself a fraud risk."
          />

          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {[
              {
                icon: ServerOff,
                title: "No backend for analysis",
                body: "OCR, ELA, and the rule engine all run in your browser via WebAssembly + Canvas. The app works fully offline once loaded.",
              },
              {
                icon: Lock,
                title: "No accounts, no tracking",
                body: "There is no sign-up, no analytics on your scans, and no fingerprinting. Open the page, use it, close the tab.",
              },
              {
                icon: Eye,
                title: "Transparent heuristics",
                body: "Every risk score is broken down into the signals that contributed. You can audit the rules in the open-source repo.",
              },
            ].map((p) => (
              <Panel key={p.title} className="p-6 h-full">
                <p.icon className="h-5 w-5 text-brand mb-3" strokeWidth={2.2} />
                <h3 className="font-sans text-[15px] font-semibold text-text-primary mb-1.5">
                  {p.title}
                </h3>
                <p className="text-[13.5px] text-text-secondary leading-relaxed">
                  {p.body}
                </p>
              </Panel>
            ))}
          </div>

          {/* Technical deep-dive */}
          <Panel className="p-7 md:p-8">
            <h3 className="font-sans text-[18px] font-semibold text-text-primary mb-5 flex items-center gap-2">
              <Code2 className="h-5 w-5 text-brand" />
              How the in-browser analysis actually works
            </h3>
            <div className="space-y-5 text-[14px] text-text-secondary leading-relaxed">
              <div>
                <p className="font-semibold text-text-primary mb-1">Tesseract.js (OCR)</p>
                <p>
                  Text extraction runs on a WebAssembly port of Google&apos;s Tesseract
                  engine. The OCR model (~2 MB) loads once per session and is cached by
                  the browser. Every character, digit, and symbol comes from your local
                  CPU — no API call.
                </p>
              </div>
              <div>
                <p className="font-semibold text-text-primary mb-1">Canvas + WebGL (ELA)</p>
                <p>
                  Error Level Analysis recompresses your image at a known JPEG quality,
                  then subtracts it from the original pixel-by-pixel on an HTML5 canvas.
                  Regions that were edited after the original compression show up as
                  bright anomalies — a classic signal of tampering.
                </p>
              </div>
              <div>
                <p className="font-semibold text-text-primary mb-1">Rule engine</p>
                <p>
                  Extracted text and ELA scores feed a weighted rule engine. Each rule
                  contributes additively to the final 0–100 risk score, and the
                  explanation panel shows exactly which rules fired and how much each
                  one weighed.
                </p>
              </div>
            </div>
          </Panel>
        </div>
      </section>

      {/* ── TECH STACK ── */}
      <section
        id="stack"
        className="py-20 md:py-24 px-6 border-t border-border-default/40 bg-surface-raised/40"
      >
        <div className="max-w-5xl mx-auto space-y-10">
          <SectionHeader
            eyebrow="Tech stack"
            title="Boring, fast, and open."
            subtitle="No backend services. No ML APIs. No vendor lock-in."
          />

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4 max-w-4xl mx-auto">
            {[
              { name: "Next.js 15", role: "Framework" },
              { name: "TypeScript", role: "Language" },
              { name: "Tailwind CSS v4", role: "Styling" },
              { name: "Tesseract.js", role: "OCR (WASM)" },
              { name: "Framer Motion", role: "Animation" },
              { name: "Canvas / WebGL", role: "Forensics" },
              { name: "Vercel", role: "Hosting" },
              { name: "MIT License", role: "License" },
            ].map((tech) => (
              <div
                key={tech.name}
                className="card-elevated p-4 rounded-xl border border-border-default/40 bg-surface/60 text-center"
              >
                <p className="font-sans text-[14px] font-semibold text-text-primary">
                  {tech.name}
                </p>
                <p className="text-[11px] text-text-muted mt-0.5 font-mono uppercase tracking-wider">
                  {tech.role}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── ABOUT THE CREATOR ── */}
      <section
        id="creator"
        className="py-20 md:py-24 px-6 border-t border-border-default/40"
      >
        <div className="max-w-4xl mx-auto space-y-10">
          <SectionHeader
            eyebrow="Built by"
            title="A student, for everyone."
          />

          <Panel className="p-7 md:p-9">
            <div className="flex flex-col md:flex-row gap-7 md:gap-9 items-start">
              {/* Avatar block */}
              <div className="shrink-0 flex flex-col items-center md:items-start gap-3">
                <div className="h-20 w-20 rounded-2xl bg-gradient-to-br from-brand to-ai-accent flex items-center justify-center text-white text-[28px] font-bold shadow-lg">
                  TM
                </div>
                <div className="flex gap-2">
                  <a
                    href="https://github.com/tanmay-alpha"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="h-9 w-9 rounded-md border border-border-default/60 flex items-center justify-center text-text-secondary hover:text-text-primary hover:border-text-primary transition-colors"
                    aria-label="GitHub"
                  >
                    <Github className="h-4 w-4" />
                  </a>
                  <a
                    href="https://www.linkedin.com/in/tanmaymangal/"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="h-9 w-9 rounded-md border border-border-default/60 flex items-center justify-center text-text-secondary hover:text-text-primary hover:border-text-primary transition-colors"
                    aria-label="LinkedIn"
                  >
                    <Linkedin className="h-4 w-4" />
                  </a>
                </div>
              </div>

              {/* Bio */}
              <div className="flex-1 space-y-4">
                <div>
                  <h3 className="font-sans text-[22px] font-bold text-text-primary">
                    Tanmay Mangal
                  </h3>
                  <p className="text-[13px] text-text-muted font-mono mt-0.5">
                    B.Tech CSE · Class of 2027
                  </p>
                </div>
                <p className="text-[14.5px] text-text-secondary leading-relaxed">
                  Tanmay is a Computer Science undergraduate at{" "}
                  <span className="text-text-primary font-semibold">VIT Bhopal</span>,
                  where he&apos;s been building applied AI products since his first
                  semester. Lumint started as a side project to understand how
                  client-side forensics could replace server-side AI APIs — and
                  grew into a full multimodal fraud intelligence framework.
                </p>
                <p className="text-[14.5px] text-text-secondary leading-relaxed">
                  He previously interned at{" "}
                  <span className="text-text-primary font-semibold">TradeVed</span>{" "}
                  (fintech, 2024) and{" "}
                  <span className="text-text-primary font-semibold">MAET</span>{" "}
                  (Marine & Automotive Engineering Training, 2023), working on
                  data pipelines, internal tooling, and ML-assisted product
                  features.
                </p>

                {/* Badges */}
                <div className="flex flex-wrap gap-2 pt-2">
                  {[
                    { icon: GraduationCap, label: "VIT Bhopal" },
                    { label: "TradeVed · 2024" },
                    { label: "MAET · 2023" },
                    { label: "Fintech + AI" },
                  ].map((b) => (
                    <span
                      key={b.label}
                      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-surface-raised border border-border-default/50 text-[11.5px] font-semibold text-text-secondary"
                    >
                      {b.icon ? <b.icon className="h-3 w-3" /> : null}
                      {b.label}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </Panel>
        </div>
      </section>

      {/* ── CTA ── */}
      <section
        className="py-24 md:py-32 px-6 border-t border-border-default/40 relative overflow-hidden"
        style={{
          background: `
            radial-gradient(circle at 50% 50%, rgba(220,38,38,0.10) 0%, transparent 60%),
            var(--bg)
          `,
        }}
      >
        <div className="max-w-3xl mx-auto text-center space-y-6 relative z-10">
          <h2 className="font-sans font-bold text-[32px] md:text-[44px] text-text-primary tracking-tight leading-[1.1]">
            Ready to run your first scan?
          </h2>
          <p className="font-sans text-[16px] md:text-[17px] text-text-secondary max-w-xl mx-auto leading-relaxed">
            No account. No install. Open the dashboard, drop a file, and see the
            verdict in under a second.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
            <Link href="/dashboard">
              <Button
                variant="solid"
                className="h-12 px-7 flex items-center justify-center gap-2 rounded-[8px] bg-brand hover:bg-brand-hover text-white text-[15px] font-semibold transition-colors shadow-[0_0_30px_rgba(220,38,38,0.3)]"
              >
                Try Lumint Now
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <Link href="/dashboard/research">
              <Button
                variant="outline"
                className="h-12 px-7 flex items-center justify-center gap-2 rounded-[8px] border border-border-default hover:bg-surface-raised text-text-primary text-[15px] font-semibold transition-colors"
              >
                Read the Research Paper
              </Button>
            </Link>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
