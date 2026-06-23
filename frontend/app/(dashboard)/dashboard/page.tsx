"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import client from "@/lib/api/client";
import { DashboardStats, RecentEvent } from "@/lib/types";
import { MetricCard } from "@/components/ui/MetricCard";
import { DataCard } from "@/components/ui/DataCard";
import { Badge } from "@/components/ui/Badge";
import { SkeletonLoader } from "@/components/ui/SkeletonLoader";
import { EmptyStateWithCTA } from "@/components/ui/EmptyStateWithCTA";
import { Button } from "@/components/ui/Button";
import { IntelligenceTable, Column } from "@/components/ui/IntelligenceTable";
import {
  RefreshCw,
  ShieldCheck,
  AlertTriangle,
  FileSearch,
  ShieldAlert,
  Smartphone,
  Network,
  Activity,
} from "lucide-react";
import { motion } from "framer-motion";
import { useThreatStream } from "@/hooks/useThreatStream";
import LiveStatsBar from "@/components/dashboard/LiveStatsBar";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";
import { TimelinePoint } from "@/lib/types";

// Risk-distribution pie slices (must match the backend /risk-distribution order).
const RISK_COLORS: Record<string, string> = {
  CLEAN: "var(--safe, #10b981)",
  SUSPICIOUS: "var(--warn, #f59e0b)",
  HIGH: "var(--risk-high, #ef4444)",
  CRITICAL: "#991b1b",
};

// Format an ISO timestamp into "Last updated 30s ago" / "1m ago" / "5m ago".
function formatLastUpdated(iso: string | null | undefined): string {
  if (!iso) return "Never";
  const ts = new Date(iso).getTime();
  if (Number.isNaN(ts)) return "Never";
  const diffSec = Math.max(0, Math.round((Date.now() - ts) / 1000));
  if (diffSec < 5) return "Just now";
  if (diffSec < 60) return `${diffSec}s ago`;
  const mins = Math.floor(diffSec / 60);
  if (mins < 60) return `${mins}m ago`;
  return `${Math.floor(mins / 60)}h ago`;
}

// Sparkline uses the same color tokens as the metric card icon, no new theme.
function padSparkData(points: TimelinePoint[], key: "total" | "documents" | "phishing", outLen = 7): number[] {
  // Pad with leading zeros if fewer than outLen points are available
  const tail = points.slice(-outLen).map((p) => p[key]);
  if (tail.length >= outLen) return tail;
  return Array(outLen - tail.length).fill(0).concat(tail);
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="rounded-[var(--r-2)] border border-[var(--border)] bg-[var(--surface)] p-3 shadow-[var(--shadow-2)] text-[12px] font-sans">
        <p className="font-semibold text-text-primary mb-1">{label}</p>
        <div className="space-y-1">
          {payload.map((p: any) => (
            <div key={p.name} className="flex items-center justify-between gap-6">
              <span className="flex items-center gap-1.5 text-text-secondary">
                <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: p.color }} />
                {p.name}
              </span>
              <span className="font-mono font-bold text-text-primary">{p.value}</span>
            </div>
          ))}
        </div>
      </div>
    );
  }
  return null;
};

