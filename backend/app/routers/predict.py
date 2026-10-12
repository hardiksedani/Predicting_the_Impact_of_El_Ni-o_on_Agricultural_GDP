from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool

from app.constants import DISCLAIMER, MODEL_DISPLAY_NAMES, MODEL_NAMES
from app.models.schemas import PredictRequest, PredictResponse, SinglePrediction, TrainResponse
from app.services.ml import (
    get_all_model_runs,
    get_linear_climate_permutation,
    get_model_metrics,
    log_prediction,
    predict_gdp,
)

router = APIRouter(prefix="/api", tags=["models"])


@router.get("/models")
async def list_models():
    """List all supported regression models and their display labels."""
    metrics = get_model_metrics()
    best_m = metrics.get("best_model") if metrics else None
    return {
        "models": [
            {
                "id": name,
                "name": MODEL_DISPLAY_NAMES.get(name, name),
                "is_best": name == best_m,
                "metrics": metrics.get("models", {}).get(name) if metrics else None,
            }
            for name in MODEL_NAMES
        ],
        "best_model": best_m,
    }


@router.get("/models/comparison", response_model=TrainResponse)
async def models_comparison():
    metrics = get_model_metrics()
    if not metrics:
        raise HTTPException(
            status_code=404,
            detail="No trained models found. Run POST /api/train first.",
        )
    permutation = await run_in_threadpool(get_linear_climate_permutation, metrics)
    return TrainResponse(**metrics, linear_permutation=permutation)


@router.get("/models/best")
async def get_best_model():
    metrics = get_model_metrics()
    if not metrics or "best_model" not in metrics:
        raise HTTPException(status_code=404, detail="No models trained yet.")
    best_name = metrics["best_model"]
    return {
        "best_model": best_name,
        "name_display": MODEL_DISPLAY_NAMES.get(best_name, best_name),
        "selection_metric": metrics.get("selection_metric", "rmse"),
        "metrics": metrics["models"].get(best_name),
        "trained_at": metrics.get("trained_at"),
    }


@router.get("/models/runs")
async def list_model_runs():
    runs = get_all_model_runs()
    return {"runs": runs, "total": len(runs)}


@router.post("/predict", response_model=PredictResponse)
async def predict(body: PredictRequest):
    try:
        result = predict_gdp(
            state=body.state,
            rainfall=body.rainfall,
            temperature=body.temperature,
            oni_index=body.oni_index,
            model_name=body.model,
        )
        log_prediction(
            body.state,
            body.rainfall,
            body.temperature,
            body.oni_index,
            result["predictions"],
        )
        return PredictResponse(
            state=result["state"],
            historical_avg_gdp_cr=result["historical_avg_gdp_cr"],
            predictions=[SinglePrediction(**p) for p in result["predictions"]],
            ensemble_gdp_cr=result.get("ensemble_gdp_cr"),
            disclaimer=DISCLAIMER,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Prediction failed. Check server logs for details.",
        )
