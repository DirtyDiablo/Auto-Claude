"""
Phase 23A — Time-Travel Debugger

Inspect, replay, and fork workflow executions from any checkpoint.
Provides execution timelines, state diffs, and what-if analysis.
"""

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import structlog

from Engine8_Knowledge.workflows.checkpoint_store import CheckpointStore, get_checkpoint_store

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class NodeVisit:
    step: int
    node_name: str
    started_at: str
    duration_seconds: float
    state_keys_modified: List[str]
    input_summary: str
    output_summary: str


@dataclass
class ErrorEvent:
    step: int
    node_name: str
    error: str
    traceback: str = ""
    timestamp: str = ""


@dataclass
class InterruptEvent:
    step: int
    node_name: str
    description: str
    timestamp: str = ""
    resolved: bool = False
    resolution: str = ""


@dataclass
class ExecutionTimeline:
    thread_id: str
    workflow_name: str
    started_at: str
    completed_at: Optional[str]
    status: str
    total_steps: int
    nodes_visited: List[NodeVisit]
    errors: List[ErrorEvent]
    interrupts: List[InterruptEvent]
    total_duration_seconds: float


@dataclass
class StateDiff:
    step_a: int
    step_b: int
    added_keys: List[str]
    removed_keys: List[str]
    modified_keys: Dict[str, Tuple[Any, Any]]


@dataclass
class ComparisonReport:
    thread_id_a: str
    thread_id_b: str
    workflow_name: str
    timeline_a: ExecutionTimeline
    timeline_b: ExecutionTimeline
    divergence_point: Optional[int]
    shared_nodes: List[str]
    different_nodes: List[str]
    state_diffs: List[StateDiff]


# ---------------------------------------------------------------------------
# TimeTravelDebugger
# ---------------------------------------------------------------------------

