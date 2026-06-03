"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Shield,
  Link2,
  GitBranch,
  Smartphone,
  Activity,
  Settings,
  ChevronLeft,
  ChevronRight,
  Menu,
  X,
  Bell,
  Zap,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { twMerge } from "tailwind-merge";
import client from "@/lib/api/client";

const NAV_ITEMS = [
  { name: "Dashboard",    href: "/dashboard",             icon: LayoutDashboard, desc: "Threat telemetry overview" },
  { name: "DocShield",    href: "/docshield",             icon: Shield,          desc: "Document forensics" },
  { name: "PhishShield",  href: "/phishshield",           icon: Link2,           desc: "URL & domain analysis" },
  { name: "Fraud DNA",    href: "/fraud-dna",             icon: GitBranch,       desc: "Campaign network graph" },
  { name: "UPI Shield",   href: "/upi-shield",            icon: Smartphone,      desc: "Payment screenshot scan" },
  { name: "Activity",     href: "/events",                icon: Activity,        desc: "Event timeline" },
  { name: "Settings",     href: "/settings",              icon: Settings,        desc: "Configuration" },
] as const;

const PAGE_LABELS: Record<string, string> = {
  "/dashboard":   "Dashboard Overview",
  "/docshield":   "DocShield · Document Forensics",
  "/phishshield": "PhishShield · Link Analysis",
  "/fraud-dna":   "Fraud DNA · Campaign Network",
  "/upi-shield":  "UPI Shield · Screenshot Analysis",
  "/events":      "Activity Timeline",
  "/settings":    "Settings",
};

