"use client";

import React from "react";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export type RiskVariant = "critical" | "high" | "medium" | "low" | "safe";

export interface RiskBadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant: RiskVariant;
  className?: string;
}

const variantStyles: Record<
  RiskVariant,
  { bg: string; text: string; dot: string }
> = {
  critical: {
    bg: "bg-risk-critical/10",
    text: "text-risk-critical",
    dot: "bg-risk-critical",
  },
  high: {
    bg: "bg-risk-high/10",
    text: "text-risk-high",
    dot: "bg-risk-high",
  },
  medium: {
    bg: "bg-risk-medium/10",
    text: "text-risk-medium",
    dot: "bg-risk-medium",
  },
  low: {
    bg: "bg-accent-blue/10",
    text: "text-accent-blue",
    dot: "bg-accent-blue",
  },
  safe: {
    bg: "bg-risk-safe/10",
    text: "text-risk-safe",
    dot: "bg-risk-safe",
  },
};

export const RiskBadge = ({
  variant,
  className,
  ...props
}: RiskBadgeProps) => {
  const styles = variantStyles[variant];

  return (
    <span
      className={twMerge(
        "inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-[10px] font-bold tracking-wider uppercase",
        styles.bg,
        styles.text,
        className
      )}
      {...props}
    >
      <span className={clsx("h-1.5 w-1.5 rounded-full", styles.dot)} />
      {variant}
    </span>
  );
};

export default RiskBadge;
