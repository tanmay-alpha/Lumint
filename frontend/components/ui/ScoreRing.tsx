"use client";

import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { twMerge } from "tailwind-merge";

export interface ScoreRingProps extends React.HTMLAttributes<HTMLDivElement> {
  score: number;       // 0–100
  size?: number;
  label?: string;
  animated?: boolean;
  className?: string;
}

function getScoreColors(score: number): { stroke: string; text: string; bg: string; label: string } {
  if (score >= 90) return { stroke: "var(--risk-critical)", text: "text-risk-critical", bg: "rgba(110, 64, 201, 0.1)", label: "CRITICAL" };
  if (score >= 70) return { stroke: "var(--risk-high)", text: "text-risk-high", bg: "rgba(207, 34, 46, 0.1)", label: "HIGH" };
  if (score >= 40) return { stroke: "var(--risk-medium)", text: "text-risk-medium", bg: "rgba(154, 103, 0, 0.1)", label: "MEDIUM" };
  return { stroke: "var(--risk-none)", text: "text-risk-none", bg: "rgba(26, 127, 55, 0.1)", label: "SAFE" };
}

export const ScoreRing = ({
  score,
  size = 120,
  label = "Risk Score",
  animated = true,
  className,
  ...props
}: ScoreRingProps) => {
  const clamped = Math.min(Math.max(score, 0), 100);
  const sw = Math.max(size * 0.065, 5);
  const radius = (size - sw) / 2;
  const circ = 2 * Math.PI * radius;
  const offset = circ - (circ * clamped) / 100;
  const colors = getScoreColors(clamped);

  const [displayed, setDisplayed] = useState(animated ? 0 : clamped);

  useEffect(() => {
    if (!animated) return;
    let frame: number;
    const start = performance.now();
    const duration = 900;
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
      className={twMerge("relative flex flex-col items-center justify-center shrink-0", className)}
      style={{ width: size, height: size }}
      {...props}
    >
      <svg
        width={size}
        height={size}
        className="absolute -rotate-90"
        aria-hidden="true"
      >
        {/* Track */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--border-muted)"
          strokeWidth={sw}
        />
        {/* Filled arc */}
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={colors.stroke}
          strokeWidth={sw}
          strokeDasharray={circ}
          strokeLinecap="round"
          initial={{ strokeDashoffset: circ }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 0.9, ease: [0.34, 1.56, 0.64, 1] }}
        />
      </svg>

      {/* Center content */}
      <div className="relative z-10 flex flex-col items-center justify-center text-center">
        <span className={twMerge("font-mono text-2xl font-bold tracking-tight", colors.text)}>
          {displayed}
        </span>
        {label && (
          <span className="text-[10px] mt-0.5 font-sans font-medium tracking-widest text-text-secondary uppercase">
            {label}
          </span>
        )}
      </div>
    </div>
  );
};

export default ScoreRing;
