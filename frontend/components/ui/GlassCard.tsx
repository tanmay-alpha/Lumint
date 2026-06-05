"use client";

import React from "react";
import { DataCard, DataCardProps } from "./DataCard";

export interface GlassCardProps extends DataCardProps {
  elevated?: boolean;
  glass?: boolean;
}

export const GlassCard = ({
  children,
  className,
  elevated = false,
  glass = false,
  ...props
}: GlassCardProps) => {
  const variant = glass || elevated ? "overlay" : "raised";
  return (
    <DataCard
      variant={variant}
      className={className}
      withPattern={glass}
      {...props}
    >
      {children}
    </DataCard>
  );
};

export default GlassCard;
