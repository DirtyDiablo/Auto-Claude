"""Phase 45A — MCP Orchestrator.

Chains multiple MCP tool calls into intelligent workflows with
DAG-based execution, parallel processing, cost tracking, and
error handling with fallbacks.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from src.mcp.tool_registry import MCPToolRegistry, get_tool_registry


# =========================================
# ENUMS & DATA CLASSES
# =========================================

class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class PlanStatus(str, Enum):
    DRAFT = "draft"
    READY = "ready"
    EXECUTING = "executing"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


@dataclass
class MCPExecutionStep:
    step_id: str = ""
    server_id: str = ""
    tool_name: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    fallback_server: str = ""
    fallback_tool: str = ""
    status: str = "pending"
    result: Optional[Dict[str, Any]] = None
    error: str = ""
    latency_ms: int = 0
    cost: float = 0.0

    def __post_init__(self):
        if not self.step_id:
            raw = f"{self.server_id}:{self.tool_name}:{datetime.utcnow().isoformat()}"
            self.step_id = f"step_{hashlib.md5(raw.encode()).hexdigest()[:8]}"


@dataclass
class MCPExecutionPlan:
    plan_id: str = ""
    intent: str = ""
    steps: List[MCPExecutionStep] = field(default_factory=list)
    status: str = "draft"
    created_at: str = ""
    estimated_cost: float = 0.0
    estimated_time_ms: int = 0

    def __post_init__(self):
        if not self.plan_id:
            raw = f"plan:{self.intent}:{datetime.utcnow().isoformat()}"
            self.plan_id = f"plan_{hashlib.md5(raw.encode()).hexdigest()[:10]}"
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()


@dataclass
class MCPExecutionResult:
    plan_id: str = ""
    status: str = "completed"
    steps_completed: int = 0
    steps_failed: int = 0
    steps_skipped: int = 0
    total_cost: float = 0.0
    total_latency_ms: int = 0
    results: Dict[str, Any] = field(default_factory=dict)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    completed_at: str = ""

    def __post_init__(self):
        if not self.completed_at:
            self.completed_at = datetime.utcnow().isoformat()


# =========================================
# PLAN TEMPLATES
# =========================================

_PLAN_TEMPLATES: Dict[str, List[Dict[str, Any]]] = {
    "outreach_prep": [
        {"server_id": "mcp_notion", "tool_name": "query_database",
         "parameters": {"filter": "program_contacts"}, "depends_on": []},
        {"server_id": "mcp_day_ai", "tool_name": "enrich_contact",
         "parameters": {"enrich": True}, "depends_on": ["step_0"]},
        {"server_id": "mcp_google_maps", "tool_name": "distance_matrix",
         "parameters": {"calculate": True}, "depends_on": ["step_0"]},
        {"server_id": "mcp_google_workspace", "tool_name": "draft_email",
         "parameters": {"draft": True}, "depends_on": ["step_1"]},
        {"server_id": "mcp_slack", "tool_name": "send_message",
         "parameters": {"channel": "#bd-team", "notify": True}, "depends_on": ["step_3"]},
    ],
    "competitor_scan": [
        {"server_id": "mcp_notion", "tool_name": "query_database",
         "parameters": {"filter": "competitor_jobs"}, "depends_on": []},
        {"server_id": "mcp_day_ai", "tool_name": "company_intel",
         "parameters": {"deep_scan": True}, "depends_on": ["step_0"]},
        {"server_id": "mcp_slack", "tool_name": "send_message",
         "parameters": {"channel": "#competitive-intel"}, "depends_on": ["step_1"]},
    ],
    "meeting_prep": [
        {"server_id": "mcp_notion", "tool_name": "query_database",
         "parameters": {"filter": "contact_details"}, "depends_on": []},
        {"server_id": "mcp_day_ai", "tool_name": "enrich_contact",
         "parameters": {"enrich": True}, "depends_on": ["step_0"]},
        {"server_id": "mcp_google_workspace", "tool_name": "list_events",
         "parameters": {"days": 7}, "depends_on": []},
        {"server_id": "mcp_memory", "tool_name": "recall_memory",
         "parameters": {"query": "meeting_history"}, "depends_on": []},
    ],
}


# =========================================
# MCP ORCHESTRATOR
# =========================================

class MCPOrchestrator:
    """Orchestrates complex multi-tool MCP operations."""

    def __init__(self, registry: Optional[MCPToolRegistry] = None) -> None:
        self._registry = registry or get_tool_registry()
        self._executions: List[MCPExecutionResult] = []
        self._plans: Dict[str, MCPExecutionPlan] = {}

    # --------------------------------------------------
    # PLAN GENERATION
    # --------------------------------------------------

    def plan_from_intent(self, intent: str, context: Optional[Dict] = None) -> MCPExecutionPlan:
        """Decompose natural language intent into an MCP execution plan."""
        context = context or {}
        intent_lower = intent.lower()

        # Match intent to plan template
        template_key = ""
        if any(kw in intent_lower for kw in ["outreach", "contact", "reach out", "engage"]):
            template_key = "outreach_prep"
        elif any(kw in intent_lower for kw in ["competitor", "competitive", "market scan"]):
            template_key = "competitor_scan"
        elif any(kw in intent_lower for kw in ["meeting", "call prep", "prepare for call"]):
            template_key = "meeting_prep"

        steps: List[MCPExecutionStep] = []
        estimated_cost = 0.0
        estimated_time = 0

        if template_key and template_key in _PLAN_TEMPLATES:
            template_steps = _PLAN_TEMPLATES[template_key]
            for i, ts in enumerate(template_steps):
                step_id = f"step_{i}"
                # Resolve depends_on to actual step IDs
                deps = [d for d in ts.get("depends_on", []) if d.startswith("step_")]
                # Look up tool for cost estimation
                server = self._registry.get_server(ts["server_id"])
                tool_cost = 0.0
                tool_latency = 200
                if server:
                    for tool in server.tools:
                        if tool.name == ts["tool_name"]:
                            tool_cost = tool.cost_per_call
                            tool_latency = tool.estimated_latency_ms
                            break

                step = MCPExecutionStep(
                    step_id=step_id,
                    server_id=ts["server_id"],
                    tool_name=ts["tool_name"],
                    parameters={**ts.get("parameters", {}), **context},
                    depends_on=deps,
                    cost=tool_cost,
                )
                steps.append(step)
                estimated_cost += tool_cost
                estimated_time += tool_latency
        else:
            # Single-step fallback: route the intent
            routing = self._registry.route_request(intent, context)
            if routing.selected_server:
                step = MCPExecutionStep(
                    server_id=routing.selected_server,
                    tool_name=routing.selected_tool,
                    parameters=context,
                )
                steps.append(step)
                estimated_time = 500

        plan = MCPExecutionPlan(
            intent=intent,
            steps=steps,
            status=PlanStatus.READY.value,
            estimated_cost=round(estimated_cost, 4),
            estimated_time_ms=estimated_time,
        )
        self._plans[plan.plan_id] = plan
        return plan

    # --------------------------------------------------
    # EXECUTION
    # --------------------------------------------------

    def execute_plan(self, plan: MCPExecutionPlan) -> MCPExecutionResult:
        """Execute a multi-step MCP plan."""
        plan.status = PlanStatus.EXECUTING.value

        completed_steps: Dict[str, Dict[str, Any]] = {}
        total_cost = 0.0
        total_latency = 0
        errors: List[Dict[str, Any]] = []

        # Topological execution: process steps in dependency order
        remaining = list(plan.steps)
        max_iterations = len(remaining) * 2  # safety limit
        iteration = 0

        while remaining and iteration < max_iterations:
            iteration += 1
            ready = [
                s for s in remaining
                if all(dep in completed_steps for dep in s.depends_on)
            ]
            if not ready:
                # Deadlock or unresolvable deps — skip remaining
                for s in remaining:
                    s.status = StepStatus.SKIPPED.value
                break

            for step in ready:
                result = self._execute_step(step, completed_steps)
                if step.status == StepStatus.COMPLETED.value:
                    completed_steps[step.step_id] = result
                    total_cost += step.cost
                    total_latency += step.latency_ms
                elif step.status == StepStatus.FAILED.value:
                    # Try fallback
                    if step.fallback_server:
                        step.server_id = step.fallback_server
                        step.tool_name = step.fallback_tool or step.tool_name
                        fallback_result = self._execute_step(step, completed_steps)
                        if step.status == StepStatus.COMPLETED.value:
                            completed_steps[step.step_id] = fallback_result
                        else:
                            errors.append({
                                "step_id": step.step_id,
                                "error": step.error,
                            })
                    else:
                        errors.append({
                            "step_id": step.step_id,
                            "error": step.error,
                        })
                remaining.remove(step) if step in remaining else None

        steps_completed = sum(1 for s in plan.steps if s.status == StepStatus.COMPLETED.value)
        steps_failed = sum(1 for s in plan.steps if s.status == StepStatus.FAILED.value)
        steps_skipped = sum(1 for s in plan.steps if s.status == StepStatus.SKIPPED.value)

        if steps_failed == 0 and steps_skipped == 0:
            plan.status = PlanStatus.COMPLETED.value
            result_status = "completed"
        elif steps_completed > 0:
            plan.status = PlanStatus.PARTIAL.value
            result_status = "partial"
        else:
            plan.status = PlanStatus.FAILED.value
            result_status = "failed"

        execution_result = MCPExecutionResult(
            plan_id=plan.plan_id,
            status=result_status,
            steps_completed=steps_completed,
            steps_failed=steps_failed,
            steps_skipped=steps_skipped,
            total_cost=round(total_cost, 4),
            total_latency_ms=total_latency,
            results=completed_steps,
            errors=errors,
        )
        self._executions.append(execution_result)
        return execution_result

    def _execute_step(self, step: MCPExecutionStep,
                      prior_results: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single step. Simulates actual MCP tool call."""
        step.status = StepStatus.RUNNING.value

        # Verify server exists and is healthy
        server = self._registry.get_server(step.server_id)
        if not server:
            step.status = StepStatus.FAILED.value
            step.error = f"Server {step.server_id} not found"
            return {}

        if server.health == "unhealthy":
            step.status = StepStatus.FAILED.value
            step.error = f"Server {step.server_id} is unhealthy"
            return {}

        # Simulate execution
        step.latency_ms = 100
        step.status = StepStatus.COMPLETED.value

        # Build simulated result
        result = {
            "step_id": step.step_id,
            "server_id": step.server_id,
            "tool_name": step.tool_name,
            "status": "success",
            "data": {"message": f"Executed {step.tool_name} on {step.server_id}"},
        }

        # Record usage
        self._registry.record_usage(step.server_id, step.tool_name, success=True, latency_ms=100)

        return result

    # --------------------------------------------------
    # QUERIES
    # --------------------------------------------------

    def get_plan(self, plan_id: str) -> Optional[MCPExecutionPlan]:
        return self._plans.get(plan_id)

    def list_plans(self) -> List[MCPExecutionPlan]:
        return list(self._plans.values())

    def get_executions(self) -> List[MCPExecutionResult]:
        return list(self._executions)

    def get_stats(self) -> Dict[str, Any]:
        total_exec = len(self._executions)
        completed = sum(1 for e in self._executions if e.status == "completed")
        total_cost = sum(e.total_cost for e in self._executions)

        return {
            "total_plans": len(self._plans),
            "total_executions": total_exec,
            "completed": completed,
            "partial": sum(1 for e in self._executions if e.status == "partial"),
            "failed": sum(1 for e in self._executions if e.status == "failed"),
            "total_cost": round(total_cost, 4),
            "avg_steps_per_plan": round(
                sum(len(p.steps) for p in self._plans.values()) / max(len(self._plans), 1), 1
            ),
        }


# =========================================
# SINGLETON
# =========================================

_instance: Optional[MCPOrchestrator] = None


def get_orchestrator() -> MCPOrchestrator:
    global _instance
    if _instance is None:
        _instance = MCPOrchestrator()
    return _instance
