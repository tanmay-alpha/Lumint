"use client";

import React, { useEffect, useState } from "react";
import client from "@/lib/api/client";
import { DashboardStats, RecentEvent } from "@/lib/types";
import { MetricBlock } from "@/components/ui/MetricBlock";
import { DataCard } from "@/components/ui/DataCard";
import { Badge } from "@/components/ui/Badge";
import { SkeletonLoader } from "@/components/ui/SkeletonLoader";
import { Button } from "@/components/ui/Button";
import { IntelligenceTable, Column } from "@/components/ui/IntelligenceTable";
import {
  RefreshCw,
  Clock,
  ShieldCheck,
  AlertTriangle,
  FileSpreadsheet,
  Link as LinkIcon,
  Fingerprint,
} from "lucide-react";
import { motion } from "framer-motion";
import { useThreatStream } from "@/hooks/useThreatStream";
import LiveStatsBar from "@/components/dashboard/LiveStatsBar";

export default function DashboardOverviewPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [events, setEvents] = useState<RecentEvent[]>([]);
  const { events: liveEvents, status: wsStatus } = useThreatStream(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const fetchDashboardData = async (showRefreshIndicator = false) => {
    if (showRefreshIndicator) setIsRefreshing(true);
    else setIsLoading(true);

    try {
      const [statsData, eventsData] = await Promise.all([
        client.getStats(),
        client.getRecentEvents(25),
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
    const timer = setTimeout(() => {
      fetchDashboardData();
    }, 0);
    return () => clearTimeout(timer);
  }, []);

  if (isLoading) {
    return (
      <div className="space-y-8">
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <SkeletonLoader variant="text-lg" className="w-48" />
            <SkeletonLoader variant="text-sm" className="w-72" />
          </div>
          <SkeletonLoader variant="text-md" className="w-28 h-10" />
        </div>

        {/* Stats Grid Skeleton */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <SkeletonLoader key={i} variant="rect" className="h-[120px] rounded-xl" />
          ))}
        </div>

        {/* Panels Skeleton */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2">
            <SkeletonLoader variant="rect" className="h-[450px] rounded-xl" />
          </div>
          <div>
            <SkeletonLoader variant="rect" className="h-[450px] rounded-xl" />
          </div>
        </div>
      </div>
    );
  }

  // Calculate risk percentages
  const totalRiskCount = (stats?.clean_count ?? 0) + (stats?.suspicious_count ?? 0) + (stats?.high_risk_count ?? 0);
  const cleanPercentage = totalRiskCount ? Math.round(((stats?.clean_count ?? 0) / totalRiskCount) * 100) : 0;
  const suspiciousPercentage = totalRiskCount ? Math.round(((stats?.suspicious_count ?? 0) / totalRiskCount) * 100) : 0;
  const highRiskPercentage = totalRiskCount ? Math.round(((stats?.high_risk_count ?? 0) / totalRiskCount) * 100) : 0;

  // Table columns definition
  const columns: Column<RecentEvent>[] = [
    {
      header: "Inspection Type",
      accessorKey: "source_type",
      cell: (event) => {
        const isDoc = event.source_type === "DOCUMENT";
        return (
          <span className="inline-flex items-center gap-1.5 font-semibold text-text-primary">
            {isDoc ? (
              <FileSpreadsheet className="h-4 w-4 text-brand" />
            ) : (
              <LinkIcon className="h-4 w-4 text-intel" />
            )}
            {isDoc ? "DocShield" : "PhishShield"}
          </span>
        );
      },
    },
    {
      header: "Entity Identity",
      accessorKey: "identity",
      cell: (event) => (
        <span className="font-mono text-caption text-text-secondary select-all truncate max-w-[220px] block">
          {event.source_type === "DOCUMENT" ? event.original_filename : event.source_domain}
        </span>
      ),
    },
    {
      header: "Score",
      accessorKey: "risk_score",
      align: "center",
      cell: (event) => (
        <span className="font-mono text-body font-bold text-text-primary">
          {event.risk_score}
        </span>
      ),
    },
    {
      header: "Risk Level",
      accessorKey: "risk_level",
      cell: (event) => (
        <Badge variant={event.risk_level === "HIGH" ? "danger" : event.risk_level === "SUSPICIOUS" ? "warn" : "safe"} dot>
          {event.risk_level}
        </Badge>
      ),
    },
    {
      header: "Age",
      accessorKey: "created_at",
      align: "right",
      cell: (event) => {
        const diff = Date.now() - new Date(event.created_at).getTime();
        const mins = Math.floor(diff / 60000);
        if (mins < 1) return "Just now";
        if (mins < 60) return `${mins}m ago`;
        return `${Math.floor(mins / 60)}h ago`;
      },
    },
  ];

  // Render expanded detail view
  const renderExpandedRow = (event: RecentEvent) => {
    return (
      <div className="px-6 py-5 space-y-4 text-caption border-t border-border-default/40">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-2">
            <span className="text-label text-text-secondary">Entity Details</span>
            <div className="space-y-1.5 font-mono text-[11px] leading-tight">
              <div>
                <span className="text-text-muted">UUID Hash: </span>
                <span className="text-text-primary select-all">{event.event_id}</span>
              </div>
              {event.file_hash && (
                <div>
                  <span className="text-text-muted">SHA-256: </span>
                  <span className="text-text-primary break-all select-all">{event.file_hash}</span>
                </div>
              )}
              {event.metadata_hash && (
                <div>
                  <span className="text-text-muted">Meta Hash: </span>
                  <span className="text-text-primary select-all">{event.metadata_hash}</span>
                </div>
              )}
              {event.editor_tool && (
                <div>
                  <span className="text-text-muted">Editor Signature: </span>
                  <span className="text-text-primary">{event.editor_tool}</span>
                </div>
              )}
              {event.creator && (
                <div>
                  <span className="text-text-muted">Author Creator: </span>
                  <span className="text-text-primary">{event.creator}</span>
                </div>
              )}
            </div>
          </div>

          <div className="space-y-2.5">
            <span className="text-label text-text-secondary">Triggered Forensic Indicators</span>
            {event.risk_indicators.length === 0 ? (
              <p className="text-text-muted italic">No threat signatures matched.</p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {event.risk_indicators.map((ind, i) => (
                  <Badge key={i} variant="danger" size="sm">
                    <AlertTriangle className="h-3 w-3 mr-1" />
                    {ind}
                  </Badge>
                ))}
              </div>
            )}
            {event.top_keywords && event.top_keywords.length > 0 && (
              <div className="mt-3">
                <span className="text-[10px] text-text-muted font-semibold uppercase tracking-wider block mb-1">
                  High Risk Keyword Discovered
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {event.top_keywords.map((kw, i) => (
                    <span
                      key={i}
                      className="bg-surface-raised border border-border-default px-1.5 py-0.5 rounded text-[10px] text-text-primary font-medium"
                    >
                      {kw}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-8 font-sans">
      {/* Live Threat Stats Bar */}
      <LiveStatsBar events={liveEvents} connectionStatus={wsStatus} />

      {/* Top Welcome Title bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-headline font-semibold text-text-primary">
            Forensic Telemetry Overview
          </h1>
          <p className="text-caption text-text-secondary">
            Dynamic statistics and correlation maps representing threats verified across SentinelX engine nodes.
          </p>
        </div>

        <Button
          onClick={() => fetchDashboardData(true)}
          disabled={isRefreshing}
          variant="outline"
          size="sm"
          className="shrink-0 flex items-center gap-2"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${isRefreshing ? "animate-spin text-brand" : "text-text-muted"}`} />
          {isRefreshing ? "Refreshing..." : "Refresh Feed"}
        </Button>
      </div>

      {/* Stats Summary Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricBlock
          label="Aggregated Detections"
          value={stats?.total_events || 0}
          trend={{ value: "+8.3%", isPositive: true }}
          icon={<FileSpreadsheet className="h-4 w-4" />}
        />
        <MetricBlock
          label="DocShield Scans"
          value={stats?.document_events || 0}
          trend={{ value: "+12.1%", isPositive: true }}
          icon={<ShieldCheck className="h-4 w-4 text-brand" />}
        />
        <MetricBlock
          label="PhishShield Audits"
          value={stats?.url_events || 0}
          trend={{ value: "+4.6%", isPositive: true }}
          icon={<LinkIcon className="h-4 w-4 text-intel" />}
        />
        <MetricBlock
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
          <DataCard className="p-6 flex flex-col min-h-[500px]">
            <div className="flex items-center justify-between mb-5">
              <div>
                <h3 className="text-title text-text-primary">Recent Forensic Events</h3>
                <p className="text-caption text-text-secondary">Realtime inspection logs sorted by event timestamp.</p>
              </div>
              <span className="font-mono text-[10px] font-semibold text-text-secondary flex items-center gap-1.5 bg-surface-raised px-2.5 py-1 rounded-lg border border-border-default/60">
                <Clock className="h-3 w-3 text-brand" />
                LIVE STREAM
              </span>
            </div>

            {events.length === 0 ? (
              <div className="flex-grow flex flex-col items-center justify-center p-8 text-center text-text-muted">
                <ShieldCheck className="h-12 w-12 text-border-default mb-3" />
                <p className="font-semibold text-body text-text-primary">No recent anomalies detected</p>
                <p className="text-caption max-w-xs mt-1">Uploaded documents or URLs verified as clean will appear in the historical archive.</p>
              </div>
            ) : (
              <IntelligenceTable
                data={events}
                columns={columns}
                keyExtractor={(item) => item.event_id}
                renderExpandedRow={renderExpandedRow}
                emptyMessage="No historical inspection logs found."
                className="border-none shadow-none bg-transparent rounded-none"
              />
            )}
          </DataCard>
        </div>

        {/* Right column - Risk Stats & Alerts */}
        <div className="space-y-6">
          {/* Risk Level Distribution Card */}
          <DataCard className="p-6">
            <h3 className="text-title text-text-primary mb-1">Risk Breakdown</h3>
            <p className="text-caption text-text-secondary mb-6">Percentage allocation of verified scanned entities.</p>

            <div className="space-y-5">
              {/* Clean */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-caption font-semibold">
                  <span className="flex items-center gap-1.5 text-text-secondary">
                    <span className="h-2 w-2 rounded-full bg-risk-none" />
                    Clean / Validated
                  </span>
                  <span className="text-text-primary">{cleanPercentage}%</span>
                </div>
                <div className="h-2 bg-surface-raised border border-border-default/40 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${cleanPercentage}%` }}
                    transition={{ duration: 1, ease: "easeOut" }}
                    className="h-full bg-risk-none"
                  />
                </div>
                <span className="text-[10px] text-text-muted font-medium block">
                  {stats?.clean_count || 0} events flagged safe
                </span>
              </div>

              {/* Suspicious */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-caption font-semibold">
                  <span className="flex items-center gap-1.5 text-text-secondary">
                    <span className="h-2 w-2 rounded-full bg-risk-medium" />
                    Suspicious Anomalies
                  </span>
                  <span className="text-text-primary">{suspiciousPercentage}%</span>
                </div>
                <div className="h-2 bg-surface-raised border border-border-default/40 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${suspiciousPercentage}%` }}
                    transition={{ duration: 1, ease: "easeOut" }}
                    className="h-full bg-risk-medium"
                  />
                </div>
                <span className="text-[10px] text-text-muted font-medium block">
                  {stats?.suspicious_count || 0} indicators mismatching standards
                </span>
              </div>

              {/* High Risk */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-caption font-semibold">
                  <span className="flex items-center gap-1.5 text-text-secondary">
                    <span className="h-2 w-2 rounded-full bg-risk-high" />
                    Confirmed High Risk
                  </span>
                  <span className="text-text-primary">{highRiskPercentage}%</span>
                </div>
                <div className="h-2 bg-surface-raised border border-border-default/40 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${highRiskPercentage}%` }}
                    transition={{ duration: 1, ease: "easeOut" }}
                    className="h-full bg-risk-high"
                  />
                </div>
                <span className="text-[10px] text-text-muted font-medium block">
                  {stats?.high_risk_count || 0} events triggers critical policy violation
                </span>
              </div>
            </div>
          </DataCard>

          {/* Top Threat Indicators */}
          <DataCard className="p-6">
            <h3 className="text-title text-text-primary mb-1">Top Threat Indicators</h3>
            <p className="text-caption text-text-secondary mb-6">Most frequently triggered signatures within the workspace.</p>

            <div className="space-y-4">
              {stats?.top_indicators?.map((ind, idx) => (
                <div key={idx} className="flex items-center justify-between text-[13px] font-medium">
                  <span className="flex items-center gap-2 max-w-[210px] truncate text-text-primary">
                    <span className="h-5 w-5 flex items-center justify-center rounded bg-risk-high-bg border border-risk-high/15 text-risk-high font-mono text-[10px] font-bold">
                      {idx + 1}
                    </span>
                    {ind.indicator}
                  </span>
                  <span className="font-mono text-text-secondary bg-surface-raised border border-border-default/50 px-2 py-0.5 rounded text-[11px] font-medium">
                    {ind.count} occurrences
                  </span>
                </div>
              ))}
            </div>
          </DataCard>
        </div>
      </div>
    </div>
  );
}
