"""Phase 40A — Agentic RAG Orchestrator

AI agent that plans and executes multi-step retrieval strategies.
Implements the analyze → plan → execute → evaluate → adapt/synthesize loop.
"""

import logging
import re
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


# =========================================
# ENUMS
# =========================================


class QueryComplexity(str, Enum):
    SIMPLE = "simple"  # Single fact lookup, 1 round
    MODERATE = "moderate"  # Multi-fact query, 1-2 rounds
    COMPLEX = "complex"  # Multi-hop reasoning, 2-3 rounds
    ANALYTICAL = "analytical"  # Trend/comparison, 3-5 rounds


class RetrievalToolType(str, Enum):
    VECTOR_SEARCH = "vector_search"
    GRAPH_TRAVERSE = "graph_traverse"
    TEMPORAL_QUERY = "temporal_query"
    KEYWORD_SEARCH = "keyword_search"
    SQL_QUERY = "sql_query"
    MEMORY_RECALL = "memory_recall"
    WEB_SEARCH = "web_search"
    DOCUMENT_LOOKUP = "document_lookup"


class AgentState(str, Enum):
    ANALYZE = "analyze"
    PLAN = "plan"
    EXECUTE = "execute"
    EVALUATE = "evaluate"
    ADAPT = "adapt"
    SYNTHESIZE = "synthesize"
    DONE = "done"


# =========================================
# DATA CLASSES
# =========================================


@dataclass
class Citation:
    """A source citation for a piece of information."""

    source_id: str = ""
    source_type: str = ""  # collection name, graph, etc.
    text: str = ""
    relevance_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RetrievalStep:
    """Record of a single retrieval action."""

    step_id: str = ""
    tool: str = ""
    query: str = ""
    results_count: int = 0
    top_score: float = 0.0
    latency_ms: float = 0.0
    iteration: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RetrievalPlan:
    """Planned retrieval strategy for a query."""

    tools: List[str] = field(default_factory=list)
    queries: Dict[str, str] = field(default_factory=dict)  # tool → query
    parallel: bool = True
    max_results_per_tool: int = 10
    quality_threshold: float = 0.7
    max_iterations: int = 3


@dataclass
class EvaluationResult:
    """Result of evaluating retrieved results."""

    relevance_score: float = 0.0
    coverage_score: float = 0.0
    confidence: float = 0.0
    gaps: List[str] = field(default_factory=list)
    sufficient: bool = False


@dataclass
class AgenticRAGResult:
    """Complete result from the agentic RAG pipeline."""

    query_id: str = ""
    answer: str = ""
    confidence: float = 0.0
    citations: List[Citation] = field(default_factory=list)
    retrieval_trace: List[RetrievalStep] = field(default_factory=list)
    iterations: int = 0
    tools_used: List[str] = field(default_factory=list)
    latency_ms: float = 0.0
    tokens_used: int = 0
    complexity: str = QueryComplexity.SIMPLE.value
    state_history: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RetrievalToolResult:
    """Result from a single retrieval tool execution."""

    tool: str = ""
    results: List[Dict[str, Any]] = field(default_factory=list)
    scores: List[float] = field(default_factory=list)
    latency_ms: float = 0.0
    error: str = ""


@dataclass
class OrchestratorState:
    """Full state of the agentic RAG pipeline."""

    query: str = ""
    query_id: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    # Analysis
    intent: str = ""
    entities: List[str] = field(default_factory=list)
    complexity: str = QueryComplexity.SIMPLE.value
    # Planning
    plan: Optional[RetrievalPlan] = None
    # Execution
    tool_results: List[RetrievalToolResult] = field(default_factory=list)
    all_passages: List[Dict[str, Any]] = field(default_factory=list)
    # Evaluation
    evaluation: Optional[EvaluationResult] = None
    # Synthesis
    answer: str = ""
    confidence: float = 0.0
    citations: List[Citation] = field(default_factory=list)
    # Control
    current_state: str = AgentState.ANALYZE.value
    iteration: int = 0
    max_iterations: int = 5
    retrieval_trace: List[RetrievalStep] = field(default_factory=list)
    state_history: List[str] = field(default_factory=list)
    start_time: float = 0.0


# =========================================
# RETRIEVAL TOOL INTERFACE
# =========================================


class RetrievalTool:
    """Base interface for retrieval tools."""

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description

    async def search(
        self, query: str, limit: int = 10, **kwargs
    ) -> RetrievalToolResult:
        """Execute a search with this tool."""
        return RetrievalToolResult(tool=self.name)


