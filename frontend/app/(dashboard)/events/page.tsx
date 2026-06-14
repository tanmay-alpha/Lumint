"use client";

import React, { useState, useEffect } from "react";
import { 
  Search, 
  Filter, 
  FileText, 
  Globe, 
  Layers, 
  Cpu, 
  CornerDownRight, 
  Terminal, 
  ShieldCheck, 
  ChevronDown, 
  ChevronUp,
  Activity,
  Play,
  Pause,
  Trash2,
  Sliders,
  Database
} from "lucide-react";
import GlassCard from "@/components/ui/GlassCard";
import RiskBadge from "@/components/ui/RiskBadge";
import SkeletonLoader from "@/components/ui/SkeletonLoader";
import { EmptyStateWithCTA } from "@/components/ui/EmptyStateWithCTA";
import client from "@/lib/api/client";
import { RecentEvent } from "@/lib/types";
import { useThreatStream } from "@/hooks/useThreatStream";
import ThreatEventCard from "@/components/activity/ThreatEventCard";

export default function ThreatEventsPage() {
  // Tabs: "LIVE" | "HISTORICAL"
  const [activeTab, setActiveTab] = useState<"LIVE" | "HISTORICAL">("LIVE");

  // Live Stream Settings
  const [simulate, setSimulate] = useState(false);
  const [simulationRate, setSimulationRate] = useState(1.0);
  const { events: liveEvents, status: wsStatus, clearEvents } = useThreatStream(simulate, simulationRate);

  // Historical state
  const [events, setEvents] = useState<RecentEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState<"ALL" | "DOCUMENT" | "URL">("ALL");
  const [riskFilter, setRiskFilter] = useState<"ALL" | "CLEAN" | "SUSPICIOUS" | "HIGH">("ALL");
  const [expandedEventId, setExpandedEventId] = useState<string | null>(null);

  useEffect(() => {
    async function loadEvents() {
      try {
        const eventsData = await client.getRecentEvents(50);
        setEvents(eventsData ?? []);
      } catch (error) {
        console.error("Failed to load events logs", error);
        setEvents([]);
      } finally {
        setLoading(false);
      }
    }
    loadEvents();
  }, [activeTab]);

  const toggleRow = (id: string) => {
    setExpandedEventId(expandedEventId === id ? null : id);
  };

  const getRiskVariant = (level: string) => {
    switch (level) {
      case "HIGH":
      case "CRITICAL":
        return "high";
      case "SUSPICIOUS":
      case "MEDIUM":
        return "medium";
      default:
        return "safe";
    }
  };

  // Filter events based on criteria
  const filteredEvents = events.filter((event) => {
    const target = (event.original_filename || event.source_domain || "").toLowerCase();
    const matchesSearch = target.includes(searchQuery.toLowerCase());
    
    const matchesType = typeFilter === "ALL" || event.source_type === typeFilter;
    
    const matchesRisk = riskFilter === "ALL" || event.risk_level === riskFilter;

    return matchesSearch && matchesType && matchesRisk;
  });

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-text-primary flex items-center gap-2">
            <Activity className="h-6 w-6 text-accent-blue animate-pulse" />
            Threat Activity Center
          </h1>
          <p className="text-sm text-text-secondary font-medium mt-0.5">
            Real-time streaming threat intelligence, event replay logs, and adaptive drift forensics.
          </p>
        </div>

        {/* Tab Selector */}
        <div className="inline-flex rounded-xl bg-[var(--color-surface-2)] p-1 border border-[var(--color-border)] self-start sm:self-auto">
          <button
            onClick={() => setActiveTab("LIVE")}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-bold transition-all ${
              activeTab === "LIVE"
                ? "bg-[var(--color-surface)] text-[var(--color-accent)] shadow-sm"
                : "text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]"
            }`}
          >
            <Activity className="h-3.5 w-3.5" />
            Live Monitor
          </button>
          <button
            onClick={() => setActiveTab("HISTORICAL")}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-bold transition-all ${
              activeTab === "HISTORICAL"
                ? "bg-[var(--color-surface)] text-[var(--color-accent)] shadow-sm"
                : "text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]"
            }`}
          >
            <Database className="h-3.5 w-3.5" />
            Historical Logs
          </button>
        </div>
      </div>

      {/* Tab 1: Live Monitor */}
      {activeTab === "LIVE" && (
        <div className="space-y-6">
          {/* Live Controller Panel */}
          <GlassCard className="p-5 flex flex-col md:flex-row gap-5 items-stretch md:items-center justify-between">
            <div className="flex items-center gap-4 flex-wrap">
              {/* WS Status Badge */}
              <div className="flex items-center gap-2">
                <span className={`h-2.5 w-2.5 rounded-full ${
                  wsStatus === "connected" 
                    ? "bg-emerald-400 animate-pulse" 
                    : wsStatus === "connecting"
                    ? "bg-amber-400 animate-pulse"
                    : "bg-red-500"
                }`} />
                <span className="text-xs font-mono font-bold text-text-secondary uppercase">
                  {wsStatus}
                </span>
              </div>

              <div className="h-4 w-[1px] bg-[var(--color-border)] hidden md:block" />

              {/* Simulation Mode Toggle */}
              <button
                onClick={() => setSimulate(!simulate)}
                className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold transition-all ${
                  simulate
                    ? "bg-[var(--color-accent)] text-white"
                    : "bg-[var(--color-surface-2)] text-[var(--color-text-secondary)] border border-[var(--color-border)] hover:bg-[var(--color-surface)]"
                }`}
              >
                {simulate ? <Pause className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5" />}
                {simulate ? "Simulation Active" : "Start Simulation"}
              </button>

              {/* Rate Adjustment (Only if simulate active) */}
              {simulate && (
                <div className="flex items-center gap-2 bg-[var(--color-surface-2)] px-3 py-1.5 rounded-xl border border-[var(--color-border)]/60">
                  <button
                    onClick={() => setSimulationRate(Math.max(0.2, simulationRate - 0.2))}
                    className="w-6 h-6 flex items-center justify-center rounded bg-[var(--color-border)] text-text-primary font-bold hover:bg-[var(--color-accent)] hover:text-white"
                  >-</button>
                  <span className="text-xs font-mono font-bold text-text-primary w-10 text-center">
                    {simulationRate.toFixed(1)}/s
                  </span>
                  <button
                    onClick={() => setSimulationRate(Math.min(5.0, simulationRate + 0.2))}
                    className="w-6 h-6 flex items-center justify-center rounded bg-[var(--color-border)] text-text-primary font-bold hover:bg-[var(--color-accent)] hover:text-white"
                  >+</button>
                </div>
              )}
            </div>

            {/* Clear logs action */}
            <button
              onClick={clearEvents}
              disabled={liveEvents.length === 0}
              className="flex items-center justify-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold bg-red-950/40 text-red-400 border border-red-800/20 hover:bg-red-950/60 transition-all disabled:opacity-40 disabled:pointer-events-none"
            >
              <Trash2 className="h-3.5 w-3.5" />
              Clear Monitor Log
            </button>
          </GlassCard>

          {/* Live events grid */}
          <div className="space-y-4">
            {liveEvents.length === 0 ? (
              <div className="p-16 rounded-2xl border border-[var(--color-border)] border-dashed text-center flex flex-col items-center justify-center">
                <Activity className="h-12 w-12 text-[var(--color-text-muted)] animate-pulse text-3" />
                <h3 className="text-sm font-bold text-[var(--color-text-secondary)] mt-3">
                  Connect to threat stream to monitor live events
                </h3>
                <p className="text-xs text-[var(--color-text-muted)] font-medium max-w-xs mt-1">
                  Use Simulation Mode to preview feed
                </p>
              </div>
            ) : (
              <div className="space-y-4 max-h-[calc(100vh-400px)] overflow-y-auto">
                {liveEvents.map((evt) => (
                  <ThreatEventCard key={evt.event_id} event={evt} />
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 2: Historical Logs */}
      {activeTab === "HISTORICAL" && (
        <div className="space-y-6">
          {/* Filtering Section */}
          <GlassCard className="p-4 flex flex-col md:flex-row gap-4 items-center justify-between">
            {/* Search Input */}
            <div className="relative w-full md:w-80">
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-text-secondary" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by filename or domain..."
                className="w-full pl-10 pr-4 py-2.5 bg-bg-base/40 border border-border rounded-xl text-xs font-semibold text-text-primary placeholder:text-text-secondary focus:outline-none focus:border-accent-blue focus:bg-white transition-all"
              />
            </div>

            {/* Filters Group */}
            <div className="flex flex-wrap gap-3 w-full md:w-auto items-center justify-end">
              <div className="flex items-center gap-1.5 text-xs text-text-secondary font-bold shrink-0">
                <Filter className="h-3.5 w-3.5" />
                <span>Filters:</span>
              </div>

              {/* Type dropdown */}
              <select
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value as "ALL" | "DOCUMENT" | "URL")}
                className="px-3 py-2 bg-surface hover:bg-white border border-border rounded-xl text-xs font-bold text-text-primary focus:outline-none focus:border-accent-blue cursor-pointer transition-colors"
              >
                <option value="ALL">All Asset Types</option>
                <option value="DOCUMENT">Documents Only</option>
                <option value="URL">URLs / Hostnames</option>
              </select>

              {/* Severity dropdown */}
              <select
                value={riskFilter}
                onChange={(e) => setRiskFilter(e.target.value as "ALL" | "CLEAN" | "SUSPICIOUS" | "HIGH")}
                className="px-3 py-2 bg-surface hover:bg-white border border-border rounded-xl text-xs font-bold text-text-primary focus:outline-none focus:border-accent-blue cursor-pointer transition-colors"
              >
                <option value="ALL">All Risk Levels</option>
                <option value="CLEAN">Verified Safe</option>
                <option value="SUSPICIOUS">Suspicious</option>
                <option value="HIGH">High Risk</option>
              </select>
            </div>
          </GlassCard>

          {/* Events Table Container */}
          {loading ? (
            <div className="space-y-4">
              <SkeletonLoader variant="card" className="h-16" />
              <SkeletonLoader variant="card" className="h-16" />
              <SkeletonLoader variant="card" className="h-16" />
              <SkeletonLoader variant="card" className="h-16" />
            </div>
          ) : events.length === 0 ? (
            /* Demo mode: backend is not connected — the events load returned
               an empty list. Show a friendly empty state instead of an
               empty table with a single "No matching…" row. */
            <EmptyStateWithCTA
              icon="history"
              title="No activity yet"
              description="Event timeline will show recent scans across all shields once a backend is connected."
              technicalDetails="Backend not connected · Demo mode"
              primaryAction={{ label: "Try UPI Shield →", href: "/upi-shield" }}
            />
          ) : (
            <>
              {/* Desktop Table View */}
              <GlassCard className="hidden sm:block p-0 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full border-collapse text-left text-xs text-text-secondary">
                  <thead>
                    <tr className="bg-bg-base/40 border-b border-border/80 font-bold text-text-secondary uppercase tracking-wider text-[10px]">
                      <th className="py-4 px-6">Timestamp</th>
                      <th className="py-4 px-6">Vetted Target</th>
                      <th className="py-4 px-6">Type</th>
                      <th className="py-4 px-6 text-center">Score</th>
                      <th className="py-4 px-6">Severity</th>
                      <th className="py-4 px-6">Incidents Flagged</th>
                      <th className="py-4 px-6 text-center w-12">Details</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/40 font-semibold">
                    {filteredEvents.length === 0 ? (
                      <tr>
                        <td colSpan={7} className="text-center py-12 text-text-secondary italic font-semibold">
                          No matching threat records found in log cache.
                        </td>
                      </tr>
                    ) : (
                      filteredEvents.map((event) => {
                        const targetName = event.original_filename || event.source_domain || "Unknown Asset";
                        const isExpanded = expandedEventId === event.event_id;

                        return (
                          <React.Fragment key={event.event_id}>
                            <tr
                              onClick={() => toggleRow(event.event_id)}
                              className={`hover:bg-bg-base/30 cursor-pointer transition-colors ${isExpanded ? "bg-bg-base/50" : ""}`}
                            >
                              <td className="py-4 px-6 font-mono text-text-secondary/80 whitespace-nowrap">
                                {new Date(event.created_at).toLocaleString()}
                              </td>
                              <td className="py-4 px-6 font-bold text-text-primary truncate max-w-[200px]" title={targetName}>
                                {targetName}
                              </td>
                              <td className="py-4 px-6 whitespace-nowrap">
                                <span className="inline-flex items-center gap-1.5 font-bold text-[10px]">
                                  {event.source_type === "DOCUMENT" ? (
                                    <>
                                      <FileText className="h-3.5 w-3.5 text-accent-blue" />
                                      <span className="text-accent-blue">Document</span>
                                    </>
                                  ) : (
                                    <>
                                      <Globe className="h-3.5 w-3.5 text-accent-teal" />
                                      <span className="text-accent-teal">URL / Host</span>
                                    </>
                                  )}
                                </span>
                              </td>
                              <td className="py-4 px-6 font-mono font-extrabold text-center text-text-primary whitespace-nowrap">
                                {event.risk_score}
                              </td>
                              <td className="py-4 px-6 whitespace-nowrap">
                                <RiskBadge variant={getRiskVariant(event.risk_level)} />
                              </td>
                              <td className="py-4 px-6 text-text-secondary font-medium max-w-xs truncate" title={event.risk_indicators?.join(", ")}>
                                {event.risk_indicators && event.risk_indicators.length > 0
                                  ? event.risk_indicators.join(", ")
                                  : event.document_type_hint || "No anomalies flagged"}
                              </td>
                              <td className="py-4 px-6 text-center">
                                <button className="text-text-secondary hover:text-text-primary transition-colors">
                                  {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                                </button>
                              </td>
                            </tr>

                            {/* Collapsible Details Drawer */}
                            {isExpanded && (
                              <tr>
                                <td colSpan={7} className="bg-bg-base/10 p-6 border-t border-border/40">
                                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-xs leading-relaxed text-text-secondary max-w-5xl">
                                    
                                    {/* Static Details */}
                                    <div className="space-y-3 p-4 rounded-2xl bg-surface border border-border shadow-sm">
                                      <span className="text-[10px] text-text-secondary font-bold uppercase tracking-wider flex items-center gap-1.5">
                                        <Layers className="h-3.5 w-3.5" /> Static Identifiers
                                      </span>
                                      <div className="space-y-1.5 font-medium">
                                        <div>Event ID: <code className="text-text-primary bg-bg-base/70 px-1 py-0.5 rounded font-mono text-[10px]">{event.event_id}</code></div>
                                        {event.doc_id && <div>Doc ID: <code className="text-text-primary bg-bg-base/70 px-1 py-0.5 rounded font-mono text-[10px]">{event.doc_id}</code></div>}
                                        {event.file_hash && <div className="truncate">File SHA-256: <code className="text-text-primary bg-bg-base/70 px-1 py-0.5 rounded font-mono text-[10px]" title={event.file_hash}>{event.file_hash.substring(0, 16)}...</code></div>}
                                        {event.metadata_hash && <div className="truncate">Meta ID: <code className="text-text-primary bg-bg-base/70 px-1 py-0.5 rounded font-mono text-[10px]">{event.metadata_hash}</code></div>}
                                      </div>
                                    </div>

                                    {/* Metadata Source */}
                                    <div className="space-y-3 p-4 rounded-2xl bg-surface border border-border shadow-sm">
                                      <span className="text-[10px] text-text-secondary font-bold uppercase tracking-wider flex items-center gap-1.5">
                                        <Terminal className="h-3.5 w-3.5" /> Forensic Editor Meta
                                      </span>
                                      <div className="space-y-1.5 font-medium">
                                        <div>Creator Tool: <strong className="text-text-primary">{event.creator || "Not Available"}</strong></div>
                                        <div>PDF Producer: <strong className="text-text-primary">{event.producer || "Not Available"}</strong></div>
                                        <div>Editor Agent: <strong className="text-text-primary">{event.editor_tool || "Not Available"}</strong></div>
                                      </div>
                                    </div>

                                    {/* Flags raised */}
                                    <div className="space-y-3 p-4 rounded-2xl bg-surface border border-border shadow-sm">
                                      <span className="text-[10px] text-text-secondary font-bold uppercase tracking-wider flex items-center gap-1.5">
                                        <Cpu className="h-3.5 w-3.5" /> Indicators Vetted
                                      </span>
                                      {!event.risk_indicators || event.risk_indicators.length === 0 ? (
                                        <div className="flex items-center gap-1.5 text-risk-safe font-bold">
                                          <ShieldCheck className="h-4 w-4" /> Validated Clean Asset
                                        </div>
                                      ) : (
                                        <ul className="space-y-1.5">
                                          {event.risk_indicators.map((indicator, index) => (
                                            <li key={index} className="flex gap-1.5 items-start font-medium text-text-primary">
                                              <CornerDownRight className="h-3.5 w-3.5 text-text-secondary/70 shrink-0 mt-0.5" />
                                              <span>{indicator}</span>
                                            </li>
                                          ))}
                                        </ul>
                                      )}
                                    </div>

                                  </div>
                                </td>
                              </tr>
                            )}
                          </React.Fragment>
                        );
                      })
                    )}
                  </tbody>
                </table>
              </div>
              </GlassCard>

              {/* Mobile Cards View */}
              <div className="sm:hidden space-y-3">
                {filteredEvents.length === 0 ? (
                  <GlassCard className="p-8 text-center text-text-secondary italic font-semibold">
                    No matching threat records found in log cache.
                  </GlassCard>
                ) : (
                  filteredEvents.map((event) => {
                    const targetName = event.original_filename || event.source_domain || "Unknown Asset";
                    const isExpanded = expandedEventId === event.event_id;
                    return (
                      <GlassCard
                        key={event.event_id}
                        className="p-4 cursor-pointer"
                        onClick={() => toggleRow(event.event_id)}
                      >
                        <div className="space-y-2.5">
                          <div className="flex items-center justify-between gap-2">
                            <span className="inline-flex items-center gap-1.5 font-bold text-[10px]">
                              {event.source_type === "DOCUMENT" ? (
                                <>
                                  <FileText className="h-3.5 w-3.5 text-accent-blue" />
                                  <span className="text-accent-blue">Document</span>
                                </>
                              ) : (
                                <>
                                  <Globe className="h-3.5 w-3.5 text-accent-teal" />
                                  <span className="text-accent-teal">URL / Host</span>
                                </>
                              )}
                            </span>
                            <RiskBadge variant={getRiskVariant(event.risk_level)} />
                          </div>

                          <div className="font-bold text-text-primary truncate" title={targetName}>
                            {targetName}
                          </div>

                          <div className="flex items-center justify-between gap-3 text-[11px] font-mono">
                            <span className="text-text-secondary/80 truncate">
                              {new Date(event.created_at).toLocaleString()}
                            </span>
                            <span className="font-extrabold text-text-primary shrink-0">
                              Score {event.risk_score}
                            </span>
                          </div>

                          {event.risk_indicators && event.risk_indicators.length > 0 && (
                            <p className="text-[11px] text-text-secondary line-clamp-2">
                              {event.risk_indicators.join(", ")}
                            </p>
                          )}

                          <div className="flex items-center justify-end pt-1 border-t border-border/30">
                            {isExpanded ? <ChevronUp className="h-4 w-4 text-text-secondary" /> : <ChevronDown className="h-4 w-4 text-text-secondary" />}
                          </div>

                          {isExpanded && (
                            <div className="pt-2 border-t border-border/30 space-y-2 text-[11px] text-text-secondary">
                              <div>Event ID: <code className="text-text-primary bg-bg-base/70 px-1 py-0.5 rounded font-mono text-[10px]">{event.event_id}</code></div>
                              {event.doc_id && <div>Doc ID: <code className="text-text-primary bg-bg-base/70 px-1 py-0.5 rounded font-mono text-[10px]">{event.doc_id}</code></div>}
                              {event.file_hash && <div className="truncate">SHA-256: <code className="text-text-primary bg-bg-base/70 px-1 py-0.5 rounded font-mono text-[10px]">{event.file_hash.substring(0, 16)}...</code></div>}
                              {!event.risk_indicators || event.risk_indicators.length === 0 ? (
                                <div className="flex items-center gap-1.5 text-risk-safe font-bold">
                                  <ShieldCheck className="h-4 w-4" /> Validated Clean Asset
                                </div>
                              ) : (
                                <ul className="space-y-1">
                                  {event.risk_indicators.map((ind, i) => (
                                    <li key={i} className="flex gap-1.5 items-start">
                                      <CornerDownRight className="h-3 w-3 text-text-secondary/70 shrink-0 mt-0.5" />
                                      <span>{ind}</span>
                                    </li>
                                  ))}
                                </ul>
                              )}
                            </div>
                          )}
                        </div>
                      </GlassCard>
                    );
                  })
                )}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
