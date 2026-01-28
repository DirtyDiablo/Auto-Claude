"""
FastAPI Router for Streaming Pipeline Control.

Provides REST API endpoints to control the Pathway streaming pipeline:
- Start/stop pipeline
- Get pipeline status
- View real-time metrics

Note: Pathway requires Linux/macOS. On Windows, endpoints will report unavailability.
"""

import threading
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass, field

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from .pathway_config import PathwayConfig

# Pathway is only available on Linux/macOS
PATHWAY_AVAILABLE = False
BDStreamingPipeline = None

try:
    from .bd_streaming_pipeline import BDStreamingPipeline
    PATHWAY_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    pass

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/streaming", tags=["streaming"])


# =============================================================================
# MODELS
# =============================================================================

class PipelineConfig(BaseModel):
    """Configuration for starting the pipeline."""
    kafka_bootstrap_servers: str = "localhost:9092"
    postgres_connection: str = "postgresql://localhost:5432/bd_intelligence"
    s3_bucket: str = "bd-intelligence-data"
    embedding_model: str = "text-embedding-3-small"
    batch_size: int = 100
    checkpoint_interval_ms: int = 30000
    sam_source: str = "data/streaming/sam_opportunities/"
    fpds_source: str = "data/streaming/fpds_contracts/"
    bullhorn_source: str = "data/streaming/bullhorn_activities/"
    output_postgres: bool = True
    output_kafka: bool = False
    output_webhook: bool = True
    webhook_url: Optional[str] = None


class PipelineStatus(BaseModel):
    """Pipeline status response."""
    status: str
    running: bool
    started_at: Optional[str] = None
    uptime_seconds: Optional[float] = None
    error: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


class PipelineMetrics(BaseModel):
    """Real-time pipeline metrics."""
    opportunities_processed: int = 0
    contracts_processed: int = 0
    activities_processed: int = 0
    alerts_generated: int = 0
    relevant_opportunities: int = 0
    recompete_signals: int = 0
    competitor_wins: int = 0
    last_updated: str = ""


# =============================================================================
# GLOBAL STATE
# =============================================================================

@dataclass
class PipelineState:
    """Global pipeline state."""
    running: bool = False
    started_at: Optional[datetime] = None
    config: Optional[PipelineConfig] = None
    pipeline: Optional[BDStreamingPipeline] = None
    thread: Optional[threading.Thread] = None
    error: Optional[str] = None
    metrics: Dict[str, int] = field(default_factory=lambda: {
        "opportunities_processed": 0,
        "contracts_processed": 0,
        "activities_processed": 0,
        "alerts_generated": 0,
        "relevant_opportunities": 0,
        "recompete_signals": 0,
        "competitor_wins": 0,
    })


_state = PipelineState()
_state_lock = threading.Lock()


# =============================================================================
# PIPELINE EXECUTION
# =============================================================================

def _run_pipeline_thread(config: PipelineConfig) -> None:
    """Run the pipeline in a background thread."""
    global _state

    if not PATHWAY_AVAILABLE or BDStreamingPipeline is None:
        with _state_lock:
            _state.error = "Pathway not available. Requires Linux/macOS. Use WSL, Docker, or VM on Windows."
            _state.running = False
        return

    try:
        # Convert PipelineConfig to PathwayConfig
        pathway_config = PathwayConfig(
            kafka_bootstrap_servers=config.kafka_bootstrap_servers,
            postgres_connection=config.postgres_connection,
            s3_bucket=config.s3_bucket,
            embedding_model=config.embedding_model,
            batch_size=config.batch_size,
            checkpoint_interval_ms=config.checkpoint_interval_ms,
            webhook_url=config.webhook_url,
        )

        pipeline = BDStreamingPipeline(pathway_config)

        with _state_lock:
            _state.pipeline = pipeline

        # Run the pipeline (blocking)
        pipeline.run_bd_intelligence_pipeline(
            sam_source=config.sam_source,
            fpds_source=config.fpds_source,
            bullhorn_source=config.bullhorn_source,
            output_postgres=config.output_postgres,
            output_kafka=config.output_kafka,
            output_webhook=config.output_webhook,
        )

    except Exception as e:
        logger.exception("Pipeline error")
        with _state_lock:
            _state.error = str(e)
            _state.running = False


# =============================================================================
# API ENDPOINTS
# =============================================================================

