"use client";

import React from "react";
import { motion } from "framer-motion";
import { twMerge } from "tailwind-merge";

export interface XAIBarFeature {
  name: string;
  value: number;       // Raw value (for display)
  contribution: number; // -100 to +100, positive = increases risk
}

export interface XAIBarProps {
  features: XAIBarFeature[];
  title?: string;
  className?: string;
}

function clamp(v: number, min: number, max: number) {
  return Math.min(Math.max(v, min), max);
}

export const XAIBar = ({ features, title = "Feature contributions", className }: XAIBarProps) => {
  const maxAbs = Math.max(...features.map((f) => Math.abs(f.contribution)), 1);

  return (
    <div className={twMerge("space-y-3", className)}>
      <p className="text-label uppercase tracking-widest text-[var(--color-text-muted)] text-[12px]">
        {title}
      </p>

      <div className="space-y-2.5">
        {features.map((feature, i) => {
          const pct = clamp((Math.abs(feature.contribution) / maxAbs) * 100, 0, 100);
          const isPositive = feature.contribution >= 0; // positive = risk increasing

          return (
            <div key={feature.name} className="flex items-center gap-3">
              {/* Feature name */}
              <span
                className="font-mono text-[12px] text-[var(--color-text-secondary)] shrink-0"
                style={{ width: 140, textOverflow: "ellipsis", overflow: "hidden", whiteSpace: "nowrap" }}
                title={feature.name}
              >
                {feature.name}
              </span>

              {/* Bar track */}
              <div className="flex-1 h-[6px] rounded-full bg-[var(--color-surface-2)] overflow-hidden">
                <motion.div
                  className="h-full rounded-full"
                  style={{
                    background: isPositive
                      ? "var(--color-danger)"
                      : "var(--color-safe)",
                    opacity: 0.85,
                  }}
                  initial={{ width: "0%" }}
                  animate={{ width: `${pct}%` }}
                  transition={{
                    duration: 0.6,
                    delay: i * 0.05,
                    ease: "easeOut",
                  }}
                />
              </div>

              {/* Percentage label */}
              <span
                className={twMerge(
                  "font-mono text-[11px] shrink-0 w-10 text-right",
                  isPositive ? "text-[var(--color-danger)]" : "text-[var(--color-safe)]"
                )}
              >
                {feature.contribution > 0 ? "+" : ""}
                {feature.contribution.toFixed(1)}%
              </span>
            </div>
          );
        })}
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 pt-1">
        <div className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-[var(--color-danger)]" />
          <span className="text-[10px] text-[var(--color-text-muted)]">Increases risk</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-[var(--color-safe)]" />
          <span className="text-[10px] text-[var(--color-text-muted)]">Reduces risk</span>
        </div>
      </div>
    </div>
  );
};

export default XAIBar;
