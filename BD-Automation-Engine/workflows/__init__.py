"""
LangGraph Workflow Orchestration Engine for BD Automation.

Provides stateful, graph-based workflow execution as a modern replacement
for sequential pipeline orchestration.  Each workflow is a LangGraph
StateGraph with typed state, structured logging, error quarantine, and
optional human-in-the-loop gates.

Workflows:
    master_pipeline   — Full 7-node BD pipeline (scrape → index)
    morning_briefing  — Daily intelligence briefing (3 nodes)
    contact_enrichment — Stale-contact refresh (4 nodes)
    scheduler         — APScheduler integration for cron-style execution
"""

from workflows.state import PipelineState, WorkflowConfig

__all__ = [
    "PipelineState",
    "WorkflowConfig",
]
