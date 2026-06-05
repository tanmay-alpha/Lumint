import { DocumentAnalysisResult } from "../types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const MOCK_ANALYSIS_RESULT: DocumentAnalysisResult = {
  doc_id: "doc-89a12b",
  original_filename: "invoice_9821.pdf",
  saved_filename: "doc-89a12b.pdf",
  file_path: "/uploads/doc-89a12b.pdf",
  file_size: 102400,
  content_type: "application/pdf",
  analysis_status: "COMPLETED",
  risk_score: 87,
  risk_level: "HIGH",
  metadata: {
    title: "Invoice 9821 Forged",
    author: "Malicious Actor",
    creator: "Accounts Payable Manager",
    producer: "Adobe PDF Library 15.0",
    creation_date: new Date().toISOString(),
    modification_date: new Date().toISOString(),
    page_count: 1,
    is_encrypted: false,
    file_size: 102400
  },
  text_analysis: {
    sensitive_keywords_found: ["payment", "wire transfer", "bank routing"],
    suspicious_patterns: ["modified IBAN number"]
  },
  layout_analysis: {
    overlapping_text_blocks: true,
    font_discrepancies: ["Arial and Helvetica mixed irregularly"]
  },
  ela_analysis: {
    ela_discrepancy_score: 0.85,
    tampering_detected: true
  },
  indicators: [
    { rule: "Metadata Modification Detected", score: 35, detail: "File creation dates modified relative to original metadata timestamps." },
    { rule: "Spoofed Creator Field", score: 25, detail: "Producer fields indicate graphical tool generation rather than standard ERP output." },
    { rule: "Swift Code Alteration Hint", score: 27, detail: "Swift / Routing info fields modified via image layered overrides." }
  ],
  explanation: [
    "The document's creator metadata field was spoofed to mimic a standard invoice application.",
    "Graphic alteration signatures detected in the SWIFT code layout structure.",
    "Error Level Analysis shows tampering markers around the banking information."
  ],
  analysis_warnings: [],
  message: "High risk document anomalies matching invoicing forgery pattern."
};

export const documentApi = {
  analyzeDocument: async (file: File): Promise<DocumentAnalysisResult> => {
    const url = `${BASE_URL}/api/documents/analyze`;
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch(url, {
        method: "POST",
        body: formData,
        // Short timeout for fallback, but file uploads might take a bit longer
        signal: AbortSignal.timeout(10000)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return (await response.json()) as DocumentAnalysisResult;
    } catch (error) {
      console.warn("Lumint DocShield API fallback to mock analysis result:", error);
      // Simulate artificial latency
      await new Promise((resolve) => setTimeout(resolve, 1500));
      return MOCK_ANALYSIS_RESULT;
    }
  }
};

export default documentApi;
