import logging
from pathlib import Path
from typing import Any

import pandas as pd

from app.constants import LOCAL_DATA_DIR
from app.services.ingestion.climate import fetch_climate_panel
from app.services.ingestion.gdp import fetch_agricultural_gdp
from app.services.ingestion.imd import load_imd_rainfall
from app.services.ingestion.oni import fetch_oni_annual
from app.services.ingestion.states import DEFAULT_END_YEAR, DEFAULT_START_YEAR

logger = logging.getLogger(__name__)
RAW_DATA_DIR = Path(LOCAL_DATA_DIR) / "raw"


def _load_saved_source(
    filename: str,
    required_columns: set[str],
    start_year: int,
    end_year: int,
    key_columns: list[str],
) -> pd.DataFrame:
    """Use a previously downloaded source only when it covers the requested years."""
    path = RAW_DATA_DIR / filename
    if not path.is_file():
        raise ValueError(f"Saved source is missing: {path}")

    data = pd.read_csv(path)
    missing_columns = required_columns - set(data.columns)
    if missing_columns:
        raise ValueError(f"Saved source {path} lacks columns: {', '.join(sorted(missing_columns))}")

    data["year"] = pd.to_numeric(data["year"], errors="coerce")
    data = data[data["year"].between(start_year, end_year)].copy()
    expected_years = set(range(start_year, end_year + 1))
    actual_years = set(data["year"].dropna().astype(int))
    if actual_years != expected_years:
        missing_years = sorted(expected_years - actual_years)
        raise ValueError(f"Saved source {path} does not cover years: {missing_years}")
    if data.duplicated(key_columns).any():
        raise ValueError(f"Saved source {path} has duplicate {', '.join(key_columns)} rows")
    if data[list(required_columns)].isna().any().any():
        raise ValueError(f"Saved source {path} contains missing required values")

    data["year"] = data["year"].astype(int)
    return data


