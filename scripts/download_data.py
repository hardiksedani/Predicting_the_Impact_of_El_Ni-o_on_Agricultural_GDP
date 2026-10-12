"""Download climate and ENSO data plus the bundled economic sample.

Sources:
1. NOAA Physical Sciences Laboratory - Oceanic Niño Index (ONI)
2. Open-Meteo Archive API - State-centroid precipitation & temperature
3. Bundled project reference - illustrative agricultural GDP target

Official IMD rainfall is fetched separately by scripts/download_imd_rainfall.py.
"""

import logging
import sys
from pathlib import Path

# Add backend to sys.path
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR / "backend"))

import pandas as pd
from app.services.ingestion.climate import fetch_climate_panel
from app.services.ingestion.gdp import fetch_agricultural_gdp
from app.services.ingestion.oni import fetch_oni_annual
from app.services.ingestion.states import DEFAULT_END_YEAR, DEFAULT_START_YEAR

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main():
    raw_dir = BASE_DIR / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    logger.info("==================================================")
    logger.info("PHASE 3: REAL DATA ACQUISITION PIPELINE")
    logger.info("==================================================")

    # 1. Download NOAA ONI
    logger.info("Step 1: Downloading NOAA Oceanic Niño Index (ONI)...")
    oni_df = fetch_oni_annual(DEFAULT_START_YEAR, DEFAULT_END_YEAR)
    oni_path = raw_dir / "oni_raw.csv"
    oni_df.to_csv(oni_path, index=False)
    logger.info("Saved ONI data (%d rows) -> %s", len(oni_df), oni_path)

    # 2. Agricultural GDP/GVA
    logger.info("Step 2: Fetching Agricultural GVA/GDP Series...")
    gdp_df = fetch_agricultural_gdp()
    gdp_path = raw_dir / "agricultural_gva_raw.csv"
    gdp_df.to_csv(gdp_path, index=False)
    logger.info("Saved Agricultural GVA data (%d rows) -> %s", len(gdp_df), gdp_path)

    # 3. Climate Data (Open-Meteo)
    logger.info("Step 3: Downloading state-level Climate Data (Open-Meteo Archive)...")
    states = gdp_df["state"].unique().tolist()
    climate_df = fetch_climate_panel(DEFAULT_START_YEAR, DEFAULT_END_YEAR, states=states)
    climate_path = raw_dir / "climate_raw.csv"
    climate_df.to_csv(climate_path, index=False)
    logger.info("Saved Climate data (%d rows) -> %s", len(climate_df), climate_path)

    logger.info("Data download complete! All raw datasets saved in data/raw/")


if __name__ == "__main__":
    main()
