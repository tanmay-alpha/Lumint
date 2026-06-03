"use client";

import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { twMerge } from "tailwind-merge";
import { SkeletonLoader } from "./SkeletonLoader";

export interface AIAnalystCardProps {
  isLoading?: boolean;
  title?: string;
  children?: React.ReactNode;
  timestamp?: string;
  modelInfo?: string;
  className?: string;
}

// Small circuit/brain SVG icon
const AIIcon = () => (
  <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
    <circle cx="8" cy="8" r="3" stroke="currentColor" strokeWidth="1.5" />
    <path d="M8 1v2M8 13v2M1 8h2M13 8h2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    <circle cx="8" cy="8" r="1" fill="currentColor" />
    <path d="M3.05 3.05l1.41 1.41M11.54 11.54l1.41 1.41M3.05 12.95l1.41-1.41M11.54 4.46l1.41-1.41"
      stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
  </svg>
);

export const AIAnalystCard = ({
  isLoading = false,
  title = "Lumint AI Analyst",
  children,
  timestamp,
  modelInfo = "LLaMA 3.3 70B · Groq",
  className,
}: AIAnalystCardProps) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.2, ease: "easeOut" }}
      className={twMerge(
        "rounded-[12px] border-[1.5px] border-dashed border-[var(--color-ai-border)]",
        "bg-[var(--color-ai-bg)] overflow-hidden",
        className
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3.5">
        <div className="flex items-center gap-2.5 text-[var(--color-ai-text)]">
          <AIIcon />
          <span className="text-[13px] font-semibold">{title}</span>
        </div>
        <span className="font-mono text-[10px] text-[var(--color-text-muted)] bg-[var(--color-surface-2)] px-2 py-0.5 rounded-full">
          {modelInfo}
        </span>
      </div>

      {/* Divider */}
      <div className="border-t border-dashed border-[var(--color-ai-border)]" />

      {/* Content area */}
      <div className="px-5 py-4">
        <AnimatePresence mode="wait">
          {isLoading ? (
            <motion.div
              key="skeleton"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.3 }}
              className="space-y-3"
            >
              <SkeletonLoader variant="text-md" />
              <SkeletonLoader variant="text-md" className="w-4/5" />
              <SkeletonLoader variant="text-sm" className="w-3/5 mt-4" />
              <div className="mt-4 space-y-2">
                <SkeletonLoader variant="text-sm" />
                <SkeletonLoader variant="text-sm" className="w-5/6" />
                <SkeletonLoader variant="text-sm" className="w-4/6" />
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="content"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.3 }}
            >
              {children}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Footer */}
      {!isLoading && (
        <div className="border-t border-dashed border-[var(--color-ai-border)] px-5 py-2.5">
          <span className="font-mono text-[11px] text-[var(--color-text-muted)]">
            Analysis generated ·{" "}
            {timestamp ??
              new Date().toLocaleString("en-IN", {
                dateStyle: "medium",
                timeStyle: "short",
              })}
          </span>
        </div>
      )}
    </motion.div>
  );
};

export default AIAnalystCard;
