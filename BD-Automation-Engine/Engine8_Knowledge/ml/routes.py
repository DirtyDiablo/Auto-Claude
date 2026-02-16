"""
ML API Routes — FastAPI router for predictive BD intelligence endpoints.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ml", tags=["ML Predictions"])


# ─── Request/Response Models ────────────────────────────────────────────────


class PredictRequestSingle(BaseModel):
    contact_tier: int = 3
    interaction_count: int = 0
    days_since_last: int = 30
    channel: str = "email"
    program_value: str = "0"
    hiring_velocity: float = 0.0
    day_of_week: Optional[int] = None


class PredictRequestBatch(BaseModel):
    contacts: List[PredictRequestSingle]


class TrainRequest(BaseModel):
    n_samples: int = 5000


# ─── Response Prediction Endpoints ──────────────────────────────────────────


@router.post("/predict-response")
async def predict_response(request: PredictRequestSingle):
    """
    Predict response probability for a single contact.

    Returns probability (0-1) and confidence category.
    """
    from Engine8_Knowledge.ml.response_predictor import get_response_predictor

    try:
        predictor = get_response_predictor()
        features = request.model_dump()
        probability = predictor.predict(features)

        # Categorize confidence
        if probability >= 0.7:
            category = "high"
        elif probability >= 0.4:
            category = "medium"
        else:
            category = "low"

        return {
            "probability": round(probability, 4),
            "category": category,
            "features_used": list(features.keys()),
        }
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict-response/batch")
async def predict_response_batch(request: PredictRequestBatch):
    """Predict response probabilities for multiple contacts."""
    from Engine8_Knowledge.ml.response_predictor import get_response_predictor

    try:
        predictor = get_response_predictor()
        features_list = [c.model_dump() for c in request.contacts]
        probabilities = predictor.batch_predict(features_list)

        results = []
        for prob in probabilities:
            category = "high" if prob >= 0.7 else "medium" if prob >= 0.4 else "low"
            results.append({"probability": round(prob, 4), "category": category})

        return {"predictions": results, "count": len(results)}
    except Exception as e:
        logger.error(f"Batch prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model-status")
async def model_status():
    """Get model status including training date and feature importance."""
    from Engine8_Knowledge.ml.response_predictor import get_response_predictor

    try:
        predictor = get_response_predictor()
        return predictor.get_status()
    except Exception as e:
        logger.error(f"Model status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/train")
async def train_model(request: TrainRequest):
    """Retrain the response prediction model on synthetic data."""
    from Engine8_Knowledge.ml.response_predictor import get_response_predictor

    try:
        predictor = get_response_predictor()
        metrics = predictor.train(n_samples=request.n_samples)
        return {"success": True, "metrics": metrics}
    except Exception as e:
        logger.error(f"Training error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─── Hiring Signal Endpoints ────────────────────────────────────────────────


@router.get("/hiring-signals")
async def get_hiring_signals(
    refresh: bool = Query(False, description="Re-run detection on latest data"),
):
    """
    Get active hiring signals.

    Returns detected anomalies: hiring surges, new capabilities, clearance escalations.
    """
    from Engine8_Knowledge.ml.hiring_signals import get_signal_detector

    try:
        detector = get_signal_detector()

        if refresh or not detector.get_active_signals():
            # Fetch jobs from vector store or API
            jobs_data = await _fetch_jobs_for_signals()
            detector.detect_signals(jobs_data)

        signals = detector.get_active_signals()
        return {
            "signals": [s.to_dict() for s in signals],
            "count": len(signals),
            "status": detector.get_status(),
        }
    except Exception as e:
        logger.error(f"Hiring signals error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hiring-signals/status")
async def hiring_signals_status():
    """Get hiring signal detector status."""
    from Engine8_Knowledge.ml.hiring_signals import get_signal_detector

    detector = get_signal_detector()
    return detector.get_status()


# ─── Helper ─────────────────────────────────────────────────────────────────


async def _fetch_jobs_for_signals() -> list:
    """Fetch job data for signal detection from the API's own data."""
    import httpx

    try:
        async with httpx.AsyncClient(base_url="http://localhost:8100") as client:
            resp = await client.get(
                "/api/v2/jobs", params={"limit": 2000}, timeout=10.0
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("jobs", [])
    except Exception as e:
        logger.warning(f"Could not fetch jobs from API: {e}")

    return []
