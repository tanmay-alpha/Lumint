"use client";

import React from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface GlassCardProps extends React.ComponentPropsWithoutRef<typeof motion.div> {
  hoverEffect?: boolean;
  tiltEffect?: boolean;
  delay?: number;
}

export const GlassCard: React.FC<GlassCardProps> = ({
  children,
  hoverEffect = true,
  tiltEffect = false,
  className,
  delay = 0,
  ...props
}) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ 
        duration: 0.5, 
        ease: [0.16, 1, 0.3, 1], // Apple-like easeOutExpo
        delay 
      }}
      whileHover={hoverEffect ? { 
        y: -4, 
        boxShadow: "0 20px 40px rgba(0, 0, 0, 0.04)", 
        borderColor: "rgba(0, 0, 0, 0.08)" 
      } : undefined}
      className={cn(
        "rounded-2xl border border-white/70 bg-white/65 p-6 backdrop-blur-xl transition-all duration-300 shadow-[0_8px_30px_rgb(0,0,0,0.02)]",
        className
      )}
      {...props}
    >
      {children}
    </motion.div>
  );
};
export default GlassCard;
