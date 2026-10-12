"""Shared constants for ML model identifiers, feature specifications, and academic definitions."""
from pathlib import Path

MODEL_NAMES = [
    "linear_regression",
    "random_forest",
    "gradient_boosting",
    "xgboost",
    "extra_trees",
]

MODEL_DISPLAY_NAMES = {
    "linear_regression": "Linear Regression (OLS / Baseline)",
    "random_forest": "Random Forest Regressor",
    "gradient_boosting": "Gradient Boosting Regressor",
    "xgboost": "XGBoost Regressor",
    "extra_trees": "Extra Trees Regressor",
}

# Base climate features
BASE_FEATURE_COLUMNS = [
    "rainfall_mm",
    "avg_temperature_c",
    "oni_index",
]

# Engineered panel features
ENGINEERED_FEATURE_COLUMNS = [
    "rainfall_anomaly",
    "temp_anomaly",
    "lagged_rainfall_mm",
    "lagged_temperature_c",
    "lagged_oni",
]

FEATURE_COLUMNS = BASE_FEATURE_COLUMNS

TARGET_COLUMN = "agricultural_gdp_cr"
TARGET_ALT_COLUMN = "agricultural_gva_cr"
TARGET_LABEL = "Bundled agricultural GDP sample (official source and units unverified)"
OFFICIAL_TARGET_LABEL = "RBI/NSO GSVA Agriculture (crops), constant 2011-12 prices (INR crore)"
OFFICIAL_TARGET_SOURCE = "rbi_2011_12"
OFFICIAL_COLLECTION = "official_climate_gdp_data"
OFFICIAL_CLIMATE_METHOD = "nearest_representative_grid_point_fy_apr_mar"
OFFICIAL_MODEL_STORAGE_PREFIX = "models/official"

REQUIRED_CSV_COLUMNS = [
    "state",
    "year",
    "rainfall_mm",
    "avg_temperature_c",
    "oni_index",
    "agricultural_gdp_cr",
]

BASE_DIR = Path(__file__).resolve().parents[2]
LOCAL_MODEL_CACHE_DIR = str(BASE_DIR / "data" / "models")
LOCAL_DATA_DIR = str(BASE_DIR / "data")

DISCLAIMER = (
    "This platform provides analytical estimates based on historical climate and economic data "
    "and machine-learning models. Results are not official government forecasts and should not "
    "be interpreted as proof that El Niño alone determines agricultural economic performance. "
    "The target is RBI/NSO crop GSVA at constant 2011-12 prices; climate inputs represent one grid point per state, not statewide averages."
)
