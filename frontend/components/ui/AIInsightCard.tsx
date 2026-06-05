"use client";

import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { twMerge } from "tailwind-merge";
import { SkeletonLoader } from "./SkeletonLoader";

export interface AIInsightCardProps {
  isLoading?: boolean;
  title?: string;
  children?: React.ReactNode;
  timestamp?: string;
  modelInfo?: string;
  className?: string;
}

const SparklesIcon = () => (
  <svg className="h-4 w-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.3-6.3l-.7.7M6.7 17.3l-.7.7m12.6 0l-.7-.7M6.7 6.7l-.7-.7N" />
    <path d="M10 8.5L12 6l2 2.5L15.5 10l-2.5 2-1 2-2-2.5L6.5 11l3.5-2.5z" fill="currentColor" opacity="0.3" />
  </svg>
);

export const AIInsightCard = ({
  isLoading = false,
  title = "LUMINT AI INSIGHT",
  children,
  timestamp,
  modelInfo = "Llama 3.3 70B · Groq",
  className,
}: AIInsightCardProps) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      className={twMerge(
        "rounded-xl border border-dashed border-ai-border/80 bg-ai-bg/60 overflow-hidden relative",
        className
      )}
    >
      {/* Decorative gradient overlay */}
      <div className="absolute top-0 inset-x-0 h-[3px] bg-gradient-to-r from-ai-accent/30 via-transparent to-ai-accent/10" />

      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4">
        <div className="flex items-center gap-2 text-ai-text">
          <SparklesIcon />
          <span className="text-label tracking-wider">{title}</span>
        </div>
        <span className="font-mono text-[10px] text-text-muted bg-surface-raised border border-border-default/60 px-2 py-0.5 rounded-full uppercase">
          {modelInfo}
        </span>
      </div>

      {/* Divider */}
      <div className="border-t border-dashed border-ai-border/40" />

      {/* Content */}
      <div className="px-5 py-5 text-body text-text-primary leading-relaxed">
        <AnimatePresence mode="wait">
          {isLoading ? (
            <motion.div
              key="skeleton"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="space-y-3"
            >
              <SkeletonLoader variant="text-md" className="bg-ai-border/10" />
              <SkeletonLoader variant="text-md" className="w-11/12 bg-ai-border/10" />
              <SkeletonLoader variant="text-sm" className="w-4/5 bg-ai-border/10" />
              <div className="pt-2 space-y-2">
                <SkeletonLoader variant="text-sm" className="bg-ai-border/10" />
                <SkeletonLoader variant="text-sm" className="w-5/6 bg-ai-border/10" />
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="content"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="prose prose-sm prose-slate max-w-none dark:prose-invert"
            >
              {children}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Footer */}
      {!isLoading && (
        <div className="border-t border-dashed border-ai-border/30 px-5 py-3 bg-surface-raised/20">
          <span className="font-mono text-[10px] text-text-secondary">
            ANALYSIS TIMESTAMP · {" "}
            {timestamp ??
              new Date().toLocaleString("en-IN", {
                dateStyle: "medium",
                timeStyle: "short",
              }).toUpperCase()}
          </span>
        </div>
      )}
    </motion.div>
  );
};

export default AIInsightCard;
