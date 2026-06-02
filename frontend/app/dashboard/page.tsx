"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { 
  FileText, 
  Globe, 
  Network, 
  AlertTriangle,
  ArrowRight,
  TrendingUp,
  ShieldCheck,
  Zap,
  Activity,
  History
} from "lucide-react";
import GlassCard from "@/components/GlassCard";
import StatsCard from "@/components/StatsCard";
import ThreatBadge from "@/components/ThreatBadge";
import { dashboardService } from "@/services/dashboard";
import { StatsResponse, RecentEvent } from "@/types";

export default function DashboardOverview() {
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [events, setEvents] = useState<RecentEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDashboardData() {
      try {
        const [statsData, eventsData] = await Promise.all([
          dashboardService.getStats(),
          dashboardService.getRecentEvents(5),
        ]);
        setStats(statsData);
        setEvents(eventsData.events);
      } catch (error) {
        console.error("Failed to load dashboard data", error);
      } finally {
        setLoading(false);
      }
    }
    loadDashboardData();
  }, []);

  if (loading) {
    return (
      <div className="space-y-8 animate-pulse">
        {/* Header skeleton */}
        <div className="h-8 w-64 bg-slate-200 rounded-lg"></div>

        {/* Stats grid skeleton */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-32 bg-slate-200 rounded-3xl"></div>
          ))}
        </div>

        {/* Main section skeleton */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 h-[420px] bg-slate-200 rounded-3xl"></div>
          <div className="h-[420px] bg-slate-200 rounded-3xl"></div>
        </div>
      </div>
    );
  }

  const cleanCount = stats?.clean_count || 0;
  const suspiciousCount = stats?.suspicious_count || 0;
  const highRiskCount = stats?.high_risk_count || 0;
  const totalThreats = cleanCount + suspiciousCount + highRiskCount;
  
  const highRiskPercent = totalThreats > 0 ? Math.round((highRiskCount / totalThreats) * 100) : 0;
  const suspiciousPercent = totalThreats > 0 ? Math.round((suspiciousCount / totalThreats) * 100) : 0;
  const cleanPercent = totalThreats > 0 ? Math.round((cleanCount / totalThreats) * 100) : 0;

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      
      {/* Intro Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight">
            Threat Intelligence Console
          </h2>
          <p className="text-slate-500 mt-1.5 text-sm font-medium">
            Real-time telemetry, metadata validation, and digital forensics summary.
          </p>
        </div>
        <div className="flex items-center gap-2.5 text-xs font-bold text-slate-500 bg-white border border-slate-200/60 rounded-full px-4 py-2 shadow-sm">
          <span className="h-2 w-2 rounded-full bg-emerald-500 animate-ping" />
          <span>Monitoring Active Node</span>
        </div>
      </div>

      {/* Stats Cards Section */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatsCard
          title="Documents Screened"
          value={stats?.document_events || 0}
          icon={FileText}
          description="Magic-byte & visual layout check"
          trend={{ value: "+12% today", isPositive: true }}
        />
        <StatsCard
          title="Vetted Hostnames"
          value={stats?.url_events || 0}
          icon={Globe}
          description="Typosquatting & DNS verification"
          trend={{ value: "+4.8%", isPositive: true }}
        />
        <StatsCard
          title="Identified Campaigns"
          value={stats?.active_campaigns || 0}
          icon={Network}
          description="Coordinated DNA risk clusters"
          trend={{ value: "Active clusters", isPositive: false }}
        />
        <StatsCard
          title="Overall Threat Index"
          value={`${highRiskPercent}%`}
          icon={AlertTriangle}
          description="Ratio of identified High-Risk elements"
          trend={{ value: "Critical threat volume", isPositive: highRiskPercent > 10 }}
        />
      </div>

      {/* Primary Analytics Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Graph & Stats Visuals */}
        <div className="lg:col-span-2 space-y-8">
          <GlassCard className="p-6 md:p-8 flex flex-col justify-between min-h-[380px]">
            <div>
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-bold text-slate-900">Forensics Distribution</h3>
                  <p className="text-xs text-slate-500 mt-0.5">Classification of threat payloads</p>
                </div>
                <div className="flex items-center gap-1.5 text-xs font-bold text-sky-600 bg-sky-50 border border-sky-100 rounded-full px-2.5 py-1">
                  <TrendingUp className="h-3 w-3" />
                  <span>Telemetry</span>
                </div>
              </div>

              {/* Progress bars matching elegant Apple design */}
              <div className="mt-8 space-y-6">
                <div>
                  <div className="flex justify-between text-xs font-semibold mb-2">
                    <span className="text-slate-700">High Risk (Exploits, Alternations, Phish)</span>
                    <span className="text-red-600 font-bold">{highRiskCount} alerts ({highRiskPercent}%)</span>
                  </div>
                  <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                    <div 
                      className="bg-red-500 h-full rounded-full transition-all duration-1000" 
                      style={{ width: `${highRiskPercent}%` }} 
                    />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-xs font-semibold mb-2">
                    <span className="text-slate-700">Suspicious (Structural Typos, Metadata Warns)</span>
                    <span className="text-amber-600 font-bold">{suspiciousCount} warnings ({suspiciousPercent}%)</span>
                  </div>
                  <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                    <div 
                      className="bg-amber-400 h-full rounded-full transition-all duration-1000" 
                      style={{ width: `${suspiciousPercent}%` }} 
                    />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-xs font-semibold mb-2">
                    <span className="text-slate-700">Verified Safe (Validated Assets)</span>
                    <span className="text-emerald-600 font-bold">{cleanCount} verified ({cleanPercent}%)</span>
                  </div>
                  <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                    <div 
                      className="bg-emerald-500 h-full rounded-full transition-all duration-1000" 
                      style={{ width: `${cleanPercent}%` }} 
                    />
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-8 pt-6 border-t border-slate-100 flex justify-between items-center text-xs text-slate-500 font-medium">
              <span>Total Screened items: <strong className="text-slate-900">{totalThreats}</strong></span>
              <span className="flex items-center gap-1"><ShieldCheck className="h-3.5 w-3.5 text-emerald-500" /> Compliant status</span>
            </div>
          </GlassCard>
          
          {/* Quick-Scan Portal Links */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Link href="/dashboard/docshield" className="group">
              <GlassCard className="p-5 hover:border-slate-300 transition-all duration-300 cursor-pointer h-full flex flex-col justify-between">
                <div>
                  <div className="rounded-xl bg-slate-900 text-white p-2.5 w-fit mb-4">
                    <FileText className="h-5 w-5" />
                  </div>
                  <h4 className="text-sm font-bold text-slate-900 group-hover:text-sky-600 transition-colors">DocShield</h4>
                  <p className="text-xs text-slate-500 mt-1 line-clamp-2">Validate document magic headers and analyze forensic alterations.</p>
                </div>
                <div className="flex items-center gap-1 mt-4 text-xs font-bold text-slate-800">
                  <span>Open workspace</span>
                  <ArrowRight className="h-3 w-3 group-hover:translate-x-1 transition-transform" />
                </div>
              </GlassCard>
            </Link>

            <Link href="/dashboard/phishshield" className="group">
              <GlassCard className="p-5 hover:border-slate-300 transition-all duration-300 cursor-pointer h-full flex flex-col justify-between">
                <div>
                  <div className="rounded-xl bg-slate-900 text-white p-2.5 w-fit mb-4">
                    <Globe className="h-5 w-5" />
                  </div>
                  <h4 className="text-sm font-bold text-slate-900 group-hover:text-sky-600 transition-colors">PhishShield</h4>
                  <p className="text-xs text-slate-500 mt-1 line-clamp-2">Audit deceptive hostnames, brand likeness, and register records.</p>
                </div>
                <div className="flex items-center gap-1 mt-4 text-xs font-bold text-slate-800">
                  <span>Scan hostnames</span>
                  <ArrowRight className="h-3 w-3 group-hover:translate-x-1 transition-transform" />
                </div>
              </GlassCard>
            </Link>

            <Link href="/dashboard/fraud-dna" className="group">
              <GlassCard className="p-5 hover:border-slate-300 transition-all duration-300 cursor-pointer h-full flex flex-col justify-between">
                <div>
                  <div className="rounded-xl bg-slate-900 text-white p-2.5 w-fit mb-4">
                    <Network className="h-5 w-5" />
                  </div>
                  <h4 className="text-sm font-bold text-slate-900 group-hover:text-sky-600 transition-colors">Fraud DNA</h4>
                  <p className="text-xs text-slate-500 mt-1 line-clamp-2">Graph campaign links, visual clusters, and threat actor maps.</p>
                </div>
                <div className="flex items-center gap-1 mt-4 text-xs font-bold text-slate-800">
                  <span>Explore DNA</span>
                  <ArrowRight className="h-3 w-3 group-hover:translate-x-1 transition-transform" />
                </div>
              </GlassCard>
            </Link>
          </div>
        </div>

        {/* Recent Events Log Side Panel */}
        <div className="space-y-6">
          <GlassCard className="p-6 md:p-8 h-full flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between pb-4 border-b border-slate-100">
                <div className="flex items-center gap-2">
                  <Activity className="h-4.5 w-4.5 text-slate-500" />
                  <h3 className="text-sm font-bold text-slate-900">Live Threat Stream</h3>
                </div>
                <Link href="/dashboard/events" className="text-xs font-bold text-sky-600 hover:underline flex items-center gap-0.5">
                  <History className="h-3 w-3" />
                  <span>View all</span>
                </Link>
              </div>

              <div className="mt-6 space-y-5">
                {events.length === 0 ? (
                  <p className="text-xs text-slate-400 text-center py-8">No recent incidents detected.</p>
                ) : (
                  events.map((event) => {
                    const target = event.original_filename || event.source_domain || "Unknown Asset";
                    const details = event.risk_indicators && event.risk_indicators.length > 0 
                      ? event.risk_indicators.join(", ") 
                      : event.document_type_hint || "No anomalies flagged";
                    
                    return (
                      <div key={event.event_id} className="flex gap-3 text-xs leading-relaxed">
                        <div className="mt-0.5 shrink-0">
                          {event.source_type === "DOCUMENT" ? (
                            <div className="bg-sky-50 border border-sky-100 p-1.5 rounded-lg text-sky-700">
                              <FileText className="h-3.5 w-3.5" />
                            </div>
                          ) : (
                            <div className="bg-emerald-50 border border-emerald-100 p-1.5 rounded-lg text-emerald-700">
                              <Globe className="h-3.5 w-3.5" />
                            </div>
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex justify-between items-start">
                            <span className="font-bold text-slate-800 truncate block mr-1" title={target}>
                              {target}
                            </span>
                            <ThreatBadge level={event.risk_level} />
                          </div>
                          <p className="text-[11px] text-slate-500 mt-0.5 line-clamp-2">{details}</p>
                          <span className="text-[10px] text-slate-400 mt-1 block">
                            {new Date(event.created_at).toLocaleTimeString()}
                          </span>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>

            <div className="mt-6 pt-6 border-t border-slate-100 text-center">
              <span className="inline-flex items-center gap-1.5 text-xs text-sky-600 bg-sky-50 hover:bg-sky-100/70 border border-sky-100 font-bold px-3 py-1.5 rounded-full transition-colors cursor-pointer w-full justify-center">
                <Zap className="h-3.5 w-3.5" />
                Trigger Live Telemetry Pull
              </span>
            </div>
          </GlassCard>
        </div>
        
      </div>
      
    </div>
  );
}