class VectorSearchTool(RetrievalTool):
    """Qdrant semantic similarity search."""

    def __init__(self, search_fn: Optional[Callable] = None):
        super().__init__(
            "vector_search", "Qdrant semantic similarity across collections"
        )
        self._search_fn = search_fn

    async def search(
        self, query: str, limit: int = 10, **kwargs
    ) -> RetrievalToolResult:
        start = time.time()
        if self._search_fn:
            try:
                results = await self._search_fn(query, limit=limit, **kwargs)
                return RetrievalToolResult(
                    tool=self.name,
                    results=results if isinstance(results, list) else [results],
                    scores=[r.get("score", 0.5) for r in results]
                    if isinstance(results, list)
                    else [0.5],
                    latency_ms=(time.time() - start) * 1000,
                )
            except Exception as e:
                return RetrievalToolResult(
                    tool=self.name,
                    error=str(e),
                    latency_ms=(time.time() - start) * 1000,
                )
        return RetrievalToolResult(
            tool=self.name, latency_ms=(time.time() - start) * 1000
        )


class GraphTraverseTool(RetrievalTool):
    """Neo4j Cypher relationship queries."""

    def __init__(self, query_fn: Optional[Callable] = None):
        super().__init__(
            "graph_traverse", "Neo4j Cypher for relationship-based queries"
        )
        self._query_fn = query_fn

    async def search(
        self, query: str, limit: int = 10, **kwargs
    ) -> RetrievalToolResult:
        start = time.time()
        if self._query_fn:
            try:
                results = await self._query_fn(query, limit=limit, **kwargs)
                return RetrievalToolResult(
                    tool=self.name,
                    results=results if isinstance(results, list) else [results],
                    scores=[0.8] * (len(results) if isinstance(results, list) else 1),
                    latency_ms=(time.time() - start) * 1000,
                )
            except Exception as e:
                return RetrievalToolResult(
                    tool=self.name,
                    error=str(e),
                    latency_ms=(time.time() - start) * 1000,
                )
        return RetrievalToolResult(
            tool=self.name, latency_ms=(time.time() - start) * 1000
        )


class TemporalQueryTool(RetrievalTool):
    """Temporal KG time-bound queries."""

    def __init__(self, query_fn: Optional[Callable] = None):
        super().__init__("temporal_query", "Temporal KG for time-bound questions")
        self._query_fn = query_fn

    async def search(
        self, query: str, limit: int = 10, **kwargs
    ) -> RetrievalToolResult:
        start = time.time()
        if self._query_fn:
            try:
                results = await self._query_fn(query, limit=limit, **kwargs)
                return RetrievalToolResult(
                    tool=self.name,
                    results=results if isinstance(results, list) else [results],
                    scores=[0.75] * (len(results) if isinstance(results, list) else 1),
                    latency_ms=(time.time() - start) * 1000,
                )
            except Exception as e:
                return RetrievalToolResult(
                    tool=self.name,
                    error=str(e),
                    latency_ms=(time.time() - start) * 1000,
                )
        return RetrievalToolResult(
            tool=self.name, latency_ms=(time.time() - start) * 1000
        )


class KeywordSearchTool(RetrievalTool):
    """BM25 sparse retrieval for exact term matching."""

    def __init__(self, search_fn: Optional[Callable] = None):
        super().__init__(
            "keyword_search", "BM25 sparse retrieval for exact term matching"
        )
        self._search_fn = search_fn

    async def search(
        self, query: str, limit: int = 10, **kwargs
    ) -> RetrievalToolResult:
        start = time.time()
        if self._search_fn:
            try:
                results = await self._search_fn(query, limit=limit, **kwargs)
                return RetrievalToolResult(
                    tool=self.name,
                    results=results if isinstance(results, list) else [results],
                    scores=[r.get("score", 0.5) for r in results]
                    if isinstance(results, list)
                    else [0.5],
                    latency_ms=(time.time() - start) * 1000,
                )
            except Exception as e:
                return RetrievalToolResult(
                    tool=self.name,
                    error=str(e),
                    latency_ms=(time.time() - start) * 1000,
                )
        return RetrievalToolResult(
            tool=self.name, latency_ms=(time.time() - start) * 1000
        )


# =========================================
# QUERY ANALYSIS
# =========================================

