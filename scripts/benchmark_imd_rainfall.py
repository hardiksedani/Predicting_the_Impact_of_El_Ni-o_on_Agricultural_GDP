"""Paired, read-only IMD-vs-Open-Meteo rainfall benchmark on fixed years/rows."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, r2_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.constants import FEATURE_COLUMNS, MODEL_NAMES, TARGET_COLUMN  # noqa: E402
from app.services.ingestion.imd import load_imd_rainfall  # noqa: E402
from app.services.ml import _build_model, time_aware_split  # noqa: E402


def main() -> None:
    raw = ROOT / "data" / "raw"
    climate = pd.read_csv(raw / "climate_raw.csv")
    gdp = pd.read_csv(ROOT / "backend" / "app" / "data" / "sources" / "agricultural_gdp_reference.csv")
    oni = pd.read_csv(raw / "oni_raw.csv")
    baseline = climate.merge(gdp, on=["state", "year"], validate="one_to_one").merge(
        oni, on="year", validate="many_to_one"
    )
    imd = load_imd_rainfall(2009, 2023, baseline["state"].unique().tolist())
    comparison = baseline.drop(columns=["rainfall_mm"]).merge(
        imd, on=["state", "year"], validate="one_to_one"
    )
    if len(comparison) != len(baseline):
        raise ValueError("Rainfall sources do not cover identical rows")

    print(f"Paired comparison: {len(baseline)} identical state-year rows")
    print("Training years: 2009-2019; held-out years: 2020-2023")
    print("Model                 Open-Meteo R2  IMD R2  Open-Meteo RMSE  IMD RMSE")
    for model_name in MODEL_NAMES:
        scores = []
        for panel in (baseline, comparison):
            train, test, _, _ = time_aware_split(panel)
            model = _build_model(model_name)
            model.fit(train[FEATURE_COLUMNS], train[TARGET_COLUMN])
            predictions = model.predict(test[FEATURE_COLUMNS])
            scores.append(
                (
                    r2_score(test[TARGET_COLUMN], predictions),
                    np.sqrt(mean_squared_error(test[TARGET_COLUMN], predictions)),
                )
            )
        print(
            f"{model_name:<22}{scores[0][0]:>10.4f}{scores[1][0]:>9.4f}"
            f"{scores[0][1]:>17.2f}{scores[1][1]:>10.2f}"
        )


if __name__ == "__main__":
    main()
