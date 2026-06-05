"use client";

import React, { useEffect, useState } from "react";
import { twMerge } from "tailwind-merge";
import { motion } from "framer-motion";

export interface RiskScoreProps extends React.HTMLAttributes<HTMLDivElement> {
  score: number;       // 0–100
  size?: "sm" | "md" | "lg";
  animated?: boolean;
  className?: string;
}

const SIZE_MAP = { sm: 80, md: 120, lg: 160 };

function getScoreColor(score: number): string {
  if (score >= 80) return "var(--critical)";
  if (score >= 60) return "var(--high)";
  if (score >= 30) return "var(--warn)";
  return "var(--safe)";
}

function getVerdict(score: number): string {
  if (score >= 80) return "CRITICAL";
  if (score >= 60) return "HIGH RISK";
  if (score >= 30) return "SUSPICIOUS";
  return "SAFE";
}

function getVerdictColor(score: number): string {
  if (score >= 80) return "var(--critical)";
  if (score >= 60) return "var(--high)";
  if (score >= 30) return "var(--warn)";
  return "var(--safe)";
}

/**
 * RiskScore — half-gauge arc SVG with animated fill and count-up number.
 * Replaces ScoreRing with a more space-efficient design.
 */
export const RiskScore = ({
  score,
  size = "md",
  animated = true,
  className,
  ...props
}: RiskScoreProps) => {
  const w = SIZE_MAP[size];
  const h = Math.ceil(w * 0.6);  // half-gauge height
  const cx = w / 2;
  const cy = h - (size === "sm" ? 10 : size === "md" ? 14 : 18);
  const strokeWidth = size === "sm" ? 6 : size === "md" ? 8 : 10;
  const r = (w / 2) - strokeWidth - 2;

  // Arc: from 180° to 0° (left → right, top only)
  const startAngle = Math.PI;       // 180°
  const endAngle = 0;               // 0°
  const totalArc = Math.PI;         // 180° sweep

  const clamped = Math.min(Math.max(score, 0), 100);
  const arcLength = (clamped / 100) * totalArc;
  const fillEndAngle = startAngle - arcLength;

  // Convert polar → cartesian
  const polar = (angle: number) => ({
    x: cx + r * Math.cos(angle),
    y: cy - r * Math.sin(angle),
  });

  const trackStart = polar(startAngle);
  const trackEnd = polar(endAngle);
  const fillEnd = polar(fillEndAngle);
  const fillLargeArc = arcLength > Math.PI / 2 ? 0 : 0;

  const trackPath = `M ${trackStart.x} ${trackStart.y} A ${r} ${r} 0 0 1 ${trackEnd.x} ${trackEnd.y}`;

  // Segment the arc into colored sections
  const safeEnd   = polar(startAngle - 0.30 * totalArc);
  const warnEnd   = polar(startAngle - 0.60 * totalArc);
  const highEnd   = polar(startAngle - 0.80 * totalArc);

  const arcSegment = (from: number, to: number) => {
    const p1 = polar(from);
    const p2 = polar(to);
    const sweep = Math.abs(from - to);
    const large = sweep > Math.PI ? 1 : 0;
    return `M ${p1.x} ${p1.y} A ${r} ${r} 0 ${large} 1 ${p2.x} ${p2.y}`;
  };

  const fillPath = clamped === 0
    ? ""
    : `M ${trackStart.x} ${trackStart.y} A ${r} ${r} 0 ${fillLargeArc} 1 ${fillEnd.x} ${fillEnd.y}`;

  // Count-up animation
  const [displayed, setDisplayed] = useState(animated ? 0 : clamped);

  useEffect(() => {
    if (!animated) { setDisplayed(clamped); return; }
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

  const arcColor = getScoreColor(clamped);
  const fontSize = size === "sm" ? 18 : size === "md" ? 26 : 36;
  const labelSize = size === "sm" ? 9 : size === "md" ? 10 : 11;

  return (
    <div
      className={twMerge("relative flex flex-col items-center shrink-0", className)}
      style={{ width: w, height: h }}
      {...props}
    >
      <svg width={w} height={h} aria-hidden="true" overflow="visible">
        {/* Track arc — grey */}
        <path
          d={trackPath}
          fill="none"
          stroke="var(--border)"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        />

        {/* Filled arc — risk color */}
        {clamped > 0 && (
          <motion.path
            d={fillPath}
            fill="none"
            stroke={arcColor}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: 0.9, ease: [0.34, 1.1, 0.64, 1] }}
          />
        )}

        {/* Score number */}
        <text
          x={cx}
          y={cy - strokeWidth / 2}
          textAnchor="middle"
          dominantBaseline="middle"
          fill={arcColor}
          fontFamily="var(--font-mono), 'JetBrains Mono', monospace"
          fontSize={fontSize}
          fontWeight="600"
        >
          {displayed}
        </text>

        {/* Verdict label */}
        <text
          x={cx}
          y={cy + fontSize * 0.65}
          textAnchor="middle"
          dominantBaseline="middle"
          fill="var(--text-3)"
          fontFamily="var(--font-body), system-ui, sans-serif"
          fontSize={labelSize}
          fontWeight="500"
          letterSpacing="0.06em"
          style={{ textTransform: "uppercase" }}
        >
          {getVerdict(clamped)}
        </text>
      </svg>
    </div>
  );
};

export default RiskScore;
