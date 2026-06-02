"use client";

import React from "react";
import { twMerge } from "tailwind-merge";

export interface SkeletonLoaderProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "card" | "list" | "table" | "text";
  rows?: number;
  className?: string;
}

export const SkeletonLoader = ({
  variant = "text",
  rows = 3,
  className,
  ...props
}: SkeletonLoaderProps) => {
  const shimmerClass = "animate-pulse bg-gradient-to-r from-border/50 via-border/80 to-border/50 bg-[length:200%_100%]";

  return (
    <div className={twMerge("w-full space-y-4", className)} {...props}>
      {variant === "card" && (
        <div className="rounded-2xl border border-border/60 bg-surface p-6 shadow-glass backdrop-blur-[12px]">
          <div className="flex items-center justify-between">
            <div className={twMerge("h-3 w-24 rounded", shimmerClass)} />
            <div className={twMerge("h-8 w-8 rounded-lg", shimmerClass)} />
          </div>
          <div className="mt-6 flex items-baseline justify-between">
            <div className={twMerge("h-8 w-32 rounded", shimmerClass)} />
            <div className={twMerge("h-5 w-12 rounded-full", shimmerClass)} />
          </div>
        </div>
      )}

      {variant === "list" && (
        <div className="space-y-3">
          {Array.from({ length: rows }).map((_, idx) => (
            <div
              key={idx}
              className="flex items-center gap-3 rounded-xl border border-border/30 bg-surface/50 p-3 shadow-sm"
            >
              <div className={twMerge("h-8 w-8 rounded-full shrink-0", shimmerClass)} />
              <div className="flex-1 space-y-2">
                <div className={twMerge("h-3 w-1/3 rounded", shimmerClass)} />
                <div className={twMerge("h-2.5 w-2/3 rounded", shimmerClass)} />
              </div>
              <div className={twMerge("h-5 w-16 rounded-full shrink-0", shimmerClass)} />
            </div>
          ))}
        </div>
      )}

      {variant === "table" && (
        <div className="rounded-xl border border-border/50 overflow-hidden bg-surface/30">
          <div className="flex border-b border-border/40 p-4 bg-bg-base/50">
            <div className={twMerge("h-3.5 w-1/5 rounded", shimmerClass)} />
            <div className={twMerge("h-3.5 w-1/5 rounded ml-auto", shimmerClass)} />
            <div className={twMerge("h-3.5 w-1/5 rounded ml-auto", shimmerClass)} />
          </div>
          <div className="divide-y divide-border/20">
            {Array.from({ length: rows }).map((_, idx) => (
              <div key={idx} className="flex p-4 items-center justify-between">
                <div className={twMerge("h-3.5 w-1/4 rounded", shimmerClass)} />
                <div className={twMerge("h-3.5 w-1/6 rounded", shimmerClass)} />
                <div className={twMerge("h-3.5 w-1/5 rounded", shimmerClass)} />
              </div>
            ))}
          </div>
        </div>
      )}

      {variant === "text" && (
        <div className="space-y-2.5">
          {Array.from({ length: rows }).map((_, idx) => (
            <div
              key={idx}
              className={twMerge("h-3 rounded", shimmerClass)}
              style={{
                width: idx === rows - 1 ? "60%" : "100%",
                animationDelay: `${idx * 0.1}s`,
              }}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default SkeletonLoader;
