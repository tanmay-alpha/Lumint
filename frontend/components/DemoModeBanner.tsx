"use client";
import { Info } from "lucide-react";

/**
 * Banner shown across the dashboard pages in demo deployments to make it
 * clear that most modules require a backend and are non-functional here.
 * Only UPI Shield works without a backend.
 */
export function DemoModeBanner() {
  return (
    <div
      role="note"
      className="rounded-lg border border-[var(--warn-border)]/30 bg-[var(--warn-bg)] px-4 py-2.5 flex items-center gap-2 text-xs font-sans"
    >
      <Info className="h-4 w-4 text-[var(--warn)] shrink-0" />
      <span className="text-[var(--text-2)]">
        <strong className="font-semibold">Demo deployment</strong>{" "}
        — Only UPI Shield is fully functional. Other modules require a
        backend (future enhancement).
      </span>
    </div>
  );
}

export default DemoModeBanner;
