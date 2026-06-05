"use client";

import React from "react";
import { twMerge } from "tailwind-merge";

export type RiskVariant =
  | "safe" | "warn" | "high" | "critical"
  | "genuine" | "forged" | "phishing"
  | "ai" | "neutral";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: RiskVariant;
  size?: "sm" | "md";
  dot?: boolean;
  pulse?: boolean;
}

const VARIANT_STYLES: Record<RiskVariant, string> = {
  safe:     "bg-[var(--safe-bg)]     text-[var(--safe)]     border border-[var(--safe-border)]",
  warn:     "bg-[var(--warn-bg)]     text-[var(--warn)]     border border-[var(--warn-border)]",
  high:     "bg-[var(--high-bg)]     text-[var(--high)]     border border-[var(--high-border)]",
  critical: "bg-[var(--critical-bg)] text-[var(--critical)] border border-[var(--critical-border)]",
  genuine:  "bg-[var(--safe-bg)]     text-[var(--safe)]     border border-[var(--safe-border)]",
  forged:   "bg-[var(--high-bg)]     text-[var(--high)]     border border-[var(--high-border)]",
  phishing: "bg-[var(--critical-bg)] text-[var(--critical)] border border-[var(--critical-border)]",
  ai:       "bg-[var(--ai-muted)]    text-[var(--ai-text)]  border border-[var(--ai-border)]",
  neutral:  "bg-[var(--surface-2)]   text-[var(--text-3)]   border border-[var(--border)]",
};

const DOT_COLORS: Record<RiskVariant, string> = {
  safe:     "bg-[var(--safe)]",
  warn:     "bg-[var(--warn)]",
  high:     "bg-[var(--high)]",
  critical: "bg-[var(--critical)]",
  genuine:  "bg-[var(--safe)]",
  forged:   "bg-[var(--high)]",
  phishing: "bg-[var(--critical)]",
  ai:       "bg-[var(--ai)]",
  neutral:  "bg-[var(--text-4)]",
};

const SIZE_STYLES = {
  sm: "px-1.5 py-0.5 text-[10px] gap-1",
  md: "px-2.5 py-[3px] text-[11px] gap-1.5",
};

export const Badge = ({
  variant = "neutral",
  size = "md",
  dot = false,
  pulse = false,
  children,
  className,
  ...props
}: BadgeProps) => {
  const shouldPulse = pulse && (variant === "high" || variant === "critical" || variant === "warn");

  return (
    <span
      className={twMerge(
        "inline-flex items-center rounded-full font-[var(--font-mono),monospace] font-medium tracking-wide uppercase shrink-0",
        VARIANT_STYLES[variant],
        SIZE_STYLES[size],
        className
      )}
      {...props}
    >
      {dot && (
        <span
          className={twMerge(
            "rounded-full shrink-0",
            size === "sm" ? "h-[5px] w-[5px]" : "h-1.5 w-1.5",
            DOT_COLORS[variant],
            shouldPulse && "risk-dot-pulse"
          )}
        />
      )}
      {children}
    </span>
  );
};

export default Badge;
