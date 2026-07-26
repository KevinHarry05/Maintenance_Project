from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.ml_prediction_service import MLPredictionSingleton

router = APIRouter(prefix="/ai", tags=["AI"])


class AIPredictRequest(BaseModel):
    title: str
    description: str


class AIPredictResponse(BaseModel):
    category: str
    priority: str
    confidence: float


@router.post("/predict", response_model=AIPredictResponse)
async def predict(request: AIPredictRequest):
    if not request.title or not request.description:
        raise HTTPException(status_code=422, detail="title and description are required")

    confidence, priority, category = MLPredictionSingleton.instance().predict(
        request.title, request.description
    )

    return AIPredictResponse(
        category=category,
        priority=priority,
        confidence=round(confidence, 4),
    )
