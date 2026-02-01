"""
UltraRAG - Multi-Step Reasoning RAG Pipeline
Handles complex queries through decomposition and iterative refinement.
"""
import yaml
import json
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import asyncio
import time


class RetrievalStrategy(Enum):
    VECTOR = "vector"
    BM25 = "bm25"
    HYBRID = "hybrid"
    PAGEINDEX = "pageindex"
    KNOWLEDGE_GRAPH = "knowledge_graph"


class ReasoningStep(Enum):
    DECOMPOSE = "decompose"       # Break complex query into sub-queries
    RETRIEVE = "retrieve"         # Fetch relevant information
    SYNTHESIZE = "synthesize"     # Combine retrieved information
    VERIFY = "verify"             # Self-check the answer
    REFINE = "refine"             # Improve the answer
    CITE = "cite"                 # Add citations


@dataclass
class QueryPlan:
    """Execution plan for a complex query."""
    original_query: str
    sub_queries: List[str] = field(default_factory=list)
    steps: List[Dict] = field(default_factory=list)
    intermediate_results: Dict = field(default_factory=dict)
    final_answer: Optional[str] = None
    citations: List[Dict] = field(default_factory=list)
    confidence: float = 0.0
    execution_time_ms: int = 0
    pipeline_used: str = "simple"


@dataclass
class PipelineConfig:
    """Configuration for UltraRAG pipeline."""
    max_iterations: int = 3
    min_confidence: float = 0.7
    parallel_retrieval: bool = True
    self_reflection: bool = True
    citation_required: bool = True
    strategies: List[RetrievalStrategy] = field(
        default_factory=lambda: [RetrievalStrategy.HYBRID]
    )


