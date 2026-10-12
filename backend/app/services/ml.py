"""Multi-Model Machine Learning Service for Agricultural GVA/GDP Prediction.

Implements and benchmarks 5 regression models:
1. Linear Regression (OLS / baseline)
2. Random Forest Regressor
3. Gradient Boosting Regressor
4. XGBoost Regressor
5. Extra Trees Regressor

Evaluates models on held-out chronological test years (MAE, RMSE, R2, MAPE),
automatically selects the best performing model empirically, and stores versioned runs.
"""

import hashlib
import re
import secrets
import time
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesRegressor, GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor

from app.constants import (
    FEATURE_COLUMNS,
    LOCAL_MODEL_CACHE_DIR,
    MODEL_NAMES,
    OFFICIAL_CLIMATE_METHOD,
    OFFICIAL_COLLECTION,
    OFFICIAL_MODEL_STORAGE_PREFIX,
    OFFICIAL_TARGET_LABEL,
    OFFICIAL_TARGET_SOURCE,
    TARGET_COLUMN,
)
from app.services.db_storage import get_db, get_storage
from app.services.ingestion.states import INDIAN_STATES


_RUN_ID_PATTERN = re.compile(r"^run_\d{8}_\d{6}_[0-9a-f]{8}$")
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def _json_safe(value: Any) -> Any:
    """Convert model metadata into values accepted by strict JSON encoders."""
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, np.generic):
        return _json_safe(value.item())
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def state_slug(state: str) -> str:
    return state.strip().lower().replace(" ", "_")


def model_feature_columns(training_states: list[str]) -> list[str]:
    return FEATURE_COLUMNS + [f"state__{state_slug(state)}" for state in training_states]


def model_features(df: pd.DataFrame, training_states: list[str]) -> pd.DataFrame:
    """Build the same state fixed-effect columns for training and inference."""
    features = df[FEATURE_COLUMNS].copy()
    for state in training_states:
        features[f"state__{state_slug(state)}"] = df["state"].eq(state).astype(int)
    return features


def _official_panel_signature(db) -> tuple[str, int] | None:
    """Accept only one fully tagged official panel, never mixed or legacy rows."""
    rows = [doc.to_dict() for doc in db.collection(OFFICIAL_COLLECTION).stream()]
    if not rows:
        return None
    hashes = {row.get("panel_sha256") for row in rows}
    if (len(hashes) != 1 or
            any(row.get("source") != OFFICIAL_TARGET_SOURCE or
                row.get("climate_method") != OFFICIAL_CLIMATE_METHOD for row in rows)):
        return None
    digest = next(iter(hashes))
    if not isinstance(digest, str) or not _SHA256_PATTERN.fullmatch(digest):
        return None
    keys = [(row.get("state"), row.get("year")) for row in rows]
    if len(set(keys)) != len(keys):
        return None
    if set(row.get("state") for row in rows) != set(INDIAN_STATES):
        return None
    return digest, len(rows)


