"use client";

import React, { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import client from "@/lib/api/client";
import Sidebar from "@/components/layout/Sidebar";
import Topbar from "@/components/layout/Topbar";

const PAGE_LABELS: Record<string, string> = {
  "/dashboard":   "Dashboard Overview",
  "/docshield":   "DocShield · Document Forensics",
  "/phishshield": "PhishShield · Link Analysis",
  "/fraud-dna":   "Fraud DNA · Campaign Network",
  "/upi-shield":  "UPI Shield · Screenshot Analysis",
  "/events":      "Activity Timeline",
  "/dashboard/research": "Lumint Research Results",
  "/settings":    "Settings",
};

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [isOnline, setIsOnline] = useState<boolean | null>(null);
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const check = async () => {
      try {
        const res = await client.getHealth();
        setIsOnline(res.status === "ok");
      } catch {
        setIsOnline(false);
      }
    };
    check();
    const id = setInterval(check, 30_000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="relative min-h-screen bg-canvas text-text-primary flex overflow-hidden">
      {/* Background patterns */}
      <div className="absolute inset-0 mesh-grid-bg opacity-[0.015] pointer-events-none" />
      <div className="absolute inset-0 hero-mesh-bg pointer-events-none" />

      {/* Sidebar Component */}
      <Sidebar
        isOnline={isOnline}
        collapsed={collapsed}
        setCollapsed={setCollapsed}
        mobileOpen={mobileOpen}
        setMobileOpen={setMobileOpen}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 relative z-20">
        {/* Topbar Component */}
        <Topbar
          isOnline={isOnline}
          setMobileOpen={setMobileOpen}
          pathname={pathname}
          pageLabels={PAGE_LABELS}
        />

        {/* Dynamic page contents */}
        <main className="flex-1 overflow-y-auto p-6 lg:p-8">
          <motion.div
            key={pathname}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.25, ease: "easeOut" }}
            className="max-w-7xl mx-auto space-y-8"
          >
            {children}
          </motion.div>
        </main>
      </div>
    </div>
  );
}