class UltraRAG:
    """
    Multi-step reasoning RAG with configurable pipelines.
    """

    def __init__(self,
                 retriever_func: Callable,
                 llm_func: Callable = None,
                 config: PipelineConfig = None):
        """
        Args:
            retriever_func: Function(query, strategy, top_k, collection) -> List[Dict]
            llm_func: Function(prompt) -> str (optional, for reasoning)
            config: Pipeline configuration
        """
        self.retrieve = retriever_func
        self.llm = llm_func
        self.config = config or PipelineConfig()
        self.pipelines = {}
        self._load_default_pipelines()

    def _load_default_pipelines(self):
        """Load default reasoning pipelines."""

        # Simple query pipeline
        self.pipelines["simple"] = {
            "name": "Simple Retrieval",
            "steps": [
                {"type": "retrieve", "strategy": "hybrid", "top_k": 5},
                {"type": "synthesize"},
                {"type": "cite"}
            ]
        }

        # Complex query pipeline (decomposition)
        self.pipelines["complex"] = {
            "name": "Complex Query Decomposition",
            "steps": [
                {"type": "decompose", "max_sub_queries": 3},
                {"type": "retrieve", "strategy": "hybrid", "top_k": 3, "parallel": True},
                {"type": "synthesize"},
                {"type": "verify"},
                {"type": "refine", "condition": "confidence < 0.7"},
                {"type": "cite"}
            ]
        }

        # Fact-checking pipeline
        self.pipelines["factcheck"] = {
            "name": "Fact Verification",
            "steps": [
                {"type": "retrieve", "strategy": "pageindex", "top_k": 10},
                {"type": "verify", "strict": True},
                {"type": "cite", "required": True}
            ]
        }

        # Multi-source pipeline
        self.pipelines["multisource"] = {
            "name": "Multi-Source Aggregation",
            "steps": [
                {"type": "retrieve", "strategy": "vector", "top_k": 5},
                {"type": "retrieve", "strategy": "bm25", "top_k": 5},
                {"type": "retrieve", "strategy": "knowledge_graph", "top_k": 5},
                {"type": "synthesize", "mode": "merge_dedupe"},
                {"type": "verify"},
                {"type": "cite"}
            ]
        }

        # BD-specific pipeline
        self.pipelines["bd_intelligence"] = {
            "name": "BD Intelligence Analysis",
            "steps": [
                {"type": "decompose", "template": "bd_query"},
                {"type": "retrieve", "strategy": "hybrid", "collection": "programs", "top_k": 3},
                {"type": "retrieve", "strategy": "hybrid", "collection": "contacts", "top_k": 5},
                {"type": "retrieve", "strategy": "hybrid", "collection": "jobs", "top_k": 5},
                {"type": "synthesize", "mode": "bd_report"},
                {"type": "verify"},
                {"type": "cite"}
            ]
        }

    def load_pipeline_from_yaml(self, yaml_path: str) -> str:
        """Load a custom pipeline from YAML file."""
        with open(yaml_path) as f:
            pipeline = yaml.safe_load(f)

        pipeline_id = pipeline.get("id", yaml_path)
        self.pipelines[pipeline_id] = pipeline
        return pipeline_id

    def add_pipeline(self, pipeline_id: str, name: str, steps: List[Dict]) -> None:
        """Add a custom pipeline programmatically."""
        self.pipelines[pipeline_id] = {
            "name": name,
            "steps": steps
        }

    def _classify_query(self, query: str) -> str:
        """Classify query complexity to select appropriate pipeline."""
        query_lower = query.lower()

        # BD-specific queries
        bd_keywords = ["program", "contract", "contractor", "contact", "dcgs", "gdit", "opportunity"]
        if any(kw in query_lower for kw in bd_keywords):
            return "bd_intelligence"

        # Complex queries (multiple questions, comparisons)
        complex_indicators = ["compare", "difference between", "how does", "why", "analyze", "relationship"]
        if any(ind in query_lower for ind in complex_indicators):
            return "complex"

        # Fact-checking queries
        fact_indicators = ["is it true", "verify", "fact check", "according to", "source"]
        if any(ind in query_lower for ind in fact_indicators):
            return "factcheck"

        # Default to simple
        return "simple"

    def _decompose_query(self, query: str, max_sub: int = 3, template: str = None) -> List[str]:
        """Break a complex query into sub-queries."""
        if not self.llm:
            # Simple heuristic decomposition
            sub_queries = [query]

            # Split on conjunctions
            for conj in [" and ", " also ", " additionally "]:
                if conj in query.lower():
                    parts = query.lower().split(conj)
                    sub_queries = [p.strip() for p in parts if p.strip()]
                    break

            return sub_queries[:max_sub]

        # Use LLM for intelligent decomposition
        prompt = f"""Decompose this complex question into {max_sub} simpler sub-questions that can be answered independently.

Question: {query}

Return as JSON array: ["sub_question_1", "sub_question_2", ...]"""

        response = self.llm(prompt)
        try:
            return json.loads(response)[:max_sub]
        except:
            return [query]

    async def _execute_step(self,
                           step: Dict,
                           plan: QueryPlan,
                           context: Dict) -> Dict:
        """Execute a single pipeline step."""
        step_type = step.get("type")
        result = {"step": step_type, "success": False}

        if step_type == "decompose":
            sub_queries = self._decompose_query(
                plan.original_query,
                step.get("max_sub_queries", 3),
                step.get("template")
            )
            plan.sub_queries = sub_queries
            result["sub_queries"] = sub_queries
            result["success"] = True

        elif step_type == "retrieve":
            strategy = step.get("strategy", "hybrid")
            top_k = step.get("top_k", 5)
            collection = step.get("collection")

            # Retrieve for each sub-query (or original if no decomposition)
            queries = plan.sub_queries if plan.sub_queries else [plan.original_query]

            all_results = []
            for q in queries:
                try:
                    results = self.retrieve(q, strategy=strategy, top_k=top_k, collection=collection)
                    if results:
                        all_results.extend(results)
                except Exception as e:
                    result["error"] = str(e)

            # Store in intermediate results
            key = f"retrieve_{strategy}_{collection or 'all'}"
            plan.intermediate_results[key] = all_results
            result["num_results"] = len(all_results)
            result["success"] = True

        elif step_type == "synthesize":
            mode = step.get("mode", "default")

            # Gather all retrieved results
            all_retrieved = []
            for key, value in plan.intermediate_results.items():
                if key.startswith("retrieve_"):
                    all_retrieved.extend(value)

            # Deduplicate
            seen = set()
            unique_results = []
            for r in all_retrieved:
                r_id = r.get("id") or r.get("content", "")[:100]
                if r_id not in seen:
                    seen.add(r_id)
                    unique_results.append(r)

            plan.intermediate_results["synthesized"] = unique_results

            # Generate answer
            if self.llm and unique_results:
                context_text = "\n\n".join([
                    f"[{i+1}] {r.get('content', r.get('text', str(r)))[:500]}"
                    for i, r in enumerate(unique_results[:10])
                ])

                prompt = f"""Based on the following information, answer the question.

Question: {plan.original_query}

Information:
{context_text}

Answer:"""

                plan.final_answer = self.llm(prompt)
            else:
                plan.final_answer = f"Found {len(unique_results)} relevant results."

            result["success"] = True

        elif step_type == "verify":
            # Self-reflection step
            if self.llm and plan.final_answer:
                prompt = f"""Verify if this answer correctly addresses the question.

Question: {plan.original_query}
Answer: {plan.final_answer}

Rate confidence (0.0-1.0) and identify any issues:
{{"confidence": X.X, "issues": ["issue1", ...], "verified": true/false}}"""

                try:
                    verification = json.loads(self.llm(prompt))
                    plan.confidence = verification.get("confidence", 0.5)
                    result["verification"] = verification
                except:
                    plan.confidence = 0.5
            else:
                plan.confidence = 0.5

            result["success"] = True

        elif step_type == "refine":
            condition = step.get("condition", "")

            # Check condition
            should_refine = False
            if "confidence <" in condition:
                threshold = float(condition.split("<")[1].strip())
                should_refine = plan.confidence < threshold

            if should_refine and self.llm:
                prompt = f"""Improve this answer to be more accurate and complete.

Question: {plan.original_query}
Current Answer: {plan.final_answer}
Issues: Low confidence

Improved Answer:"""

                plan.final_answer = self.llm(prompt)
                plan.confidence = min(plan.confidence + 0.1, 0.9)

            result["refined"] = should_refine
            result["success"] = True

        elif step_type == "cite":
            # Extract citations from retrieved results
            synthesized = plan.intermediate_results.get("synthesized", [])

            citations = []
            for r in synthesized[:5]:
                citations.append({
                    "source": r.get("source", r.get("document_name", "Unknown")),
                    "excerpt": r.get("content", r.get("text", ""))[:200],
                    "score": r.get("score", 0)
                })

            plan.citations = citations
            result["num_citations"] = len(citations)
            result["success"] = True

        return result

    async def query(self,
                   query: str,
                   pipeline: str = "auto") -> QueryPlan:
        """
        Execute a query through the reasoning pipeline.

        Args:
            query: The user's question
            pipeline: Pipeline ID or "auto" for automatic selection

        Returns:
            QueryPlan with final answer and all intermediate results
        """
        start_time = time.time()

        # Select pipeline
        if pipeline == "auto":
            pipeline = self._classify_query(query)

        if pipeline not in self.pipelines:
            pipeline = "simple"

        pipeline_config = self.pipelines[pipeline]

        # Initialize query plan
        plan = QueryPlan(original_query=query)
        plan.steps = pipeline_config.get("steps", [])
        plan.pipeline_used = pipeline

        context = {}

        # Execute steps
        for step in plan.steps:
            step_result = await self._execute_step(step, plan, context)
            context[step.get("type")] = step_result

        plan.execution_time_ms = int((time.time() - start_time) * 1000)

        return plan

    def query_sync(self, query: str, pipeline: str = "auto") -> QueryPlan:
        """Synchronous wrapper for query()."""
        try:
            loop = asyncio.get_running_loop()
            # If there's a running loop, create a new thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, self.query(query, pipeline))
                return future.result()
        except RuntimeError:
            # No running loop, safe to use asyncio.run
            return asyncio.run(self.query(query, pipeline))

    def list_pipelines(self) -> List[Dict]:
        """List all available pipelines."""
        return [
            {
                "id": pid,
                "name": p.get("name", pid),
                "steps": len(p.get("steps", []))
            }
            for pid, p in self.pipelines.items()
        ]


# Pipeline YAML template
PIPELINE_TEMPLATE = """
# Custom UltraRAG Pipeline
# Save as: pipelines/my_pipeline.yaml

id: my_custom_pipeline
name: My Custom Pipeline
description: Example custom pipeline for specific use case

steps:
  - type: decompose
    max_sub_queries: 3
    template: null  # Use default

  - type: retrieve
    strategy: hybrid  # vector, bm25, hybrid, pageindex, knowledge_graph
    collection: null  # null = all collections
    top_k: 5
    parallel: true

  - type: synthesize
    mode: default  # default, merge_dedupe, bd_report

  - type: verify
    strict: false

  - type: refine
    condition: "confidence < 0.7"
    max_iterations: 2

  - type: cite
    required: true
    min_citations: 1
"""
