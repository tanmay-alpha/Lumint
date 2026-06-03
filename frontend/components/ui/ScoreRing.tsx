"use client";

import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { twMerge } from "tailwind-merge";

export interface ScoreRingProps extends React.HTMLAttributes<HTMLDivElement> {
  score: number;       // 0–100
  size?: 80 | 120 | 160 | number;
  label?: string;
  animated?: boolean;
  className?: string;
}

function getScoreColor(score: number): string {
  if (score >= 90) return "var(--color-critical)";
  if (score >= 70) return "var(--color-danger)";
  if (score >= 40) return "var(--color-warn)";
  return "var(--color-safe)";
}

function getScoreTextClass(score: number): string {
  if (score >= 90) return "text-[var(--color-critical)]";
  if (score >= 70) return "text-[var(--color-danger)]";
  if (score >= 40) return "text-[var(--color-warn)]";
  return "text-[var(--color-safe)]";
}

function getTrackColor(score: number): string {
  if (score >= 90) return "rgba(124,58,237,0.12)";
  if (score >= 70) return "rgba(239,68,68,0.12)";
  if (score >= 40) return "rgba(245,158,11,0.12)";
  return "rgba(16,185,129,0.12)";
}

export const ScoreRing = ({
  score,
  size = 120,
  label = "Risk Score",
  animated = true,
  className,
  ...props
}: ScoreRingProps) => {
  const clamped   = Math.min(Math.max(score, 0), 100);
  const sw        = Math.max(size * 0.075, 6);
  const radius    = (size - sw) / 2;
  const circ      = 2 * Math.PI * radius;
  const offset    = circ - (circ * clamped) / 100;
  const color     = getScoreColor(clamped);
  const track     = getTrackColor(clamped);
  const textClass = getScoreTextClass(clamped);

  // Counter animation
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

  const fontSize = size >= 160 ? "text-4xl" : size >= 120 ? "text-3xl" : "text-2xl";
  const labelSize = size >= 120 ? "text-[10px]" : "text-[9px]";

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
          stroke={track}
          strokeWidth={sw}
        />
        {/* Filled arc */}
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
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
        <span className={twMerge("font-mono font-bold tracking-tight", fontSize, textClass)}>
          {displayed}
        </span>
        {label && (
          <span className={twMerge("mt-0.5 font-sans font-semibold tracking-widest text-[var(--color-text-muted)] uppercase", labelSize)}>
            {label}
          </span>
        )}
      </div>
    </div>
  );
};

export default ScoreRing;
