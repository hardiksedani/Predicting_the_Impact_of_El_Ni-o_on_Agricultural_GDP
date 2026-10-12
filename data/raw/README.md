# Raw official-source files

This directory holds the original downloads. **Do not alter or replace them with the project's old sample CSVs.** Derived state-year files go in `data/interim/` and `data/processed/`; see [`scripts/OFFICIAL_PANEL_WORKFLOW.md`](../../scripts/OFFICIAL_PANEL_WORKFLOW.md) for the exact commands. Large raw files are excluded from Git by `.gitignore`, so another checkout must obtain the originals separately.

## Files present in this workspace

```text
data/raw/
├── economic/
│   ├── mospi_1999_2000/    # 32 state PDFs; separate older-price series
│   ├── mospi_2004_05.pdf   # separate older-price series
│   └── rbi_2011_12.pdf     # selected training target: crops GSVA
├── rainfall/               # rainfall_2001.nc … rainfall_2025.nc (25 files)
├── temperature/
│   ├── tmax/               # 2001.GRD … 2025.GRD (25 files)
│   └── tmin/               # 2001.GRD … 2025.GRD (25 files)
├── oni/                    # oni.ascii.txt
├── basin_boundaries/       # Subbasin.shp plus .shx, .dbf, .prj and companions
├── streamflow/             # seven state/UT river-discharge CSVs
└── imd/                    # earlier comparison files; not selected for this panel
```

The new model input is **not** `climate_raw.csv`, `oni_raw.csv`, or `agricultural_gva_raw.csv`. Those older sample inputs are not part of the official-panel workflow.

## Provenance and purpose

The links below retain the download sources provided with the raw archive. Verify each local file against its source metadata before publishing or redistributing it.

| Dataset | Provider and portal | Raw format | Use in the new panel |
| --- | --- | --- | --- |
| Daily rainfall | [India Meteorological Department (IMD Pune), 0.25° NetCDF rainfall](https://www.imdpune.gov.in/cmpg/Griddata/Rainfall_25_NetCDF.html) | Annual `.nc` with daily time × latitude × longitude grid | Sum daily rainfall in each April–March financial year at the nearest grid cell to a representative point |
| Daily Tmax | [IMD Pune maximum-temperature grid](https://www.imdpune.gov.in/cmpg/Griddata/Max_1_Bin.html) | Annual 1° `.GRD` binary grid | Pair with Tmin; missing marker `99.9` |
| Daily Tmin | [IMD Pune minimum-temperature grid](https://www.imdpune.gov.in/cmpg/Griddata/Min_1_Bin.html) | Annual 1° `.GRD` binary grid | Mean of `(Tmax + Tmin) / 2` across the financial year at the nearest grid cell |
| ONI | [NOAA Climate Prediction Center ONI](https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/oni/) | `oni.ascii.txt`, seasons `SEAS`, `YR`, `ANOM` | Mean of ten complete overlapping seasons within April–March. ONI is **not daily** |
| Agriculture target | Downloaded RBI/NSO Table 30, `economic/rbi_2011_12.pdf` | Published PDF table | **Agriculture (crops) GSVA**, constant 2011–12 prices, ₹ crore, by state and financial year |
| Older agriculture tables | Downloaded MoSPI `mospi_1999_2000/*.pdf`, `mospi_2004_05.pdf` | Published PDFs | Extracted for audit **only**; different price bases/accounting definitions are not blended into the selected target |
| River discharge | [Central Water Commission / India-WRIS / National Water Data Portal](https://www.nwdp.nwic.gov.in/dataset/river-discharge-manual-dailly-central-water-commission-cw) | Station-day CSV | **Not used** in this crop-GSVA project |
| Basin polygons | Survey of India / India-WRIS as named in the supplied archive; check local shapefile metadata for exact lineage | ESRI shapefile set | **Not used** for state aggregation: Krishna/Cauvery basin boundaries are not state boundaries |

Rainfall reference: [Pai et al. (2014)](https://doi.org/10.54302/mausam.v65i1.851). Temperature reference: [Srivastava, Rajeevan & Kshirsagar (2009)](https://doi.org/10.1002/asl.232). ONI reference supplied with the archive: [Kousky & Higgins (2007)](https://doi.org/10.1175/WAF987.1). Preserve the original archive's source notes and any licence terms.

## Why these formats differ

NetCDF carries coordinates, time and units alongside gridded numeric values. GRD is a compact binary sequence of temperature grids whose layout and missing-value code come from IMD's specification. ONI is a small overlapping three-month index table, so ASCII is sufficient. A shapefile uses several companion files for geometry, attributes, index and projection. Economic tables are PDFs because they are published statistical tables. There is no benefit in flattening every daily grid cell into CSV; the converter extracts only the 28 state-point observations needed for this model.

## What the converter does—and does not do

`scripts/prepare_official_panel.py` uses the required **2011–2025 calendar-year climate files** to produce **FY 2011–12 through FY 2024–25** rows. The earlier 2001–2010 climate files are preserved, not used in this comparable RBI panel. It uses one point per state from `data/metadata/state_representative_points.csv`; the nearest IMD grid cell is a **proxy, not a state-wide average or station observation**. A grid-cell center can fall outside a state boundary—especially with the 1° temperature grid, notably for Goa. The converter checks daily time axes, units, expected GRD byte lengths, and at least 95% climate coverage. The economic extractor preserves blanks and a separate issue report. Of 392 candidate cells, seven currently have no official target and are excluded rather than imputed, leaving **385 complete state-years across all 28 states**. These counts must be rechecked after source files change.

The selected target is *crop GSVA*, not total GDP or all agriculture/forestry/fishing. `year` stores the financial-year **start**: `2011` denotes FY 2011–12. Daily IMD inputs do not turn 14 annual labels into thousands of independent labels. The output CSV is a candidate supervised-learning panel; only the user's later manual `scripts/train_models.py` run fits the five models. No guaranteed R² improvement follows from using more official weather data.
