"use client";

import React from "react";
import { GlassCard, GlassCardProps } from "./GlassCard";
import { ArrowUpRight, ArrowDownRight } from "lucide-react";
import { twMerge } from "tailwind-merge";

export interface StatCardProps extends GlassCardProps {
  label: string;
  value: string | number;
  trend?: {
    value: string;
    isPositive: boolean;
  };
  icon?: React.ReactNode;
}

export const StatCard = ({
  label,
  value,
  trend,
  icon,
  className,
  elevated = false,
  ...props
}: StatCardProps) => {
  return (
    <GlassCard
      elevated={elevated}
      className={twMerge("flex flex-col justify-between min-h-[140px] p-6", className)}
      {...props}
    >
      <div className="flex items-start justify-between">
        <span className="text-xs font-semibold tracking-wider text-text-secondary uppercase">
          {label}
        </span>
        {icon && (
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-bg-base text-text-secondary border border-border/40">
            {icon}
          </div>
        )}
      </div>

      <div className="mt-4 flex items-baseline justify-between">
        <span className="font-mono text-3xl font-bold tracking-tight text-text-primary">
          {value}
        </span>

        {trend && (
          <div
            className={twMerge(
              "inline-flex items-center gap-0.5 rounded-full px-2 py-0.5 text-xs font-semibold",
              trend.isPositive
                ? "bg-risk-safe/10 text-risk-safe"
                : "bg-risk-critical/10 text-risk-critical"
            )}
          >
            {trend.isPositive ? (
              <ArrowUpRight className="h-3 w-3" />
            ) : (
              <ArrowDownRight className="h-3 w-3" />
            )}
            <span>{trend.value}</span>
          </div>
        )}
      </div>
    </GlassCard>
  );
};

export default StatCard;
