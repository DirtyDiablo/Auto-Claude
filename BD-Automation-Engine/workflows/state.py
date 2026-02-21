"""
Shared state definitions for LangGraph workflows.

PipelineState is the canonical TypedDict passed through every node.
WorkflowConfig holds runtime knobs (batch size, parallelism, etc.).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

try:
    from typing import TypedDict
except ImportError:
    from typing_extensions import TypedDict


class StageEntry(TypedDict, total=False):
    """Single entry in the stage_history list."""
    name: str
    status: str          # "passed", "failed", "skipped"
    started_at: str      # ISO-8601
    ended_at: str        # ISO-8601
    duration_seconds: float
    record_count: int
    error: Optional[str]


class PipelineState(TypedDict, total=False):
    """Shared state flowing through every workflow node."""
    jobs: List[Dict[str, Any]]
    contacts: List[Dict[str, Any]]
    programs: List[Dict[str, Any]]
    enriched_jobs: List[Dict[str, Any]]
    scored_jobs: List[Dict[str, Any]]
    qa_results: Dict[str, Any]
    errors: List[str]
    metadata: Dict[str, Any]
    stage_history: List[StageEntry]


def make_initial_state(**overrides: Any) -> PipelineState:
    """Return a fresh PipelineState with sensible defaults."""
    state: PipelineState = {
        "jobs": [],
        "contacts": [],
        "programs": [],
        "enriched_jobs": [],
        "scored_jobs": [],
        "qa_results": {},
        "errors": [],
        "metadata": {},
        "stage_history": [],
    }
    state.update(overrides)  # type: ignore[typeddict-item]
    return state


@dataclass
class WorkflowConfig:
    """Runtime configuration for workflow execution."""
    batch_size: int = 50
    parallel: bool = False
    checkpoint_dir: str = "outputs/workflow_checkpoints"
    human_approval_required: bool = True
    input_path: Optional[str] = None
    test_mode: bool = False
