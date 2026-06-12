"use client";

import React from "react";
import { Settings, Info, FileText, ExternalLink } from "lucide-react";
import { GlassCard } from "@/components/ui/GlassCard";
import { motion } from "framer-motion";

export default function SettingsPage() {
  return (
    <div className="space-y-8 max-w-3xl">
      <div className="flex items-center gap-3">
        <div className="h-9 w-9 rounded-xl bg-[var(--color-surface-2)] flex items-center justify-center">
          <Settings className="h-5 w-5 text-[var(--color-text-muted)]" />
        </div>
        <div>
          <h1 className="text-h2 font-display text-[var(--color-text-primary)]">Settings</h1>
          <p className="text-[13px] text-[var(--color-text-muted)]">
            Platform information
          </p>
        </div>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35 }}
        className="space-y-4"
      >
        <GlassCard className="p-5">
          <div className="flex items-center gap-2 mb-4">
            <Info className="h-4 w-4 text-[var(--color-accent)]" />
            <h2 className="text-[14px] font-semibold text-[var(--color-text-primary)]">
              Platform Info
            </h2>
          </div>
          <div className="space-y-3">
            {[
              { label: "Version", value: "1.0" },
              { label: "AI Engine", value: "Groq · LLaMA 3.3 70B Versatile" },
              { label: "Backend", value: "FastAPI · Python 3.11" },
              { label: "Frontend", value: "Next.js 14 · App Router · TypeScript" },
              { label: "Database", value: "SQLAlchemy ORM" },
              { label: "License", value: "MIT" },
            ].map(({ label, value }) => (
              <div
                key={label}
                className="flex justify-between items-center py-2 border-b border-[var(--color-border)] last:border-0"
              >
                <span className="text-[13px] text-[var(--color-text-secondary)]">
                  {label}
                </span>
                <span className="font-mono text-[12px] text-[var(--color-text-primary)] bg-[var(--color-surface-2)] px-2 py-0.5 rounded">
                  {value}
                </span>
              </div>
            ))}
          </div>
        </GlassCard>

        <GlassCard className="p-5">
          <div className="flex items-center gap-2 mb-4">
            <FileText className="h-4 w-4 text-[var(--color-accent)]" />
            <h2 className="text-[14px] font-semibold text-[var(--color-text-primary)]">
              Resources
            </h2>
          </div>
          <p className="text-[13px] text-[var(--color-text-secondary)] leading-relaxed mb-4">
            Lumint is open source. Browse the source, read the documentation, or follow the project
            for updates.
          </p>
          <div className="flex flex-wrap gap-3">
            <a
              href="https://github.com/tanmay-alpha/Lumint"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 text-[13px] font-semibold text-[var(--color-accent)] hover:underline"
            >
              <ExternalLink className="h-4 w-4" />
              GitHub Repository
            </a>
            <a
              href="https://huggingface.co/tanmay-alpha"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 text-[13px] font-semibold text-[var(--color-accent)] hover:underline"
            >
              <FileText className="h-4 w-4" />
              HuggingFace
            </a>
          </div>
        </GlassCard>
      </motion.div>
    </div>
  );
}
