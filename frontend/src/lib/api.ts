// TRACE AI Frontend API Client

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api";

export interface LogEntry {
  id: string;
  run_id: string;
  line_number: number;
  timestamp: string | null;
  raw_timestamp: string | null;
  severity: string;
  service: string;
  message: string;
  raw_text: string;
  is_malformed: boolean;
  anomaly_score?: number;
  is_anomaly?: boolean;
  feature_contributions?: Record<string, any> | null;
}

export interface Anomaly {
  id: string;
  run_id: string;
  log_id: string;
  anomaly_score: number;
  is_anomaly: boolean;
  detection_time: string;
  feature_contributions?: Record<string, any>;
  log?: LogEntry;
}

export interface Diagnosis {
  id: string;
  incident_id: string;
  possible_cause: string;
  confidence: number;
  explanation: string;
  uncertainty?: string;
  recommended_steps: string[];
  is_demo_mode: boolean;
  raw_jev_response?: any;
}

export interface IncidentEvidence {
  id: string;
  incident_id: string;
  log_id: string;
  evidence_type: string;
  description?: string;
  log?: LogEntry;
}

export interface Incident {
  id: string;
  run_id: string;
  title: string;
  severity: string;
  category: string;
  status: string;
  detected_time: string;
  summary?: string;
  confidence: number;
  evidence: IncidentEvidence[];
  diagnosis?: Diagnosis;
}

export interface AnalysisRun {
  id: string;
  filename: string;
  file_size_bytes: number;
  status: string;
  error_message?: string;
  total_entries: number;
  parsed_count: number;
  rejected_count: number;
  anomaly_count: number;
  incident_count: number;
  start_time: string;
  completion_time?: string;
}

export interface DashboardStats {
  total_entries_analysed: number;
  total_anomalies_detected: number;
  total_incidents_identified: number;
  severity_distribution: Record<string, number>;
  category_distribution: Record<string, number>;
  error_frequency_timeline: Array<{
    time: string;
    critical: number;
    errors: number;
    warnings: number;
    info: number;
    total: number;
  }>;
  recent_incidents: Incident[];
  latest_run_id?: string;
}

export interface SettingsData {
  jev_api_key_configured: boolean;
  jev_api_key_masked: string;
  jev_api_url: string;
  demo_mode: boolean;
  default_contamination: number;
  default_correlation_window_seconds: number;
  max_file_size_mb: number;
}

export interface EvaluationMetricResult {
  scenario_name: string;
  total_logs: number;
  true_anomalies: number;
  detected_anomalies: number;
  true_positives: number;
  false_positives: number;
  false_negatives: number;
  precision: number;
  recall: number;
  f1_score: number;
  false_positive_rate: number;
  diagnosis_match: boolean;
  predicted_category: string;
  expected_category: string;
  diagnosis_confidence: number;
  details: string;
}

export interface EvaluationSummary {
  overall_precision: number;
  overall_recall: number;
  overall_f1: number;
  overall_false_positive_rate: number;
  diagnosis_accuracy: number;
  scenario_results: EvaluationMetricResult[];
  evaluated_at: string;
}

export interface SampleCatalogItem {
  id: string;
  title: string;
  category: string;
  description: string;
  filename: string;
  recommended_for: string;
}

