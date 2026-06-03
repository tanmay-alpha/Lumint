"use client";

import React from "react";
import { motion } from "framer-motion";
import { GlassCard } from "./GlassCard";
import { ArrowUpRight, ArrowDownRight } from "lucide-react";
import { twMerge } from "tailwind-merge";

export interface StatCardProps {
  label: string;
  value: string | number;
  trend?: { value: string; isPositive: boolean };
  icon?: React.ReactNode;
  className?: string;
  elevated?: boolean;
}

export const StatCard = ({
  label,
  value,
  trend,
  icon,
  className,
  elevated = false,
}: StatCardProps) => {
  return (
    <GlassCard
      elevated={elevated}
      className={twMerge("flex flex-col justify-between min-h-[140px] p-6", className)}
    >
      <div className="flex items-start justify-between">
        <span className="text-label text-[var(--color-text-muted)] uppercase tracking-widest">
          {label}
        </span>
        {icon && (
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--color-accent-subtle)] text-[var(--color-accent)]">
            {icon}
          </div>
        )}
      </div>

      <div className="mt-4 flex items-baseline justify-between gap-3">
        <span className="font-mono text-mono-lg font-medium tracking-tight text-[var(--color-text-primary)]">
          {value}
        </span>

        {trend && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className={twMerge(
              "inline-flex items-center gap-0.5 rounded-full px-2 py-0.5 text-[11px] font-semibold shrink-0",
              trend.isPositive
                ? "bg-[var(--color-safe-subtle)] text-[var(--color-safe)]"
                : "bg-[var(--color-danger-subtle)] text-[var(--color-danger)]"
            )}
          >
            {trend.isPositive ? (
              <ArrowUpRight className="h-3 w-3" />
            ) : (
              <ArrowDownRight className="h-3 w-3" />
            )}
            <span>{trend.value}</span>
          </motion.div>
        )}
      </div>
    </GlassCard>
  );
};

export default StatCard;
