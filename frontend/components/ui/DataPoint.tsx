"use client";

import React, { useState } from "react";
import { twMerge } from "tailwind-merge";
import { Copy, Check } from "lucide-react";

export interface DataPointProps {
  label: string;
  value: React.ReactNode;
  copyable?: boolean;
  mono?: boolean;
  className?: string;
}

/**
 * DataPoint — atomic key-value pair used everywhere for structured data display.
 * Label: .t-label / text-3
 * Value: .t-mono / text-1 (default) or Inter when mono=false
 * Optional copy-to-clipboard icon on hover
 */
export const DataPoint = ({
  label,
  value,
  copyable = false,
  mono = true,
  className,
}: DataPointProps) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    const text = typeof value === "string" || typeof value === "number"
      ? String(value)
      : "";
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      // clipboard not available
    }
  };

  return (
    <div className={twMerge("flex flex-col gap-0.5 group", className)}>
      <span
        className="t-label"
        style={{ color: "var(--text-3)" }}
      >
        {label}
      </span>
      <div className="flex items-center gap-1.5">
        <span
          className={mono ? "t-mono" : "t-small"}
          style={{ color: "var(--text-1)" }}
        >
          {value ?? "—"}
        </span>
        {copyable && (
          <button
            onClick={handleCopy}
            aria-label={`Copy ${label}`}
            className="opacity-0 group-hover:opacity-100 transition-opacity duration-150 text-[var(--text-4)] hover:text-[var(--text-2)] p-0.5 rounded"
          >
            {copied
              ? <Check className="h-3 w-3 text-[var(--safe)]" />
              : <Copy className="h-3 w-3" />
            }
          </button>
        )}
      </div>
    </div>
  );
};

export default DataPoint;
