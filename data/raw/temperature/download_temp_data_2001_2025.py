"""
Download IMD gridded daily minimum temperature (tmin) data (2001-2025),
with per-year retries and resume support.

Requirements:
    pip install imdlib

Usage:
    python download_tmin_2001_2025.py

Notes:
- IMD's servers are often slow/flaky, so this retries each year
  individually (with a short pause) instead of failing the whole run.
- If a year's file already exists in the output folder, it's skipped
  on rerun - so if the script stops partway, just run it again.
"""

import os
import time

import imdlib as imd

START_YEAR = 2001
END_YEAR = 2025

VARIABLE = "tmin"
OUT_DIR = "tmin"

MAX_RETRIES = 4
RETRY_DELAY_SEC = 15

FILE_PREFIX = "mintemp"


def year_already_downloaded(year):
    fname = f"{FILE_PREFIX}{year}.GRD"
    return os.path.exists(os.path.join(OUT_DIR, fname))


def download_year(year):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            imd.get_data(
                VARIABLE,
                year,
                year,
                fn_format="yearwise",
                file_dir=OUT_DIR,
            )
            return True
        except Exception as e:
            print(f"  [{year}] attempt {attempt}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SEC)
    print(f"  [{year}] GAVE UP after {MAX_RETRIES} attempts.")
    return False


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"=== Downloading tmin for {START_YEAR}-{END_YEAR} ===")

    failed_years = []
    for year in range(START_YEAR, END_YEAR + 1):
        if year_already_downloaded(year):
            print(f"  {year}: already downloaded, skipping.")
            continue
        print(f"  {year}: downloading...")
        ok = download_year(year)
        if not ok:
            failed_years.append(year)

    if failed_years:
        print(f"\nFailed years: {failed_years}")
        print("Rerun this script to retry just the missing ones.")
    else:
        print(f"\nAll done. Files are in: {os.path.abspath(OUT_DIR)}")


if __name__ == "__main__":
    main()