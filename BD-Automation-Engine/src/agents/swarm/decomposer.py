"""Phase 41A — Task Decomposition Engine

Breaks high-level BD tasks into dependency-ordered sub-task DAGs.
Supports template-based decomposition, DAG optimization, and cost estimation.
"""

import logging
import re
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from src.agents.swarm.workers import SubTask, WorkerType, DEFAULT_CAPABILITIES

logger = logging.getLogger(__name__)


# =========================================
# DATA CLASSES
# =========================================

@dataclass
class TaskDAG:
    """Directed acyclic graph of sub-tasks."""
    dag_id: str = ""
    root_task: str = ""
    nodes: List[SubTask] = field(default_factory=list)
    edges: List[Tuple[str, str]] = field(default_factory=list)  # (from_id, to_id)
    execution_layers: List[List[str]] = field(default_factory=list)  # parallel groups
    total_estimated_tokens: int = 0
    total_estimated_seconds: float = 0.0
    critical_path_seconds: float = 0.0


@dataclass
class CostEstimate:
    """Cost and time estimate for executing a DAG."""
    total_tokens: int = 0
    total_api_cost_usd: float = 0.0
    estimated_time_seconds: float = 0.0
    critical_path_seconds: float = 0.0
    num_workers: int = 0
    num_parallel_groups: int = 0
    worker_breakdown: Dict[str, int] = field(default_factory=dict)  # worker_type → token estimate


# =========================================
# TASK TEMPLATES
# =========================================

# Each template defines sub-tasks with their worker type and dependencies.
# Dependencies reference the position index in the list (0-based).

TASK_TEMPLATES: Dict[str, List[Dict[str, Any]]] = {
    "campaign_build": [
        {"name": "Research program/contract details", "worker": "research", "depends": []},
        {"name": "Discover and validate contacts", "worker": "contact_discovery", "depends": []},
        {"name": "Analyze current job openings", "worker": "job_intel", "depends": []},
        {"name": "Find relevant past performance", "worker": "past_performance", "depends": []},
        {"name": "Classify contacts by tier and priority", "worker": "analytics", "depends": [1]},
        {"name": "Match jobs to contacts and programs", "worker": "analytics", "depends": [1, 2]},
        {"name": "Identify pain points from HUMINT data", "worker": "knowledge", "depends": [0]},
        {"name": "Craft personalized outreach messages", "worker": "outreach_crafter", "depends": [3, 4, 5, 6]},
        {"name": "Generate call sheet", "worker": "document_generator", "depends": [4, 7]},
        {"name": "Generate BD playbook", "worker": "document_generator", "depends": [0, 1, 2, 3, 4, 5, 6, 7]},
    ],
    "contact_enrichment": [
        {"name": "Discover contacts from multiple sources", "worker": "contact_discovery", "depends": []},
        {"name": "Validate contact information", "worker": "contact_discovery", "depends": [0]},
        {"name": "Classify contacts by tier", "worker": "analytics", "depends": [1]},
        {"name": "Enrich with knowledge graph data", "worker": "knowledge", "depends": [1]},
        {"name": "Update CRM records", "worker": "document_generator", "depends": [2, 3]},
    ],
    "program_analysis": [
        {"name": "Research program details and timeline", "worker": "research", "depends": []},
        {"name": "Analyze contracts and funding", "worker": "research", "depends": []},
        {"name": "Find program contacts", "worker": "contact_discovery", "depends": []},
        {"name": "Analyze related job postings", "worker": "job_intel", "depends": []},
        {"name": "Gather competitor intelligence", "worker": "research", "depends": [0]},
        {"name": "Generate analysis report", "worker": "document_generator", "depends": [0, 1, 2, 3, 4]},
    ],
    "weekly_briefing": [
        {"name": "Scan for new job postings", "worker": "job_intel", "depends": []},
        {"name": "Check for contact changes", "worker": "contact_discovery", "depends": []},
        {"name": "Review contract updates", "worker": "research", "depends": []},
        {"name": "Summarize HUMINT data", "worker": "knowledge", "depends": []},
        {"name": "Generate weekly briefing document", "worker": "document_generator", "depends": [0, 1, 2, 3]},
    ],
    "competitive_analysis": [
        {"name": "Research target competitor", "worker": "research", "depends": []},
        {"name": "Find competitor contracts", "worker": "research", "depends": [0]},
        {"name": "Identify competitor personnel", "worker": "contact_discovery", "depends": [0]},
        {"name": "Analyze competitor job postings", "worker": "job_intel", "depends": [0]},
        {"name": "Compare with our capabilities", "worker": "analytics", "depends": [1, 3]},
        {"name": "Generate competitive intel report", "worker": "document_generator", "depends": [0, 1, 2, 3, 4]},
    ],
}