# Intent classification patterns
INTENT_PATTERNS = {
    "person_lookup": [
        re.compile(r"\b(who is|contact|email|phone|find)\b", re.IGNORECASE),
        re.compile(r"\b(manager|director|lead|pm)\b.*\b(of|for|at)\b", re.IGNORECASE),
    ],
    "relationship": [
        re.compile(
            r"\b(works at|reports to|manages|connected to|knows)\b", re.IGNORECASE
        ),
        re.compile(r"\b(relationship|connection|network)\b", re.IGNORECASE),
    ],
    "program_intel": [
        re.compile(
            r"\b(program|contract|award|prime|sub)\b.*\b(status|info|detail|update)\b",
            re.IGNORECASE,
        ),
        re.compile(r"\b(dcgs|gbsd|ngen|jadc2|abms)\b", re.IGNORECASE),
    ],
    "hiring": [
        re.compile(
            r"\b(hiring|recruiting|open positions?|vacancy|staffing)\b", re.IGNORECASE
        ),
        re.compile(r"\b(job|role|requisition|headcount)\b", re.IGNORECASE),
    ],
    "trend_analysis": [
        re.compile(
            r"\b(trend|change|growth|decline|compare|comparison)\b", re.IGNORECASE
        ),
        re.compile(
            r"\b(over time|last \d+ months?|year over year|quarterly)\b", re.IGNORECASE
        ),
    ],
    "competitive_intel": [
        re.compile(r"\b(competitor|competing|rival|alternative)\b", re.IGNORECASE),
        re.compile(r"\b(win rate|market share|bid|proposal)\b", re.IGNORECASE),
    ],
}

# Complexity indicators
COMPLEXITY_INDICATORS = {
    "analytical": [
        re.compile(r"\b(compare|trend|analyze|across|between)\b", re.IGNORECASE),
        re.compile(
            r"\b(last \d+ months?|year over year|historically)\b", re.IGNORECASE
        ),
        re.compile(r"\b(forecast|predict|projection)\b", re.IGNORECASE),
    ],
    "complex": [
        re.compile(r"\b(which|how many).*\b(that|who|where)\b", re.IGNORECASE),
        re.compile(r"\b(connection|path|hop)\b", re.IGNORECASE),
        re.compile(r"\band\b.*\band\b", re.IGNORECASE),
    ],
    "moderate": [
        re.compile(r"\b(and|also|with|including)\b", re.IGNORECASE),
        re.compile(r"\b(pain point|challenge|issue|concern)\b", re.IGNORECASE),
    ],
}

# Entity extraction patterns for query understanding
ENTITY_PATTERNS = [
    re.compile(r"\b([A-Z][a-z]+ [A-Z][a-z]+)\b"),  # Person names
    re.compile(
        r"\b(DCGS|DCGS-A|GBSD|NGEN|DEOS|CES|JADC2|ABMS|ODIN|TITAN)\b", re.IGNORECASE
    ),
    re.compile(
        r"\b(GDIT|Leidos|SAIC|Northrop|Raytheon|Lockheed|BAE|CACI|ManTech|Peraton)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(Langley|PACAF|Wright-Patterson|San Diego|Fort Meade)\b", re.IGNORECASE
    ),
]

# Tool selection mapping per intent
INTENT_TOOL_MAP = {
    "person_lookup": [
        RetrievalToolType.VECTOR_SEARCH,
        RetrievalToolType.GRAPH_TRAVERSE,
    ],
    "relationship": [RetrievalToolType.GRAPH_TRAVERSE, RetrievalToolType.VECTOR_SEARCH],
    "program_intel": [
        RetrievalToolType.VECTOR_SEARCH,
        RetrievalToolType.GRAPH_TRAVERSE,
        RetrievalToolType.DOCUMENT_LOOKUP,
    ],
    "hiring": [
        RetrievalToolType.VECTOR_SEARCH,
        RetrievalToolType.TEMPORAL_QUERY,
        RetrievalToolType.KEYWORD_SEARCH,
    ],
    "trend_analysis": [
        RetrievalToolType.TEMPORAL_QUERY,
        RetrievalToolType.VECTOR_SEARCH,
        RetrievalToolType.KEYWORD_SEARCH,
    ],
    "competitive_intel": [
        RetrievalToolType.VECTOR_SEARCH,
        RetrievalToolType.GRAPH_TRAVERSE,
        RetrievalToolType.WEB_SEARCH,
    ],
    "general": [RetrievalToolType.VECTOR_SEARCH, RetrievalToolType.KEYWORD_SEARCH],
}

