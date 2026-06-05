"use client";

import React from "react";
import { motion } from "framer-motion";
import { twMerge } from "tailwind-merge";

export interface FeatureBarContribution {
  name: string;
  value: number;       // Raw value
  contribution: number; // -100 to +100 (positive increases risk)
}

export interface FeatureBarProps {
  features: FeatureBarContribution[];
  title?: string;
  className?: string;
}

export const FeatureBar = ({
  features,
  title = "EXPLAINABLE FORENSICS (FEATURE CONTRIBUTIONS)",
  className,
}: FeatureBarProps) => {
  const maxAbs = Math.max(...features.map((f) => Math.abs(f.contribution)), 1);

  return (
    <div className={twMerge("space-y-4", className)}>
      <span className="text-label text-text-secondary block">
        {title}
      </span>

      <div className="space-y-3">
        {features.map((feature, i) => {
          const pct = Math.min((Math.abs(feature.contribution) / maxAbs) * 100, 100);
          const isPositive = feature.contribution >= 0;

          return (
            <div key={feature.name} className="flex items-center justify-between gap-4">
              {/* Feature info */}
              <div className="flex flex-col min-w-0">
                <span className="text-body text-text-primary truncate font-medium max-w-[180px]" title={feature.name}>
                  {feature.name}
                </span>
                <span className="font-mono text-[10px] text-text-muted">
                  VALUE: {typeof feature.value === "number" ? feature.value.toFixed(2) : String(feature.value)}
                </span>
              </div>

              {/* Bar visualization */}
              <div className="flex-1 flex items-center gap-3">
                <div className="flex-1 h-2 rounded bg-surface-raised border border-border-default/50 overflow-hidden relative">
                  <motion.div
                    className={twMerge(
                      "h-full rounded",
                      isPositive ? "bg-risk-high" : "bg-risk-none"
                    )}
                    initial={{ width: "0%" }}
                    animate={{ width: `${pct}%` }}
                    transition={{ duration: 0.7, delay: i * 0.04, ease: "easeOut" }}
                  />
                </div>

                {/* Percentage label */}
                <span
                  className={twMerge(
                    "font-mono text-[12px] font-medium shrink-0 w-14 text-right",
                    isPositive ? "text-risk-high" : "text-risk-none"
                  )}
                >
                  {feature.contribution > 0 ? "+" : ""}
                  {feature.contribution.toFixed(1)}%
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 pt-1 border-t border-border-muted">
        <div className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-risk-high" />
          <span className="text-[10px] text-text-muted font-medium uppercase tracking-wider">Increases Threat</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-risk-none" />
          <span className="text-[10px] text-text-muted font-medium uppercase tracking-wider">Mitigates Threat</span>
        </div>
      </div>
    </div>
  );
};

export default FeatureBar;
