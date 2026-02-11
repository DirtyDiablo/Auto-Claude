"""Phase 40A — Query Decomposition Engine

Break complex queries into atomic sub-queries for parallel retrieval,
identify dependencies, and synthesize combined answers.
"""

import logging
import re
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


# =========================================
# DATA CLASSES
# =========================================

@dataclass
class SubQuery:
    """An atomic sub-query extracted from a complex query."""
    id: str = ""
    text: str = ""
    intent: str = ""  # person, program, hiring, trend, comparison
    entities: List[str] = field(default_factory=list)
    depends_on: List[str] = field(default_factory=list)  # IDs of prerequisite sub-queries
    priority: int = 1  # Lower = higher priority
    answer: str = ""  # Filled after retrieval


@dataclass
class DependencyGraph:
    """Dependency graph for sub-queries."""
    nodes: List[str] = field(default_factory=list)  # sub-query IDs
    edges: List[Tuple[str, str]] = field(default_factory=list)  # (from, to) = "from" must complete before "to"
    parallel_groups: List[List[str]] = field(default_factory=list)  # Groups that can run in parallel
    execution_order: List[List[str]] = field(default_factory=list)  # Ordered layers of parallel groups


@dataclass
class DecompositionPlan:
    """Complete plan for decomposing and executing a complex query."""
    original_query: str = ""
    sub_queries: List[SubQuery] = field(default_factory=list)
    dependency_graph: Optional[DependencyGraph] = None
    is_decomposed: bool = False
    complexity_score: float = 0.0  # 0-1
    synthesis_strategy: str = "merge"  # merge, compare, aggregate, narrative


# =========================================
# DECOMPOSITION PATTERNS
# =========================================

# Comparison patterns: "X vs Y", "compare X and Y"
COMPARISON_PATTERNS = [
    re.compile(r'\b(compare|versus|vs\.?|compared to|difference between)\b', re.IGNORECASE),
    re.compile(r'(\w+)\s+(?:vs\.?|versus)\s+(\w+)', re.IGNORECASE),
]

# Conjunction patterns: "X and Y", "X as well as Y"
CONJUNCTION_PATTERNS = [
    re.compile(r'\band\b(?!\s+(?:the|a|an)\b)', re.IGNORECASE),
    re.compile(r'\b(as well as|along with|together with|in addition to|also)\b', re.IGNORECASE),
]

# Multi-aspect patterns: "who ... and what ..."
MULTI_ASPECT_PATTERNS = [
    re.compile(r'\b(who|what|where|when|how)\b.*\b(and|also|plus)\b.*\b(who|what|where|when|how)\b', re.IGNORECASE),
]

# Temporal decomposition: "over the last X months"
TEMPORAL_PATTERNS = [
    re.compile(r'\b(over|during|in|for)\s+the\s+(last|past|previous)\s+(\d+)\s+(month|year|quarter|week)s?\b', re.IGNORECASE),
    re.compile(r'\b(trend|change|growth|evolution|history)\b', re.IGNORECASE),
]

# Entity extraction for sub-query generation
ENTITY_PATTERNS = [
    re.compile(r'\b([A-Z][a-z]+ [A-Z][a-z]+)\b'),
    re.compile(r'\b(DCGS|DCGS-A|GBSD|NGEN|DEOS|CES|JADC2|ABMS|ODIN|TITAN)\b', re.IGNORECASE),
    re.compile(r'\b(GDIT|Leidos|SAIC|Northrop|Raytheon|Lockheed|BAE|CACI|ManTech|Peraton)\b', re.IGNORECASE),
    re.compile(r'\b(Langley|PACAF|Wright-Patterson|San Diego|Fort Meade)\b', re.IGNORECASE),
]

# Intent markers for sub-query classification
INTENT_MARKERS = {
    "person": [r'\b(who|contact|manager|director|lead|pm|email|phone)\b'],
    "program": [r'\b(program|contract|award|prime|sub|status)\b'],
    "hiring": [r'\b(hiring|recruiting|open positions?|vacancy|staffing|headcount)\b'],
    "trend": [r'\b(trend|change|growth|decline|over time|historically)\b'],
    "comparison": [r'\b(compare|versus|vs|difference|better|worse)\b'],
    "relationship": [r'\b(connection|relationship|reports to|works with|network)\b'],
    "pain_point": [r'\b(pain point|challenge|issue|concern|problem|struggle)\b'],
}


def _extract_entities(text: str) -> List[str]:
    """Extract named entities from text."""
    entities = set()
    for pattern in ENTITY_PATTERNS:
        for match in pattern.finditer(text):
            name = match.group(0)
            if len(name) > 2:
                entities.add(name)
    return list(entities)


def _classify_sub_intent(text: str) -> str:
    """Classify the intent of a sub-query."""
    for intent, patterns in INTENT_MARKERS.items():
        for p in patterns:
            if re.search(p, text, re.IGNORECASE):
                return intent
    return "general"


