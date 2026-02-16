"""Phase 41A — Worker Agent Registry

Specialized worker agents with defined capabilities, output schemas,
and performance tracking. Each worker type handles a specific BD domain.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


# =========================================
# ENUMS
# =========================================


class WorkerType(str, Enum):
    RESEARCH = "research"
    CONTACT_DISCOVERY = "contact_discovery"
    JOB_INTEL = "job_intel"
    OUTREACH_CRAFTER = "outreach_crafter"
    DOCUMENT_GENERATOR = "document_generator"
    ANALYTICS = "analytics"
    PAST_PERFORMANCE = "past_performance"
    KNOWLEDGE = "knowledge"


class WorkerStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    CANCELLED = "cancelled"


# =========================================
# DATA CLASSES
# =========================================


@dataclass
class WorkerCapability:
    """Describes what a worker type can do."""

    worker_type: str
    description: str
    tools: List[str] = field(default_factory=list)
    output_fields: List[str] = field(default_factory=list)
    avg_tokens: int = 2000
    avg_time_seconds: float = 30.0
    keywords: List[str] = field(default_factory=list)


@dataclass
class WorkerStats:
    """Performance statistics for a worker type."""

    worker_type: str
    total_executions: int = 0
    successful: int = 0
    failed: int = 0
    avg_latency_seconds: float = 0.0
    avg_tokens_used: int = 0
    avg_quality_score: float = 0.0


@dataclass
class WorkerHandle:
    """Handle to a running worker instance."""

    worker_id: str
    worker_type: str
    status: str = WorkerStatus.IDLE.value
    task_id: str = ""
    started_at: str = ""
    completed_at: str = ""
    result: Dict[str, Any] = field(default_factory=dict)
    error: str = ""
    tokens_used: int = 0
    latency_seconds: float = 0.0


@dataclass
class SubTask:
    """A sub-task assigned to a worker."""

    id: str = ""
    description: str = ""
    worker_type: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    priority: int = 1
    timeout_seconds: int = 120
    context: Dict[str, Any] = field(default_factory=dict)


# =========================================
# WORKER AGENT
# =========================================


class WorkerAgent:
    """Base worker agent that executes sub-tasks."""

    def __init__(self, worker_type: str, capability: WorkerCapability):
        self.worker_type = worker_type
        self.capability = capability
        self._execute_fn: Optional[Callable] = None

    def set_execute_fn(self, fn: Callable) -> None:
        """Set custom execution function."""
        self._execute_fn = fn

    async def execute(self, subtask: SubTask) -> Dict[str, Any]:
        """Execute a sub-task and return results."""
        if self._execute_fn:
            return await self._execute_fn(subtask)

        # Default: return a structured result based on worker type
        return self._default_execute(subtask)

    def _default_execute(self, subtask: SubTask) -> Dict[str, Any]:
        """Default execution producing placeholder structured output."""
        base = {
            "worker_type": self.worker_type,
            "task_id": subtask.id,
            "description": subtask.description,
            "status": "completed",
        }

        if self.worker_type == WorkerType.RESEARCH.value:
            base.update(
                {
                    "program_name": subtask.parameters.get("program", ""),
                    "findings": [],
                    "contracts": [],
                    "competitors": [],
                }
            )
        elif self.worker_type == WorkerType.CONTACT_DISCOVERY.value:
            base.update(
                {
                    "contacts_found": 0,
                    "contacts": [],
                    "sources_checked": self.capability.tools,
                }
            )
        elif self.worker_type == WorkerType.JOB_INTEL.value:
            base.update(
                {
                    "jobs_found": 0,
                    "jobs": [],
                    "trends": [],
                }
            )
        elif self.worker_type == WorkerType.OUTREACH_CRAFTER.value:
            base.update(
                {
                    "messages_crafted": 0,
                    "outreach": [],
                }
            )
        elif self.worker_type == WorkerType.DOCUMENT_GENERATOR.value:
            base.update(
                {
                    "documents_generated": 0,
                    "documents": [],
                }
            )
        elif self.worker_type == WorkerType.ANALYTICS.value:
            base.update(
                {
                    "metrics": {},
                    "trends": [],
                    "insights": [],
                }
            )
        elif self.worker_type == WorkerType.PAST_PERFORMANCE.value:
            base.update(
                {
                    "matches_found": 0,
                    "past_performance": [],
                }
            )
        elif self.worker_type == WorkerType.KNOWLEDGE.value:
            base.update(
                {
                    "facts_found": 0,
                    "entities": [],
                    "relationships": [],
                }
            )

        return base


# =========================================
# WORKER REGISTRY
# =========================================

# Default capabilities for each worker type
DEFAULT_CAPABILITIES: Dict[str, WorkerCapability] = {
    WorkerType.RESEARCH.value: WorkerCapability(
        worker_type=WorkerType.RESEARCH.value,
        description="Program, contract, and company research",
        tools=["web_search", "graph_traverse", "vector_search", "sam_gov_query"],
        output_fields=["program_name", "findings", "contracts", "competitors"],
        avg_tokens=2000,
        avg_time_seconds=30.0,
        keywords=[
            "research",
            "program",
            "contract",
            "company",
            "investigation",
            "analysis",
        ],
    ),
    WorkerType.CONTACT_DISCOVERY.value: WorkerCapability(
        worker_type=WorkerType.CONTACT_DISCOVERY.value,
        description="Find, validate, and enrich contacts",
        tools=["vector_search", "graph_traverse", "zoominfo_api", "linkedin_search"],
        output_fields=["contacts_found", "contacts", "sources_checked"],
        avg_tokens=3000,
        avg_time_seconds=45.0,
        keywords=["contact", "person", "find", "discover", "lookup", "email", "phone"],
    ),
    WorkerType.JOB_INTEL.value: WorkerCapability(
        worker_type=WorkerType.JOB_INTEL.value,
        description="Job scraping, analysis, and program mapping",
        tools=["job_scrape", "program_mapper", "trend_analyzer"],
        output_fields=["jobs_found", "jobs", "trends"],
        avg_tokens=2500,
        avg_time_seconds=35.0,
        keywords=["job", "position", "opening", "hiring", "vacancy", "staffing"],
    ),
    WorkerType.OUTREACH_CRAFTER.value: WorkerCapability(
        worker_type=WorkerType.OUTREACH_CRAFTER.value,
        description="Personalized BD outreach following 6-step formula",
        tools=["memory_recall", "past_perf_search", "pain_point_lookup"],
        output_fields=["messages_crafted", "outreach"],
        avg_tokens=4000,
        avg_time_seconds=60.0,
        keywords=["outreach", "message", "email", "call", "script", "pitch"],
    ),
    WorkerType.DOCUMENT_GENERATOR.value: WorkerCapability(
        worker_type=WorkerType.DOCUMENT_GENERATOR.value,
        description="Generate playbooks, call sheets, reports, briefings",
        tools=["template_engine", "data_formatter", "file_creator"],
        output_fields=["documents_generated", "documents"],
        avg_tokens=5000,
        avg_time_seconds=90.0,
        keywords=[
            "document",
            "report",
            "playbook",
            "call sheet",
            "briefing",
            "generate",
        ],
    ),
    WorkerType.ANALYTICS.value: WorkerCapability(
        worker_type=WorkerType.ANALYTICS.value,
        description="Data analysis, trends, comparisons, statistics",
        tools=["sql_query", "vector_search", "temporal_query", "statistical_analysis"],
        output_fields=["metrics", "trends", "insights"],
        avg_tokens=2500,
        avg_time_seconds=40.0,
        keywords=["analyze", "trend", "compare", "statistics", "metric", "data"],
    ),
    WorkerType.PAST_PERFORMANCE.value: WorkerCapability(
        worker_type=WorkerType.PAST_PERFORMANCE.value,
        description="Past performance matching and relevance scoring",
        tools=["vector_search", "document_lookup", "keyword_search"],
        output_fields=["matches_found", "past_performance"],
        avg_tokens=2000,
        avg_time_seconds=25.0,
        keywords=[
            "past performance",
            "capability",
            "experience",
            "win",
            "contract history",
        ],
    ),
    WorkerType.KNOWLEDGE.value: WorkerCapability(
        worker_type=WorkerType.KNOWLEDGE.value,
        description="Knowledge graph queries, entity resolution, fact compilation",
        tools=[
            "temporal_query",
            "graph_traverse",
            "entity_resolution",
            "knowledge_compiler",
        ],
        output_fields=["facts_found", "entities", "relationships"],
        avg_tokens=1500,
        avg_time_seconds=20.0,
        keywords=["knowledge", "entity", "relationship", "fact", "graph", "timeline"],
    ),
}


class WorkerRegistry:
    """Registry of all available worker agent types and their capabilities."""

    def __init__(self):
        self._capabilities: Dict[str, WorkerCapability] = dict(DEFAULT_CAPABILITIES)
        self._stats: Dict[str, WorkerStats] = {
            wt: WorkerStats(worker_type=wt) for wt in self._capabilities
        }
        self._custom_executors: Dict[str, Callable] = {}

    def register_executor(self, worker_type: str, fn: Callable) -> None:
        """Register a custom execution function for a worker type."""
        self._custom_executors[worker_type] = fn

    def list_worker_types(self) -> List[str]:
        """List all registered worker types."""
        return list(self._capabilities.keys())

    def get_capability(self, worker_type: str) -> Optional[WorkerCapability]:
        """Get capability description for a worker type."""
        return self._capabilities.get(worker_type)

    def get_all_capabilities(self) -> Dict[str, WorkerCapability]:
        """Get all worker capabilities."""
        return dict(self._capabilities)

    def get_worker(self, worker_type: str) -> Optional[WorkerAgent]:
        """Instantiate a worker agent of the given type."""
        cap = self._capabilities.get(worker_type)
        if not cap:
            return None
        agent = WorkerAgent(worker_type, cap)
        if worker_type in self._custom_executors:
            agent.set_execute_fn(self._custom_executors[worker_type])
        return agent

    def get_best_worker(self, subtask: SubTask) -> str:
        """Select the best worker type for a sub-task using keyword matching."""
        if subtask.worker_type and subtask.worker_type in self._capabilities:
            return subtask.worker_type

        desc_lower = subtask.description.lower()
        best_type = ""
        best_score = 0

        for wtype, cap in self._capabilities.items():
            score = 0
            for kw in cap.keywords:
                if kw.lower() in desc_lower:
                    score += 1
            if score > best_score:
                best_score = score
                best_type = wtype

        return best_type or WorkerType.RESEARCH.value

    def get_stats(self, worker_type: str) -> Optional[WorkerStats]:
        """Get performance statistics for a worker type."""
        return self._stats.get(worker_type)

    def get_all_stats(self) -> Dict[str, WorkerStats]:
        """Get stats for all worker types."""
        return dict(self._stats)

    def record_execution(
        self,
        worker_type: str,
        success: bool,
        latency_seconds: float,
        tokens_used: int,
        quality_score: float = 0.8,
    ) -> None:
        """Record a worker execution for statistics."""
        stats = self._stats.get(worker_type)
        if not stats:
            return

        n = stats.total_executions
        stats.total_executions += 1
        if success:
            stats.successful += 1
        else:
            stats.failed += 1

        if n == 0:
            stats.avg_latency_seconds = latency_seconds
            stats.avg_tokens_used = tokens_used
            stats.avg_quality_score = quality_score
        else:
            stats.avg_latency_seconds = (
                stats.avg_latency_seconds * n + latency_seconds
            ) / (n + 1)
            stats.avg_tokens_used = int(
                (stats.avg_tokens_used * n + tokens_used) / (n + 1)
            )
            stats.avg_quality_score = (stats.avg_quality_score * n + quality_score) / (
                n + 1
            )


# =========================================
# SINGLETON
# =========================================

_registry: Optional[WorkerRegistry] = None


def get_worker_registry() -> WorkerRegistry:
    global _registry
    if _registry is None:
        _registry = WorkerRegistry()
    return _registry
