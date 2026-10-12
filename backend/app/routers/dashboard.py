from fastapi import APIRouter

from app.models.schemas import DashboardSummary
from app.services.db_storage import get_db
from app.services.ml import fetch_climate_dataframe, get_model_metrics

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
async def dashboard_summary():
    df = fetch_climate_dataframe()

    states_count = 0
    years_count = 0
    records_count = 0
    year_min = None
    year_max = None

    if not df.empty and "state" in df.columns:
        states_count = int(df["state"].nunique())
        records_count = len(df)
        if "year" in df.columns and not df["year"].dropna().empty:
            year_min = int(df["year"].min())
            year_max = int(df["year"].max())
            years_count = int(df["year"].nunique())

    metrics = get_model_metrics()
    best_model = metrics.get("best_model") if metrics else None
    best_r2 = None
    best_rmse = None
    if metrics and best_model and "models" in metrics and best_model in metrics["models"]:
        best_r2 = metrics["models"][best_model].get("r2")
        best_rmse = metrics["models"][best_model].get("rmse")

    db = get_db()
    latest_docs = (
        db.collection("predictions")
        .order_by("created_at", direction="DESCENDING")
        .limit(100)
        .stream()
    )
    latest_prediction = None
    for doc in latest_docs:
        data = doc.to_dict()
        if (metrics and data.get("panel_sha256") == metrics.get("panel_sha256") and
                data.get("model_run_id") == metrics.get("run_id")):
            latest_prediction = {
                "state": data.get("state"),
                "predicted_impact_pct": data.get("predicted_impact_pct"),
                "model_used": data.get("model_used"),
                "created_at": data.get("created_at"),
            }
            break

    return DashboardSummary(
        states_count=states_count,
        years_count=years_count,
        records_count=records_count,
        year_min=year_min,
        year_max=year_max,
        best_model=best_model,
        best_r2=best_r2,
        best_rmse=best_rmse,
        latest_prediction=latest_prediction,
    )
