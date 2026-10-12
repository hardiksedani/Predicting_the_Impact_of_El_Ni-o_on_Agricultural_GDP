from fastapi import APIRouter, HTTPException

from app.models.schemas import PipelineStatusResponse
from app.services.pipeline import get_pipeline_status

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])

@router.post("/run", response_model=PipelineStatusResponse)
async def run_pipeline():
    """The legacy automatic path is disabled to protect the official panel."""
    raise HTTPException(
        status_code=409,
        detail=("Legacy Open-Meteo/sample-target pipeline is disabled. Prepare the new "
                "IMD/NOAA/RBI panel locally, then run scripts/train_models.py manually."),
    )


@router.get("/status", response_model=PipelineStatusResponse)
async def pipeline_status():
    status = get_pipeline_status()
    if not status:
        return PipelineStatusResponse(
            status="idle",
            message="Legacy automatic pipeline is disabled. Use the new raw-data preparation scripts.",
        )
    return PipelineStatusResponse(**status)
