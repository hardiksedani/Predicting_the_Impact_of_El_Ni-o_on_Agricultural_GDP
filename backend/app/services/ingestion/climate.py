import logging

import httpx
import pandas as pd

from app.services.ingestion.states import (
    DEFAULT_END_YEAR,
    DEFAULT_START_YEAR,
    STATE_COORDINATES,
)

logger = logging.getLogger(__name__)

OPEN_METEO_URL = "https://archive-api.open-meteo.com/v1/archive"


def _fetch_state_climate(
    state: str, lat: float, lon: float, start_year: int, end_year: int
) -> pd.DataFrame:
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": f"{start_year}-01-01",
        "end_date": f"{end_year}-12-31",
        "daily": "temperature_2m_mean,precipitation_sum",
        "timezone": "Asia/Kolkata",
    }
    response = httpx.get(OPEN_METEO_URL, params=params, timeout=60.0)
    response.raise_for_status()
    data = response.json()

    daily = pd.DataFrame(
        {
            "date": pd.to_datetime(data["daily"]["time"]),
            "temp": data["daily"]["temperature_2m_mean"],
            "precip": data["daily"]["precipitation_sum"],
        }
    )
    daily["year"] = daily["date"].dt.year
    daily["state"] = state

    annual = (
        daily.groupby(["state", "year"], as_index=False)
        .agg(
            avg_temperature_c=("temp", "mean"),
            rainfall_mm=("precip", "sum"),
        )
        .round({"avg_temperature_c": 2, "rainfall_mm": 1})
    )
    return annual


import time

def fetch_climate_panel(
    start_year: int = DEFAULT_START_YEAR,
    end_year: int = DEFAULT_END_YEAR,
    states: list[str] | None = None,
) -> pd.DataFrame:
    """Download historical rainfall & temperature from Open-Meteo archive API with retries and rate limit avoidance."""
    target_states = states or list(STATE_COORDINATES.keys())
    frames: list[pd.DataFrame] = []

    logger.info("Fetching climate data from Open-Meteo for %d states", len(target_states))
    for state in target_states:
        if state not in STATE_COORDINATES:
            logger.warning("Skipping unknown state: %s", state)
            continue
        lat, lon = STATE_COORDINATES[state]
        fetched = False
        for attempt in range(3):
            try:
                time.sleep(1.2)  # Respect Open-Meteo free tier rate limits
                df = _fetch_state_climate(state, lat, lon, start_year, end_year)
                frames.append(df)
                logger.info("Climate: %s — %d years", state, len(df))
                fetched = True
                break
            except httpx.ConnectError:
                # A connection or DNS failure affects the entire source; let the
                # pipeline use its saved data instead of retrying every state.
                raise
            except Exception as exc:
                logger.warning("Climate fetch attempt %d failed for %s: %s", attempt + 1, state, exc)
                time.sleep(3.0 * (attempt + 1))

        if not fetched:
            logger.error("Could not fetch climate data for %s after 3 attempts", state)

    if not frames:
        raise ValueError("Could not fetch climate data from Open-Meteo.")

    return pd.concat(frames, ignore_index=True)
