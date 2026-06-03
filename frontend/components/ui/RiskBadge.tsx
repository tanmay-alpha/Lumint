"use client";

import React from "react";
import { motion } from "framer-motion";
import { twMerge } from "tailwind-merge";

export type RiskLevel = "safe" | "warn" | "danger" | "critical" | "unknown";

// Legacy variant values used in old dashboard page
type LegacyVariant = "safe" | "medium" | "high" | "critical" | "clean";

export interface RiskBadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  /** New API: pass a normalised RiskLevel */
  level?: RiskLevel;
  /** Legacy API: pass variant string from old components */
  variant?: LegacyVariant | string;
  size?: "sm" | "md";
  pulse?: boolean;
  className?: string;
}

const variantStyles: Record<RiskLevel, { bg: string; text: string; dot: string; label: string }> = {
  safe: {
    bg:    "bg-[var(--color-safe-subtle)]",
    text:  "text-[var(--color-safe)]",
    dot:   "bg-[var(--color-safe)]",
    label: "SAFE",
  },
  warn: {
    bg:    "bg-[var(--color-warn-subtle)]",
    text:  "text-[var(--color-warn)]",
    dot:   "bg-[var(--color-warn)]",
    label: "SUSPICIOUS",
  },
  danger: {
    bg:    "bg-[var(--color-danger-subtle)]",
    text:  "text-[var(--color-danger)]",
    dot:   "bg-[var(--color-danger)]",
    label: "HIGH RISK",
  },
  critical: {
    bg:    "bg-[var(--color-critical-subtle)]",
    text:  "text-[var(--color-critical)]",
    dot:   "bg-[var(--color-critical)]",
    label: "CRITICAL",
  },
  unknown: {
    bg:    "bg-[var(--color-surface-2)]",
    text:  "text-[var(--color-text-muted)]",
    dot:   "bg-[var(--color-text-muted)]",
    label: "UNKNOWN",
  },
};

// Map backend risk strings (and old variant values) to RiskLevel
export function toRiskLevel(raw: string | undefined | null): RiskLevel {
  const s = (raw ?? "").toUpperCase();
  if (s === "CLEAN" || s === "SAFE")                return "safe";
  if (s === "SUSPICIOUS" || s === "WARN" || s === "MEDIUM") return "warn";
  if (s === "HIGH" || s === "HIGH RISK")            return "danger";
  if (s === "CRITICAL")                             return "critical";
  // numeric-ish
  if (s === "LOW")                                  return "safe";
  return "unknown";
}

export const RiskBadge = ({
  level,
  variant,
  size = "md",
  pulse = false,
  className,
  ...props
}: RiskBadgeProps) => {
  // Resolve: new `level` prop takes precedence over legacy `variant`
  const resolvedLevel: RiskLevel = level ?? toRiskLevel(variant);
  const styles = variantStyles[resolvedLevel];
  const shouldPulse = pulse && (resolvedLevel === "danger" || resolvedLevel === "critical");

  return (
    <span
      className={twMerge(
        "inline-flex items-center gap-1.5 rounded-full font-semibold tracking-widest uppercase",
        size === "sm" ? "px-2 py-0.5 text-[11px]" : "px-3 py-1 text-[12px]",
        styles.bg,
        styles.text,
        className
      )}
      {...props}
    >
      <motion.span
        className={twMerge("rounded-full shrink-0", size === "sm" ? "h-1.5 w-1.5" : "h-2 w-2", styles.dot)}
        initial={shouldPulse ? { scale: 1 } : false}
        animate={shouldPulse ? { scale: [1, 1.4, 1] } : {}}
        transition={{ duration: 0.6, ease: "easeInOut" }}
      />
      {styles.label}
    </span>
  );
};

// Backward-compat: accepts raw backend string
export const RiskBadgeFromBackend = ({ level, ...rest }: Omit<RiskBadgeProps, "level"> & { level: string }) => (
  <RiskBadge level={toRiskLevel(level)} {...rest} />
);

export default RiskBadge;
