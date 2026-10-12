"""Data preprocessing and panel dataset construction script.

Performs:
- Schema validation
- State name normalization
- Deduplication and missing value inspection
- Panel join (state, year)
- Feature engineering:
  * rainfall_anomaly
  * temp_anomaly
  * lagged_rainfall_mm
  * lagged_temperature_c
  * lagged_oni
- Outputs cleaned panel to data/processed/panel_dataset.csv
- Populates database for dashboard and model training
"""

import argparse
import json
import logging
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR / "backend"))

import numpy as np
import pandas as pd
from app.services.cleaning import clean_panel_data
from app.services.db_storage import get_db
from app.services.ingestion.imd import load_imd_rainfall
from app.services.ingestion.states import DEFAULT_END_YEAR, DEFAULT_START_YEAR

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def engineer_panel_features(df: pd.DataFrame) -> pd.DataFrame:
    """Engineer state-level climate anomalies and lag features without lookahead leakage."""
    work = df.sort_values(["state", "year"]).reset_index(drop=True)

    # 1. State-specific climate baselines (computed across panel)
    state_rain_mean = work.groupby("state")["rainfall_mm"].transform("mean")
    state_temp_mean = work.groupby("state")["avg_temperature_c"].transform("mean")

    work["rainfall_anomaly"] = (work["rainfall_mm"] - state_rain_mean).round(1)
    work["temp_anomaly"] = (work["avg_temperature_c"] - state_temp_mean).round(2)

    # 2. Lagged climate features (t - 1)
    work["lagged_rainfall_mm"] = work.groupby("state")["rainfall_mm"].shift(1)
    work["lagged_temperature_c"] = work.groupby("state")["avg_temperature_c"].shift(1)
    work["lagged_oni"] = work.groupby("state")["oni_index"].shift(1)

    # Impute first-year lag with contemporary value
    work["lagged_rainfall_mm"] = work["lagged_rainfall_mm"].fillna(work["rainfall_mm"]).round(1)
    work["lagged_temperature_c"] = work["lagged_temperature_c"].fillna(work["avg_temperature_c"]).round(2)
    work["lagged_oni"] = work["lagged_oni"].fillna(work["oni_index"]).round(3)

    return work


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--rainfall-source", choices=["open_meteo", "imd"], default="open_meteo"
    )
    args = parser.parse_args()
    raw_dir = BASE_DIR / "data" / "raw"
    processed_dir = BASE_DIR / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    logger.info("==================================================")
    logger.info("PHASE 4 & 5: PANEL DATA CONSTRUCTION & CLEANING")
    logger.info("==================================================")

    climate_path = raw_dir / "climate_raw.csv"
    gdp_path = raw_dir / "agricultural_gva_raw.csv"
    oni_path = raw_dir / "oni_raw.csv"

    # Fallback to backend source files if raw not generated yet
    if not (climate_path.exists() and gdp_path.exists() and oni_path.exists()):
        logger.info("Raw files not found in data/raw. Loading from ingestion services...")
        from app.services.ingestion.join import download_all_sources
        raw_panel, source_log = download_all_sources(rainfall_source=args.rainfall_source)
    else:
        climate_df = pd.read_csv(climate_path)
        gdp_df = pd.read_csv(gdp_path)
        oni_df = pd.read_csv(oni_path)

        if args.rainfall_source == "imd":
            imd_df = load_imd_rainfall(
                DEFAULT_START_YEAR, DEFAULT_END_YEAR, climate_df["state"].unique().tolist()
            )
            climate_df = climate_df.drop(columns=["rainfall_mm"]).merge(
                imd_df, on=["state", "year"], validate="one_to_one"
            )
            logger.info("Using official IMD rainfall for %d state-year rows", len(imd_df))
        else:
            logger.info("Using Open-Meteo rainfall to reproduce the earlier benchmark")

        raw_panel = climate_df.merge(gdp_df, on=["state", "year"], how="inner")
        raw_panel = raw_panel.merge(oni_df, on="year", how="inner")

    logger.info("Initial merged panel: %d rows", len(raw_panel))

    # Clean panel
    cleaned, report = clean_panel_data(raw_panel)
    logger.info("After initial cleaning: %d rows", len(cleaned))

    # Feature engineering
    panel_df = engineer_panel_features(cleaned)

    # Save to processed
    out_csv = processed_dir / "panel_dataset.csv"
    panel_df.to_csv(out_csv, index=False)
    logger.info("Saved finalized panel dataset -> %s", out_csv)

    # Upsert into database
    db = get_db()
    batch = db.batch()
    from app.services.ml import state_slug
    for _, row in panel_df.iterrows():
        st = str(row["state"]).strip()
        yr = int(row["year"])
        doc_ref = db.collection("climate_gdp_data").document(f"{state_slug(st)}_{yr}")
        batch.set(
            doc_ref,
            {
                "state": st,
                "year": yr,
                "rainfall_mm": float(row["rainfall_mm"]),
                "avg_temperature_c": float(row["avg_temperature_c"]),
                "oni_index": float(row["oni_index"]),
                "agricultural_gdp_cr": float(row["agricultural_gdp_cr"]),
                "rainfall_anomaly": float(row.get("rainfall_anomaly", 0)),
                "temp_anomaly": float(row.get("temp_anomaly", 0)),
                "source": f"preprocessed_panel_{args.rainfall_source}",
            },
            merge=True,
        )
    batch.commit()
    logger.info("Synchronized %d panel records to active database.", len(panel_df))

    # Preprocessing Quality Report
    print("\n" + "=" * 50)
    print("DATA PREPROCESSING REPORT")
    print("=" * 50)
    print(f"Total Rows In:           {report['rows_in']}")
    print(f"Total Rows Out:          {len(panel_df)}")
    print(f"Total States:            {panel_df['state'].nunique()}")
    print(f"Year Coverage:           {int(panel_df['year'].min())} – {int(panel_df['year'].max())}")
    print(f"Duplicates Removed:      {report.get('duplicates_removed', 0)}")
    print(f"Imputed Cells:           {report.get('imputed_cells', 0)}")
    print(f"Engineered Features:     rainfall_anomaly, temp_anomaly, lags")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    main()
