import { PhishingAnalysisResult } from "../types";
import { apiBaseUrl } from "../config";

export const phishingApi = {
  checkUrl: async (url: string): Promise<PhishingAnalysisResult | null> => {
    const base = apiBaseUrl();
    if (!base) {
      // Demo deployment: no backend configured. Fail soft so the UI can
      // surface a friendly empty state rather than a confusing error.
      return null;
    }
    const apiEndpoint = `${base}/api/phishing/check`;

    const requestHeaders: Record<string, string> = {
      "Content-Type": "application/json",
    };

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);

    try {
      const response = await fetch(apiEndpoint, {
        method: "POST",
        headers: requestHeaders,
        body: JSON.stringify({ url }),
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

      return (await response.json()) as PhishingAnalysisResult;
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : "network error";
      console.warn("[Lumint PhishShield] check unreachable:", message);
      // Surface a structured error to the caller so the UI can show the
      // real reason (instead of the misleading "demo deployment" copy).
      throw new Error(`PhishShield backend unreachable: ${message}`);
    } finally {
      clearTimeout(timeoutId);
    }
  },
};

export default phishingApi;