@router.get("/status", response_model=PipelineStatus)
async def get_pipeline_status() -> PipelineStatus:
    """
    Get the current pipeline status.

    Returns:
        Pipeline status including running state, uptime, and configuration
    """
    with _state_lock:
        uptime = None
        if _state.running and _state.started_at:
            uptime = (datetime.now() - _state.started_at).total_seconds()

        return PipelineStatus(
            status="running" if _state.running else "stopped",
            running=_state.running,
            started_at=_state.started_at.isoformat() if _state.started_at else None,
            uptime_seconds=uptime,
            error=_state.error,
            config=_state.config.model_dump() if _state.config else None,
        )


@router.post("/start", response_model=PipelineStatus)
async def start_pipeline(
    config: PipelineConfig,
    background_tasks: BackgroundTasks,
) -> PipelineStatus:
    """
    Start the streaming pipeline.

    Args:
        config: Pipeline configuration

    Returns:
        Pipeline status after starting

    Raises:
        HTTPException: If pipeline is already running or Pathway unavailable
    """
    global _state

    if not PATHWAY_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Pathway not available. Requires Linux/macOS. Use WSL, Docker, or VM on Windows."
        )

    with _state_lock:
        if _state.running:
            raise HTTPException(
                status_code=400,
                detail="Pipeline is already running"
            )

        _state.running = True
        _state.started_at = datetime.now()
        _state.config = config
        _state.error = None
        _state.metrics = {
            "opportunities_processed": 0,
            "contracts_processed": 0,
            "activities_processed": 0,
            "alerts_generated": 0,
            "relevant_opportunities": 0,
            "recompete_signals": 0,
            "competitor_wins": 0,
        }

    # Start pipeline in background thread
    thread = threading.Thread(
        target=_run_pipeline_thread,
        args=(config,),
        daemon=True,
    )
    thread.start()

    with _state_lock:
        _state.thread = thread

    logger.info(f"Pipeline started with config: {config.model_dump()}")

    return PipelineStatus(
        status="starting",
        running=True,
        started_at=_state.started_at.isoformat(),
        config=config.model_dump(),
    )


@router.post("/stop", response_model=PipelineStatus)
async def stop_pipeline() -> PipelineStatus:
    """
    Stop the running pipeline.

    Returns:
        Pipeline status after stopping

    Raises:
        HTTPException: If pipeline is not running
    """
    global _state

    with _state_lock:
        if not _state.running:
            raise HTTPException(
                status_code=400,
                detail="Pipeline is not running"
            )

        # Signal pipeline to stop
        if _state.pipeline:
            _state.pipeline.stop_pipeline()

        _state.running = False
        stopped_at = datetime.now()
        uptime = (stopped_at - _state.started_at).total_seconds() if _state.started_at else 0

    logger.info(f"Pipeline stopped after {uptime:.1f} seconds")

    return PipelineStatus(
        status="stopped",
        running=False,
        started_at=_state.started_at.isoformat() if _state.started_at else None,
        uptime_seconds=uptime,
    )


@router.get("/metrics", response_model=PipelineMetrics)
async def get_pipeline_metrics() -> PipelineMetrics:
    """
    Get real-time pipeline metrics.

    Returns:
        Current pipeline metrics including processed counts
    """
    with _state_lock:
        if not _state.running:
            return PipelineMetrics(
                last_updated=datetime.now().isoformat(),
            )

        return PipelineMetrics(
            opportunities_processed=_state.metrics.get("opportunities_processed", 0),
            contracts_processed=_state.metrics.get("contracts_processed", 0),
            activities_processed=_state.metrics.get("activities_processed", 0),
            alerts_generated=_state.metrics.get("alerts_generated", 0),
            relevant_opportunities=_state.metrics.get("relevant_opportunities", 0),
            recompete_signals=_state.metrics.get("recompete_signals", 0),
            competitor_wins=_state.metrics.get("competitor_wins", 0),
            last_updated=datetime.now().isoformat(),
        )


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint for the streaming service.

    Returns:
        Health status including Pathway availability
    """
    pathway_version = None
    if PATHWAY_AVAILABLE:
        try:
            import pathway as pw
            pathway_version = getattr(pw, "__version__", "unknown")
        except ImportError:
            pass

    return {
        "status": "healthy",
        "pathway_available": PATHWAY_AVAILABLE,
        "pathway_version": pathway_version,
        "pipeline_running": _state.running,
        "platform_note": None if PATHWAY_AVAILABLE else "Pathway requires Linux/macOS. Use WSL, Docker, or VM on Windows.",
        "timestamp": datetime.now().isoformat(),
    }


# =============================================================================
# INTEGRATION WITH MAIN API
# =============================================================================

def include_streaming_router(app) -> None:
    """
    Include the streaming router in the main FastAPI app.

    Usage:
        from streaming.streaming_api import include_streaming_router
        include_streaming_router(app)
    """
    app.include_router(router)
