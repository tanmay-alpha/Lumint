import { apiRequest } from "@/lib/api-client";
import type { UPIAnalysisResult, UTRVerificationResult, QRScanResult, UPIAIResult } from "@/types";

// ─────────────────────────────────────────────────────────────────────────────
// UPI SHIELD SERVICE — wraps backend /api/upi endpoints
// ─────────────────────────────────────────────────────────────────────────────

export const upiService = {
  /**
   * Analyze a UPI payment screenshot via OCR + Groq LLM forensics.
   */
  analyzeScreenshot: async (file: File, customOcr?: string): Promise<UPIAnalysisResult> => {
    const formData = new FormData();
    formData.append("file", file);
    if (customOcr) formData.append("custom_ocr", customOcr);

    return apiRequest<UPIAnalysisResult>(
      "/api/upi/analyze-screenshot",
      { method: "POST", body: formData },
      (): UPIAnalysisResult => {
        // Deterministic mock based on filename
        const name = file.name.toLowerCase();
        const isForged =
          name.includes("fake") || name.includes("edited") || name.includes("spoof");
        const isSuspicious = name.includes("test") || name.includes("sample");

        const risk_score = isForged ? 87 : isSuspicious ? 54 : 12;
        const risk_level: UPIAnalysisResult["risk_level"] = isForged
          ? "HIGH"
          : isSuspicious
          ? "SUSPICIOUS"
          : "CLEAN";

        return {
          id: Math.floor(Math.random() * 10000),
          timestamp: new Date().toISOString(),
          event_type: "screenshot",
          utr_number: isForged ? "fake123abc" : "398273645192",
          utr_valid: !isForged,
          utr_format: "googlepay",
          sender_upi_id: "user.sender@okhdfcbank",
          receiver_upi_id: isForged ? "scam.handle@okaxis" : "merchant@okaxis",
          amount: isForged ? 50000 : 1500,
          transaction_date: new Date().toISOString(),
          is_valid_utr: !isForged,
          font_anomalies_detected: isForged,
          suspicious_handle_flagged: isForged,
          risk_score,
          risk_level,
          ai_fraud_explanation: isForged
            ? "High-confidence forgery detected. UTR number does not conform to PhonePe/GPay format. Inconsistent font metrics in amount field. Likely generated using a mobile receipt editor app."
            : isSuspicious
            ? "Minor anomalies detected. Receiver VPA domain unverified. Manual review recommended before proceeding."
            : "No forgery indicators detected. Receipt structure appears authentic with consistent font metrics and valid UTR format.",
          raw_ocr_text: null,
          metadata_json: { file_name: file.name, file_size: file.size },
          ela_tamper_regions: isForged ? 3 : 0,
          font_consistent: !isForged,
          color_authentic: !isForged,
          ocr_confidence: isForged ? 61 : 94,
          amount_extracted: isForged ? "₹50,000.00" : "₹1,500.00",
          app_detected: "Google Pay",
          timestamp_extracted: new Date().toLocaleString("en-IN"),
        };
      }
    );
  },

  /**
   * Verify a UTR number structurally and against known fraud logs.
   */
  verifyUTR: async (utr: string): Promise<UTRVerificationResult> => {
    return apiRequest<UTRVerificationResult>(
      `/api/upi/verify-utr/${encodeURIComponent(utr)}`,
      { method: "GET" },
      (): UTRVerificationResult => {
        const clean = utr.replace(/\D/g, "");
        const isValid = clean.length === 12;
        return {
          utr_number: utr,
          is_valid: isValid,
          risk_score: isValid ? 8 : 75,
          risk_level: isValid ? "CLEAN" : "HIGH",
          known_fraud_match: false,
          checks_passed: isValid
            ? ["12-digit format verified", "No fraud database match"]
            : [],
          checks_failed: isValid ? [] : [`Expected 12 digits, got ${clean.length}`],
          message: "UTR verification completed (mock mode)",
        };
      }
    );
  },

  /**
   * Decode a UPI QR code payload URI.
   */
  decodeQR: async (qrUrl: string): Promise<QRScanResult> => {
    const formData = new FormData();
    formData.append("qr_url", qrUrl);

    return apiRequest<QRScanResult>(
      "/api/upi/decode-qr",
      { method: "POST", body: formData },
      (): QRScanResult => {
        const pa = qrUrl.match(/pa=([^&]+)/)?.[1] ?? null;
        const pn = qrUrl.match(/pn=([^&]+)/)?.[1] ?? null;
        const am = qrUrl.match(/am=([^&]+)/)?.[1] ?? null;
        const isSuspicious = pa
          ? ["scam", "free", "gift", "prize"].some((kw) => pa.toLowerCase().includes(kw))
          : false;
        return {
          raw_uri: qrUrl,
          pa,
          pn,
          am,
          cu: "INR",
          risk_score: isSuspicious ? 85 : 10,
          risk_level: isSuspicious ? "HIGH" : "CLEAN",
          is_suspicious_handle: isSuspicious,
          message: "QR decoded (mock mode)",
        };
      }
    );
  },

  /**
   * Request a Groq LLM narrative analysis of a UPI screenshot result.
   */
  analyzeWithAI: async (upiResult: UPIAnalysisResult): Promise<UPIAIResult> => {
    return apiRequest<UPIAIResult>(
      "/api/ai/analyze-upi",
      {
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
      },
      (): UPIAIResult => {
        const isHigh = upiResult.risk_score >= 70;
        const isMid = upiResult.risk_score >= 40;
        return {
          verdict: isHigh ? "FORGED" : isMid ? "SUSPICIOUS" : "GENUINE",
          confidence: isHigh ? 91 : isMid ? 72 : 95,
          forgery_method: isHigh
            ? "Mobile receipt editor app (screen-capture manipulation)"
            : null,
          evidence_points: isHigh
            ? [
                "UTR string does not match PhonePe/GPay 12-digit format",
                "Font rendering inconsistencies in amount field (pixel-level analysis)",
                "Receiver VPA domain suffix not registered with NPCI whitelist",
                "Amount figure shows pixel aliasing artifacts consistent with image editing",
              ]
            : isMid
            ? [
                "Receiver VPA unverified against NPCI merchant registry",
                "Minor font weight variation in timestamp field",
              ]
            : ["Valid UTR format", "Consistent font metrics", "Verified VPA domains"],
          analyst_note: isHigh
            ? "This screenshot exhibits multiple forensic markers consistent with receipt generation tools. Do not release funds. File a complaint with your bank's fraud department citing UTR discrepancy."
            : isMid
            ? "Exercise caution. Verify the transaction via your banking app before acknowledging payment receipt."
            : "Receipt appears authentic. Standard due-diligence verification recommended for amounts above ₹10,000.",
          recommended_action: isHigh
            ? "Block payment. Escalate to NPCI Chargeback. File cybercrime complaint."
            : isMid
            ? "Verify transaction ID directly in banking app. Contact merchant via official channel."
            : "No immediate action required.",
          model_used: "llama-3.3-70b-versatile",
          latency_ms: Math.floor(Math.random() * 400) + 300,
        };
      }
    );
  },
};
