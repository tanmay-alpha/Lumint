import { DocumentAnalysisResult } from "../types";
import { apiBaseUrl } from "../config";

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
      console.warn("[Lumint DocShield] analyze unreachable; returning null:", message);
      // Network or server error — fail soft, return null. The page's
      // try/catch will display the friendly empty state.
      return null;
    } finally {
      clearTimeout(timeoutId);
    }
  }
};

export default documentApi;
