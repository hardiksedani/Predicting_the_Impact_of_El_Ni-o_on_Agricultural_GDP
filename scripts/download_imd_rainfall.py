"""Download official IMD 1-degree rainfall and extract annual centroid totals.

Run from the repository root with backend/.venv/Scripts/python.exe
scripts/download_imd_rainfall.py. The NetCDF files are retained locally but
ignored by Git; the small state-year CSV supports an optional comparison mode.
"""

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import httpx
import numpy as np
import pandas as pd
from scipy.io import netcdf_file

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.ingestion.states import (  # noqa: E402
    DEFAULT_END_YEAR,
    DEFAULT_START_YEAR,
    STATE_COORDINATES,
)

DOWNLOAD_URL = "https://imdpune.gov.in/cmpg/Griddata/rainfallone.php"
SOURCE_PAGE = "https://www.imdpune.gov.in/cmpg/Griddata/Rainfall_1_NetCDF.html"
RAW_DIR = ROOT / "data" / "raw" / "imd"
OUTPUT = ROOT / "data" / "raw" / "imd_rainfall_raw.csv"
PROVENANCE = ROOT / "data" / "metadata" / "imd_rainfall_provenance.json"


def download_year(year: int, *, retries: int = 4) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / f"imd_rf_1x1_{year}.nc"
    if path.is_file() and path.stat().st_size > 1_000_000:
        return path

    for attempt in range(retries):
        part = path.with_suffix(".part")
        try:
            with httpx.Client(timeout=120.0, follow_redirects=True) as client:
                with client.stream("POST", DOWNLOAD_URL, data={"rainone": str(year)}) as response:
                    response.raise_for_status()
                    if "application/octet-stream" not in response.headers.get("content-type", ""):
                        raise ValueError(f"IMD returned non-NetCDF content for {year}")
                    with part.open("wb") as stream:
                        for chunk in response.iter_bytes():
                            stream.write(chunk)
            if part.stat().st_size < 1_000_000:
                raise ValueError(f"IMD returned an unexpectedly small file for {year}")
            part.replace(path)
            return path
        except (httpx.HTTPError, OSError, ValueError) as exc:
            part.unlink(missing_ok=True)
            if attempt == retries - 1:
                raise RuntimeError(f"Could not download IMD rainfall for {year}: {exc}") from exc
            print(f"{year}: attempt {attempt + 1} failed: {exc}; retrying", flush=True)
            time.sleep(3 * (attempt + 1))
    raise AssertionError("unreachable")


def extract_year(path: Path, year: int) -> list[dict[str, object]]:
    with netcdf_file(path, "r", mmap=False) as dataset:
        latitudes = np.asarray(dataset.variables["LATITUDE"][:])
        longitudes = np.asarray(dataset.variables["LONGITUDE"][:])
        rainfall = np.asarray(dataset.variables["RAINFALL"][:])
        expected_days = 366 if pd.Timestamp(year, 12, 31).is_leap_year else 365
        if rainfall.shape != (expected_days, len(latitudes), len(longitudes)):
            raise ValueError(f"Unexpected IMD grid shape for {year}: {rainfall.shape}")

        rows = []
        for state, (lat, lon) in STATE_COORDINATES.items():
            lat_idx = int(np.argmin(np.abs(latitudes - lat)))
            lon_idx = int(np.argmin(np.abs(longitudes - lon)))
            values = rainfall[:, lat_idx, lon_idx]
            if not np.isfinite(values).all() or (values < 0).any():
                raise ValueError(f"Missing IMD rainfall at {state} centroid in {year}")
            rows.append(
                {
                    "state": state,
                    "year": year,
                    "rainfall_mm": round(float(values.sum()), 2),
                }
            )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-year", type=int, default=DEFAULT_START_YEAR)
    parser.add_argument("--end-year", type=int, default=DEFAULT_END_YEAR)
    parser.add_argument("--offline", action="store_true", help="Use downloaded NetCDF files only")
    args = parser.parse_args()
    if args.start_year > args.end_year:
        parser.error("start-year must be at most end-year")

    rows = []
    hashes = {}
    for year in range(args.start_year, args.end_year + 1):
        path = RAW_DIR / f"imd_rf_1x1_{year}.nc"
        if not args.offline:
            path = download_year(year)
        if not path.is_file():
            raise FileNotFoundError(f"Missing {path}; run without --offline")
        rows.extend(extract_year(path, year))
        hashes[str(year)] = hashlib.sha256(path.read_bytes()).hexdigest()
        print(f"{year}: extracted {len(STATE_COORDINATES)} state centroids", flush=True)

    panel = pd.DataFrame(rows).sort_values(["state", "year"])
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    panel.to_csv(OUTPUT, index=False)
    PROVENANCE.parent.mkdir(parents=True, exist_ok=True)
    PROVENANCE.write_text(
        json.dumps(
            {
                "provider": "India Meteorological Department, Climate Research & Services, Pune",
                "source_page": SOURCE_PAGE,
                "download_endpoint": DOWNLOAD_URL,
                "years": [args.start_year, args.end_year],
                "spatial_method": "nearest 1-degree grid cell to each state centroid; not a state-wide average",
                "temporal_method": "sum daily rainfall in each calendar year",
                "units": "mm",
                "netcdf_sha256_by_year": hashes,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(panel)} rows to {OUTPUT}")


if __name__ == "__main__":
    main()
