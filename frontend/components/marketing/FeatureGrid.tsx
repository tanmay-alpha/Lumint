"use client";

import React from "react";
import { GlassCard } from "../ui/GlassCard";
import { ShieldAlert, Network, Fingerprint } from "lucide-react";
import { motion } from "framer-motion";

export const FeatureGrid = () => {
  const features = [
    {
      title: "DocShield",
      tagline: "File Structure Inspection",
      description:
        "Perform deep binary analysis on uploaded images and PDFs. Expose hidden Photoshop or graphical signatures, highlight Error Level Analysis (ELA) anomalies, and flag modified fields.",
      icon: ShieldAlert,
      color: "text-accent-blue",
      bgColor: "bg-accent-blue/10",
      accent: "from-accent-blue/20 to-transparent",
    },
    {
      title: "PhishShield",
      tagline: "Domain & URL Defense",
      description:
        "Evaluate incoming hyperlinks against known domain vectors. SentinelX flags typosquatting lookalikes, assesses character entropy patterns, and alerts users of credential theft landing zones.",
      icon: Network,
      color: "text-accent-teal",
      bgColor: "bg-accent-teal/10",
      accent: "from-accent-teal/20 to-transparent",
    },
    {
      title: "Fraud DNA",
      tagline: "Threat Connection Mapping",
      description:
        "Compile metadata fingerprints across events. Map matching document authors, creation software versions, or templates to reveal coordinated campaigns and recurring adversary nodes.",
      icon: Fingerprint,
      color: "text-risk-critical",
      bgColor: "bg-risk-critical/10",
      accent: "from-risk-critical/20 to-transparent",
    },
  ];

  return (
    <section id="features" className="py-24 px-6 max-w-7xl mx-auto z-10 relative">
      <div className="text-center max-w-2xl mx-auto mb-16">
        <h2 className="font-display text-4xl sm:text-5xl font-bold text-text-primary">
          Engineered for Forensic Clarity.
        </h2>
        <p className="mt-4 text-text-secondary font-medium">
          Three specialized subsystems running inside a unified execution sandbox to identify, score, and link digital threats.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {features.map((feature, idx) => (
          <motion.div
            key={feature.title}
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: idx * 0.1, ease: [0.16, 1, 0.3, 1] }}
          >
            <GlassCard className="h-full flex flex-col justify-between overflow-hidden relative group hover:shadow-xl transition-all border-border/80">
              {/* Top Accent Gradient Line */}
              <div className={`absolute top-0 left-0 w-full h-[3px] bg-gradient-to-r ${feature.accent}`} />

              <div>
                {/* Feature Icon */}
                <div className={`inline-flex h-12 w-12 items-center justify-center rounded-xl ${feature.bgColor} ${feature.color} mb-6`}>
                  <feature.icon className="h-6 w-6" />
                </div>

                {/* Tags and Labels */}
                <div className="text-[11px] font-bold text-accent-blue/80 uppercase tracking-widest mb-1.5 font-mono">
                  {feature.tagline}
                </div>

                {/* Feature Title */}
                <h3 className="text-2xl font-bold text-text-primary tracking-tight mb-3">
                  {feature.title}
                </h3>

                {/* Description */}
                <p className="text-sm leading-relaxed text-text-secondary">
                  {feature.description}
                </p>
              </div>

              {/* Sub-Feature Bullets */}
              <div className="mt-8 pt-6 border-t border-border/40 grid grid-cols-2 gap-3 text-xs font-semibold text-text-primary/80">
                <span className="flex items-center gap-1.5">
                  <span className="h-1.5 w-1.5 rounded-full bg-accent-blue" />
                  Auto-Parsing
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="h-1.5 w-1.5 rounded-full bg-accent-blue" />
                  Realtime Alert
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="h-1.5 w-1.5 rounded-full bg-accent-blue" />
                  API Access
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="h-1.5 w-1.5 rounded-full bg-accent-blue" />
                  SHA-256 Hashes
                </span>
              </div>
            </GlassCard>
          </motion.div>
        ))}
      </div>
    </section>
  );
};

export default FeatureGrid;
