"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Shield, Menu, X, ArrowRight } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export const NavBar = () => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border/40 bg-surface/80 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        {/* Brand Logo */}
        <Link href="/" className="flex items-center gap-2.5 group">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-text-primary text-white shadow-md transition-transform group-hover:scale-105">
            <Shield className="h-5 w-5 stroke-[1.75]" />
          </div>
          <span className="font-display text-2xl font-bold tracking-wide text-text-primary">
            Sentinel<span className="text-accent-blue">X</span>
          </span>
        </Link>

        {/* Desktop Navigation */}
        <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-text-secondary">
          <a href="#features" className="hover:text-text-primary transition-colors">Forensic Suite</a>
          <a href="#metrics" className="hover:text-text-primary transition-colors">Platform Metrics</a>
          <a href="https://github.com/tanmay-alpha/Fraud-Intelligence" target="_blank" rel="noopener noreferrer" className="hover:text-text-primary transition-colors">GitHub</a>
        </nav>

        {/* CTA Button */}
        <div className="hidden md:block">
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-1.5 rounded-full bg-accent-blue/10 hover:bg-accent-blue/15 px-5 py-2 text-sm font-semibold text-accent-blue shadow-sm border border-accent-blue/20 transition-all hover:scale-[1.02] active:scale-[0.98]"
          >
            Launch App
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>

        {/* Mobile Menu Toggle */}
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="flex h-9 w-9 items-center justify-center rounded-lg border border-border/60 bg-surface/50 text-text-primary md:hidden hover:bg-surface transition-colors"
          aria-label="Toggle menu"
        >
          {isOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {/* Mobile Menu Panel */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
            className="border-b border-border/40 bg-surface/95 backdrop-blur-lg md:hidden overflow-hidden"
          >
            <div className="flex flex-col gap-4 px-6 py-6 font-medium">
              <a
                href="#features"
                onClick={() => setIsOpen(false)}
                className="text-text-secondary hover:text-text-primary transition-colors"
              >
                Forensic Suite
              </a>
              <a
                href="#metrics"
                onClick={() => setIsOpen(false)}
                className="text-text-secondary hover:text-text-primary transition-colors"
              >
                Platform Metrics
              </a>
              <a
                href="https://github.com/tanmay-alpha/Fraud-Intelligence"
                target="_blank"
                rel="noopener noreferrer"
                className="text-text-secondary hover:text-text-primary transition-colors"
              >
                GitHub
              </a>
              <hr className="border-border/40 my-1" />
              <Link
                href="/dashboard"
                onClick={() => setIsOpen(false)}
                className="inline-flex items-center justify-center gap-1.5 rounded-full bg-accent-blue px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-accent-blue/90 transition-all text-center"
              >
                Launch App
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
};

export default NavBar;