# Max iterations per complexity
COMPLEXITY_MAX_ITERATIONS = {
    QueryComplexity.SIMPLE.value: 1,
    QueryComplexity.MODERATE.value: 2,
    QueryComplexity.COMPLEX.value: 3,
    QueryComplexity.ANALYTICAL.value: 5,
}


def classify_intent(query: str) -> str:
    """Classify query intent based on patterns."""
    scores: Dict[str, int] = {}
    for intent, patterns in INTENT_PATTERNS.items():
        score = 0
        for p in patterns:
            if p.search(query):
                score += 1
        if score > 0:
            scores[intent] = score

    if not scores:
        return "general"
    return max(scores, key=scores.get)


def classify_complexity(query: str) -> str:
    """Classify query complexity."""
    for level in ["analytical", "complex", "moderate"]:
        for p in COMPLEXITY_INDICATORS[level]:
            if p.search(query):
                return level
    return QueryComplexity.SIMPLE.value


def extract_query_entities(query: str) -> List[str]:
    """Extract named entities from query."""
    entities = []
    for pattern in ENTITY_PATTERNS:
        for match in pattern.finditer(query):
            name = match.group(0)
            if len(name) > 2 and name.lower() not in {
                "the",
                "and",
                "for",
                "who",
                "what",
                "how",
            }:
                entities.append(name)
    return list(set(entities))


# =========================================
# AGENTIC RAG ORCHESTRATOR
# =========================================


