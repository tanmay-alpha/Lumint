"use client";

import React from "react";
import { twMerge } from "tailwind-merge";
import { motion } from "framer-motion";

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "elevated" | "inset" | "ai";
  interactive?: boolean;
  children?: React.ReactNode;
  className?: string;
}

const variantBase: Record<string, string> = {
  default:  "bg-[var(--surface)] border border-[var(--border)] rounded-[var(--r-3)] shadow-[var(--shadow-1)]",
  elevated: "bg-[var(--surface)] border border-[var(--border)] rounded-[var(--r-3)] shadow-[var(--shadow-3)] transition-[box-shadow,transform] duration-[80ms] ease-out hover:shadow-[var(--shadow-4)] hover:-translate-y-px",
  inset:    "bg-[var(--surface-3)] border border-[var(--border-2)] rounded-[var(--r-3)]",
  ai:       "bg-[var(--ai-muted)] border-[1.5px] border-dashed border-[var(--ai-border)] rounded-[var(--r-3)]",
};

export const Card = ({
  variant = "default",
  interactive = false,
  children,
  className,
  ...props
}: CardProps) => {
  const base = variantBase[variant];

  if (interactive && variant === "elevated") {
    return (
      <motion.div
        className={twMerge("relative overflow-hidden", base, className)}
        whileHover={{ y: -1 }}
        transition={{ duration: 0.08, ease: "easeOut" }}
        {...(props as React.ComponentPropsWithoutRef<typeof motion.div>)}
      >
        {children}
      </motion.div>
    );
  }

  return (
    <div className={twMerge("relative overflow-hidden", base, className)} {...props}>
      {children}
    </div>
  );
};

export default Card;
