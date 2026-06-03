"use client";

import React from "react";
import { twMerge } from "tailwind-merge";

export type SkeletonVariant =
  | "text-sm"
  | "text-md"
  | "text-lg"
  | "circle"
  | "rect"
  | "ring"
  | "card";

export interface SkeletonLoaderProps {
  variant?: SkeletonVariant;
  size?: number;           // For circle / ring
  width?: number | string; // For rect
  height?: number | string;// For rect
  className?: string;
}

export const SkeletonLoader = ({
  variant = "text-md",
  size = 64,
  width,
  height,
  className,
}: SkeletonLoaderProps) => {
  if (variant === "card") {
    return (
      <span
        className={twMerge("shimmer rounded-[16px] block", className)}
        style={{ width: width ?? "100%", height: height ?? 140 }}
        aria-hidden="true"
      />
    );
  }

  if (variant === "circle") {
    return (
      <span
        className={twMerge("shimmer rounded-full block shrink-0", className)}
        style={{ width: size, height: size }}
        aria-hidden="true"
      />
    );
  }

  if (variant === "ring") {
    return (
      <span
        className={twMerge("shimmer rounded-full block shrink-0", className)}
        style={{ width: size, height: size }}
        aria-hidden="true"
      />
    );
  }

  if (variant === "rect") {
    return (
      <span
        className={twMerge("shimmer rounded-[8px] block", className)}
        style={{
          width: width ?? "100%",
          height: height ?? 80,
        }}
        aria-hidden="true"
      />
    );
  }

  const heightMap = { "text-sm": "h-3", "text-md": "h-4", "text-lg": "h-6" };

  return (
    <span
      className={twMerge(
        "shimmer block rounded-[4px] w-full",
        heightMap[variant as "text-sm" | "text-md" | "text-lg"],
        className
      )}
      aria-hidden="true"
    />
  );
};

export default SkeletonLoader;
