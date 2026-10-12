from pydantic import BaseModel, Field
from typing import Any, Literal, Optional


ModelName = Literal[
    "linear_regression",
    "random_forest",
    "gradient_boosting",
    "xgboost",
    "extra_trees",
]


class UploadSummary(BaseModel):
    rows_processed: int
    rows_upserted: int
    rows_skipped: int
    skip_reasons: list[str]
    storage_path: str


class FeatureImportance(BaseModel):
    rainfall_mm: float
    avg_temperature_c: float
    oni_index: float
    rainfall_anomaly: Optional[float] = 0.0
    temp_anomaly: Optional[float] = 0.0


class ModelMetrics(BaseModel):
    mae: float
    rmse: float
    r2: float
    mape: Optional[float] = None
    training_time_sec: Optional[float] = None
    hyperparameters: Optional[dict[str, Any]] = None
    feature_importance: dict[str, float]


class LinearClimatePermutation(BaseModel):
    baseline_rmse_cr: float
    rmse_change_cr: dict[str, float]
    repeats: int
    test_years: list[int]
    method: str


class TrainResponse(BaseModel):
    run_id: Optional[str] = None
    trained_at: str
    train_years: list[int]
    test_years: list[int]
    panel_rows: int | None = None
    train_rows: int | None = None
    test_rows: int | None = None
    models: dict[str, ModelMetrics]
    best_model: ModelName
    selection_metric: str = "rmse"
    target_variable: str = "Bundled agricultural GDP sample (official source and units unverified)"
    linear_permutation: Optional[LinearClimatePermutation] = None


class PredictRequest(BaseModel):
    state: str
    rainfall: float = Field(..., ge=0)
    temperature: float
    oni_index: float
    model: Optional[ModelName] = None


class SinglePrediction(BaseModel):
    model: ModelName
    model_name_display: Optional[str] = None
    predicted_gdp_cr: float
    predicted_impact_pct: float
    absolute_change_cr: Optional[float] = None


class PredictResponse(BaseModel):
    state: str
    historical_avg_gdp_cr: float
    predictions: list[SinglePrediction]
    ensemble_gdp_cr: Optional[float] = None
    ensemble_impact_pct: Optional[float] = None
    disclaimer: str


class ScenarioRequest(BaseModel):
    state: str
    rainfall: float = Field(..., ge=0)
    temperature: float
    oni_index: float
    preset_name: Optional[str] = None
    model: Optional[ModelName] = None


class ScenarioSingleResult(BaseModel):
    model: ModelName
    model_name_display: str
    predicted_gdp_cr: float
    predicted_impact_pct: float
    absolute_change_cr: float


class ScenarioResponse(BaseModel):
    state: str
    historical_avg_gdp_cr: float
    preset_name: Optional[str] = None
    inputs: dict[str, float]
    predictions: list[ScenarioSingleResult]
    best_model_result: ScenarioSingleResult
    ensemble_gdp_cr: Optional[float] = None
    ensemble_impact_pct: Optional[float] = None
    interpretation: str
    disclaimer: str


class YearGdpPoint(BaseModel):
    year: int
    agricultural_gdp_cr: float


class StateSummary(BaseModel):
    state: str
    trend: list[YearGdpPoint]
    prediction_available: bool = False


class StatesResponse(BaseModel):
    states: list[StateSummary]


class HistoryRow(BaseModel):
    year: int
    rainfall_mm: float
    avg_temperature_c: float
    oni_index: float
    agricultural_gdp_cr: float
    rainfall_anomaly: Optional[float] = None
    temp_anomaly: Optional[float] = None


class StateHistoryResponse(BaseModel):
    state: str
    history: list[HistoryRow]


class DashboardSummary(BaseModel):
    states_count: int
    years_count: Optional[int] = None
    records_count: Optional[int] = None
    year_min: Optional[int]
    year_max: Optional[int]
    best_model: Optional[ModelName]
    best_r2: Optional[float] = None
    best_rmse: Optional[float] = None
    latest_prediction: Optional[dict]


class ClimateDataRow(BaseModel):
    state: str
    year: int
    rainfall_mm: float
    avg_temperature_c: float
    oni_index: float
    agricultural_gdp_cr: float


class ClimateDataResponse(BaseModel):
    rows: list[ClimateDataRow]
    total: int


class ErrorResponse(BaseModel):
    detail: str


class SourceLogEntry(BaseModel):
    source: str
    provider: str
    status: str
    records: int | None = None
    url: str | None = None
    error: str | None = None
    detail: str | None = None


class CleaningReport(BaseModel):
    rows_in: int
    rows_out: int
    rows_dropped: int
    duplicates_removed: int = 0
    imputed_cells: int = 0
    warnings: list[str] = []
    steps: list[str] = []
    storage_path: str | None = None


class PipelineRunResponse(BaseModel):
    status: str
    rainfall_source: str | None = None
    started_at: str
    completed_at: str | None = None
    failed_at: str | None = None
    current_step: str | None = None
    sources: list[dict] | None = None
    cleaning: dict | None = None
    storage: dict | None = None
    training: TrainResponse | None = None
    error: str | None = None


class PipelineStatusResponse(BaseModel):
    status: str = "idle"
    rainfall_source: str | None = None
    message: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    failed_at: str | None = None
    current_step: str | None = None
    sources: list[dict] | None = None
    cleaning: dict | None = None
    storage: dict | None = None
    training: dict | None = None
    error: str | None = None


# Search & AI Assistant Schemas
class SearchRequest(BaseModel):
    query: str


class SearchCitation(BaseModel):
    source: str
    title: str
    url: Optional[str] = None
    snippet: str


class SearchResponse(BaseModel):
    query: str
    intent: Literal["factual", "historical", "prediction", "scenario", "mixed"]
    answer: str
    project_data: Optional[dict[str, Any]] = None
    citations: list[SearchCitation]
    disclaimer: str


class ModelRunRecord(BaseModel):
    run_id: str
    created_at: str
    dataset_version: str
    train_years: list[int]
    test_years: list[int]
    models: dict[str, Any]
    best_model: str
    parameters: Optional[dict[str, Any]] = None
