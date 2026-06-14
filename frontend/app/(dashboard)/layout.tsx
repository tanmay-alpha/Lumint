"use client";

import React, { useState } from "react";
import { usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import Sidebar from "@/components/layout/Sidebar";
import Topbar from "@/components/layout/Topbar";
import { DemoModeBanner } from "@/components/DemoModeBanner";
import { useApiHealth } from "@/hooks/useApiHealth";

const PAGE_LABELS: Record<string, string> = {
  "/dashboard":   "Dashboard Overview",
  "/docshield":   "DocShield · Document Forensics",
  "/phishshield": "PhishShield · Link Analysis",
  "/fraud-dna":   "Fraud DNA · Campaign Network",
  "/upi-shield":  "UPI Shield · Screenshot Analysis",
  "/events":      "Activity Timeline",
  "/dashboard/research": "Lumint Research Results",
  "/dashboard/history": "Scan History",
  "/settings":    "Settings",
};

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  // User can dismiss the demo-mode banner; session-scoped state.
  const [bannerDismissed, setBannerDismissed] = useState(false);
  // Polls /health every 60s. Exposes status + latency + last error so the
  // banner and topbar can render accurate diagnostics.
  const apiHealth = useApiHealth();

  const showBanner = apiHealth.status !== "online" && !bannerDismissed;

  return (
    <div className="relative min-h-screen bg-canvas text-text-primary flex overflow-hidden">
      {/* Background patterns */}
      <div className="absolute inset-0 mesh-grid-bg opacity-[0.015] pointer-events-none" />
      <div className="absolute inset-0 hero-mesh-bg pointer-events-none" />

      {/* Sidebar Component */}
      <Sidebar
        collapsed={collapsed}
        setCollapsed={setCollapsed}
        mobileOpen={mobileOpen}
        setMobileOpen={setMobileOpen}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 relative z-20">
        {/* Topbar Component */}
        <Topbar
          setMobileOpen={setMobileOpen}
          pathname={pathname}
          pageLabels={PAGE_LABELS}
          apiHealth={apiHealth.status}
          apiLatency={apiHealth.latency}
        />

        {/* Debug: Show current API URL in development */}
        {process.env.NODE_ENV !== "production" && process.env.NEXT_PUBLIC_API_URL && (
          <div className="px-6 pt-1 lg:px-8">
            <div className="max-w-7xl mx-auto">
              <div className="text-[10px] text-[var(--text-4)] font-mono px-4 py-1 bg-[var(--surface-raised)] rounded">
                API: {process.env.NEXT_PUBLIC_API_URL}
              </div>
            </div>
          </div>
        )}

        {/* Demo-mode banner — hidden once the backend reports online.
            User can dismiss; setting is per-session only. */}
        <AnimatePresence>
          {showBanner && (
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.2 }}
              className="px-6 pt-3 lg:px-8 sticky top-0 z-40"
            >
              <div className="max-w-7xl mx-auto">
                <DemoModeBanner
                  status={apiHealth.status}
                  latency={apiHealth.latency}
                  lastError={apiHealth.lastError}
                  onRetry={apiHealth.recheck}
                  onDismiss={() => setBannerDismissed(true)}
                />
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Dynamic page contents — page transition fade */}
        <main className="flex-1 overflow-y-auto p-6 lg:p-8">
          <AnimatePresence mode="wait">
            <motion.div
              key={pathname}
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.1, ease: "easeOut" }}
              className="max-w-7xl mx-auto space-y-8"
            >
              {children}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
}