def fetch_climate_dataframe() -> pd.DataFrame:
    """Fetch cleaned climate and economic records from the active storage engine."""
    db = get_db()
    docs = db.collection(OFFICIAL_COLLECTION).stream()
    rows = [doc.to_dict() for doc in docs]
    if rows:
        hashes = {row.get("panel_sha256") for row in rows}
        if (len(hashes) != 1 or
                any(row.get("source") != OFFICIAL_TARGET_SOURCE or
                    row.get("climate_method") != OFFICIAL_CLIMATE_METHOD for row in rows)):
            rows = []
    if not rows:
        return pd.DataFrame(
            columns=[
                "state",
                "year",
                "rainfall_mm",
                "avg_temperature_c",
                "oni_index",
                "agricultural_gdp_cr",
            ]
        )
    df = pd.DataFrame(rows)
    # Ensure numeric columns
    for col in ["year", "rainfall_mm", "avg_temperature_c", "oni_index", "agricultural_gdp_cr"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def time_aware_split(df: pd.DataFrame, test_fraction: float = 0.25):
    """Chronological split preserving state-year panel integrity.

    Avoids lookahead bias by training strictly on earlier years and testing on latest held-out years.
    """
    years = sorted(int(y) for y in df["year"].dropna().unique())
    if len(years) < 2:
        raise ValueError("Need at least 2 distinct years in panel for train/test split.")

    split_idx = max(1, int(len(years) * (1 - test_fraction)))
    train_years = years[:split_idx]
    test_years = years[split_idx:] or [years[-1]]

    if not test_years or set(test_years) == set(train_years):
        test_years = [years[-1]]
        train_years = years[:-1]

    train_df = df[df["year"].isin(train_years)].copy()
    test_df = df[df["year"].isin(test_years)].copy()
    return train_df, test_df, train_years, test_years


def _build_model(name: str):
    """Instantiate model with defensible baseline hyperparameters."""
    if name == "linear_regression":
        return LinearRegression()
    elif name == "random_forest":
        return RandomForestRegressor(
            n_estimators=150,
            max_depth=10,
            min_samples_split=3,
            min_samples_leaf=2,
            random_state=42,
        )
    elif name == "gradient_boosting":
        return GradientBoostingRegressor(
            n_estimators=150,
            learning_rate=0.08,
            max_depth=4,
            subsample=0.85,
            random_state=42,
        )
    elif name == "xgboost":
        return XGBRegressor(
            n_estimators=150,
            learning_rate=0.08,
            max_depth=4,
            subsample=0.85,
            colsample_bytree=0.85,
            random_state=42,
            objective="reg:squarederror",
        )
    elif name == "extra_trees":
        return ExtraTreesRegressor(
            n_estimators=150,
            max_depth=10,
            min_samples_split=3,
            min_samples_leaf=2,
            random_state=42,
        )
    raise ValueError(f"Unknown model architecture: {name}")


def _feature_importance_dict(name: str, model, feature_columns: list[str]) -> dict[str, float]:
    """Extract normalized feature importance across tree and linear models."""
    if hasattr(model, "feature_importances_"):
        importances = model.feature_importances_
    elif hasattr(model, "coef_"):
        coefs = np.abs(model.coef_)
        total = float(coefs.sum()) or 1.0
        importances = coefs / total
    else:
        importances = np.ones(len(feature_columns)) / len(feature_columns)

    total = float(np.sum(importances)) or 1.0
    values = {col: round(float(imp / total), 4) for col, imp in zip(feature_columns, importances)}
    values["state_identity"] = round(sum(v for k, v in values.items() if k.startswith("state__")), 4)
    return {key: values.get(key, 0.0) for key in FEATURE_COLUMNS} | {
        "state_identity": values["state_identity"]
    }


def _evaluate_model(name: str, model, X_test, y_test, elapsed_sec: float,
                    feature_columns: list[str]) -> dict[str, Any]:
    preds = model.predict(X_test)
    mae = float(mean_absolute_error(y_test, preds))
    rmse = float(np.sqrt(mean_squared_error(y_test, preds)))
    r2 = float(r2_score(y_test, preds))

    # Calculate MAPE where safe
    non_zero = y_test != 0
    mape = (
        float(np.mean(np.abs((y_test[non_zero] - preds[non_zero]) / y_test[non_zero]))) * 100.0
        if np.any(non_zero)
        else 0.0
    )

    return {
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "r2": round(r2, 4),
        "mape": round(mape, 2),
        "training_time_sec": round(elapsed_sec, 3),
        "hyperparameters": _json_safe(
            {
                k: v
                for k, v in model.get_params().items()
                if isinstance(v, (int, float, str, bool))
            }
        ),
        "feature_importance": _feature_importance_dict(name, model, feature_columns),
    }


def _artifact_paths(name: str, run_id: str) -> tuple[Path, str]:
    if name not in MODEL_NAMES or not _RUN_ID_PATTERN.fullmatch(run_id):
        raise ValueError("Invalid official model name or run identifier")
    local_path = Path(LOCAL_MODEL_CACHE_DIR) / "official" / run_id / f"{name}.joblib"
    storage_path = f"{OFFICIAL_MODEL_STORAGE_PREFIX}/{run_id}/{name}.joblib"
    return local_path, storage_path


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as model_file:
        for chunk in iter(lambda: model_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _save_model(name: str, model, run_id: str) -> str:
    local_path, storage_path = _artifact_paths(name, run_id)
    local_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, local_path, compress=3)
    digest = _file_sha256(local_path)
    get_storage().blob(storage_path).upload_from_filename(str(local_path))
    return digest


def load_model(name: str, metrics: dict[str, Any] | None = None):
    """Load only an artifact identified and hashed by the active official run."""
    metrics = metrics or get_model_metrics()
    if not metrics or name not in metrics.get("models", {}):
        raise FileNotFoundError(f"No active official model named '{name}'")
    run_id = metrics.get("run_id", "")
    local_path, storage_path = _artifact_paths(name, run_id)
    expected_sha = metrics.get("artifact_sha256", {}).get(name)
    if not isinstance(expected_sha, str) or not _SHA256_PATTERN.fullmatch(expected_sha):
        raise ValueError(f"No verified artifact checksum for {name}")
    if not local_path.is_file() or _file_sha256(local_path) != expected_sha:
        blob = get_storage().blob(storage_path)
        if not blob.exists():
            raise FileNotFoundError(f"Verified official model '{name}' is missing; retrain the five models")
        local_path.parent.mkdir(parents=True, exist_ok=True)
        blob.download_to_filename(str(local_path))
    if _file_sha256(local_path) != expected_sha:
        raise ValueError(f"Official model '{name}' failed its artifact checksum")
    model = joblib.load(local_path)
    expected_features = metrics.get("feature_columns", [])
    if hasattr(model, "feature_names_in_") and list(model.feature_names_in_) != expected_features:
        raise ValueError(f"Official model '{name}' has incompatible feature columns")
    if hasattr(model, "n_features_in_") and model.n_features_in_ != len(expected_features):
        raise ValueError(f"Official model '{name}' has incompatible feature count")
    return model


def _linear_climate_permutation_on_test(model, test_df: pd.DataFrame,
                                        training_states: list[str], repeats: int = 20) -> dict[str, Any]:
    """Measure held-out RMSE change when each climate input is shuffled.

    Weather is shuffled across test years *within* each state, while ONI is
    shuffled as one annual series shared by all states. State identity stays
    fixed. This measures model reliance, not causal climate effects.
    """
    test_df = test_df.sort_values(["year", "state"]).reset_index(drop=True)
    y_test = test_df[TARGET_COLUMN].to_numpy(dtype=float)
    baseline = float(np.sqrt(mean_squared_error(
        y_test, model.predict(model_features(test_df, training_states))
    )))
    state_rows = [group.index.to_numpy() for _, group in test_df.groupby("state", sort=True)]
    annual_oni = test_df.groupby("year")["oni_index"].first()
    if not test_df.groupby("year")["oni_index"].nunique().eq(1).all():
        raise ValueError("Held-out ONI must have one value per financial year")

    rng = np.random.default_rng(42)
    changes: dict[str, float] = {}
    for feature in FEATURE_COLUMNS:
        rmse_changes = []
        for _ in range(repeats):
            perturbed = test_df.copy()
            if feature == "oni_index":
                shuffled_years = dict(zip(annual_oni.index, rng.permutation(annual_oni.to_numpy())))
                perturbed[feature] = perturbed["year"].map(shuffled_years)
            else:
                for rows in state_rows:
                    perturbed.loc[rows, feature] = rng.permutation(test_df.loc[rows, feature].to_numpy())
            shuffled_rmse = float(np.sqrt(mean_squared_error(
                y_test, model.predict(model_features(perturbed, training_states))
            )))
            rmse_changes.append(shuffled_rmse - baseline)
        changes[feature] = round(float(np.mean(rmse_changes)), 2)

    return {
        "baseline_rmse_cr": round(baseline, 2),
        "rmse_change_cr": changes,
        "repeats": repeats,
        "test_years": sorted(int(year) for year in test_df["year"].unique()),
        "method": "within_state_weather_and_shared_year_oni_permutation",
    }


@lru_cache(maxsize=4)
def _cached_linear_climate_permutation(run_id: str, panel_sha256: str) -> dict[str, Any]:
    metrics = get_model_metrics()
    if not metrics or (metrics["run_id"], metrics["panel_sha256"]) != (run_id, panel_sha256):
        raise ValueError("The active panel or model run changed during evaluation")
    test_df = fetch_climate_dataframe()
    test_df = test_df[test_df["year"].isin(metrics["test_years"])].copy()
    if len(test_df) != metrics["test_rows"]:
        raise ValueError("Held-out panel rows do not match the active model run")
    model = load_model("linear_regression", metrics)
    result = _linear_climate_permutation_on_test(model, test_df, metrics["training_states"])
    if abs(result["baseline_rmse_cr"] - metrics["models"]["linear_regression"]["rmse"]) > 0.02:
        raise ValueError("Held-out panel and model RMSE do not match the saved evaluation")
    return result


def get_linear_climate_permutation(metrics: dict[str, Any]) -> dict[str, Any]:
    """Evaluate the current official model; never fit or modify its artifact."""
    return _cached_linear_climate_permutation(metrics["run_id"], metrics["panel_sha256"])


def train_all_models(panel_df: pd.DataFrame | None = None) -> dict[str, Any]:
    """Train only on the validated user-supplied official panel."""
    if panel_df is None:
        raise ValueError("Supply data/processed/official_panel.csv through scripts/train_models.py; legacy database training is disabled.")
    df = panel_df.copy()
    if df.empty:
        raise ValueError("Official panel is empty")

    if ("target_source" not in df or df["target_source"].isna().any() or
            set(df["target_source"]) != {OFFICIAL_TARGET_SOURCE}):
        raise ValueError("Only the RBI/NSO 2011-12-base crop GSVA target is accepted")
    if ("climate_method" not in df or df["climate_method"].isna().any() or
            set(df["climate_method"]) != {OFFICIAL_CLIMATE_METHOD}):
        raise ValueError("Panel lacks the validated new-raw-climate method")
    if ("panel_sha256" not in df or df["panel_sha256"].isna().any() or
            len(set(df["panel_sha256"])) != 1 or
            not _SHA256_PATTERN.fullmatch(str(df["panel_sha256"].iloc[0]))):
        raise ValueError("Panel lacks a single validated source checksum")

    required_cols = ["state", "year"] + FEATURE_COLUMNS + [TARGET_COLUMN]
    missing_cols = sorted(set(required_cols) - set(df.columns))
    if missing_cols:
        raise ValueError(f"Official panel is missing columns: {missing_cols}")
    if df[required_cols].isna().any().any():
        raise ValueError("Official panel has nulls; review the preparation report")
    if df.duplicated(["state", "year"]).any():
        raise ValueError("Official panel has duplicate state-year records")
    df = df.dropna(subset=required_cols)
    if len(df) < 10:
        raise ValueError(f"Insufficient panel records ({len(df)} rows). Need at least 10 observations.")

    train_df, test_df, train_years, test_years = time_aware_split(df)

    training_states = sorted(train_df["state"].astype(str).unique().tolist())
    if set(df["state"].astype(str)) != set(training_states):
        raise ValueError("Some states appear only in held-out years; cannot estimate their state effect")
    if set(training_states) != set(INDIAN_STATES):
        raise ValueError("Official training panel must contain all 28 Indian states")
    feature_columns = model_feature_columns(training_states)

    X_train = model_features(train_df, training_states)
    y_train = train_df[TARGET_COLUMN]
    X_test = model_features(test_df, training_states)
    y_test = test_df[TARGET_COLUMN]

    run_id = f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(4)}"
    metrics: dict[str, Any] = {}
    artifact_hashes: dict[str, str] = {}

    for name in MODEL_NAMES:
        start_t = time.perf_counter()
        model = _build_model(name)
        model.fit(X_train, y_train)
        elapsed = time.perf_counter() - start_t

        metrics[name] = _evaluate_model(name, model, X_test, y_test, elapsed, feature_columns)
        artifact_hashes[name] = _save_model(name, model, run_id)

    # Empirical selection: Lowest RMSE on held-out test set
    best_model = min(metrics, key=lambda m: metrics[m]["rmse"])
    trained_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    payload = {
        "run_id": run_id,
        "trained_at": trained_at,
        "train_years": [int(y) for y in train_years],
        "test_years": [int(y) for y in test_years],
        "panel_rows": len(df),
        "training_states": training_states,
        "feature_columns": feature_columns,
        "data_source": OFFICIAL_TARGET_SOURCE,
        "climate_method": OFFICIAL_CLIMATE_METHOD,
        "panel_sha256": str(df["panel_sha256"].iloc[0]),
        "artifact_sha256": artifact_hashes,
        "train_rows": len(train_df),
        "test_rows": len(test_df),
        "models": metrics,
        "best_model": best_model,
        "selection_metric": "rmse",
        "target_variable": OFFICIAL_TARGET_LABEL,
    }

    db = get_db()
    db.collection("model_metrics").document("current").set(payload)
    db.collection("model_runs").document(run_id).set(payload)

    return payload


