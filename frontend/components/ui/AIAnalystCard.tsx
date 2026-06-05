"use client";

import React from "react";
import { AIInsightCard, AIInsightCardProps } from "./AIInsightCard";

export type AIAnalystCardProps = AIInsightCardProps;

export const AIAnalystCard = (props: AIAnalystCardProps) => {
  return <AIInsightCard {...props} />;
};

export default AIAnalystCard;
