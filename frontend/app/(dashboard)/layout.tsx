"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Shield,
  LayoutDashboard,
  ShieldCheck,
  Link2,
  Fingerprint,
  Signal,
  SignalZero,
  Cpu,
  Menu,
  X
} from "lucide-react";
import client from "@/lib/api/client";
import { twMerge } from "tailwind-merge";
import { motion, AnimatePresence } from "framer-motion";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const [isSystemOnline, setIsSystemOnline] = useState<boolean | null>(null);
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  useEffect(() => {
    // Probe backend health status
    const checkHealth = async () => {
      try {
        const res = await client.getHealth();
        setIsSystemOnline(res.status === "ok");
      } catch (err) {
        setIsSystemOnline(false);
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  const navItems = [
    {
      name: "Dashboard Overview",
      href: "/dashboard",
      icon: LayoutDashboard,
      description: "Aggregated threat telemetry"
    },
    {
      name: "DocShield Analysis",
      href: "/docshield",
      icon: ShieldCheck,
      description: "Expose hidden document edits"
    },
    {
      name: "PhishShield Defender",
      href: "/phishshield",
      icon: Link2,
      description: "Verify URLs & spoof domains"
    },
    {
      name: "Fraud DNA Clusters",
      href: "/fraud-dna",
      icon: Fingerprint,
      description: "Visualize matching actor pools"
    }
  ];

  return (
    <div className="relative min-h-screen bg-bg-base text-text-primary flex overflow-hidden">
      {/* Decorative Blur Backgrounds */}
      <div className="absolute top-0 right-0 w-[40vw] h-[40vw] rounded-full bg-accent-blue/5 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-0 left-[20vw] w-[35vw] h-[35vw] rounded-full bg-accent-teal/5 blur-[120px] pointer-events-none" />

      {/* Grid overlay */}
      <div className="absolute inset-0 grid-bg opacity-30 pointer-events-none" />

      {/* Sidebar - Desktop */}
      <aside className="hidden lg:flex w-72 flex-col shrink-0 border-r border-border/60 bg-surface/70 backdrop-blur-md relative z-30">
        {/* Brand */}
        <div className="flex items-center gap-2.5 px-6 py-6 border-b border-border/40">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-text-primary text-white shadow-md">
            <Shield className="h-5 w-5" />
          </div>
          <div className="flex flex-col">
            <span className="font-display text-xl font-bold tracking-tight">SentinelX</span>
            <span className="text-[10px] font-mono font-bold tracking-wider text-text-secondary uppercase">
              Forensic Platform
            </span>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 px-4 py-6 space-y-1">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={twMerge(
                  "flex items-start gap-3.5 rounded-xl px-4 py-3 text-sm font-medium transition-all group",
                  isActive
                    ? "bg-text-primary text-white shadow-sm"
                    : "text-text-secondary hover:text-text-primary hover:bg-surface/90"
                )}
              >
                <item.icon className={twMerge("h-5 w-5 mt-0.5 shrink-0", isActive ? "text-white" : "text-text-secondary group-hover:text-text-primary")} />
                <div className="flex flex-col">
                  <span>{item.name}</span>
                  <span className={twMerge("text-[10px] mt-0.5 font-normal", isActive ? "text-white/70" : "text-text-secondary/80")}>
                    {item.description}
                  </span>
                </div>
              </Link>
            );
          })}
        </nav>

        {/* Engine and Connection Telemetry */}
        <div className="p-4 border-t border-border/40 bg-surface/30">
          <div className="rounded-xl border border-border/50 bg-bg-base/60 p-4.5">
            <div className="flex items-center justify-between mb-3">
              <span className="text-[10px] font-bold text-text-secondary uppercase tracking-wider flex items-center gap-1.5">
                <Cpu className="h-3 w-3" /> System Engine
              </span>
              <div className="flex items-center gap-1.5">
                {isSystemOnline === null ? (
                  <span className="h-2 w-2 rounded-full bg-slate-300 animate-pulse" />
                ) : isSystemOnline ? (
                  <span className="h-2 w-2 rounded-full bg-risk-safe animate-pulse" />
                ) : (
                  <span className="h-2 w-2 rounded-full bg-risk-critical animate-pulse" />
                )}
                <span className="text-[10px] font-mono font-bold uppercase">
                  {isSystemOnline === null ? "checking" : isSystemOnline ? "online" : "offline"}
                </span>
              </div>
            </div>
            <div className="text-[11px] text-text-secondary font-medium leading-relaxed">
              {isSystemOnline
                ? "FastAPI sandbox core active. Dynamic scanning fully enabled."
                : "FastAPI offline. Running in hybrid local mock sandbox mode."}
            </div>
          </div>
        </div>
      </aside>

      {/* Main Panel Content Area */}
      <div className="flex-1 flex flex-col min-w-0 relative z-20 overflow-hidden">
        {/* Header bar */}
        <header className="h-16 shrink-0 border-b border-border/40 bg-surface/60 backdrop-blur-md px-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* Mobile burger button */}
            <button
              onClick={() => setIsMobileOpen(true)}
              className="lg:hidden h-8 w-8 flex items-center justify-center rounded-lg border border-border/60 bg-surface/50 text-text-primary"
            >
              <Menu className="h-5 w-5" />
            </button>
            <h1 className="text-base font-bold tracking-tight text-text-primary capitalize">
              {pathname === "/dashboard"
                ? "Telemetry Dashboard"
                : pathname === "/docshield"
                ? "DocShield Document Forensics"
                : pathname === "/phishshield"
                ? "PhishShield Link Verification"
                : pathname === "/fraud-dna"
                ? "Fraud DNA Connected Clusters"
                : "SentinelX Analysis Core"}
            </h1>
          </div>

          <div className="flex items-center gap-4">
            <span className="hidden md:inline-flex items-center gap-1.5 text-xs font-semibold text-text-secondary bg-surface/80 border border-border/60 px-3 py-1 rounded-full">
              Sandbox active
            </span>
            <div className="h-8 w-8 rounded-full bg-accent-blue/10 border border-accent-blue/30 text-accent-blue flex items-center justify-center text-xs font-bold font-mono">
              TM
            </div>
          </div>
        </header>

        {/* Dynamic page contents scroll frame */}
        <main className="flex-1 overflow-y-auto p-6 lg:p-8">
          <div className="max-w-7xl mx-auto space-y-8">
            {children}
          </div>
        </main>
      </div>

      {/* Mobile Drawer Navigation */}
      <AnimatePresence>
        {isMobileOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 0.4 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsMobileOpen(false)}
              className="fixed inset-0 bg-black z-40 lg:hidden"
            />
            {/* Drawer */}
            <motion.aside
              initial={{ x: "-100%" }}
              animate={{ x: 0 }}
              exit={{ x: "-100%" }}
              transition={{ type: "spring", damping: 25, stiffness: 250 }}
              className="fixed inset-y-0 left-0 w-80 bg-surface/95 backdrop-blur-xl border-r border-border z-50 p-6 flex flex-col justify-between lg:hidden"
            >
              <div>
                <div className="flex items-center justify-between mb-8">
                  <div className="flex items-center gap-2.5">
                    <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-text-primary text-white shadow-md">
                      <Shield className="h-5 w-5" />
                    </div>
                    <span className="font-display text-xl font-bold tracking-tight">SentinelX</span>
                  </div>
                  <button
                    onClick={() => setIsMobileOpen(false)}
                    className="h-8 w-8 flex items-center justify-center rounded-lg border border-border/60 bg-surface text-text-primary"
                  >
                    <X className="h-5 w-5" />
                  </button>
                </div>

                <nav className="space-y-1">
                  {navItems.map((item) => {
                    const isActive = pathname === item.href;
                    return (
                      <Link
                        key={item.href}
                        href={item.href}
                        onClick={() => setIsMobileOpen(false)}
                        className={twMerge(
                          "flex items-start gap-3.5 rounded-xl px-4 py-3.5 text-sm font-medium transition-all",
                          isActive
                            ? "bg-text-primary text-white shadow-sm"
                            : "text-text-secondary hover:text-text-primary hover:bg-bg-base"
                        )}
                      >
                        <item.icon className="h-5 w-5 mt-0.5 shrink-0" />
                        <div className="flex flex-col">
                          <span>{item.name}</span>
                          <span className="text-[10px] text-text-secondary/70 font-normal">
                            {item.description}
                          </span>
                        </div>
                      </Link>
                    );
                  })}
                </nav>
              </div>

              {/* Status footer inside mobile drawer */}
              <div className="rounded-xl border border-border/50 bg-bg-base/60 p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] font-bold text-text-secondary uppercase">Engine Connection</span>
                  <span className="text-[10px] font-mono font-bold uppercase text-accent-blue">
                    {isSystemOnline ? "connected" : "mock sandbox"}
                  </span>
                </div>
                <div className="text-[10px] text-text-secondary leading-relaxed">
                  FastAPI sandbox connection telemetry automatically manages client fallbacks.
                </div>
              </div>
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
