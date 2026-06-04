"use client";

import React, { useEffect, useState } from "react";
import client from "@/lib/api/client";
import { DashboardStats, RecentEvent } from "@/lib/types";
import StatCard from "@/components/ui/StatCard";
import GlassCard from "@/components/ui/GlassCard";
import RiskBadge from "@/components/ui/RiskBadge";
import SkeletonLoader from "@/components/ui/SkeletonLoader";
import {
  RefreshCw,
  Clock,
  ShieldCheck,
  AlertTriangle,
  FileSpreadsheet,
  Link,
  ChevronDown,
  ChevronUp,
  Fingerprint
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useThreatStream } from "@/hooks/useThreatStream";
import LiveStatsBar from "@/components/dashboard/LiveStatsBar";

export default function DashboardOverviewPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [events, setEvents] = useState<RecentEvent[]>([]);
  const { events: liveEvents, status: wsStatus } = useThreatStream(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [expandedEventId, setExpandedEventId] = useState<string | null>(null);

  const fetchDashboardData = async (showRefreshIndicator = false) => {
    if (showRefreshIndicator) setIsRefreshing(true);
    else setIsLoading(true);

    try {
      const [statsData, eventsData] = await Promise.all([
        client.getStats(),
        client.getRecentEvents(25)
      ]);
      
      setStats(statsData);
      setEvents(eventsData);
    } catch (err) {
      console.error("Error loading dashboard metrics:", err);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchDashboardData();
  }, []);

  const toggleExpandEvent = (eventId: string) => {
    setExpandedEventId(expandedEventId === eventId ? null : eventId);
  };

  if (isLoading) {
    return (
      <div className="space-y-8">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <div className="h-7 w-48 bg-border/40 rounded-lg animate-pulse" />
            <div className="h-4 w-72 bg-border/40 rounded-lg animate-pulse mt-2" />
          </div>
          <div className="h-10 w-28 bg-border/40 rounded-lg animate-pulse" />
        </div>

        {/* Stats Grid Skeleton */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <SkeletonLoader key={i} variant="card" className="h-[140px]" />
          ))}
        </div>

        {/* Panels Skeleton */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <SkeletonLoader variant="card" className="lg:col-span-2 h-[450px]" />
          <SkeletonLoader variant="card" className="h-[450px]" />
        </div>
      </div>
    );
  }

  // Calculate risk percentages
  const totalRiskCount = (stats?.clean_count ?? 0) + (stats?.suspicious_count ?? 0) + (stats?.high_risk_count ?? 0);
  const cleanPercentage = totalRiskCount ? Math.round(((stats?.clean_count ?? 0) / totalRiskCount) * 100) : 0;
  const suspiciousPercentage = totalRiskCount ? Math.round(((stats?.suspicious_count ?? 0) / totalRiskCount) * 100) : 0;
  const highRiskPercentage = totalRiskCount ? Math.round(((stats?.high_risk_count ?? 0) / totalRiskCount) * 100) : 0;

  return (
    <div className="space-y-8">
      {/* Live Threat Stats Bar */}
      <LiveStatsBar events={liveEvents} connectionStatus={wsStatus} />

      {/* Top Welcome Title bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-text-primary">
            Forensic Telemetry Overview
          </h1>
          <p className="text-sm text-text-secondary font-medium">
            Dynamic statistics and correlation maps representing threats verified across SentinelX engine nodes.
          </p>
        </div>

        <button
          onClick={() => fetchDashboardData(true)}
          disabled={isRefreshing}
          className="inline-flex items-center justify-center gap-2 rounded-xl border border-border bg-surface hover:bg-white text-xs font-bold text-text-primary px-4 py-2.5 shadow-sm transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 shrink-0"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${isRefreshing ? "animate-spin text-accent-blue" : "text-text-secondary"}`} />
          {isRefreshing ? "Refreshing..." : "Refresh Feed"}
        </button>
      </div>

      {/* Stats Summary Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          label="Aggregated Detections"
          value={stats?.total_events || 0}
          trend={{ value: "+8.3%", isPositive: true }}
          icon={<FileSpreadsheet className="h-4 w-4" />}
        />
        <StatCard
          label="DocShield Scans"
          value={stats?.document_events || 0}
          trend={{ value: "+12.1%", isPositive: true }}
          icon={<ShieldCheck className="h-4 w-4 text-accent-blue" />}
        />
        <StatCard
          label="PhishShield Audits"
          value={stats?.url_events || 0}
          trend={{ value: "+4.6%", isPositive: true }}
          icon={<Link className="h-4 w-4 text-accent-teal" />}
        />
        <StatCard
          label="Threat Campaigns DNA"
          value={stats?.active_campaigns || 0}
          trend={{ value: "Stable", isPositive: true }}
          icon={<Fingerprint className="h-4 w-4 text-risk-critical" />}
        />
      </div>

      {/* Main Analysis Breakdowns */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left column - Live Forensic Events */}
        <div className="lg:col-span-2 space-y-6">
          <GlassCard className="p-6 flex flex-col min-h-[500px]">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-lg font-bold text-text-primary">Recent Forensic Events</h3>
                <p className="text-xs text-text-secondary font-medium">Realtime inspection logs sorted by event timestamp.</p>
              </div>
              <span className="text-[11px] font-mono font-bold text-text-secondary flex items-center gap-1.5 bg-bg-base px-2.5 py-1 rounded-lg border border-border/40">
                <Clock className="h-3 w-3 text-accent-blue" />
                Live stream
              </span>
            </div>

            {events.length === 0 ? (
              <div className="flex-1 flex flex-col items-center justify-center p-8 text-center text-text-secondary">
                <ShieldCheck className="h-12 w-12 text-border mb-3" />
                <p className="font-semibold text-sm">No recent anomalies detected</p>
                <p className="text-xs max-w-xs mt-1">Uploaded documents or URLs verified as clean will appear in the historical archive.</p>
              </div>
            ) : (
              <div className="overflow-x-auto -mx-6">
                <table className="w-full text-left border-collapse text-sm">
                  <thead>
                    <tr className="border-b border-border/40 text-[10px] font-bold text-text-secondary uppercase tracking-wider bg-bg-base/40">
                      <th className="py-3 px-6 w-8"></th>
                      <th className="py-3 px-4">Inspection Type</th>
                      <th className="py-3 px-4">Entity Identity</th>
                      <th className="py-3 px-4 text-center">Score</th>
                      <th className="py-3 px-4">Risk Level</th>
                      <th className="py-3 px-6 text-right">Age</th>
                    </tr>
                  </thead>
                  <tbody>
                    {events.map((event) => {
                      const isExpanded = expandedEventId === event.event_id;
                      const hasDocInfo = event.source_type === "DOCUMENT";
                      return (
                        <React.Fragment key={event.event_id}>
                          {/* Main Row */}
                          <tr
                            onClick={() => toggleExpandEvent(event.event_id)}
                            className={`border-b border-border/20 cursor-pointer hover:bg-bg-base/30 transition-colors ${
                              isExpanded ? "bg-bg-base/20" : ""
                            }`}
                          >
                            <td className="py-4 px-6 text-center text-text-secondary">
                              {isExpanded ? (
                                <ChevronUp className="h-4 w-4 stroke-[2.5]" />
                              ) : (
                                <ChevronDown className="h-4 w-4 stroke-[2.5]" />
                              )}
                            </td>
                            <td className="py-4 px-4 font-semibold text-text-primary">
                              <span className="inline-flex items-center gap-1.5">
                                {hasDocInfo ? (
                                  <FileSpreadsheet className="h-4 w-4 text-accent-blue" />
                                ) : (
                                  <Link className="h-4 w-4 text-accent-teal" />
                                )}
                                {hasDocInfo ? "DocShield" : "PhishShield"}
                              </span>
                            </td>
                            <td className="py-4 px-4 max-w-[200px] truncate font-mono text-xs font-semibold text-text-primary">
                              {hasDocInfo ? event.original_filename : event.source_domain}
                            </td>
                            <td className="py-4 px-4 text-center font-mono font-bold text-text-primary">
                              {event.risk_score}
                            </td>
                            <td className="py-4 px-4">
                              <RiskBadge
                                variant={
                                  event.risk_level === "HIGH"
                                    ? "high"
                                    : event.risk_level === "SUSPICIOUS"
                                    ? "medium"
                                    : "safe"
                                }
                              />
                            </td>
                            <td className="py-4 px-6 text-right text-xs text-text-secondary font-semibold">
                              {(() => {
                                const diff = Date.now() - new Date(event.created_at).getTime();
                                const mins = Math.floor(diff / 60000);
                                if (mins < 1) return "Just now";
                                if (mins < 60) return `${mins}m ago`;
                                return `${Math.floor(mins / 60)}h ago`;
                              })()}
                            </td>
                          </tr>

                          {/* Expandable Details Tray */}
                          <AnimatePresence>
                            {isExpanded && (
                              <tr>
                                <td colSpan={6} className="bg-bg-base/40 border-b border-border/30 p-0">
                                  <motion.div
                                    initial={{ opacity: 0, height: 0 }}
                                    animate={{ opacity: 1, height: "auto" }}
                                    exit={{ opacity: 0, height: 0 }}
                                    transition={{ duration: 0.2 }}
                                    className="overflow-hidden px-12 py-5 space-y-4 text-xs font-medium"
                                  >
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                      <div className="space-y-2">
                                        <div className="text-[10px] font-bold text-text-secondary uppercase tracking-widest">
                                          Entity Details
                                        </div>
                                        <div className="space-y-1.5 font-mono text-[11px]">
                                          <div>
                                            <span className="text-text-secondary">UUID Hash: </span>
                                            <span className="text-text-primary select-all">{event.event_id}</span>
                                          </div>
                                          {event.file_hash && (
                                            <div>
                                              <span className="text-text-secondary">SHA-256: </span>
                                              <span className="text-text-primary break-all select-all">{event.file_hash}</span>
                                            </div>
                                          )}
                                          {event.metadata_hash && (
                                            <div>
                                              <span className="text-text-secondary">Meta Hash: </span>
                                              <span className="text-text-primary select-all">{event.metadata_hash}</span>
                                            </div>
                                          )}
                                          {event.editor_tool && (
                                            <div>
                                              <span className="text-text-secondary">Editor Signature: </span>
                                              <span className="text-text-primary">{event.editor_tool}</span>
                                            </div>
                                          )}
                                          {event.creator && (
                                            <div>
                                              <span className="text-text-secondary">Author Creator: </span>
                                              <span className="text-text-primary">{event.creator}</span>
                                            </div>
                                          )}
                                        </div>
                                      </div>

                                      <div className="space-y-2.5">
                                        <div className="text-[10px] font-bold text-text-secondary uppercase tracking-widest">
                                          Triggered Forensic Indicators
                                        </div>
                                        {event.risk_indicators.length === 0 ? (
                                          <div className="text-text-secondary italic">No threat signatures matched.</div>
                                        ) : (
                                          <div className="flex flex-wrap gap-2">
                                            {event.risk_indicators.map((ind, i) => (
                                              <span
                                                key={i}
                                                className="inline-flex items-center gap-1 bg-risk-high/5 text-risk-high border border-risk-high/10 px-2 py-1 rounded text-[10px] font-bold font-mono"
                                              >
                                                <AlertTriangle className="h-3 w-3" />
                                                {ind}
                                              </span>
                                            ))}
                                          </div>
                                        )}
                                        {event.top_keywords && event.top_keywords.length > 0 && (
                                          <div className="mt-3">
                                            <div className="text-[9px] font-bold text-text-secondary uppercase tracking-wider mb-1">
                                              High Risk Keyword Discovered
                                            </div>
                                            <div className="flex flex-wrap gap-1.5">
                                              {event.top_keywords.map((kw, i) => (
                                                <span
                                                  key={i}
                                                  className="bg-bg-base border border-border px-1.5 py-0.5 rounded text-[10px] text-text-primary font-semibold"
                                                >
                                                  {kw}
                                                </span>
                                              ))}
                                            </div>
                                          </div>
                                        )}
                                      </div>
                                    </div>
                                  </motion.div>
                                </td>
                              </tr>
                            )}
                          </AnimatePresence>
                        </React.Fragment>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </GlassCard>
        </div>

        {/* Right column - Risk Stats & Alerts */}
        <div className="space-y-6">
          {/* Risk Level Distribution Card */}
          <GlassCard className="p-6">
            <h3 className="text-lg font-bold text-text-primary mb-1">Risk Breakdown</h3>
            <p className="text-xs text-text-secondary font-medium mb-6">Percentage allocation of verified scanned entities.</p>

            <div className="space-y-5">
              {/* Clean */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs font-semibold">
                  <span className="flex items-center gap-1.5">
                    <span className="h-2 w-2 rounded-full bg-risk-safe" />
                    Clean / Validated
                  </span>
                  <span>{cleanPercentage}%</span>
                </div>
                <div className="h-2 bg-border/40 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${cleanPercentage}%` }}
                    transition={{ duration: 1, ease: "easeOut" }}
                    className="h-full bg-risk-safe"
                  />
                </div>
                <div className="text-[10px] text-text-secondary font-medium">
                  {stats?.clean_count || 0} events flagged safe
                </div>
              </div>

              {/* Suspicious */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs font-semibold">
                  <span className="flex items-center gap-1.5">
                    <span className="h-2 w-2 rounded-full bg-risk-medium" />
                    Suspicious Anomalies
                  </span>
                  <span>{suspiciousPercentage}%</span>
                </div>
                <div className="h-2 bg-border/40 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${suspiciousPercentage}%` }}
                    transition={{ duration: 1, ease: "easeOut" }}
                    className="h-full bg-risk-medium"
                  />
                </div>
                <div className="text-[10px] text-text-secondary font-medium">
                  {stats?.suspicious_count || 0} indicators mismatching standards
                </div>
              </div>

              {/* High Risk */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs font-semibold">
                  <span className="flex items-center gap-1.5">
                    <span className="h-2 w-2 rounded-full bg-risk-critical" />
                    Confirmed High Risk
                  </span>
                  <span>{highRiskPercentage}%</span>
                </div>
                <div className="h-2 bg-border/40 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${highRiskPercentage}%` }}
                    transition={{ duration: 1, ease: "easeOut" }}
                    className="h-full bg-risk-critical"
                  />
                </div>
                <div className="text-[10px] text-text-secondary font-medium">
                  {stats?.high_risk_count || 0} events triggers critical policy violation
                </div>
              </div>
            </div>
          </GlassCard>

          {/* Top Threat Indicators */}
          <GlassCard className="p-6">
            <h3 className="text-lg font-bold text-text-primary mb-1">Top Threat Indicators</h3>
            <p className="text-xs text-text-secondary font-medium mb-6">Most frequently triggered signatures within the workspace.</p>

            <div className="space-y-4">
              {stats?.top_indicators?.map((ind, idx) => (
                <div key={idx} className="flex items-center justify-between text-xs font-semibold">
                  <span className="flex items-center gap-2 max-w-[210px] truncate text-text-primary/90">
                    <span className="h-5 w-5 flex items-center justify-center rounded bg-risk-high/5 border border-risk-high/10 text-risk-high font-mono text-[10px] font-bold">
                      {idx + 1}
                    </span>
                    {ind.indicator}
                  </span>
                  <span className="font-mono text-text-secondary bg-bg-base border border-border/40 px-2 py-0.5 rounded text-[11px] font-bold">
                    {ind.count} occurrences
                  </span>
                </div>
              ))}
            </div>
          </GlassCard>
        </div>
      </div>
    </div>
  );
}
