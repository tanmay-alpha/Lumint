"use client";

import React from "react";
import { twMerge } from "tailwind-merge";
import { motion } from "framer-motion";

export interface FeatureContributionItem {
  name: string;
  value?: string | number;
  contribution: number;  // SHAP value — positive increases risk, negative reduces it
  maxContribution?: number;
}

export interface FeatureContributionProps {
  features: FeatureContributionItem[];
  title?: string;
  className?: string;
}

/**
 * FeatureContribution — replaces XAIBar with a polished design.
 *
 * Layout per row:
 *   Col 1: feature name (t-small / text-2) + value (t-mono / text-3, 12px)
 *   Col 2: horizontal bar (6px height, r-full)
 *           positive → brand/high color (increases risk)
 *           negative → safe color (reduces risk)
 *   Col 3: % right-aligned (t-mono)
 *
 * Bars: proportional to max |contribution| in the set.
 * Animation: Framer Motion with 0.04s stagger.
 */
export const FeatureContribution = ({
  features,
  title,
  className,
}: FeatureContributionProps) => {
  if (!features || features.length === 0) return null;

  // Sort by |contribution| descending, limit to 10
  const sorted = [...features]
    .sort((a, b) => Math.abs(b.contribution) - Math.abs(a.contribution))
    .slice(0, 10);

  const maxAbs = Math.max(...sorted.map((f) => Math.abs(f.contribution)), 1);

  return (
    <div className={twMerge("flex flex-col gap-3", className)}>
      {title && (
        <span className="t-label" style={{ color: "var(--text-3)" }}>
          {title}
        </span>
      )}

      <div className="flex flex-col gap-2.5">
        {sorted.map((feature, i) => {
          const pct = (Math.abs(feature.contribution) / maxAbs) * 100;
          const isRisk = feature.contribution >= 0;
          const barColor = isRisk ? "var(--high)" : "var(--safe)";
          const sign = isRisk ? "+" : "";
          const displayVal = Math.abs(feature.contribution) <= 1.05 ? feature.contribution * 100 : feature.contribution;
          const displayPct = `${sign}${displayVal.toFixed(1)}%`;

          return (
            <motion.div
              key={feature.name}
              className="flex items-center gap-3"
              initial={{ opacity: 0, x: -6 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.25, delay: i * 0.04 }}
            >
              {/* Feature name + value */}
              <div className="w-36 shrink-0 flex flex-col gap-0.5">
                <span
                  className="t-small truncate"
                  style={{ color: "var(--text-2)" }}
                  title={feature.name}
                >
                  {feature.name}
                </span>
                {feature.value !== undefined && (
                  <span
                    style={{
                      fontFamily: "var(--font-mono), monospace",
                      fontSize: 11,
                      color: "var(--text-3)",
                      lineHeight: 1,
                    }}
                  >
                    {feature.value}
                  </span>
                )}
              </div>

              {/* Bar */}
              <div
                className="flex-1 min-w-0 h-[6px] rounded-full overflow-hidden"
                style={{ background: "var(--border)" }}
              >
                <motion.div
                  className="h-full rounded-full"
                  style={{ background: barColor }}
                  initial={{ width: 0 }}
                  animate={{ width: `${pct}%` }}
                  transition={{ duration: 0.4, delay: i * 0.04, ease: [0.22, 1, 0.36, 1] }}
                />
              </div>

              {/* Percentage */}
              <span
                className="w-14 text-right t-mono shrink-0"
                style={{
                  fontSize: 11,
                  color: isRisk ? "var(--high)" : "var(--safe)",
                  fontWeight: 500,
                }}
              >
                {displayPct}
              </span>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
};

export default FeatureContribution;
