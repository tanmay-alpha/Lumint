"use client";

import React from "react";
import { AIInsightCard, AIInsightCardProps } from "./AIInsightCard";

export interface AIAnalystCardProps extends AIInsightCardProps {}

export const AIAnalystCard = (props: AIAnalystCardProps) => {
  return <AIInsightCard {...props} />;
};

export default AIAnalystCard;
