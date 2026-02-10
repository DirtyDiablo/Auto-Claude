"""
Phase 20A — Platform Stats API

Aggregated stats across all BD Intelligence services.
Provides a single endpoint for the SystemOverview dashboard.
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/platform", tags=["platform"])


async def _check_service(url: str, timeout: float = 3.0) -> dict:
    """Check if a service is reachable and return status."""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.get(url)
            return {"status": "online", "code": r.status_code, "latency_ms": round(r.elapsed.total_seconds() * 1000)}
    except Exception as e:
        return {"status": "offline", "error": str(e)[:100]}


@router.get("/stats")
async def platform_stats():
    """Aggregated stats across all BD Intelligence services."""

    # -- Service health checks --
    services = {}
    service_urls = {
        "hub_api": "http://127.0.0.1:8100/health",
        "qdrant": "http://127.0.0.1:6333/healthz",
    }
    for name, url in service_urls.items():
        services[name] = await _check_service(url)

    # -- Contact stats --
    contacts_stats = {"total": 0, "by_tier": {}, "by_program_top5": []}
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get("http://127.0.0.1:8100/api/v2/contacts", params={"limit": 1})
            if r.status_code == 200:
                contacts_stats["total"] = r.json().get("total", 0)
    except Exception:
        pass

    # -- Program stats --
    programs_stats = {"total": 0}
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get("http://127.0.0.1:8100/api/v2/programs", params={"limit": 1})
            if r.status_code == 200:
                programs_stats["total"] = r.json().get("total", 0)
    except Exception:
        pass

    # -- Jobs stats --
    jobs_stats = {"total": 0}
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get("http://127.0.0.1:8100/api/v2/jobs", params={"limit": 1})
            if r.status_code == 200:
                jobs_stats["total"] = r.json().get("total", 0)
    except Exception:
        pass

    # -- Qdrant collection stats --
    vector_stats = {"total_vectors": 0, "collections": []}
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get("http://127.0.0.1:6333/collections")
            if r.status_code == 200:
                collections = r.json().get("result", {}).get("collections", [])
                total = 0
                for col in collections:
                    col_name = col.get("name", "")
                    cr = await client.get(f"http://127.0.0.1:6333/collections/{col_name}")
                    if cr.status_code == 200:
                        count = cr.json().get("result", {}).get("points_count", 0)
                        vector_stats["collections"].append({"name": col_name, "points": count})
                        total += count
                vector_stats["total_vectors"] = total
    except Exception:
        pass

    # -- ML model stats --
    ml_stats = {"model_loaded": False, "model_type": "N/A", "drift_status": "unknown"}
    try:
        from Engine8_Knowledge.ml.response_predictor import get_response_predictor
        predictor = get_response_predictor()
        info = predictor.get_model_info()
        ml_stats["model_loaded"] = True
        ml_stats["model_type"] = info.get("model_type", "unknown")
        ml_stats["trained_at"] = info.get("trained_at", "never")
    except Exception:
        pass

    # -- Automation stats --
    automation_stats = {"scheduled_tasks": 0, "active_workflows": 0, "claude_queue": 0}
    try:
        from Engine8_Knowledge.automation.task_scheduler import get_task_scheduler
        scheduler = get_task_scheduler()
        schedule = scheduler.get_schedule()
        automation_stats["scheduled_tasks"] = len(schedule)
        enabled = sum(1 for t in schedule if t.get("enabled"))
        automation_stats["enabled_tasks"] = enabled
    except Exception:
        pass

    try:
        from Engine8_Knowledge.automation.agent_coordinator import get_agent_coordinator
        coordinator = get_agent_coordinator()
        automation_stats["active_workflows"] = len(coordinator.get_active_workflows())
        automation_stats["workflow_definitions"] = len(coordinator.workflows)
    except Exception:
        pass

    try:
        from Engine8_Knowledge.automation.auto_claude_tasks import get_claude_task_manager
        mgr = get_claude_task_manager()
        stats = mgr.get_stats()
        automation_stats["claude_queue"] = stats.get("pending", 0)
        automation_stats["claude_completed"] = stats.get("completed", 0)
    except Exception:
        pass

    # -- Graph stats --
    graph_stats = {"entities": 0, "relationships": 0}
    try:
        from Engine8_Knowledge.graph.bd_knowledge_graph import get_bd_knowledge_graph
        bg = get_bd_knowledge_graph()
        if bg:
            g_stats = bg.get_stats()
            graph_stats["entities"] = g_stats.get("total_entities", 0)
            graph_stats["relationships"] = g_stats.get("total_relationships", 0)
    except Exception:
        pass

    return {
        "timestamp": datetime.now().isoformat(),
        "services": services,
        "contacts": contacts_stats,
        "programs": programs_stats,
        "jobs": jobs_stats,
        "vectors": vector_stats,
        "ml": ml_stats,
        "automation": automation_stats,
        "graph": graph_stats,
    }


@router.get("/services")
async def platform_services():
    """Quick service health check."""
    checks = {
        "hub_api": "http://127.0.0.1:8100/health",
        "qdrant": "http://127.0.0.1:6333/healthz",
    }
    results = {}
    for name, url in checks.items():
        results[name] = await _check_service(url)
    return {"services": results, "checked_at": datetime.now().isoformat()}
