"use client";

import React from "react";
import { motion } from "framer-motion";
import { Smartphone } from "lucide-react";
import type { Variants } from "framer-motion";

// ─── HeroPanel ────────────────────────────────────────────────────────────
//
// Page header for /upi-shield: brand chip + page title + tagline.
// Pure presentational — no state. The framer-motion `useReducedMotion`
// variants are owned by the parent page so a single instance of the hook
// drives the entire page's motion budget.
export interface HeroPanelProps {
  containerVariants: Variants;
  itemVariants: Variants;
}

export function HeroPanel({ containerVariants, itemVariants }: HeroPanelProps) {
  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={containerVariants}
      className="space-y-1"
    >
      <motion.div variants={itemVariants} className="flex items-center gap-2.5">
        <div className="h-9 w-9 rounded-xl bg-[var(--brand-muted)] flex items-center justify-center shadow-sm">
          <Smartphone className="h-5 w-5 text-[var(--brand)]" />
        </div>
        <div>
          <h1 className="text-[20px] font-bold text-[var(--text-1)]">
            UPI Shield
          </h1>
          <p className="text-[12px] text-[var(--text-3)] font-semibold">
            Detect fake PhonePe, Google Pay &amp; Paytm payment screenshots
          </p>
        </div>
      </motion.div>
    </motion.div>
  );
}

export default HeroPanel;