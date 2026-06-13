import { apiRequest } from "@/lib/api-client";
import type { UPIAnalysisResult, UTRVerificationResult, QRScanResult, UPIAIResult } from "@/types";

// ─────────────────────────────────────────────────────────────────────────────
// UPI SHIELD SERVICE — wraps backend /api/upi endpoints
// No mock fallback. Real API only.
// ─────────────────────────────────────────────────────────────────────────────

export const upiService = {
  /**
   * Analyze a UPI payment screenshot via OCR + Groq LLM forensics.
   */
  analyzeScreenshot: async (file: File, customOcr?: string): Promise<UPIAnalysisResult> => {
    const formData = new FormData();
    formData.append("file", file);
    if (customOcr) formData.append("custom_ocr", customOcr);

    return apiRequest<UPIAnalysisResult>("/api/upi/analyze-screenshot", {
      method: "POST",
      body: formData,
    });
  },

  /**
   * Verify a UTR number structurally and against known fraud logs.
   */
  verifyUTR: async (utr: string): Promise<UTRVerificationResult> => {
    return apiRequest<UTRVerificationResult>(
      `/api/upi/verify-utr/${encodeURIComponent(utr)}`,
      { method: "GET" }
    );
  },

  /**
   * Decode a UPI QR code payload URI.
   */
  decodeQR: async (qrUrl: string): Promise<QRScanResult> => {
    const formData = new FormData();
    formData.append("qr_url", qrUrl);

    return apiRequest<QRScanResult>("/api/upi/decode-qr", {
      method: "POST",
      body: formData,
    });
  },

  /**
   * Request a Groq LLM narrative analysis of a UPI screenshot result.
   */
  analyzeWithAI: async (upiResult: UPIAnalysisResult): Promise<UPIAIResult> => {
    return apiRequest<UPIAIResult>("/api/ai/analyze-upi", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        utr_number: upiResult.utr_number,
        risk_score: upiResult.risk_score,
        sender: upiResult.sender_upi_id,
        receiver: upiResult.receiver_upi_id,
        amount: upiResult.amount,
        font_anomalies: upiResult.font_anomalies_detected,
        suspicious_handle: upiResult.suspicious_handle_flagged,
      }),
    });
  },
};
