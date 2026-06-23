"use client";

import React, { useEffect, useState, useRef, useMemo, useCallback } from "react";
import fraudDnaApi from "@/lib/api/fraud-dna";
import {
  CampaignsResponse,
  GraphResponse,
  ThreatSummary,
  CampaignAIResult,
  FraudCampaignDetail
} from "@/lib/types";
import aiApi from "@/lib/api/ai";
import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import DataPoint from "@/components/ui/DataPoint";
import { EmptyStateWithCTA } from "@/components/ui/EmptyStateWithCTA";
import {
  Fingerprint,
  RefreshCw,
  Info,
  ChevronDown,
  ChevronUp,
  Network,
  Sparkles,
  Cpu,
  Calendar,
  Clock,
  CheckSquare,
  Maximize2,
  Database,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import * as d3 from "d3";
import { wsOrigin } from "@/lib/config";

export default function FraudDnaPage() {
  const [campaigns, setCampaigns] = useState<CampaignsResponse | null>(null);
  const [graphData, setGraphData] = useState<GraphResponse | null>(null);
  const [summary, setSummary] = useState<ThreatSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isReclustering, setIsReclustering] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [expandedCampaignId, setExpandedCampaignId] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<any | null>(null);
  const [activeTab, setActiveTab] = useState<"fingerprints" | "campaigns" | "graph">("fingerprints");
  const [isSeeding, setIsSeeding] = useState(false);
  const [liveEventCount, setLiveEventCount] = useState(0);

  // D3 force graph zoom & simulation state helpers
  const svgRef = useRef<SVGSVGElement | null>(null);
  const zoomBehaviorRef = useRef<any>(null);
  const [hoveredNode, setHoveredNode] = useState<any | null>(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });

  const [aiCampaigns, setAiCampaigns] = useState<Record<string, CampaignAIResult>>({});
  const [loadingAiCampaigns, setLoadingAiCampaigns] = useState<Record<string, boolean>>({});

  const fetchCampaignAI = async (campaign: FraudCampaignDetail) => {
    if (aiCampaigns[campaign.campaign_id] || loadingAiCampaigns[campaign.campaign_id]) return;

    setLoadingAiCampaigns((prev) => ({ ...prev, [campaign.campaign_id]: true }));
    try {
      const res = await aiApi.analyzeCampaign(campaign);
      setAiCampaigns((prev) => ({ ...prev, [campaign.campaign_id]: res }));
    } catch (err) {
      console.error("AI campaign metrics load error:", err);
    } finally {
      setLoadingAiCampaigns((prev) => ({ ...prev, [campaign.campaign_id]: false }));
    }
  };

  const toggleCampaignExpand = (camp: FraudCampaignDetail) => {
    const isExpanding = expandedCampaignId !== camp.campaign_id;
    setExpandedCampaignId(isExpanding ? camp.campaign_id : null);
    if (isExpanding) {
      fetchCampaignAI(camp);
    }
  };

  const fetchDnaData = async (reclustering = false) => {
    if (reclustering) setIsReclustering(true);
    else setIsLoading(true);
    setLoadError(null);

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
    } catch (err: any) {
      console.error("Error loading Fraud DNA cluster metrics:", err);
      setLoadError(err?.message || "Could not reach the Fraud DNA backend.");
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

  // Replace the on-disk store with the curated sample set so the page
  // has a populated graph even before any real scans have been run.
  const handleSeed = async () => {
    setIsSeeding(true);
    try {
      await fraudDnaApi.seedSampleEvents();
      // Re-fetch all derived views (campaigns + graph + summary) so the
      // UI reflects the freshly seeded store without a manual reload.
      await fetchDnaData(true);
    } catch (err: any) {
      console.error("Seed failed:", err);
      setLoadError(err?.message || "Failed to load sample data.");
    } finally {
      setIsSeeding(false);
    }
  };

  // Subscribe to the live threat stream. The /ws/threats WebSocket
  // re-emits past events on connect, so a fresh client sees the existing
  // store immediately. We only count new events to keep the page quiet.
  useEffect(() => {
    if (typeof window === "undefined") return;
    const origin = wsOrigin();
    if (!origin) return;

    // The backend expects the same auth header the proxy uses in
    // production. The browser cannot set a custom header on a
    // WebSocket, so we only connect when the backend is in dev mode
    // (no LUMINT_API_KEY configured) — otherwise the handshake would
    // be rejected. The HTTP polling via /api/fraud-dna/* still works
    // in production because it goes through the same-origin proxy.
    let ws: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let closed = false;

    const connect = () => {
      try {
        ws = new WebSocket(`${origin}/ws/threats`);
      } catch (e) {
        return;
      }
      ws.onopen = () => {
        // No-op: server replays past events; we just count new arrivals.
      };
      ws.onmessage = () => {
        setLiveEventCount((c) => c + 1);
      };
      ws.onerror = () => {
        // Silent: the page already works via HTTP polling.
      };
      ws.onclose = () => {
        if (closed) return;
        // Auto-reconnect after 5s if the component is still mounted.
        reconnectTimer = setTimeout(connect, 5000);
      };
    };

    connect();
    return () => {
      closed = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      if (ws && ws.readyState <= 1) ws.close();
    };
  }, []);

  // After a burst of live events, refresh the derived views so the
  // graph + campaign cards pick up the new fingerprints. We debounce
  // to avoid hammering the API when several events arrive in quick
  // succession.
  useEffect(() => {
    if (liveEventCount === 0) return;
    const id = setTimeout(() => {
      // Re-pull campaigns+graph+summary in the background (no
      // loading spinner — the existing data stays visible while we
      // swap in the updated values).
      Promise.all([
        fraudDnaApi.getCampaigns(),
        fraudDnaApi.getGraph(),
        fraudDnaApi.getThreatSummary(),
      ])
        .then(([c, g, s]) => {
          if (c) setCampaigns(c);
          if (g) setGraphData(g);
          if (s) setSummary(s);
        })
        .catch(() => {
          /* ignore — page keeps the previous data */
        });
    }, 1500);
    return () => clearTimeout(id);
  }, [liveEventCount]);

  const getThreatVariant = (level: string): any => {
    switch (level?.toUpperCase()) {
      case "CRITICAL":
        return "critical";
      case "HIGH":
      case "ELEVATED":
        return "high";
      case "SUSPICIOUS":
      case "WARNING":
      case "WARN":
        return "warn";
      default:
        return "safe";
    }
  };

  // Compile individual fingerprints/events list
  const fingerprintsList = useMemo(() => {
    if (!campaigns || !campaigns.campaigns) return [];
    const list: any[] = [];
    campaigns.campaigns.forEach((camp) => {
      camp.events.forEach((evt) => {
        list.push({
          ...evt,
          campaign_id: camp.campaign_id,
          campaign_risk: camp.risk_level,
          common_indicators: camp.common_indicators
        });
      });
    });
    return list.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
  }, [campaigns]);

  // Expanded fingerprint row state
  const [expandedFingerprintId, setExpandedFingerprintId] = useState<string | null>(null);

  // Graph force simulation setup (D3)
  useEffect(() => {
    if (!graphData || !svgRef.current || activeTab !== "graph") return;

    const svgElement = svgRef.current;
    const parent = svgElement.parentElement;
    const width = parent?.clientWidth || 600;
    const height = parent?.clientHeight || 450;

    // Deep copy data for D3 mutation
    const nodes: any[] = graphData.nodes.map((n) => ({ ...n }));
    const edges: any[] = graphData.edges.map((e) => ({ ...e }));

    // Clear svg elements
    const svg: any = d3.select(svgElement);
    svg.selectAll("*").remove();

    // Create main outer group for zoom/pan
    const g = svg.append("g").attr("class", "graph-container-inner");

    // Initialize Zoom
    const zoom: any = d3
      .zoom()
      .scaleExtent([0.15, 3])
      .on("zoom", (event) => {
        g.attr("transform", event.transform);
      });
    
    svg.call(zoom);
    zoomBehaviorRef.current = { zoom, svg };

    // Setup force simulation
    const simulation = d3
      .forceSimulation(nodes)
      .force(
        "link",
        d3
          .forceLink(edges)
          .id((d: any) => d.id)
          .distance(110)
      )
      .force("charge", d3.forceManyBody().strength(-280))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force(
        "collide",
        d3.forceCollide().radius((d: any) => (d.type === "ACTOR" ? 38 : 22))
      );

    // Draw links/edges
    const link = g
      .append("g")
      .attr("class", "links")
      .selectAll("line")
      .data(edges)
      .enter()
      .append("line")
      .attr("stroke", "var(--border-focus)")
      .attr("stroke-opacity", 0.4)
      .attr("stroke-width", (d: any) => Math.max(1.5, (d.weight || 0.5) * 4.5))
      .attr("stroke-dasharray", (d: any) => (d.type === "ACTOR" ? "4,4" : "none"))
      .attr("cursor", "pointer");

    // Draw node groups
    const node = g
      .append("g")
      .attr("class", "nodes")
      .selectAll("g")
      .data(nodes)
      .enter()
      .append("g")
      .attr("class", "node-group")
      .attr("cursor", "pointer")
      .call(
        d3
          .drag<SVGGElement, any>()
          .on("start", dragstarted)
          .on("drag", dragged)
          .on("end", dragended)
      );

    // Node circles styling
    node
      .append("circle")
      .attr("r", (d: any) => (d.type === "ACTOR" ? 22 : 12))
      .attr("fill", (d: any) => {
        if (d.type === "ACTOR") return "var(--brand-muted)";
        const variant = getThreatVariant(d.risk_level);
        if (variant === "critical") return "rgba(239, 68, 68, 0.2)";
        if (variant === "high") return "rgba(249, 115, 22, 0.2)";
        if (variant === "warn") return "rgba(234, 179, 8, 0.2)";
        return "rgba(34, 197, 94, 0.2)";
      })
      .attr("stroke", (d: any) => {
        if (d.type === "ACTOR") return "var(--brand)";
        const variant = getThreatVariant(d.risk_level);
        if (variant === "critical") return "var(--critical)";
        if (variant === "high") return "var(--high)";
        if (variant === "warn") return "var(--warn)";
        return "var(--safe)";
      })
      .attr("stroke-width", (d: any) => (d.type === "ACTOR" ? 2.5 : 2));

    // Inner center dots for Event nodes
    node
      .filter((d: any) => d.type !== "ACTOR")
      .append("circle")
      .attr("r", 4.5)
      .attr("fill", (d: any) => {
        const variant = getThreatVariant(d.risk_level);
        if (variant === "critical") return "var(--critical)";
        if (variant === "high") return "var(--high)";
        if (variant === "warn") return "var(--warn)";
        return "var(--safe)";
      });

    // Add icon letter indicators inside Actor nodes
    node
      .filter((d: any) => d.type === "ACTOR")
      .append("text")
      .attr("text-anchor", "middle")
      .attr("dy", ".3em")
      .attr("fill", "var(--brand)")
      .attr("font-size", "11px")
      .attr("font-family", "var(--font-mono), monospace")
      .attr("font-weight", "bold")
      .text("ACT");

    // Dynamic hover & click events on nodes
    node
      .on("mouseover", (event: any, d: any) => {
        setHoveredNode(d);
        const rect = svgElement.getBoundingClientRect();
        setTooltipPos({
          x: event.clientX - rect.left + 15,
          y: event.clientY - rect.top + 15
        });
      })
      .on("mousemove", (event: any) => {
        const rect = svgElement.getBoundingClientRect();
        setTooltipPos({
          x: event.clientX - rect.left + 15,
          y: event.clientY - rect.top + 15
        });
      })
      .on("mouseout", () => {
        setHoveredNode(null);
      })
      .on("click", (event: any, d: any) => {
        event.stopPropagation();
        setSelectedNode(d);

        // Highlight selected node + connected nodes & links
        const connectedNodeIds = new Set<string>([d.id]);
        edges.forEach((edge: any) => {
          if (edge.source.id === d.id) connectedNodeIds.add(edge.target.id);
          if (edge.target.id === d.id) connectedNodeIds.add(edge.source.id);
        });

        node.style("opacity", (n: any) => (connectedNodeIds.has(n.id) ? 1.0 : 0.18));
        link.style("opacity", (l: any) =>
          (l.source.id === d.id || l.target.id === d.id) ? 1.0 : 0.08
        );
      });

    // Click canvas to clear filter selection
    svg.on("click", () => {
      setSelectedNode(null);
      node.style("opacity", 1.0);
      link.style("opacity", 0.4);
    });

    simulation.on("tick", () => {
      link
        .attr("x1", (d: any) => d.source.x)
        .attr("y1", (d: any) => d.source.y)
        .attr("x2", (d: any) => d.target.x)
        .attr("y2", (d: any) => d.target.y);

      node.attr("transform", (d: any) => `translate(${d.x},${d.y})`);
    });

    function dragstarted(event: any, d: any) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(event: any, d: any) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragended(event: any, d: any) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }

    return () => {
      simulation.stop();
    };
  }, [graphData, activeTab]);

  // Zoom control buttons handlers
  const handleResetZoom = () => {
    if (zoomBehaviorRef.current) {
      const { zoom, svg } = zoomBehaviorRef.current;
      svg.transition().duration(500).call(zoom.transform, d3.zoomIdentity);
    }
  };

  const handleFitZoom = () => {
    if (zoomBehaviorRef.current && svgRef.current) {
      const { zoom, svg } = zoomBehaviorRef.current;
      const g = svg.select(".graph-container-inner");
      if (g.empty()) return;
      const bounds = (g.node() as SVGGraphicsElement).getBBox();
      const parent = svgRef.current.parentElement;
      const width = parent?.clientWidth || 600;
      const height = parent?.clientHeight || 450;

      const dx = bounds.width;
      const dy = bounds.height;
      if (dx === 0 || dy === 0) return;

      const x = bounds.x + dx / 2;
      const y = bounds.y + dy / 2;
      const scale = Math.max(0.25, Math.min(1.8, 0.85 / Math.max(dx / width, dy / height)));
      const translate = [width / 2 - scale * x, height / 2 - scale * y];

      svg
        .transition()
        .duration(600)
        .call(zoom.transform, d3.zoomIdentity.translate(translate[0], translate[1]).scale(scale));
    }
  };

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[var(--border)] pb-5">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="h-9 w-9 rounded-lg bg-[var(--brand-muted)] text-[var(--brand)] flex items-center justify-center shadow-sm">
              <Network className="h-5 w-5" />
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-[var(--text-1)]">
              Fraud DNA Cluster Analysis
            </h1>
          </div>
          <p className="text-sm text-[var(--text-3)] font-medium mt-1 pl-11">
            Correlate files, domains, exif dates, and digital hashes into high-confidence campaign footprints.
          </p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={handleSeed}
            disabled={isSeeding}
            className="inline-flex items-center justify-center gap-1.5 rounded-xl border border-[var(--border)] bg-[var(--surface)] hover:bg-[var(--surface-2)] text-xs font-bold text-[var(--text-1)] px-4 py-2.5 shadow-sm transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 disabled:pointer-events-none cursor-pointer"
            title="Replace the store with 8 sample events so the graph is populated"
          >
            <Database
              className={`h-3.5 w-3.5 ${
                isSeeding ? "animate-pulse text-[var(--brand)]" : "text-[var(--text-3)]"
              }`}
            />
            {isSeeding ? "Seeding..." : "Load sample data"}
          </button>
          <button
            onClick={handleRecluster}
            disabled={isReclustering || isLoading || !campaigns}
            className="inline-flex items-center justify-center gap-1.5 rounded-xl border border-[var(--border)] bg-[var(--surface)] hover:bg-[var(--surface-2)] text-xs font-bold text-[var(--text-1)] px-4 py-2.5 shadow-sm transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 disabled:pointer-events-none cursor-pointer"
            title={!campaigns ? "Backend not connected" : "Re-run clustering"}
          >
            <RefreshCw
              className={`h-3.5 w-3.5 ${
                isReclustering ? "animate-spin text-[var(--brand)]" : "text-[var(--text-3)]"
              }`}
            />
            {isReclustering ? "Re-clustering..." : "Re-cluster Sandbox"}
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="min-h-[400px] flex flex-col items-center justify-center">
          <div className="h-10 w-10 border-4 border-[var(--border-2)] border-t-[var(--brand)] animate-spin rounded-full mb-3" />
          <p className="text-sm text-[var(--text-3)] font-semibold">Generating campaign graph nodes...</p>
        </div>
      ) : loadError ? (
        /* Backend reachable but errored (or proxy 503'd). Show the real
           reason so the operator can fix LUMINT_API_KEY / Render URL. */
        <div className="space-y-4">
          <EmptyStateWithCTA
            icon="network"
            title="Could not load Fraud DNA"
            description={loadError}
            technicalDetails="Check the LUMINT_API_KEY env var on Vercel, or visit /settings to override the backend URL."
            primaryAction={{ label: "Retry", href: "#" }}
            secondaryAction={{ label: "Open settings", href: "/settings" }}
          />

          {/* "How it works" — only visible in demo mode so users understand
              what the page is meant to do. */}
          <Card className="p-5">
            <div className="flex items-center gap-2 mb-3">
              <Sparkles className="h-4 w-4 text-[var(--brand)]" />
              <h4 className="text-xs font-bold uppercase tracking-wider text-[var(--text-1)]">
                How Fraud DNA works
              </h4>
            </div>
            <ol className="space-y-2.5 text-xs text-[var(--text-2)] font-semibold">
              {[
                { src: "PhishShield", desc: "extracts domain hashes from scanned URLs" },
                { src: "DocShield",   desc: "extracts file hashes from uploaded documents" },
                { src: "UPI Shield",  desc: "extracts UPI handle hashes from screenshots" },
                { src: "DBSCAN",      desc: "clusters related threats using density-based grouping" },
                { src: "Force graph", desc: "visualizes relationships between domains, files, and campaigns" },
              ].map((step, i) => (
                <li key={i} className="flex items-start gap-3">
                  <span className="h-5 w-5 rounded-full bg-[var(--brand-muted)] text-[var(--brand)] flex items-center justify-center text-[10px] font-bold shrink-0">
                    {i + 1}
                  </span>
                  <span>
                    <span className="text-[var(--text-1)] font-bold">{step.src}</span>{" "}
                    {step.desc}.
                  </span>
                </li>
              ))}
            </ol>
          </Card>
        </div>
      ) : (
        <>
          {/* Top Threat summary panel */}
          {summary && (
            <Card variant="elevated" className="p-6 border-l-4 border-l-[var(--high)]">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold text-[var(--text-3)] uppercase tracking-widest font-semibold">
                      Threat Intelligence Sandbox Summary
                    </span>
                    <Badge variant={getThreatVariant(summary.threat_level)} dot size="sm">
                      {summary.threat_level}
                    </Badge>
                  </div>
                  <p className="text-sm text-[var(--text-2)] font-semibold leading-relaxed mt-2.5">
                    {summary.summary}
                  </p>
                </div>

                <div className="flex gap-4 md:border-l border-[var(--border)] md:pl-6 shrink-0 font-semibold text-xs text-[var(--text-3)]">
                  <div className="text-center">
                    <span className="block font-mono text-xl font-bold text-[var(--critical)]">
                      {summary.high_risk_count}
                    </span>
                    <span>High Risk</span>
                  </div>
                  <div className="text-center border-l border-[var(--border)] pl-4">
                    <span className="block font-mono text-xl font-bold text-[var(--warn)]">
                      {summary.suspicious_count}
                    </span>
                    <span>Suspicious</span>
                  </div>
                </div>
              </div>
            </Card>
          )}

          {/* Navigation Tab Bar */}
          <div className="flex border-b border-[var(--border)] gap-6">
            {(["fingerprints", "campaigns", "graph"] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => {
                  setActiveTab(tab);
                  setSelectedNode(null);
                }}
                className={`pb-3 text-xs font-bold uppercase tracking-wider relative cursor-pointer ${
                  activeTab === tab
                    ? "text-[var(--brand)]"
                    : "text-[var(--text-3)] hover:text-[var(--text-2)]"
                }`}
              >
                {tab === "fingerprints"
                  ? "Fingerprints Archive"
                  : tab === "campaigns"
                  ? "Identified Campaigns"
                  : "DNA Network Graph"}
                {activeTab === tab && (
                  <motion.div
                    layoutId="fraudDnaTabUnderline"
                    className="absolute bottom-0 left-0 right-0 h-[2px] bg-[var(--brand)]"
                    transition={{ type: "spring", stiffness: 380, damping: 30 }}
                  />
                )}
              </button>
            ))}
          </div>

          {/* Tab description — short copy that explains what each view contains. */}
          <p className="text-xs text-[var(--text-3)] font-semibold -mt-2" aria-live="polite">
            {activeTab === "fingerprints" &&
              "Individual forensic records matching visual anomalies or spoofed headers."}
            {activeTab === "campaigns" &&
              "Threat actor groups and patterns correlated from multiple events."}
            {activeTab === "graph" &&
              "Visual force-directed graph showing relationships between domains, files, and campaigns."}
          </p>

          {/* Tab Content Areas */}
          <AnimatePresence mode="wait">
            {activeTab === "fingerprints" && (
              <motion.div
                key="fingerprints-tab"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="space-y-4"
              >
                <Card variant="default" className="p-6">
                  <div className="flex justify-between items-center mb-6">
                    <div>
                      <h3 className="text-sm font-bold text-[var(--text-1)]">Forensic Logs</h3>
                      <p className="text-xs text-[var(--text-3)] font-semibold mt-0.5">
                        Individual forensic records matching visual anomalies or spoofed headers.
                      </p>
                    </div>
                    <Badge variant="neutral" size="sm">
                      {fingerprintsList.length} total events
                    </Badge>
                  </div>

                  <div className="space-y-3">
                    {fingerprintsList.map((evt) => {
                      const isExpanded = expandedFingerprintId === evt.event_id;
                      return (
                        <div
                          key={evt.event_id}
                          className="border border-[var(--border)] rounded-xl bg-[var(--surface-2)] overflow-hidden"
                        >
                          <div
                            onClick={() =>
                              setExpandedFingerprintId(isExpanded ? null : evt.event_id)
                            }
                            className="flex flex-col sm:flex-row sm:items-center justify-between p-4 gap-3 cursor-pointer hover:bg-[var(--surface-3)]/60 transition-colors"
                          >
                            <div className="flex items-center gap-3">
                              <span className="h-7 w-7 rounded-lg bg-[var(--surface-3)] text-[var(--text-2)] flex items-center justify-center">
                                <Fingerprint className="h-4 w-4" />
                              </span>
                              <div>
                                <span className="font-mono text-xs font-bold text-[var(--text-1)] select-all">
                                  {evt.event_id}
                                </span>
                                <span className="text-xs text-[var(--text-3)] font-semibold ml-2">
                                  {evt.label}
                                </span>
                              </div>
                            </div>
                            <div className="flex items-center gap-4">
                              <Badge variant={evt.source_type === "DOCUMENT" ? "neutral" : "ai"} size="sm">
                                {evt.source_type}
                              </Badge>
                              <div className="flex items-center gap-2">
                                <span className="font-mono text-xs font-bold text-[var(--text-2)]">
                                  Score: {evt.risk_score}
                                </span>
                                <Badge variant={getThreatVariant(evt.risk_level)} size="sm">
                                  {evt.risk_level}
                                </Badge>
                              </div>
                              {isExpanded ? (
                                <ChevronUp className="h-4 w-4 text-[var(--text-3)]" />
                              ) : (
                                <ChevronDown className="h-4 w-4 text-[var(--text-3)]" />
                              )}
                            </div>
                          </div>

                          <AnimatePresence>
                            {isExpanded && (
                              <motion.div
                                initial={{ height: 0 }}
                                animate={{ height: "auto" }}
                                exit={{ height: 0 }}
                                className="border-t border-[var(--border)] bg-[var(--surface)] p-4 text-xs font-semibold text-[var(--text-2)] space-y-3"
                              >
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                  <DataPoint
                                    label="Document Entity ID"
                                    value={evt.doc_id || "N/A"}
                                    mono
                                    copyable
                                  />
                                  <DataPoint
                                    label="Classification Hint"
                                    value={evt.document_type_hint || "N/A"}
                                    mono
                                  />
                                  <DataPoint
                                    label="Associated Campaign"
                                    value={evt.campaign_id}
                                    mono
                                  />
                                </div>
                                <div>
                                  <span className="t-label block mb-1 text-[var(--text-3)]">
                                    Triggered Campaign Policies
                                  </span>
                                  <div className="flex flex-wrap gap-1.5 pt-1">
                                    {evt.common_indicators.map((ind: string, idx: number) => (
                                      <span
                                        key={idx}
                                        className="bg-[var(--high-bg)] text-[var(--high)] border border-[var(--high-border)] text-[10px] px-2 py-0.5 rounded font-mono font-medium"
                                      >
                                        {ind}
                                      </span>
                                    ))}
                                  </div>
                                </div>
                                <div className="flex justify-between items-center pt-2 border-t border-[var(--border)] text-[10px] text-[var(--text-3)]">
                                  <span className="flex items-center gap-1">
                                    <Clock className="h-3.5 w-3.5" />
                                    Seen: {new Date(evt.created_at).toLocaleString()}
                                  </span>
                                  <a
                                    href={evt.source_type === "DOCUMENT" ? "/docshield" : "/phishshield"}
                                    className="text-[var(--brand)] hover:underline flex items-center gap-1 font-bold"
                                  >
                                    Inspect Source Log &rarr;
                                  </a>
                                </div>
                              </motion.div>
                            )}
                          </AnimatePresence>
                        </div>
                      );
                    })}
                  </div>
                </Card>
              </motion.div>
            )}

            {activeTab === "campaigns" && (
              <motion.div
                key="campaigns-tab"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="space-y-6"
              >
                {campaigns?.campaigns.map((camp) => {
                  const isExpanded = expandedCampaignId === camp.campaign_id;
                  return (
                    <Card key={camp.campaign_id} variant="default" className="p-6 space-y-4">
                      {/* Campaign Header */}
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[var(--border)] pb-4">
                        <div className="space-y-1">
                          <span className="font-mono text-sm font-bold text-[var(--brand)] block">
                            CAMPAIGN: {camp.campaign_id.toUpperCase()}
                          </span>
                          <div className="flex flex-wrap items-center gap-4 text-xs font-semibold text-[var(--text-3)]">
                            <span className="flex items-center gap-1">
                              <Maximize2 className="h-3.5 w-3.5" />
                              {camp.event_count} associated events
                            </span>
                            <span className="flex items-center gap-1">
                              <Calendar className="h-3.5 w-3.5" />
                              Seen: {new Date(camp.first_seen).toLocaleDateString()} &ndash;{" "}
                              {new Date(camp.last_seen).toLocaleDateString()}
                            </span>
                          </div>
                        </div>

                        <div className="flex items-center gap-3">
                          <div className="text-right">
                            <span className="text-[10px] text-[var(--text-3)] block font-semibold uppercase tracking-wider">
                              Avg Risk Score
                            </span>
                            <span className="font-mono text-sm font-bold text-[var(--text-1)]">
                              {camp.avg_risk_score.toFixed(1)}
                            </span>
                          </div>
                          <Badge variant={getThreatVariant(camp.risk_level)} size="md">
                            {camp.risk_level}
                          </Badge>
                        </div>
                      </div>

                      {/* Keywords & Indicators */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs font-semibold">
                        <div>
                          <span className="t-label block mb-2 text-[var(--text-3)]">Common Keywords</span>
                          <div className="flex flex-wrap gap-1.5">
                            {camp.common_keywords.map((kw, i) => (
                              <span
                                key={i}
                                className="bg-[var(--surface-3)] border border-[var(--border-2)] text-[10px] text-[var(--text-2)] px-2 py-0.5 rounded-md"
                              >
                                {kw}
                              </span>
                            ))}
                          </div>
                        </div>
                        <div>
                          <span className="t-label block mb-2 text-[var(--text-3)]">Common Indicators</span>
                          <div className="flex flex-wrap gap-1.5">
                            {camp.common_indicators.map((ind, i) => (
                              <span
                                key={i}
                                className="bg-[var(--high-bg)] text-[var(--high)] border border-[var(--high-border)] text-[9px] px-2 py-0.5 rounded font-mono font-medium"
                              >
                                {ind}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>

                      {/* Table of Associated Scans */}
                      <div className="pt-2">
                        <span className="t-label block mb-2 text-[var(--text-3)]">Associated Scans</span>
                        <div className="border border-[var(--border)] rounded-xl overflow-hidden bg-[var(--surface-2)]">
                          <table className="w-full text-left border-collapse text-xs font-semibold">
                            <thead>
                              <tr className="border-b border-[var(--border)] bg-[var(--surface-3)]/60 text-[var(--text-3)]">
                                <th className="p-3">Event ID</th>
                                <th className="p-3">Entity Label</th>
                                <th className="p-3">Type</th>
                                <th className="p-3 text-right">Risk Score</th>
                              </tr>
                            </thead>
                            <tbody>
                              {camp.events.map((evt) => (
                                <tr key={evt.event_id} className="border-b border-[var(--border)]/40 last:border-0 hover:bg-[var(--surface-3)]/40">
                                  <td className="p-3 font-mono text-[var(--text-1)] select-all">{evt.event_id}</td>
                                  <td className="p-3 font-mono text-[var(--text-2)]">{evt.label}</td>
                                  <td className="p-3">
                                    <Badge variant="neutral" size="sm">
                                      {evt.source_type}
                                    </Badge>
                                  </td>
                                  <td className="p-3 text-right font-mono font-bold text-[var(--text-1)]">
                                    {evt.risk_score}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>

                      {/* AI Intelligence Toggle */}
                      <div className="pt-4 border-t border-[var(--border)]">
                        <button
                          onClick={() => toggleCampaignExpand(camp)}
                          className="flex items-center gap-1.5 text-xs font-bold text-[var(--brand)] hover:underline cursor-pointer"
                        >
                          {isExpanded ? (
                            <>
                              <ChevronUp className="h-4 w-4" /> Hide AI Campaign Intel
                            </>
                          ) : (
                            <>
                              <Sparkles className="h-4 w-4" /> Analyze with AI Campaign Oracle
                            </>
                          )}
                        </button>

                        <AnimatePresence>
                          {isExpanded && (
                            <motion.div
                              initial={{ opacity: 0, height: 0 }}
                              animate={{ opacity: 1, height: "auto" }}
                              exit={{ opacity: 0, height: 0 }}
                              className="mt-4"
                            >
                              {loadingAiCampaigns[camp.campaign_id] ? (
                                <div className="py-6 flex items-center justify-center gap-2 text-xs font-semibold text-[var(--text-3)] bg-[var(--ai-muted)] rounded-xl border border-dashed border-[var(--ai-border)]">
                                  <div className="h-4 w-4 border-2 border-[var(--ai-border)] border-t-[var(--ai)] animate-spin rounded-full" />
                                  <span>Generating Operation Intelligence Brief...</span>
                                </div>
                              ) : aiCampaigns[camp.campaign_id] ? (
                                <Card variant="ai" className="p-5 space-y-4">
                                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[var(--ai-border)] pb-3">
                                    <div>
                                      <span className="text-[9px] font-bold text-[var(--ai-text)] uppercase tracking-wider block">
                                        Operation
                                      </span>
                                      <h4 className="text-lg text-[var(--text-1)]" style={{ fontFamily: "var(--font-display), serif" }}>
                                        {aiCampaigns[camp.campaign_id].campaign_name}
                                      </h4>
                                    </div>

                                    <div className="flex flex-wrap items-center gap-4 text-xs font-semibold">
                                      <div>
                                        <span className="text-[9px] font-bold text-[var(--text-3)] uppercase block">
                                          Threat Scale
                                        </span>
                                        <span className="text-xs font-mono font-bold text-[var(--text-1)]">
                                          {aiCampaigns[camp.campaign_id].estimated_scale}
                                        </span>
                                      </div>
                                      <div>
                                        <span className="text-[9px] font-bold text-[var(--text-3)] uppercase block">
                                          AI Threat
                                        </span>
                                        <Badge
                                          variant={getThreatVariant(
                                            aiCampaigns[camp.campaign_id].threat_level
                                          )}
                                          size="sm"
                                        >
                                          {aiCampaigns[camp.campaign_id].threat_level}
                                        </Badge>
                                      </div>
                                    </div>
                                  </div>

                                  <div className="grid grid-cols-1 md:grid-cols-2 gap-5 text-xs font-semibold">
                                    <div className="space-y-3.5">
                                      <div>
                                        <span className="text-[9px] font-bold text-[var(--text-3)] uppercase block mb-1">
                                          Analyst Intelligence Brief
                                        </span>
                                        <p className="text-[var(--text-2)] leading-relaxed bg-[var(--surface)]/45 p-3 rounded-lg border border-[var(--border)]/30 font-sans font-medium">
                                          {aiCampaigns[camp.campaign_id].analyst_brief}
                                        </p>
                                      </div>
                                      <div>
                                        <span className="text-[9px] font-bold text-[var(--text-3)] uppercase block mb-1">
                                          Pattern Summary
                                        </span>
                                        <p className="text-[var(--text-2)] leading-relaxed font-sans font-medium">
                                          {aiCampaigns[camp.campaign_id].pattern_summary}
                                        </p>
                                      </div>
                                    </div>

                                    <div className="space-y-4 md:border-l border-[var(--border)] md:pl-5">
                                      <div>
                                        <span className="text-[9px] font-bold text-[var(--text-3)] uppercase block mb-1.5">
                                          MITRE ATT&CK TTP Mapping
                                        </span>
                                        <div className="flex flex-wrap gap-1">
                                          {aiCampaigns[camp.campaign_id].ttps.map((ttp, idx) => (
                                            <span
                                              key={idx}
                                              className="bg-[var(--surface)] border border-[var(--border)] text-[10px] text-[var(--text-1)] px-2 py-0.5 rounded font-mono font-bold"
                                            >
                                              {ttp}
                                            </span>
                                          ))}
                                        </div>
                                      </div>
                                      <div>
                                        <span className="text-[9px] font-bold text-[var(--text-3)] uppercase block mb-1.5">
                                          Recommended Mitigations
                                        </span>
                                        <ul className="space-y-1.5">
                                          {aiCampaigns[camp.campaign_id].recommended_actions.map(
                                            (act, idx) => (
                                              <li
                                                key={idx}
                                                className="text-[var(--text-2)] font-sans font-medium flex items-start gap-1.5"
                                              >
                                                <CheckSquare className="h-3.5 w-3.5 text-[var(--ai)] mt-0.5 shrink-0" />
                                                <span>{act}</span>
                                              </li>
                                            )
                                          )}
                                        </ul>
                                      </div>
                                    </div>
                                  </div>

                                  {/* Info Footer */}
                                  <div className="flex items-center justify-between border-t border-[var(--ai-border)] pt-3 text-[9px] text-[var(--text-3)] font-semibold">
                                    <div className="flex items-center gap-1">
                                      <Cpu className="h-3.5 w-3.5 text-[var(--ai)]" />
                                      <span>
                                        Model:{" "}
                                        <span className="font-mono font-bold text-[var(--text-1)]">
                                          {aiCampaigns[camp.campaign_id].model_used}
                                        </span>
                                      </span>
                                    </div>
                                    {aiCampaigns[camp.campaign_id].latency_ms > 0 && (
                                      <span>
                                        Latency:{" "}
                                        <span className="font-mono font-bold text-[var(--text-1)]">
                                          {aiCampaigns[camp.campaign_id].latency_ms}ms
                                        </span>
                                      </span>
                                    )}
                                  </div>
                                </Card>
                              ) : (
                                <div className="p-4 bg-[var(--surface-3)] text-xs text-[var(--text-3)] rounded-xl italic">
                                  No AI results found.
                                </div>
                              )}
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </div>
                    </Card>
                  );
                })}
              </motion.div>
            )}

            {activeTab === "graph" && (
              <motion.div
                key="graph-tab"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="grid grid-cols-1 lg:grid-cols-10 gap-8 items-start"
              >
                {/* SVG Visual Canvas Area - 7 columns */}
                <div className="lg:col-span-7 space-y-4">
                  <Card variant="default" className="p-4 flex flex-col h-[520px] relative">
                    <div className="flex justify-between items-center mb-4">
                      <div>
                        <h3 className="text-sm font-bold text-[var(--text-1)]">Connected Threat Network</h3>
                        <p className="text-xs text-[var(--text-3)] font-semibold mt-0.5">
                          Drag nodes to reposition. Hover for summary, click to filter relationships.
                        </p>
                      </div>

                      {/* Zoom controls */}
                      <div className="flex items-center gap-2">
                        <button
                          onClick={handleFitZoom}
                          className="px-2.5 py-1.5 rounded-lg border border-[var(--border)] bg-[var(--surface-2)] text-[var(--text-2)] hover:bg-[var(--border-2)] text-[10px] font-bold cursor-pointer transition-all flex items-center gap-1 select-none"
                        >
                          <Maximize2 className="h-3 w-3" />
                          Fit Graph
                        </button>
                        <button
                          onClick={handleResetZoom}
                          className="px-2.5 py-1.5 rounded-lg border border-[var(--border)] bg-[var(--surface-2)] text-[var(--text-2)] hover:bg-[var(--border-2)] text-[10px] font-bold cursor-pointer transition-all flex items-center gap-1 select-none"
                        >
                          <RefreshCw className="h-3 w-3" />
                          Reset View
                        </button>
                      </div>
                    </div>

                    {/* Canvas frame */}
                    <div className="flex-1 bg-[var(--surface-2)] rounded-xl border border-[var(--border)] relative overflow-hidden">
                      {/* Grid overlay */}
                      <div className="absolute inset-0 bg-[radial-gradient(var(--border-2)_1.5px,transparent_1.5px)] [background-size:20px_20px] opacity-40 pointer-events-none" />

                      <svg ref={svgRef} className="w-full h-full block" />

                      {/* Floating hover tooltip card */}
                      {hoveredNode && (
                        <div
                          style={{
                            position: "absolute",
                            left: `${tooltipPos.x}px`,
                            top: `${tooltipPos.y}px`
                          }}
                          className="w-[160px] pointer-events-none z-50 bg-[var(--surface)] border border-[var(--border)] rounded-lg shadow-[var(--shadow-3)] p-3 space-y-1.5 text-[10px] font-semibold text-[var(--text-2)]"
                        >
                          <div className="flex justify-between items-center gap-2">
                            <span className="font-mono font-bold text-[var(--text-1)] truncate block flex-1">
                              {hoveredNode.label}
                            </span>
                            <Badge variant={hoveredNode.type === "ACTOR" ? "neutral" : "ai"} size="sm">
                              {hoveredNode.type}
                            </Badge>
                          </div>
                          {hoveredNode.type !== "ACTOR" && (
                            <div className="flex items-center gap-1">
                              <span>Risk Score:</span>
                              <span className="font-mono font-bold text-[var(--text-1)]">
                                {hoveredNode.risk_score}
                              </span>
                            </div>
                          )}
                          <div>
                            <span className="text-[var(--text-4)] text-[9px] uppercase tracking-wider block font-bold">
                              Node ID
                            </span>
                            <span className="font-mono text-[var(--text-3)] truncate block">
                              {hoveredNode.id}
                            </span>
                          </div>
                        </div>
                      )}

                      {/* Legend bottom left */}
                      <div className="absolute bottom-3 left-3 bg-[var(--surface)] border border-[var(--border)] rounded-lg p-3 space-y-2 text-[10px] font-semibold text-[var(--text-2)] shadow-md pointer-events-none select-none">
                        <div className="font-bold text-[var(--text-3)] uppercase tracking-wider">
                          Graph Legend
                        </div>
                        <div className="space-y-1.5">
                          <div className="flex items-center gap-2">
                            <span className="h-3 w-3 rounded-full border-[1.5px] border-[var(--brand)] bg-[var(--brand-muted)]" />
                            <span>Actor Node</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="h-3 w-3 rounded-full bg-[var(--critical)]/25 border-[1.5px] border-[var(--critical)]" />
                            <span>Critical Threat</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="h-3 w-3 rounded-full bg-[var(--high)]/25 border-[1.5px] border-[var(--high)]" />
                            <span>High Threat</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="h-3 w-3 rounded-full bg-[var(--warn)]/25 border-[1.5px] border-[var(--warn)]" />
                            <span>Suspicious Target</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="h-3 w-3 rounded-full bg-[var(--safe)]/25 border-[1.5px] border-[var(--safe)]" />
                            <span>Clean Node</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </Card>
                </div>

                {/* Details Sidebar - 3 columns */}
                <div className="lg:col-span-3">
                  <Card variant="elevated" className="p-6 h-[520px] flex flex-col justify-between">
                    <div>
                      <div className="flex items-center justify-between border-b border-[var(--border)] pb-3 mb-4">
                        <h4 className="text-xs font-bold text-[var(--text-3)] uppercase tracking-wider">
                          Forensic Inspector
                        </h4>
                        <span className="h-5 w-5 bg-[var(--surface-2)] text-[var(--text-3)] rounded-full flex items-center justify-center">
                          <Info className="h-3.5 w-3.5" />
                        </span>
                      </div>

                      {selectedNode ? (
                        <div className="space-y-5 text-xs font-semibold">
                          <div className="space-y-1">
                            <span className="text-[10px] text-[var(--text-4)] uppercase tracking-wider block font-bold">
                              Node Label
                            </span>
                            <div className="text-sm font-bold text-[var(--text-1)] font-mono break-all leading-normal select-all">
                              {selectedNode.label}
                            </div>
                          </div>

                          <div className="grid grid-cols-2 gap-4">
                            <DataPoint
                              label="Type"
                              value={
                                <Badge variant={selectedNode.type === "ACTOR" ? "neutral" : "ai"} size="sm">
                                  {selectedNode.type}
                                </Badge>
                              }
                            />
                            {selectedNode.type !== "ACTOR" && (
                              <DataPoint
                                label="Risk Score"
                                value={
                                  <span className="font-mono text-sm font-bold text-[var(--text-1)]">
                                    {selectedNode.risk_score}
                                  </span>
                                }
                              />
                            )}
                          </div>

                          {selectedNode.doc_id && (
                            <DataPoint
                              label="Document ID"
                              value={selectedNode.doc_id}
                              mono
                              copyable
                            />
                          )}

                          {selectedNode.type === "ACTOR" ? (
                            <div className="space-y-1">
                              <span className="text-[10px] text-[var(--text-4)] uppercase tracking-wider block font-bold">
                                Actor Correlation
                              </span>
                              <p className="text-[var(--text-2)] leading-relaxed bg-[var(--surface-2)] p-3 rounded-lg border border-[var(--border)] font-sans">
                                Threat campaigns targeting Indian UPI and invoice templates frequently share metadata clusters mapped to this signature.
                              </p>
                            </div>
                          ) : (
                            <div className="space-y-1">
                              <span className="text-[10px] text-[var(--text-4)] uppercase tracking-wider block font-bold">
                                Risk Level
                              </span>
                              <Badge variant={getThreatVariant(selectedNode.risk_level)} size="sm">
                                {selectedNode.risk_level}
                              </Badge>
                            </div>
                          )}
                        </div>
                      ) : (
                        <div className="flex flex-col items-center justify-center text-center text-[var(--text-3)] py-12">
                          <Network className="h-10 w-10 text-[var(--text-4)] mb-3 animate-pulse" />
                          <p className="font-bold text-sm text-[var(--text-1)]">No node selected</p>
                          <p className="text-xs max-w-[180px] mt-1.5 leading-normal">
                            Tap any actor template or event node on the network graph canvas to inspect matching properties.
                          </p>
                        </div>
                      )}
                    </div>

                    {selectedNode && selectedNode.type !== "ACTOR" && (
                      <div className="pt-4 border-t border-[var(--border)]">
                        <a
                          href={selectedNode.source_type === "DOCUMENT" ? "/docshield" : "/phishshield"}
                          className="w-full text-center inline-block px-4 py-2.5 rounded-lg bg-[var(--text-1)] text-[var(--text-inverse)] hover:bg-[var(--text-1)]/95 font-bold text-xs cursor-pointer select-none transition-all"
                        >
                          Analyze Source Logs &rarr;
                        </a>
                      </div>
                    )}
                  </Card>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </>
      )}
    </div>
  );
}
