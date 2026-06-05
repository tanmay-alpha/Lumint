"use client";

import React, { useEffect, useState } from "react";
import { Menu, Bell, Zap, Sun, Moon } from "lucide-react";
import { twMerge } from "tailwind-merge";

export interface TopbarProps {
  isOnline: boolean | null;
  setMobileOpen: (v: boolean) => void;
  pathname: string;
  pageLabels: Record<string, string>;
}

export const Topbar = ({
  isOnline,
  setMobileOpen,
  pathname,
  pageLabels,
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
        {/* API Connection Health */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-surface-raised/60 border border-border-default/40">
          <span className={twMerge(
            "h-1.5 w-1.5 rounded-full shrink-0",
            isOnline === null ? "bg-border-strong animate-pulse" : isOnline ? "bg-risk-none risk-dot-pulse" : "bg-risk-high"
          )} />
          <span className="font-mono text-[10px] text-text-secondary font-medium tracking-wide">
            {isOnline === null ? "CHECKING" : isOnline ? "API ONLINE" : "API OFFLINE"}
          </span>
        </div>

        {/* AI Ready Indicator */}
        {isOnline && (
          <span className="flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-md bg-ai-subtle border border-ai-border/40 text-ai-text uppercase tracking-wide">
            <Zap className="h-3 w-3 shrink-0" strokeWidth={2.5} />
            AI READY
          </span>
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
