"use client";

import React, { useCallback, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { UploadCloud, X, File, Image as ImageIcon } from "lucide-react";
import { twMerge } from "tailwind-merge";

export interface UploadZoneProps {
  accept?: string;
  maxSizeMB?: number;
  label?: string;
  subLabel?: string;
  onFileSelected: (file: File) => void;
  disabled?: boolean;
  progress?: number; // 0–100, shows progress bar when > 0
  className?: string;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1048576).toFixed(2)} MB`;
}

export const UploadZone = ({
  accept = ".pdf,.png,.jpg,.jpeg",
  maxSizeMB = 10,
  label = "Drop file here or click to browse",
  subLabel,
  onFileSelected,
  disabled = false,
  progress = 0,
  className,
}: UploadZoneProps) => {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [selected, setSelected] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFile = useCallback(
    (file: File) => {
      setError(null);
      if (file.size > maxSizeMB * 1024 * 1024) {
        setError(`File exceeds ${maxSizeMB} MB limit.`);
        return;
      }
      setSelected(file);
      onFileSelected(file);
    },
    [maxSizeMB, onFileSelected]
  );

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (disabled) return;
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  const onInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  const clearFile = (e: React.MouseEvent) => {
    e.stopPropagation();
    setSelected(null);
    setError(null);
    if (inputRef.current) inputRef.current.value = "";
  };

  const isImage = selected?.type.startsWith("image/");
  const defaultSubLabel = subLabel ?? `Accepted: ${accept} · Max ${maxSizeMB} MB`;

  return (
    <div className={twMerge("w-full", className)}>
      <motion.div
        onClick={() => !disabled && inputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); if (!disabled) setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={onDrop}
        animate={isDragging ? { scale: 1.02 } : { scale: 1 }}
        transition={{ type: "spring", stiffness: 400, damping: 30 }}
        className={twMerge(
          "relative flex flex-col items-center justify-center gap-3 rounded-[16px] border-2 border-dashed",
          "cursor-pointer transition-all duration-200 min-h-[180px] p-8 text-center",
          isDragging
             ? "border-[var(--color-accent)] bg-[var(--color-accent-subtle)]"
             : selected
             ? "border-[var(--color-border-strong)] bg-[var(--color-surface)]"
             : "border-[var(--color-border)] bg-[var(--color-surface)] hover:border-[var(--color-accent)] hover:bg-[var(--color-accent-subtle)]",
          disabled && "opacity-50 cursor-not-allowed"
        )}
      >
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          onChange={onInputChange}
          className="sr-only"
          disabled={disabled}
        />

        <AnimatePresence mode="wait">
          {selected ? (
            <motion.div
              key="selected"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="flex flex-col items-center gap-3 w-full"
            >
              {/* Icon */}
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[var(--color-accent-subtle)] text-[var(--color-accent)]">
                {isImage ? <ImageIcon className="h-6 w-6" /> : <File className="h-6 w-6" />}
              </div>

              {/* File name + size */}
              <div className="flex flex-col items-center gap-1">
                <span className="font-mono text-[13px] text-[var(--color-text-primary)] break-all max-w-[280px]">
                  {selected.name}
                </span>
                <span className="text-[11px] text-[var(--color-text-muted)]">
                  {formatBytes(selected.size)}
                </span>
              </div>

              {/* Remove button */}
              <button
                onClick={clearFile}
                className="flex items-center gap-1 text-[11px] text-[var(--color-danger)] hover:underline"
              >
                <X className="h-3 w-3" /> Remove
              </button>
            </motion.div>
          ) : (
            <motion.div
              key="empty"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex flex-col items-center gap-3"
            >
              <motion.div
                animate={isDragging ? { y: -4 } : { y: 0 }}
                className="flex h-14 w-14 items-center justify-center rounded-2xl bg-[var(--color-accent-subtle)] text-[var(--color-accent)]"
              >
                <UploadCloud className="h-7 w-7" />
              </motion.div>
              <div className="flex flex-col gap-1">
                <span className="text-[15px] font-medium text-[var(--color-text-secondary)]">
                  {label}
                </span>
                <span className="text-[12px] text-[var(--color-text-muted)]">
                  {defaultSubLabel}
                </span>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      {/* Progress bar */}
      {progress > 0 && progress < 100 && (
        <div className="mt-3 progress-track">
          <motion.div
            className="progress-fill"
            initial={{ width: "0%" }}
            animate={{ width: `${progress}%` }}
            transition={{ ease: "easeOut" }}
          />
        </div>
      )}

      {/* Error */}
      {error && (
        <p className="mt-2 text-[12px] text-[var(--color-danger)]">{error}</p>
      )}
    </div>
  );
};

export default UploadZone;
