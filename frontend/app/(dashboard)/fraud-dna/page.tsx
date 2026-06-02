"use client";

import React, { useEffect, useState } from "react";
import fraudDnaApi from "@/lib/api/fraud-dna";
import { CampaignsResponse, GraphResponse, ThreatSummary, GraphNode } from "@/lib/types";
import GlassCard from "@/components/ui/GlassCard";
import RiskBadge from "@/components/ui/RiskBadge";
import SkeletonLoader from "@/components/ui/SkeletonLoader";
import {
  GitBranch,
  Fingerprint,
  RefreshCw,
  TrendingUp,
  AlertTriangle,
  Info,
  Calendar,
  Layers,
  ChevronDown,
  ChevronUp,
  Zap,
  Network
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export default function FraudDnaPage() {
  const [campaigns, setCampaigns] = useState<CampaignsResponse | null>(null);
  const [graphData, setGraphData] = useState<GraphResponse | null>(null);
  const [summary, setSummary] = useState<ThreatSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isReclustering, setIsReclustering] = useState(false);
  const [expandedCampaignId, setExpandedCampaignId] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);

  const fetchDnaData = async (reclustering = false) => {
    if (reclustering) setIsReclustering(true);
    else setIsLoading(true);

    try {
      if (reclustering) {
        await fraudDnaApi.recluster();
      }
      const [campData, graphDataRes, summaryRes] = await Promise.all([
        fraudDnaApi.getCampaigns(),
        fraudDnaApi.getGraph(),
        fraudDnaApi.getThreatSummary()
      ]);

      setCampaigns(campData);
      setGraphData(graphDataRes);
      setSummary(summaryRes);
    } catch (err) {
      console.error("Error loading Fraud DNA cluster metrics:", err);
    } finally {
      setIsLoading(false);
      setIsReclustering(false);
    }
  };

  useEffect(() => {
    fetchDnaData();
  }, []);

  const handleRecluster = () => {
    fetchDnaData(true);
  };

  const getThreatVariant = (level: string) => {
    switch (level) {
      case "CRITICAL":
        return "critical";
      case "ELEVATED":
        return "high";
      case "WARNING":
        return "medium";
      default:
        return "safe";
    }
  };

  // Node position map for mock nodes to render SVG connections
  const nodePositions: Record<string, { x: number; y: number }> = {
    "evt-f89a23": { x: 80, y: 70 },
    "evt-a78b45": { x: 50, y: 150 },
    "evt-67d8f9": { x: 160, y: 160 },
    "actor-invoice-spoofer": { x: 120, y: 110 },
    
    "evt-87f12e": { x: 300, y: 80 },
    "evt-45b678": { x: 260, y: 170 },
    "actor-id-forge": { x: 330, y: 140 }
  };

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-text-primary">
            Fraud DNA Connected Clusters
          </h1>
          <p className="text-sm text-text-secondary font-medium">
            Evaluate overlapping document fingerprints, shared EXIF editor tags, and metadata timestamps.
          </p>
        </div>

        <button
          onClick={handleRecluster}
          disabled={isReclustering || isLoading}
          className="inline-flex items-center justify-center gap-1.5 rounded-xl border border-border bg-surface hover:bg-white text-xs font-bold text-text-primary px-4 py-2.5 shadow-sm transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 shrink-0"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${isReclustering ? "animate-spin text-accent-blue" : "text-text-secondary"}`} />
          {isReclustering ? "Re-clustering..." : "Re-cluster Sandbox"}
        </button>
      </div>

      {isLoading ? (
        <div className="space-y-8">
          <SkeletonLoader variant="card" className="h-[120px]" />
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <SkeletonLoader key="c1" variant="card" className="lg:col-span-2 h-[450px]" />
            <SkeletonLoader key="c2" variant="card" className="h-[450px]" />
          </div>
        </div>
      ) : (
        <>
          {/* Top Threat summary panel */}
          {summary && (
            <GlassCard className="p-6 border-l-4 border-l-risk-high">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold text-text-secondary uppercase tracking-widest">
                      Threat Intelligence Analysis Summary
                    </span>
                    <RiskBadge variant={getThreatVariant(summary.threat_level)} />
                  </div>
                  <p className="text-sm text-text-primary font-semibold leading-relaxed mt-2.5">
                    {summary.summary}
                  </p>
                </div>

                <div className="flex gap-4 sm:border-l border-border/40 sm:pl-6 shrink-0 font-semibold text-xs text-text-secondary">
                  <div className="text-center">
                    <span className="block font-mono text-xl font-bold text-risk-critical">
                      {summary.high_risk_count}
                    </span>
                    <span>High Risk</span>
                  </div>
                  <div className="text-center border-l border-border/40 pl-4">
                    <span className="block font-mono text-xl font-bold text-risk-medium">
                      {summary.suspicious_count}
                    </span>
                    <span>Suspicious</span>
                  </div>
                </div>
              </div>
            </GlassCard>
          )}

          {/* Core Interactive Layout */}
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
            {/* Left: Campaigns clusters list */}
            <div className="lg:col-span-3 space-y-6">
              <GlassCard className="p-6">
                <h3 className="text-base font-bold text-text-primary mb-1">Identified Campaigns</h3>
                <p className="text-xs text-text-secondary font-medium mb-6">Threat events pooled together based on shared DNA traits.</p>

                <div className="space-y-4">
                  {campaigns?.campaigns.map((camp) => {
                    const isExpanded = expandedCampaignId === camp.campaign_id;
                    return (
                      <div
                        key={camp.campaign_id}
                        className="border border-border/60 rounded-2xl bg-bg-base/30 overflow-hidden"
                      >
                        {/* Header bar */}
                        <div
                          onClick={() => setExpandedCampaignId(isExpanded ? null : camp.campaign_id)}
                          className="flex items-center justify-between p-4 cursor-pointer hover:bg-bg-base/60 transition-colors"
                        >
                          <div className="flex items-center gap-3">
                            <span className="h-8 w-8 rounded-xl bg-text-primary/5 text-text-primary flex items-center justify-center font-mono text-xs font-bold border border-border/60 shrink-0">
                              {camp.event_count}
                            </span>
                            <div>
                              <div className="text-xs font-bold text-text-primary font-mono uppercase">
                                ID: {camp.campaign_id}
                              </div>
                              <div className="text-[10px] text-text-secondary font-semibold mt-0.5">
                                Avg score: <span className="font-mono">{camp.avg_risk_score.toFixed(0)}</span>
                              </div>
                            </div>
                          </div>

                          <div className="flex items-center gap-3">
                            <RiskBadge
                              variant={
                                camp.risk_level === "HIGH"
                                  ? "high"
                                  : camp.risk_level === "SUSPICIOUS"
                                  ? "medium"
                                  : "safe"
                              }
                            />
                            {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                          </div>
                        </div>

                        {/* Expandable info list */}
                        <AnimatePresence>
                          {isExpanded && (
                            <motion.div
                              initial={{ opacity: 0, height: 0 }}
                              animate={{ opacity: 1, height: "auto" }}
                              exit={{ opacity: 0, height: 0 }}
                              transition={{ duration: 0.2 }}
                              className="border-t border-border/40 px-5 py-4 space-y-4 bg-surface/50 text-xs font-medium text-text-secondary"
                            >
                              {/* Common parameters */}
                              <div className="grid grid-cols-2 gap-4">
                                <div>
                                  <div className="text-[9px] font-bold text-text-secondary uppercase mb-1">Common Keywords</div>
                                  <div className="flex flex-wrap gap-1">
                                    {camp.common_keywords.map((kw, i) => (
                                      <span key={i} className="bg-bg-base border border-border/50 px-1.5 py-0.5 rounded text-[10px] text-text-primary font-semibold">
                                        {kw}
                                      </span>
                                    ))}
                                  </div>
                                </div>
                                <div>
                                  <div className="text-[9px] font-bold text-text-secondary uppercase mb-1">Common Indicators</div>
                                  <div className="flex flex-wrap gap-1">
                                    {camp.common_indicators.map((ind, i) => (
                                      <span key={i} className="bg-risk-high/5 text-risk-high border border-risk-high/15 px-1.5 py-0.5 rounded text-[9px] font-mono">
                                        {ind}
                                      </span>
                                    ))}
                                  </div>
                                </div>
                              </div>

                              {/* Nested events sublist */}
                              <div className="space-y-2 mt-4">
                                <div className="text-[9px] font-bold text-text-secondary uppercase">Associated Scans</div>
                                <div className="space-y-1.5">
                                  {camp.events.map((evt) => (
                                    <div
                                      key={evt.event_id}
                                      className="flex items-center justify-between p-2.5 rounded-xl border border-border/30 bg-bg-base/30 text-xs"
                                    >
                                      <span className="font-mono text-text-primary font-bold">{evt.label}</span>
                                      <div className="flex items-center gap-2">
                                        <span className="font-mono font-bold text-[11px] text-text-secondary">score: {evt.risk_score}</span>
                                        <RiskBadge variant={evt.risk_level === "HIGH" ? "high" : "medium"} />
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </div>
                    );
                  })}
                </div>
              </GlassCard>
            </div>

            {/* Right: SVG DNA cluster graph canvas */}
            <div className="lg:col-span-2 space-y-6">
              <GlassCard className="p-6 flex flex-col h-[520px]">
                <div className="mb-4">
                  <h3 className="text-base font-bold text-text-primary">Connected Network Map</h3>
                  <p className="text-xs text-text-secondary font-medium mt-0.5">Click actor templates or event nodes to verify correlations.</p>
                </div>

                {/* SVG Visual Canvas */}
                <div className="flex-1 bg-bg-base/50 rounded-2xl border border-border/60 relative overflow-hidden min-h-[300px]">
                  {/* Grid background on canvas */}
                  <div className="absolute inset-0 grid-bg opacity-30 pointer-events-none" />

                  {/* Draw SVG connections */}
                  <svg className="absolute inset-0 w-full h-full pointer-events-none">
                    {graphData?.edges.map((edge, idx) => {
                      const pos1 = nodePositions[edge.source];
                      const pos2 = nodePositions[edge.target];
                      if (!pos1 || !pos2) return null;
                      return (
                        <g key={idx}>
                          <line
                            x1={`${pos1.x}%`}
                            y1={`${pos1.y}px`}
                            x2={`${pos2.x}%`}
                            y2={`${pos2.y}px`}
                            stroke="rgba(10, 132, 255, 0.25)"
                            strokeWidth="1.5"
                          />
                        </g>
                      );
                    })}
                  </svg>

                  {/* Floating HTML Nodes */}
                  {graphData?.nodes.map((node) => {
                    const pos = nodePositions[node.id];
                    if (!pos) return null;
                    const isSelected = selectedNode?.id === node.id;
                    const isActor = node.type === "ACTOR";

                    return (
                      <button
                        key={node.id}
                        onClick={() => setSelectedNode(node)}
                        style={{ left: `${pos.x}%`, top: `${pos.y}px` }}
                        className={`absolute -translate-x-1/2 -translate-y-1/2 flex items-center justify-center p-2 rounded-xl transition-all border shadow-sm ${
                          isSelected
                            ? "bg-text-primary text-white border-text-primary scale-110 z-10"
                            : isActor
                            ? "bg-accent-blue/15 text-accent-blue border-accent-blue/40"
                            : "bg-surface text-text-primary border-border/80"
                        }`}
                      >
                        {isActor ? (
                          <Network className="h-4.5 w-4.5" />
                        ) : (
                          <Fingerprint className="h-4.5 w-4.5" />
                        )}
                      </button>
                    );
                  })}
                </div>

                {/* Node Metadata tray */}
                <div className="mt-4 border-t border-border/40 pt-4 text-xs font-semibold">
                  {selectedNode ? (
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] font-bold text-text-secondary uppercase">
                          Selected Node Metadata
                        </span>
                        <span className="font-mono text-[10px] text-text-secondary bg-bg-base px-2 py-0.5 rounded border">
                          {selectedNode.type}
                        </span>
                      </div>
                      <div className="text-text-primary font-bold text-sm">
                        {selectedNode.label}
                      </div>
                      <div className="flex gap-4 text-text-secondary mt-1">
                        <div>
                          Verdict: <span className="text-text-primary">{selectedNode.risk_level}</span>
                        </div>
                        <div>
                          Score: <span className="text-text-primary font-mono">{selectedNode.risk_score}</span>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="text-text-secondary italic text-center py-2 flex items-center justify-center gap-1.5">
                      <Info className="h-4 w-4" /> Tap nodes in the grid canvas to verify matching signatures.
                    </div>
                  )}
                </div>
              </GlassCard>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
