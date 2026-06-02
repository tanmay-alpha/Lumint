"use client";

import React from "react";
import NavBar from "@/components/marketing/NavBar";
import Hero from "@/components/marketing/Hero";
import FeatureGrid from "@/components/marketing/FeatureGrid";
import StatCard from "@/components/ui/StatCard";
import { Activity, FileCheck, AlertOctagon, Clock, Shield, ExternalLink } from "lucide-react";
import { motion } from "framer-motion";
import Link from "next/link";

export default function MarketingPage() {
  return (
    <>
      <NavBar />
      
      <main className="flex-grow">
        {/* Hero Section */}
        <Hero />

        {/* Features Subsystems Section */}
        <FeatureGrid />

        {/* Stats and Metrics Section */}
        <section id="metrics" className="py-24 px-6 max-w-7xl mx-auto relative z-10">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <h2 className="font-display text-4xl sm:text-5xl font-bold text-text-primary">
              Telemetry & Accuracy Metrics.
            </h2>
            <p className="mt-4 text-text-secondary font-medium">
              Real-time analysis dashboard benchmarks showcasing average telemetry and platform processing capacities.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            <StatCard
              label="Total Scans Processed"
              value="85,420"
              trend={{ value: "+12.4%", isPositive: true }}
              icon={<FileCheck className="h-4 w-4" />}
            />
            <StatCard
              label="High Risk Matches"
              value="1,492"
              trend={{ value: "-4.2%", isPositive: true }}
              icon={<AlertOctagon className="h-4 w-4 text-risk-critical" />}
            />
            <StatCard
              label="Associated Threat Clusters"
              value="48"
              trend={{ value: "+3 new", isPositive: false }}
              icon={<Activity className="h-4 w-4 text-risk-high" />}
            />
            <StatCard
              label="Avg Scan Latency"
              value="340ms"
              trend={{ value: "-52ms", isPositive: true }}
              icon={<Clock className="h-4 w-4 text-accent-teal" />}
            />
          </div>
        </section>

        {/* Bottom CTA Block */}
        <section className="py-20 px-6 max-w-5xl mx-auto relative z-10 text-center">
          <div className="rounded-3xl border border-border/60 bg-surface/50 p-12 backdrop-blur-xl flex flex-col items-center">
            <h2 className="font-display text-4xl sm:text-5xl font-bold text-text-primary">
              Ready to verify with forensics?
            </h2>
            <p className="mt-4 text-text-secondary max-w-xl font-medium mb-8">
              SentinelX handles document structure, lookalike URL spoof detection, and campaigns threat clustering with strict local safety.
            </p>
            <Link
              href="/dashboard"
              className="inline-flex items-center gap-2 rounded-full bg-text-primary hover:bg-text-primary/95 text-white font-semibold px-8 py-4 shadow-lg shadow-text-primary/10 transition-transform hover:scale-[1.02] active:scale-[0.98] text-base"
            >
              Launch Dashboard
            </Link>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-border/40 bg-surface/40 py-12 px-6">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6 text-sm text-text-secondary font-medium">
          <div className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-text-primary" />
            <span className="font-display text-lg font-bold text-text-primary">SentinelX</span>
            <span className="text-[11px] font-mono border border-border bg-bg-base px-1.5 py-0.5 rounded text-text-secondary">v1.2.0</span>
          </div>

          <div className="flex items-center gap-8">
            <a href="#features" className="hover:text-text-primary transition-colors">Suite</a>
            <a href="#metrics" className="hover:text-text-primary transition-colors">Metrics</a>
            <a href="https://github.com/tanmay-alpha/Fraud-Intelligence" target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1.5 hover:text-text-primary transition-colors">
              <ExternalLink className="h-4 w-4" />
              Source Code
            </a>
          </div>

          <div>
            &copy; {new Date().getFullYear()} SentinelX Forensics. All rights reserved.
          </div>
        </div>
      </footer>
    </>
  );
}
