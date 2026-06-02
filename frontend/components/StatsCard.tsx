"use client";

import React from "react";
import { GlassCard } from "./GlassCard";
import { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface StatsCardProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  description?: string;
  trend?: {
    value: string;
    isPositive: boolean;
  };
  delay?: number;
  className?: string;
}

export const StatsCard: React.FC<StatsCardProps> = ({
  title,
  value,
  icon: Icon,
  description,
  trend,
  delay = 0,
  className
}) => {
  return (
    <GlassCard delay={delay} className={cn("flex flex-col justify-between h-full", className)}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">{title}</p>
          <h3 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">{value}</h3>
        </div>
        <div className="rounded-xl bg-sky-50/50 p-2.5 text-sky-600 border border-sky-100/50">
          <Icon className="h-5.5 w-5.5" />
        </div>
      </div>
      
      {(trend || description) && (
        <div className="mt-4 flex items-center justify-between text-xs border-t border-slate-100/55 pt-3">
          {trend ? (
            <span className={cn(
              "font-medium flex items-center gap-1",
              trend.isPositive ? "text-rose-600" : "text-emerald-600" // For threats, higher trend is negative for company but positive count
            )}>
              {trend.value}
            </span>
          ) : <span />}
          {description && (
            <span className="text-slate-400 font-medium">{description}</span>
          )}
        </div>
      )}
    </GlassCard>
  );
};

export default StatsCard;
