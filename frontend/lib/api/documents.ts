import { DocumentAnalysisResult } from "../types";
import { apiBaseUrl } from "../config";

export const documentApi = {
  analyzeDocument: async (file: File): Promise<DocumentAnalysisResult> => {
    const base = apiBaseUrl();
    if (!base) {
      throw {
        message: "Backend not configured. Set NEXT_PUBLIC_API_URL to your FastAPI host.",
        status: 0,
        path: "/api/documents/analyze",
        isNetworkError: true,
      };
    }
    const url = `${base}/api/documents/analyze`;
    const formData = new FormData();
    formData.append("file", file);

    const apiKey = process.env.NEXT_PUBLIC_API_KEY;
    const requestHeaders: Record<string, string> = {};
    if (apiKey) {
      requestHeaders["Authorization"] = `Bearer ${apiKey}`;
    }

    // 30s timeout — OCR + ELA + ML can take 5-10s in production.
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000);

    try {
      const response = await fetch(url, {
        method: "POST",
        headers: requestHeaders,
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
        } catch (_) {}
        const errorObj: any = new Error(errorMessage);
        errorObj.status = response.status;
        throw errorObj;
      }

      return (await response.json()) as DocumentAnalysisResult;
    } catch (error: any) {
      console.error("[Lumint DocShield] analyze failed:", error);
      throw {
        message: error?.message || "DocShield analysis failed",
        status: error?.status || 0,
        path: "/api/documents/analyze",
        isNetworkError: !error?.status,
      };
    } finally {
      clearTimeout(timeoutId);
    }
  }
};

export default documentApi;
