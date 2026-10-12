"""Optional ONI-only climate experiment; never replaces the website's active models.

The only climate predictor is NOAA ONI. By default, state identity is retained
because the target is a state-level economic amount. Pass --strict-oni to omit
state identity as well. Run without flags for a read-only preflight, then
manually choose --train.
"""

from __future__ import annotations

import argparse
import json
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.constants import MODEL_NAMES, OFFICIAL_TARGET_LABEL  # noqa: E402
from app.services.ingestion.states import INDIAN_STATES  # noqa: E402
from app.services.ml import _build_model, state_slug, time_aware_split  # noqa: E402
from prepare_official_panel import load_oni, load_targets, sha256  # noqa: E402

ONI_FILE = ROOT / "data" / "raw" / "oni" / "oni.ascii.txt"
RBI_FILE = ROOT / "data" / "raw" / "economic" / "rbi_2011_12.pdf"
EXTRACTED_FILE = ROOT / "data" / "interim" / "economic" / "extracted_agriculture.csv"
OUTPUT_ROOT = ROOT / "data" / "models" / "oni_only"


def load_training_panel() -> tuple[pd.DataFrame, int]:
    """Join the uploaded ONI directly to the extracted RBI target; read no IMD file."""
    targets = load_targets(2011, 2024)
    oni = load_oni(2011, 2024)
    panel = targets.merge(oni, on="year", how="left", validate="many_to_one")
    if len(panel) != 28 * 14 or panel.duplicated(["state", "year"]).any():
        raise ValueError("Expected 392 unique state-financial-year candidate rows")
    if set(panel["state"]) != set(INDIAN_STATES) or panel["oni_index"].isna().any():
        raise ValueError("All states and financial years need ONI observations")
    missing_targets = int(panel["agricultural_gdp_cr"].isna().sum())
    panel = panel.dropna(subset=["agricultural_gdp_cr"]).copy()
    panel = panel.rename(columns={"agricultural_gdp_cr": "crop_gsva_cr"})
    if (panel["crop_gsva_cr"] <= 0).any() or not np.isfinite(
        panel[["oni_index", "crop_gsva_cr"]].to_numpy(dtype=float)
    ).all():
        raise ValueError("ONI and crop GSVA must be finite; crop GSVA must be positive")
    return panel.sort_values(["state", "year"]).reset_index(drop=True), missing_targets


def feature_frame(panel: pd.DataFrame, states: list[str], strict_oni: bool) -> pd.DataFrame:
    features = panel[["oni_index"]].copy()
    if not strict_oni:
        for state in states:
            features[f"state__{state_slug(state)}"] = panel["state"].eq(state).astype(int)
    return features


def scores(actual: pd.Series, predicted: np.ndarray) -> dict[str, float]:
    return {
        "mae_cr": round(float(mean_absolute_error(actual, predicted)), 2),
        "rmse_cr": round(float(np.sqrt(mean_squared_error(actual, predicted))), 2),
        "r2": round(float(r2_score(actual, predicted)), 4),
    }


def train(panel: pd.DataFrame, missing_targets: int, strict_oni: bool) -> Path:
    train_df, test_df, train_years, test_years = time_aware_split(panel)
    states = sorted(train_df["state"].unique().tolist())
    if set(states) != set(INDIAN_STATES):
        raise ValueError("All 28 states must occur in the training years")
    x_train = feature_frame(train_df, states, strict_oni)
    x_test = feature_frame(test_df, states, strict_oni)
    y_train = train_df["crop_gsva_cr"]
    y_test = test_df["crop_gsva_cr"]

    # A state-mean reference helps reveal whether ONI adds useful information
    # beyond persistent differences in the economic scale of each state.
    state_means = train_df.groupby("state")["crop_gsva_cr"].mean()
    reference = scores(y_test, test_df["state"].map(state_means).to_numpy())
    run_id = datetime.now(timezone.utc).strftime("run_%Y%m%d_%H%M%S_") + secrets.token_hex(4)
    mode = "strict_oni" if strict_oni else "oni_plus_state"
    run_dir = OUTPUT_ROOT / mode / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    results = {}
    for name in MODEL_NAMES:
        model = _build_model(name)
        model.fit(x_train, y_train)
        results[name] = scores(y_test, model.predict(x_test))
        model_path = run_dir / f"{name}.joblib"
        joblib.dump(model, model_path, compress=3)
        results[name]["artifact_sha256"] = sha256(model_path)

    best = min(results, key=lambda name: results[name]["rmse_cr"])
    report = {
        "run_id": run_id,
        "mode": mode,
        "target": OFFICIAL_TARGET_LABEL,
        "feature_columns": x_train.columns.tolist(),
        "source_sha256": {
            "oni_ascii": sha256(ONI_FILE),
            "rbi_pdf": sha256(RBI_FILE),
            "extracted_agriculture_csv": sha256(EXTRACTED_FILE),
        },
        "rows": len(panel),
        "excluded_missing_official_targets": missing_targets,
        "train_years": train_years,
        "test_years": test_years,
        "state_mean_reference": reference,
        "models": results,
        "best_model_by_test_rmse": best,
        "caution": (
            "ONI is the same nationwide within each year. High pooled R2 may mainly "
            "reflect state size; compare the state-mean reference. Selecting the best "
            "model on these test years makes its reported score optimistic."
        ),
    }
    report_path = run_dir / "evaluation.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"State-mean reference: {reference}")
    for name, result in results.items():
        print(f"{name:20} MAE={result['mae_cr']:10.2f} RMSE={result['rmse_cr']:10.2f} R2={result['r2']:7.4f}")
    print(f"Best by test RMSE: {best}")
    return report_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", action="store_true", help="Fit all five models and save a separate ONI experiment")
    parser.add_argument("--strict-oni", action="store_true", help="Use ONI alone, without state identity")
    args = parser.parse_args()
    panel, missing_targets = load_training_panel()
    print(f"ONI-only climate panel: {len(panel)} rows, {panel['state'].nunique()} states, "
          f"{panel['year'].nunique()} financial years; {missing_targets} official target blanks excluded")
    print(f"Inputs: {ONI_FILE} and {RBI_FILE}; no IMD rainfall or temperature is read")
    if not args.train:
        print("Preflight only. Add --train to fit all five models yourself.")
        return
    report_path = train(panel, missing_targets, args.strict_oni)
    print(f"Separate experiment saved: {report_path}")
    print("The website's active models and database were not changed.")


if __name__ == "__main__":
    main()
