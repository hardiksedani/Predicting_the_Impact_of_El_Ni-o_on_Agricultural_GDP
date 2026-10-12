from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api", tags=["train"])


@router.post("/train")
async def train_models():
    raise HTTPException(
        status_code=409,
        detail="One-click training is disabled. Review the official panel and run scripts/train_models.py manually.",
    )
