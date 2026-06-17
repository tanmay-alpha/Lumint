"use client";
import Link from "next/link";
import { Button } from "@/components/ui/Button";
import { FileSearch, Smartphone, History, Network, AlertCircle } from "lucide-react";

interface EmptyStateWithCTAProps {
  icon: "search" | "shield" | "history" | "network" | "alert";
  title: string;
  description: string;
  primaryAction?: { label: string; href: string };
  secondaryAction?: { label: string; href: string };
  technicalDetails?: string;
}

const ICONS = {
  search: FileSearch,
  shield: Smartphone,
  history: History,
  network: Network,
  alert: AlertCircle,
};

export function EmptyStateWithCTA({
  icon,
  title,
  description,
  primaryAction,
  secondaryAction,
  technicalDetails,
}: EmptyStateWithCTAProps) {
  const Icon = ICONS[icon];
  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-1)] p-8 text-center space-y-4">
      <div className="h-14 w-14 mx-auto rounded-xl bg-[var(--warn-bg)] flex items-center justify-center">
        <Icon className="h-7 w-7 text-[var(--warn)]" />
      </div>
      <div>
        <h3 className="text-lg font-semibold text-[var(--text-1)]">{title}</h3>
        <p className="text-sm text-[var(--text-3)] mt-1 max-w-md mx-auto leading-relaxed">{description}</p>
      </div>
      {technicalDetails && (
        <p className="text-xs text-[var(--text-4)] font-mono bg-[var(--surface-2)] inline-block px-3 py-1.5 rounded">
          {technicalDetails}
        </p>
      )}
      {(primaryAction || secondaryAction) && (
        <div className="flex items-center justify-center gap-2 pt-2">
          {primaryAction && (
            <Link href={primaryAction.href}>
              <Button variant="solid">{primaryAction.label}</Button>
            </Link>
          )}
          {secondaryAction && (
            <Link href={secondaryAction.href}>
              <Button variant="outline">{secondaryAction.label}</Button>
            </Link>
          )}
        </div>
      )}
    </div>
  );
}

export default EmptyStateWithCTA;