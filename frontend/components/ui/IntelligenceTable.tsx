"use client";

import React, { useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { twMerge } from "tailwind-merge";

export interface Column<T> {
  header: string;
  accessorKey: keyof T | string;
  cell?: (item: T) => React.ReactNode;
  align?: "left" | "center" | "right";
  className?: string;
}

export interface IntelligenceTableProps<T> {
  data: T[];
  columns: Column<T>[];
  keyExtractor: (item: T) => string | number;
  onRowClick?: (item: T) => void;
  isLoading?: boolean;
  emptyMessage?: string;
  className?: string;
  renderExpandedRow?: (item: T) => React.ReactNode;
}

export function IntelligenceTable<T>({
  data,
  columns,
  keyExtractor,
  onRowClick,
  isLoading = false,
  emptyMessage = "No matching threat intelligence records found.",
  className,
  renderExpandedRow,
}: IntelligenceTableProps<T>) {
  const [expandedKeys, setExpandedKeys] = useState<Set<string | number>>(new Set());

  const toggleExpand = (key: string | number, e: React.MouseEvent) => {
    e.stopPropagation();
    const next = new Set(expandedKeys);
    if (next.has(key)) {
      next.delete(key);
    } else {
      next.add(key);
    }
    setExpandedKeys(next);
  };

  const hasExpand = typeof renderExpandedRow === "function";

  return (
    <div className={twMerge("w-full overflow-hidden border border-border-default bg-surface rounded-xl shadow-sm", className)}>
      <div className="w-full overflow-x-auto">
        <table className="w-full border-collapse text-left">
          <thead>
            <tr className="border-b border-border-default bg-surface-raised/50 select-none">
              {hasExpand && <th className="w-10 px-4 py-3.5" />}
              {columns.map((col, idx) => (
                <th
                  key={idx}
                  className={twMerge(
                    "px-4.5 py-3.5 text-label text-text-secondary font-semibold uppercase tracking-wider text-[11px] whitespace-nowrap",
                    col.align === "center" && "text-center",
                    col.align === "right" && "text-right",
                    col.className
                  )}
                >
                  {col.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-border-muted">
            {isLoading ? (
              Array.from({ length: 5 }).map((_, rIdx) => (
                <tr key={rIdx} className="animate-pulse">
                  {hasExpand && (
                    <td className="px-4 py-4 w-10">
                      <div className="h-4 bg-border-muted rounded w-4" />
                    </td>
                  )}
                  {columns.map((_, cIdx) => (
                    <td key={cIdx} className="px-4.5 py-4">
                      <div className="h-4 bg-border-muted rounded w-2/3" />
                    </td>
                  ))}
                </tr>
              ))
            ) : data.length === 0 ? (
              <tr>
                <td colSpan={columns.length + (hasExpand ? 1 : 0)} className="px-4.5 py-12 text-center text-body text-text-muted">
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              data.map((item) => {
                const key = keyExtractor(item);
                const isExpanded = expandedKeys.has(key);

                return (
                  <React.Fragment key={key}>
                    <tr
                      onClick={() => onRowClick && onRowClick(item)}
                      className={twMerge(
                        "transition-colors duration-150 group",
                        onRowClick ? "cursor-pointer hover:bg-surface-raised/50" : "hover:bg-surface-raised/20",
                        isExpanded && "bg-surface-raised/35"
                      )}
                    >
                      {hasExpand && (
                        <td className="px-4 py-3.5 text-center w-10 select-none">
                          <button
                            onClick={(e) => toggleExpand(key, e)}
                            className="text-text-muted hover:text-text-primary transition-colors focus:outline-none"
                          >
                            {isExpanded ? (
                              <ChevronUp className="h-4 w-4 stroke-[2.5]" />
                            ) : (
                              <ChevronDown className="h-4 w-4 stroke-[2.5]" />
                            )}
                          </button>
                        </td>
                      )}
                      {columns.map((col, cIdx) => {
                        const value = typeof item === "object" && item !== null && col.accessorKey in (item as any) 
                          ? (item as any)[col.accessorKey] 
                          : null;
                        return (
                          <td
                            key={cIdx}
                            className={twMerge(
                              "px-4.5 py-3.5 text-body text-text-primary",
                              col.align === "center" && "text-center",
                              col.align === "right" && "text-right",
                              col.className
                            )}
                          >
                            {col.cell ? col.cell(item) : (
                              <span className="font-sans">
                                {value !== null && value !== undefined ? String(value) : "—"}
                              </span>
                            )}
                          </td>
                        );
                      })}
                    </tr>

                    {/* Expandable subrow */}
                    {hasExpand && (
                      <AnimatePresence>
                        {isExpanded && (
                          <tr>
                            <td colSpan={columns.length + 1} className="bg-surface-raised/20 p-0 border-b border-border-muted">
                              <motion.div
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: "auto" }}
                                exit={{ opacity: 0, height: 0 }}
                                transition={{ duration: 0.2 }}
                                className="overflow-hidden"
                              >
                                {renderExpandedRow(item)}
                              </motion.div>
                            </td>
                          </tr>
                        )}
                      </AnimatePresence>
                    )}
                  </React.Fragment>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default IntelligenceTable;
