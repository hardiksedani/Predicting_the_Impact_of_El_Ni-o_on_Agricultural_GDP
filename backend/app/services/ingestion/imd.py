"""Validated IMD rainfall panel extracted from official gridded NetCDF files."""

from pathlib import Path

import pandas as pd

from app.constants import LOCAL_DATA_DIR

IMD_RAINFALL_PATH = Path(LOCAL_DATA_DIR) / "raw" / "imd_rainfall_raw.csv"


def load_imd_rainfall(
    start_year: int, end_year: int, states: list[str]
) -> pd.DataFrame:
    if not IMD_RAINFALL_PATH.is_file():
        raise FileNotFoundError(
            f"IMD rainfall panel missing: {IMD_RAINFALL_PATH}. "
            "Run scripts/download_imd_rainfall.py first."
        )
    frame = pd.read_csv(IMD_RAINFALL_PATH)
    required = {"state", "year", "rainfall_mm"}
    if not required.issubset(frame.columns):
        raise ValueError("IMD rainfall panel lacks state, year, or rainfall_mm")
    frame = frame[frame["state"].isin(states) & frame["year"].between(start_year, end_year)]
    expected = pd.MultiIndex.from_product(
        [states, range(start_year, end_year + 1)], names=["state", "year"]
    )
    actual = pd.MultiIndex.from_frame(frame[["state", "year"]])
    if actual.has_duplicates or len(actual) != len(expected) or len(expected.difference(actual)):
        missing = expected.difference(actual)
        extra = actual.difference(expected)
        raise ValueError(
            f"IMD rainfall panel is not complete for requested states and years "
            f"(missing={len(missing)}, extra={len(extra)}, duplicates={actual.has_duplicates})"
        )
    frame = frame.copy()
    frame["rainfall_mm"] = pd.to_numeric(frame["rainfall_mm"], errors="coerce")
    if frame["rainfall_mm"].isna().any() or (frame["rainfall_mm"] < 0).any():
        raise ValueError("IMD rainfall panel contains invalid rainfall totals")
    return frame[["state", "year", "rainfall_mm"]]
