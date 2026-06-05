"use client";

import React from "react";
import { motion } from "framer-motion";
import { ArrowUpRight, ArrowDownRight } from "lucide-react";
import { twMerge } from "tailwind-merge";
import { DataCard } from "./DataCard";

export interface MetricBlockProps {
  label: string;
  value: string | number;
  trend?: { value: string; isPositive: boolean };
  icon?: React.ReactNode;
  className?: string;
  variant?: "flat" | "raised" | "overlay";
}

export const MetricBlock = ({
  label,
  value,
  trend,
  icon,
  className,
  variant = "raised",
}: MetricBlockProps) => {
  return (
    <DataCard
      variant={variant}
      interactive={true}
      className={twMerge("flex flex-col justify-between min-h-[130px] p-5 relative overflow-hidden", className)}
    >
      <div className="flex items-start justify-between">
        <span className="text-label text-text-secondary">
          {label}
        </span>
        {icon && (
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent-subtle text-accent border border-brand/10">
            {icon}
          </div>
        )}
      </div>

      <div className="mt-4 flex items-baseline justify-between gap-3">
        <span className="text-data-lg text-text-primary tracking-tight font-medium">
          {value}
        </span>

        {trend && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className={twMerge(
              "inline-flex items-center gap-0.5 rounded-full px-2 py-0.5 text-[11px] font-medium font-mono shrink-0 border",
              trend.isPositive
                ? "bg-risk-none-bg text-risk-none border-risk-none/20"
                : "bg-risk-high-bg text-risk-high border-risk-high/20"
            )}
          >
            {trend.isPositive ? (
              <ArrowUpRight className="h-3 w-3 shrink-0" />
            ) : (
              <ArrowDownRight className="h-3 w-3 shrink-0" />
            )}
            <span>{trend.value}</span>
          </motion.div>
        )}
      </div>
    </DataCard>
  );
};

export default MetricBlock;
