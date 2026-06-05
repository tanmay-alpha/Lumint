import { apiRequest } from "@/lib/api-client";
import { DocumentAnalysisResponse } from "@/types";

export const documentsService = {
  analyze: async (file: File): Promise<DocumentAnalysisResponse> => {
    const formData = new FormData();
    formData.append("file", file);

    const isPdf = file.name.toLowerCase().endsWith(".pdf");

    return apiRequest<DocumentAnalysisResponse>(
      "/api/documents/analyze",
      {
        method: "POST",
        body: formData,
      },
      () => {
        // Fallback Mock Generator based on name/extension
        const docId = `doc-${Math.random().toString(36).substr(2, 9)}`;
        const baseResponse = {
          doc_id: docId,
          original_filename: file.name,
          saved_filename: `${docId}.${isPdf ? "pdf" : "jpg"}`,
          file_path: `/uploads/${docId}.${isPdf ? "pdf" : "jpg"}`,
          file_size: file.size,
          content_type: file.type || (isPdf ? "application/pdf" : "image/jpeg"),
          analysis_status: "COMPLETED",
          message: "Document analyzed successfully (Demo Mock Mode)",
        };

        if (isPdf) {
          // If invoice in name, make it highly suspicious/malicious
          if (file.name.toLowerCase().includes("invoice")) {
            return {
              ...baseResponse,
              risk_score: 87,
              risk_level: "HIGH",
              metadata: {
                title: "Invoice #9821_Revised",
                author: "Accounts Payable Manager",
                creator: "WriterPro v4.1",
                producer: "Acrobat Distiller 15.0 (Windows)",
                creation_date: "2026-05-15T09:30:00Z",
                modification_date: "2026-06-02T14:45:00Z", // Modified later
                page_count: 1,
                is_encrypted: false,
                file_size: file.size,
              },
              text_analysis: {
                flagged_terms: ["swift", "routing code", "wire transfer", "offshore"],
                sentiment: "neutral",
              },
              layout_analysis: {
                inconsistent_fonts: true,
                overlapping_text: true,
              },
              ela_analysis: null,
              indicators: [
                {
                  rule: "Metadata Modification Detected",
                  score: 30,
                  detail: "The PDF was modified multiple days after creation, indicating possible post-approval tampering.",
                },
                {
                  rule: "Spoofed Creator Field",
                  score: 25,
                  detail: "The internal creator field ('WriterPro') does not align with the standard corporate PDF generator signature.",
                },
                {
                  rule: "Swift Code Alteration Hint",
                  score: 32,
                  detail: "Visual overlay detected on bank routing information area. Inconsistent line alignment.",
                },
              ],
              explanation: [
                "Document shows signs of visual editing in sensitive numeric tables.",
                "Metadata timestamps reveal modification 18 days after original export.",
                "Inconsistent font spacing detected inside Swift Code cell.",
              ],
              analysis_warnings: [],
            };
          } else {
            // Clean document fallback
            return {
              ...baseResponse,
              risk_score: 8,
              risk_level: "CLEAN",
              metadata: {
                title: file.name.replace(".pdf", ""),
                author: "Lumint User",
                creator: "Google Docs",
                producer: "Skia/PDF m120",
                creation_date: new Date().toISOString(),
                modification_date: new Date().toISOString(),
                page_count: 2,
                is_encrypted: false,
                file_size: file.size,
              },
              text_analysis: {
                flagged_terms: [],
                sentiment: "positive",
              },
              layout_analysis: {
                inconsistent_fonts: false,
                overlapping_text: false,
              },
              ela_analysis: null,
              indicators: [],
              explanation: [
                "No suspicious elements or metadata manipulation signs found.",
              ],
              analysis_warnings: [],
            };
          }
        } else {
          // Image upload fallback
          const isPassport = file.name.toLowerCase().includes("passport") || file.name.toLowerCase().includes("id");
          if (isPassport) {
            return {
              ...baseResponse,
              risk_score: 72,
              risk_level: "SUSPICIOUS",
              metadata: {
                title: null,
                author: null,
                creator: "Photoshop 2024",
                producer: "Adobe Photoshop CC (Macintosh)",
                creation_date: "2026-03-12T12:00:00Z",
                modification_date: new Date().toISOString(),
                page_count: null,
                is_encrypted: false,
                file_size: file.size,
              },
              text_analysis: null,
              layout_analysis: null,
              ela_analysis: {
                max_error: 0.89,
                average_error: 0.12,
                discrepancy_regions: ["Passport Number", "Date of Birth"],
              },
              indicators: [
                {
                  rule: "ELA Discrepancy Found in Image Text",
                  score: 45,
                  detail: "Error Level Analysis shows anomalous light compression density around the Document Number and DOB text regions.",
                },
                {
                  rule: "EXIF Data Mismatch (Photoshop Signature)",
                  score: 27,
                  detail: "Metadata contains Adobe Photoshop signatures, uncommon for standard smartphone/scanner camera outputs.",
                },
              ],
              explanation: [
                "Localized compression discrepancies strongly point to digital alterations inside text boundaries.",
                "Photoshop signature present in image metadata header.",
              ],
              analysis_warnings: [],
            };
          } else {
            return {
              ...baseResponse,
              risk_score: 15,
              risk_level: "CLEAN",
              metadata: {
                title: null,
                author: null,
                creator: "Apple iPhone 15 Pro",
                producer: "iOS Camera App",
                creation_date: new Date().toISOString(),
                modification_date: new Date().toISOString(),
                page_count: null,
                is_encrypted: false,
                file_size: file.size,
              },
              text_analysis: null,
              layout_analysis: null,
              ela_analysis: {
                max_error: 0.15,
                average_error: 0.02,
                discrepancy_regions: [],
              },
              indicators: [],
              explanation: [
                "No digital tampering signature detected. Compression profile appears consistent throughout the surface.",
              ],
              analysis_warnings: [],
            };
          }
        }
      }
    );
  },
};