class AgenticRAGOrchestrator:
    """AI agent that plans and executes multi-step retrieval strategies."""

    def __init__(
        self,
        tools: Optional[Dict[str, RetrievalTool]] = None,
        quality_threshold: float = 0.7,
        max_iterations: int = 5,
    ):
        self.tools: Dict[str, RetrievalTool] = tools or {}
        self.quality_threshold = quality_threshold
        self.max_iterations = max_iterations
        self._query_history: List[AgenticRAGResult] = []
        self._trace_store: Dict[str, AgenticRAGResult] = {}  # query_id → result
        self._stats = {
            "total_queries": 0,
            "avg_iterations": 0.0,
            "avg_latency_ms": 0.0,
            "complexity_distribution": {},
            "tool_usage": {},
        }

    # -----------------------------------------
    # State machine transitions
    # -----------------------------------------

    def _transition(self, state: OrchestratorState, next_state: str) -> None:
        """Transition to a new state."""
        state.current_state = next_state
        state.state_history.append(next_state)

    def _analyze(self, state: OrchestratorState) -> None:
        """Analyze the query: classify intent, extract entities, assess complexity."""
        state.intent = classify_intent(state.query)
        state.entities = extract_query_entities(state.query)
        state.complexity = classify_complexity(state.query)
        state.max_iterations = COMPLEXITY_MAX_ITERATIONS.get(
            state.complexity,
            self.max_iterations,
        )
        self._transition(state, AgentState.PLAN.value)

    def _plan(self, state: OrchestratorState) -> None:
        """Plan retrieval strategy based on analysis."""
        # Select tools based on intent
        planned_tools = INTENT_TOOL_MAP.get(state.intent, INTENT_TOOL_MAP["general"])

        # Filter to available tools
        available = [t.value for t in planned_tools if t.value in self.tools]
        if not available:
            available = list(self.tools.keys())[:3]

        # Build per-tool queries (can be refined per tool)
        queries = {}
        for tool_name in available:
            queries[tool_name] = state.query

        # Adjust quality threshold by complexity
        quality_map = {
            QueryComplexity.SIMPLE.value: 0.6,
            QueryComplexity.MODERATE.value: 0.65,
            QueryComplexity.COMPLEX.value: 0.7,
            QueryComplexity.ANALYTICAL.value: 0.75,
        }

        state.plan = RetrievalPlan(
            tools=available,
            queries=queries,
            parallel=len(available) > 1,
            max_results_per_tool=10,
            quality_threshold=quality_map.get(state.complexity, self.quality_threshold),
            max_iterations=state.max_iterations,
        )
        self._transition(state, AgentState.EXECUTE.value)

    async def _execute(self, state: OrchestratorState) -> None:
        """Execute planned retrieval steps."""
        if not state.plan:
            self._transition(state, AgentState.SYNTHESIZE.value)
            return

        state.iteration += 1

        for tool_name in state.plan.tools:
            tool = self.tools.get(tool_name)
            if not tool:
                continue

            query_text = state.plan.queries.get(tool_name, state.query)
            start = time.time()
            result = await tool.search(
                query_text, limit=state.plan.max_results_per_tool
            )
            elapsed = (time.time() - start) * 1000

            state.tool_results.append(result)

            # Record trace
            state.retrieval_trace.append(
                RetrievalStep(
                    step_id=uuid.uuid4().hex[:8],
                    tool=tool_name,
                    query=query_text,
                    results_count=len(result.results),
                    top_score=max(result.scores) if result.scores else 0.0,
                    latency_ms=round(elapsed, 2),
                    iteration=state.iteration,
                )
            )

            # Collect passages
            for i, doc in enumerate(result.results):
                passage = {
                    "text": doc.get("text", doc.get("content", str(doc))),
                    "source": tool_name,
                    "score": result.scores[i] if i < len(result.scores) else 0.0,
                    "metadata": doc.get("metadata", {}),
                }
                state.all_passages.append(passage)

        self._transition(state, AgentState.EVALUATE.value)

    def _evaluate(self, state: OrchestratorState) -> None:
        """Evaluate retrieval results quality."""
        if not state.all_passages:
            state.evaluation = EvaluationResult(
                relevance_score=0.0,
                coverage_score=0.0,
                confidence=0.0,
                gaps=["No results retrieved"],
                sufficient=False,
            )
            # If we've exhausted iterations, go to synthesize anyway
            if state.iteration >= state.max_iterations:
                self._transition(state, AgentState.SYNTHESIZE.value)
            else:
                self._transition(state, AgentState.ADAPT.value)
            return

        # Score relevance: average of top passage scores
        scores = sorted([p["score"] for p in state.all_passages], reverse=True)
        top_scores = scores[: min(5, len(scores))]
        relevance = sum(top_scores) / len(top_scores) if top_scores else 0.0

        # Score coverage: check how many entities from the query are mentioned in results
        entity_coverage = 0.0
        if state.entities:
            found = 0
            all_text = " ".join(p.get("text", "") for p in state.all_passages).lower()
            for entity in state.entities:
                if entity.lower() in all_text:
                    found += 1
            entity_coverage = found / len(state.entities)
        else:
            entity_coverage = 1.0 if state.all_passages else 0.0

        # Identify gaps
        gaps = []
        if relevance < 0.5:
            gaps.append("Low relevance scores across retrieved passages")
        if entity_coverage < 0.5:
            missing = [
                e
                for e in state.entities
                if e.lower()
                not in " ".join(p.get("text", "") for p in state.all_passages).lower()
            ]
            gaps.append(f"Missing coverage for entities: {', '.join(missing)}")
        if len(state.all_passages) < 3:
            gaps.append("Too few passages retrieved")

        confidence = relevance * 0.6 + entity_coverage * 0.4
        threshold = (
            state.plan.quality_threshold if state.plan else self.quality_threshold
        )
        sufficient = confidence >= threshold and not gaps

        state.evaluation = EvaluationResult(
            relevance_score=round(relevance, 4),
            coverage_score=round(entity_coverage, 4),
            confidence=round(confidence, 4),
            gaps=gaps,
            sufficient=sufficient,
        )

        if sufficient or state.iteration >= state.max_iterations:
            self._transition(state, AgentState.SYNTHESIZE.value)
        else:
            self._transition(state, AgentState.ADAPT.value)

    def _adapt(self, state: OrchestratorState) -> None:
        """Adapt retrieval strategy based on evaluation gaps."""
        if not state.plan:
            self._transition(state, AgentState.SYNTHESIZE.value)
            return

        # Strategy 1: Try different tools not yet used
        used_tools = {tr.tool for tr in state.retrieval_trace}
        available_new = [t for t in self.tools if t not in used_tools]

        if available_new:
            state.plan.tools = available_new[:2]
            for t in state.plan.tools:
                state.plan.queries[t] = state.query
        else:
            # Strategy 2: Refine queries for existing tools
            # Add entity names to make search more specific
            if state.entities:
                refined = state.query + " " + " ".join(state.entities)
                for t in state.plan.tools:
                    state.plan.queries[t] = refined

        self._transition(state, AgentState.EXECUTE.value)

    def _synthesize(self, state: OrchestratorState) -> None:
        """Synthesize final answer from collected passages."""
        if not state.all_passages:
            state.answer = (
                "I could not find sufficient information to answer this query."
            )
            state.confidence = 0.0
            self._transition(state, AgentState.DONE.value)
            return

        # Sort passages by score
        ranked = sorted(
            state.all_passages, key=lambda p: p.get("score", 0), reverse=True
        )
        top_passages = ranked[:10]

        # Build answer from top passages
        answer_parts = []
        citations = []
        for i, p in enumerate(top_passages):
            text = p.get("text", "")
            if text and len(text) > 10:
                answer_parts.append(text)
                citations.append(
                    Citation(
                        source_id=f"src_{i}",
                        source_type=p.get("source", "unknown"),
                        text=text[:200],
                        relevance_score=p.get("score", 0.0),
                        metadata=p.get("metadata", {}),
                    )
                )

        state.answer = (
            "\n\n".join(answer_parts[:5])
            if answer_parts
            else "No relevant information found."
        )
        state.citations = citations
        state.confidence = state.evaluation.confidence if state.evaluation else 0.0
        self._transition(state, AgentState.DONE.value)

    # -----------------------------------------
    # Main query method
    # -----------------------------------------

    async def query(
        self, question: str, context: Optional[Dict] = None
    ) -> AgenticRAGResult:
        """Process a question through the agentic RAG pipeline."""
        query_id = uuid.uuid4().hex[:12]
        start_time = time.time()

        state = OrchestratorState(
            query=question,
            query_id=query_id,
            context=context or {},
            start_time=start_time,
        )
        state.state_history.append(AgentState.ANALYZE.value)

        # Run state machine
        iteration_limit = self.max_iterations + 2  # safety limit
        steps = 0
        while (
            state.current_state != AgentState.DONE.value and steps < iteration_limit * 6
        ):
            steps += 1
            if state.current_state == AgentState.ANALYZE.value:
                self._analyze(state)
            elif state.current_state == AgentState.PLAN.value:
                self._plan(state)
            elif state.current_state == AgentState.EXECUTE.value:
                await self._execute(state)
            elif state.current_state == AgentState.EVALUATE.value:
                self._evaluate(state)
            elif state.current_state == AgentState.ADAPT.value:
                self._adapt(state)
            elif state.current_state == AgentState.SYNTHESIZE.value:
                self._synthesize(state)

        elapsed_ms = (time.time() - start_time) * 1000
        tools_used = list({tr.tool for tr in state.retrieval_trace})

        result = AgenticRAGResult(
            query_id=query_id,
            answer=state.answer,
            confidence=state.confidence,
            citations=state.citations,
            retrieval_trace=state.retrieval_trace,
            iterations=state.iteration,
            tools_used=tools_used,
            latency_ms=round(elapsed_ms, 2),
            tokens_used=0,
            complexity=state.complexity,
            state_history=state.state_history,
        )

        # Update stats
        self._update_stats(result)
        self._query_history.append(result)
        self._trace_store[query_id] = result

        return result

    async def query_simple(self, question: str) -> AgenticRAGResult:
        """Simple single-round retrieval (no adaptive loop)."""
        query_id = uuid.uuid4().hex[:12]
        start_time = time.time()

        # Direct search with all available tools
        all_passages = []
        trace = []

        for tool_name, tool in list(self.tools.items())[:2]:
            start = time.time()
            result = await tool.search(question, limit=5)
            elapsed = (time.time() - start) * 1000

            trace.append(
                RetrievalStep(
                    step_id=uuid.uuid4().hex[:8],
                    tool=tool_name,
                    query=question,
                    results_count=len(result.results),
                    top_score=max(result.scores) if result.scores else 0.0,
                    latency_ms=round(elapsed, 2),
                    iteration=1,
                )
            )

            for i, doc in enumerate(result.results):
                all_passages.append(
                    {
                        "text": doc.get("text", doc.get("content", str(doc))),
                        "source": tool_name,
                        "score": result.scores[i] if i < len(result.scores) else 0.0,
                    }
                )

        # Build answer
        ranked = sorted(all_passages, key=lambda p: p["score"], reverse=True)[:5]
        answer = (
            "\n\n".join(p["text"] for p in ranked if p.get("text"))
            or "No results found."
        )
        citations = [
            Citation(
                source_id=f"src_{i}",
                source_type=p["source"],
                text=p["text"][:200],
                relevance_score=p["score"],
            )
            for i, p in enumerate(ranked)
        ]

        elapsed_ms = (time.time() - start_time) * 1000
        return AgenticRAGResult(
            query_id=query_id,
            answer=answer,
            confidence=0.7 if ranked else 0.0,
            citations=citations,
            retrieval_trace=trace,
            iterations=1,
            tools_used=list({t.tool for t in trace}),
            latency_ms=round(elapsed_ms, 2),
            complexity=QueryComplexity.SIMPLE.value,
            state_history=["simple_query"],
        )

    def get_trace(self, query_id: str) -> Optional[AgenticRAGResult]:
        """Get full retrieval trace for a query."""
        return self._trace_store.get(query_id)

    def get_stats(self) -> Dict[str, Any]:
        """Get RAG performance statistics."""
        return {**self._stats, "total_queries": len(self._query_history)}

    def get_history(self) -> List[AgenticRAGResult]:
        return self._query_history

    def _update_stats(self, result: AgenticRAGResult) -> None:
        """Update running statistics."""
        n = len(self._query_history)
        if n == 0:
            self._stats["avg_iterations"] = result.iterations
            self._stats["avg_latency_ms"] = result.latency_ms
        else:
            self._stats["avg_iterations"] = (
                self._stats["avg_iterations"] * n + result.iterations
            ) / (n + 1)
            self._stats["avg_latency_ms"] = (
                self._stats["avg_latency_ms"] * n + result.latency_ms
            ) / (n + 1)

        # Complexity distribution
        cd = self._stats["complexity_distribution"]
        cd[result.complexity] = cd.get(result.complexity, 0) + 1

        # Tool usage
        tu = self._stats["tool_usage"]
        for tool in result.tools_used:
            tu[tool] = tu.get(tool, 0) + 1


