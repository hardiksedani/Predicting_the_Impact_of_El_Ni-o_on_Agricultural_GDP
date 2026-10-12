"""Scenario analysis engine for simulating climate and El Niño impacts on Agricultural GVA/GDP.

Computes hypothetical scenario predictions across all trained regression models,
calculates deviation from historical baselines, and generates feature interpretations.
"""

from typing import Any, Optional
import numpy as np
import pandas as pd

from app.constants import (
    DISCLAIMER,
    MODEL_DISPLAY_NAMES,
    MODEL_NAMES,
)
from app.models.schemas import (
    ModelName,
    ScenarioRequest,
    ScenarioResponse,
    ScenarioSingleResult,
)
from app.services.ml import (
    get_model_metrics,
    get_state_historical_avg_gdp,
    load_model,
    model_features,
)

PRESET_CONFIGS: dict[str, dict[str, float]] = {
    "Normal / Neutral ENSO": {"oni_index": 0.0, "rainfall_multiplier": 1.0, "temp_delta": 0.0},
    "Weak El Niño": {"oni_index": 0.8, "rainfall_multiplier": 0.90, "temp_delta": 0.5},
    "Moderate El Niño": {"oni_index": 1.5, "rainfall_multiplier": 0.80, "temp_delta": 1.2},
    "Strong El Niño": {"oni_index": 2.2, "rainfall_multiplier": 0.70, "temp_delta": 2.0},
    "La Niña (Cool / Excess Monsoon)": {"oni_index": -1.2, "rainfall_multiplier": 1.15, "temp_delta": -0.4},
}


def _interpret_scenario_impact(impact_pct: float, state: str, preset_name: Optional[str]) -> str:
    preset_str = f"under {preset_name} conditions " if preset_name else ""
    if impact_pct <= -20.0:
        severity = "severe contraction"
    elif impact_pct <= -10.0:
        severity = "moderate contraction"
    elif impact_pct < -2.0:
        severity = "mild contraction"
    elif impact_pct <= 5.0:
        severity = "stable output"
    else:
        severity = "positive expansion"

    return (
        f"The model estimates a {severity} ({impact_pct:+.1f}%) for the {state} "
        f"sample {preset_str}relative to its historical baseline. "
        "This what-if comparison changes several inputs together and does not isolate "
        "a causal effect of rainfall, temperature, or ONI."
    )


def run_scenario_simulation(req: ScenarioRequest) -> ScenarioResponse:
    state = req.state.strip()
    metrics_data = get_model_metrics()
    if not metrics_data:
        raise ValueError("No official-data models trained yet. Run scripts/train_models.py manually.")
    training_states = list(metrics_data.get("training_states") or [])
    if state not in training_states:
        raise ValueError(f"{state} was not included in the official training panel.")
    baseline = get_state_historical_avg_gdp(state, metrics_data)
    best_model_name: ModelName = "xgboost"
    if metrics_data and "best_model" in metrics_data:
        best_model_name = metrics_data["best_model"]

    models_to_run = [req.model] if req.model else MODEL_NAMES

    features = model_features(pd.DataFrame([{
        "state": state,
        "rainfall_mm": req.rainfall,
        "avg_temperature_c": req.temperature,
        "oni_index": req.oni_index,
    }]), training_states)
    results: list[ScenarioSingleResult] = []

    for name in models_to_run:
        model = load_model(name, metrics_data)
        predicted = float(model.predict(features)[0])
        abs_change = round(predicted - baseline, 2)
        pct_change = round((abs_change / baseline) * 100.0, 2) if baseline > 0 else 0.0

        results.append(
            ScenarioSingleResult(
                model=name,
                model_name_display=MODEL_DISPLAY_NAMES.get(name, name),
                predicted_gdp_cr=round(predicted, 2),
                predicted_impact_pct=pct_change,
                absolute_change_cr=abs_change,
            )
        )

    if not results:
        raise ValueError(
            "No models could be executed for this scenario. Please run the training pipeline first."
        )

    # Identify best model result
    best_res = next((r for r in results if r.model == best_model_name), results[0])

    ensemble_gdp = round(float(np.mean([r.predicted_gdp_cr for r in results])), 2)
    ensemble_impact = round(float(np.mean([r.predicted_impact_pct for r in results])), 2)

    interpretation = _interpret_scenario_impact(best_res.predicted_impact_pct, state, req.preset_name)

    return ScenarioResponse(
        state=state,
        historical_avg_gdp_cr=round(baseline, 2),
        preset_name=req.preset_name,
        inputs={
            "rainfall_mm": req.rainfall,
            "avg_temperature_c": req.temperature,
            "oni_index": req.oni_index,
        },
        predictions=results,
        best_model_result=best_res,
        ensemble_gdp_cr=ensemble_gdp,
        ensemble_impact_pct=ensemble_impact,
        interpretation=interpretation,
        disclaimer=DISCLAIMER,
    )
