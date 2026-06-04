import React from "react";
import { Activity, ShieldAlert, AlertTriangle, RefreshCw, Zap } from "lucide-react";
import { ThreatEvent, ConnectionStatus } from "@/hooks/useThreatStream";

interface LiveStatsBarProps {
  events: ThreatEvent[];
  connectionStatus: ConnectionStatus;
}

export default function LiveStatsBar({ events, connectionStatus }: LiveStatsBarProps) {
  // 1. Total threats seen in current session stream
  const totalThreats = events.length;

  // 2. Critical & High severity threat events
  const criticalHighAlerts = events.filter(
    (e) => e.threat_level === "CRITICAL" || e.threat_level === "HIGH"
  ).length;

  // 3. Current active concept drift status by module
  const moduleDriftStates: Record<string, string> = {
    phish: "stable",
    doc: "stable",
    upi: "stable",
    fraud_dna: "stable",
  };

  events.forEach((event) => {
    if (event.module) {
      moduleDriftStates[event.module] = event.drift_status || "stable";
    }
  });

  const activeWarnings = Object.values(moduleDriftStates).filter((s) => s === "warning").length;
  const activeDrifts = Object.values(moduleDriftStates).filter((s) => s === "drift").length;

  return (
    <div className="relative overflow-hidden rounded-2xl bg-[var(--color-surface)] border border-[var(--color-border)] p-4 shadow-md backdrop-blur-md">
      {/* Glow highlight */}
      <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-[var(--color-accent)] to-transparent opacity-50" />
      
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 items-center">
        {/* Stream Status indicator */}
        <div className="flex items-center gap-3 px-3 py-1 bg-[var(--color-surface-2)] rounded-xl border border-[var(--color-border)]/60">
          <div className="relative flex h-3 w-3">
            <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
              connectionStatus === "connected" 
                ? "bg-emerald-400" 
                : connectionStatus === "connecting" 
                ? "bg-amber-400" 
                : "bg-red-400"
            }`} />
            <span className={`relative inline-flex rounded-full h-3 w-3 ${
              connectionStatus === "connected" 
                ? "bg-emerald-500" 
                : connectionStatus === "connecting" 
                ? "bg-amber-500" 
                : "bg-red-500"
            }`} />
          </div>
          <div className="flex-1 min-w-0">
            <span className="text-[10px] font-bold text-[var(--color-text-muted)] uppercase tracking-wider block leading-none">
              威胁遥测流 · Threat Stream
            </span>
            <span className="text-xs font-bold text-[var(--color-text-primary)] capitalize">
              {connectionStatus === "connected" ? "Live Feed Connected" : connectionStatus === "connecting" ? "Reconnecting..." : "Offline"}
            </span>
          </div>
        </div>

        {/* Counter: Total Session Threats */}
        <div className="flex items-center justify-between px-4 py-1.5 border-r border-[var(--color-border)]/40 last:border-0">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-blue-950/40 border border-blue-900/30 text-blue-400">
              <Activity className="h-4 w-4" />
            </div>
            <div>
              <span className="text-[10px] font-bold text-[var(--color-text-muted)] uppercase tracking-wider block">
                Session Threats
              </span>
              <span className="text-sm font-black font-mono text-[var(--color-text-primary)]">
                {totalThreats}
              </span>
            </div>
          </div>
        </div>

        {/* Counter: Critical & High Alerts */}
        <div className="flex items-center justify-between px-4 py-1.5 border-r border-[var(--color-border)]/40 last:border-0">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-red-950/40 border border-red-900/30 text-red-400">
              <ShieldAlert className="h-4 w-4 animate-bounce" style={{ animationDuration: "3s" }} />
            </div>
            <div>
              <span className="text-[10px] font-bold text-[var(--color-text-muted)] uppercase tracking-wider block">
                Critical / High Alerts
              </span>
              <span className="text-sm font-black font-mono text-red-400">
                {criticalHighAlerts}
              </span>
            </div>
          </div>
        </div>

        {/* Counter: Concept Drift Modules */}
        <div className="flex items-center justify-between px-4 py-1.5 last:border-0">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-fuchsia-950/40 border border-fuchsia-900/30 text-fuchsia-400">
              <RefreshCw className="h-4 w-4 animate-spin" style={{ animationDuration: "8s" }} />
            </div>
            <div>
              <span className="text-[10px] font-bold text-[var(--color-text-muted)] uppercase tracking-wider block">
                Concept Drift Engine
              </span>
              <span className="text-sm font-bold text-[var(--color-text-primary)] flex items-center gap-1.5">
                <span className="font-mono text-fuchsia-400 font-extrabold">{activeDrifts}</span>
                <span className="text-[10px] text-[var(--color-text-muted)]">drift</span>
                <span className="text-[10px] text-[var(--color-border-strong)]">/</span>
                <span className="font-mono text-amber-400 font-extrabold">{activeWarnings}</span>
                <span className="text-[10px] text-[var(--color-text-muted)]">warn</span>
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
