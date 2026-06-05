"use client";

import React from "react";
import { ThreatEvent, ConnectionStatus } from "@/hooks/useThreatStream";
import Button from "@/components/ui/Button";

interface LiveStatsBarProps {
  events: ThreatEvent[];
  connectionStatus: ConnectionStatus;
}

export default function LiveStatsBar({ events, connectionStatus }: LiveStatsBarProps) {
  const totalThreats = events.length;
  const criticalHighAlerts = events.filter(
    (e) => e.threat_level === "CRITICAL" || e.threat_level === "HIGH"
  ).length;

  const isLive = connectionStatus === "connected";
  const dotColor = isLive ? "bg-safe" : "bg-risk-high";

  return (
    <div className="h-12 flex items-center justify-between px-4 rounded-lg bg-surface border border-border-default shadow-sm select-none">
      {/* Left section: Status indicator */}
      <div className="flex items-center gap-2.5">
        <span className="relative flex h-2 w-2">
          <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${dotColor}`} />
          <span className={`relative inline-flex rounded-full h-2 w-2 ${dotColor}`} />
        </span>
        <span className="font-sans text-[13px] font-medium text-text-secondary">
          Threat Stream
        </span>
      </div>

      {/* Center section: 3 metrics */}
      <div className="hidden sm:flex items-center gap-8 md:gap-12">
        <div className="flex items-center gap-2">
          <span className="font-sans text-[10px] font-semibold text-text-muted uppercase tracking-wider">
            Session Threats:
          </span>
          <span className="font-mono text-[13px] font-bold text-text-primary">
            {totalThreats}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <span className="font-sans text-[10px] font-semibold text-text-muted uppercase tracking-wider">
            Critical Alerts:
          </span>
          <span className="font-mono text-[13px] font-bold text-text-primary">
            {criticalHighAlerts}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <span className="font-sans text-[10px] font-semibold text-text-muted uppercase tracking-wider">
            Drift Status:
          </span>
          <span className="font-mono text-[13px] font-bold text-text-primary">
            Stable
          </span>
        </div>
      </div>

      {/* Right section: Connect button */}
      <div>
        <Button variant="ghost" size="sm" className="h-7 px-3 text-[11px] text-brand hover:bg-[var(--brand-muted)] font-medium">
          Connect
        </Button>
      </div>
    </div>
  );
}
