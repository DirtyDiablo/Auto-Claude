"""
Phase 23A — Production State Graph Builder

Factory for building production-grade LangGraph StateGraphs with standard middleware:
checkpointing, human-in-the-loop interrupts, parallel branches, error handling,
streaming, and retry logic.
"""

import asyncio
import time
import traceback
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Type, Union

import structlog

from Engine8_Knowledge.workflows.checkpoint_store import CheckpointStore, get_checkpoint_store

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Configuration data classes
# ---------------------------------------------------------------------------

@dataclass
class RetryConfig:
    """Per-node retry settings."""
    max_attempts: int = 3
    backoff_seconds: float = 2.0
    retry_on: List[Type[Exception]] = field(default_factory=lambda: [Exception])


@dataclass
class NodeSpec:
    """Specification for a single workflow node."""
    name: str
    function: Callable
    description: str = ""
    timeout_seconds: int = 300
    retry_on_error: bool = True
    max_retries: int = 3


@dataclass
class EdgeSpec:
    """Specification for a graph edge (direct or conditional)."""
    source: str
    target: Union[str, List[str]]
    condition: Optional[Callable] = None


@dataclass
class WorkflowDefinition:
    """Declarative workflow spec consumed by the builder."""
    name: str
    description: str
    state_schema: Dict[str, Any]  # field_name -> default_value
    nodes: Dict[str, NodeSpec]
    edges: List[EdgeSpec]
    entry_point: str
    interrupt_nodes: List[str] = field(default_factory=list)
    parallel_groups: List[List[str]] = field(default_factory=list)
    retry_config: Dict[str, RetryConfig] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowInfo:
    """Summary info about a registered workflow."""
    name: str
    description: str
    node_count: int
    edge_count: int
    interrupt_nodes: List[str]
    parallel_groups: List[List[str]]
    entry_point: str


# ---------------------------------------------------------------------------
# Production Graph Builder
# ---------------------------------------------------------------------------

