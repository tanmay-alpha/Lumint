"use client";

import React from "react";
import { Badge } from "./Badge";

export type RiskLevel = "safe" | "warn" | "danger" | "critical" | "low" | "unknown";
type LegacyVariant = "safe" | "medium" | "high" | "critical" | "clean";

export interface RiskBadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  level?: RiskLevel;
  variant?: LegacyVariant | string;
  size?: "sm" | "md";
  pulse?: boolean;
  className?: string;
}

export function toRiskLevel(raw: string | undefined | null): RiskLevel {
  const s = (raw ?? "").toUpperCase();
  if (s === "CLEAN" || s === "SAFE")                return "safe";
  if (s === "SUSPICIOUS" || s === "WARN" || s === "MEDIUM") return "warn";
  if (s === "HIGH" || s === "HIGH RISK")            return "danger";
  if (s === "CRITICAL")                             return "critical";
  if (s === "LOW")                                  return "low";
  return "unknown";
}

export const RiskBadge = ({
  level,
  variant,
  size = "md",
  pulse = false,
  className,
  ...props
}: RiskBadgeProps) => {
  const resolvedLevel: RiskLevel = level ?? toRiskLevel(variant);
  
  const variantMap: Record<RiskLevel, "safe" | "warn" | "danger" | "critical" | "low" | "muted"> = {
    safe: "safe",
    warn: "warn",
    danger: "danger",
    critical: "critical",
    low: "low",
    unknown: "muted",
  };

  const labelMap: Record<RiskLevel, string> = {
    safe: "SAFE",
    warn: "SUSPICIOUS",
    danger: "HIGH RISK",
    critical: "CRITICAL",
    low: "LOW RISK",
    unknown: "UNKNOWN",
  };

  const shouldPulse = pulse && (resolvedLevel === "danger" || resolvedLevel === "critical" || resolvedLevel === "warn");

  return (
    <Badge
      variant={variantMap[resolvedLevel]}
      size={size}
      dot={shouldPulse || resolvedLevel !== "unknown"}
      className={className}
      {...props}
    >
      {labelMap[resolvedLevel]}
    </Badge>
  );
};

export const RiskBadgeFromBackend = ({ level, ...rest }: Omit<RiskBadgeProps, "level"> & { level: string }) => (
  <RiskBadge level={toRiskLevel(level)} {...rest} />
);

export default RiskBadge;
