"use client";

import React, { useState, useEffect } from "react";
import { 
  History, 
  Search, 
  Filter, 
  FileText, 
  Globe, 
  Calendar,
  Layers,
  Cpu,
  CornerDownRight,
  HelpCircle,
  Clock,
  Terminal,
  User,
  ShieldCheck,
  ChevronDown,
  ChevronUp
} from "lucide-react";
import GlassCard from "@/components/GlassCard";
import ThreatBadge from "@/components/ThreatBadge";
import { dashboardService } from "@/services/dashboard";
import { RecentEvent } from "@/types";

export default function ThreatEventsPage() {
  const [events, setEvents] = useState<RecentEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState<"ALL" | "DOCUMENT" | "URL">("ALL");
  const [riskFilter, setRiskFilter] = useState<"ALL" | "CLEAN" | "SUSPICIOUS" | "HIGH">("ALL");
  const [expandedEventId, setExpandedEventId] = useState<string | null>(null);

  useEffect(() => {
    async function loadEvents() {
      try {
        const response = await dashboardService.getRecentEvents(50);
        setEvents(response.events);
      } catch (error) {
        console.error("Failed to load events logs", error);
      } finally {
        setLoading(false);
      }
    }
    loadEvents();
  }, []);

  const toggleRow = (id: string) => {
    if (expandedEventId === id) {
      setExpandedEventId(null);
    } else {
      setExpandedEventId(id);
    }
  };

  const getScoreSeverity = (score: number) => {
    if (score >= 30) return "HIGH";
    if (score >= 15) return "SUSPICIOUS";
    return "CLEAN";
  };

  // Filter events based on criteria
  const filteredEvents = events.filter((event) => {
    const target = (event.original_filename || event.source_domain || "").toLowerCase();
    const matchesSearch = target.includes(searchQuery.toLowerCase());
    
    const matchesType = typeFilter === "ALL" || event.source_type === typeFilter;
    
    let matchesRisk = true;
    if (riskFilter !== "ALL") {
      const severity = getScoreSeverity(event.risk_score);
      matchesRisk = severity === riskFilter;
    }

    return matchesSearch && matchesType && matchesRisk;
  });

  if (loading) {
    return (
      <div className="space-y-8 animate-pulse">
        <div className="h-8 w-64 bg-slate-200 rounded-lg"></div>
        <div className="h-14 bg-slate-200 rounded-2xl"></div>
        <div className="space-y-4">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-16 bg-slate-200 rounded-2xl"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      
      {/* Header */}
      <div>
        <h2 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight flex items-center gap-3">
          <History className="h-7 w-7 text-slate-900" />
          Threat Activity Log
        </h2>
        <p className="text-slate-500 mt-1.5 text-sm font-medium">
          Unified audit logs recording asset metadata signatures, character mimicry alerts, and binary structural profiles.
        </p>
      </div>

      {/* Filtering Workspace */}
      <GlassCard className="p-5 flex flex-col md:flex-row gap-4 items-center justify-between">
        {/* Search */}
        <div className="relative w-full md:w-80">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by filename or domain..."
            className="w-full pl-10 pr-4 py-2 bg-[#FBFBFC] border border-slate-200/80 rounded-xl text-xs font-semibold text-slate-800 placeholder-slate-400 focus:outline-none focus:border-sky-500 transition-all"
          />
        </div>

        {/* Filters */}
        <div className="flex flex-wrap gap-3 w-full md:w-auto items-center justify-end">
          <div className="flex items-center gap-1.5 text-xs text-slate-500 font-bold shrink-0">
            <Filter className="h-3.5 w-3.5" />
            <span>Filters:</span>
          </div>

          {/* Type dropdown */}
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value as any)}
            className="px-3 py-1.5 bg-white border border-slate-200 rounded-lg text-[11px] font-bold text-slate-600 focus:outline-none focus:border-sky-500 cursor-pointer"
          >
            <option value="ALL">All Asset Types</option>
            <option value="DOCUMENT">Documents</option>
            <option value="URL">Hostnames / URLs</option>
          </select>

          {/* Severity dropdown */}
          <select
            value={riskFilter}
            onChange={(e) => setRiskFilter(e.target.value as any)}
            className="px-3 py-1.5 bg-white border border-slate-200 rounded-lg text-[11px] font-bold text-slate-600 focus:outline-none focus:border-sky-500 cursor-pointer"
          >
            <option value="ALL">All Risk Indices</option>
            <option value="CLEAN">Verified Safe</option>
            <option value="SUSPICIOUS">Suspicious</option>
            <option value="HIGH">High Risk</option>
          </select>
        </div>
      </GlassCard>

      {/* Incidents Table list */}
      <GlassCard className="p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-left text-xs text-slate-600">
            <thead>
              <tr className="bg-[#FBFBFC] border-b border-slate-200/70 font-bold text-slate-500 uppercase tracking-wider text-[10px]">
                <th className="py-4 px-6">Timestamp</th>
                <th className="py-4 px-6">Vetted target</th>
                <th className="py-4 px-6">Type</th>
                <th className="py-4 px-6 text-center">Score</th>
                <th className="py-4 px-6">Severity</th>
                <th className="py-4 px-6">Incidents Summary</th>
                <th className="py-4 px-6 text-center w-12">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredEvents.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-12 text-slate-400 font-semibold">
                    No matching threat records found.
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
                        className={`hover:bg-slate-50/50 cursor-pointer transition-colors ${isExpanded ? "bg-slate-50/80" : ""}`}
                      >
                        <td className="py-4 px-6 font-semibold text-slate-400 whitespace-nowrap">
                          {new Date(event.created_at).toLocaleString()}
                        </td>
                        <td className="py-4 px-6 font-bold text-slate-800 truncate max-w-[200px]" title={targetName}>
                          {targetName}
                        </td>
                        <td className="py-4 px-6 whitespace-nowrap">
                          <span className="inline-flex items-center gap-1.5 font-bold text-[10px]">
                            {event.source_type === "DOCUMENT" ? (
                              <>
                                <FileText className="h-3.5 w-3.5 text-sky-600" />
                                <span className="text-sky-700">Document</span>
                              </>
                            ) : (
                              <>
                                <Globe className="h-3.5 w-3.5 text-emerald-600" />
                                <span className="text-emerald-700">URL / Host</span>
                              </>
                            )}
                          </span>
                        </td>
                        <td className="py-4 px-6 font-extrabold text-center text-slate-700 whitespace-nowrap">
                          {event.risk_score}
                        </td>
                        <td className="py-4 px-6 whitespace-nowrap">
                          <ThreatBadge level={event.risk_level} />
                        </td>
                        <td className="py-4 px-6 text-slate-500 font-medium max-w-xs truncate" title={event.risk_indicators.join(", ")}>
                          {event.risk_indicators.length > 0 
                            ? event.risk_indicators.join(", ") 
                            : event.document_type_hint || "No anomalies flagged"}
                        </td>
                        <td className="py-4 px-6 text-center">
                          <button className="text-slate-400 hover:text-slate-700 transition-colors">
                            {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                          </button>
                        </td>
                      </tr>

                      {/* Collapsible details subrow */}
                      {isExpanded && (
                        <tr>
                          <td colSpan={7} className="bg-slate-50/50 p-6 border-t border-slate-100">
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-[11px] leading-relaxed text-slate-500 font-medium max-w-5xl">
                              
                              {/* Meta Details */}
                              <div className="space-y-3 p-4 rounded-2xl bg-white border border-slate-200/50 shadow-sm">
                                <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider flex items-center gap-1">
                                  <Layers className="h-3.5 w-3.5" /> Static Properties
                                </span>
                                <div className="space-y-1.5">
                                  <div>Event ID: <code className="text-slate-800 bg-slate-50 px-1 py-0.5 rounded">{event.event_id}</code></div>
                                  {event.doc_id && <div>Doc ID: <code className="text-slate-800 bg-slate-50 px-1 py-0.5 rounded">{event.doc_id}</code></div>}
                                  {event.file_hash && <div className="truncate">File SHA-256: <code className="text-slate-800 bg-slate-50 px-1 py-0.5 rounded" title={event.file_hash}>{event.file_hash.substring(0, 16)}...</code></div>}
                                  {event.metadata_hash && <div className="truncate">Meta ID: <code className="text-slate-800 bg-slate-50 px-1 py-0.5 rounded">{event.metadata_hash}</code></div>}
                                </div>
                              </div>

                              {/* Forensic Audit context */}
                              <div className="space-y-3 p-4 rounded-2xl bg-white border border-slate-200/50 shadow-sm">
                                <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider flex items-center gap-1">
                                  <Terminal className="h-3.5 w-3.5" /> Editing Metadata
                                </span>
                                <div className="space-y-1.5">
                                  <div>Creator Suit: <strong className="text-slate-700">{event.creator || "Not Defined"}</strong></div>
                                  <div>Producer Link: <strong className="text-slate-700">{event.producer || "Not Defined"}</strong></div>
                                  <div>Software Agent: <strong className="text-slate-700">{event.editor_tool || "Not Defined"}</strong></div>
                                </div>
                              </div>

                              {/* Triggered Rule items */}
                              <div className="space-y-3 p-4 rounded-2xl bg-white border border-slate-200/50 shadow-sm">
                                <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider flex items-center gap-1">
                                  <Cpu className="h-3.5 w-3.5" /> Flags Raised
                                </span>
                                {event.risk_indicators.length === 0 ? (
                                  <div className="flex items-center gap-1.5 text-emerald-600 font-bold">
                                    <ShieldCheck className="h-4 w-4" /> Validated Clean Asset
                                  </div>
                                ) : (
                                  <ul className="space-y-1.5">
                                    {event.risk_indicators.map((indicator, index) => (
                                      <li key={index} className="flex gap-1.5 items-start">
                                        <CornerDownRight className="h-3.5 w-3.5 text-slate-400 shrink-0 mt-0.5" />
                                        <span className="text-slate-700 font-semibold">{indicator}</span>
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

    </div>
  );
}
