"""
FastAPI router for CrewAI BD Agent endpoints.

Provides /agents/ endpoints for triggering crews and checking status.
"""

import uuid
import logging
from datetime import datetime
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger("BD-AgentRoutes")

router = APIRouter(prefix="/agents", tags=["agents"])

# ── In-memory task store ──
_tasks: dict[str, dict] = {}
_executor = ThreadPoolExecutor(max_workers=2)


# ── Request / Response models ──

class ResearchRequest(BaseModel):
    program_name: str
    agency: str = ""
    prime: str = ""


class OutreachRequest(BaseModel):
    contact_name: str
    company: str = ""
    program: str = ""


class WeeklyIntelRequest(BaseModel):
    focus_programs: list[str] = Field(default_factory=list)


class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str


class TaskStatus(BaseModel):
    task_id: str
    status: str
    crew_type: str
    created_at: str
    completed_at: Optional[str] = None
    result: Optional[dict] = None
    error: Optional[str] = None


# ── Background runner ──

def run_crew_background(task_id: str, crew, crew_type: str, inputs: dict):
    """Run a crew in background thread, store results, persist to Mem0."""
    _tasks[task_id]["status"] = "running"
    try:
        result = crew.kickoff(inputs=inputs)
        result_data = {
            "raw": str(result.raw) if hasattr(result, "raw") else str(result),
            "crew_type": crew_type,
            "inputs": inputs,
        }
        if hasattr(result, "pydantic") and result.pydantic:
            result_data["structured"] = result.pydantic.model_dump()

        # Capture individual task outputs so intermediate results aren't lost
        task_outputs = {}
        for i, task in enumerate(crew.tasks):
            if task.output:
                task_outputs[f"task_{i}_{task.agent.role}"] = str(task.output)[:5000]
        result_data["task_outputs"] = task_outputs

        _tasks[task_id]["status"] = "completed"
        _tasks[task_id]["result"] = result_data
        _tasks[task_id]["completed_at"] = datetime.now().isoformat()

        # Persist to Mem0
        try:
            from Engine8_Knowledge.scripts.memory_layer import get_memory
            mem = get_memory()
            summary = f"[{crew_type}] {inputs}  →  {str(result.raw)[:500]}" if hasattr(result, "raw") else str(result)[:500]
            mem.add(summary, user_id="bd_agents", metadata={"crew_type": crew_type, "task_id": task_id})
            logger.info("Saved crew result to Mem0: %s", task_id)
        except Exception as e:
            logger.warning("Mem0 persistence failed: %s", e)

    except Exception as e:
        logger.error("Crew %s failed: %s", task_id, e)
        _tasks[task_id]["status"] = "failed"
        _tasks[task_id]["error"] = str(e)
        _tasks[task_id]["completed_at"] = datetime.now().isoformat()


# ── Endpoints ──

@router.post("/research", response_model=TaskResponse)
async def run_bd_research(req: ResearchRequest):
    """Launch a BD research crew for a federal program."""
    try:
        from Engine8_Knowledge.agents.crews import create_bd_research_crew
    except ImportError as e:
        raise HTTPException(status_code=503, detail=f"CrewAI not available: {e}")

    crew = create_bd_research_crew(req.program_name, req.agency, req.prime)
    if crew is None:
        raise HTTPException(status_code=503, detail="CrewAI not available")

    task_id = uuid.uuid4().hex[:12]
    _tasks[task_id] = {
        "status": "queued",
        "crew_type": "bd_research",
        "created_at": datetime.now().isoformat(),
        "completed_at": None,
        "result": None,
        "error": None,
    }

    _executor.submit(
        run_crew_background, task_id, crew, "bd_research",
        {"program_name": req.program_name, "agency": req.agency, "prime": req.prime},
    )

    return TaskResponse(task_id=task_id, status="queued", message=f"BD research crew launched for '{req.program_name}'")


@router.post("/outreach", response_model=TaskResponse)
async def run_contact_outreach(req: OutreachRequest):
    """Launch a contact outreach crew."""
    try:
        from Engine8_Knowledge.agents.crews import create_contact_outreach_crew
    except ImportError as e:
        raise HTTPException(status_code=503, detail=f"CrewAI not available: {e}")

    crew = create_contact_outreach_crew(req.contact_name, req.company, req.program)
    if crew is None:
        raise HTTPException(status_code=503, detail="CrewAI not available")

    task_id = uuid.uuid4().hex[:12]
    _tasks[task_id] = {
        "status": "queued",
        "crew_type": "contact_outreach",
        "created_at": datetime.now().isoformat(),
        "completed_at": None,
        "result": None,
        "error": None,
    }

    _executor.submit(
        run_crew_background, task_id, crew, "contact_outreach",
        {"contact_name": req.contact_name, "company": req.company, "program": req.program},
    )

    return TaskResponse(task_id=task_id, status="queued", message=f"Outreach crew launched for '{req.contact_name}'")


@router.post("/weekly-intel", response_model=TaskResponse)
async def run_weekly_intel(req: WeeklyIntelRequest):
    """Launch a weekly intelligence digest crew."""
    try:
        from Engine8_Knowledge.agents.crews import create_weekly_intel_crew
    except ImportError as e:
        raise HTTPException(status_code=503, detail=f"CrewAI not available: {e}")

    crew = create_weekly_intel_crew(req.focus_programs or None)
    if crew is None:
        raise HTTPException(status_code=503, detail="CrewAI not available")

    task_id = uuid.uuid4().hex[:12]
    _tasks[task_id] = {
        "status": "queued",
        "crew_type": "weekly_intel",
        "created_at": datetime.now().isoformat(),
        "completed_at": None,
        "result": None,
        "error": None,
    }

    _executor.submit(
        run_crew_background, task_id, crew, "weekly_intel",
        {"focus_programs": req.focus_programs},
    )

    return TaskResponse(task_id=task_id, status="queued", message="Weekly intel crew launched")


@router.get("/status/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """Get the status and result of a crew task."""
    if task_id not in _tasks:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")

    t = _tasks[task_id]
    return TaskStatus(
        task_id=task_id,
        status=t["status"],
        crew_type=t["crew_type"],
        created_at=t["created_at"],
        completed_at=t.get("completed_at"),
        result=t.get("result"),
        error=t.get("error"),
    )


@router.get("/tasks")
async def list_tasks():
    """List all crew tasks with their status."""
    return {
        "total": len(_tasks),
        "tasks": [
            {
                "task_id": tid,
                "status": t["status"],
                "crew_type": t["crew_type"],
                "created_at": t["created_at"],
                "completed_at": t.get("completed_at"),
            }
            for tid, t in sorted(_tasks.items(), key=lambda x: x[1]["created_at"], reverse=True)
        ],
    }