def download_all_sources(
    start_year: int = DEFAULT_START_YEAR,
    end_year: int = DEFAULT_END_YEAR,
    rainfall_source: str = "open_meteo",
    prefer_saved_baseline: bool = False,
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """
    Download from all configured sources and join into a raw panel.
    Returns merged DataFrame and per-source status log.
    """
    if rainfall_source not in {"open_meteo", "imd"}:
        raise ValueError("rainfall_source must be 'open_meteo' or 'imd'")
    source_log: list[dict[str, Any]] = []

    if prefer_saved_baseline and rainfall_source == "open_meteo":
        # Freeze the exact 150-row presentation benchmark. A live refresh can
        # change source revisions or state coverage and must be requested
        # separately; it must not silently replace the reported evaluation.
        oni_df = _load_saved_source(
            "oni_raw.csv", {"year", "oni_index"}, start_year, end_year, ["year"]
        )
        gdp_df = fetch_agricultural_gdp()
        climate_df = _load_saved_source(
            "climate_raw.csv",
            {"state", "year", "avg_temperature_c", "rainfall_mm"},
            start_year,
            end_year,
            ["state", "year"],
        )
        climate_df = climate_df[climate_df["state"].isin(gdp_df["state"])].copy()
        if climate_df.empty:
            raise ValueError("Saved climate panel has no states in the GDP reference")
        source_log.extend(
            [
                {
                    "source": "NOAA ONI Index",
                    "provider": "NOAA (saved local data)",
                    "status": "cached",
                    "records": len(oni_df),
                    "detail": "Frozen presentation benchmark; use scripts/download_data.py to refresh separately.",
                },
                {
                    "source": "Agricultural GDP",
                    "provider": "Bundled project reference (economic provenance unverified)",
                    "status": "success",
                    "records": len(gdp_df),
                    "detail": "Do not present this local sample as official RBI/MoSPI GSVA.",
                },
                {
                    "source": "Rainfall & Temperature",
                    "provider": "Open-Meteo (saved local data)",
                    "status": "cached",
                    "records": len(climate_df),
                    "detail": "Frozen presentation benchmark from data/raw/climate_raw.csv.",
                },
            ]
        )
        panel = climate_df.merge(gdp_df, on=["state", "year"], how="inner")
        panel = panel.merge(oni_df, on="year", how="inner")
        source_log.append(
            {
                "source": "Panel merge",
                "provider": "Internal join",
                "status": "success",
                "records": len(panel),
                "detail": f"Joined {panel['state'].nunique()} states × {panel['year'].nunique()} years",
            }
        )
        return panel, source_log

    # 1. NOAA ONI
    try:
        oni_df = fetch_oni_annual(start_year, end_year)
        source_log.append(
            {
                "source": "NOAA ONI Index",
                "provider": "NOAA Physical Sciences Laboratory",
                "status": "success",
                "records": len(oni_df),
                "url": "https://psl.noaa.gov/data/correlation/oni.data",
            }
        )
    except Exception as exc:
        logger.warning("Live NOAA download failed; trying saved ONI data: %s", exc)
        try:
            oni_df = _load_saved_source(
                "oni_raw.csv", {"year", "oni_index"}, start_year, end_year, ["year"]
            )
        except Exception as cache_exc:
            raise RuntimeError(
                f"NOAA download failed ({exc}); saved ONI data unavailable ({cache_exc})"
            ) from cache_exc
        source_log.append(
            {
                "source": "NOAA ONI Index",
                "provider": "NOAA (saved local data)",
                "status": "cached",
                "records": len(oni_df),
                "error": str(exc),
                "detail": f"Live download unavailable; using data/raw/oni_raw.csv for {start_year}–{end_year}.",
            }
        )

    # 2. Bundled agricultural GDP reference (not verified official GSVA)
    try:
        gdp_df = fetch_agricultural_gdp()
        source_log.append(
            {
                "source": "Agricultural GDP",
                "provider": "Bundled project reference (economic provenance unverified)",
                "status": "success",
                "records": len(gdp_df),
                "detail": "Do not present this local sample as official RBI/MoSPI GSVA.",
            }
        )
    except Exception as exc:
        source_log.append(
            {
                "source": "Agricultural GDP",
                "provider": "Bundled project reference",
                "status": "failed",
                "error": str(exc),
            }
        )
        raise

    # 3. Open-Meteo climate (states covered by GDP reference)
    gdp_states = gdp_df["state"].unique().tolist()
    try:
        climate_df = fetch_climate_panel(start_year, end_year, states=gdp_states)
        source_log.append(
            {
                "source": "Rainfall & Temperature",
                "provider": "Open-Meteo Archive API",
                "status": "success",
                "records": len(climate_df),
                "url": "https://archive-api.open-meteo.com/v1/archive",
            }
        )
    except Exception as exc:
        logger.warning("Live Open-Meteo download failed; trying saved climate data: %s", exc)
        try:
            climate_df = _load_saved_source(
                "climate_raw.csv",
                {"state", "year", "avg_temperature_c", "rainfall_mm"},
                start_year,
                end_year,
                ["state", "year"],
            )
        except Exception as cache_exc:
            raise RuntimeError(
                f"Open-Meteo download failed ({exc}); saved climate data unavailable ({cache_exc})"
            ) from cache_exc
        climate_df = climate_df[climate_df["state"].isin(gdp_states)].copy()
        if climate_df.empty:
            raise ValueError("Saved climate data has no states in the agricultural GDP reference")
        cached_states = climate_df["state"].nunique()
        source_log.append(
            {
                "source": "Rainfall & Temperature",
                "provider": "Open-Meteo (saved local data)",
                "status": "cached",
                "records": len(climate_df),
                "error": str(exc),
                "detail": (
                    "Live download unavailable; using data/raw/climate_raw.csv "
                    f"for {cached_states} of {len(gdp_states)} reference states, {start_year}–{end_year}."
                ),
            }
        )

    # IMD is an explicit comparison mode. The default preserves the earlier
    # Open-Meteo experiment and its reported metrics. Never silently switch
    # rainfall sources between training runs.
    if rainfall_source == "imd":
        climate_states = climate_df["state"].unique().tolist()
        imd_df = load_imd_rainfall(start_year, end_year, climate_states)
        climate_df = climate_df.drop(columns=["rainfall_mm"]).merge(
            imd_df, on=["state", "year"], how="inner", validate="one_to_one"
        )
        source_log.append(
            {
                "source": "Rainfall",
                "provider": "India Meteorological Department (1° gridded rainfall; state-centroid cells)",
                "status": "success",
                "records": len(imd_df),
                "url": "https://www.imdpune.gov.in/cmpg/Griddata/Rainfall_1_NetCDF.html",
                "detail": "Official IMD daily rainfall aggregated to calendar-year totals at the nearest 1° cell to each state centroid; not a state-wide average.",
            }
        )

    # Join: climate ⨝ GDP on (state, year), then ⨝ ONI on (year)
    panel = climate_df.merge(gdp_df, on=["state", "year"], how="inner")
    panel = panel.merge(oni_df, on="year", how="inner")

    source_log.append(
        {
            "source": "Panel merge",
            "provider": "Internal join",
            "status": "success",
            "records": len(panel),
            "detail": f"Joined {panel['state'].nunique()} states × {panel['year'].nunique()} years",
        }
    )

    logger.info(
        "Download complete: %d rows from %d sources",
        len(panel),
        len(source_log) - 1,
    )
    return panel, source_log
