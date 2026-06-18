import { DocumentAnalysisResult } from "../types";
import { apiBaseUrl } from "../config";
import Tesseract from "tesseract.js";

/**
 * Run Tesseract.js in the browser to extract text from an image.
 *
 * The backend has no Tesseract binary in its container, so for image
 * uploads it cannot perform OCR itself. We run the same Tesseract.js
 * pipeline UPI Shield already uses and post the extracted text back as
 * a `text` form field — the backend's keyword scanner then flags scam
 * phrases like "KYC expiry", "click here to verify", etc.
 *
 * Returns an empty string if the file isn't an image or if OCR fails.
 * Never throws — the backend will simply skip the keyword check.
 */
async function ocrImageForDocShield(file: File): Promise<string> {
  if (!file.type.startsWith("image/")) return "";
  try {
    const res = await Tesseract.recognize(file, "eng", {
      workerPath: "/tesseract/worker.min.js",
      corePath: "/tesseract/tesseract-core-relaxedsimd-lstm.wasm.js",
      langPath: "https://tessdata.projectnaptha.com/4.0.0",
    });
    return (res?.data?.text || "").trim();
  } catch (e) {
    console.warn("[Lumint DocShield] client-side OCR failed; backend will skip keyword analysis:", e);
    return "";
  }
}

export const documentApi = {
  analyzeDocument: async (file: File): Promise<DocumentAnalysisResult | null> => {
    const base = apiBaseUrl();
    if (!base) {
      // Demo deployment: no backend configured. Fail soft so the UI can
      // surface a friendly empty state rather than a confusing error.
      return null;
    }
    const url = `${base}/api/documents/analyze`;
    const formData = new FormData();
    formData.append("file", file);

    // Best-effort client-side OCR for image uploads. Without this, every
    // image would come back CLEAN because the backend has no OCR. The
    // 25s cap matches the backend's 30s timeout; we let the request
    // continue without text if Tesseract is slow.
    if (file.type.startsWith("image/")) {
      try {
        const ocrText = await Promise.race([
          ocrImageForDocShield(file),
          new Promise<string>((resolve) => setTimeout(() => resolve(""), 25000)),
        ]);
        if (ocrText) formData.append("text", ocrText.slice(0, 8000));
      } catch (e) {
        console.warn("[Lumint DocShield] OCR step threw; continuing without text hint:", e);
      }
    }

    // 30s timeout — OCR + ELA + ML can take 5-10s in production.
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000);

    try {
      const response = await fetch(url, {
        method: "POST",
        body: formData,
        signal: controller.signal,
      });

      if (!response.ok) {
        let errorMessage = `API Error: ${response.status} ${response.statusText}`;
        try {
          const errJson = await response.json();
          if (errJson && errJson.detail) {
            if (typeof errJson.detail === "string") errorMessage = errJson.detail;
          }
        } catch {}
        const errorObj = new Error(errorMessage) as Error & { status?: number };
        errorObj.status = response.status;
        throw errorObj;
      }

      return (await response.json()) as DocumentAnalysisResult;
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : "network error";
      console.warn("[Lumint DocShield] analyze unreachable:", message);
      // Surface the real reason to the caller instead of fabricating a
      // fake "Will Smith" demo scan. The page's try/catch displays it.
      throw new Error(`DocShield backend unreachable: ${message}`);
    } finally {
      clearTimeout(timeoutId);
    }
  }
};

export default documentApi;
