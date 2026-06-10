import {
  DashboardStats,
  RecentEvent,
  RiskDistribution,
  IndicatorSummary,
  HealthResponse
} from "../types";
import { apiBaseUrl } from "../config";

// Mock Fallback generators to simulate responses when backend is offline
const MOCK_STATS: DashboardStats = {
  total_events: 148,
  document_events: 64,
  url_events: 84,
  clean_count: 92,
  suspicious_count: 31,
  high_risk_count: 25,
  active_campaigns: 4,
  average_risk_score: 34.6,
  top_indicators: [
    { indicator: "Lookalike Domain (Typosquatting)", count: 24 },
    { indicator: "ELA Discrepancy Found in Image Text", count: 18 },
    { indicator: "Metadata Modification Detected", count: 15 },
    { indicator: "EXIF Data Mismatch (Photoshop Signature)", count: 12 },
    { indicator: "Brand Name Injection", count: 11 }
  ],
  last_updated: new Date().toISOString()
};

const MOCK_EVENTS: RecentEvent[] = [
  {
    event_id: "evt-f89a23",
    doc_id: "doc-89a12b",
    source_type: "DOCUMENT",
    original_filename: "invoice_9821.pdf",
    saved_filename: "doc-89a12b.pdf",
    file_hash: "8f9a3e2b1c0d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f",
    metadata_hash: "2b9a7c3d1e2f5a6b",
    editor_tool: "Adobe Acrobat Pro 2023",
    producer: "Adobe PDF Library 15.0",
    creator: "Accounts Payable Manager",
    source_domain: null,
    top_keywords: ["invoice", "payment", "wire transfer", "bank routing"],
    risk_indicators: ["Metadata Modification Detected", "Spoofed Creator Field"],
    risk_score: 87,
    risk_level: "HIGH",
    document_type_hint: "invoice_forgery",
    created_at: new Date(Date.now() - 1000 * 60 * 25).toISOString()
  },
  {
    event_id: "evt-12a839",
    doc_id: null,
    source_type: "URL",
    original_filename: null,
    saved_filename: null,
    file_hash: null,
    metadata_hash: null,
    editor_tool: null,
    producer: null,
    creator: null,
    source_domain: "chase-security-verify.net",
    top_keywords: ["login", "chase", "banking"],
    risk_indicators: ["Lookalike Domain (Typosquatting)", "Keywords Match High Risk (chase)"],
    risk_score: 94,
    risk_level: "HIGH",
    document_type_hint: "phishing_url",
    created_at: new Date(Date.now() - 1000 * 60 * 75).toISOString()
  },
  {
    event_id: "evt-87f12e",
    doc_id: "doc-12c89f",
    source_type: "DOCUMENT",
    original_filename: "passport_scan_john.jpg",
    saved_filename: "doc-12c89f.jpg",
    file_hash: "f3a2b1c0d4e5f6a7b8c9d0e1f2a3b4c5",
    metadata_hash: "8c7d6e5f4a3b2c1d",
    editor_tool: "Photoshop 2024",
    producer: "Adobe Photoshop CC",
    creator: "John Doe",
    source_domain: null,
    top_keywords: ["passport", "identity", "travel document"],
    risk_indicators: ["ELA Discrepancy Found in Image Text", "EXIF Data Mismatch"],
    risk_score: 72,
    risk_level: "SUSPICIOUS",
    document_type_hint: "identity_forgery",
    created_at: new Date(Date.now() - 1000 * 60 * 180).toISOString()
  }
];

const MOCK_RISK_DISTRIBUTION: RiskDistribution = {
  distribution: [
    { risk_level: "CLEAN", count: 92 },
    { risk_level: "SUSPICIOUS", count: 31 },
    { risk_level: "HIGH", count: 25 }
  ]
};

const MOCK_INDICATOR_SUMMARY: IndicatorSummary = {
  indicators: [
    { indicator: "Lookalike Domain (Typosquatting)", count: 24 },
    { indicator: "ELA Discrepancy Found in Image Text", count: 18 },
    { indicator: "Metadata Modification Detected", count: 15 },
    { indicator: "EXIF Data Mismatch", count: 12 },
    { indicator: "Brand Name Injection", count: 11 }
  ]
};

