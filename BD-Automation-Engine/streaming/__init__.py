"""
BD Streaming Pipeline Module.

Real-time streaming capabilities for BD intelligence using Pathway:
- Live opportunity monitoring from SAM.gov
- Contract alerts from FPDS
- Streaming RAG for knowledge base
- Recompete signal detection
- Competitor activity tracking

Usage:
    from streaming import BDStreamingPipeline, PathwayConfig, run_pipeline

    # Quick start with defaults
    run_pipeline()

    # With custom config
    config = PathwayConfig(
        kafka_bootstrap_servers="kafka:9092",
        postgres_connection="postgresql://localhost:5432/bd",
    )
    pipeline = BDStreamingPipeline(config)
    pipeline.run_bd_intelligence_pipeline()

API Integration:
    from streaming import include_streaming_router
    include_streaming_router(app)  # Adds /streaming/* endpoints

Note: Pathway requires Linux/macOS. On Windows, use WSL, Docker, or a VM.
"""

from .pathway_config import PathwayConfig, load_config_from_env

# Pathway is only available on Linux/macOS
# Import pipeline components conditionally
PATHWAY_AVAILABLE = False
BDStreamingPipeline = None
run_pipeline = None

try:
    from .bd_streaming_pipeline import BDStreamingPipeline, run_pipeline
    PATHWAY_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    pass

# Always import the API router (it handles unavailability gracefully)
from .streaming_api import router as streaming_router, include_streaming_router

__all__ = [
    "PathwayConfig",
    "load_config_from_env",
    "BDStreamingPipeline",
    "run_pipeline",
    "streaming_router",
    "include_streaming_router",
    "PATHWAY_AVAILABLE",
]
