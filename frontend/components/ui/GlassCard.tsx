"use client";

import React from "react";
import { motion } from "framer-motion";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export interface GlassCardProps extends React.ComponentPropsWithoutRef<typeof motion.div> {
  children?: React.ReactNode;
  className?: string;
  elevated?: boolean;
}

export const GlassCard = ({
  children,
  className,
  elevated = false,
  ...props
}: GlassCardProps) => {
  return (
    <motion.div
      className={twMerge(
        "rounded-[16px] border border-[rgba(255,255,255,0.6)] bg-[rgba(255,255,255,0.72)] p-6 backdrop-blur-[12px] backdrop-saturate-[160%] transition-shadow duration-300",
        elevated
          ? "shadow-[0_12px_40px_rgba(0,0,0,0.12),0_2px_4px_rgba(0,0,0,0.06)]"
          : "shadow-[0_4px_24px_rgba(0,0,0,0.06),0_1px_2px_rgba(0,0,0,0.04)]",
        className
      )}
      whileHover={
        elevated
          ? { y: -4, boxShadow: "0 20px 48px rgba(0,0,0,0.16), 0 4px 12px rgba(0,0,0,0.08)" }
          : undefined
      }
      {...props}
    >
      {children}
    </motion.div>
  );
};

export default GlassCard;
