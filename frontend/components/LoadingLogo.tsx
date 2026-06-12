"use client";
import { motion } from "framer-motion";

export function LoadingLogo() {
  return (
    <div className="flex flex-col items-center justify-center gap-8">
      <motion.svg
        width="100"
        height="100"
        viewBox="0 0 100 100"
        initial="hidden"
        animate="visible"
      >
        <motion.polygon
          points="50,5 95,30 95,70 50,95 5,70 5,30"
          fill="none"
          stroke="#1F2937"
          strokeWidth="1"
          variants={{
            hidden: { pathLength: 0 },
            visible: {
              pathLength: 1,
              transition: {
                duration: 2,
                ease: "easeInOut",
                repeat: Infinity,
                repeatType: "reverse",
              },
            },
          }}
        />
        <motion.polygon
          points="50,5 95,30 95,70 50,95 5,70 5,30"
          fill="none"
          stroke="#DC2626"
          strokeWidth="2"
          filter="url(#glow)"
          variants={{
            hidden: { pathLength: 0, opacity: 0 },
            visible: {
              pathLength: 1,
              opacity: [0, 1, 1, 0],
              transition: {
                pathLength: {
                  duration: 2.5,
                  ease: "easeInOut",
                  repeat: Infinity,
                  repeatType: "reverse",
                },
                opacity: {
                  duration: 2.5,
                  times: [0, 0.1, 0.9, 1],
                  repeat: Infinity,
                  repeatType: "reverse",
                },
              },
            },
          }}
        />
        <defs>
          <filter id="glow">
            <feGaussianBlur stdDeviation="2" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
      </motion.svg>

      <motion.div
        className="text-sm tracking-[0.3em] text-text-secondary"
        initial={{ opacity: 0 }}
        animate={{ opacity: [0.3, 0.7, 0.3] }}
        transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
      >
        LUMINT
      </motion.div>
    </div>
  );
}
