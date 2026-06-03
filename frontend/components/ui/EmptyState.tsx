"use client";

import React from "react";
import { GlassCard, GlassCardProps } from "./GlassCard";
import { Inbox } from "lucide-react";
import { twMerge } from "tailwind-merge";

export interface EmptyStateProps extends GlassCardProps {
  title: string;
  description: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
}

export const EmptyState = ({
  title,
  description,
  icon,
  action,
  className,
  ...props
}: EmptyStateProps) => {
  return (
    <GlassCard
      className={twMerge(
        "flex flex-col items-center justify-center text-center p-12 min-h-[320px]",
        className
      )}
      {...props}
    >
      <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-bg-base border border-border/40 text-text-secondary mb-6">
        {icon || <Inbox className="h-8 w-8 stroke-[1.25]" />}
      </div>

      <h3 className="text-lg font-bold tracking-tight text-text-primary mb-2">
        {title}
      </h3>
      <p className="text-sm text-text-secondary max-w-sm mb-6 leading-relaxed">
        {description}
      </p>

      {action && <div className="flex items-center gap-3">{action}</div>}
    </GlassCard>
  );
};

export default EmptyState;
