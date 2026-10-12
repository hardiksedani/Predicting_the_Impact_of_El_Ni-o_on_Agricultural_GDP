"""Legacy automated pipeline status and disabled entry point.

The former service downloaded or reused sample climate/economic data and wrote
them to the legacy collection. The official-panel workflow is intentionally
manual and audited, so that old path must never run or mutate data.
"""

from typing import Any

from app.services.db_storage import get_db
from app.services.ingestion.states import DEFAULT_END_YEAR, DEFAULT_START_YEAR


def run_full_pipeline(
    start_year: int = DEFAULT_START_YEAR,
    end_year: int = DEFAULT_END_YEAR,
    rainfall_source: str = "open_meteo",
) -> dict[str, Any]:
    """Keep the old API symbol, but prevent legacy downloads and writes."""
    raise ValueError(
        "The legacy automated pipeline is disabled: it used non-official sample data. "
        "Prepare and sync the official raw-data panel, then run scripts/train_models.py manually."
    )


def get_pipeline_status() -> dict[str, Any] | None:
    """Read prior status for diagnosis without starting the retired pipeline."""
    db = get_db()
    doc = db.collection("pipeline_runs").document("current").get()
    if not doc.exists:
        return None
    return doc.to_dict()
