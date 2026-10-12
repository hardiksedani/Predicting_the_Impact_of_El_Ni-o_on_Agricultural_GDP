# Use your new raw data; train the five models yourself

Run these commands in the **VS Code PowerShell terminal from the project root**:

```powershell
cd 'C:\Users\hardi\Coding All Programs\pbl agriculture project'
& .\backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
& .\backend\.venv\Scripts\python.exe -m pip install -r scripts\requirements-economic.txt
```

If `backend\.venv\Scripts\python.exe` does not exist, create the environment first with `python -m venv backend\.venv`. The model trainer uses the packages in `backend\requirements.txt`; `pdfplumber` is needed for the economic extraction.

## 1. Check the downloaded files

Keep the original files in `data/raw/` without converting the full daily grids to giant CSVs:

| Source | Expected path | What it supplies |
| --- | --- | --- |
| IMD rainfall | `data/raw/rainfall/rainfall_2001.nc` … `rainfall_2025.nc` | Daily 0.25° rainfall grid |
| IMD temperature | `data/raw/temperature/tmax/2001.GRD` … `2025.GRD` and the same in `tmin/` | Daily 1° maximum and minimum temperature grids |
| NOAA CPC ONI | `data/raw/oni/oni.ascii.txt` | Seasonal ENSO index |
| RBI/NSO crop GSVA | `data/raw/economic/rbi_2011_12.pdf` | Official state/financial-year target at constant 2011–12 prices |
| Older MoSPI tables | `data/raw/economic/mospi_1999_2000/*.pdf` and `mospi_2004_05.pdf` | Separate historical series for review only; **not** mixed into the training target |

The `basin_boundaries/` shapefile covers river basins, not 28 state polygons. The `streamflow/` data is not used: this model's target is crop GSVA, not river discharge. The user chose **one representative point per state**, listed in `data/metadata/state_representative_points.csv`; the nearest IMD grid-cell values are *not* state-wide averages or station observations. Selected cell centers can fall outside state boundaries, notably Goa's coarse 1° temperature proxy.

## 2. Extract and review the economic values

```powershell
& .\backend\.venv\Scripts\python.exe scripts\extract_economic_targets.py --overwrite
```

Read `data/interim/economic/extraction_issues.csv` and check flagged cells against the cited PDF pages. The script preserves official blanks and flags unusual values; it does not fill, clip, or discard them. It writes all three series separately to `data/interim/economic/extracted_agriculture.csv`. The next step selects **only** `rbi_2011_12` (RBI/NSO GSVA Agriculture—crops, constant 2011–12 prices, ₹ crore) so incompatible price bases are never blended.

## 3. Prepare the climate/economic panel

```powershell
& .\backend\.venv\Scripts\python.exe scripts\prepare_official_panel.py --overwrite
```

Inspect `data/processed/official_panel_report.json` and spot-check `data/processed/official_panel.csv` before continuing. The script reads **your raw files**, computes April–March financial-year rainfall totals and mean temperature at the closest IMD grid cells, and averages ten complete NOAA ONI seasons within each financial year. It joins these with the RBI target by state and financial-year start (`year=2011` means FY 2011–12). It requires at least 95% daily climate coverage per state-year. It neither trains models nor changes the website database.

With the files currently in this workspace, the report records **392 candidate state-years** (28 states × 14 financial years from 2011–12 to 2024–25), **385 complete rows**, and **7 excluded rows** where the official target is blank: Goa 2024–25; Gujarat 2023–24 and 2024–25; Manipur, Mizoram, Nagaland and Sikkim 2024–25. All 28 states still have earlier complete rows. Rerun and review the report if you change any source file. The 2001–2010 climate downloads cannot create matching labels in the selected RBI 2011–12-base series.

Check that the report says `model_training_performed: false`. A prepared panel is **not** a trained model, and no R², MAE, or RMSE for the new data exists yet.

## 4. Sync the validated panel to the website

```powershell
& .\backend\.venv\Scripts\python.exe scripts\sync_official_panel.py
```

This copies only the validated, hash-checked panel into the website's separate `official_climate_gdp_data` collection. The legacy sample collection remains for recovery but is not read by active pages. The script refuses to overwrite a different existing official panel: stop and review the database rather than deleting it to force a sync. If Firebase is configured, this command writes to that configured cloud database; otherwise it uses the local database. Do not use the old `scripts/preprocess_data.py` or the old one-click `/api/pipeline/run` endpoint for this dataset.

## 5. Train manually when you are satisfied

Only you run this final command:

```powershell
& .\backend\.venv\Scripts\python.exe scripts\train_models.py
```

It verifies the synced collection matches the panel hash, then fits Linear Regression, Random Forest, Gradient Boosting, XGBoost and Extra Trees on the prepared panel. Four feature groups enter each model: rainfall, mean temperature, ONI, and one-hot state identity (fixed effects). State identity helps calibrate different state output levels, **not** establish an El Niño effect. The script uses an earlier-year training partition and later-year held-out partition, saves model artifacts and metrics, and enables prediction only for states represented in that training run. Read each model's MAE, RMSE and R²; **do not expect R² near 1** just because the climate inputs now come from IMD. The trainer selects the displayed best model by the same held-out test RMSE it reports, so its selected score is optimistic compared with a separate untouched final test. A strong pooled R² may also reflect persistent state-size differences; compare a state/year baseline and inspect errors by state before making claims.

## 6. Start and inspect the app

In one terminal:

```powershell
cd 'C:\Users\hardi\Coding All Programs\pbl agriculture project\backend'
& .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

In another terminal:

```powershell
cd 'C:\Users\hardi\Coding All Programs\pbl agriculture project\frontend'
npm install
npm run dev
```

Open `http://localhost:3000`. The frontend defaults to `http://localhost:8000` for the API. If port 8000 is unavailable, choose another backend port and set `NEXT_PUBLIC_API_BASE_URL` to match before starting `npm run dev`. Until step 5 completes, the 28 states may have data/history but **predictions and scenario outputs remain pending**.

If the global `npm` launcher reports a missing `npm-cli.js` but `frontend/node_modules` already exists, `node node_modules/next/dist/bin/next dev` starts the installed Next.js directly. Fix npm before a fresh dependency install; this direct command is not a replacement for `npm install`.

The source formats are intentional: NetCDF stores labeled time/latitude/longitude grids; GRD is a compact binary grid; ONI is a small seasonal ASCII table; PDF is the published economic table. Only the derived state-year panel needs to be CSV.
