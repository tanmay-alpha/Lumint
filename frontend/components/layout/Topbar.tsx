"use client";

import React, { useEffect, useState } from "react";
import { Menu, Bell, Sun, Moon } from "lucide-react";
import { twMerge } from "tailwind-merge";
import Badge from "@/components/ui/Badge";
import type { ApiHealthStatus } from "@/hooks/useApiHealth";

export interface TopbarProps {
  setMobileOpen: (v: boolean) => void;
  pathname: string;
  pageLabels: Record<string, string>;
  /**
   * Current API connection state. Drives the right-hand status pill:
   *   - "online"  → green "API CONNECTED" (+ latency)
   *   - "offline" → red   "API DISCONNECTED"
   *   - "unknown" → pill is hidden (no backend configured yet)
   */
  apiHealth?: ApiHealthStatus;
  /** Last successful probe latency in ms; appended to the pill text when set. */
  apiLatency?: number | null;
}

export const Topbar = ({
  setMobileOpen,
  pathname,
  pageLabels,
  apiHealth = "unknown",
  apiLatency = null,
}: TopbarProps) => {
  const [theme, setTheme] = useState<"light" | "dark">("light");

  useEffect(() => {
    // Check initial theme preference
    const stored = localStorage.getItem("theme");
    const docTheme = document.documentElement.getAttribute("data-theme");
    const activeTheme = (stored === "dark" || docTheme === "dark") ? "dark" : "light";
    document.documentElement.setAttribute("data-theme", activeTheme);
    
    requestAnimationFrame(() => {
      setTheme(activeTheme);
    });
  }, []);

  const toggleTheme = () => {
    const nextTheme = theme === "light" ? "dark" : "light";
    setTheme(nextTheme);
    document.documentElement.setAttribute("data-theme", nextTheme);
    localStorage.setItem("theme", nextTheme);
  };

  return (
    <header className="h-14 shrink-0 border-b border-border-default bg-surface px-5 flex items-center justify-between z-20">
      <div className="flex items-center gap-3">
        {/* Mobile menu trigger */}
        <button
          onClick={() => setMobileOpen(true)}
          className="lg:hidden h-8 w-8 flex items-center justify-center rounded-lg border border-border-default text-text-secondary hover:bg-surface-raised transition-colors"
        >
          <Menu className="h-4 w-4" />
        </button>

        {/* Breadcrumbs */}
        <div className="flex items-center gap-2 text-caption select-none">
          <span className="text-text-muted">Lumint</span>
          <span className="text-border-strong">/</span>
          <span className="font-semibold text-text-primary">
            {pageLabels[pathname] ?? "Platform"}
          </span>
        </div>
      </div>

      <div className="flex items-center gap-3.5">
        {/* API connection status pill */}
        {apiHealth === "online" && (
          <Badge
            variant="safe"
            size="md"
            dot={true}
            className="gap-1"
            title={apiLatency != null ? `Latency: ${apiLatency}ms` : "Healthy"}
          >
            API CONNECTED{apiLatency != null ? ` · ${apiLatency}ms` : ""}
          </Badge>
        )}
        {apiHealth === "offline" && (
          <Badge variant="critical" size="md" dot={true} className="gap-1">
            API DISCONNECTED
          </Badge>
        )}

        {/* Theme Toggle Button */}
        <button
          onClick={toggleTheme}
          className="h-8 w-8 flex items-center justify-center rounded-lg border border-border-default text-text-muted hover:text-text-primary hover:bg-surface-raised transition-colors"
          title={theme === "light" ? "Switch to Dark Mode" : "Switch to Light Mode"}
        >
          {theme === "light" ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
        </button>

        {/* Notifications */}
        <button className="h-8 w-8 flex items-center justify-center rounded-lg text-text-muted hover:text-text-primary hover:bg-surface-raised transition-colors">
          <Bell className="h-4 w-4" />
        </button>
      </div>
    </header>
  );
};

export default Topbar;
