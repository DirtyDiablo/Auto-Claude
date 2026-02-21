"""
Feature 19 — BD Agent Orchestrator.

Coordinates multi-agent BD workflows with sequential and parallel execution.
Uses concurrent.futures.ThreadPoolExecutor for parallel agent runs.
"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

import structlog

from .bd_workflow_agents import (
    ALL_AGENTS,
    BDAgentBase,
    ResearcherAgent,
    AnalystAgent,
    CompetitorAgent,
    PlaybookAgent,
    CallPrepAgent,
    OutreachAgent,
    WinStrategyAgent,
    AccountMapperAgent,
)

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Workflow definitions
# ---------------------------------------------------------------------------

WORKFLOW_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "full_analysis": {
        "description": "Full BD analysis pipeline: researcher → analyst → competitor → win_strategy",
        "steps": [
            {"type": "sequential", "agents": ["researcher"]},
            {"type": "sequential", "agents": ["analyst"]},
            {"type": "sequential", "agents": ["competitor"]},
            {"type": "sequential", "agents": ["win_strategy"]},
        ],
    },
    "call_prep": {
        "description": "Call preparation workflow: researcher + account_mapper (parallel) → call_prep",
        "steps": [
            {"type": "parallel", "agents": ["researcher", "account_mapper"]},
            {"type": "sequential", "agents": ["call_prep"]},
        ],
    },
    "opportunity_capture": {
        "description": "Opportunity capture pipeline: researcher → analyst → playbook → outreach",
        "steps": [
            {"type": "sequential", "agents": ["researcher"]},
            {"type": "sequential", "agents": ["analyst"]},
            {"type": "sequential", "agents": ["playbook"]},
            {"type": "sequential", "agents": ["outreach"]},
        ],
    },
    "competitive_intel": {
        "description": "Competitive intelligence: competitor + researcher (parallel) → analyst",
        "steps": [
            {"type": "parallel", "agents": ["competitor", "researcher"]},
            {"type": "sequential", "agents": ["analyst"]},
        ],
    },
}


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


class BDAgentOrchestrator:
    """Coordinates multi-agent BD workflows."""

    def __init__(self, max_workers: int = 4):
        self.agents: Dict[str, BDAgentBase] = {}
        self._max_workers = max_workers
        self._register_agents()

    def _register_agents(self) -> None:
        """Instantiate all registered agent classes."""
        for name, cls in ALL_AGENTS.items():
            try:
                self.agents[name] = cls()
                logger.debug("agent_registered", agent=name)
            except Exception as exc:
                logger.error("agent_registration_failed", agent=name, error=str(exc))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_workflow(self, workflow_name: str, context: dict) -> dict:
        """Run a named multi-agent workflow."""
        if workflow_name not in WORKFLOW_DEFINITIONS:
            return {
                "workflow": workflow_name,
                "status": "error",
                "error": f"Unknown workflow: {workflow_name}. Available: {list(WORKFLOW_DEFINITIONS.keys())}",
                "results": {},
            }

        defn = WORKFLOW_DEFINITIONS[workflow_name]
        logger.info("workflow_start", workflow=workflow_name, steps=len(defn["steps"]))

        start = time.monotonic()
        accumulated_results: Dict[str, dict] = {}
        ctx = dict(context)  # shallow copy

        for step_idx, step in enumerate(defn["steps"]):
            step_type = step["type"]
            agent_names = step["agents"]

            # Pass prior results into context
            if accumulated_results:
                ctx["prior_results"] = dict(accumulated_results)

            if step_type == "parallel":
                step_results = self.run_parallel(agent_names, ctx)
                for name, result in step_results.get("results", {}).items():
                    accumulated_results[name] = result
            else:
                for agent_name in agent_names:
                    result = self.run_single_agent(agent_name, ctx)
                    accumulated_results[agent_name] = result
                    # Update context for next agent in sequence
                    ctx["prior_results"] = dict(accumulated_results)

        elapsed = time.monotonic() - start
        logger.info("workflow_complete", workflow=workflow_name, duration_s=round(elapsed, 3))

        return {
            "workflow": workflow_name,
            "status": "success",
            "results": accumulated_results,
            "duration_seconds": round(elapsed, 3),
            "agents_used": list(accumulated_results.keys()),
        }

    def run_single_agent(self, agent_name: str, context: dict) -> dict:
        """Run a single agent."""
        agent = self.agents.get(agent_name)
        if agent is None:
            logger.warning("agent_not_found", agent=agent_name)
            return {
                "agent_name": agent_name,
                "status": "error",
                "error": f"Unknown agent: {agent_name}. Available: {list(self.agents.keys())}",
                "findings": [],
                "recommendations": [],
                "confidence": 0.0,
            }

        try:
            logger.info("agent_run_start", agent=agent_name)
            start = time.monotonic()
            result = agent.execute(context)
            elapsed = time.monotonic() - start
            result["duration_seconds"] = round(elapsed, 3)
            logger.info("agent_run_complete", agent=agent_name, duration_s=result["duration_seconds"])
            return result
        except Exception as exc:
            logger.error("agent_run_failed", agent=agent_name, error=str(exc))
            return {
                "agent_name": agent_name,
                "status": "error",
                "error": str(exc),
                "findings": [],
                "recommendations": [],
                "confidence": 0.0,
            }

    def run_parallel(self, agent_names: list, context: dict) -> dict:
        """Run multiple agents in parallel and merge results."""
        results: Dict[str, dict] = {}
        errors: List[str] = []

        valid_names = [n for n in agent_names if n in self.agents]
        invalid_names = [n for n in agent_names if n not in self.agents]
        for inv in invalid_names:
            errors.append(f"Unknown agent: {inv}")
            results[inv] = {
                "agent_name": inv,
                "status": "error",
                "error": f"Unknown agent: {inv}",
                "findings": [],
                "recommendations": [],
                "confidence": 0.0,
            }

        if not valid_names:
            return {"status": "error", "results": results, "errors": errors}

        start = time.monotonic()
        with ThreadPoolExecutor(max_workers=min(self._max_workers, len(valid_names))) as executor:
            future_to_name = {
                executor.submit(self.agents[name].execute, context): name
                for name in valid_names
            }
            for future in as_completed(future_to_name):
                name = future_to_name[future]
                try:
                    results[name] = future.result()
                except Exception as exc:
                    logger.error("parallel_agent_failed", agent=name, error=str(exc))
                    errors.append(f"{name}: {exc}")
                    results[name] = {
                        "agent_name": name,
                        "status": "error",
                        "error": str(exc),
                        "findings": [],
                        "recommendations": [],
                        "confidence": 0.0,
                    }

        elapsed = time.monotonic() - start
        return {
            "status": "success" if not errors else "partial",
            "results": results,
            "duration_seconds": round(elapsed, 3),
            "errors": errors,
        }

    def get_agent_status(self) -> dict:
        """Get status of all registered agents."""
        agents_info = []
        for name, agent in self.agents.items():
            agents_info.append({
                "name": name,
                "role": agent.role,
                "goal": agent.goal,
                "status": "ready",
            })
        return {
            "total_agents": len(self.agents),
            "agents": agents_info,
        }

    def get_workflows(self) -> dict:
        """List available workflows with descriptions."""
        workflows = []
        for name, defn in WORKFLOW_DEFINITIONS.items():
            agents_involved = []
            for step in defn["steps"]:
                agents_involved.extend(step["agents"])
            workflows.append({
                "name": name,
                "description": defn["description"],
                "agents": list(dict.fromkeys(agents_involved)),  # unique, ordered
                "steps": len(defn["steps"]),
            })
        return {
            "total_workflows": len(workflows),
            "workflows": workflows,
        }


# ---------------------------------------------------------------------------
# Singleton accessor
# ---------------------------------------------------------------------------

_orchestrator_instance: Optional[BDAgentOrchestrator] = None


def get_bd_orchestrator() -> BDAgentOrchestrator:
    """Get or create the singleton orchestrator instance."""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = BDAgentOrchestrator()
    return _orchestrator_instance