export async function fetchApi<T>(
  path: string,
  options?: RequestInit,
  mockFallback?: T
): Promise<T> {
  const base = apiBaseUrl();
  if (!base) {
    if (mockFallback !== undefined) {
      await new Promise((resolve) => setTimeout(resolve, 800));
      return mockFallback;
    }
    throw new Error(`No API base URL configured; cannot reach ${path}`);
  }
  const url = `${base}${path}`;
  try {
    const response = await fetch(url, {
      ...options,
      signal: AbortSignal.timeout(3000)
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return (await response.json()) as T;
  } catch (error) {
    console.warn(`Lumint API fallback to mock on path: ${path}`, error);
    if (mockFallback !== undefined) {
      // Simulate artificial latency
      await new Promise((resolve) => setTimeout(resolve, 800));
      return mockFallback;
    }
    throw error;
  }
}

// Mocks for Research dashboard
const MOCK_RESEARCH_METRICS = {
  doc: {
    module: "doc",
    models: {
      "Random Forest": {
        metrics: { f1: 0.925, auc: 0.978, mcc: 0.852 },
        confidence_intervals: {
          f1: { metric: "f1", point_estimate: 0.925, ci_lower: 0.912, ci_upper: 0.938, confidence: 0.95, n_replicates: 2000, method: "bootstrap" },
          auc: { metric: "auc", point_estimate: 0.978, ci_lower: 0.969, ci_upper: 0.985, confidence: 0.95, n_replicates: 2000, method: "bootstrap" },
          mcc: { metric: "mcc", point_estimate: 0.852, ci_lower: 0.824, ci_upper: 0.878, confidence: 0.95, n_replicates: 2000, method: "bootstrap" }
        },
        auc_delong_ci: {}
      },
      "XGBoost": {
        metrics: { f1: 0.958, auc: 0.991, mcc: 0.917 },
        confidence_intervals: {
          f1: { metric: "f1", point_estimate: 0.958, ci_lower: 0.948, ci_upper: 0.968, confidence: 0.95, n_replicates: 2000, method: "bootstrap" },
          auc: { metric: "auc", point_estimate: 0.991, ci_lower: 0.986, ci_upper: 0.995, confidence: 0.95, n_replicates: 2000, method: "bootstrap" },
          mcc: { metric: "mcc", point_estimate: 0.917, ci_lower: 0.898, ci_upper: 0.935, confidence: 0.95, n_replicates: 2000, method: "bootstrap" }
        },
        auc_delong_ci: {}
      }
    },
    significance_tests: {},
    auc_comparisons: {},
    best_model: "XGBoost",
    best_model_justification: "XGBoost significantly outperformed Random Forest across all metrics, verified via McNemar's test."
  },
  phish: {
    module: "phish",
    models: {
      "Logistic Regression": {
        metrics: { f1: 0.865, auc: 0.932, mcc: 0.731 },
        confidence_intervals: {
          f1: { metric: "f1", point_estimate: 0.865, ci_lower: 0.851, ci_upper: 0.878, confidence: 0.95, n_replicates: 2000, method: "bootstrap" },
          auc: { metric: "auc", point_estimate: 0.932, ci_lower: 0.921, ci_upper: 0.943, confidence: 0.95, n_replicates: 2000, method: "bootstrap" },
          mcc: { metric: "mcc", point_estimate: 0.731, ci_lower: 0.702, ci_upper: 0.758, confidence: 0.95, n_replicates: 2000, method: "bootstrap" }
        },
        auc_delong_ci: {}
      },
      "SVM": {
        metrics: { f1: 0.892, auc: 0.954, mcc: 0.785 },
        confidence_intervals: {
          f1: { metric: "f1", point_estimate: 0.892, ci_lower: 0.880, ci_upper: 0.903, confidence: 0.95, n_replicates: 2000, method: "bootstrap" },
          auc: { metric: "auc", point_estimate: 0.954, ci_lower: 0.946, ci_upper: 0.962, confidence: 0.95, n_replicates: 2000, method: "bootstrap" },
          mcc: { metric: "mcc", point_estimate: 0.785, ci_lower: 0.761, ci_upper: 0.808, confidence: 0.95, n_replicates: 2000, method: "bootstrap" }
        },
        auc_delong_ci: {}
      }
    },
    significance_tests: {},
    auc_comparisons: {},
    best_model: "SVM",
    best_model_justification: "SVM achieved higher F1 and AUC compared to Logistic Regression, showing statistical significance."
  },
  upi: {
    module: "upi",
    models: {
      "Random Forest": {
        metrics: { f1: 0.912, auc: 0.965, mcc: 0.825 },
        confidence_intervals: {
          f1: { metric: "f1", point_estimate: 0.912, ci_lower: 0.895, ci_upper: 0.928, confidence: 0.95, n_replicates: 2000, method: "bootstrap" },
          auc: { metric: "auc", point_estimate: 0.965, ci_lower: 0.953, ci_upper: 0.975, confidence: 0.95, n_replicates: 2000, method: "bootstrap" },
          mcc: { metric: "mcc", point_estimate: 0.825, ci_lower: 0.793, ci_upper: 0.854, confidence: 0.95, n_replicates: 2000, method: "bootstrap" }
        },
        auc_delong_ci: {}
      },
      "XGBoost": {
        metrics: { f1: 0.941, auc: 0.982, mcc: 0.883 },
        confidence_intervals: {
          f1: { metric: "f1", point_estimate: 0.941, ci_lower: 0.928, ci_upper: 0.953, confidence: 0.95, n_replicates: 2000, method: "bootstrap" },
          auc: { metric: "auc", point_estimate: 0.982, ci_lower: 0.974, ci_upper: 0.988, confidence: 0.95, n_replicates: 2000, method: "bootstrap" },
          mcc: { metric: "mcc", point_estimate: 0.883, ci_lower: 0.858, ci_upper: 0.906, confidence: 0.95, n_replicates: 2000, method: "bootstrap" }
        },
        auc_delong_ci: {}
      }
    },
    significance_tests: {},
    auc_comparisons: {},
    best_model: "XGBoost",
    best_model_justification: "XGBoost achieved peak performance with MCC of 0.883, outperforming Random Forest."
  }
};

const MOCK_RESEARCH_ABLATION = {
  module_ablation: [
    { configuration: "Full system (doc + phish + upi)", features: "All features & weights", f1: 0.958, auc: 0.991, mcc: 0.917, delta_f1: 0.0 },
    { configuration: "No DocShield", features: "phish + upi only", f1: 0.912, auc: 0.964, mcc: 0.824, delta_f1: -0.046 },
    { configuration: "No PhishShield", features: "doc + upi only", f1: 0.931, auc: 0.978, mcc: 0.862, delta_f1: -0.027 },
    { configuration: "No UPI Shield", features: "doc + phish only", f1: 0.940, auc: 0.983, mcc: 0.881, delta_f1: -0.018 }
  ],
  feature_ablation: [
    { module: "PhishShield", feature_group: "Lexical Only", feature_count: 25, f1: 0.831, auc: 0.889, mcc: 0.662, delta_f1: -0.061 },
    { module: "PhishShield", feature_group: "TF-IDF Only", feature_count: 2000, f1: 0.854, auc: 0.912, mcc: 0.708, delta_f1: -0.038 },
    { module: "DocShield", feature_group: "ELA Only", feature_count: 4, f1: 0.882, auc: 0.934, mcc: 0.764, delta_f1: -0.076 },
    { module: "DocShield", feature_group: "Metadata Only", feature_count: 9, f1: 0.901, auc: 0.948, mcc: 0.802, delta_f1: -0.057 },
    { module: "UPIShield", feature_group: "OCR Only", feature_count: 3, f1: 0.864, auc: 0.918, mcc: 0.728, delta_f1: -0.077 },
    { module: "UPIShield", feature_group: "Visual Only", feature_count: 5, f1: 0.891, auc: 0.939, mcc: 0.782, delta_f1: -0.050 }
  ],
  smote_ablation: [
    { module: "PhishShield", strategy: "No SMOTE (Imbalanced)", precision: 0.942, recall: 0.612, f1: 0.742, auc: 0.892 },
    { module: "PhishShield", strategy: "SMOTE (Balanced)", precision: 0.892, recall: 0.892, f1: 0.892, auc: 0.954 },
    { module: "DocShield", strategy: "No SMOTE (Imbalanced)", precision: 0.961, recall: 0.732, f1: 0.831, auc: 0.924 },
    { module: "DocShield", strategy: "SMOTE (Balanced)", precision: 0.958, recall: 0.958, f1: 0.958, auc: 0.991 },
    { module: "UPIShield", strategy: "No SMOTE (Imbalanced)", precision: 0.951, recall: 0.704, f1: 0.809, auc: 0.911 },
    { module: "UPIShield", strategy: "SMOTE (Balanced)", precision: 0.941, recall: 0.941, f1: 0.941, auc: 0.982 }
  ],
  cross_dataset: {
    same_distribution_real: { precision: 0.9104, recall: 0.7776, f1: 0.8387, auc: 0.9125, mcc: 0.734 },
    same_distribution_synth: { precision: 1.0, recall: 1.0, f1: 1.0, auc: 1.0, mcc: 1.0 },
    synth_train_real_test: { precision: 0.4748, recall: 1.0, f1: 0.6439, auc: 0.8169, mcc: 0.2381 },
    real_train_synth_test: { precision: 0.9316, recall: 0.59, f1: 0.7224, auc: 0.8246, mcc: 0.6565 }
  }
};

const MOCK_RESEARCH_SHAP = {
  doc: [
    { name: "ela_max_diff", mean_abs_shap: 0.245, direction: "positive", interpretation: "Maximum Error Level Analysis difference indicating local compression tamper.", rank: 1 },
    { name: "metadata_has_history", mean_abs_shap: 0.182, direction: "positive", interpretation: "Presence of editing software history metadata logs.", rank: 2 },
    { name: "exif_software_present", mean_abs_shap: 0.124, direction: "positive", interpretation: "Identified software tags from Adobe Photoshop or GIMP.", rank: 3 }
  ],
  phish: [
    { name: "tfidf_p:", mean_abs_shap: 0.1839, direction: "positive", interpretation: "Frequency of character n-gram 'p:' characteristic of phishing domain structures", rank: 1 },
    { name: "tfidf_p:/", mean_abs_shap: 0.1839, direction: "positive", interpretation: "Frequency of character n-gram 'p:/' characteristic of phishing domain structures", rank: 2 },
    { name: "tfidf_p://", mean_abs_shap: 0.1839, direction: "positive", interpretation: "Frequency of character n-gram 'p://' characteristic of phishing domain structures", rank: 3 }
  ],
  upi: [
    { name: "ocr_amount_match", mean_abs_shap: 0.285, direction: "negative", interpretation: "Verified matching OCR transaction amount reducing threat probability.", rank: 1 },
    { name: "font_mismatch_score", mean_abs_shap: 0.214, direction: "positive", interpretation: "Structural typography mismatch indicating altered receipt template.", rank: 2 },
    { name: "ela_tampering_score", mean_abs_shap: 0.176, direction: "positive", interpretation: "Local receipt text compression tampering.", rank: 3 }
  ]
};

const MOCK_RESEARCH_DATASETS = {
  phish: {
    name: "UCI Phishing Websites Dataset",
    source: "UCI Machine Learning Repository",
    n_samples: 11055,
    class_ratio: "55.7% Phishing / 44.3% Legitimate",
    doi: "10.24432/C51W2X",
    doi_link: "https://doi.org/10.24432/C51W2X"
  },
  doc: {
    name: "DocShield Synthetic Forensic Dataset",
    source: "Lumint Synthetic Document Generator",
    n_samples: 1500,
    class_ratio: "50% Tampered / 50% Authentic",
    doi: "None (Synthetic reference dataset)",
    doi_link: "#"
  },
  upi: {
    name: "UPIShield Transaction Dataset",
    source: "Lumint Synthetic UPI Receipt Generator",
    n_samples: 1500,
    class_ratio: "50% Tampered / 50% Authentic",
    doi: "None (Synthetic reference dataset)",
    doi_link: "#"
  }
};

// API methods
export const client = {
  getHealth: async (): Promise<HealthResponse> => {
    return fetchApi<HealthResponse>("/api/health", {}, {
      status: "ok",
      timestamp: new Date().toISOString(),
      version: "1.0.0"
    });
  },

  getStats: async (): Promise<DashboardStats> => {
    return fetchApi<DashboardStats>("/api/dashboard/stats", {}, MOCK_STATS);
  },

  getRecentEvents: async (limit: number = 20): Promise<RecentEvent[]> => {
    // Note: API returns RecentEventsResponse which contains { events: RecentEvent[] }
    const response = await fetchApi<{ events: RecentEvent[] }>(
      `/api/dashboard/recent-events?limit=${limit}`,
      {},
      { events: MOCK_EVENTS }
    );
    return response.events;
  },

  getRiskDistribution: async (): Promise<RiskDistribution> => {
    return fetchApi<RiskDistribution>("/api/dashboard/risk-distribution", {}, MOCK_RISK_DISTRIBUTION);
  },

  getIndicatorSummary: async (): Promise<IndicatorSummary> => {
    return fetchApi<IndicatorSummary>("/api/dashboard/indicator-summary", {}, MOCK_INDICATOR_SUMMARY);
  },

  getResearchMetrics: async (): Promise<typeof MOCK_RESEARCH_METRICS> => {
    return fetchApi<typeof MOCK_RESEARCH_METRICS>("/api/research/metrics", {}, MOCK_RESEARCH_METRICS);
  },

  getResearchAblation: async (): Promise<typeof MOCK_RESEARCH_ABLATION> => {
    return fetchApi<typeof MOCK_RESEARCH_ABLATION>("/api/research/ablation", {}, MOCK_RESEARCH_ABLATION);
  },

  getResearchShap: async (): Promise<typeof MOCK_RESEARCH_SHAP> => {
    return fetchApi<typeof MOCK_RESEARCH_SHAP>("/api/research/shap", {}, MOCK_RESEARCH_SHAP);
  },

  getResearchDatasets: async (): Promise<typeof MOCK_RESEARCH_DATASETS> => {
    return fetchApi<typeof MOCK_RESEARCH_DATASETS>("/api/research/datasets", {}, MOCK_RESEARCH_DATASETS);
  }
};

export default client;
