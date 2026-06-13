"use client";
import React from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { History, Trash2, Shield, FileSearch, ShieldAlert, Smartphone, ExternalLink } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { getScanHistory, clearScanHistory, ScanHistoryEntry } from "@/lib/scan-history";

const SHIELD_ICONS = {
  upi: Smartphone,
  doc: FileSearch,
  phish: ShieldAlert,
};

const RISK_COLORS: Record<string, string> = {
  GENUINE: "text-[var(--safe)] bg-[var(--safe-bg)]",
  CLEAN: "text-[var(--safe)] bg-[var(--safe-bg)]",
  SUSPICIOUS: "text-[var(--warn)] bg-[var(--warn-bg)]",
  HIGH_RISK: "text-[var(--high)] bg-[var(--high-bg)]",
  HIGH: "text-[var(--high)] bg-[var(--high-bg)]",
  CRITICAL: "text-[var(--high)] bg-[var(--high-bg)]",
  ERROR: "text-[var(--text-3)] bg-[var(--surface-2)]",
  NOT_UPI: "text-[var(--text-3)] bg-[var(--surface-2)]",
  NOT_DOCUMENT: "text-[var(--text-3)] bg-[var(--surface-2)]",
};

export default function HistoryPage() {
  const [history, setHistory] = React.useState<ScanHistoryEntry[]>([]);

  React.useEffect(() => {
    setHistory(getScanHistory());
  }, []);

  const handleClear = () => {
    if (confirm("Clear all scan history? This cannot be undone.")) {
      clearScanHistory();
      setHistory([]);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-[var(--brand-muted)] flex items-center justify-center">
            <History className="h-5 w-5 text-[var(--brand)]" />
          </div>
          <div>
            <h1 className="text-xl font-bold">Scan History</h1>
            <p className="text-sm text-[var(--text-3)]">Last {history.length} scans, stored locally on your device</p>
          </div>
        </div>
        {history.length > 0 && (
          <Button variant="outline" onClick={handleClear} className="flex items-center gap-2">
            <Trash2 className="h-4 w-4" />
            Clear All
          </Button>
        )}
      </div>

      {history.length === 0 ? (
        <Card className="p-12 text-center">
          <Shield className="h-12 w-12 mx-auto text-[var(--text-4)] mb-3" />
          <p className="text-[var(--text-3)]">No scans yet. Try one of the shields to get started.</p>
          <Link href="/upi-shield">
            <Button className="mt-4">Try UPI Shield</Button>
          </Link>
        </Card>
      ) : (
        <div className="space-y-3">
          {history.map((entry) => {
            const Icon = SHIELD_ICONS[entry.shield];
            const colorClass = RISK_COLORS[entry.verdict] || RISK_COLORS.ERROR;
            const date = new Date(entry.timestamp);
            const link = `/${entry.shield === 'upi' ? 'upi-shield' : entry.shield === 'doc' ? 'docshield' : 'phishshield'}`;

            return (
              <motion.div
                key={entry.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <Link href={link}>
                  <Card className="p-4 hover:border-[var(--brand)] transition-colors cursor-pointer">
                    <div className="flex items-center gap-4">
                      <div className="h-10 w-10 rounded-lg bg-[var(--surface-2)] flex items-center justify-center">
                        <Icon className="h-5 w-5 text-[var(--brand)]" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold capitalize">{entry.shield} Shield</span>
                          <span className={`text-[10px] font-bold uppercase px-1.5 py-0.5 rounded ${colorClass}`}>
                            {entry.verdict}
                          </span>
                        </div>
                        <p className="text-sm text-[var(--text-3)] truncate">
                          {entry.fileName || entry.url || "Scan"} · Score: {entry.score}
                        </p>
                      </div>
                      <div className="text-right text-xs text-[var(--text-4)]">
                        {date.toLocaleDateString()}
                        <br />
                        {date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                      </div>
                      <ExternalLink className="h-4 w-4 text-[var(--text-4)]" />
                    </div>
                  </Card>
                </Link>
              </motion.div>
            );
          })}
        </div>
      )}
    </div>
  );
}
