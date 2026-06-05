"use client";

import React from "react";
import { motion } from "framer-motion";
import { twMerge } from "tailwind-merge";

export interface DataCardProps extends React.ComponentPropsWithoutRef<typeof motion.div> {
  children?: React.ReactNode;
  className?: string;
  variant?: "flat" | "raised" | "overlay";
  withPattern?: boolean;
  interactive?: boolean;
}

export const DataCard = ({
  children,
  className,
  variant = "raised",
  withPattern = false,
  interactive = true,
  ...props
}: DataCardProps) => {
  const baseClass = "rounded-xl border relative overflow-hidden transition-colors duration-200";
  
  // Style mapping based on theme variables
  const variantStyles = {
    flat: "bg-transparent border-border-muted shadow-none",
    raised: "bg-surface border-border-default shadow-sm hover:shadow-md",
    overlay: "bg-surface-overlay backdrop-blur-md border-border-strong shadow-lg",
  };

  return (
    <motion.div
      className={twMerge(
        baseClass,
        variantStyles[variant],
        className
      )}
      whileHover={interactive ? {
        y: -2,
        borderColor: "var(--border-strong)",
        transition: { duration: 0.15, ease: "easeOut" }
      } : undefined}
      {...props}
    >
      {/* Subtle background grid pattern if enabled */}
      {withPattern && (
        <div className="absolute inset-0 mesh-grid-bg opacity-[0.03] pointer-events-none" />
      )}
      
      {/* Decorative top border highlight */}
      <div className="absolute top-0 inset-x-0 h-[1.5px] bg-gradient-to-r from-brand/20 via-transparent to-brand/10 opacity-30" />
      
      <div className="relative z-10 p-6">
        {children}
      </div>
    </motion.div>
  );
};

export default DataCard;
