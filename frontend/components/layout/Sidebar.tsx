"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  FileSearch,
  ShieldAlert,
  Network,
  Smartphone,
  Activity,
  Settings,
  ChevronLeft,
  ChevronRight,
  Zap,
  Moon,
  Sun,
  Shield,
  History,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { twMerge } from "tailwind-merge";

const NAV_GROUPS = [
  {
    title: "Overview",
    items: [
      { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard, desc: "Threat telemetry overview" },
    ],
  },
  {
    title: "Analysis",
    items: [
      { name: "DocShield", href: "/docshield", icon: FileSearch, desc: "Document forensics", beta: true },
      { name: "PhishShield", href: "/phishshield", icon: ShieldAlert, desc: "URL & domain analysis", beta: true },
      { name: "Fraud DNA", href: "/fraud-dna", icon: Network, desc: "Campaign network graph", beta: true },
      { name: "UPI Shield", href: "/upi-shield", icon: Smartphone, desc: "Payment screenshot scan" },
    ],
  },
  {
    title: "Intelligence",
    items: [
      { name: "Activity", href: "/events", icon: Activity, desc: "Event timeline" },
      { name: "History", href: "/dashboard/history", icon: History, desc: "Past scans (local)" },
      { name: "Research", href: "/dashboard/research", icon: Zap, desc: "Statistical analysis & paper" },
    ],
  },
  {
    title: "System",
    items: [
      { name: "Settings", href: "/settings", icon: Settings, desc: "Configuration" },
    ],
  },
];

export interface SidebarProps {
  collapsed: boolean;
  setCollapsed: (v: boolean) => void;
  mobileOpen: boolean;
  setMobileOpen: (v: boolean) => void;
}

const LumintLogo = ({ collapsed }: { collapsed: boolean }) => (
  <Link href="/" className="flex items-center gap-2.5 select-none font-sans no-underline">
    <div className="relative flex h-9 w-9 items-center justify-center shrink-0">
      <div className="absolute inset-0 rounded-lg bg-brand/10 opacity-60 blur-sm" />
      <div className="relative h-9 w-9 rounded-lg bg-brand flex items-center justify-center shadow-md">
        <Shield className="h-5 w-5 text-white" strokeWidth={2.5} />
      </div>
    </div>
    {!collapsed && (
      <div className="flex flex-col leading-tight">
        <span className="text-[18px] tracking-tight text-text-primary font-semibold">
          Lumint
        </span>
      </div>
    )}
  </Link>
);

const SystemStatus = ({
  collapsed,
}: {
  collapsed: boolean;
}) => {
  const [theme, setTheme] = React.useState<"light" | "dark">("light");

  React.useEffect(() => {
    const stored = localStorage.getItem("theme");
    const docTheme = document.documentElement.getAttribute("data-theme");
    const activeTheme = stored === "dark" || docTheme === "dark" ? "dark" : "light";
    setTheme(activeTheme);
  }, []);

  const toggleTheme = () => {
    const nextTheme = theme === "light" ? "dark" : "light";
    setTheme(nextTheme);
    document.documentElement.setAttribute("data-theme", nextTheme);
    localStorage.setItem("theme", nextTheme);
  };

  // Client-side mode: analysis runs entirely in the browser, so the
  // system is always "Ready" regardless of backend connectivity.
  const statusText = "Ready";
  const statusColor = "bg-safe";

  if (collapsed) {
    return (
      <div className="flex flex-col items-center gap-4 py-2">
        <span className={`h-2 w-2 rounded-full ${statusColor} animate-pulse`} />
        <button
          onClick={toggleTheme}
          className="text-text-muted hover:text-text-primary transition-colors"
          title={theme === "light" ? "Dark Mode" : "Light Mode"}
        >
          {theme === "light" ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
        </button>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-between px-3 py-2.5 w-full bg-surface-raised/40 border border-border-default/45 rounded-lg">
      <div className="flex items-center gap-2">
        <span className={`h-2 w-2 rounded-full ${statusColor} animate-pulse`} />
        <span className="font-sans text-[10px] font-semibold text-text-secondary tracking-wide uppercase">
          {statusText}
        </span>
      </div>
      <button
        onClick={toggleTheme}
        className="h-7 w-7 flex items-center justify-center rounded-md border border-border-default bg-surface hover:bg-surface-raised text-text-muted hover:text-text-primary transition-all shadow-sm"
        title={theme === "light" ? "Switch to Dark" : "Switch to Light"}
      >
        {theme === "light" ? <Moon className="h-3.5 w-3.5" /> : <Sun className="h-3.5 w-3.5" />}
      </button>
    </div>
  );
};

export const Sidebar = ({
  collapsed,
  setCollapsed,
  mobileOpen,
  setMobileOpen,
}: SidebarProps) => {
  const pathname = usePathname();

  const renderNavItem = (
    item: (typeof NAV_GROUPS)[number]["items"][number],
    isMobile = false
  ) => {
    const isActive =
      pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href));
    return (
      <Link
        key={item.href}
        href={item.href}
        onClick={() => setMobileOpen(false)}
        className={twMerge(
          "relative flex items-center gap-3 rounded-lg transition-all duration-150 group",
          collapsed && !isMobile ? "px-3 py-3 justify-center" : "px-3.5 py-2.5",
          isActive
            ? "bg-[var(--brand-muted)] text-brand border border-brand/10"
            : "text-text-secondary hover:bg-surface-raised hover:text-text-primary border border-transparent"
        )}
      >
        {isActive && (
          <span className="absolute left-0 top-0 h-full w-[2px] bg-brand" />
        )}

        <item.icon
          className={twMerge(
            "h-[18px] w-[18px] shrink-0 transition-colors",
            isActive ? "text-brand" : "text-text-muted group-hover:text-text-primary"
          )}
        />

        {(!collapsed || isMobile) && (
          <div className="flex flex-col overflow-hidden whitespace-nowrap">
            <span className={twMerge(
              "text-[13px] font-medium font-sans leading-tight flex items-center gap-1.5",
              isActive ? "text-brand" : "text-text-primary"
            )}>
              {item.name}
              {item.beta && (
                <span className="text-[8px] font-bold tracking-wider uppercase bg-brand/15 text-brand px-1 py-0.5 rounded-sm leading-none">
                  BETA
                </span>
              )}
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
      <div
        className={twMerge(
          "px-4.5 py-4 border-b border-border-muted flex items-center justify-between",
          collapsed && !isMobile && "px-3.5 justify-center"
        )}
      >
        <LumintLogo collapsed={collapsed && !isMobile} />
      </div>

      {/* Nav Link list */}
      <nav className="flex-1 py-4 overflow-y-auto space-y-4">
        {NAV_GROUPS.map((group) => (
          <div key={group.title} className="space-y-1">
            {(!collapsed || isMobile) && (
              <div className="px-3.5 mt-3 mb-1.5 text-[10px] font-mono tracking-wider text-text-muted uppercase font-semibold select-none">
                {group.title}
              </div>
            )}
            <div className={twMerge("space-y-1", collapsed && !isMobile ? "px-2" : "px-3")}>
              {group.items.map((item) => renderNavItem(item, isMobile))}
            </div>
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div className={twMerge("p-3 border-t border-border-muted bg-surface-raised/40", collapsed && !isMobile && "px-1")}>
        <SystemStatus collapsed={collapsed && !isMobile} />
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