def get_model_metrics() -> dict[str, Any] | None:
    db = get_db()
    doc = db.collection("model_metrics").document("current").get()
    if not doc.exists:
        return None
    metrics = _json_safe(doc.to_dict())
    if (metrics.get("data_source") != OFFICIAL_TARGET_SOURCE or
            metrics.get("climate_method") != OFFICIAL_CLIMATE_METHOD):
        return None
    active_panel = _official_panel_signature(db)
    if active_panel != (metrics.get("panel_sha256"), metrics.get("panel_rows")):
        return None
    training_states = metrics.get("training_states")
    if (not isinstance(training_states, list) or
            not all(isinstance(state, str) for state in training_states) or
            training_states != sorted(INDIAN_STATES) or
            metrics.get("feature_columns") != model_feature_columns(training_states) or
            not _RUN_ID_PATTERN.fullmatch(str(metrics.get("run_id", "")))):
        return None
    models = metrics.get("models")
    hashes = metrics.get("artifact_sha256")
    if (not isinstance(models, dict) or set(models) != set(MODEL_NAMES) or
            not isinstance(hashes, dict) or set(hashes) != set(MODEL_NAMES) or
            any(not isinstance(digest, str) or not _SHA256_PATTERN.fullmatch(digest)
                for digest in hashes.values())):
        return None
    if (not isinstance(metrics.get("train_years"), list) or
            not isinstance(metrics.get("test_years"), list) or
            not metrics["train_years"] or not metrics["test_years"] or
            set(metrics["train_years"]) & set(metrics["test_years"])):
        return None
    return metrics