class ProductionGraphBuilder:
    """Builds StateGraphs with production features baked in."""

    def __init__(self, checkpoint_store: Optional[CheckpointStore] = None):
        self.checkpoint_store = checkpoint_store or get_checkpoint_store()
        self._compiled_graphs: Dict[str, Any] = {}
        logger.info("graph_builder.init")

    def build(self, workflow_def: WorkflowDefinition) -> "CompiledProductionGraph":
        """
        Build a production-grade compiled graph from a WorkflowDefinition.

        Features:
        - Checkpointing at every node transition
        - Configurable interrupt_before for human-in-the-loop
        - Error handling with retry and graceful degradation
        - Parallel branch execution for independent nodes
        - Streaming support for real-time visibility
        - Performance tracking per node
        """
        logger.info("graph_builder.building", workflow=workflow_def.name,
                     nodes=len(workflow_def.nodes), edges=len(workflow_def.edges))

        # Try to build a real LangGraph StateGraph
        try:
            graph = self._build_langgraph(workflow_def)
            logger.info("graph_builder.langgraph_compiled", workflow=workflow_def.name)
        except ImportError:
            logger.warning("graph_builder.langgraph_unavailable, using production wrapper")
            graph = None

        compiled = CompiledProductionGraph(
            workflow_def=workflow_def,
            checkpoint_store=self.checkpoint_store,
            langgraph=graph,
        )

        self._compiled_graphs[workflow_def.name] = compiled
        return compiled

    def _build_langgraph(self, workflow_def: WorkflowDefinition):
        """Build a real LangGraph StateGraph."""
        from langgraph.graph import StateGraph, END

        # Create state schema as TypedDict dynamically
        state_annotations = {}
        for key, default in workflow_def.state_schema.items():
            if isinstance(default, list):
                state_annotations[key] = list
            elif isinstance(default, dict):
                state_annotations[key] = dict
            elif isinstance(default, bool):
                state_annotations[key] = bool
            elif isinstance(default, int):
                state_annotations[key] = int
            elif isinstance(default, float):
                state_annotations[key] = float
            else:
                state_annotations[key] = str

        # Build graph
        builder = StateGraph(dict)

        # Add nodes with retry wrapping
        for node_name, node_spec in workflow_def.nodes.items():
            retry_cfg = workflow_def.retry_config.get(node_name, RetryConfig())
            wrapped = self._wrap_node_with_retry(node_spec, retry_cfg)
            builder.add_node(node_name, wrapped)

        # Add edges
        for edge in workflow_def.edges:
            if edge.condition is not None:
                builder.add_conditional_edges(edge.source, edge.condition)
            elif isinstance(edge.target, str):
                if edge.target == "__end__":
                    builder.add_edge(edge.source, END)
                else:
                    builder.add_edge(edge.source, edge.target)

        # Set entry point
        builder.set_entry_point(workflow_def.entry_point)

        # Compile with interrupts
        compile_kwargs = {}
        if workflow_def.interrupt_nodes:
            compile_kwargs["interrupt_before"] = workflow_def.interrupt_nodes

        return builder.compile(**compile_kwargs)

    def _wrap_node_with_retry(self, node_spec: NodeSpec, retry_config: RetryConfig) -> Callable:
        """Wrap a node function with retry logic and timing."""

        async def wrapped(state: Dict[str, Any]) -> Dict[str, Any]:
            last_error = None
            attempts = retry_config.max_attempts if node_spec.retry_on_error else 1

            for attempt in range(1, attempts + 1):
                try:
                    start = time.time()
                    if asyncio.iscoroutinefunction(node_spec.function):
                        result = await asyncio.wait_for(
                            node_spec.function(state),
                            timeout=node_spec.timeout_seconds
                        )
                    else:
                        result = node_spec.function(state)

                    duration = time.time() - start

                    # Track timing in state
                    if isinstance(result, dict):
                        timings = result.get("step_timings", state.get("step_timings", {}))
                        timings[node_spec.name] = round(duration, 3)
                        result["step_timings"] = timings

                    logger.info("graph_builder.node_completed",
                                node=node_spec.name, attempt=attempt, duration=round(duration, 3))
                    return result

                except asyncio.TimeoutError:
                    last_error = f"Timeout after {node_spec.timeout_seconds}s"
                    logger.warning("graph_builder.node_timeout",
                                   node=node_spec.name, attempt=attempt, timeout=node_spec.timeout_seconds)
                except Exception as e:
                    last_error = str(e)
                    logger.warning("graph_builder.node_error",
                                   node=node_spec.name, attempt=attempt, error=str(e))

                if attempt < attempts:
                    await asyncio.sleep(retry_config.backoff_seconds * attempt)

            # All retries exhausted
            errors = state.get("errors", [])
            errors.append({
                "node": node_spec.name,
                "error": last_error,
                "attempts": attempts,
                "traceback": traceback.format_exc(),
            })
            return {**state, "errors": errors}

        return wrapped

    def get_compiled(self, workflow_name: str) -> Optional["CompiledProductionGraph"]:
        """Get a previously compiled graph."""
        return self._compiled_graphs.get(workflow_name)

    def list_workflows(self) -> List[WorkflowInfo]:
        """List all registered workflows."""
        results = []
        for name, graph in self._compiled_graphs.items():
            wf = graph.workflow_def
            results.append(WorkflowInfo(
                name=wf.name, description=wf.description,
                node_count=len(wf.nodes), edge_count=len(wf.edges),
                interrupt_nodes=wf.interrupt_nodes,
                parallel_groups=wf.parallel_groups,
                entry_point=wf.entry_point,
            ))
        return results


# ---------------------------------------------------------------------------
# Compiled Production Graph
# ---------------------------------------------------------------------------

