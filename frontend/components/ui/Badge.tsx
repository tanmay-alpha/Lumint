"use client";

import React from "react";
import { twMerge } from "tailwind-merge";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "brand" | "intel" | "safe" | "warn" | "danger" | "critical" | "low" | "muted";
  size?: "sm" | "md";
  dot?: boolean;
}

export const Badge = ({
  children,
  className,
  variant = "default",
  size = "md",
  dot = false,
  ...props
}: BadgeProps) => {
  const baseClass = "inline-flex items-center gap-1.5 rounded-full font-medium tracking-wide text-label uppercase shrink-0";
  
  const variantStyles = {
    default: "bg-surface-raised text-text-primary border border-border-default",
    brand: "bg-brand-subtle text-accent border border-brand/20",
    intel: "bg-intel-subtle text-intel border border-intel/20",
    safe: "bg-risk-none-bg text-risk-none border border-risk-none/20",
    warn: "bg-risk-medium-bg text-risk-medium border border-risk-medium/20",
    danger: "bg-risk-high-bg text-risk-high border border-risk-high/20",
    critical: "bg-risk-critical-bg text-risk-critical border border-risk-critical/20",
    low: "bg-risk-low-bg text-risk-low border border-risk-low/20",
    muted: "bg-transparent text-text-muted border border-border-default",
  };

  const dotColors = {
    default: "bg-text-secondary",
    brand: "bg-accent",
    intel: "bg-intel",
    safe: "bg-risk-none",
    warn: "bg-risk-medium",
    danger: "bg-risk-high",
    critical: "bg-risk-critical",
    low: "bg-risk-low",
    muted: "bg-border-strong",
  };

  const sizeStyles = {
    sm: "px-2 py-0.5 text-[10px]",
    md: "px-2.5 py-0.5 text-[11px]",
  };

  return (
    <span
      className={twMerge(
        baseClass,
        variantStyles[variant],
        sizeStyles[size],
        className
      )}
      {...props}
    >
      {dot && (
        <span className={twMerge(
          "h-1.5 w-1.5 rounded-full shrink-0 risk-dot-pulse",
          dotColors[variant]
        )} />
      )}
      {children}
    </span>
  );
};

export default Badge;
