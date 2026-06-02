"use client";

import React, { useState, useEffect } from "react";
import { 
  Network, 
  RefreshCw, 
  ShieldAlert, 
  HelpCircle,
  FileText,
  Globe,
  Fingerprint,
  Info,
  Calendar,
  AlertTriangle
} from "lucide-react";
import GlassCard from "@/components/GlassCard";
import ThreatBadge from "@/components/ThreatBadge";
import { fraudDNAService } from "@/services/fraud-dna";
import { Campaign, GraphNode, GraphEdge } from "@/types";

interface NodeWithPosition extends GraphNode {
  x: number;
  y: number;
}

export default function FraudDNA() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [nodes, setNodes] = useState<NodeWithPosition[]>([]);
  const [edges, setEdges] = useState<GraphEdge[]>([]);
  const [loading, setLoading] = useState(true);
  const [reclustering, setReclustering] = useState(false);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [selectedCampaign, setSelectedCampaign] = useState<Campaign | null>(null);

  async function loadData() {
    try {
      const [campaignsRes, graphRes] = await Promise.all([
        fraudDNAService.getCampaigns(),
        fraudDNAService.getGraph(),
      ]);
      
      setCampaigns(campaignsRes.campaigns);
      
      // Calculate coordinates for nodes using a radial cluster layout
      const calculatedNodes = computeNodeCoordinates(graphRes.nodes, graphRes.edges);
      setNodes(calculatedNodes);
      setEdges(graphRes.edges);

      // Select first campaign by default
      if (campaignsRes.campaigns.length > 0) {
        setSelectedCampaign(campaignsRes.campaigns[0]);
      }
    } catch (error) {
      console.error("Failed to load DNA graph data", error);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  const handleRecluster = async () => {
    setReclustering(true);
    try {
      const res = await fraudDNAService.recluster();
      setCampaigns(res.campaigns);
      await loadData();
    } catch (err) {
      console.error(err);
    } finally {
      setReclustering(false);
    }
  };

  // Radial cluster layout generator
  const computeNodeCoordinates = (rawNodes: GraphNode[], rawEdges: GraphEdge[]): NodeWithPosition[] => {
    const width = 600;
    const height = 400;
    
    // 1. Identify campaign centers
    const campaignNodes = rawNodes.filter(n => n.type === "campaign");
    const otherNodes = rawNodes.filter(n => n.type !== "campaign");
    
    const nodeMap = new Map<string, NodeWithPosition>();
    
    // Position campaign nodes at focal centers
    campaignNodes.forEach((campaign, idx) => {
      // Space centers evenly across width
      const x = (idx + 0.5) * (width / Math.max(1, campaignNodes.length)) + (Math.random() - 0.5) * 20;
      const y = height / 2 + (Math.random() - 0.5) * 40;
      nodeMap.set(campaign.id, { ...campaign, x, y });
    });

    // Handle case if no campaign centers exist
    if (campaignNodes.length === 0) {
      rawNodes.forEach((node, idx) => {
        const angle = (idx / rawNodes.length) * 2 * Math.PI;
        nodeMap.set(node.id, {
          ...node,
          x: width / 2 + Math.cos(angle) * 120,
          y: height / 2 + Math.sin(angle) * 120
        });
      });
      return Array.from(nodeMap.values());
    }

    // 2. Position orbiting child nodes around their campaign hubs
    otherNodes.forEach((node) => {
      // Find connected campaign edge
      const connectedEdges = rawEdges.filter(e => e.source === node.id || e.target === node.id);
      const parentCampaignEdge = connectedEdges.find(e => 
        campaignNodes.some(c => c.id === e.source || c.id === e.target)
      );
      
      const parentId = parentCampaignEdge 
        ? (campaignNodes.some(c => c.id === parentCampaignEdge.source) ? parentCampaignEdge.source : parentCampaignEdge.target)
        : campaignNodes[0].id;
      
      const parent = nodeMap.get(parentId);
      
      if (parent) {
        // Orbit count for this parent
        const childrenOfParent = otherNodes.filter(n => {
          const childEdges = rawEdges.filter(e => e.source === n.id || e.target === n.id);
          return childEdges.some(e => e.source === parentId || e.target === parentId);
        });
        
        const childIdx = childrenOfParent.indexOf(node);
        const totalChildren = Math.max(1, childrenOfParent.length);
        
        const angle = (childIdx / totalChildren) * 2 * Math.PI + (parentId === campaignNodes[0].id ? 0.3 : -0.3);
        const radius = 85 + (childIdx % 2 === 0 ? 15 : -15); // Stagger radius for less overlaps
        
        nodeMap.set(node.id, {
          ...node,
          x: parent.x + Math.cos(angle) * radius,
          y: parent.y + Math.sin(angle) * radius
        });
      } else {
        nodeMap.set(node.id, {
          ...node,
          x: width / 2 + (Math.random() - 0.5) * 100,
          y: height / 2 + (Math.random() - 0.5) * 100
        });
      }
    });

    return Array.from(nodeMap.values());
  };

  const getIconForNodeType = (type: GraphNode["type"]) => {
    switch (type) {
      case "campaign": return Network;
      case "event": return FileText;
      case "domain": return Globe;
      default: return Fingerprint;
    }
  };

  const getRiskColor = (level: string) => {
    if (level === "HIGH" || level === "CRITICAL") return "fill-red-500 stroke-red-100";
    if (level === "SUSPICIOUS" || level === "ELEVATED") return "fill-amber-400 stroke-amber-100";
    return "fill-emerald-500 stroke-emerald-100";
  };

  if (loading) {
    return (
      <div className="space-y-8 animate-pulse">
        <div className="h-8 w-64 bg-slate-200 rounded-lg"></div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 h-[450px] bg-slate-200 rounded-3xl"></div>
          <div className="h-[450px] bg-slate-200 rounded-3xl"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight flex items-center gap-3">
            <Network className="h-7 w-7 text-slate-900" />
            Fraud DNA Clustering
          </h2>
          <p className="text-slate-500 mt-1.5 text-sm font-medium">
            Graph database displaying shared registry infrastructure, matching metadata tags, and spoof campaigns.
          </p>
        </div>

        <button
          onClick={handleRecluster}
          disabled={reclustering}
          className="flex items-center gap-2 px-4 py-2.5 bg-white border border-slate-200/80 hover:bg-slate-50 text-slate-700 rounded-xl text-xs font-bold shadow-sm transition-all"
        >
          <RefreshCw className={`h-4 w-4 text-slate-500 ${reclustering && "animate-spin"}`} />
          <span>{reclustering ? "Reclustering..." : "Run Recluster Sync"}</span>
        </button>
      </div>

      {/* Main Graph Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Visual Graph Viewport */}
        <div className="lg:col-span-2 space-y-8">
          <GlassCard className="p-6 overflow-hidden">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4 mb-4">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">DNA Relationship Cluster Map</span>
              <span className="text-[10px] text-slate-400 font-semibold flex items-center gap-1">
                <Info className="h-3.5 w-3.5" /> Hover or click nodes to audit attributes
              </span>
            </div>

            <div className="relative bg-[#FBFBFC] rounded-2xl border border-slate-200/40 overflow-hidden flex items-center justify-center">
              {/* Interactive SVG Network Graph */}
              <svg 
                viewBox="0 0 600 400" 
                className="w-full aspect-[3/2] select-none"
              >
                {/* 1. Draw Links/Edges */}
                <g>
                  {edges.map((edge, idx) => {
                    const sourceNode = nodes.find(n => n.id === edge.source);
                    const targetNode = nodes.find(n => n.id === edge.target);
                    if (!sourceNode || !targetNode) return null;
                    return (
                      <line
                        key={idx}
                        x1={sourceNode.x}
                        y1={sourceNode.y}
                        x2={targetNode.x}
                        y2={targetNode.y}
                        stroke="#CBD5E1"
                        strokeWidth="1.5"
                        strokeDasharray={edge.type === "campaign_link" ? "0" : "3 3"}
                        opacity="0.75"
                      />
                    );
                  })}
                </g>

                {/* 2. Draw Nodes */}
                <g>
                  {nodes.map((node) => {
                    const IconComponent = getIconForNodeType(node.type);
                    const isSelected = selectedNode?.id === node.id;
                    return (
                      <g 
                        key={node.id}
                        transform={`translate(${node.x}, ${node.y})`}
                        className="cursor-pointer group"
                        onClick={() => {
                          setSelectedNode(node);
                          // If connected to a campaign, highlight that campaign details
                          const campaignLink = edges.find(e => 
                            (e.source === node.id || e.target === node.id) &&
                            (e.source.startsWith("camp-") || e.target.startsWith("camp-"))
                          );
                          if (campaignLink) {
                            const campId = campaignLink.source.startsWith("camp-") ? campaignLink.source : campaignLink.target;
                            const comp = campaigns.find(c => c.campaign_id === campId);
                            if (comp) setSelectedCampaign(comp);
                          }
                        }}
                      >
                        {/* Node Halo Ring */}
                        <circle
                          r={isSelected ? "20" : "14"}
                          className={`fill-white stroke-2 transition-all duration-300 ${getRiskColor(node.risk_level)} ${
                            isSelected ? "stroke-[3px]" : "group-hover:stroke-[2.5px]"
                          }`}
                        />
                        
                        {/* Smaller inner circle indicator */}
                        <circle
                          r="3"
                          className={`${getRiskColor(node.risk_level)} opacity-30`}
                          cy="0"
                          cx="0"
                        />

                        {/* Node Label Text */}
                        <text
                          y="24"
                          textAnchor="middle"
                          className="text-[9px] font-bold fill-slate-700 tracking-wide select-none"
                        >
                          {node.label.length > 15 ? `${node.label.substring(0, 12)}...` : node.label}
                        </text>
                      </g>
                    );
                  })}
                </g>
              </svg>
            </div>
          </GlassCard>

          {/* List of campaigns */}
          <GlassCard className="p-6 md:p-8">
            <h3 className="text-sm font-bold text-slate-900 mb-4">Active Threat Clusters</h3>
            <div className="divide-y divide-slate-100">
              {campaigns.map((camp) => (
                <div 
                  key={camp.campaign_id}
                  onClick={() => setSelectedCampaign(camp)}
                  className={`py-4 flex flex-col md:flex-row md:items-center justify-between gap-4 cursor-pointer transition-colors ${
                    selectedCampaign?.campaign_id === camp.campaign_id ? "bg-slate-50 -mx-6 px-6" : "hover:bg-slate-50/50 -mx-4 px-4 rounded-xl"
                  }`}
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <h4 className="text-sm font-bold text-slate-800">{camp.name}</h4>
                      <ThreatBadge level={camp.risk_level} />
                    </div>
                    <p className="text-xs text-slate-500 leading-normal line-clamp-1">{camp.description}</p>
                  </div>
                  
                  <div className="flex items-center gap-3 shrink-0">
                    <span className="text-[10px] text-slate-400 font-bold bg-white border border-slate-200/50 px-2 py-0.5 rounded-lg">
                      {camp.common_indicators.length} linked assets
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </GlassCard>
        </div>

        {/* Sidebar Details Panel */}
        <div className="space-y-8">
          
          {/* Node metadata detail Card */}
          {selectedNode && (
            <GlassCard className="p-6 md:p-8 space-y-6">
              <div className="flex justify-between items-start border-b border-slate-100 pb-4">
                <div>
                  <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Selected DNA Node</span>
                  <h3 className="text-sm font-bold text-slate-900 mt-0.5">{selectedNode.label}</h3>
                </div>
                <button 
                  onClick={() => setSelectedNode(null)}
                  className="text-xs font-semibold text-slate-400 hover:text-slate-700"
                >
                  Clear
                </button>
              </div>

              <div className="space-y-4">
                <div className="flex justify-between items-center text-xs font-semibold">
                  <span className="text-slate-500">Node ID</span>
                  <code className="text-slate-800 bg-slate-50 border border-slate-100 px-1.5 py-0.5 rounded">{selectedNode.id}</code>
                </div>

                <div className="flex justify-between items-center text-xs font-semibold">
                  <span className="text-slate-500">Classification</span>
                  <span className="text-slate-800 capitalize">{selectedNode.type}</span>
                </div>

                <div className="flex justify-between items-center text-xs font-semibold">
                  <span className="text-slate-500">Node Threat Index</span>
                  <ThreatBadge level={selectedNode.risk_level} />
                </div>

                {selectedNode.details && (
                  <div className="pt-4 border-t border-slate-100 space-y-2">
                    <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">Context / Registry Details</span>
                    <p className="text-xs text-slate-600 leading-relaxed bg-slate-50 border border-slate-200/40 p-3 rounded-2xl font-medium">
                      {selectedNode.details}
                    </p>
                  </div>
                )}
              </div>
            </GlassCard>
          )}

          {/* Campaign details Card */}
          {selectedCampaign && (
            <GlassCard className="p-6 md:p-8 space-y-6">
              <div className="border-b border-slate-100 pb-4">
                <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Campaign Dossier</span>
                <h3 className="text-base font-bold text-slate-900 mt-1">{selectedCampaign.name}</h3>
                <div className="flex items-center gap-2 mt-2">
                  <ThreatBadge level={selectedCampaign.risk_level} />
                  <span className="text-[10px] text-slate-400 font-semibold">• Actor: {selectedCampaign.threat_actor_hint}</span>
                </div>
              </div>

              <div className="space-y-4 text-xs">
                <div>
                  <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block mb-1">Incident Summary</span>
                  <p className="text-slate-600 leading-relaxed font-medium">{selectedCampaign.description}</p>
                </div>

                <div>
                  <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block mb-2">Common Indicators</span>
                  <div className="flex flex-wrap gap-2">
                    {selectedCampaign.common_indicators.map((ind, idx) => (
                      <span key={idx} className="bg-slate-50 border border-slate-200/40 text-[10px] font-bold text-slate-600 px-2.5 py-1 rounded-xl">
                        {ind}
                      </span>
                    ))}
                  </div>
                </div>

                <div>
                  <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block mb-2">Common Keyword Matches</span>
                  <div className="flex flex-wrap gap-1.5">
                    {selectedCampaign.common_keywords.map((kw, idx) => (
                      <span key={idx} className="bg-sky-50 border border-sky-100/50 text-[10px] font-bold text-sky-700 px-2 py-0.5 rounded-lg">
                        {kw}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="pt-4 border-t border-slate-100 flex items-center justify-between text-[10px] text-slate-400 font-semibold">
                  <span className="flex items-center gap-1"><Calendar className="h-3.5 w-3.5" /> Detected:</span>
                  <span>{new Date(selectedCampaign.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            </GlassCard>
          )}

        </div>

      </div>

    </div>
  );
}