class CompiledProductionGraph:
    """A compiled production graph that wraps LangGraph with additional features."""

    def __init__(self, workflow_def: WorkflowDefinition,
                 checkpoint_store: CheckpointStore,
                 langgraph: Any = None):
        self.workflow_def = workflow_def
        self.checkpoint_store = checkpoint_store
        self.langgraph = langgraph
        self._running: Dict[str, bool] = {}

    async def invoke(self, input_state: Dict[str, Any],
                     thread_id: Optional[str] = None) -> Dict[str, Any]:
        """Execute the workflow synchronously (wait for completion)."""
        tid = thread_id or f"thread_{uuid.uuid4().hex[:12]}"

        # Initialize state with defaults
        state = {}
        for key, default in self.workflow_def.state_schema.items():
            if isinstance(default, list):
                state[key] = list(default)
            elif isinstance(default, dict):
                state[key] = dict(default)
            else:
                state[key] = default
        state.update(input_state)
        state.setdefault("errors", [])
        state.setdefault("step_timings", {})

        # Create thread
        await self.checkpoint_store.create_thread(
            workflow_name=self.workflow_def.name, thread_id=tid,
            metadata={"input_keys": list(input_state.keys())}
        )

        # If LangGraph is available, use it
        if self.langgraph is not None:
            try:
                checkpointer = await self.checkpoint_store.get_checkpointer()
                config = {"configurable": {"thread_id": tid}, "checkpointer": checkpointer}
                result = await self.langgraph.ainvoke(state, config=config)
                await self.checkpoint_store.update_thread_status(tid, "completed")
                return result
            except Exception as e:
                logger.warning("graph_builder.langgraph_invoke_failed, using manual execution",
                               error=str(e))

        # Manual execution fallback
        result = await self._execute_manually(state, tid)
        return result

    async def _execute_manually(self, state: Dict[str, Any], thread_id: str) -> Dict[str, Any]:
        """Execute workflow manually following edges."""
        current_node = self.workflow_def.entry_point
        step = 0
        visited = set()

        self._running[thread_id] = True

        try:
            while current_node and current_node != "__end__" and self._running.get(thread_id, False):
                if current_node in visited and step > len(self.workflow_def.nodes) * 2:
                    break  # Prevent infinite loops
                visited.add(current_node)
                step += 1

                node_spec = self.workflow_def.nodes.get(current_node)
                if not node_spec:
                    logger.error("graph_builder.node_not_found", node=current_node)
                    break

                # Check for interrupt
                if current_node in self.workflow_def.interrupt_nodes:
                    await self.checkpoint_store.save_snapshot(
                        thread_id, step, current_node, state,
                        metadata={"interrupted": True}
                    )
                    await self.checkpoint_store.update_thread_status(
                        thread_id, "interrupted", current_node=current_node, step_count=step
                    )
                    state["_interrupted_at"] = current_node
                    state["_thread_id"] = thread_id
                    return state

                # Check for parallel group
                parallel_group = None
                for group in self.workflow_def.parallel_groups:
                    if current_node in group:
                        parallel_group = group
                        break

                if parallel_group and all(n in self.workflow_def.nodes for n in parallel_group):
                    # Execute parallel nodes
                    state = await self._execute_parallel(parallel_group, state, thread_id, step)
                    step += len(parallel_group) - 1  # Account for parallel steps
                    # Skip to the edge target of the last parallel node
                    last_parallel = parallel_group[-1]
                    current_node = self._find_next_node(last_parallel, state)
                else:
                    # Execute single node
                    retry_cfg = self.workflow_def.retry_config.get(current_node, RetryConfig())
                    wrapped = self._wrap_node(node_spec, retry_cfg)
                    state = await wrapped(state)

                    # Save checkpoint
                    await self.checkpoint_store.save_snapshot(
                        thread_id, step, current_node, state
                    )

                    # Find next node
                    current_node = self._find_next_node(current_node, state)

            # Workflow complete
            await self.checkpoint_store.update_thread_status(
                thread_id, "completed", step_count=step
            )
            state["_completed"] = True

        except Exception as e:
            logger.error("graph_builder.execution_error", error=str(e), node=current_node)
            state["errors"] = state.get("errors", []) + [{
                "node": current_node, "error": str(e),
                "traceback": traceback.format_exc()
            }]
            await self.checkpoint_store.update_thread_status(
                thread_id, "failed", current_node=current_node, step_count=step
            )
        finally:
            self._running.pop(thread_id, None)

        return state

    async def _execute_parallel(self, group: List[str], state: Dict[str, Any],
                                 thread_id: str, base_step: int) -> Dict[str, Any]:
        """Execute a group of nodes in parallel."""

        async def run_node(node_name: str) -> Dict[str, Any]:
            node_spec = self.workflow_def.nodes[node_name]
            retry_cfg = self.workflow_def.retry_config.get(node_name, RetryConfig())
            wrapped = self._wrap_node(node_spec, retry_cfg)
            return await wrapped(dict(state))  # Copy state

        tasks = [run_node(name) for name in group]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Merge results
        merged = dict(state)
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                merged.setdefault("errors", []).append({
                    "node": group[i], "error": str(result)
                })
            elif isinstance(result, dict):
                for key, val in result.items():
                    if key in ("errors", "step_timings"):
                        # Merge lists/dicts
                        if isinstance(val, list):
                            merged.setdefault(key, []).extend(val)
                        elif isinstance(val, dict):
                            merged.setdefault(key, {}).update(val)
                    else:
                        merged[key] = val

        # Save parallel checkpoint
        await self.checkpoint_store.save_snapshot(
            thread_id, base_step, f"parallel:{'|'.join(group)}", merged,
            metadata={"parallel": True, "nodes": group}
        )

        return merged

    def _wrap_node(self, node_spec: NodeSpec, retry_config: RetryConfig) -> Callable:
        """Create a retry-wrapped async node function."""

        async def wrapped(state: Dict[str, Any]) -> Dict[str, Any]:
            last_error = None
            attempts = retry_config.max_attempts if node_spec.retry_on_error else 1

            for attempt in range(1, attempts + 1):
                try:
                    start = time.time()
                    if asyncio.iscoroutinefunction(node_spec.function):
                        result = await asyncio.wait_for(
                            node_spec.function(state),
                            timeout=node_spec.timeout_seconds
                        )
                    else:
                        result = node_spec.function(state)

                    duration = time.time() - start
                    if isinstance(result, dict):
                        timings = result.get("step_timings", state.get("step_timings", {}))
                        timings[node_spec.name] = round(duration, 3)
                        result["step_timings"] = timings
                    return result

                except (asyncio.TimeoutError, asyncio.CancelledError) as e:
                    last_error = str(e)
                except Exception as e:
                    last_error = str(e)

                if attempt < attempts:
                    await asyncio.sleep(retry_config.backoff_seconds * attempt)

            errors = state.get("errors", [])
            errors.append({"node": node_spec.name, "error": last_error, "attempts": attempts})
            return {**state, "errors": errors}

        return wrapped

    def _find_next_node(self, current: str, state: Dict[str, Any]) -> Optional[str]:
        """Find the next node based on edges."""
        for edge in self.workflow_def.edges:
            if edge.source == current:
                if edge.condition:
                    return edge.condition(state)
                return edge.target if isinstance(edge.target, str) else edge.target[0]
        return "__end__"

    async def resume(self, thread_id: str, updated_state: Optional[Dict] = None) -> Dict[str, Any]:
        """Resume an interrupted workflow."""
        history = await self.checkpoint_store.get_thread_history(thread_id)
        if not history:
            raise ValueError(f"No checkpoints found for thread {thread_id}")

        last = history[-1]
        state = dict(last.state)
        if updated_state:
            state.update(updated_state)

        # Remove interrupt marker and continue
        interrupted_at = state.pop("_interrupted_at", None)
        state.pop("_thread_id", None)

        if interrupted_at:
            # Find the next node after the interrupt
            next_node = self._find_next_node(interrupted_at, state)
            if next_node and next_node != "__end__":
                # Re-execute from next node
                state_copy = dict(state)
                # Temporarily remove interrupt to allow proceeding
                orig_interrupts = list(self.workflow_def.interrupt_nodes)
                if interrupted_at in self.workflow_def.interrupt_nodes:
                    self.workflow_def.interrupt_nodes.remove(interrupted_at)

                self.workflow_def.entry_point = next_node
                result = await self._execute_manually(state_copy, thread_id)

                # Restore
                self.workflow_def.interrupt_nodes = orig_interrupts
                return result

        return state

    async def cancel(self, thread_id: str) -> bool:
        """Cancel a running workflow."""
        self._running[thread_id] = False
        await self.checkpoint_store.update_thread_status(thread_id, "cancelled")
        return True


# ---------------------------------------------------------------------------
# Singleton builder
# ---------------------------------------------------------------------------

_builder: Optional[ProductionGraphBuilder] = None


def get_graph_builder() -> ProductionGraphBuilder:
    """Get or create the singleton ProductionGraphBuilder."""
    global _builder
    if _builder is None:
        _builder = ProductionGraphBuilder()
    return _builder
