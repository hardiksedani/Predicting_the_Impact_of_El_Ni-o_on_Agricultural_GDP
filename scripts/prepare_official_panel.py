"""Build an auditable FY state panel from user-supplied IMD, NOAA and RBI files.

This script does not fit models or modify the website database. It uses one
representative grid point per state; these features are NOT state-wide means.
"""

from __future__ import annotations

import argparse
import calendar
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.io import netcdf_file

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.services.ingestion.states import INDIAN_STATES

RAW = ROOT / "data" / "raw"
POINTS = ROOT / "data" / "metadata" / "state_representative_points.csv"
ECONOMIC = ROOT / "data" / "interim" / "economic" / "extracted_agriculture.csv"
OUTPUT = ROOT / "data" / "processed" / "official_panel.csv"
REPORT = ROOT / "data" / "processed" / "official_panel_report.json"
CLIMATE_OUTPUT = ROOT / "data" / "interim" / "official_climate_points.csv"
TARGET_SOURCE = "rbi_2011_12"
ONI_CENTER_MONTH = {
    "DJF": 1, "JFM": 2, "FMA": 3, "MAM": 4, "AMJ": 5, "MJJ": 6,
    "JJA": 7, "JAS": 8, "ASO": 9, "SON": 10, "OND": 11, "NDJ": 12,
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_points(path: Path = POINTS) -> pd.DataFrame:
    points = pd.read_csv(path)
    required = {"state", "latitude", "longitude", "point_label"}
    if not required.issubset(points.columns):
        raise ValueError(f"Point file needs columns: {sorted(required)}")
    if points["state"].duplicated().any() or set(points["state"]) != set(INDIAN_STATES):
        raise ValueError("Point file must have exactly one entry for each of the 28 states")
    if points[["latitude", "longitude"]].isna().any().any():
        raise ValueError("Point coordinates cannot be blank")
    if not points["latitude"].between(7.5, 38.5).all() or not points["longitude"].between(67.5, 98.5).all():
        raise ValueError("Representative points must lie within the IMD temperature grid")
    return points.sort_values("state").reset_index(drop=True)


def load_targets(start: int, end: int, path: Path = ECONOMIC) -> pd.DataFrame:
    source_pdf = RAW / "economic" / "rbi_2011_12.pdf"
    if not path.is_file():
        raise FileNotFoundError(f"Extract the economic PDFs first: {path}")
    if path.stat().st_mtime < source_pdf.stat().st_mtime:
        raise ValueError("Economic extraction predates the RBI PDF; regenerate it first")
    data = pd.read_csv(path)
    data = data.loc[data["source"].eq(TARGET_SOURCE)].copy()
    data["start_year"] = pd.to_numeric(data["start_year"], errors="raise").astype(int)
    data = data.loc[data["start_year"].between(start, end)]
    expected = len(INDIAN_STATES) * (end - start + 1)
    if len(data) != expected or data.duplicated(["state", "start_year"]).any():
        raise ValueError(f"Expected {expected} unique RBI state-year cells; found {len(data)}")
    if set(data["state"]) != set(INDIAN_STATES):
        raise ValueError("RBI extraction does not cover all 28 states")
    if set(data["price_base"]) != {"2011-12"} or not data["measure"].str.contains("GSVA").all():
        raise ValueError("Only the RBI 2011-12-base GSVA Agriculture (crops) series is allowed")
    if set(data["source_file"]) != {"data/raw/economic/rbi_2011_12.pdf"}:
        raise ValueError("RBI extraction has unexpected source-file provenance")
    data["agricultural_gdp_cr"] = pd.to_numeric(data["agriculture_crore"], errors="coerce")
    if (data["agricultural_gdp_cr"].dropna() <= 0).any():
        raise ValueError("RBI target must be positive or officially missing")
    return data.rename(columns={"start_year": "year"})[
        ["state", "year", "financial_year", "agricultural_gdp_cr", "quality_flags"]
    ]


def load_oni(start: int, end: int, path: Path = RAW / "oni" / "oni.ascii.txt") -> pd.DataFrame:
    table = pd.read_csv(path, sep=r"\s+")
    if not {"SEAS", "YR", "ANOM"}.issubset(table.columns):
        raise ValueError("ONI ASCII file lacks SEAS, YR or ANOM")
    if not table["SEAS"].isin(ONI_CENTER_MONTH).all():
        raise ValueError("Unrecognised ONI seasonal code")
    table["month"] = table["SEAS"].map(ONI_CENTER_MONTH)
    table["YR"] = pd.to_numeric(table["YR"], errors="raise").astype(int)
    table["ANOM"] = pd.to_numeric(table["ANOM"], errors="raise")
    if table.duplicated(["SEAS", "YR"]).any() or not np.isfinite(table["ANOM"]).all():
        raise ValueError("ONI has duplicate seasons or non-finite anomalies")
    # Complete 3-month seasons inside Apr-Mar: AMJ..NDJ of start year,
    # then DJF and JFM of end year (10 overlapping seasons).
    table["year"] = table["YR"] - table["month"].lt(4).astype(int)
    selected = table.loc[table["year"].between(start, end) & table["month"].isin(
        [5, 6, 7, 8, 9, 10, 11, 12, 1, 2]
    )]
    counts = selected.groupby("year")["ANOM"].agg(["count", "mean"])
    if set(counts.index) != set(range(start, end + 1)) or not counts["count"].eq(10).all():
        raise ValueError("ONI needs 10 complete overlapping seasons for every financial year")
    return counts.reset_index().rename(columns={"mean": "oni_index"})[["year", "oni_index"]]


def nearest(values: np.ndarray, point: float) -> int:
    index = int(np.abs(values - point).argmin())
    if abs(float(values[index]) - point) > float(np.diff(values).max()) / 2 + 1e-6:
        raise ValueError(f"Point {point} lies outside the climate grid")
    return index


def calendar_year_samples(year: int, points: pd.DataFrame) -> pd.DataFrame:
    rainfall_file = RAW / "rainfall" / f"rainfall_{year}.nc"
    tmax_file = RAW / "temperature" / "tmax" / f"{year}.GRD"
    tmin_file = RAW / "temperature" / "tmin" / f"{year}.GRD"
    for path in (rainfall_file, tmax_file, tmin_file):
        if not path.is_file():
            raise FileNotFoundError(path)

    days = 366 if calendar.isleap(year) else 365
    expected_size = days * 31 * 31 * 4
    if tmax_file.stat().st_size != expected_size or tmin_file.stat().st_size != expected_size:
        raise ValueError(f"Unexpected temperature GRD size for {year}")
    tmax = np.memmap(tmax_file, dtype="<f4", mode="r", shape=(days, 31, 31))
    tmin = np.memmap(tmin_file, dtype="<f4", mode="r", shape=(days, 31, 31))
    dates = pd.date_range(f"{year}-01-01", periods=days, freq="D")
    with netcdf_file(rainfall_file, "r", mmap=False) as dataset:
        if set(dataset.variables) < {"RAINFALL", "LATITUDE", "LONGITUDE", "TIME"}:
            raise ValueError(f"Missing NetCDF variables in {rainfall_file}")
        rainfall = dataset.variables["RAINFALL"]
        if rainfall.shape != (days, 129, 135):
            raise ValueError(f"Unexpected NetCDF rainfall grid in {rainfall_file}")
        if getattr(rainfall, "units", b"") != b"mm":
            raise ValueError(f"Unexpected rainfall units in {rainfall_file}")
        latitudes = np.asarray(dataset.variables["LATITUDE"][:], dtype=float)
        longitudes = np.asarray(dataset.variables["LONGITUDE"][:], dtype=float)
        time_values = np.asarray(dataset.variables["TIME"][:], dtype=float)
        time_units = getattr(dataset.variables["TIME"], "units", b"")
        if time_units != b"days since 1900-12-31 00:00:00":
            raise ValueError(f"Unexpected NetCDF time units in {rainfall_file}")
        parsed_dates = pd.to_datetime(time_values, unit="D", origin="1900-12-31")
        if not parsed_dates.normalize().equals(dates):
            raise ValueError(f"NetCDF daily time axis does not match {year}")

        frames = []
        temp_lats = np.arange(7.5, 38.5, 1.0)
        temp_lons = np.arange(67.5, 98.5, 1.0)
        for point in points.itertuples(index=False):
            rlat = nearest(latitudes, point.latitude)
            rlon = nearest(longitudes, point.longitude)
            tlat = nearest(temp_lats, point.latitude)
            tlon = nearest(temp_lons, point.longitude)
            rain = np.asarray(rainfall[:, rlat, rlon], dtype=float)
            high = np.asarray(tmax[:, tlat, tlon], dtype=float)
            low = np.asarray(tmin[:, tlat, tlon], dtype=float)
            rain[~np.isfinite(rain) | (rain < 0)] = np.nan
            high[~np.isfinite(high) | np.isclose(high, 99.9)] = np.nan
            low[~np.isfinite(low) | np.isclose(low, 99.9)] = np.nan
            temp = (high + low) / 2
            frames.append(pd.DataFrame({
                "state": point.state, "date": dates, "rainfall_mm_daily": rain,
                "avg_temperature_c_daily": temp,
                "rainfall_grid_lat": float(latitudes[rlat]),
                "rainfall_grid_lon": float(longitudes[rlon]),
                "temperature_grid_lat": float(temp_lats[tlat]),
                "temperature_grid_lon": float(temp_lons[tlon]),
            }))
    return pd.concat(frames, ignore_index=True)


def aggregate_financial_year(daily: pd.DataFrame, start: int, end: int) -> pd.DataFrame:
    work = daily.copy()
    work["year"] = work["date"].dt.year - work["date"].dt.month.lt(4).astype(int)
    work = work.loc[work["year"].between(start, end)]
    grouped = work.groupby(["state", "year"], sort=True)
    annual = grouped.agg(
        rainfall_mm=("rainfall_mm_daily", "sum"),
        avg_temperature_c=("avg_temperature_c_daily", "mean"),
        rainfall_days=("rainfall_mm_daily", "count"),
        temperature_days=("avg_temperature_c_daily", "count"),
        expected_days=("date", "count"),
        rainfall_grid_lat=("rainfall_grid_lat", "first"),
        rainfall_grid_lon=("rainfall_grid_lon", "first"),
        temperature_grid_lat=("temperature_grid_lat", "first"),
        temperature_grid_lon=("temperature_grid_lon", "first"),
    ).reset_index()
    annual["rainfall_coverage"] = annual["rainfall_days"] / annual["expected_days"]
    annual["temperature_coverage"] = annual["temperature_days"] / annual["expected_days"]
    correct_days = annual["year"].map(lambda year: 366 if calendar.isleap(int(year) + 1) else 365)
    if not annual["expected_days"].eq(correct_days).all():
        raise ValueError("Incomplete daily calendar in one or more April-March financial years")
    return annual


def build_panel(start: int = 2011, end: int = 2024) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    if start < 2011 or end > 2024 or start > end:
        raise ValueError("Supported financial-year starts are 2011 through 2024")
    points = load_points()
    targets = load_targets(start, end)
    oni = load_oni(start, end)
    daily = pd.concat(
        [calendar_year_samples(year, points) for year in range(start, end + 2)],
        ignore_index=True,
    )
    climate = aggregate_financial_year(daily, start, end)
    expected = len(points) * (end - start + 1)
    if len(climate) != expected or climate.duplicated(["state", "year"]).any():
        raise ValueError(f"Expected {expected} unique climate state-years; found {len(climate)}")
    merged = climate.merge(targets, on=["state", "year"], how="inner", validate="one_to_one")
    merged = merged.merge(oni, on="year", how="left", validate="many_to_one")
    if len(merged) != expected:
        raise ValueError("Unexpected state-year rows lost in the climate/economic join")
    merged["excluded_reason"] = ""
    merged.loc[merged["agricultural_gdp_cr"].isna(), "excluded_reason"] = "official_target_missing"
    low_climate = (merged["rainfall_coverage"] < 0.95) | (merged["temperature_coverage"] < 0.95)
    merged.loc[low_climate, "excluded_reason"] += " climate_coverage_below_95pct"
    merged["excluded_reason"] = merged["excluded_reason"].str.strip()
    panel = merged.loc[merged["excluded_reason"].eq("")].copy()
    if panel.empty or panel["state"].nunique() != len(INDIAN_STATES):
        raise ValueError("The clean panel does not cover all 28 states; inspect the climate report")
    panel["target_source"] = TARGET_SOURCE
    panel["target_measure"] = "GSVA Agriculture (crops), constant 2011-12 prices, INR crore"
    panel["climate_method"] = "nearest_representative_grid_point_fy_apr_mar"
    panel["rainfall_mm"] = panel["rainfall_mm"].round(2)
    panel["avg_temperature_c"] = panel["avg_temperature_c"].round(3)
    panel["oni_index"] = panel["oni_index"].round(3)
    panel = panel.sort_values(["state", "year"]).reset_index(drop=True)
    report = {
        "target": "RBI/NSO GSVA Agriculture (crops), 2011-12 constant prices, INR crore",
        "climate_method": (
            "nearest IMD grid cell to one representative point per state; grid centers may "
            "fall outside state boundaries (notably coastal Goa); not a state-wide average "
            "or station observation"
        ),
        "time_window": "financial year April-March; ONI mean of 10 complete 3-month seasons inside FY",
        "unused_available_climate_years": "2001-2010 retained in raw files but not used because the comparable RBI target begins FY 2011-12",
        "input_years": [start, end],
        "candidate_state_years": expected,
        "training_ready_rows": len(panel),
        "states_with_rows": panel["state"].nunique(),
        "rows_by_state": panel.groupby("state").size().to_dict(),
        "minimum_rainfall_coverage": round(float(merged["rainfall_coverage"].min()), 6),
        "minimum_temperature_coverage": round(float(merged["temperature_coverage"].min()), 6),
        "source_quality_flags_retained_for_review": panel.loc[
            panel["quality_flags"].fillna("").ne(""),
            ["state", "financial_year", "quality_flags"],
        ].to_dict("records"),
        "exclusions": merged.loc[merged["excluded_reason"].ne(""),
                                 ["state", "year", "excluded_reason"]].to_dict("records"),
        "source_sha256": {
            "rbi_pdf": sha256(RAW / "economic" / "rbi_2011_12.pdf"),
            "rbi_extraction_csv": sha256(ECONOMIC),
            "oni_ascii": sha256(RAW / "oni" / "oni.ascii.txt"),
            "state_points": sha256(POINTS),
        },
        "climate_file_sha256": {
            path.relative_to(ROOT).as_posix(): sha256(path)
            for year in range(start, end + 2)
            for path in (
                RAW / "rainfall" / f"rainfall_{year}.nc",
                RAW / "temperature" / "tmax" / f"{year}.GRD",
                RAW / "temperature" / "tmin" / f"{year}.GRD",
            )
        },
        "model_training_performed": False,
    }
    return panel, climate, report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    outputs = (OUTPUT, REPORT, CLIMATE_OUTPUT)
    if not args.overwrite and any(path.exists() for path in outputs):
        raise SystemExit("Output exists; pass --overwrite to regenerate only the derived files")
    panel, climate, report = build_panel()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    CLIMATE_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    panel.to_csv(OUTPUT, index=False)
    climate.to_csv(CLIMATE_OUTPUT, index=False)
    report["panel_sha256"] = sha256(OUTPUT)
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({
        "panel": str(OUTPUT), "rows": len(panel), "states": panel["state"].nunique(),
        "years": [int(panel["year"].min()), int(panel["year"].max())],
        "excluded": len(report["exclusions"]), "training_performed": False,
    }, indent=2))


if __name__ == "__main__":
    main()
