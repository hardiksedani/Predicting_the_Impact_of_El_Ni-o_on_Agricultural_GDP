from fastapi import APIRouter, Query

from app.constants import OFFICIAL_COLLECTION
from app.models.schemas import ClimateDataRow, ClimateDataResponse
from app.services.db_storage import get_db

router = APIRouter(prefix="/api/data", tags=["data"])


@router.get("", response_model=ClimateDataResponse)
async def list_climate_data(
    state: str | None = Query(None),
    year_min: int | None = Query(None),
    year_max: int | None = Query(None),
):
    db = get_db()
    query = db.collection(OFFICIAL_COLLECTION)

    if state:
        query = query.where("state", "==", state)

    docs = query.stream()
    rows = []
    for doc in docs:
        data = doc.to_dict()
        year = int(data["year"])
        if year_min is not None and year < year_min:
            continue
        if year_max is not None and year > year_max:
            continue
        rows.append(
            ClimateDataRow(
                state=data["state"],
                year=year,
                rainfall_mm=float(data["rainfall_mm"]),
                avg_temperature_c=float(data["avg_temperature_c"]),
                oni_index=float(data["oni_index"]),
                agricultural_gdp_cr=float(data["agricultural_gdp_cr"]),
            )
        )

    rows.sort(key=lambda r: (r.state, r.year))
    return ClimateDataResponse(rows=rows, total=len(rows))
