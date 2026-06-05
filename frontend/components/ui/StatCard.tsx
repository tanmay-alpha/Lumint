"use client";

import React from "react";
import { MetricBlock, MetricBlockProps } from "./MetricBlock";

export interface StatCardProps extends Omit<MetricBlockProps, "variant"> {
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
    <MetricBlock
      label={label}
      value={value}
      trend={trend}
      icon={icon}
      className={className}
      variant={elevated ? "overlay" : "raised"}
    />
  );
};

export default StatCard;
