"use client";

import React from "react";
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
  Zap,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { twMerge } from "tailwind-merge";

const NAV_ITEMS = [
  { name: "Dashboard",    href: "/dashboard",             icon: LayoutDashboard, desc: "Threat telemetry overview" },
  { name: "DocShield",    href: "/docshield",             icon: Shield,          desc: "Document forensics" },
  { name: "PhishShield",  href: "/phishshield",           icon: Link2,           desc: "URL & domain analysis" },
  { name: "Fraud DNA",    href: "/fraud-dna",             icon: GitBranch,       desc: "Campaign network graph" },
  { name: "UPI Shield",   href: "/upi-shield",            icon: Smartphone,      desc: "Payment screenshot scan" },
  { name: "Activity",     href: "/events",                icon: Activity,        desc: "Event timeline" },
  { name: "Research",     href: "/dashboard/research",    icon: Zap,             desc: "Statistical analysis & paper" },
  { name: "Settings",     href: "/settings",              icon: Settings,        desc: "Configuration" },
] as const;

export interface SidebarProps {
  collapsed: boolean;
  setCollapsed: (v: boolean) => void;
  mobileOpen: boolean;
  setMobileOpen: (v: boolean) => void;
}

const LumintLogo = ({ collapsed }: { collapsed: boolean }) => (
  <div className="flex items-center gap-2.5 select-none font-display">
    <div className="relative flex h-8 w-8 items-center justify-center shrink-0">
      <div className="absolute inset-0 rounded-lg bg-brand/10 opacity-60 blur-sm" />
      <div className="relative h-8 w-8 rounded-lg bg-brand flex items-center justify-center shadow-md">
        <Zap className="h-4.5 w-4.5 text-white" strokeWidth={2.5} />
      </div>
    </div>
    {!collapsed && (
      <span className="text-[22px] tracking-tight text-text-primary leading-normal font-semibold">
        Lumint
      </span>
    )}
  </div>
);

export const Sidebar = ({
  collapsed,
  setCollapsed,
  mobileOpen,
  setMobileOpen,
}: SidebarProps) => {
  const pathname = usePathname();

  const renderNavItem = (item: (typeof NAV_ITEMS)[number], isMobile = false) => {
    const isActive = pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href));
    return (
      <Link
        key={item.href}
        href={item.href}
        onClick={() => setMobileOpen(false)}
        className={twMerge(
          "relative flex items-center gap-3 rounded-lg transition-all duration-150 group",
          collapsed && !isMobile ? "px-3 py-3 justify-center" : "px-3.5 py-2.5",
          isActive
            ? "bg-brand-subtle text-accent border border-brand/10"
            : "text-text-secondary hover:bg-surface-raised hover:text-text-primary border border-transparent"
        )}
      >
        {isActive && (
          <motion.span
            layoutId="active-indicator"
            className="absolute left-0 top-1/4 h-1/2 w-[3px] rounded-r-full bg-brand"
            transition={{ type: "spring", stiffness: 380, damping: 30 }}
          />
        )}

        <item.icon
          className={twMerge(
            "h-[18px] w-[18px] shrink-0 transition-colors",
            isActive ? "text-accent" : "text-text-muted group-hover:text-text-primary"
          )}
        />

        {(!collapsed || isMobile) && (
          <div className="flex flex-col overflow-hidden whitespace-nowrap">
            <span className={twMerge("text-[13px] font-semibold leading-tight", isActive && "text-accent")}>
              {item.name}
            </span>
            <span className="text-[10px] text-text-muted font-normal leading-tight mt-0.5">
              {item.desc}
            </span>
          </div>
        )}

        {/* Collapsed tooltip */}
        {collapsed && !isMobile && (
          <div className="absolute left-full ml-3 hidden group-hover:flex items-center px-2.5 py-1.5 rounded-md bg-text-primary text-text-inverse text-[11px] font-medium shadow-md whitespace-nowrap z-50 pointer-events-none">
            {item.name}
          </div>
        )}
      </Link>
    );
  };

  const content = (isMobile = false) => (
    <div className="flex flex-col h-full bg-surface border-r border-border-default">
      {/* Header / Logo */}
      <div className={twMerge("px-4.5 py-4 border-b border-border-muted flex items-center justify-between", collapsed && !isMobile && "px-3.5 justify-center")}>
        <LumintLogo collapsed={collapsed && !isMobile} />
      </div>

      {/* Nav Link list */}
      <nav className={twMerge("flex-1 py-4 space-y-1 overflow-y-auto", collapsed && !isMobile ? "px-2" : "px-3")}>
        {NAV_ITEMS.map((item) => renderNavItem(item, isMobile))}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-border-muted bg-surface-raised/40">
        {(!collapsed || isMobile) ? (
          <div className="flex flex-col gap-1.5" />
        ) : (
          <div className="flex items-center justify-center h-4">
            <span className="h-1.5 w-1.5 rounded-full bg-intel" />
          </div>
        )}
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Sidebar wrapper */}
      <motion.aside
        animate={{ width: collapsed ? 68 : 240 }}
        transition={{ type: "spring", stiffness: 300, damping: 28 }}
        className="hidden lg:block shrink-0 relative z-30 h-screen select-none"
      >
        {content()}
        
        {/* Toggle button */}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="absolute bottom-20 right-0 translate-x-1/2 h-6 w-6 flex items-center justify-center rounded-full bg-surface border border-border-default text-text-muted hover:text-text-primary hover:border-border-strong shadow-sm z-40 transition-all"
        >
          {collapsed ? <ChevronRight className="h-3 w-3" /> : <ChevronLeft className="h-3 w-3" />}
        </button>
      </motion.aside>

      {/* Mobile drawer wrapper */}
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
              transition={{ type: "spring", damping: 25, stiffness: 220 }}
              className="fixed inset-y-0 left-0 w-64 z-50 lg:hidden h-full"
            >
              {content(true)}
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </>
  );
};

export default Sidebar;
