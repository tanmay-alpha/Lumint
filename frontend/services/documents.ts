import { apiRequest } from "@/lib/api-client";
import { DocumentAnalysisResponse } from "@/types";

export const documentsService = {
  analyze: async (file: File): Promise<DocumentAnalysisResponse> => {
    const formData = new FormData();
    formData.append("file", file);

    return apiRequest<DocumentAnalysisResponse>("/api/documents/analyze", {
      method: "POST",
      body: formData,
    });
  },
};
