"""Publish only the validated new-raw panel to the website's official collection.

The legacy collection is left intact for recovery but is not read by the site.
This script does not fit or replace models.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.constants import OFFICIAL_COLLECTION, OFFICIAL_TARGET_SOURCE
from app.services.db_storage import get_db
from app.services.ml import state_slug
from app.services.ingestion.states import INDIAN_STATES

PANEL = ROOT / "data" / "processed" / "official_panel.csv"
REPORT = ROOT / "data" / "processed" / "official_panel_report.json"
SOURCE_PATHS = {
    "rbi_pdf": ROOT / "data" / "raw" / "economic" / "rbi_2011_12.pdf",
    "rbi_extraction_csv": ROOT / "data" / "interim" / "economic" / "extracted_agriculture.csv",
    "oni_ascii": ROOT / "data" / "raw" / "oni" / "oni.ascii.txt",
    "state_points": ROOT / "data" / "metadata" / "state_representative_points.csv",
}


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_sources(report: dict) -> None:
    """Ensure the prepared panel still corresponds to the supplied raw files."""
    if set(report.get("source_sha256", {})) != set(SOURCE_PATHS):
        raise ValueError("Validation report has incomplete source provenance")
    for label, path in SOURCE_PATHS.items():
        if not path.is_file() or file_sha256(path) != report["source_sha256"][label]:
            raise ValueError(f"Source {label} changed or is missing; rebuild the official panel")
    expected_climate = {
        path.relative_to(ROOT).as_posix()
        for year in range(2011, 2026)
        for path in (
            ROOT / "data" / "raw" / "rainfall" / f"rainfall_{year}.nc",
            ROOT / "data" / "raw" / "temperature" / "tmax" / f"{year}.GRD",
            ROOT / "data" / "raw" / "temperature" / "tmin" / f"{year}.GRD",
        )
    }
    recorded = report.get("climate_file_sha256", {})
    if set(recorded) != expected_climate:
        raise ValueError("Validation report has incomplete climate-file provenance")
    for relative_path, recorded_hash in recorded.items():
        path = ROOT / relative_path
        if not path.is_file() or file_sha256(path) != recorded_hash:
            raise ValueError(f"Climate file {relative_path} changed or is missing; rebuild the official panel")


def validated_panel() -> tuple[pd.DataFrame, str]:
    if not PANEL.is_file() or not REPORT.is_file():
        raise FileNotFoundError("Run scripts/prepare_official_panel.py first")
    digest = file_sha256(PANEL)
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    if report.get("panel_sha256") != digest:
        raise ValueError("Panel CSV changed after validation; regenerate the report")
    if report.get("input_years") != [2011, 2024] or report.get("model_training_performed") is not False:
        raise ValueError("Validation report describes an unexpected panel")
    verify_sources(report)
    panel = pd.read_csv(PANEL)
    required = {
        "state", "year", "rainfall_mm", "avg_temperature_c", "oni_index",
        "agricultural_gdp_cr", "target_source", "climate_method",
    }
    if not required.issubset(panel.columns) or panel[list(required)].isna().any().any():
        raise ValueError("Official panel has missing required values")
    if panel.duplicated(["state", "year"]).any() or set(panel["state"]) != set(INDIAN_STATES):
        raise ValueError("Official panel must have unique state-years for all 28 states")
    if set(panel["target_source"]) != {OFFICIAL_TARGET_SOURCE}:
        raise ValueError("Refusing a panel with non-RBI target values")
    if set(panel["climate_method"]) != {"nearest_representative_grid_point_fy_apr_mar"}:
        raise ValueError("Refusing a panel with unknown climate provenance")
    if len(panel) != report.get("training_ready_rows"):
        raise ValueError("Panel row count does not match validation report")
    numeric = ["year", "rainfall_mm", "avg_temperature_c", "oni_index", "agricultural_gdp_cr"]
    for column in numeric:
        panel[column] = pd.to_numeric(panel[column], errors="raise")
        if not panel[column].map(math.isfinite).all():
            raise ValueError(f"Official panel has non-finite {column} values")
    if not panel["year"].between(2011, 2024).all():
        raise ValueError("Official panel has years outside the comparable RBI series")
    if not panel["year"].eq(panel["year"].astype(int)).all():
        raise ValueError("Official panel has a non-integer financial-year start")
    if (panel["rainfall_mm"] < 0).any() or (panel["agricultural_gdp_cr"] <= 0).any():
        raise ValueError("Official panel has negative rainfall or nonpositive target")
    expected_fy = panel["year"].astype(int).map(lambda year: f"{year}-{(year + 1) % 100:02d}")
    if not panel["financial_year"].eq(expected_fy).all():
        raise ValueError("Official panel financial-year labels do not match years")
    return panel, digest


def expected_documents(panel: pd.DataFrame, digest: str) -> dict[str, dict]:
    records = {}
    for row in panel.itertuples(index=False):
        doc_id = f"{state_slug(row.state)}_{int(row.year)}"
        records[doc_id] = {
            "state": row.state,
            "year": int(row.year),
            "rainfall_mm": float(row.rainfall_mm),
            "avg_temperature_c": float(row.avg_temperature_c),
            "oni_index": float(row.oni_index),
            "agricultural_gdp_cr": float(row.agricultural_gdp_cr),
            "financial_year": row.financial_year,
            "source": OFFICIAL_TARGET_SOURCE,
            "climate_method": row.climate_method,
            "panel_sha256": digest,
        }
    if len(records) != len(panel):
        raise ValueError("State-year document IDs are not unique")
    return records


def verify_collection(panel: pd.DataFrame, digest: str, snapshots: list) -> None:
    """Reject a modified or partial website collection before manual training."""
    expected = expected_documents(panel, digest)
    actual = {doc.id: doc.to_dict() for doc in snapshots}
    if len(snapshots) != len(actual) or set(actual) != set(expected):
        raise ValueError("Official collection document IDs differ from the validated panel")
    for doc_id, fields in expected.items():
        if actual[doc_id] != fields:
            raise ValueError(f"Official collection row {doc_id} differs from the validated panel")


def sync() -> dict:
    panel, digest = validated_panel()
    db = get_db()
    collection = db.collection(OFFICIAL_COLLECTION)
    existing = list(collection.stream())
    if existing:
        verify_collection(panel, digest, existing)
        return {"status": "already_synced", "rows": len(panel), "panel_sha256": digest}

    batch = db.batch()
    pending = 0
    for doc_id, fields in expected_documents(panel, digest).items():
        ref = collection.document(doc_id)
        batch.set(ref, fields)
        pending += 1
        if pending == 400:
            batch.commit()
            batch = db.batch()
            pending = 0
    if pending:
        batch.commit()
    return {"status": "synced", "rows": len(panel), "panel_sha256": digest}


if __name__ == "__main__":
    print(json.dumps(sync(), indent=2))