class TimeTravelDebugger:
    """Inspect, replay, and fork workflow executions from any checkpoint."""

    def __init__(self, checkpoint_store: Optional[CheckpointStore] = None):
        self.checkpoint_store = checkpoint_store or get_checkpoint_store()
        logger.info("time_travel.init")

    async def get_execution_timeline(self, thread_id: str) -> ExecutionTimeline:
        """Return full execution history of a workflow run."""
        threads = await self.checkpoint_store.list_threads()
        thread = next((t for t in threads if t.thread_id == thread_id), None)

        if not thread:
            raise ValueError(f"Thread {thread_id} not found")

        snapshots = await self.checkpoint_store.get_thread_history(thread_id)

        # Build node visits from snapshots
        nodes_visited = []
        errors = []
        interrupts = []
        prev_state_keys = set()

        for i, snap in enumerate(snapshots):
            # Determine duration
            if i > 0:
                try:
                    t0 = datetime.fromisoformat(snapshots[i - 1].timestamp)
                    t1 = datetime.fromisoformat(snap.timestamp)
                    duration = (t1 - t0).total_seconds()
                except (ValueError, TypeError):
                    duration = 0.0
            else:
                duration = 0.0

            current_keys = set(snap.state.keys())
            modified = list(current_keys - prev_state_keys)
            prev_state_keys = current_keys

            # Truncate state summaries
            input_summary = self._summarize_state(
                snapshots[i - 1].state if i > 0 else {}, max_len=200
            )
            output_summary = self._summarize_state(snap.state, max_len=200)

            nodes_visited.append(NodeVisit(
                step=snap.step,
                node_name=snap.node_name,
                started_at=snap.timestamp,
                duration_seconds=round(duration, 3),
                state_keys_modified=modified,
                input_summary=input_summary,
                output_summary=output_summary,
            ))

            # Check for errors in state
            for err in snap.state.get("errors", []):
                if isinstance(err, dict) and err.get("node") == snap.node_name:
                    errors.append(ErrorEvent(
                        step=snap.step,
                        node_name=snap.node_name,
                        error=err.get("error", ""),
                        traceback=err.get("traceback", ""),
                        timestamp=snap.timestamp,
                    ))

            # Check for interrupts
            if snap.metadata.get("interrupted"):
                interrupts.append(InterruptEvent(
                    step=snap.step,
                    node_name=snap.node_name,
                    description=f"Workflow interrupted at {snap.node_name}",
                    timestamp=snap.timestamp,
                    resolved=thread.status != "interrupted",
                ))

        # Calculate total duration
        if snapshots:
            try:
                t0 = datetime.fromisoformat(snapshots[0].timestamp)
                t1 = datetime.fromisoformat(snapshots[-1].timestamp)
                total_duration = (t1 - t0).total_seconds()
            except (ValueError, TypeError):
                total_duration = 0.0
        else:
            total_duration = 0.0

        return ExecutionTimeline(
            thread_id=thread_id,
            workflow_name=thread.workflow_name,
            started_at=thread.created_at,
            completed_at=thread.updated_at if thread.status in ("completed", "failed") else None,
            status=thread.status,
            total_steps=thread.step_count,
            nodes_visited=nodes_visited,
            errors=errors,
            interrupts=interrupts,
            total_duration_seconds=round(total_duration, 3),
        )

    async def inspect_state_at(self, thread_id: str, step: int) -> dict:
        """Get the exact state at any checkpoint step."""
        snap = await self.checkpoint_store.get_checkpoint_at(thread_id, step)
        if not snap:
            raise ValueError(f"No checkpoint at step {step} for thread {thread_id}")

        return {
            "thread_id": thread_id,
            "step": snap.step,
            "node_name": snap.node_name,
            "timestamp": snap.timestamp,
            "state": snap.state,
            "metadata": snap.metadata,
        }

    async def diff_states(self, thread_id: str, step_a: int, step_b: int) -> StateDiff:
        """Show what changed between two checkpoints."""
        snap_a = await self.checkpoint_store.get_checkpoint_at(thread_id, step_a)
        snap_b = await self.checkpoint_store.get_checkpoint_at(thread_id, step_b)

        if not snap_a or not snap_b:
            raise ValueError(f"Could not find checkpoints at steps {step_a} and/or {step_b}")

        state_a = snap_a.state
        state_b = snap_b.state

        keys_a = set(state_a.keys())
        keys_b = set(state_b.keys())

        added = list(keys_b - keys_a)
        removed = list(keys_a - keys_b)
        modified = {}

        for key in keys_a & keys_b:
            val_a = state_a[key]
            val_b = state_b[key]
            if val_a != val_b:
                # Summarize for large values
                modified[key] = (
                    self._summarize_value(val_a),
                    self._summarize_value(val_b),
                )

        return StateDiff(
            step_a=step_a,
            step_b=step_b,
            added_keys=added,
            removed_keys=removed,
            modified_keys=modified,
        )

    async def replay_from(self, thread_id: str, step: int,
                          modified_state: Optional[dict] = None) -> str:
        """Fork a new execution from a historical checkpoint.
        Returns new thread_id for the forked execution."""
        snap = await self.checkpoint_store.get_checkpoint_at(thread_id, step)
        if not snap:
            raise ValueError(f"No checkpoint at step {step} for thread {thread_id}")

        # Create new thread
        new_tid = f"fork_{uuid.uuid4().hex[:8]}"

        # Get original workflow name
        threads = await self.checkpoint_store.list_threads()
        thread = next((t for t in threads if t.thread_id == thread_id), None)
        workflow_name = thread.workflow_name if thread else "unknown"

        await self.checkpoint_store.create_thread(
            workflow_name=workflow_name,
            thread_id=new_tid,
            metadata={
                "forked_from": thread_id,
                "forked_at_step": step,
                "has_modifications": modified_state is not None,
            }
        )

        # Copy state and apply modifications
        forked_state = dict(snap.state)
        if modified_state:
            forked_state.update(modified_state)

        # Save initial snapshot
        await self.checkpoint_store.save_snapshot(
            thread_id=new_tid, step=0,
            node_name=f"forked_from_{snap.node_name}",
            state=forked_state,
            metadata={"forked_from": thread_id, "original_step": step}
        )

        logger.info("time_travel.replay_forked",
                     original=thread_id, step=step,
                     new_thread=new_tid, modified=modified_state is not None)
        return new_tid

    async def compare_executions(self, thread_id_a: str,
                                  thread_id_b: str) -> ComparisonReport:
        """Compare two executions of the same workflow."""
        timeline_a = await self.get_execution_timeline(thread_id_a)
        timeline_b = await self.get_execution_timeline(thread_id_b)

        # Find shared and different nodes
        nodes_a = [n.node_name for n in timeline_a.nodes_visited]
        nodes_b = [n.node_name for n in timeline_b.nodes_visited]

        shared = [n for n in nodes_a if n in nodes_b]
        different = list(set(nodes_a) ^ set(nodes_b))

        # Find divergence point
        divergence = None
        min_len = min(len(nodes_a), len(nodes_b))
        for i in range(min_len):
            if nodes_a[i] != nodes_b[i]:
                divergence = i
                break

        # Compute state diffs at shared steps
        state_diffs = []
        snapshots_a = await self.checkpoint_store.get_thread_history(thread_id_a)
        snapshots_b = await self.checkpoint_store.get_thread_history(thread_id_b)

        for i in range(min(len(snapshots_a), len(snapshots_b))):
            sa = snapshots_a[i].state
            sb = snapshots_b[i].state

            keys_a_set = set(sa.keys())
            keys_b_set = set(sb.keys())
            modified = {}
            for key in keys_a_set & keys_b_set:
                if sa[key] != sb[key]:
                    modified[key] = (
                        self._summarize_value(sa[key]),
                        self._summarize_value(sb[key]),
                    )

            if modified or (keys_a_set != keys_b_set):
                state_diffs.append(StateDiff(
                    step_a=snapshots_a[i].step,
                    step_b=snapshots_b[i].step,
                    added_keys=list(keys_b_set - keys_a_set),
                    removed_keys=list(keys_a_set - keys_b_set),
                    modified_keys=modified,
                ))

        return ComparisonReport(
            thread_id_a=thread_id_a,
            thread_id_b=thread_id_b,
            workflow_name=timeline_a.workflow_name,
            timeline_a=timeline_a,
            timeline_b=timeline_b,
            divergence_point=divergence,
            shared_nodes=shared,
            different_nodes=different,
            state_diffs=state_diffs,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _summarize_state(self, state: dict, max_len: int = 200) -> str:
        """Create a truncated summary of state."""
        if not state:
            return "{}"
        keys = list(state.keys())
        summary = f"{{{', '.join(keys[:10])}"
        if len(keys) > 10:
            summary += f", ... +{len(keys) - 10} more"
        summary += "}"
        return summary[:max_len]

    def _summarize_value(self, value: Any, max_len: int = 100) -> Any:
        """Summarize a value for display."""
        if isinstance(value, list):
            return f"[{len(value)} items]" if len(value) > 5 else value
        if isinstance(value, dict):
            return f"{{{len(value)} keys}}" if len(value) > 5 else value
        if isinstance(value, str) and len(value) > max_len:
            return value[:max_len] + "..."
        return value


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_debugger: Optional[TimeTravelDebugger] = None


def get_time_travel_debugger() -> TimeTravelDebugger:
    """Get or create the singleton TimeTravelDebugger."""
    global _debugger
    if _debugger is None:
        _debugger = TimeTravelDebugger()
    return _debugger
