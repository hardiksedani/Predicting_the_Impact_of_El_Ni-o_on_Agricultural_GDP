# Extracting the downloaded agriculture target PDFs

The script reads the 32 state PDFs in `data/raw/economic/mospi_1999_2000/`,
`data/raw/economic/mospi_2004_05.pdf`, and `data/raw/economic/rbi_2011_12.pdf`.
It selects **row 1 Agriculture at constant prices** from each MoSPI table and
**RBI Table 30 (Agriculture, constant prices)** for all 28 current Indian states
(Union Territories are not included in this state-only catalogue).
It does not extract the total GSDP, forestry, fishing, or current-price rows.

From PowerShell in the project root:

```powershell
cd 'C:\Users\hardi\Coding All Programs\pbl agriculture project'
& .\backend\.venv\Scripts\python.exe -m pip install -r scripts\requirements-economic.txt
& .\backend\.venv\Scripts\python.exe scripts\extract_economic_targets.py
```

The script writes four files in `data/interim/economic/`:

- `extracted_agriculture.csv`: all extracted cells, including blanks for missing official values, source PDF and page, financial year, lakh and converted crore.
- `complete_cases_by_source.csv`: only positive, nonmissing cells. It still contains three **different** series and is **not** a ready-to-train dataset.
- `extraction_issues.csv`: missing values, suspicious year-on-year changes, and extraction errors for manual review. A large change is flagged, **not automatically deleted**; it might be a real drought or recovery.
- `extraction_summary.json`: row counts, state/year coverage and explicit training-readiness warning.

The source PDFs are not changed. The script does **not** fill missing values,
clip valid official values, remove real climate-related extremes, or train a model.
To regenerate the four output files, use `--overwrite`; avoid hand-editing these
generated outputs because the next run would replace your changes.

The downloaded 1999-2000 series has no separate Telangana PDF, because that
state did not exist separately for most of that period. Keep this as an explicit
coverage gap; do not invent values by copying Andhra Pradesh. Official blank
cells remain blank, and flagged year-on-year jumps need comparison with the
source page before use.

Before training, inspect every issue and compare representative cells against
the cited PDF pages. Decide how to reconcile the 1999-2000 and 2004-05 MoSPI
factor-cost series with the RBI/NSO 2011-12-base GSVA crops series. The
pre/post Telangana Andhra Pradesh boundary change also needs review. Align
April-March financial-year targets with a documented weather window, then
build a state-year panel. The existing `scripts/preprocess_data.py` is **not**
the converter for these PDFs and currently clips `agricultural_gdp_cr` at
10,000; do not run it on these official values without correcting that logic.

The website lists all 28 states, but lists them as prediction-ready only when
the stored panel contains a historical target for that state and the current
model metadata records it as a training state. The newly extracted PDF rows
are **not** automatically inserted into the training database. After you
prepare and verify a consistent all-state climate/economic panel, retrain the
five models manually and inspect their out-of-time test results before making
predictions for additional states.
Older model runs without recorded `training_states` are conservatively marked
unavailable because the current database may contain states added **after**
the model was trained. A new manual training run records that field.

To run the parser tests:

```powershell
& .\backend\.venv\Scripts\python.exe scripts\test_extract_economic_targets.py
```
