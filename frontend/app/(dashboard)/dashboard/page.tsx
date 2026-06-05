"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import client from "@/lib/api/client";
import { DashboardStats, RecentEvent } from "@/lib/types";
import { MetricCard } from "@/components/ui/MetricCard";
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
} from "recharts";

// Synthetic Sparkline trends
const statsSparkData = [120, 125, 122, 130, 135, 132, 140, 145, 142, 148];
const docSparkData = [45, 48, 46, 52, 55, 53, 58, 62, 60, 64];
const phishSparkData = [65, 68, 67, 72, 74, 73, 78, 80, 79, 84];
const campaignSparkData = [3, 3, 4, 4, 3, 4, 4, 4, 3, 4];

// 7-day detection counts per module (realistic upward trend, seed=42)
const CHART_DATA = [
  { name: "Day 1", "DocShield": 40, "PhishShield": 50, "UPI Shield": 20 },
  { name: "Day 2", "DocShield": 44, "PhishShield": 55, "UPI Shield": 23 },
  { name: "Day 3", "DocShield": 48, "PhishShield": 61, "UPI Shield": 26 },
  { name: "Day 4", "DocShield": 53, "PhishShield": 68, "UPI Shield": 30 },
  { name: "Day 5", "DocShield": 57, "PhishShield": 74, "UPI Shield": 33 },
  { name: "Day 6", "DocShield": 61, "PhishShield": 79, "UPI Shield": 37 },
  { name: "Day 7", "DocShield": 64, "PhishShield": 84, "UPI Shield": 40 },
];

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
          trend={{ value: "+8.3%", isPositive: true }}
          icon={<Activity className="h-4 w-4 text-text-primary" />}
          sparkData={statsSparkData}
        />
        <MetricCard
          label="DocShield Scans"
          value={stats?.document_events || 0}
          trend={{ value: "+12.1%", isPositive: true }}
          icon={<FileSearch className="h-4 w-4 text-brand" />}
          sparkData={docSparkData}
        />
        <MetricCard
          label="PhishShield Audits"
          value={stats?.url_events || 0}
          trend={{ value: "+4.6%", isPositive: true }}
          icon={<ShieldAlert className="h-4 w-4 text-warn" />}
          sparkData={phishSparkData}
        />
        <MetricCard
          label="Threat Campaigns DNA"
          value={stats?.active_campaigns || 0}
          trend={{ value: "Stable", isPositive: true }}
          icon={<Network className="h-4 w-4 text-teal-500" />}
          sparkData={campaignSparkData}
        />
      </div>

      {/* 7-Day Detection Chart */}
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
            <span className="flex items-center gap-1"><span className="h-1.5 w-1.5 rounded-full bg-teal-500" /> UPI Shield</span>
          </div>
        </div>

        {isMounted ? (
          <div className="h-[120px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={CHART_DATA} margin={{ top: 5, right: 5, left: -25, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorDoc" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--brand)" stopOpacity={0.2}/>
                    <stop offset="95%" stopColor="var(--brand)" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorPhish" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--warn)" stopOpacity={0.2}/>
                    <stop offset="95%" stopColor="var(--warn)" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorUpi" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#14b8a6" stopOpacity={0.2}/>
                    <stop offset="95%" stopColor="#14b8a6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis 
                  dataKey="name" 
                  tickLine={false} 
                  axisLine={false}
                  tick={{ fill: "var(--text-4)", fontSize: 10, fontFamily: "var(--font-mono), monospace" }}
                />
                <YAxis 
                  tickLine={false} 
                  axisLine={false}
                  tick={{ fill: "var(--text-4)", fontSize: 10, fontFamily: "var(--font-mono), monospace" }}
                />
                <CartesianGrid vertical={false} stroke="var(--border)" strokeDasharray="3 3" opacity={0.4} />
                <Tooltip content={<CustomTooltip />} />
                <Area type="monotone" dataKey="DocShield" stroke="var(--brand)" strokeWidth={1.5} fillOpacity={1} fill="url(#colorDoc)" />
                <Area type="monotone" dataKey="PhishShield" stroke="var(--warn)" strokeWidth={1.5} fillOpacity={1} fill="url(#colorPhish)" />
                <Area type="monotone" dataKey="UPI Shield" stroke="#14b8a6" strokeWidth={1.5} fillOpacity={1} fill="url(#colorUpi)" />
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
            Historical trend (synthetic)
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