export default function DashboardOverviewPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [events, setEvents] = useState<RecentEvent[]>([]);
  const [timeline, setTimeline] = useState<TimelinePoint[]>([]);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);
  const [tick, setTick] = useState(0); // forces "Last updated Xs ago" to re-render
  const { events: liveEvents, status: wsStatus } = useThreatStream(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  const fetchDashboardData = async (showRefreshIndicator = false) => {
    if (showRefreshIndicator) setIsRefreshing(true);
    else setIsLoading(true);

    try {
      const [statsData, eventsData, timelineData] = await Promise.all([
        client.getStats(),
        client.getRecentEvents(25),
        client.getTimeline(7),
      ]);
      setStats(statsData);
      setEvents(eventsData ?? []);
      setTimeline(timelineData?.points ?? []);
      setLastUpdated(statsData?.last_updated ?? new Date().toISOString());
    } catch (err) {
      console.error("Error loading dashboard metrics:", err);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  // Initial fetch
  useEffect(() => {
    const timer = setTimeout(() => {
      fetchDashboardData();
    }, 0);
    return () => clearTimeout(timer);
  }, []);

  // 30s polling — TASK 4: refresh stats + timeline so "Last updated" stays fresh
  // and the dashboard reflects new scans within 30s of their creation.
  useEffect(() => {
    const id = setInterval(() => {
      fetchDashboardData();
    }, 30_000);
    return () => clearInterval(id);
  }, []);

  // Re-render the "Last updated" string every second (cheap; just re-reads
  // lastUpdated from state and recomputes relative time).
  useEffect(() => {
    const id = setInterval(() => setTick((t) => t + 1), 1000);
    return () => clearInterval(id);
  }, []);
  void tick; // reference the state so React keeps the interval alive

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

  // Demo mode: backend is not connected — stats load returns null. Show
  // demo telemetry cards so the user can see the UI shape instead of an
  // empty page. Each card shows a realistic placeholder.
  if (!stats) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          <MetricCard
            label="Scans today"
            value="0"
            sublabel="Demo data"
            icon={<Activity className="h-4 w-4 text-text-muted" />}
          />
          <MetricCard
            label="Risk events"
            value="—"
            sublabel="Awaiting first scan"
            icon={<AlertTriangle className="h-4 w-4 text-text-muted" />}
          />
          <MetricCard
            label="Active campaigns"
            value="0"
            sublabel="Backend offline"
            icon={<Network className="h-4 w-4 text-text-muted" />}
          />
          <MetricCard
            label="Threat intel feeds"
            value="0 / 4"
            sublabel="Demo mode"
            icon={<ShieldAlert className="h-4 w-4 text-text-muted" />}
          />
        </div>
        <EmptyStateWithCTA
          icon="shield"
          title="Dashboard is empty"
          description="Threat telemetry requires a backend. In a full deployment, you'd see recent scans, attack vectors, and campaign heatmaps."
          technicalDetails="Backend not connected · Demo mode"
          primaryAction={{ label: "Try UPI Shield →", href: "/upi-shield" }}
        />
      </div>
    );
  }

  // Calculate risk percentages — now includes CRITICAL bucket (TASK 4).
  const totalRiskCount =
    (stats?.clean_count ?? 0) +
    (stats?.suspicious_count ?? 0) +
    (stats?.high_risk_count ?? 0) +
    (stats?.critical_count ?? 0);
  const cleanPercentage = totalRiskCount ? Math.round(((stats?.clean_count ?? 0) / totalRiskCount) * 100) : 0;
  const suspiciousPercentage = totalRiskCount ? Math.round(((stats?.suspicious_count ?? 0) / totalRiskCount) * 100) : 0;
  const highRiskPercentage = totalRiskCount ? Math.round(((stats?.high_risk_count ?? 0) / totalRiskCount) * 100) : 0;
  const criticalPercentage = totalRiskCount ? Math.round(((stats?.critical_count ?? 0) / totalRiskCount) * 100) : 0;

  // Pie chart data — matches /api/dashboard/risk-distribution order
  const riskPieData = [
    { name: "Clean",      value: stats?.clean_count ?? 0,      key: "CLEAN" },
    { name: "Suspicious", value: stats?.suspicious_count ?? 0, key: "SUSPICIOUS" },
    { name: "High",       value: stats?.high_risk_count ?? 0,  key: "HIGH" },
    { name: "Critical",   value: stats?.critical_count ?? 0,   key: "CRITICAL" },
  ].filter((s) => s.value > 0);

  // Table columns definition
  const columns: Column<RecentEvent>[] = [
    {
      header: "Inspection Type",
      accessorKey: "source_type",
      cell: (event) => {
        const isPhish = event.source_type === "URL";
        const isUpi = event.original_filename && /upi|payment|screenshot/i.test(event.original_filename);

        let typeLabel = "DocShield";
        let typeIcon = <FileSearch className="h-4 w-4 text-brand" />;

        if (isPhish) {
          typeLabel = "PhishShield";
          typeIcon = <ShieldAlert className="h-4 w-4 text-warn" />;
        } else if (isUpi) {
          typeLabel = "UPI Shield";
          typeIcon = <Smartphone className="h-4 w-4 text-teal-500" />;
        }

        return (
          <span className="inline-flex items-center gap-1.5 font-medium text-text-primary">
            {typeIcon}
            {typeLabel}
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
        <span className="font-mono text-[14px] font-bold text-text-primary">
          {event.risk_score}
        </span>
      ),
    },
    {
      header: "Risk Level",
      accessorKey: "risk_level",
      cell: (event) => (
        <Badge variant={event.risk_level === "CRITICAL" ? "critical" : event.risk_level === "HIGH" ? "high" : event.risk_level === "SUSPICIOUS" ? "warn" : "safe"} dot>
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
        let timeStr = "Just now";
        if (mins >= 1 && mins < 60) {
          timeStr = `${mins}m ago`;
        } else if (mins >= 60) {
          timeStr = `${Math.floor(mins / 60)}h ago`;
        }
        return (
          <span className="font-mono text-[12px] text-text-secondary">
            {timeStr}
          </span>
        );
      },
    },
  ];

  // Render expanded detail view (expands on click, Framer Motion animated height)
  const renderExpandedRow = (event: RecentEvent) => {
    const isDoc = event.source_type === "DOCUMENT";
    const targetPath = isDoc ? "/docshield" : "/phishshield";

    return (
      <div className="px-6 py-4 space-y-3 bg-[var(--surface-raised)]/30 border-t border-border-default/40 text-caption font-sans">
        {/* Row 1: Indicators */}
        <div className="flex flex-col sm:flex-row sm:items-center gap-2">
          <span className="text-[11px] font-semibold text-text-muted uppercase tracking-wider w-24 shrink-0">
            Indicators:
          </span>
          <div className="flex flex-wrap gap-1.5">
            {event.risk_indicators.length === 0 ? (
              <span className="text-text-muted italic text-[11px]">No risk signatures matched.</span>
            ) : (
              event.risk_indicators.map((ind, i) => (
                <Badge key={i} variant="critical" size="sm" className="bg-risk-high-bg text-risk-high border border-risk-high/10">
                  {ind}
                </Badge>
              ))
            )}
          </div>
        </div>

        {/* Row 2: Action */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2 border-t border-border-default/20">
          <div className="flex items-center gap-4 text-[10px] text-text-muted font-mono">
            <span>UUID: {event.event_id.slice(0, 8)}...</span>
            {event.file_hash && <span>SHA256: {event.file_hash.slice(0, 12)}...</span>}
          </div>
          <Link href={targetPath}>
            <Button variant="outline" size="sm" className="h-7 px-3 text-[11px] font-medium border-border-default hover:bg-surface-raised flex items-center gap-1">
              View Full Analysis
            </Button>
          </Link>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6 font-sans">
      {/* Live Threat Stats Bar */}
      <LiveStatsBar events={liveEvents} connectionStatus={wsStatus} />

      {/* Top Welcome Title bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-headline font-semibold text-text-primary">
            Forensic Telemetry Overview
          </h1>
          <p className="text-caption text-text-secondary">
            Dynamic statistics and correlation maps representing threats verified across Lumint engine nodes.
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
        <MetricCard
          label="Aggregated Detections"
          value={stats?.total_events || 0}
          icon={<Activity className="h-4 w-4 text-text-primary" />}
          sparkData={padSparkData(timeline, "total")}
        />
        <MetricCard
          label="DocShield Scans"
          value={stats?.document_events || 0}
          icon={<FileSearch className="h-4 w-4 text-brand" />}
          sparkData={padSparkData(timeline, "documents")}
        />
        <MetricCard
          label="PhishShield Audits"
          value={stats?.url_events || 0}
          icon={<ShieldAlert className="h-4 w-4 text-warn" />}
          sparkData={padSparkData(timeline, "phishing")}
        />
        <MetricCard
          label="Threat Campaigns DNA"
          value={stats?.active_campaigns || 0}
          icon={<Network className="h-4 w-4 text-teal-500" />}
          // No dedicated campaign-history endpoint; show a flat constant
          // (still driven by the same data system, not synthetic noise).
          sparkData={Array(7).fill(stats?.active_campaigns || 0)}
        />
      </div>

      {/* 7-Day Detection Chart — driven by /api/dashboard/timeline */}
      <DataCard className="p-4">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h4 className="text-[12px] font-semibold text-text-primary uppercase tracking-wider">
              7-Day Detection Telemetry
            </h4>
          </div>
          <div className="flex items-center gap-4 text-[10px] font-medium text-text-muted">
            <span className="flex items-center gap-1"><span className="h-1.5 w-1.5 rounded-full bg-brand" /> DocShield</span>
            <span className="flex items-center gap-1"><span className="h-1.5 w-1.5 rounded-full bg-[var(--warn)]" /> PhishShield</span>
          </div>
        </div>

        {isMounted ? (
          <div className="h-[120px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart
                data={timeline.map((p) => ({
                  date: p.date.slice(5), // MM-DD for a tighter x-axis
                  DocShield: p.documents,
                  PhishShield: p.phishing,
                }))}
                margin={{ top: 5, right: 5, left: -25, bottom: 0 }}
              >
                <defs>
                  <linearGradient id="colorDoc" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--brand)" stopOpacity={0.2}/>
                    <stop offset="95%" stopColor="var(--brand)" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorPhish" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--warn)" stopOpacity={0.2}/>
                    <stop offset="95%" stopColor="var(--warn)" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis
                  dataKey="date"
                  tickLine={false}
                  axisLine={false}
                  tick={{ fill: "var(--text-4)", fontSize: 10, fontFamily: "var(--font-mono), monospace" }}
                />
                <YAxis
                  tickLine={false}
                  axisLine={false}
                  tick={{ fill: "var(--text-4)", fontSize: 10, fontFamily: "var(--font-mono), monospace" }}
                  allowDecimals={false}
                />
                <CartesianGrid vertical={false} stroke="var(--border)" strokeDasharray="3 3" opacity={0.4} />
                <Tooltip content={<CustomTooltip />} />
                <Area type="monotone" dataKey="DocShield" stroke="var(--brand)" strokeWidth={1.5} fillOpacity={1} fill="url(#colorDoc)" />
                <Area type="monotone" dataKey="PhishShield" stroke="var(--warn)" strokeWidth={1.5} fillOpacity={1} fill="url(#colorPhish)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="h-[120px] w-full flex items-center justify-center text-text-muted text-[11px]">
            Loading chart telemetry...
          </div>
        )}
        <div className="mt-2 text-center">
          <span className="font-sans text-[10px] text-text-muted">
            Last updated {formatLastUpdated(lastUpdated)} · refreshes every 30s
          </span>
        </div>
      </DataCard>

      {/* Main Analysis Breakdowns */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left column - Live Forensic Events */}
        <div className="lg:col-span-2 space-y-6">
          <DataCard className="p-6 flex flex-col min-h-[500px]">
            <div className="flex items-center justify-between mb-5">
              <div>
                <h3 className="text-title text-text-primary">Recent Forensic Events</h3>
                <p className="text-caption text-text-secondary">Realtime inspection logs sorted by event timestamp.</p>
              </div>
              <span className="font-mono text-[10px] font-bold text-white bg-brand px-2.5 py-1 rounded-full flex items-center gap-1.5 shadow-[var(--shadow-1)]">
                <span className="h-1.5 w-1.5 rounded-full bg-white animate-pulse" />
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

            {/* Pie — TASK 4: real risk-distribution visualization */}
            {isMounted && riskPieData.length > 0 ? (
              <div className="h-[140px] w-full mb-4">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={riskPieData}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      innerRadius={32}
                      outerRadius={56}
                      paddingAngle={2}
                      stroke="var(--surface)"
                      strokeWidth={2}
                    >
                      {riskPieData.map((slice) => (
                        <Cell key={slice.key} fill={RISK_COLORS[slice.key]} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        background: "var(--surface)",
                        border: "1px solid var(--border)",
                        borderRadius: 8,
                        fontSize: 11,
                      }}
                      formatter={(value, name) => [`${value ?? 0} events`, String(name ?? "")]}
                    />
                    <Legend
                      iconType="circle"
                      iconSize={8}
                      wrapperStyle={{ fontSize: 10, color: "var(--text-3)" }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            ) : null}

            <div className="space-y-5">
              {/* Clean / Safe */}
              <div className="space-y-2">
                <div className="flex justify-between items-start">
                  <div className="flex flex-col">
                    <span className="flex items-center gap-2 text-[13px] font-medium text-text-primary">
                      <span className="h-1.5 w-1.5 rounded-full bg-safe shrink-0" />
                      Clean / Validated
                    </span>
                    <span className="text-[11px] text-text-muted ml-3.5">
                      {stats?.clean_count || 0} events
                    </span>
                  </div>
                  <span className="font-mono text-[14px] font-bold text-text-primary">{cleanPercentage}%</span>
                </div>
                <div className="h-2 bg-[var(--surface-3)] rounded-full overflow-hidden border border-border-default/30">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${cleanPercentage}%` }}
                    transition={{ duration: 1, ease: "easeOut" }}
                    className="h-full bg-safe"
                  />
                </div>
              </div>

              {/* Suspicious */}
              <div className="space-y-2">
                <div className="flex justify-between items-start">
                  <div className="flex flex-col">
                    <span className="flex items-center gap-2 text-[13px] font-medium text-text-primary">
                      <span className="h-1.5 w-1.5 rounded-full bg-[var(--warn)] shrink-0" />
                      Suspicious Anomalies
                    </span>
                    <span className="text-[11px] text-text-muted ml-3.5">
                      {stats?.suspicious_count || 0} events
                    </span>
                  </div>
                  <span className="font-mono text-[14px] font-bold text-text-primary">{suspiciousPercentage}%</span>
                </div>
                <div className="h-2 bg-[var(--surface-3)] rounded-full overflow-hidden border border-border-default/30">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${suspiciousPercentage}%` }}
                    transition={{ duration: 1, ease: "easeOut" }}
                    className="h-full bg-[var(--warn)]"
                  />
                </div>
              </div>

              {/* High Risk */}
              <div className="space-y-2">
                <div className="flex justify-between items-start">
                  <div className="flex flex-col">
                    <span className="flex items-center gap-2 text-[13px] font-medium text-text-primary">
                      <span className="h-1.5 w-1.5 rounded-full bg-risk-high shrink-0" />
                      Confirmed High Risk
                    </span>
                    <span className="text-[11px] text-text-muted ml-3.5">
                      {stats?.high_risk_count || 0} events
                    </span>
                  </div>
                  <span className="font-mono text-[14px] font-bold text-text-primary">{highRiskPercentage}%</span>
                </div>
                <div className="h-2 bg-[var(--surface-3)] rounded-full overflow-hidden border border-border-default/30">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${highRiskPercentage}%` }}
                    transition={{ duration: 1, ease: "easeOut" }}
                    className="h-full bg-risk-high"
                  />
                </div>
              </div>

              {/* Critical — TASK 4: new bucket exposed as its own bar */}
              <div className="space-y-2">
                <div className="flex justify-between items-start">
                  <div className="flex flex-col">
                    <span className="flex items-center gap-2 text-[13px] font-medium text-text-primary">
                      <span className="h-1.5 w-1.5 rounded-full shrink-0" style={{ backgroundColor: "#991b1b" }} />
                      Critical Threats
                    </span>
                    <span className="text-[11px] text-text-muted ml-3.5">
                      {stats?.critical_count || 0} events
                    </span>
                  </div>
                  <span className="font-mono text-[14px] font-bold text-text-primary">{criticalPercentage}%</span>
                </div>
                <div className="h-2 bg-[var(--surface-3)] rounded-full overflow-hidden border border-border-default/30">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${criticalPercentage}%` }}
                    transition={{ duration: 1, ease: "easeOut" }}
                    className="h-full"
                    style={{ backgroundColor: "#991b1b" }}
                  />
                </div>
              </div>
            </div>
          </DataCard>

          {/* Top Threat Indicators */}
          <DataCard className="p-6">
            <h3 className="text-title text-text-primary mb-1">Top Threat Indicators</h3>
            <p className="text-caption text-text-secondary mb-6">Most frequently triggered signatures within the workspace.</p>

            <div className="space-y-2">
              {stats?.top_indicators?.map((ind, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between text-[13px] font-medium p-2 rounded-lg transition-colors hover:bg-[var(--surface-2)] group select-none"
                >
                  <div className="flex items-center gap-2 max-w-[210px] truncate">
                    {/* Severity dot (pulse for top) */}
                    <span className="h-1.5 w-1.5 rounded-full bg-risk-high shrink-0 animate-pulse" />
                    <span className="font-mono text-[12px] text-text-muted w-4">
                      {idx + 1}.
                    </span>
                    <span className="text-text-primary truncate">
                      {ind.indicator}
                    </span>
                  </div>
                  <span className="font-mono text-text-secondary bg-[var(--surface-3)] border border-border-default/50 px-2 py-0.5 rounded text-[11px] font-semibold shrink-0">
                    {ind.count}
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
