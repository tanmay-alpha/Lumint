"use client";

import React from "react";
import { motion } from "framer-motion";
import { twMerge } from "tailwind-merge";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "solid" | "outline" | "ghost" | "danger" | "intel";
  size?: "sm" | "md" | "lg";
  loading?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "solid", size = "md", loading, disabled, children, ...props }, ref) => {
    
    const baseClass = "inline-flex items-center justify-center font-medium rounded-lg text-body transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-brand disabled:opacity-50 disabled:pointer-events-none";

    const variantStyles = {
      solid: "bg-brand text-text-inverse hover:bg-brand-hover active:bg-brand-hover shadow-sm border border-transparent",
      outline: "bg-transparent border border-border-default text-text-primary hover:bg-surface-raised active:bg-surface-raised",
      ghost: "bg-transparent text-text-secondary hover:bg-surface-raised hover:text-text-primary",
      danger: "bg-danger text-text-inverse hover:bg-red-600 active:bg-red-700 shadow-sm border border-transparent",
      intel: "bg-intel text-text-inverse hover:bg-emerald-600 active:bg-emerald-700 shadow-sm border border-transparent",
    };

    const sizeStyles = {
      sm: "h-8 px-3.5 text-caption rounded-md",
      md: "h-10 px-5",
      lg: "h-12 px-6 text-[15px]",
    };

    return (
      <motion.button
        ref={ref}
        disabled={disabled || loading}
        whileTap={{ scale: 0.98 }}
        className={twMerge(
          baseClass,
          variantStyles[variant],
          sizeStyles[size],
          className
        )}
        {...(props as Record<string, unknown>)}
      >
        {loading ? (
          <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-current" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
        ) : null}
        {children}
      </motion.button>
    );
  }
);

Button.displayName = "Button";
export default Button;