# Keyword-to-template mapping
TEMPLATE_KEYWORDS: Dict[str, List[str]] = {
    "campaign_build": ["campaign", "playbook", "outreach", "bd campaign", "business development"],
    "contact_enrichment": ["enrich", "contact enrichment", "update contacts", "validate contacts"],
    "program_analysis": ["program analysis", "analyze program", "program intel", "contract analysis"],
    "weekly_briefing": ["weekly", "briefing", "weekly update", "status report"],
    "competitive_analysis": ["competitor", "competitive", "compete", "rival"],
}


# =========================================
# TASK DECOMPOSER
# =========================================

class TaskDecomposer:
    """Breaks high-level BD tasks into dependency-ordered sub-task DAGs."""

    def __init__(self):
        self._history: List[TaskDAG] = []

    def _detect_template(self, description: str) -> str:
        """Detect the best template for a task description."""
        desc_lower = description.lower()
        best_template = ""
        best_score = 0

        for template_name, keywords in TEMPLATE_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in desc_lower)
            if score > best_score:
                best_score = score
                best_template = template_name

        return best_template or "campaign_build"

    def _extract_parameters(self, description: str) -> Dict[str, str]:
        """Extract key parameters from the task description."""
        params: Dict[str, str] = {}

        # Program names
        programs = re.findall(
            r'\b(DCGS|DCGS-[A-Z]|GBSD|NGEN|DEOS|CES|JADC2|ABMS|ODIN|TITAN)\b',
            description, re.IGNORECASE,
        )
        if programs:
            params["program"] = programs[0].upper()

        # Organization names
        orgs = re.findall(
            r'\b(GDIT|Leidos|SAIC|Northrop|Raytheon|Lockheed|BAE|CACI|ManTech|Peraton|Navy|Army|Air Force)\b',
            description, re.IGNORECASE,
        )
        if orgs:
            params["organization"] = orgs[0]

        # Locations
        locations = re.findall(
            r'\b(Norfolk|Langley|PACAF|Wright-Patterson|San Diego|Fort Meade|Huntsville)\b',
            description, re.IGNORECASE,
        )
        if locations:
            params["location"] = locations[0]

        return params

    async def decompose(self, task_description: str, task_type: str = "") -> TaskDAG:
        """Create a dependency DAG from a task description."""
        dag_id = uuid.uuid4().hex[:10]

        # Detect template
        template_name = task_type if task_type in TASK_TEMPLATES else self._detect_template(task_description)
        template = TASK_TEMPLATES.get(template_name, TASK_TEMPLATES["campaign_build"])

        # Extract parameters
        params = self._extract_parameters(task_description)

        # Build sub-tasks from template
        nodes: List[SubTask] = []
        id_map: Dict[int, str] = {}

        for i, tmpl in enumerate(template):
            task_id = uuid.uuid4().hex[:8]
            id_map[i] = task_id

            nodes.append(SubTask(
                id=task_id,
                description=tmpl["name"],
                worker_type=tmpl["worker"],
                parameters=dict(params),
                depends_on=[],
                priority=1 if not tmpl["depends"] else 2,
            ))

        # Resolve dependency references (index → actual ID)
        edges: List[Tuple[str, str]] = []
        for i, tmpl in enumerate(template):
            for dep_idx in tmpl["depends"]:
                if dep_idx in id_map:
                    nodes[i].depends_on.append(id_map[dep_idx])
                    edges.append((id_map[dep_idx], id_map[i]))

        # Compute execution layers (topological sort into parallel groups)
        execution_layers = self._compute_layers(nodes)

        # Estimate costs
        total_tokens = 0
        total_time = 0.0
        for node in nodes:
            cap = DEFAULT_CAPABILITIES.get(node.worker_type)
            if cap:
                total_tokens += cap.avg_tokens
                total_time += cap.avg_time_seconds

        # Critical path = sum of longest path through DAG
        critical_path = self._compute_critical_path(nodes, edges)

        dag = TaskDAG(
            dag_id=dag_id,
            root_task=task_description,
            nodes=nodes,
            edges=edges,
            execution_layers=execution_layers,
            total_estimated_tokens=total_tokens,
            total_estimated_seconds=round(total_time, 1),
            critical_path_seconds=round(critical_path, 1),
        )

        self._history.append(dag)
        return dag

    async def optimize_dag(self, dag: TaskDAG) -> TaskDAG:
        """Optimize DAG for maximum parallelism.

        Strategy: recompute layers to maximize parallel execution.
        """
        dag.execution_layers = self._compute_layers(dag.nodes)
        dag.critical_path_seconds = self._compute_critical_path(dag.nodes, dag.edges)
        return dag

    async def estimate_cost(self, dag: TaskDAG) -> CostEstimate:
        """Estimate tokens, time, and API costs for executing the DAG."""
        total_tokens = 0
        worker_breakdown: Dict[str, int] = {}

        for node in dag.nodes:
            cap = DEFAULT_CAPABILITIES.get(node.worker_type)
            tokens = cap.avg_tokens if cap else 2000
            total_tokens += tokens
            worker_breakdown[node.worker_type] = worker_breakdown.get(node.worker_type, 0) + tokens

        # Cost estimate: ~$0.003 per 1K input tokens (Claude Sonnet pricing approximation)
        api_cost = (total_tokens / 1000) * 0.003

        return CostEstimate(
            total_tokens=total_tokens,
            total_api_cost_usd=round(api_cost, 4),
            estimated_time_seconds=dag.total_estimated_seconds,
            critical_path_seconds=dag.critical_path_seconds,
            num_workers=len(dag.nodes),
            num_parallel_groups=len(dag.execution_layers),
            worker_breakdown=worker_breakdown,
        )

    def get_history(self) -> List[TaskDAG]:
        return self._history

    # -----------------------------------------
    # Internal helpers
    # -----------------------------------------

    def _compute_layers(self, nodes: List[SubTask]) -> List[List[str]]:
        """Topological sort into parallel execution layers."""
        node_ids = {n.id for n in nodes}
        in_degree: Dict[str, int] = {n.id: 0 for n in nodes}
        dependents: Dict[str, List[str]] = {n.id: [] for n in nodes}

        for node in nodes:
            for dep in node.depends_on:
                if dep in node_ids:
                    in_degree[node.id] += 1
                    dependents[dep].append(node.id)

        layers: List[List[str]] = []
        remaining = set(node_ids)

        while remaining:
            # Find all nodes with in_degree == 0
            ready = [nid for nid in remaining if in_degree.get(nid, 0) == 0]
            if not ready:
                # Break cycles
                ready = [min(remaining)]

            layers.append(sorted(ready))
            for nid in ready:
                remaining.discard(nid)
                for dep in dependents.get(nid, []):
                    in_degree[dep] = max(0, in_degree.get(dep, 0) - 1)

        return layers

    def _compute_critical_path(
        self, nodes: List[SubTask], edges: List[Tuple[str, str]],
    ) -> float:
        """Compute the critical path duration (longest path through DAG)."""
        node_map = {n.id: n for n in nodes}
        time_map: Dict[str, float] = {}

        def get_time(nid: str) -> float:
            cap = DEFAULT_CAPABILITIES.get(node_map[nid].worker_type) if nid in node_map else None
            return cap.avg_time_seconds if cap else 30.0

        # Build adjacency for reverse traversal
        children: Dict[str, List[str]] = {n.id: [] for n in nodes}
        for from_id, to_id in edges:
            children[from_id].append(to_id)

        # Compute longest path using dynamic programming
        memo: Dict[str, float] = {}

        def longest_path(nid: str) -> float:
            if nid in memo:
                return memo[nid]
            node_time = get_time(nid)
            child_times = [longest_path(cid) for cid in children.get(nid, [])]
            total = node_time + (max(child_times) if child_times else 0)
            memo[nid] = total
            return total

        # Find the longest path from any root node
        roots = [n.id for n in nodes if not n.depends_on]
        if not roots:
            roots = [nodes[0].id] if nodes else []

        if not roots:
            return 0.0

        return max(longest_path(r) for r in roots)


# =========================================
# SINGLETON
# =========================================

_decomposer: Optional[TaskDecomposer] = None


def get_task_decomposer() -> TaskDecomposer:
    global _decomposer
    if _decomposer is None:
        _decomposer = TaskDecomposer()
    return _decomposer
