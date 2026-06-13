import { PhishingAnalysisResult } from "../types";
import { apiBaseUrl } from "../config";

export const phishingApi = {
  checkUrl: async (url: string): Promise<PhishingAnalysisResult> => {
    const base = apiBaseUrl();
    if (!base) {
      throw {
        message: "Backend not configured. Set NEXT_PUBLIC_API_URL to your FastAPI host.",
        status: 0,
        path: "/api/phishing/check",
        isNetworkError: true,
      };
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
      console.error("[Lumint PhishShield] check failed:", error);
      throw {
        message: error?.message || "PhishShield analysis failed",
        status: error?.status || 0,
        path: "/api/phishing/check",
        isNetworkError: !error?.status,
      };
    } finally {
      clearTimeout(timeoutId);
    }
  },
};

export default phishingApi;