// API methods
export const api = {
  // Stats
  async getDashboardStats(runId?: string): Promise<DashboardStats> {
    const url = runId ? `${API_BASE}/analysis/stats?run_id=${runId}` : `${API_BASE}/analysis/stats`;
    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) throw new Error("Failed to fetch dashboard stats");
    return res.json();
  },

  // Upload
  async uploadFile(file: File, contamination?: number, windowSeconds?: number): Promise<AnalysisRun> {
    const formData = new FormData();
    formData.append("file", file);
    if (contamination) formData.append("contamination", contamination.toString());
    if (windowSeconds) formData.append("correlation_window", windowSeconds.toString());

    const res = await fetch(`${API_BASE}/upload`, {
      method: "POST",
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Upload failed" }));
      throw new Error(err.detail || "Upload failed");
    }
    return res.json();
  },

  async loadSample(sampleName: string): Promise<AnalysisRun> {
    const res = await fetch(`${API_BASE}/upload/sample/${sampleName}`, {
      method: "POST",
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Sample load failed" }));
      throw new Error(err.detail || "Sample load failed");
    }
    return res.json();
  },

  // Runs & Logs
  async getRuns(): Promise<AnalysisRun[]> {
    const res = await fetch(`${API_BASE}/analysis/runs`, { cache: "no-store" });
    if (!res.ok) throw new Error("Failed to fetch runs");
    return res.json();
  },

  async clearRealData(): Promise<{
    message: string;
    deleted: { runs: number; logs: number; anomalies: number; incidents: number };
  }> {
    const res = await fetch(`${API_BASE}/analysis/real-data`, { method: "DELETE" });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Failed to clear real data" }));
      throw new Error(err.detail || "Failed to clear real data");
    }
    return res.json();
  },

  async getRun(runId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/analysis/runs/${runId}`, { cache: "no-store" });
    if (!res.ok) throw new Error("Failed to fetch run detail");
    return res.json();
  },

  async getRunLogs(
    runId: string,
    page: number = 1,
    pageSize: number = 50,
    severity?: string,
    isAnomaly?: boolean,
    search?: string
  ): Promise<{ total: number; page: number; page_size: number; total_pages: number; items: LogEntry[] }> {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    if (severity && severity !== "ALL") params.append("severity", severity);
    if (isAnomaly !== undefined) params.append("is_anomaly", isAnomaly.toString());
    if (search) params.append("search", search);

    const res = await fetch(`${API_BASE}/analysis/runs/${runId}/logs?${params.toString()}`, { cache: "no-store" });
    if (!res.ok) throw new Error("Failed to fetch run logs");
    return res.json();
  },

  // Incidents
  async getIncidents(params?: {
    run_id?: string;
    severity?: string;
    category?: string;
    status?: string;
    search?: string;
  }): Promise<Incident[]> {
    const query = new URLSearchParams();
    if (params?.run_id) query.append("run_id", params.run_id);
    if (params?.severity && params.severity !== "ALL") query.append("severity", params.severity);
    if (params?.category && params.category !== "ALL") query.append("category", params.category);
    if (params?.status && params.status !== "ALL") query.append("status", params.status);
    if (params?.search) query.append("search", params.search);

    const res = await fetch(`${API_BASE}/incidents?${query.toString()}`, { cache: "no-store" });
    if (!res.ok) throw new Error("Failed to fetch incidents");
    return res.json();
  },

  async getIncident(id: string): Promise<Incident> {
    const res = await fetch(`${API_BASE}/incidents/${id}`, { cache: "no-store" });
    if (!res.ok) throw new Error("Failed to fetch incident details");
    return res.json();
  },

  async updateIncidentStatus(id: string, status: string): Promise<Incident> {
    const res = await fetch(`${API_BASE}/incidents/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
    });
    if (!res.ok) throw new Error("Failed to update incident status");
    return res.json();
  },

  // Reports
  getPdfReportUrl(incidentId: string): string {
    return `${API_BASE}/reports/incident/${incidentId}/pdf`;
  },

  getJsonReportUrl(incidentId: string): string {
    return `${API_BASE}/reports/incident/${incidentId}/json`;
  },

  // Samples
  async getSamples(): Promise<SampleCatalogItem[]> {
    const res = await fetch(`${API_BASE}/samples`, { cache: "no-store" });
    if (!res.ok) throw new Error("Failed to fetch samples");
    return res.json();
  },

  // Settings
  async getSettings(): Promise<SettingsData> {
    const res = await fetch(`${API_BASE}/settings`, { cache: "no-store" });
    if (!res.ok) throw new Error("Failed to fetch settings");
    return res.json();
  },

  async updateSettings(data: Partial<SettingsData> & { jev_api_key?: string }): Promise<SettingsData> {
    const res = await fetch(`${API_BASE}/settings`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to update settings");
    return res.json();
  },

  // Evaluation
  async getEvaluation(): Promise<EvaluationSummary> {
    const res = await fetch(`${API_BASE}/evaluation/latest`, { cache: "no-store" });
    if (!res.ok) throw new Error("Failed to fetch evaluation metrics");
    return res.json();
  },

  async runEvaluation(): Promise<EvaluationSummary> {
    const res = await fetch(`${API_BASE}/evaluation/run`, {
      method: "POST",
    });
    if (!res.ok) throw new Error("Failed to run evaluation benchmark");
    return res.json();
  },

  // Health
  async checkHealth(): Promise<{ status: string; demo_mode: boolean; jev_configured: boolean }> {
    const res = await fetch(`${API_BASE}/health`, { cache: "no-store" });
    if (!res.ok) throw new Error("Backend offline");
    return res.json();
  }
};
