"""
Phase 8A API Router - Pipeline Orchestrator + Staleness Auto-Alerts

Endpoints:
  - POST /pipeline/run         - Trigger pipeline execution
  - GET  /pipeline/status      - Current orchestrator status
  - GET  /pipeline/history     - Run history with pagination

Background Task:
  - Staleness checker (runs every hour on startup)
    Checks collection freshness and auto-creates notifications
"""

import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger("BDKnowledgeAPI.phase8a")

router = APIRouter()

# =========================================
# ORCHESTRATOR SINGLETON
# =========================================

_orchestrator = None


def _get_orchestrator():
    """Lazy-init the pipeline orchestrator singleton."""
    global _orchestrator
    if _orchestrator is None:
        try:
            from Engine0_Orchestrator.orchestrator import PipelineOrchestrator
            _orchestrator = PipelineOrchestrator()
            logger.info("Pipeline orchestrator initialized")
        except ImportError as e:
            logger.warning(f"Pipeline orchestrator not available: {e}")
    return _orchestrator


# =========================================
# REQUEST MODELS
# =========================================

class PipelineRunRequest(BaseModel):
    test_mode: bool = False


# =========================================
# PIPELINE ENDPOINTS
# =========================================

@router.post("/pipeline/run")
async def run_pipeline(req: PipelineRunRequest):
    """Trigger a full pipeline execution."""
    orch = _get_orchestrator()
    if orch is None:
        raise HTTPException(status_code=503, detail="Pipeline orchestrator not available")

    if orch.is_running:
        raise HTTPException(status_code=409, detail="Pipeline is already running")

    # Run pipeline in background task
    async def _run():
        try:
            await orch.run(test_mode=req.test_mode)
        except Exception as e:
            logger.error(f"Background pipeline run failed: {e}")

    asyncio.create_task(_run())

    return {
        "success": True,
        "run_id": "starting",
        "status": "Pipeline execution started",
        "test_mode": req.test_mode,
    }


@router.get("/pipeline/status")
async def pipeline_status():
    """Get current pipeline orchestrator status."""
    orch = _get_orchestrator()
    if orch is None:
        # Return a default status when orchestrator isn't available
        return {
            "is_running": False,
            "current_run": None,
            "last_run": None,
            "history": [],
            "steps_definition": [],
            "stats": {"total_runs": 0, "success_rate": 0, "avg_duration": 0},
        }

    return orch.get_status()


@router.get("/pipeline/history")
async def pipeline_history(
    limit: int = Query(default=20, ge=1, le=100),
):
    """Get pipeline run history."""
    orch = _get_orchestrator()
    if orch is None:
        return {"runs": [], "total": 0}

    runs = orch.get_history(limit=limit)
    return {"runs": runs, "total": len(orch.history)}


# =========================================
# BACKGROUND STALENESS CHECKER
# =========================================

async def staleness_auto_alerts(interval_seconds: int = 3600):
    """
    Background task that checks collection freshness every hour.
    Auto-creates notifications for stale collections.

    Called from the API lifespan handler.
    """
    # Import here to avoid circular imports
    from Engine8_Knowledge.api_routers.phase7_endpoints import (
        _create_notification,
        _read_json,
        FRESHNESS_LOG,
    )

    logger.info(f"Staleness auto-alerts started (interval={interval_seconds}s)")

    # Wait 30 seconds on startup before first check
    await asyncio.sleep(30)

    while True:
        try:
            freshness = _read_json(FRESHNESS_LOG, {})
            now = datetime.utcnow()
            stale_collections = []

            for collection, info in freshness.items():
                if collection.startswith("_"):
                    continue  # Skip internal keys

                last_indexed = info.get("last_indexed") or info.get("timestamp")
                if not last_indexed:
                    continue

                try:
                    last_dt = datetime.fromisoformat(last_indexed.replace("Z", ""))
                    days_stale = (now - last_dt).days

                    if days_stale >= 14:
                        stale_collections.append((collection, days_stale, "critical"))
                    elif days_stale >= 7:
                        stale_collections.append((collection, days_stale, "warning"))
                except (ValueError, AttributeError):
                    continue

            # Create notifications for stale collections
            for coll_name, days, severity in stale_collections:
                _create_notification(
                    notif_type="stale_data",
                    title=f"{coll_name} collection is {days}d stale",
                    message=f"The {coll_name} collection hasn't been updated in {days} days. Consider running a pipeline refresh.",
                    entity_type="collection",
                    entity_id=coll_name,
                    priority=severity,
                )

            if stale_collections:
                logger.info(
                    f"Staleness check: {len(stale_collections)} stale collections detected"
                )
            else:
                logger.debug("Staleness check: all collections fresh")

        except Exception as e:
            logger.error(f"Staleness auto-alert error: {e}")

        await asyncio.sleep(interval_seconds)
