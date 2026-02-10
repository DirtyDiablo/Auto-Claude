"""Phase 28A — ML API Router (12 endpoints)

FastAPI router exposing NER prediction/training, topic clustering,
placement prediction, and embedding training/benchmark endpoints.
"""
from dataclasses import asdict
from typing import Any, Dict, List, Optional

import structlog
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["ml-v2"])


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class NERPredictRequest(BaseModel):
    text: str


class NERTrainRequest(BaseModel):
    epochs: int = 30


class ClusterRequest(BaseModel):
    documents: List[str] = []
    days: int = 90


class PlacementPredictRequest(BaseModel):
    contact_tier: int = 3
    days_since_last_contact: int = 30
    interaction_count: int = 0
    response_rate: float = 0.0
    sentiment_score: float = 0.0
    program_pain_score: float = 0.0
    pts_past_perf_match: float = 0.0
    clearance_match: int = 0
    location_match: int = 0


class EmbeddingTrainRequest(BaseModel):
    epochs: int = 10


# ---------------------------------------------------------------------------
# Lazy component getters
# ---------------------------------------------------------------------------


def _get_ner():
    try:
        from Engine8_Knowledge.ml.defense_ner import get_defense_ner

        return get_defense_ner()
    except Exception:
        return None


def _get_modeler():
    try:
        from Engine8_Knowledge.ml.topic_modeler import get_topic_modeler

        return get_topic_modeler()
    except Exception:
        return None


def _get_predictor():
    try:
        from Engine8_Knowledge.ml.placement_predictor import get_placement_predictor

        return get_placement_predictor()
    except Exception:
        return None


def _get_adapter():
    try:
        from Engine8_Knowledge.ml.domain_adapter_v2 import get_domain_adapter_v2

        return get_domain_adapter_v2()
    except Exception:
        return None


# ---------------------------------------------------------------------------
# NER endpoints (3)
# ---------------------------------------------------------------------------


@router.post("/ml/ner/predict")
async def ner_predict(req: NERPredictRequest):
    """Extract defense-domain entities from text."""
    ner = _get_ner()
    if not ner:
        raise HTTPException(503, "NER engine not available")
    entities = ner.predict(req.text)
    return {"entities": [asdict(e) for e in entities], "count": len(entities)}


@router.post("/ml/ner/train")
async def ner_train(req: NERTrainRequest):
    """Train the NER model on auto-generated defense data."""
    ner = _get_ner()
    if not ner:
        raise HTTPException(503, "NER engine not available")
    data = ner.generate_training_data()
    metrics = ner.train(data, epochs=req.epochs)
    return asdict(metrics)


@router.get("/ml/ner/metrics")
async def ner_metrics():
    """Return NER model status and supported entity types."""
    ner = _get_ner()
    if not ner:
        return {"trained": False}
    return {"trained": ner._trained, "entity_types": ner.ENTITY_TYPES}


# ---------------------------------------------------------------------------
# Topic endpoints (3)
# ---------------------------------------------------------------------------


@router.post("/ml/topics/cluster-jobs")
async def cluster_jobs(req: ClusterRequest):
    """Cluster job posting documents into topics."""
    modeler = _get_modeler()
    if not modeler:
        raise HTTPException(503, "Topic modeler not available")
    result = await modeler.cluster_jobs(documents=req.documents, days=req.days)
    return asdict(result)


@router.post("/ml/topics/cluster-notes")
async def cluster_notes(req: ClusterRequest):
    """Cluster call/meeting notes into topics."""
    modeler = _get_modeler()
    if not modeler:
        raise HTTPException(503, "Topic modeler not available")
    result = await modeler.cluster_notes(documents=req.documents, days=req.days)
    return asdict(result)


@router.get("/ml/topics/trends/{topic_id}")
async def topic_trends(topic_id: int, days: int = Query(90)):
    """Retrieve temporal trend data for a specific topic."""
    modeler = _get_modeler()
    if not modeler:
        raise HTTPException(503, "Topic modeler not available")
    trend = await modeler.get_topic_trends(topic_id, days)
    return asdict(trend)


# ---------------------------------------------------------------------------
# Prediction endpoints (4)
# ---------------------------------------------------------------------------


@router.post("/ml/predict/placement")
async def predict_placement(req: PlacementPredictRequest):
    """Predict placement probability for a BD contact."""
    predictor = _get_predictor()
    if not predictor:
        raise HTTPException(503, "Placement predictor not available")
    prediction = predictor.predict(req.model_dump())
    return asdict(prediction)


@router.post("/ml/predict/train")
async def train_predictor():
    """Train the XGBoost placement model on synthetic data."""
    predictor = _get_predictor()
    if not predictor:
        raise HTTPException(503, "Placement predictor not available")
    result = predictor.train()
    return asdict(result)


@router.get("/ml/predict/feature-importance")
async def feature_importance():
    """Return ranked feature importance from the trained model."""
    predictor = _get_predictor()
    if not predictor:
        return {"features": []}
    features = predictor.get_feature_importance()
    return {"features": [asdict(f) for f in features]}


@router.get("/ml/predict/metrics")
async def predictor_metrics():
    """Return placement model status and feature list."""
    predictor = _get_predictor()
    if not predictor:
        return {"trained": False}
    return {"trained": predictor._trained, "features": predictor.feature_names}


# ---------------------------------------------------------------------------
# Embeddings endpoints (2)
# ---------------------------------------------------------------------------


@router.post("/ml/embeddings/train")
async def train_embeddings(req: EmbeddingTrainRequest):
    """Fine-tune domain embeddings with hard negative mining."""
    adapter = _get_adapter()
    if not adapter:
        raise HTTPException(503, "Domain adapter not available")
    result = adapter.train_with_hard_negatives([], epochs=req.epochs)
    return result


@router.get("/ml/embeddings/benchmark")
async def embeddings_benchmark():
    """Evaluate embedding quality on defense-domain benchmark."""
    adapter = _get_adapter()
    if not adapter:
        return {"status": "unavailable"}
    result = adapter.evaluate_on_benchmark()
    return asdict(result)