# =========================================
# BENCHMARK
# =========================================


@dataclass
class BenchmarkResult:
    """Result of running the quality benchmark suite."""

    total_queries: int = 0
    avg_confidence: float = 0.0
    avg_iterations: float = 0.0
    avg_latency_ms: float = 0.0
    complexity_breakdown: Dict[str, Dict[str, float]] = field(default_factory=dict)
    results: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: str = ""


BENCHMARK_QUERIES = [
    {
        "query": "Who is the program manager for DCGS-A?",
        "expected_complexity": "simple",
    },
    {
        "query": "What are the hiring trends at Langley?",
        "expected_complexity": "moderate",
    },
    {
        "query": "Which contacts at Leidos have connections to DCGS program managers?",
        "expected_complexity": "complex",
    },
    {
        "query": "Compare staffing levels at Langley vs PACAF over the last 6 months",
        "expected_complexity": "analytical",
    },
    {"query": "What is Jeff Bartsch's email?", "expected_complexity": "simple"},
    {
        "query": "Who manages DCGS-A and what are their pain points?",
        "expected_complexity": "moderate",
    },
    {
        "query": "What past performance does GDIT have on ISR programs?",
        "expected_complexity": "moderate",
    },
    {
        "query": "How has the competitive landscape changed for DCGS contracts?",
        "expected_complexity": "analytical",
    },
]


