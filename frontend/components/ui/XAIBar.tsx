"use client";

import React from "react";
import { FeatureBar, FeatureBarContribution } from "./FeatureBar";

export type XAIBarFeature = FeatureBarContribution;
export interface XAIBarProps {
  features: XAIBarFeature[];
  title?: string;
  className?: string;
}

export const XAIBar = ({ features, title, className }: XAIBarProps) => {
  return (
    <FeatureBar
      features={features}
      title={title}
      className={className}
    />
  );
};

export default XAIBar;
