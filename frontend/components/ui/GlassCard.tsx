"use client";

import React from "react";
import { motion } from "framer-motion";
import { twMerge } from "tailwind-merge";

export interface GlassCardProps extends React.ComponentPropsWithoutRef<typeof motion.div> {
  children?: React.ReactNode;
  className?: string;
  elevated?: boolean;
  glass?: boolean;
}

export const GlassCard = ({
  children,
  className,
  elevated = false,
  glass = false,
  ...props
}: GlassCardProps) => {
  const baseClass = glass
    ? [
        "rounded-[16px] p-6 transition-shadow duration-300",
        "bg-[rgba(255,255,255,0.72)] backdrop-blur-[12px] backdrop-saturate-[160%]",
        "border border-[rgba(255,255,255,0.6)]",
      ].join(" ")
    : [
        "rounded-[16px] p-6 transition-shadow duration-300",
        "bg-[var(--color-surface)] border border-[var(--color-border)]",
      ].join(" ");

  const shadowClass = elevated
    ? "shadow-[0_4px_16px_rgba(0,0,0,0.08),0_1px_4px_rgba(0,0,0,0.04)]"
    : "shadow-[0_1px_3px_rgba(0,0,0,0.06),0_1px_2px_rgba(0,0,0,0.04)]";

  return (
    <motion.div
      className={twMerge(baseClass, shadowClass, className)}
      whileHover={{
        y: -2,
        boxShadow: "0 4px 16px rgba(0,0,0,0.10), 0 2px 6px rgba(0,0,0,0.06)",
        borderColor: "var(--color-border-strong)",
      }}
      transition={{ type: "spring", stiffness: 300, damping: 25 }}
      {...props}
    >
      {children}
    </motion.div>
  );
};

export default GlassCard;
