import { useEffect, useState, useRef, useCallback } from "react";

export interface ThreatEvent {
  event_id: string;
  timestamp: string;
  module: "phish" | "doc" | "upi" | "fraud_dna";
  threat_level: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  summary: string;
  risk_score: number;
  ai_verdict: string;
  indicators: string[];
  drift_status: "stable" | "warning" | "drift";
}

export type ConnectionStatus = "connecting" | "connected" | "disconnected";

export function useThreatStream(simulate = false, simulationRate = 1.0) {
  const [events, setEvents] = useState<ThreatEvent[]>([]);
  const [status, setStatus] = useState<ConnectionStatus>("disconnected");
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectCountRef = useRef(0);
  const connectRef = useRef<() => void>(() => {});

  const connect = useCallback(() => {
    if (wsRef.current) {
      try {
        wsRef.current.close();
      } catch {}
    }

    setStatus("connecting");
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    // Fallback to local 8000 port
    const host = process.env.NEXT_PUBLIC_WS_HOST || "localhost:8000";
    
    const path = simulate 
      ? `/ws/threats/simulate?rate=${simulationRate}` 
      : "/ws/threats";
      
    const url = `${protocol}//${host}${path}`;
    
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setStatus("connected");
      reconnectCountRef.current = 0;
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };

    ws.onmessage = (event) => {
      try {
        const newEvent = JSON.parse(event.data) as ThreatEvent;
        setEvents((prev) => {
          // Avoid duplicate events
          if (prev.some((e) => e.event_id === newEvent.event_id)) {
            return prev;
          }
          const updated = [...prev, newEvent];
          // Limit to 50 items (keep most recent)
          if (updated.length > 50) {
            return updated.slice(updated.length - 50);
          }
          return updated;
        });
      } catch (err) {
        console.error("Failed to parse threat stream event:", err);
      }
    };

    ws.onclose = () => {
      setStatus("disconnected");
      wsRef.current = null;
      
      const delay = Math.min(1000 * Math.pow(2, reconnectCountRef.current), 3000);
      reconnectCountRef.current += 1;
      
      reconnectTimeoutRef.current = setTimeout(() => {
        connectRef.current();
      }, delay);
    };

    ws.onerror = (err) => {
      console.error("WebSocket error:", err);
      try {
        ws.close();
      } catch {}
    };
  }, [simulate, simulationRate]);

  useEffect(() => {
    connectRef.current = connect;
  }, [connect]);

  useEffect(() => {
    const timer = setTimeout(() => {
      connect();
    }, 0);
    return () => {
      clearTimeout(timer);
      if (wsRef.current) {
        try {
          wsRef.current.close();
        } catch {}
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [connect]);

  const clearEvents = useCallback(() => {
    setEvents([]);
  }, []);

  return { events, status, clearEvents };
}
