import logging
from pathlib import Path

import httpx
import pandas as pd

logger = logging.getLogger(__name__)

# Bundled project reference panel. Provenance is unverified; do not label as RBI/MoSPI.
LOCAL_GDP_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "sources" / "agricultural_gdp_reference.csv"
)
def _load_local_reference() -> pd.DataFrame | None:
    if not LOCAL_GDP_PATH.exists():
        return None
    df = pd.read_csv(LOCAL_GDP_PATH)
    required = {"state", "year", "agricultural_gdp_cr"}
    if not required.issubset(df.columns):
        return None
    return df[["state", "year", "agricultural_gdp_cr"]]


def fetch_agricultural_gdp() -> pd.DataFrame:
    """
    Download agricultural GDP panel.
    Primary: bundled sample CSV with unverified economic provenance.
    Fallback: expanded sample panel from project sample_data.
    """
    logger.info("Fetching agricultural GDP reference data")

    df = _load_local_reference()
    if df is not None:
        logger.info("GDP: loaded %d rows from unverified local reference", len(df))
        return df

    sample_path = (
        Path(__file__).resolve().parents[4] / "sample_data" / "climate_gdp_sample.csv"
    )
    if sample_path.exists():
        raw = pd.read_csv(sample_path)
        df = raw[["state", "year", "agricultural_gdp_cr"]].copy()
        logger.info("GDP: loaded %d rows from sample reference panel", len(df))
        return df

    raise ValueError(
        "Agricultural GDP source unavailable. Ensure reference CSV exists."
    )
