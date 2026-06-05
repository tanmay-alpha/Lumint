import React from "react";
import { Globe, FileText, Smartphone, RefreshCw, Zap } from "lucide-react";
import { ThreatEvent } from "@/hooks/useThreatStream";

interface ThreatEventCardProps {
  event: ThreatEvent;
}

export default function ThreatEventCard({ event }: ThreatEventCardProps) {
  const getModuleIcon = () => {
    switch (event.module) {
      case "phish":
        return <Globe className="h-5 w-5 text-teal-400" />;
      case "doc":
        return <FileText className="h-5 w-5 text-blue-400" />;
      case "upi":
        return <Smartphone className="h-5 w-5 text-indigo-400" />;
      default:
        return <Zap className="h-5 w-5 text-purple-400" />;
    }
  };

  const getSeverityStyles = () => {
    switch (event.threat_level) {
      case "CRITICAL":
        return {
          badge: "bg-red-950/80 text-red-400 border-red-800/60",
          glow: "shadow-[0_0_15px_rgba(239,68,68,0.15)] border-red-950/60 hover:border-red-500/40",
          scoreBg: "text-red-400"
        };
      case "HIGH":
        return {
          badge: "bg-orange-950/80 text-orange-400 border-orange-800/60",
          glow: "shadow-[0_0_15px_rgba(249,115,22,0.1)] border-orange-950/60 hover:border-orange-500/40",
          scoreBg: "text-orange-400"
        };
      case "MEDIUM":
        return {
          badge: "bg-yellow-950/80 text-yellow-400 border-yellow-800/60",
          glow: "shadow-[0_0_15px_rgba(234,179,8,0.08)] border-yellow-950/60 hover:border-yellow-500/40",
          scoreBg: "text-yellow-400"
        };
      default:
        return {
          badge: "bg-emerald-950/80 text-emerald-400 border-emerald-800/60",
          glow: "shadow-[0_0_15px_rgba(16,185,129,0.08)] border-emerald-950/60 hover:border-emerald-500/40",
          scoreBg: "text-emerald-400"
        };
    }
  };

  const getDriftStyles = () => {
    switch (event.drift_status) {
      case "drift":
        return "bg-fuchsia-950/80 text-fuchsia-400 border-fuchsia-800/60 animate-pulse";
      case "warning":
        return "bg-amber-950/80 text-amber-400 border-amber-800/60";
      default:
        return "bg-emerald-950/60 text-emerald-400 border-emerald-800/20";
    }
  };

  const sevStyles = getSeverityStyles();
  const dateStr = new Date(event.timestamp).toLocaleTimeString();

  return (
    <div className={`p-5 rounded-2xl bg-[var(--color-surface)] border border-[var(--color-border)] backdrop-blur-md transition-all duration-300 hover:-translate-y-0.5 ${sevStyles.glow}`}>
      {/* Top Header Row */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-[var(--color-surface-2)] border border-[var(--color-border)] flex items-center justify-center">
            {getModuleIcon()}
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-[11px] font-bold tracking-widest text-[var(--color-text-muted)] uppercase">
                {event.module === "phish" ? "PHISH_SHIELD" : event.module === "doc" ? "DOC_SHIELD" : event.module === "upi" ? "UPI_SHIELD" : "FRAUD_DNA"}
              </span>
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${sevStyles.badge}`}>
                {event.threat_level}
              </span>
              {event.drift_status !== "stable" && (
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border flex items-center gap-1 ${getDriftStyles()}`}>
                  <RefreshCw className="h-2.5 w-2.5 animate-spin" style={{ animationDuration: "6s" }} />
                  Drift: {event.drift_status}
                </span>
              )}
            </div>
            <h3 className="text-sm font-bold text-[var(--color-text-primary)] mt-1 line-clamp-1">
              {event.summary}
            </h3>
          </div>
        </div>

        {/* Risk Score indicator */}
        <div className="text-right">
          <span className={`text-2xl font-black font-mono tracking-tighter ${sevStyles.scoreBg}`}>
            {event.risk_score}
          </span>
          <span className="text-[9px] font-bold text-[var(--color-text-muted)] block -mt-1 uppercase tracking-wider">
            Risk Score
          </span>
        </div>
      </div>

      {/* Middle Body */}
      <div className="mt-4 pt-3 border-t border-[var(--color-border)]/60 flex items-center justify-between gap-4 flex-wrap">
        {/* Indicators checklist */}
        <div className="flex flex-wrap gap-1.5 max-w-[80%]">
          {event.indicators.slice(0, 3).map((ind, idx) => (
            <span key={idx} className="text-[10px] font-semibold px-2 py-1 rounded-lg bg-[var(--color-surface-2)] text-[var(--color-text-secondary)] border border-[var(--color-border)]/40">
              {ind}
            </span>
          ))}
          {event.indicators.length > 3 && (
            <span className="text-[10px] font-semibold px-2 py-1 rounded-lg bg-[var(--color-surface-2)] text-[var(--color-text-muted)]">
              +{event.indicators.length - 3} more
            </span>
          )}
        </div>

        {/* Timestamp */}
        <span className="text-[10px] font-bold font-mono text-[var(--color-text-muted)] shrink-0">
          {dateStr}
        </span>
      </div>
    </div>
  );
}