def get_all_model_runs() -> list[dict[str, Any]]:
    db = get_db()
    active_panel = _official_panel_signature(db)
    if not active_panel:
        return []
    docs = db.collection("model_runs").stream()
    runs = [_json_safe(d.to_dict()) for d in docs]
    runs = [run for run in runs if run.get("data_source") == OFFICIAL_TARGET_SOURCE and
            (run.get("panel_sha256"), run.get("panel_rows")) == active_panel]
    runs.sort(key=lambda r: r.get("trained_at", ""), reverse=True)
    return runs


def get_state_historical_avg_gdp(state: str, metrics: dict[str, Any] | None = None) -> float:
    db = get_db()
    metrics = metrics or get_model_metrics()
    if not metrics:
        raise ValueError("No official-data models trained yet")
    docs = db.collection(OFFICIAL_COLLECTION).where("state", "==", state).stream()
    values = [d.to_dict().get("agricultural_gdp_cr") for d in docs
              if d.to_dict().get("panel_sha256") == metrics.get("panel_sha256") and
              d.to_dict().get("year") in metrics["train_years"]]
    values = [float(v) for v in values if v is not None]
    if not values:
        raise ValueError(f"No historical agricultural target for {state}. Prepare its panel before predicting.")
    return float(np.mean(values))


