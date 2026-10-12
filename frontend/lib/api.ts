import { ModelName } from "./constants";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      ...(init?.body instanceof FormData
        ? {}
        : { "Content-Type": "application/json" }),
      ...init?.headers,
    },
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      /* ignore */
    }
    throw new ApiError(detail, res.status);
  }

  return res.json();
}

export interface FeatureImportance {
  rainfall_mm: number;
  avg_temperature_c: number;
  oni_index: number;
  [key: string]: number;
}

export interface ModelMetrics {
  mae: number;
  rmse: number;
  r2: number;
  mape?: number;
  training_time_sec?: number;
  hyperparameters?: Record<string, unknown>;
  feature_importance: Record<string, number>;
}

export interface LinearClimatePermutation {
  baseline_rmse_cr: number;
  rmse_change_cr: Record<string, number>;
  repeats: number;
  test_years: number[];
  method: string;
}

export interface ModelComparison {
  run_id?: string;
  trained_at: string;
  train_years: number[];
  test_years: number[];
  models: Record<ModelName, ModelMetrics>;
  best_model: ModelName;
  selection_metric?: string;
  target_variable?: string;
  linear_permutation?: LinearClimatePermutation | null;
}

export interface SinglePrediction {
  model: ModelName;
  model_name_display?: string;
  // Legacy backend key; the value is RBI/NSO crop GSVA, not total GDP.
  predicted_gdp_cr: number;
  predicted_impact_pct: number;
  absolute_change_cr?: number;
}

export interface PredictResponse {
  state: string;
  // Historical and ensemble "gdp" keys are legacy backend names for crop GSVA.
  historical_avg_gdp_cr: number;
  predictions: SinglePrediction[];
  ensemble_gdp_cr: number | null;
  ensemble_impact_pct?: number | null;
  disclaimer: string;
}

export interface ScenarioSingleResult {
  model: ModelName;
  model_name_display: string;
  predicted_gdp_cr: number;
  predicted_impact_pct: number;
  absolute_change_cr: number;
}

export interface ScenarioResponse {
  state: string;
  historical_avg_gdp_cr: number;
  preset_name?: string;
  inputs: {
    rainfall_mm: number;
    avg_temperature_c: number;
    oni_index: number;
  };
  predictions: ScenarioSingleResult[];
  best_model_result: ScenarioSingleResult;
  ensemble_gdp_cr?: number;
  ensemble_impact_pct?: number;
  interpretation: string;
  disclaimer: string;
}

export interface SearchCitation {
  source: string;
  title: string;
  url?: string;
  snippet: string;
}

export interface SearchResponse {
  query: string;
  intent: "factual" | "historical" | "prediction" | "scenario" | "mixed";
  answer: string;
  project_data?: unknown;
  citations: SearchCitation[];
  disclaimer: string;
}

export interface YearGdpPoint {
  year: number;
  agricultural_gdp_cr: number;
}

export interface StateSummary {
  state: string;
  trend: YearGdpPoint[];
  prediction_available: boolean;
}

export interface HistoryRow {
  year: number;
  rainfall_mm: number;
  avg_temperature_c: number;
  oni_index: number;
  agricultural_gdp_cr: number;
  rainfall_anomaly?: number;
  temp_anomaly?: number;
}

export interface DashboardSummary {
  states_count: number;
  years_count?: number;
  records_count?: number;
  year_min: number | null;
  year_max: number | null;
  best_model: ModelName | null;
  best_r2?: number;
  best_rmse?: number;
  latest_prediction: {
    state: string;
    predicted_impact_pct: number;
    model_used: string;
    created_at: string;
  } | null;
}

export interface UploadSummary {
  rows_processed: number;
  rows_upserted: number;
  rows_skipped: number;
  skip_reasons: string[];
  storage_path: string;
}

export interface ClimateRow extends HistoryRow {
  state: string;
}

export interface PipelineStatus {
  status: string;
  message?: string;
  started_at?: string;
  completed_at?: string;
  failed_at?: string;
  current_step?: string;
  sources?: Array<{
    source: string;
    provider: string;
    status: string;
    records?: number;
    url?: string;
    error?: string;
    detail?: string;
  }>;
  cleaning?: {
    rows_in: number;
    rows_out: number;
    rows_dropped: number;
    imputed_cells: number;
    steps?: string[];
    warnings?: string[];
  };
  storage?: { rows_upserted: number; archive_path?: string };
  training?: ModelComparison;
  error?: string;
}

export interface PipelineRunResponse extends PipelineStatus {
  training?: ModelComparison;
}

export const api = {
  getDashboardSummary: () =>
    request<DashboardSummary>("/api/dashboard/summary"),

  getModelComparison: () =>
    request<ModelComparison>("/api/models/comparison"),

  getModels: () =>
    request<{ models: Array<{ id: string; name: string; is_best: boolean; metrics: unknown }>; best_model: string }>("/api/models"),

  getModelRuns: () =>
    request<{ runs: unknown[]; total: number }>("/api/models/runs"),

  getStates: () =>
    request<{ states: StateSummary[] }>("/api/states"),

  getStateHistory: (state: string) =>
    request<{ state: string; history: HistoryRow[] }>(
      `/api/states/${encodeURIComponent(state)}/history`,
    ),

  predict: (body: {
    state: string;
    rainfall: number;
    temperature: number;
    oni_index: number;
    model?: ModelName;
  }) =>
    request<PredictResponse>("/api/predict", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  runScenario: (body: {
    state: string;
    rainfall: number;
    temperature: number;
    oni_index: number;
    preset_name?: string;
    model?: ModelName;
  }) =>
    request<ScenarioResponse>("/api/scenario", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  getScenarioPresets: () =>
    request<{ presets: Record<string, unknown> }>("/api/scenario/presets"),

  search: (query: string) =>
    request<SearchResponse>("/api/search", {
      method: "POST",
      body: JSON.stringify({ query }),
    }),

  train: () =>
    request<ModelComparison>("/api/train", { method: "POST" }),

  uploadCsv: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<UploadSummary>("/api/data/upload", {
      method: "POST",
      body: form,
    });
  },

  getClimateData: (params?: {
    state?: string;
    year_min?: number;
    year_max?: number;
  }) => {
    const qs = new URLSearchParams();
    if (params?.state) qs.set("state", params.state);
    if (params?.year_min != null) qs.set("year_min", String(params.year_min));
    if (params?.year_max != null) qs.set("year_max", String(params.year_max));
    const query = qs.toString();
    return request<{ rows: ClimateRow[]; total: number }>(
      `/api/data${query ? `?${query}` : ""}`,
    );
  },

  getExportUrl: (type: "panel" | "metrics", format: "csv" | "json") =>
    `${API_BASE}/api/export/${type}?format=${format}`,

  runPipeline: () =>
    request<PipelineStatus>("/api/pipeline/run", { method: "POST" }),

  getPipelineStatus: () =>
    request<PipelineStatus>("/api/pipeline/status"),
};

export { ApiError };
