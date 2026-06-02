"use client";

import React, { useRef, useState } from "react";
import { Upload, FileText, X, AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";

interface UploadZoneProps {
  onFileAccepted: (file: File) => void;
  isLoading?: boolean;
  maxSizeMB?: number;
  allowedExtensions?: string[];
}

export const UploadZone: React.FC<UploadZoneProps> = ({
  onFileAccepted,
  isLoading = false,
  maxSizeMB = 15,
  allowedExtensions = [".pdf", ".png", ".jpg", ".jpeg"],
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragActive, setIsDragActive] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const validateFile = (file: File): boolean => {
    setErrorMessage(null);
    const suffix = "." + file.name.split(".").pop()?.toLowerCase();
    
    if (!allowedExtensions.includes(suffix)) {
      setErrorMessage(`Unsupported file extension. Allowed: ${allowedExtensions.join(", ")}`);
      return false;
    }

    if (file.size > maxSizeMB * 1024 * 1024) {
      setErrorMessage(`File exceeds maximum size of ${maxSizeMB}MB.`);
      return false;
    }

    return true;
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setIsDragActive(true);
    } else if (e.type === "dragleave") {
      setIsDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (validateFile(file)) {
        setSelectedFile(file);
        onFileAccepted(file);
      }
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (validateFile(file)) {
        setSelectedFile(file);
        onFileAccepted(file);
      }
    }
  };

  const onButtonClick = () => {
    fileInputRef.current?.click();
  };

  const clearFile = () => {
    setSelectedFile(null);
    setErrorMessage(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  return (
    <div className="w-full">
      <input
        ref={fileInputRef}
        type="file"
        className="hidden"
        accept={allowedExtensions.join(",")}
        onChange={handleFileChange}
        disabled={isLoading}
      />

      <div
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        className={cn(
          "relative flex flex-col items-center justify-center rounded-2xl border border-dashed p-10 text-center transition-all duration-300",
          isDragActive 
            ? "border-sky-500 bg-sky-50/40 ring-2 ring-sky-100" 
            : "border-slate-200 bg-slate-50/30 hover:border-slate-300 hover:bg-slate-50/50",
          isLoading && "pointer-events-none opacity-60"
        )}
      >
        <AnimatePresence mode="wait">
          {selectedFile ? (
            <motion.div
              key="file-details"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="flex flex-col items-center w-full"
            >
              <div className="rounded-2xl bg-sky-100/50 p-4 text-sky-600 border border-sky-200/50 shadow-sm">
                <FileText className="h-10 w-10" />
              </div>
              <p className="mt-4 font-semibold text-slate-800 break-all max-w-xs sm:max-w-md">
                {selectedFile.name}
              </p>
              <p className="text-xs font-medium text-slate-400 mt-1">
                {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
              </p>
              
              {!isLoading && (
                <button
                  type="button"
                  onClick={clearFile}
                  className="mt-4 inline-flex items-center gap-1.5 rounded-full bg-slate-100 hover:bg-slate-200 border border-slate-200/50 px-3 py-1 text-xs font-semibold text-slate-600 transition-colors"
                >
                  <X className="h-3.5 w-3.5" /> Remove file
                </button>
              )}
            </motion.div>
          ) : (
            <motion.div
              key="empty-upload"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex flex-col items-center cursor-pointer w-full"
              onClick={onButtonClick}
            >
              <div className="rounded-2xl bg-slate-100/50 p-4 text-slate-400 border border-slate-200/20 shadow-sm transition-transform hover:scale-105 duration-300">
                <Upload className="h-8 w-8 text-slate-500" />
              </div>
              <p className="mt-4 text-sm font-semibold text-slate-700">
                Drag and drop your file here, or{" "}
                <span className="text-sky-600 hover:text-sky-700 underline font-semibold transition-colors">
                  browse local files
                </span>
              </p>
              <p className="mt-2 text-xs font-medium text-slate-400">
                Accepted: {allowedExtensions.join(", ")} (max {maxSizeMB}MB)
              </p>
            </motion.div>
          )}
        </AnimatePresence>

        {isLoading && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-white/80 rounded-2xl backdrop-blur-sm z-10">
            <div className="relative flex items-center justify-center">
              <div className="h-12 w-12 rounded-full border-4 border-slate-100 border-t-sky-500 animate-spin" />
            </div>
            <p className="mt-4 text-xs font-bold text-slate-600 uppercase tracking-wider animate-pulse">
              Analyzing Forensic Fingerprints...
            </p>
          </div>
        )}
      </div>

      <AnimatePresence>
        {errorMessage && (
          <motion.div
            initial={{ opacity: 0, y: -5 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -5 }}
            className="mt-3 flex items-center gap-2 rounded-xl bg-rose-50 text-rose-700 border border-rose-100 p-3 text-xs font-semibold"
          >
            <AlertTriangle className="h-4 w-4 shrink-0" />
            <span>{errorMessage}</span>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default UploadZone;
