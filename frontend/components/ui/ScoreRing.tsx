"use client";

import React from "react";
import { motion } from "framer-motion";
import { twMerge } from "tailwind-merge";

export interface ScoreRingProps extends React.HTMLAttributes<HTMLDivElement> {
  score: number; // 0-100
  size?: number; // width & height in px
  label?: string;
  className?: string;
}

export const ScoreRing = ({
  score,
  size = 120,
  label = "Risk Score",
  className,
  ...props
}: ScoreRingProps) => {
  // Normalize score between 0 and 100
  const normalizedScore = Math.min(Math.max(score, 0), 100);

  // SVG circle calculations
  const strokeWidth = size * 0.08;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (circumference * normalizedScore) / 100;

  // Determine color based on threshold
  // green < 40, amber < 70, red >= 70
  let strokeColor = "var(--risk-safe)";
  let textColor = "text-risk-safe";
  let bgColorClass = "stroke-risk-safe/10";
  if (normalizedScore >= 70) {
    strokeColor = "var(--risk-critical)";
    textColor = "text-risk-critical";
    bgColorClass = "stroke-risk-critical/10";
  } else if (normalizedScore >= 40) {
    strokeColor = "var(--risk-high)";
    textColor = "text-risk-high";
    bgColorClass = "stroke-risk-high/10";
  }

  return (
    <div
      className={twMerge("relative flex flex-col items-center justify-center", className)}
      style={{ width: size, height: size }}
      {...props}
    >
      <svg
        width={size}
        height={size}
        className="absolute -rotate-90 transform"
      >
        {/* Background Circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          className={twMerge("fill-transparent", bgColorClass)}
          strokeWidth={strokeWidth}
        />
        {/* Foreground Circle */}
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="transparent"
          stroke={strokeColor}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeLinecap="round"
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset }}
          transition={{ duration: 1, ease: "easeOut" }}
        />
      </svg>

      {/* Content overlays */}
      <div className="z-10 flex flex-col items-center justify-center text-center">
        <span
          className={twMerge("font-mono text-3xl font-bold tracking-tight", textColor)}
        >
          {normalizedScore}
        </span>
        {label && (
          <span className="mt-0.5 text-[10px] font-semibold tracking-wider text-text-secondary uppercase">
            {label}
          </span>
        )}
      </div>
    </div>
  );
};

export default ScoreRing;
