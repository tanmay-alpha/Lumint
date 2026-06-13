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

    const apiKey = process.env.NEXT_PUBLIC_API_KEY;
    const requestHeaders: Record<string, string> = {
      "Content-Type": "application/json",
    };
    if (apiKey) {
      requestHeaders["Authorization"] = `Bearer ${apiKey}`;
    }

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
        } catch (_) {}
        const errorObj: any = new Error(errorMessage);
        errorObj.status = response.status;
        throw errorObj;
      }

      return (await response.json()) as PhishingAnalysisResult;
    } catch (error: any) {
      console.warn("[Lumint PhishShield] check unreachable; returning null:", error?.message);
      // Network or server error — fail soft, return null.
      return null;
    } finally {
      clearTimeout(timeoutId);
    }
  },
};

export default phishingApi;
