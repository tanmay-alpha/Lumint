"use client";

import React, { useCallback, useRef, useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { UploadCloud, X, File, Image as ImageIcon } from "lucide-react";
import { twMerge } from "tailwind-merge";

export interface UploadZoneProps {
  accept?: string;
  maxSizeMB?: number;
  label?: string;
  subLabel?: string;
  onFileSelected?: (file: File) => void;
  onFileAccepted?: (file: File) => void;
  disabled?: boolean;
  isLoading?: boolean;
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
  onFileAccepted,
  disabled = false,
  isLoading = false,
  progress = 0,
  className,
}: UploadZoneProps) => {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [selected, setSelected] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [thumbUrl, setThumbUrl] = useState<string | null>(null);

  // Manage object URL for image preview
  useEffect(() => {
    if (!selected) {
      setThumbUrl(null);
      return;
    }
    if (selected.type.startsWith("image/")) {
      const url = URL.createObjectURL(selected);
      setThumbUrl(url);
      return () => {
        URL.revokeObjectURL(url);
      };
    }
  }, [selected]);

  const handleFile = useCallback(
    (file: File) => {
      setError(null);
      if (file.size > maxSizeMB * 1024 * 1024) {
        setError(`File exceeds ${maxSizeMB} MB limit.`);
        return;
      }
      setSelected(file);
      if (onFileSelected) onFileSelected(file);
      if (onFileAccepted) onFileAccepted(file);
    },
    [maxSizeMB, onFileSelected, onFileAccepted]
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
        onClick={() => !disabled && !isLoading && inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          if (!disabled && !isLoading) setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={onDrop}
        animate={isDragging ? { scale: 1.01 } : { scale: 1 }}
        transition={{ type: "spring", stiffness: 400, damping: 30 }}
        className={twMerge(
          "relative flex flex-col items-center justify-center gap-3 rounded-[var(--r-3)] cursor-pointer transition-all duration-200 min-h-[190px] p-6 text-center group",
          isDragging
            ? "border-2 border-solid border-[var(--brand)] bg-[var(--brand-muted)]/35 dark:bg-[var(--brand-muted)]/20"
            : selected
            ? "border-2 border-dashed border-[var(--border-2)] bg-[var(--surface-raised)]"
            : "border-2 border-dashed border-[var(--border-2)] bg-[var(--surface)] hover:border-[var(--brand)] hover:bg-[var(--surface-raised)]",
          (disabled || isLoading) && "opacity-50 cursor-not-allowed"
        )}
      >
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          onChange={onInputChange}
          className="sr-only"
          disabled={disabled || isLoading}
        />

        {isLoading && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-[var(--surface)]/80 rounded-[var(--r-3)] backdrop-blur-[2px] z-10">
            <div className="relative flex items-center justify-center">
              <div className="h-10 w-10 rounded-full border-4 border-[var(--border)] border-t-[var(--brand)] animate-spin" />
            </div>
            <p className="mt-4 text-[11px] font-bold text-[var(--text-2)] uppercase tracking-wider animate-pulse font-sans">
              Analyzing Forensic Fingerprints...
            </p>
          </div>
        )}

        <AnimatePresence mode="wait">
          {selected ? (
            <motion.div
              key="selected"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="flex flex-col items-center gap-2.5 w-full"
            >
              {/* Thumbnail / Icon */}
              {isImage && thumbUrl ? (
                <div className="relative group/thumb shadow-md rounded-lg overflow-hidden border border-[var(--border-2)]">
                  <img
                    src={thumbUrl}
                    alt="Uploaded screenshot preview"
                    className="h-24 w-18 object-cover transition-transform duration-200 group-hover/thumb:scale-105"
                  />
                </div>
              ) : (
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[var(--brand-muted)]/30 text-[var(--brand)]">
                  {isImage ? <ImageIcon className="h-6 w-6" /> : <File className="h-6 w-6" />}
                </div>
              )}

              {/* File name + size */}
              <div className="flex flex-col items-center gap-0.5">
                <span className="font-mono text-[12px] font-semibold text-[var(--text-1)] break-all max-w-[280px]">
                  {selected.name}
                </span>
                <span className="text-[11px] text-[var(--text-3)] font-mono">
                  {formatBytes(selected.size)}
                </span>
              </div>

              {/* Remove button */}
              <button
                onClick={clearFile}
                className="flex items-center gap-1 text-[11px] text-[var(--high)] hover:underline mt-1 font-medium"
              >
                <X className="h-3.5 w-3.5" /> Remove file
              </button>
            </motion.div>
          ) : (
            <motion.div
              key="empty"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex flex-col items-center gap-2.5"
            >
              <motion.div
                animate={isDragging ? { y: -3 } : { y: 0 }}
                className="flex h-12 w-12 items-center justify-center rounded-xl bg-[var(--surface-3)] text-[var(--text-3)] group-hover:text-[var(--text-2)] transition-colors duration-200"
              >
                <UploadCloud className="h-7 w-7 transition-transform duration-200 group-hover:scale-105" />
              </motion.div>
              <div className="flex flex-col gap-1">
                <span className="text-[14px] font-semibold text-[var(--text-2)] group-hover:text-[var(--text-1)] transition-colors duration-200">
                  {label}
                </span>
                <span className="text-[11px] text-[var(--text-4)]">
                  {defaultSubLabel}
                </span>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      {/* Progress bar */}
      {progress > 0 && progress < 100 && (
        <div className="mt-3 h-1.5 w-full bg-[var(--surface-3)] rounded-full overflow-hidden border border-[var(--border)]">
          <motion.div
            className="h-full bg-[var(--brand)] rounded-full"
            initial={{ width: "0%" }}
            animate={{ width: `${progress}%` }}
            transition={{ ease: "easeOut" }}
          />
        </div>
      )}

      {/* Error */}
      {error && (
        <p className="mt-2 text-[12px] text-[var(--high)] font-semibold">{error}</p>
      )}
    </div>
  );
};

export default UploadZone;
