"use client";

import React from "react";
import { cn } from "@/lib/utils";
import { RiskLevel } from "@/types";

interface ThreatBadgeProps {
  level: RiskLevel | null | string;
  className?: string;
  showDot?: boolean;
}

export const ThreatBadge: React.FC<ThreatBadgeProps> = ({
  level = "CLEAN",
  className,
  showDot = true,
}) => {
  const normalized = (level || "NONE").toUpperCase();

  let styles = "bg-gray-100 text-gray-700 border-gray-200/50";
  let dotColor = "bg-gray-400";
  let label = "Unknown";

  if (normalized === "CLEAN" || normalized === "NORMAL" || normalized === "NONE") {
    styles = "bg-emerald-50 text-emerald-700 border-emerald-200/50 dark:bg-emerald-950/20 dark:text-emerald-400 dark:border-emerald-900/30";
    dotColor = "bg-emerald-500";
    label = normalized === "NONE" ? "No Threat" : (normalized === "NORMAL" ? "Normal" : "Clean");
  } else if (normalized === "SUSPICIOUS" || normalized === "ELEVATED") {
    styles = "bg-amber-50 text-amber-700 border-amber-200/50 dark:bg-amber-950/20 dark:text-amber-400 dark:border-amber-900/30";
    dotColor = "bg-amber-500";
    label = normalized === "ELEVATED" ? "Elevated Risk" : "Suspicious";
  } else if (normalized === "HIGH" || normalized === "CRITICAL") {
    styles = "bg-rose-50 text-rose-700 border-rose-200/50 dark:bg-rose-950/20 dark:text-rose-400 dark:border-rose-900/30";
    dotColor = "bg-rose-500";
    label = normalized === "CRITICAL" ? "Critical threat" : "High Risk";
  }

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-semibold tracking-wide transition-colors",
        styles,
        className
      )}
    >
      {showDot && (
        <span className={cn("relative flex h-2 w-2")}>
          {(normalized === "HIGH" || normalized === "CRITICAL") && (
            <span className={cn("absolute inline-flex h-full w-full animate-ping rounded-full opacity-75", dotColor)}></span>
          )}
          <span className={cn("relative inline-flex h-2 w-2 rounded-full", dotColor)}></span>
        </span>
      )}
      {label}
    </span>
  );
};

export default ThreatBadge;
