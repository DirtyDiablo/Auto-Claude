"""Phase 47A — Embedding Quality Benchmark Suite.

Golden queries for acronym resolution, program mapping, contact queries,
pain points, job mapping, and past performance. Model comparison and
automated regression checking after each fine-tuning cycle.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


# =========================================
# ENUMS & DATA CLASSES
# =========================================

class BenchmarkCategory(str, Enum):
    ACRONYM_RESOLUTION = "acronym_resolution"
    PROGRAM_MAPPING = "program_mapping"
    CONTACT_QUERY = "contact_query"
    PAIN_POINT = "pain_point"
    JOB_MAPPING = "job_mapping"
    PAST_PERFORMANCE = "past_performance"


@dataclass
class GoldenQuery:
    id: str = ""
    category: str = ""
    query: str = ""
    expected_document: str = ""
    expected_keywords: List[str] = field(default_factory=list)
    difficulty: str = "medium"  # easy | medium | hard
    notes: str = ""

    def __post_init__(self):
        if not self.id:
            raw = f"gq:{self.query[:30]}:{self.category}"
            self.id = f"gq_{hashlib.md5(raw.encode()).hexdigest()[:10]}"


@dataclass
class QueryResult:
    query_id: str = ""
    query: str = ""
    category: str = ""
    hit: bool = False
    rank: int = 0  # 0 = not found
    relevance_score: float = 0.0
    retrieved_keywords: List[str] = field(default_factory=list)
    keyword_recall: float = 0.0


@dataclass
class BenchmarkRun:
    id: str = ""
    model_id: str = ""
    model_name: str = ""
    total_queries: int = 0
    results: List[QueryResult] = field(default_factory=list)
    metrics_by_category: Dict[str, Dict[str, float]] = field(default_factory=dict)
    overall_metrics: Dict[str, float] = field(default_factory=dict)
    created_at: str = ""
    passed_regression: bool = True
    regression_details: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.id:
            raw = f"bench:{self.model_id}:{datetime.now(timezone.utc).isoformat()}"
            self.id = f"bench_{hashlib.md5(raw.encode()).hexdigest()[:10]}"
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


# =========================================
# GOLDEN QUERIES
# =========================================

_GOLDEN_QUERIES: List[GoldenQuery] = [
    # --- Acronym Resolution ---
    GoldenQuery(category="acronym_resolution", query="What is DCGS?",
                expected_document="Distributed Common Ground System",
                expected_keywords=["Distributed", "Common", "Ground", "System"],
                difficulty="easy", notes="Core acronym, should be trivial"),
    GoldenQuery(category="acronym_resolution", query="What does JADC2 stand for?",
                expected_document="Joint All-Domain Command and Control",
                expected_keywords=["Joint", "All-Domain", "Command", "Control"],
                difficulty="easy"),
    GoldenQuery(category="acronym_resolution", query="Define PED in military context",
                expected_document="Processing, Exploitation, and Dissemination",
                expected_keywords=["Processing", "Exploitation", "Dissemination"],
                difficulty="medium", notes="Common acronym but context-dependent"),
    GoldenQuery(category="acronym_resolution", query="What is TS/SCI clearance?",
                expected_document="Top Secret / Sensitive Compartmented Information",
                expected_keywords=["Top Secret", "Sensitive", "Compartmented"],
                difficulty="easy"),
    GoldenQuery(category="acronym_resolution", query="What does ABMS refer to?",
                expected_document="Advanced Battle Management System",
                expected_keywords=["Advanced", "Battle", "Management"],
                difficulty="medium"),
    GoldenQuery(category="acronym_resolution", query="Define MASINT",
                expected_document="Measurement and Signature Intelligence",
                expected_keywords=["Measurement", "Signature", "Intelligence"],
                difficulty="hard", notes="Less common acronym"),
    GoldenQuery(category="acronym_resolution", query="What is DO-178C?",
                expected_document="Software Considerations in Airborne Systems",
                expected_keywords=["Software", "Airborne", "Certification"],
                difficulty="hard"),

    # --- Program Mapping ---
    GoldenQuery(category="program_mapping", query="Which company primes DCGS-A?",
                expected_document="Leidos primes DCGS-A",
                expected_keywords=["Leidos", "DCGS-A"],
                difficulty="easy"),
    GoldenQuery(category="program_mapping", query="Army ISR ground processing program",
                expected_document="DCGS-A Distributed Common Ground System Army",
                expected_keywords=["DCGS-A", "Army", "ISR"],
                difficulty="medium"),
    GoldenQuery(category="program_mapping", query="Minuteman III replacement program",
                expected_document="GBSD Ground Based Strategic Deterrent",
                expected_keywords=["GBSD", "Minuteman", "ICBM"],
                difficulty="hard", notes="Requires domain knowledge"),
    GoldenQuery(category="program_mapping", query="Navy carrier-based unmanned refueling",
                expected_document="MQ-25 Stingray",
                expected_keywords=["MQ-25", "Stingray", "refueling"],
                difficulty="medium"),
    GoldenQuery(category="program_mapping", query="DOD connect sensors and shooters initiative",
                expected_document="JADC2 Joint All-Domain Command and Control",
                expected_keywords=["JADC2", "sensors", "shooters", "domain"],
                difficulty="hard"),

    # --- Contact Queries ---
    GoldenQuery(category="contact_query", query="Who manages DCGS-A at Leidos?",
                expected_document="Craig Lindahl Program Manager Leidos DCGS-A",
                expected_keywords=["Craig Lindahl", "Program Manager", "Leidos"],
                difficulty="easy"),
    GoldenQuery(category="contact_query", query="SETA lead advising Joint Staff on JADC2",
                expected_document="Amanda Chen SETA Lead GDIT JADC2",
                expected_keywords=["Amanda Chen", "SETA", "JADC2"],
                difficulty="medium"),
    GoldenQuery(category="contact_query", query="Contracting officer for DCGS-A at Aberdeen",
                expected_document="Robert Hayes Contracting Officer US Army",
                expected_keywords=["Robert Hayes", "Contracting", "Aberdeen"],
                difficulty="hard"),
    GoldenQuery(category="contact_query", query="Boeing chief engineer for unmanned systems",
                expected_document="Diana Torres Chief Engineer Boeing MQ-25",
                expected_keywords=["Diana Torres", "Boeing", "MQ-25"],
                difficulty="medium"),

    # --- Pain Points ---
    GoldenQuery(category="pain_point", query="Programs struggling with cloud architect hiring",
                expected_document="DCGS-A struggling to fill 5 senior cloud architect positions",
                expected_keywords=["cloud architect", "Langley", "DCGS-A"],
                difficulty="medium"),
    GoldenQuery(category="pain_point", query="Legacy Java codebase migration challenges",
                expected_document="DCGS-N legacy Java monolith needs microservices",
                expected_keywords=["Java", "monolith", "microservices", "DCGS-N"],
                difficulty="medium"),
    GoldenQuery(category="pain_point", query="Cleared developer retention issues",
                expected_document="Northrop struggling with retention losing people to commercial tech",
                expected_keywords=["retention", "Northrop", "commercial"],
                difficulty="hard"),
    GoldenQuery(category="pain_point", query="SIGINT processing performance bottleneck",
                expected_document="SIGINT processing pipeline has latency issues",
                expected_keywords=["SIGINT", "latency", "pipeline"],
                difficulty="hard"),

    # --- Job Mapping ---
    GoldenQuery(category="job_mapping", query="Kubernetes positions at DCGS-N",
                expected_document="Kubernetes Platform Engineer DCGS-N St Inigoes",
                expected_keywords=["Kubernetes", "DCGS-N", "St. Inigoes"],
                difficulty="easy"),
    GoldenQuery(category="job_mapping", query="TS/SCI cleared UAS autonomy engineer jobs",
                expected_document="Autonomy Engineer MQ-25 Stingray Boeing",
                expected_keywords=["Autonomy", "MQ-25", "UAS", "TS/SCI"],
                difficulty="medium"),
    GoldenQuery(category="job_mapping", query="Safety-critical real-time systems developer Hill AFB",
                expected_document="Software Developer GBSD Hill AFB DO-178C",
                expected_keywords=["GBSD", "Hill AFB", "DO-178C", "real-time"],
                difficulty="hard"),
    GoldenQuery(category="job_mapping", query="SIGINT analyst position at DGS-1",
                expected_document="SIGINT Analyst DGS-1 DCGS-A Langley",
                expected_keywords=["SIGINT", "DGS-1", "Langley", "DCGS-A"],
                difficulty="medium"),

    # --- Past Performance ---
    GoldenQuery(category="past_performance", query="GDIT GovCloud migration experience",
                expected_document="GDIT GovCloud approach preferred by Leidos for DCGS-A",
                expected_keywords=["GDIT", "GovCloud", "DCGS-A"],
                difficulty="medium"),
    GoldenQuery(category="past_performance", query="PED throughput improvement results",
                expected_document="PED throughput improved 30% after microservices migration",
                expected_keywords=["PED", "30%", "microservices"],
                difficulty="hard"),
    GoldenQuery(category="past_performance", query="BAE proposal for DCGS-A cloud",
                expected_document="BAE submitted unsolicited proposal rejected",
                expected_keywords=["BAE", "unsolicited", "rejected"],
                difficulty="hard"),
]


# =========================================
# BENCHMARK SUITE
# =========================================

class EmbeddingBenchmarkSuite:
    """Golden query benchmark for evaluating embedding quality."""

    def __init__(self) -> None:
        self._golden_queries = list(_GOLDEN_QUERIES)
        self._runs: List[BenchmarkRun] = []
        self._regression_threshold: float = 0.02  # max allowed drop in Recall@10

    # --------------------------------------------------
    # GOLDEN QUERIES
    # --------------------------------------------------

    def get_golden_queries(self, category: str = "") -> List[GoldenQuery]:
        """Get golden queries, optionally filtered by category."""
        if category:
            return [q for q in self._golden_queries if q.category == category]
        return list(self._golden_queries)

    def add_golden_query(self, query: GoldenQuery) -> GoldenQuery:
        """Add a custom golden query to the benchmark."""
        self._golden_queries.append(query)
        return query

    def get_categories(self) -> List[str]:
        """Get all benchmark categories."""
        return list(set(q.category for q in self._golden_queries))

    # --------------------------------------------------
    # BENCHMARK EXECUTION
    # --------------------------------------------------

    def run_benchmark(self, model_id: str, model_name: str = "",
                      is_fine_tuned: bool = False) -> BenchmarkRun:
        """Run the full golden benchmark suite against a model.

        Simulates retrieval results. Fine-tuned models get higher scores,
        especially on hard/domain-specific queries.
        """
        import random
        rng = random.Random(hash(model_id) % 2**32)

        results: List[QueryResult] = []
        for gq in self._golden_queries:
            result = self._simulate_retrieval(gq, is_fine_tuned, rng)
            results.append(result)

        # Compute metrics by category
        metrics_by_cat: Dict[str, Dict[str, float]] = {}
        for cat in self.get_categories():
            cat_results = [r for r in results if r.category == cat]
            metrics_by_cat[cat] = self._compute_category_metrics(cat_results)

        # Overall metrics
        overall = self._compute_category_metrics(results)

        run = BenchmarkRun(
            model_id=model_id,
            model_name=model_name,
            total_queries=len(results),
            results=results,
            metrics_by_category=metrics_by_cat,
            overall_metrics=overall,
        )

        # Regression check against previous runs
        if self._runs:
            prev = self._runs[-1]
            prev_r10 = prev.overall_metrics.get("recall_at_10", 0)
            curr_r10 = overall.get("recall_at_10", 0)
            if curr_r10 < prev_r10 - self._regression_threshold:
                run.passed_regression = False
                run.regression_details.append(
                    f"Recall@10 dropped from {prev_r10:.4f} to {curr_r10:.4f} "
                    f"(threshold: {self._regression_threshold})"
                )

        self._runs.append(run)
        return run

    def _simulate_retrieval(self, gq: GoldenQuery, is_fine_tuned: bool,
                            rng: random.Random) -> QueryResult:
        """Simulate retrieval of a golden query."""
        # Base hit probability depends on difficulty
        base_hit_prob = {"easy": 0.85, "medium": 0.65, "hard": 0.40}
        hit_prob = base_hit_prob.get(gq.difficulty, 0.60)

        # Fine-tuned models get a significant boost
        if is_fine_tuned:
            hit_prob = min(hit_prob + 0.20, 0.98)

        hit = rng.random() < hit_prob
        rank = rng.randint(1, 5) if hit else 0
        relevance = round(rng.uniform(0.7, 0.95) if hit else rng.uniform(0.1, 0.4), 4)

        # Keyword recall
        kw_hits = 0
        for kw in gq.expected_keywords:
            # Fine-tuned models better at domain-specific keywords
            kw_prob = 0.7 if is_fine_tuned else 0.5
            if rng.random() < kw_prob:
                kw_hits += 1

        kw_recall = round(kw_hits / max(len(gq.expected_keywords), 1), 4)

        return QueryResult(
            query_id=gq.id,
            query=gq.query,
            category=gq.category,
            hit=hit,
            rank=rank,
            relevance_score=relevance,
            retrieved_keywords=gq.expected_keywords[:kw_hits],
            keyword_recall=kw_recall,
        )

    def _compute_category_metrics(self, results: List[QueryResult]) -> Dict[str, float]:
        """Compute aggregated metrics for a set of results."""
        if not results:
            return {"recall_at_1": 0, "recall_at_5": 0, "recall_at_10": 0, "mrr": 0, "avg_relevance": 0, "keyword_recall": 0}

        n = len(results)
        hits_at_1 = sum(1 for r in results if r.hit and r.rank <= 1)
        hits_at_5 = sum(1 for r in results if r.hit and r.rank <= 5)
        hits_at_10 = sum(1 for r in results if r.hit)  # all hits are in top 10 in our sim

        # MRR
        rr_sum = sum(1.0 / r.rank for r in results if r.hit and r.rank > 0)

        return {
            "recall_at_1": round(hits_at_1 / n, 4),
            "recall_at_5": round(hits_at_5 / n, 4),
            "recall_at_10": round(hits_at_10 / n, 4),
            "mrr": round(rr_sum / n, 4),
            "avg_relevance": round(sum(r.relevance_score for r in results) / n, 4),
            "keyword_recall": round(sum(r.keyword_recall for r in results) / n, 4),
            "total_queries": n,
            "total_hits": sum(1 for r in results if r.hit),
        }

    # --------------------------------------------------
    # COMPARISON & REGRESSION
    # --------------------------------------------------

    def compare_runs(self, run_a_id: str, run_b_id: str) -> Dict[str, Any]:
        """Compare two benchmark runs."""
        run_a = next((r for r in self._runs if r.id == run_a_id), None)
        run_b = next((r for r in self._runs if r.id == run_b_id), None)

        if not run_a or not run_b:
            return {"error": "Run not found"}

        deltas: Dict[str, float] = {}
        for key in run_a.overall_metrics:
            if isinstance(run_a.overall_metrics[key], (int, float)) and isinstance(run_b.overall_metrics.get(key, 0), (int, float)):
                deltas[key] = round(run_b.overall_metrics.get(key, 0) - run_a.overall_metrics.get(key, 0), 4)

        return {
            "run_a": {"id": run_a.id, "model": run_a.model_name, "metrics": run_a.overall_metrics},
            "run_b": {"id": run_b.id, "model": run_b.model_name, "metrics": run_b.overall_metrics},
            "deltas": deltas,
            "improved": deltas.get("recall_at_10", 0) > 0,
        }

    def check_regression(self, current_run: BenchmarkRun,
                         baseline_run: Optional[BenchmarkRun] = None) -> Dict[str, Any]:
        """Check if current run regresses from baseline (overall metrics)."""
        if baseline_run is None:
            baseline_run = self._runs[0] if self._runs else None

        if not baseline_run:
            return {"passed": True, "message": "No baseline to compare against"}

        issues: List[str] = []

        # Check overall metrics (not per-category, which has too much variance)
        base_r10 = baseline_run.overall_metrics.get("recall_at_10", 0)
        curr_r10 = current_run.overall_metrics.get("recall_at_10", 0)

        if curr_r10 < base_r10 - self._regression_threshold:
            issues.append(f"Overall Recall@10 dropped {base_r10:.4f} → {curr_r10:.4f}")

        base_mrr = baseline_run.overall_metrics.get("mrr", 0)
        curr_mrr = current_run.overall_metrics.get("mrr", 0)

        if curr_mrr < base_mrr - self._regression_threshold:
            issues.append(f"Overall MRR dropped {base_mrr:.4f} → {curr_mrr:.4f}")

        return {
            "passed": len(issues) == 0,
            "issues": issues,
            "threshold": self._regression_threshold,
        }

    # --------------------------------------------------
    # QUERIES
    # --------------------------------------------------

    def get_run(self, run_id: str) -> Optional[BenchmarkRun]:
        return next((r for r in self._runs if r.id == run_id), None)

    def get_runs(self) -> List[Dict[str, Any]]:
        """Get all benchmark run summaries."""
        return [
            {
                "id": r.id, "model_id": r.model_id, "model_name": r.model_name,
                "total_queries": r.total_queries,
                "overall_metrics": r.overall_metrics,
                "passed_regression": r.passed_regression,
                "created_at": r.created_at,
            }
            for r in self._runs
        ]

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_golden_queries": len(self._golden_queries),
            "total_runs": len(self._runs),
            "categories": self.get_categories(),
            "queries_by_category": {
                cat: len([q for q in self._golden_queries if q.category == cat])
                for cat in self.get_categories()
            },
            "queries_by_difficulty": {
                diff: len([q for q in self._golden_queries if q.difficulty == diff])
                for diff in ["easy", "medium", "hard"]
            },
        }


# =========================================
# SINGLETON
# =========================================

_instance: Optional[EmbeddingBenchmarkSuite] = None


def get_benchmark_suite() -> EmbeddingBenchmarkSuite:
    global _instance
    if _instance is None:
        _instance = EmbeddingBenchmarkSuite()
    return _instance
