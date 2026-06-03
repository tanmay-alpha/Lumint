"use client";

import React from "react";
import { twMerge } from "tailwind-merge";

export interface ConfidenceTagProps {
  confidence: number; // 0–100
  className?: string;
}

export const ConfidenceTag = ({ confidence, className }: ConfidenceTagProps) => {
  const pct = Math.min(Math.max(confidence, 0), 100);

  const colorClass =
    pct > 85
      ? "bg-[var(--color-safe-subtle)] text-[var(--color-safe)]"
      : pct >= 60
      ? "bg-[var(--color-warn-subtle)] text-[var(--color-warn)]"
      : "bg-[var(--color-danger-subtle)] text-[var(--color-danger)]";

  return (
    <span
      className={twMerge(
        "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 font-mono text-[11px] font-medium",
        colorClass,
        className
      )}
    >
      <span className="tabular-nums">{pct}%</span>
      <span className="text-[10px] opacity-80">confident</span>
    </span>
  );
};

export default ConfidenceTag;
