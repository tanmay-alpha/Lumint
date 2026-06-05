"use client";

import React from "react";
import { twMerge } from "tailwind-merge";
import { ArrowUpRight, ArrowDownRight } from "lucide-react";
import { motion } from "framer-motion";

export interface MetricCardProps {
  label: string;
  value: string | number;
  unit?: string;
  trend?: { delta?: string; value?: string; isPositive: boolean; period?: string };
  sparkData?: number[];
  icon?: React.ReactNode;
  className?: string;
}

function MiniSparkline({ data }: { data: number[] }) {
  if (data.length < 2) return null;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const W = 80, H = 32, pad = 2;

  const pts = data.map((v, i) => {
    const x = pad + (i / (data.length - 1)) * (W - pad * 2);
    const y = H - pad - ((v - min) / range) * (H - pad * 2);
    return `${x},${y}`;
  });

  return (
    <svg width={W} height={H} aria-hidden="true" className="shrink-0 opacity-70">
      <polyline
        points={pts.join(" ")}
        fill="none"
        stroke="var(--brand)"
        strokeWidth={1.5}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

/**
 * MetricCard — replaces StatCard.
 * Large JetBrains Mono number, trend indicator, optional sparkline.
 */
export const MetricCard = ({
  label,
  value,
  unit,
  trend,
  sparkData,
  icon,
  className,
}: MetricCardProps) => {
  const trendVal = trend?.delta || trend?.value;

  return (
    <motion.div
      className={twMerge(
        "flex flex-col justify-between rounded-[var(--r-3)] border border-[var(--border)] bg-[var(--surface)] p-5 shadow-[var(--shadow-1)] min-h-[130px] relative overflow-hidden transition-shadow duration-150 hover:shadow-[var(--shadow-3)] hover:-translate-y-px",
        className
      )}
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
    >
      {/* Top stripe accent */}
      <div className="absolute top-0 inset-x-0 h-[1.5px] bg-gradient-to-r from-[var(--brand)]/30 via-transparent to-transparent" />

      {/* Header row */}
      <div className="flex items-start justify-between">
        <span
          className="t-label"
          style={{ color: "var(--text-3)" }}
        >
          {label}
        </span>
        {icon && (
          <div
            className="flex h-7 w-7 items-center justify-center rounded-lg"
            style={{
              background: "var(--brand-muted)",
              color: "var(--brand)",
            }}
          >
            {icon}
          </div>
        )}
      </div>

      {/* Value row */}
      <div className="mt-3 flex items-end justify-between gap-2">
        <div className="flex items-baseline gap-1.5">
          <span
            className="t-mono-xl"
            style={{ color: "var(--text-1)" }}
          >
            {value}
          </span>
          {unit && (
            <span className="t-small" style={{ color: "var(--text-3)" }}>
              {unit}
            </span>
          )}
        </div>
        {sparkData && <MiniSparkline data={sparkData} />}
      </div>

      {/* Trend row */}
      {trend && trendVal && (
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="mt-2 flex items-center gap-1.5"
        >
          <span
            className="inline-flex items-center gap-0.5 rounded-full px-2 py-0.5 t-mono border"
            style={{
              fontSize: 11,
              background: trend.isPositive ? "var(--safe-bg)" : "var(--high-bg)",
              color: trend.isPositive ? "var(--safe)" : "var(--high)",
              borderColor: trend.isPositive ? "var(--safe-border)" : "var(--high-border)",
            }}
          >
            {trend.isPositive
              ? <ArrowUpRight className="h-3 w-3 shrink-0" />
              : <ArrowDownRight className="h-3 w-3 shrink-0" />
            }
            {trendVal}
          </span>
          {trend.period && (
            <span className="t-small" style={{ color: "var(--text-4)", fontSize: 11 }}>
              {trend.period}
            </span>
          )}
        </motion.div>
      )}
    </motion.div>
  );
};

export default MetricCard;
