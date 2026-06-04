"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, Eye } from "lucide-react";

interface CountUpProps {
  end: number;
  suffix?: string;
  duration?: number;
}

const CountUp = ({ end, suffix = "", duration = 1500 }: CountUpProps) => {
  const [count, setCount] = useState(0);

  useEffect(() => {
    let start = 0;
    const increment = end / (duration / 16); // ~60fps
    const timer = setInterval(() => {
      start += increment;
      if (start >= end) {
        setCount(end);
        clearInterval(timer);
      } else {
        setCount(Math.floor(start));
      }
    }, 16);

    return () => clearInterval(timer);
  }, [end, duration]);

  return <span>{count.toLocaleString()}{suffix}</span>;
};

export const Hero = () => {
  // Staggered child variants
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.15,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 24 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.8,
        ease: [0.16, 1, 0.3, 1] as const, // Premium easeOutExpo
      },
    },
  };

  return (
    <section className="relative flex flex-col items-center justify-center pt-24 pb-20 px-6 max-w-5xl mx-auto text-center z-10">
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="flex flex-col items-center"
      >
        {/* Upper Micro-Badge */}
        <motion.div
          variants={itemVariants}
          className="inline-flex items-center gap-1.5 rounded-full border border-accent-blue/20 bg-accent-blue/5 px-4 py-1.5 text-xs font-bold text-accent-blue uppercase tracking-wider mb-8"
        >
          <span className="h-1.5 w-1.5 rounded-full bg-accent-blue animate-pulse" />
          Enterprise Forensics Suite v1.2
        </motion.div>

        {/* Hero Headline */}
        <motion.h1
          variants={itemVariants}
          className="font-display text-5xl sm:text-7xl font-bold tracking-tight max-w-4xl leading-[1.05] text-text-primary"
        >
          Fraud Intelligence, <br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-accent-blue via-accent-blue to-accent-teal">
            Forensic Precision.
          </span>
        </motion.h1>

        {/* Hero Subheading */}
        <motion.p
          variants={itemVariants}
          className="mt-8 text-lg sm:text-xl text-text-secondary max-w-2xl font-medium leading-relaxed"
        >
          Expose metadata anomalies, scan spoofed URLs, and map connected threat clusters using automated image forensics, magic-byte checks, and AI pattern models.
        </motion.p>

        {/* CTA Buttons */}
        <motion.div
          variants={itemVariants}
          className="mt-10 flex flex-wrap justify-center gap-4"
        >
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-2 rounded-full bg-text-primary hover:bg-text-primary/95 text-white font-semibold px-8 py-4 shadow-lg shadow-text-primary/10 transition-transform hover:scale-[1.02] active:scale-[0.98] text-base"
          >
            Launch Core App
            <ArrowRight className="h-4 w-4" />
          </Link>
          <a
            href="#features"
            className="inline-flex items-center gap-2 rounded-full bg-surface hover:bg-white text-text-primary border border-border/80 font-semibold px-8 py-4 shadow-sm transition-transform hover:scale-[1.02] active:scale-[0.98] text-base"
          >
            <Eye className="h-4 w-4 text-text-secondary" />
            Explore Suite
          </a>
        </motion.div>

        {/* Trust Indicators Row */}
        <motion.div
          variants={itemVariants}
          className="mt-20 w-full border-t border-border/40 pt-10"
        >
          <div className="grid grid-cols-3 gap-6 max-w-3xl mx-auto">
            <div className="flex flex-col items-center">
              <span className="font-mono text-3xl sm:text-4xl font-bold text-text-primary">
                <CountUp end={85420} suffix="+" />
              </span>
              <span className="mt-1 text-[11px] font-bold text-text-secondary uppercase tracking-widest">
                Scans Analyzed
              </span>
            </div>
            <div className="flex flex-col items-center border-x border-border/40">
              <span className="font-mono text-3xl sm:text-4xl font-bold text-text-primary">
                <CountUp end={2810} suffix="+" />
              </span>
              <span className="mt-1 text-[11px] font-bold text-text-secondary uppercase tracking-widest">
                Threats Blocked
              </span>
            </div>
            <div className="flex flex-col items-center">
              <span className="font-mono text-3xl sm:text-4xl font-bold text-text-primary">
                <CountUp end={99} suffix=".9%" />
              </span>
              <span className="mt-1 text-[11px] font-bold text-text-secondary uppercase tracking-widest">
                Precision Rate
              </span>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </section>
  );
};

export default Hero;