// Lumint glow dot logo
const LumintLogo = () => (
  <div className="flex items-center gap-2.5 select-none">
    <div className="relative flex h-8 w-8 items-center justify-center">
      <div className="absolute inset-0 rounded-lg bg-[var(--color-accent)] opacity-10 blur-sm" />
      <div className="relative h-7 w-7 rounded-lg bg-[var(--color-text-primary)] flex items-center justify-center shadow-md">
        <Zap className="h-4 w-4 text-white" strokeWidth={2.5} />
      </div>
    </div>
    <span className="font-display text-[22px] text-[var(--color-text-primary)] leading-none">
      Lumint
    </span>
  </div>
);

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

  const sidebarWidth = collapsed ? 64 : 240;

  const NavItem = ({
    item,
    mobile = false,
  }: {
    item: (typeof NAV_ITEMS)[number];
    mobile?: boolean;
  }) => {
    const isActive = pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href));
    return (
      <Link
        href={item.href}
        onClick={() => setMobileOpen(false)}
        className={twMerge(
          "relative flex items-center gap-3 rounded-xl transition-all duration-150 group",
          collapsed && !mobile ? "px-3.5 py-3 justify-center" : "px-3.5 py-2.5",
          isActive
            ? "bg-[var(--color-accent-subtle)] text-[var(--color-accent)]"
            : "text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-2)] hover:text-[var(--color-text-primary)]"
        )}
      >
        {/* Active indicator bar */}
        {isActive && (
          <motion.span
            layoutId="active-nav-bar"
            className="absolute left-0 top-1/4 h-1/2 w-[3px] rounded-r-full bg-[var(--color-accent)]"
          />
        )}

        <item.icon
          className={twMerge(
            "h-[18px] w-[18px] shrink-0 transition-colors",
            isActive ? "text-[var(--color-accent)]" : "text-[var(--color-text-muted)] group-hover:text-[var(--color-text-primary)]"
          )}
        />

        {/* Label */}
        <AnimatePresence>
          {(!collapsed || mobile) && (
            <motion.div
              initial={{ opacity: 0, width: 0 }}
              animate={{ opacity: 1, width: "auto" }}
              exit={{ opacity: 0, width: 0 }}
              transition={{ duration: 0.2 }}
              className="flex flex-col overflow-hidden whitespace-nowrap"
            >
              <span className={twMerge("text-[13px] font-semibold leading-tight", isActive && "text-[var(--color-accent)]")}>
                {item.name}
              </span>
              {!collapsed && (
                <span className="text-[10px] text-[var(--color-text-muted)] font-normal leading-tight mt-0.5">
                  {item.desc}
                </span>
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Tooltip when collapsed */}
        {collapsed && !mobile && (
          <div className="absolute left-full ml-3 hidden group-hover:flex items-center px-2.5 py-1.5 rounded-lg bg-[var(--color-text-primary)] text-white text-[12px] font-medium shadow-lg whitespace-nowrap z-50 pointer-events-none">
            {item.name}
          </div>
        )}
      </Link>
    );
  };

  const SidebarContent = ({ mobile = false }: { mobile?: boolean }) => (
    <>
      {/* Logo */}
      <div className={twMerge("px-4 py-5 border-b border-[var(--color-border)]", collapsed && !mobile && "px-3.5")}>
        {collapsed && !mobile ? (
          <div className="flex items-center justify-center h-8 w-8 mx-auto">
            <Zap className="h-5 w-5 text-[var(--color-text-primary)]" strokeWidth={2.5} />
          </div>
        ) : (
          <LumintLogo />
        )}
      </div>

      {/* Nav */}
      <nav className={twMerge("flex-1 py-4 space-y-0.5", collapsed && !mobile ? "px-2" : "px-3")}>
        {NAV_ITEMS.map((item) => (
          <NavItem key={item.href} item={item} mobile={mobile} />
        ))}
      </nav>

      {/* Footer */}
      <div className={twMerge("border-t border-[var(--color-border)] p-3", collapsed && !mobile && "px-2")}>
        {!collapsed || mobile ? (
          <span className="font-mono text-[10px] text-[var(--color-text-muted)] px-1">
            v1.0.0 · research build
          </span>
        ) : null}
      </div>
    </>
  );

  return (
    <div className="relative min-h-screen bg-[var(--color-canvas)] text-[var(--color-text-primary)] flex overflow-hidden">
      {/* Very subtle gradient mesh */}
      <div className="absolute inset-0 hero-mesh pointer-events-none opacity-60" />

      {/* ── SIDEBAR DESKTOP ── */}
      <motion.aside
        animate={{ width: sidebarWidth }}
        transition={{ type: "spring", stiffness: 320, damping: 30 }}
        className="hidden lg:flex flex-col shrink-0 bg-[var(--color-surface)] border-r border-[var(--color-border)] relative z-30 overflow-hidden"
        style={{ minWidth: sidebarWidth }}
      >
        <SidebarContent />

        {/* Collapse toggle */}
        <button
          onClick={() => setCollapsed((c) => !c)}
          className="absolute bottom-14 right-0 translate-x-1/2 h-6 w-6 flex items-center justify-center rounded-full bg-[var(--color-surface)] border border-[var(--color-border)] text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] shadow-1 z-40"
          aria-label="Toggle sidebar"
        >
          {collapsed ? <ChevronRight className="h-3 w-3" /> : <ChevronLeft className="h-3 w-3" />}
        </button>
      </motion.aside>

      {/* ── MOBILE DRAWER ── */}
      <AnimatePresence>
        {mobileOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 0.4 }}
              exit={{ opacity: 0 }}
              onClick={() => setMobileOpen(false)}
              className="fixed inset-0 bg-black z-40 lg:hidden"
            />
            <motion.aside
              initial={{ x: "-100%" }}
              animate={{ x: 0 }}
              exit={{ x: "-100%" }}
              transition={{ type: "spring", damping: 28, stiffness: 260 }}
              className="fixed inset-y-0 left-0 w-64 bg-[var(--color-surface)] border-r border-[var(--color-border)] z-50 flex flex-col lg:hidden"
            >
              <button
                onClick={() => setMobileOpen(false)}
                className="absolute top-4 right-4 h-8 w-8 flex items-center justify-center rounded-lg border border-[var(--color-border)] text-[var(--color-text-muted)]"
              >
                <X className="h-4 w-4" />
              </button>
              <SidebarContent mobile />
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      {/* ── MAIN AREA ── */}
      <div className="flex-1 flex flex-col min-w-0 relative z-20">
        {/* Topbar */}
        <header className="h-14 shrink-0 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* Mobile burger */}
            <button
              onClick={() => setMobileOpen(true)}
              className="lg:hidden h-8 w-8 flex items-center justify-center rounded-lg border border-[var(--color-border)] text-[var(--color-text-secondary)]"
            >
              <Menu className="h-4 w-4" />
            </button>

            {/* Breadcrumb */}
            <div className="flex items-center gap-2 text-[13px]">
              <span className="text-[var(--color-text-muted)]">Lumint</span>
              <span className="text-[var(--color-border-strong)]">/</span>
              <span className="font-medium text-[var(--color-text-primary)]">
                {PAGE_LABELS[pathname] ?? "Platform"}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Backend health */}
            <div className="flex items-center gap-1.5">
              {isOnline === null ? (
                <span className="h-2 w-2 rounded-full bg-[var(--color-border-strong)] animate-pulse" />
              ) : isOnline ? (
                <span className="h-2 w-2 rounded-full bg-[var(--color-safe)] animate-pulse" />
              ) : (
                <span className="h-2 w-2 rounded-full bg-[var(--color-danger)]" />
              )}
              <span className="text-[11px] font-mono text-[var(--color-text-muted)]">
                {isOnline === null ? "checking" : isOnline ? "API online" : "API offline"}
              </span>
            </div>

            {/* AI ready badge */}
            {isOnline && (
              <span className="flex items-center gap-1 text-[11px] font-semibold px-2.5 py-1 rounded-full bg-[var(--color-accent-subtle)] text-[var(--color-accent)]">
                <Zap className="h-3 w-3" strokeWidth={2.5} />
                AI Ready
              </span>
            )}

            {/* Bell */}
            <button className="h-8 w-8 flex items-center justify-center rounded-lg text-[var(--color-text-muted)] hover:bg-[var(--color-surface-2)]">
              <Bell className="h-4 w-4" />
            </button>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto p-6 lg:p-8">
          <motion.div
            key={pathname}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, ease: "easeOut" }}
            className="max-w-7xl mx-auto space-y-8"
          >
            {children}
          </motion.div>
        </main>
      </div>
    </div>
  );
}