def predict_gdp(
    state: str,
    rainfall: float,
    temperature: float,
    oni_index: float,
    model_name: str | None = None,
) -> dict[str, Any]:
    metrics = get_model_metrics()
    if not metrics:
        raise ValueError("No trained models found. Train the five models after preparing a panel.")
    # Older runs did not record state coverage. Current DB rows cannot prove
    # which states were in an older model's training panel.
    trained_states = list(metrics.get("training_states") or [])
    if not trained_states:
        raise ValueError("Current model run does not record training-state coverage. Retrain the five models before predicting.")
    if state not in trained_states:
        raise ValueError(f"{state} was not in the trained panel. Retrain with this state's data first.")
    historical_avg = get_state_historical_avg_gdp(state, metrics)
    inputs = pd.DataFrame([{
        "state": state,
        "rainfall_mm": rainfall,
        "avg_temperature_c": temperature,
        "oni_index": oni_index,
    }])
    features = model_features(inputs, trained_states)

    if model_name is not None and model_name not in MODEL_NAMES:
        raise ValueError(f"Unknown model: {model_name}")
    models_to_run = [model_name] if model_name else MODEL_NAMES
    predictions = []

    from app.constants import MODEL_DISPLAY_NAMES

    for name in models_to_run:
        model = load_model(name, metrics)
        predicted = float(model.predict(features)[0])
        abs_change = round(predicted - historical_avg, 2)
        impact_pct = round((abs_change / historical_avg) * 100, 2) if historical_avg > 0 else 0.0
        predictions.append(
            {
                "model": name,
                "model_name_display": MODEL_DISPLAY_NAMES.get(name, name),
                "predicted_gdp_cr": round(predicted, 2),
                "predicted_impact_pct": impact_pct,
                "absolute_change_cr": abs_change,
            }
        )

    if not predictions:
        raise ValueError("Could not run predictions. Models not yet trained.")

    ensemble = round(
        float(np.mean([p["predicted_gdp_cr"] for p in predictions])), 2
    )
    ensemble_impact = round(
        float(np.mean([p["predicted_impact_pct"] for p in predictions])), 2
    )

    return {
        "state": state,
        "historical_avg_gdp_cr": round(historical_avg, 2),
        "predictions": predictions,
        "ensemble_gdp_cr": ensemble,
        "ensemble_impact_pct": ensemble_impact,
    }


def log_prediction(
    state: str,
    rainfall: float,
    temperature: float,
    oni_index: float,
    predictions: list[dict],
) -> None:
    db = get_db()
    metrics = get_model_metrics()
    if not metrics:
        return
    for pred in predictions:
        db.collection("predictions").add(
            {
                "state": state,
                "input_rainfall": rainfall,
                "input_temperature": temperature,
                "input_oni": oni_index,
                "model_used": pred["model"],
                "predicted_gdp_cr": pred["predicted_gdp_cr"],
                "predicted_impact_pct": pred["predicted_impact_pct"],
                "panel_sha256": metrics["panel_sha256"],
                "model_run_id": metrics["run_id"],
                "created_at": datetime.now(timezone.utc)
                .isoformat()
                .replace("+00:00", "Z"),
            }
        )
