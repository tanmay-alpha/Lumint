"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  ShieldAlert, 
  LayoutDashboard, 
  FileText, 
  Globe, 
  Network, 
  Settings, 
  Menu, 
  X, 
  RefreshCw,
  Cpu,
  History
} from "lucide-react";
import { cn } from "@/lib/utils";
import { subscribeToModeChange } from "@/lib/api-client";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isLive, setIsLive] = useState(false);
  const [checking, setChecking] = useState(false);

  useEffect(() => {
    // Subscribe to api client mode changes (live vs mock)
    const unsubscribe = subscribeToModeChange((live) => {
      setIsLive(live);
    });
    return () => unsubscribe();
  }, []);

  const navItems = [
    { name: "Overview", href: "/dashboard", icon: LayoutDashboard },
    { name: "DocShield Forensics", href: "/dashboard/docshield", icon: FileText },
    { name: "PhishShield URL", href: "/dashboard/phishshield", icon: Globe },
    { name: "Fraud DNA Clusters", href: "/dashboard/fraud-dna", icon: Network },
    { name: "Threat Activity", href: "/dashboard/events", icon: History },
  ];

  return (
    <div className="flex h-screen bg-[#FBFBFC] overflow-hidden font-sans">
      
      {/* Sidebar for Desktop */}
      <aside className="hidden lg:flex lg:flex-col lg:w-64 bg-white border-r border-slate-200/60 shrink-0 z-20">
        <div className="flex items-center gap-2 px-6 py-5 border-b border-slate-100/80">
          <div className="rounded-xl bg-slate-900 p-2 text-white shadow-sm">
            <ShieldAlert className="h-5 w-5" />
          </div>
          <span className="text-lg font-bold tracking-tight text-slate-900">
            Sentinel<span className="text-sky-600">X</span>
          </span>
        </div>

        <nav className="flex-1 px-4 py-6 space-y-1.5 overflow-y-auto">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-semibold tracking-wide transition-all duration-200",
                  isActive
                    ? "bg-sky-50 text-sky-700 border border-sky-100/50 shadow-[0_2px_8px_rgba(2,132,199,0.02)]"
                    : "text-slate-500 hover:text-slate-900 hover:bg-slate-50 border border-transparent"
                )}
              >
                <Icon className={cn("h-4.5 w-4.5 shrink-0", isActive ? "text-sky-600" : "text-slate-400")} />
                {item.name}
              </Link>
            );
          })}
        </nav>

        {/* Sidebar Footer */}
        <div className="p-4 border-t border-slate-100 bg-[#FCFCFD]">
          <div className="flex items-center justify-between p-2 rounded-xl bg-white border border-slate-200/50 shadow-sm text-xs font-semibold text-slate-500">
            <div className="flex items-center gap-2">
              <Cpu className="h-4 w-4 text-slate-400" />
              <span>SentinelX Node</span>
            </div>
            <span className="text-[10px] text-slate-400">v1.0.0</span>
          </div>
        </div>
      </aside>

      {/* Main content area */}
      <div className="flex flex-col flex-1 overflow-hidden min-w-0">
        
        {/* Top Header */}
        <header className="flex items-center justify-between px-6 py-4 bg-white/80 border-b border-slate-200/60 backdrop-blur-md z-10 shrink-0">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden p-2 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-600 transition-colors"
            >
              <Menu className="h-5 w-5" />
            </button>
            <h1 className="text-lg font-bold text-slate-900 hidden sm:block">
              {pathname === "/dashboard" && "Platform Overview"}
              {pathname === "/dashboard/docshield" && "DocShield Document Forensics"}
              {pathname === "/dashboard/phishshield" && "PhishShield Phishing URL Scanner"}
              {pathname === "/dashboard/fraud-dna" && "Fraud DNA Threat Campaign Clusters"}
              {pathname === "/dashboard/events" && "Unified Forensic Threat Activity"}
            </h1>
          </div>

          <div className="flex items-center gap-4">
            {/* Dynamic Status Connection Badge */}
            <div className={cn(
              "flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-bold transition-all shadow-[0_2px_4px_rgba(0,0,0,0.01)]",
              isLive 
                ? "bg-emerald-50 text-emerald-700 border-emerald-200/50" 
                : "bg-amber-50 text-amber-700 border-amber-200/50"
            )}>
              <span className={cn(
                "h-1.5 w-1.5 rounded-full shrink-0", 
                isLive ? "bg-emerald-500 animate-pulse" : "bg-amber-500 animate-pulse"
              )} />
              <span className="hidden xs:inline">
                {isLive ? "API Connected (Live)" : "Demo Mode (Offline Mock)"}
              </span>
            </div>

            <button 
              onClick={() => {
                setChecking(true);
                // Refresh logic to trigger API recheck
                setTimeout(() => setChecking(false), 600);
              }}
              className="p-2 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-500 hover:text-slate-800 transition-colors"
            >
              <RefreshCw className={cn("h-4 w-4", checking && "animate-spin")} />
            </button>
          </div>
        </header>

        {/* Content Wrapper */}
        <main className="flex-1 overflow-y-auto p-6 md:p-8 bg-[#FBFBFC]">
          {children}
        </main>
      </div>

      {/* Mobile Drawer Navigation overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 bg-slate-900/25 backdrop-blur-sm z-30 lg:hidden">
          <div className="w-64 h-full bg-white flex flex-col shadow-2xl relative">
            <button
              onClick={() => setSidebarOpen(false)}
              className="absolute top-4 right-4 p-2 rounded-xl border border-slate-100 text-slate-500 hover:text-slate-800 transition-colors"
            >
              <X className="h-5 w-5" />
            </button>

            <div className="flex items-center gap-2 px-6 py-5 border-b border-slate-100">
              <div className="rounded-xl bg-slate-900 p-2 text-white">
                <ShieldAlert className="h-5 w-5" />
              </div>
              <span className="text-lg font-bold tracking-tight text-slate-900">
                Sentinel<span className="text-sky-600">X</span>
              </span>
            </div>

            <nav className="flex-1 px-4 py-6 space-y-1.5 overflow-y-auto">
              {navItems.map((item) => {
                const isActive = pathname === item.href;
                const Icon = item.icon;
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    onClick={() => setSidebarOpen(false)}
                    className={cn(
                      "flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-semibold tracking-wide transition-all",
                      isActive
                        ? "bg-sky-50 text-sky-700 border border-sky-100/50"
                        : "text-slate-500 hover:text-slate-900 hover:bg-slate-50 border border-transparent"
                    )}
                  >
                    <Icon className={cn("h-4.5 w-4.5 shrink-0", isActive ? "text-sky-600" : "text-slate-400")} />
                    {item.name}
                  </Link>
                );
              })}
            </nav>
          </div>
        </div>
      )}
    </div>
  );
}
