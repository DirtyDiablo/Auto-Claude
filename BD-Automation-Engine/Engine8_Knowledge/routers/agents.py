"""
Feature 19 — BD Agent API Router.

Provides REST endpoints for running BD agent workflows, individual agents,
and parallel agent execution.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger("BDKnowledgeAPI")

router = APIRouter(prefix="/bd-agents", tags=["BD Agents"])


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class WorkflowRunRequest(BaseModel):
    """Run a named multi-agent workflow."""
    workflow: str = Field(..., description="Workflow name (full_analysis, call_prep, opportunity_capture, competitive_intel)")
    context: Dict = Field(default_factory=dict, description="Context data for the workflow")


class SingleAgentRequest(BaseModel):
    """Run a single agent."""
    context: Dict = Field(default_factory=dict, description="Context data for the agent")


class ParallelAgentRequest(BaseModel):
    """Run multiple agents in parallel."""
    agents: List[str] = Field(..., description="Agent names to run in parallel")
    context: Dict = Field(default_factory=dict, description="Context data for all agents")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/run")
async def run_workflow(body: WorkflowRunRequest):
    """Run a named multi-agent BD workflow."""
    import asyncio
    from Engine8_Knowledge.agents.orchestrator import get_bd_orchestrator

    orchestrator = get_bd_orchestrator()
    result = await asyncio.to_thread(orchestrator.run_workflow, body.workflow, body.context)

    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("error", "Workflow failed"))

    return result


@router.post("/run/{agent_name}")
async def run_single_agent(agent_name: str, body: SingleAgentRequest):
    """Run a single BD agent by name."""
    import asyncio
    from Engine8_Knowledge.agents.orchestrator import get_bd_orchestrator

    orchestrator = get_bd_orchestrator()

    if agent_name not in orchestrator.agents:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown agent: {agent_name}. Available: {list(orchestrator.agents.keys())}",
        )

    result = await asyncio.to_thread(orchestrator.run_single_agent, agent_name, body.context)
    return result


@router.get("/status")
async def get_agent_status():
    """List all agents and their status."""
    from Engine8_Knowledge.agents.orchestrator import get_bd_orchestrator

    orchestrator = get_bd_orchestrator()
    return orchestrator.get_agent_status()


@router.get("/workflows")
async def list_workflows():
    """List available workflows with descriptions."""
    from Engine8_Knowledge.agents.orchestrator import get_bd_orchestrator

    orchestrator = get_bd_orchestrator()
    return orchestrator.get_workflows()


@router.post("/parallel")
async def run_parallel_agents(body: ParallelAgentRequest):
    """Run multiple agents in parallel."""
    import asyncio
    from Engine8_Knowledge.agents.orchestrator import get_bd_orchestrator

    orchestrator = get_bd_orchestrator()
    result = await asyncio.to_thread(orchestrator.run_parallel, body.agents, body.context)
    return result
