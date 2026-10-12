from collections import defaultdict

from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    HistoryRow,
    StateHistoryResponse,
    StateSummary,
    StatesResponse,
    YearGdpPoint,
)
from app.constants import OFFICIAL_CLIMATE_METHOD, OFFICIAL_COLLECTION, OFFICIAL_TARGET_SOURCE
from app.services.db_storage import get_db
from app.services.ingestion.states import INDIAN_STATES
from app.services.ml import get_model_metrics

router = APIRouter(prefix="/api/states", tags=["states"])


@router.get("", response_model=StatesResponse)
async def list_states():
    db = get_db()
    docs = db.collection(OFFICIAL_COLLECTION).stream()
    metrics = get_model_metrics()
    trained_states = set(metrics.get("training_states") or []) if metrics else set()

    by_state: dict[str, list] = defaultdict(list)
    hashes_by_state: dict[str, set[str]] = defaultdict(set)
    for doc in docs:
        data = doc.to_dict()
        state = data.get("state")
        year = data.get("year")
        gdp = data.get("agricultural_gdp_cr")
        if (state and year is not None and gdp is not None and
                data.get("source") == OFFICIAL_TARGET_SOURCE and
                data.get("climate_method") == OFFICIAL_CLIMATE_METHOD):
            by_state[state].append({"year": int(year), "agricultural_gdp_cr": float(gdp)})
            hashes_by_state[state].add(str(data.get("panel_sha256", "")))

    states = []
    for state in INDIAN_STATES:
        points = by_state.get(state, [])
        points.sort(key=lambda p: p["year"])
        matches_active_run = bool(
            metrics and points and state in trained_states and
            hashes_by_state[state] == {metrics.get("panel_sha256")}
        )
        states.append(
            StateSummary(
                state=state,
                trend=[YearGdpPoint(**p) for p in points],
                prediction_available=matches_active_run,
            )
        )

    return StatesResponse(states=states)


@router.get("/{state}/history", response_model=StateHistoryResponse)
async def state_history(state: str):
    db = get_db()
    docs = (
        db.collection(OFFICIAL_COLLECTION)
        .where("state", "==", state)
        .order_by("year")
        .stream()
    )

    history = []
    for doc in docs:
        data = doc.to_dict()
        if (data.get("source") != OFFICIAL_TARGET_SOURCE or
                data.get("climate_method") != OFFICIAL_CLIMATE_METHOD):
            continue
        history.append(
            HistoryRow(
                year=int(data["year"]),
                rainfall_mm=float(data["rainfall_mm"]),
                avg_temperature_c=float(data["avg_temperature_c"]),
                oni_index=float(data["oni_index"]),
                agricultural_gdp_cr=float(data["agricultural_gdp_cr"]),
            )
        )

    if not history:
        raise HTTPException(status_code=404, detail=f"No data found for state: {state}")

    return StateHistoryResponse(state=state, history=history)