async def run_benchmark(orchestrator: AgenticRAGOrchestrator) -> BenchmarkResult:
    """Run the quality benchmark suite."""
    results = []
    total_conf = 0.0
    total_iter = 0
    total_latency = 0.0

    for bq in BENCHMARK_QUERIES:
        r = await orchestrator.query(bq["query"])
        results.append(
            {
                "query": bq["query"],
                "expected_complexity": bq["expected_complexity"],
                "actual_complexity": r.complexity,
                "confidence": r.confidence,
                "iterations": r.iterations,
                "latency_ms": r.latency_ms,
                "tools_used": r.tools_used,
            }
        )
        total_conf += r.confidence
        total_iter += r.iterations
        total_latency += r.latency_ms

    n = len(BENCHMARK_QUERIES)
    return BenchmarkResult(
        total_queries=n,
        avg_confidence=round(total_conf / n, 4) if n else 0.0,
        avg_iterations=round(total_iter / n, 2) if n else 0.0,
        avg_latency_ms=round(total_latency / n, 2) if n else 0.0,
        results=results,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


# =========================================
# SINGLETON
# =========================================

_orchestrator: Optional[AgenticRAGOrchestrator] = None


def get_agentic_rag() -> AgenticRAGOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgenticRAGOrchestrator()
    return _orchestrator