def _compute_complexity(query: str) -> float:
    """Compute a complexity score for a query (0-1)."""
    score = 0.0
    # Length factor
    words = len(query.split())
    score += min(words / 30, 0.3)

    # Conjunction count
    conjunctions = len(re.findall(r'\band\b', query, re.IGNORECASE))
    score += min(conjunctions * 0.1, 0.2)

    # Question word count
    q_words = len(re.findall(r'\b(who|what|where|when|how|which|why)\b', query, re.IGNORECASE))
    score += min(q_words * 0.1, 0.2)

    # Comparison markers
    if any(p.search(query) for p in COMPARISON_PATTERNS):
        score += 0.15

    # Temporal markers
    if any(p.search(query) for p in TEMPORAL_PATTERNS):
        score += 0.1

    # Entity count
    entities = _extract_entities(query)
    score += min(len(entities) * 0.05, 0.15)

    return min(score, 1.0)


# =========================================
# QUERY DECOMPOSER
# =========================================

class QueryDecomposer:
    """Break complex queries into atomic sub-queries for parallel retrieval."""

    def __init__(self, complexity_threshold: float = 0.3):
        self.complexity_threshold = complexity_threshold
        self._history: List[DecompositionPlan] = []

    async def decompose(self, query: str) -> DecompositionPlan:
        """Break a complex query into atomic sub-queries."""
        complexity = _compute_complexity(query)

        # If query is simple enough, don't decompose
        if complexity < self.complexity_threshold:
            plan = DecompositionPlan(
                original_query=query,
                sub_queries=[SubQuery(
                    id=uuid.uuid4().hex[:8],
                    text=query,
                    intent=_classify_sub_intent(query),
                    entities=_extract_entities(query),
                    priority=1,
                )],
                is_decomposed=False,
                complexity_score=round(complexity, 4),
                synthesis_strategy="direct",
            )
            self._history.append(plan)
            return plan

        sub_queries = []

        # Strategy 1: Comparison decomposition
        is_comparison = any(p.search(query) for p in COMPARISON_PATTERNS)
        if is_comparison:
            sub_queries.extend(self._decompose_comparison(query))

        # Strategy 2: Multi-aspect decomposition (who + what)
        elif any(p.search(query) for p in MULTI_ASPECT_PATTERNS):
            sub_queries.extend(self._decompose_multi_aspect(query))

        # Strategy 3: Entity-based decomposition
        elif len(_extract_entities(query)) > 1:
            sub_queries.extend(self._decompose_by_entities(query))

        # Strategy 4: Conjunction splitting
        elif any(p.search(query) for p in CONJUNCTION_PATTERNS):
            sub_queries.extend(self._decompose_conjunctions(query))

        # Fallback: single query
        if not sub_queries:
            sub_queries.append(SubQuery(
                id=uuid.uuid4().hex[:8],
                text=query,
                intent=_classify_sub_intent(query),
                entities=_extract_entities(query),
                priority=1,
            ))

        # Determine synthesis strategy
        strategy = "merge"
        if is_comparison:
            strategy = "compare"
        elif any(p.search(query) for p in TEMPORAL_PATTERNS):
            strategy = "aggregate"

        # Build dependency graph
        dep_graph = await self.classify_dependency([sq.text for sq in sub_queries])
        # Map IDs
        dep_graph.nodes = [sq.id for sq in sub_queries]

        plan = DecompositionPlan(
            original_query=query,
            sub_queries=sub_queries,
            dependency_graph=dep_graph,
            is_decomposed=len(sub_queries) > 1,
            complexity_score=round(complexity, 4),
            synthesis_strategy=strategy,
        )
        self._history.append(plan)
        return plan

    async def classify_dependency(
        self, sub_queries: List[str],
    ) -> DependencyGraph:
        """Identify which sub-queries can run in parallel vs. sequentially."""
        n = len(sub_queries)
        if n <= 1:
            return DependencyGraph(
                nodes=list(range(n)),
                parallel_groups=[[0]] if n else [],
                execution_order=[[0]] if n else [],
            )

        # Analyze dependencies: a sub-query depends on another if it
        # references entities that the other one defines
        entities_per_query: List[Set[str]] = []
        for q in sub_queries:
            entities_per_query.append(set(e.lower() for e in _extract_entities(q)))

        edges = []
        # Check for referential dependencies
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                # If query j references entities from query i's output domain
                # This is a simple heuristic — in practice would use LLM
                overlap = entities_per_query[i] & entities_per_query[j]
                # Only create dependency if one query is more specific
                if overlap and len(entities_per_query[i]) < len(entities_per_query[j]):
                    edges.append((i, j))

        # Build parallel groups using topological sorting
        in_degree = [0] * n
        for _, to in edges:
            in_degree[to] += 1

        execution_order = []
        remaining = set(range(n))

        while remaining:
            # Find all nodes with no incoming edges from remaining nodes
            ready = [i for i in remaining if in_degree[i] == 0]
            if not ready:
                # Break cycles by picking arbitrary node
                ready = [min(remaining)]

            execution_order.append(ready)
            for node in ready:
                remaining.discard(node)
                for _, to in edges:
                    if _ == node and to in remaining:
                        in_degree[to] -= 1

        return DependencyGraph(
            nodes=list(range(n)),
            edges=edges,
            parallel_groups=execution_order,
            execution_order=execution_order,
        )

    async def synthesize(
        self, query: str, sub_answers: Dict[str, str],
    ) -> str:
        """Combine sub-query answers into a coherent final answer."""
        if not sub_answers:
            return "No information retrieved for this query."

        if len(sub_answers) == 1:
            return list(sub_answers.values())[0]

        # Build synthesis based on strategy
        parts = []
        for sub_q, answer in sub_answers.items():
            if answer and len(answer.strip()) > 5:
                parts.append(f"**{sub_q}**\n{answer}")

        if not parts:
            return "Could not synthesize a meaningful answer from the sub-query results."

        return "\n\n".join(parts)

    # -----------------------------------------
    # Decomposition strategies
    # -----------------------------------------

    def _decompose_comparison(self, query: str) -> List[SubQuery]:
        """Decompose comparison queries (X vs Y)."""
        sub_queries = []
        entities = _extract_entities(query)

        if len(entities) >= 2:
            # Create a sub-query for each entity
            for i, entity in enumerate(entities[:4]):
                sq = SubQuery(
                    id=uuid.uuid4().hex[:8],
                    text=f"What information is available about {entity}?",
                    intent=_classify_sub_intent(query),
                    entities=[entity],
                    priority=1,
                )
                sub_queries.append(sq)

            # Add a comparative sub-query
            sub_queries.append(SubQuery(
                id=uuid.uuid4().hex[:8],
                text=query,
                intent="comparison",
                entities=entities,
                depends_on=[sq.id for sq in sub_queries],
                priority=2,
            ))
        else:
            # Can't identify entities to compare, treat as single query
            sub_queries.append(SubQuery(
                id=uuid.uuid4().hex[:8],
                text=query,
                intent="comparison",
                entities=entities,
                priority=1,
            ))

        return sub_queries

    def _decompose_multi_aspect(self, query: str) -> List[SubQuery]:
        """Decompose multi-aspect queries (who + what)."""
        sub_queries = []
        # Split on question words
        parts = re.split(r'\b(and|also|plus)\b', query, flags=re.IGNORECASE)
        for part in parts:
            part = part.strip()
            if len(part) > 10 and part.lower() not in {"and", "also", "plus"}:
                sq = SubQuery(
                    id=uuid.uuid4().hex[:8],
                    text=part,
                    intent=_classify_sub_intent(part),
                    entities=_extract_entities(part),
                    priority=1,
                )
                sub_queries.append(sq)
        return sub_queries

    def _decompose_by_entities(self, query: str) -> List[SubQuery]:
        """Decompose by creating per-entity sub-queries."""
        entities = _extract_entities(query)
        sub_queries = []

        # Remove entity names from query to get the "template"
        template = query
        for entity in entities:
            template = template.replace(entity, "{ENTITY}")

        for entity in entities[:5]:
            sq_text = template.replace("{ENTITY}", entity)
            # If template has multiple {ENTITY}, fill all with same entity
            sq_text = sq_text.replace("{ENTITY}", entity)
            sub_queries.append(SubQuery(
                id=uuid.uuid4().hex[:8],
                text=sq_text,
                intent=_classify_sub_intent(query),
                entities=[entity],
                priority=1,
            ))

        return sub_queries

    def _decompose_conjunctions(self, query: str) -> List[SubQuery]:
        """Split on conjunctions (and, as well as, etc.)."""
        # Split on "and" that's not part of a common phrase
        parts = re.split(r'\band\b', query, flags=re.IGNORECASE)
        sub_queries = []
        for part in parts:
            part = part.strip().strip(",").strip()
            if len(part) > 10:
                sub_queries.append(SubQuery(
                    id=uuid.uuid4().hex[:8],
                    text=part,
                    intent=_classify_sub_intent(part),
                    entities=_extract_entities(part),
                    priority=1,
                ))
        return sub_queries

    def get_history(self) -> List[DecompositionPlan]:
        return self._history


# =========================================
# SINGLETON
# =========================================

_decomposer: Optional[QueryDecomposer] = None


def get_query_decomposer() -> QueryDecomposer:
    global _decomposer
    if _decomposer is None:
        _decomposer = QueryDecomposer()
    return _decomposer
