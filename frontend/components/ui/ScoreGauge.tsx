"use client";

import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { twMerge } from "tailwind-merge";

export interface ScoreGaugeProps extends React.HTMLAttributes<HTMLDivElement> {
  score: number; // 0–100
  size?: number; // width/height
  label?: string;
  animated?: boolean;
  className?: string;
}

function getScoreColors(score: number): { stroke: string; text: string; bg: string; label: string } {
  if (score >= 90) return { stroke: "var(--risk-critical)", text: "text-risk-critical", bg: "rgba(110, 64, 201, 0.1)", label: "CRITICAL" };
  if (score >= 70) return { stroke: "var(--risk-high)", text: "text-risk-high", bg: "rgba(207, 34, 46, 0.1)", label: "HIGH RISK" };
  if (score >= 40) return { stroke: "var(--risk-medium)", text: "text-risk-medium", bg: "rgba(154, 103, 0, 0.1)", label: "SUSPICIOUS" };
  return { stroke: "var(--risk-none)", text: "text-risk-none", bg: "rgba(26, 127, 55, 0.1)", label: "SAFE" };
}

export const ScoreGauge = ({
  score,
  size = 140,
  label = "RISK SCORE",
  animated = true,
  className,
  ...props
}: ScoreGaugeProps) => {
  const clamped = Math.min(Math.max(score, 0), 100);
  const strokeWidth = 8;
  const radius = (size - strokeWidth * 2) / 2;
  const circ = Math.PI * radius; // Half circle (gauge style)
  const offset = circ - (circ * clamped) / 100;
  const colors = getScoreColors(clamped);

  const [displayed, setDisplayed] = useState(animated ? 0 : clamped);

  useEffect(() => {
    if (!animated) return;
    let frame: number;
    const start = performance.now();
    const duration = 1000;
    const animate = (now: number) => {
      const t = Math.min((now - start) / duration, 1);
      const ease = 1 - Math.pow(1 - t, 3);
      setDisplayed(Math.round(ease * clamped));
      if (t < 1) frame = requestAnimationFrame(animate);
    };
    frame = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frame);
  }, [clamped, animated]);

  return (
    <div
      className={twMerge("flex flex-col items-center justify-center relative", className)}
      {...props}
    >
      <div className="relative" style={{ width: size, height: size / 2 + strokeWidth }}>
        <svg width={size} height={size / 2 + strokeWidth} className="overflow-visible">
          {/* Background Arc */}
          <path
            d={`M ${strokeWidth} ${size / 2} A ${radius} ${radius} 0 0 1 ${size - strokeWidth} ${size / 2}`}
            fill="none"
            stroke="var(--border-muted)"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
          />
          {/* Value Arc */}
          <motion.path
            d={`M ${strokeWidth} ${size / 2} A ${radius} ${radius} 0 0 1 ${size - strokeWidth} ${size / 2}`}
            fill="none"
            stroke={colors.stroke}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circ}
            initial={{ strokeDashoffset: circ }}
            animate={{ strokeDashoffset: offset }}
            transition={{ duration: 1.1, ease: "easeOut" }}
          />
        </svg>

        {/* Text Center Overlaid */}
        <div className="absolute inset-x-0 bottom-0 flex flex-col items-center justify-end text-center pointer-events-none select-none">
          <span className="text-caption text-text-muted tracking-widest font-medium uppercase text-[10px]">
            {label}
          </span>
          <span className={twMerge("text-data-lg font-bold leading-none mt-1", colors.text)}>
            {displayed}%
          </span>
          <span className={twMerge("text-[10px] font-semibold tracking-wider px-2 py-0.5 rounded-full mt-1.5 border uppercase", colors.text, "border-current/25")} style={{ backgroundColor: colors.bg }}>
            {colors.label}
          </span>
        </div>
      </div>
    </div>
  );
};

export default ScoreGauge;
