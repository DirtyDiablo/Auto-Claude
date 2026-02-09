"""
Search Quality Benchmark — Measures retrieval quality with golden test queries.

30 test queries across contacts, programs, and jobs with known-relevant documents.
Metrics: Precision@5, Recall@10, MRR, NDCG@10.
Compares: base_embeddings vs query_expanded vs domain_adapted vs full_pipeline.
"""

import os
import sys
import json
import math
import logging
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

logger = logging.getLogger(__name__)

E8_DATA = Path(__file__).parent.parent / "data"
RESULTS_DIR = E8_DATA / "embeddings"


# ─── Golden test set ──────────────────────────────────────

GOLDEN_QUERIES: List[Dict] = [
    # --- 10 Contact queries ---
    {
        "query": "PACAF site lead for DCGS",
        "category": "contacts",
        "relevant_keywords": ["PACAF", "DCGS", "site lead", "Pacific Air Forces"],
    },
    {
        "query": "FSO at Herndon VA office",
        "category": "contacts",
        "relevant_keywords": ["FSO", "Facility Security Officer", "Herndon"],
    },
    {
        "query": "who manages AF DCGS at Langley",
        "category": "contacts",
        "relevant_keywords": ["AF DCGS", "Langley", "manager", "program manager"],
    },
    {
        "query": "Tier 1 contacts at Leidos working on ISR",
        "category": "contacts",
        "relevant_keywords": ["Tier 1", "Leidos", "ISR", "intelligence surveillance"],
    },
    {
        "query": "GDIT program manager Fort Belvoir",
        "category": "contacts",
        "relevant_keywords": ["GDIT", "program manager", "Fort Belvoir"],
    },
    {
        "query": "Northrop Grumman capture manager GBSD",
        "category": "contacts",
        "relevant_keywords": ["Northrop Grumman", "capture", "GBSD", "Ground Based Strategic Deterrent"],
    },
    {
        "query": "cybersecurity ISSO with TS/SCI clearance",
        "category": "contacts",
        "relevant_keywords": ["ISSO", "cybersecurity", "TS/SCI", "Top Secret"],
    },
    {
        "query": "SAIC systems engineer Wright-Patterson",
        "category": "contacts",
        "relevant_keywords": ["SAIC", "systems engineer", "Wright-Patterson"],
    },
    {
        "query": "BD lead for coalition programs",
        "category": "contacts",
        "relevant_keywords": ["BD", "business development", "coalition"],
    },
    {
        "query": "Raytheon SIGINT program technical lead",
        "category": "contacts",
        "relevant_keywords": ["Raytheon", "SIGINT", "signals intelligence", "technical lead"],
    },
    # --- 10 Program queries ---
    {
        "query": "GDIT Army DCGS contract value",
        "category": "programs",
        "relevant_keywords": ["GDIT", "Army DCGS", "contract", "value"],
    },
    {
        "query": "AF DCGS recompete timeline",
        "category": "programs",
        "relevant_keywords": ["AF DCGS", "recompete", "timeline", "period of performance"],
    },
    {
        "query": "BICES NATO coalition intelligence system",
        "category": "programs",
        "relevant_keywords": ["BICES", "NATO", "coalition", "intelligence"],
    },
    {
        "query": "JSTARS sustainment contract prime contractor",
        "category": "programs",
        "relevant_keywords": ["JSTARS", "sustainment", "prime", "contractor"],
    },
    {
        "query": "ABMS Advanced Battle Management System requirements",
        "category": "programs",
        "relevant_keywords": ["ABMS", "Advanced Battle Management", "requirements"],
    },
    {
        "query": "programs requiring TS/SCI with CI Poly",
        "category": "programs",
        "relevant_keywords": ["TS/SCI", "CI Poly", "clearance"],
    },
    {
        "query": "ISR programs at Fort Meade Maryland",
        "category": "programs",
        "relevant_keywords": ["ISR", "Fort Meade", "Maryland", "intelligence"],
    },
    {
        "query": "DevSecOps cloud migration defense programs",
        "category": "programs",
        "relevant_keywords": ["DevSecOps", "cloud", "migration", "defense"],
    },
    {
        "query": "PTS past performance coalition networks",
        "category": "programs",
        "relevant_keywords": ["PTS", "past performance", "coalition", "networks"],
    },
    {
        "query": "DISA network infrastructure IDIQ",
        "category": "programs",
        "relevant_keywords": ["DISA", "network", "infrastructure", "IDIQ"],
    },
    # --- 10 Job queries ---
    {
        "query": "DCGS network engineer San Diego TS/SCI",
        "category": "jobs",
        "relevant_keywords": ["DCGS", "network engineer", "San Diego", "TS/SCI"],
    },
    {
        "query": "DevSecOps Wright-Patterson Air Force",
        "category": "jobs",
        "relevant_keywords": ["DevSecOps", "Wright-Patterson", "Air Force"],
    },
    {
        "query": "cyber analyst Hampton Roads TS clearance",
        "category": "jobs",
        "relevant_keywords": ["cyber analyst", "Hampton Roads", "TS", "clearance"],
    },
    {
        "query": "systems administrator Fort Meade Linux",
        "category": "jobs",
        "relevant_keywords": ["systems administrator", "Fort Meade", "Linux"],
    },
    {
        "query": "intelligence analyst GEOINT NGA",
        "category": "jobs",
        "relevant_keywords": ["intelligence analyst", "GEOINT", "NGA"],
    },
    {
        "query": "software developer cleared JADC2",
        "category": "jobs",
        "relevant_keywords": ["software developer", "cleared", "JADC2"],
    },
    {
        "query": "project manager GDIT Secret clearance",
        "category": "jobs",
        "relevant_keywords": ["project manager", "GDIT", "Secret"],
    },
    {
        "query": "RF engineer SIGINT collection",
        "category": "jobs",
        "relevant_keywords": ["RF engineer", "SIGINT", "collection"],
    },
    {
        "query": "data scientist machine learning DoD",
        "category": "jobs",
        "relevant_keywords": ["data scientist", "machine learning", "DoD"],
    },
    {
        "query": "cloud architect AWS GovCloud migration",
        "category": "jobs",
        "relevant_keywords": ["cloud architect", "AWS", "GovCloud", "migration"],
    },
]


@dataclass
class QueryResult:
    """Result for a single benchmark query."""
    query: str
    category: str
    precision_at_5: float = 0.0
    recall_at_10: float = 0.0
    mrr: float = 0.0
    ndcg_at_10: float = 0.0
    relevant_found: int = 0
    total_results: int = 0


@dataclass
class BenchmarkResult:
    """Aggregated benchmark results for a search method."""
    method: str
    avg_precision_at_5: float = 0.0
    avg_recall_at_10: float = 0.0
    avg_mrr: float = 0.0
    avg_ndcg_at_10: float = 0.0
    per_query: List[Dict] = field(default_factory=list)
    total_queries: int = 0
    run_at: str = ""


@dataclass
class ComparisonReport:
    """Comparison across multiple search methods."""
    methods: List[Dict] = field(default_factory=list)
    best_method: str = ""
    improvement_pct: float = 0.0
    run_at: str = ""


class SearchBenchmark:
    """
    Benchmarks search quality using golden test queries with known-relevant documents.
    """

    def __init__(self):
        self.queries = GOLDEN_QUERIES

    def _compute_relevance(self, result_text: str, relevant_keywords: List[str]) -> float:
        """Score how relevant a result is based on keyword overlap."""
        text_lower = result_text.lower()
        matched = sum(1 for kw in relevant_keywords if kw.lower() in text_lower)
        return matched / max(1, len(relevant_keywords))

    def _precision_at_k(self, relevance_scores: List[float], k: int = 5) -> float:
        """Precision@K: fraction of top-K results that are relevant."""
        top_k = relevance_scores[:k]
        if not top_k:
            return 0.0
        relevant = sum(1 for s in top_k if s > 0.3)
        return relevant / len(top_k)

    def _recall_at_k(self, relevance_scores: List[float], k: int = 10) -> float:
        """Recall@K: fraction of relevant docs found in top-K."""
        top_k = relevance_scores[:k]
        all_relevant = sum(1 for s in relevance_scores if s > 0.3)
        if all_relevant == 0:
            return 0.0
        found = sum(1 for s in top_k if s > 0.3)
        return found / all_relevant

    def _mrr(self, relevance_scores: List[float]) -> float:
        """Mean Reciprocal Rank: 1/rank of first relevant result."""
        for i, s in enumerate(relevance_scores):
            if s > 0.3:
                return 1.0 / (i + 1)
        return 0.0

    def _ndcg_at_k(self, relevance_scores: List[float], k: int = 10) -> float:
        """NDCG@K: Normalized Discounted Cumulative Gain."""
        top_k = relevance_scores[:k]
        if not top_k:
            return 0.0

        dcg = sum(s / math.log2(i + 2) for i, s in enumerate(top_k))
        ideal = sorted(relevance_scores, reverse=True)[:k]
        idcg = sum(s / math.log2(i + 2) for i, s in enumerate(ideal))

        return dcg / idcg if idcg > 0 else 0.0

    def run_benchmark(
        self,
        search_fn: Callable[[str, int], List[Dict]],
        method_name: str = "default",
    ) -> BenchmarkResult:
        """
        Run benchmark against a search function.

        Args:
            search_fn: Function(query, limit) -> list of dicts with "text" or "content" key
            method_name: Name for this search method

        Returns:
            BenchmarkResult with per-query and aggregated metrics
        """
        result = BenchmarkResult(
            method=method_name,
            total_queries=len(self.queries),
            run_at=datetime.now().isoformat(),
        )

        all_p5 = []
        all_r10 = []
        all_mrr = []
        all_ndcg = []

        for q in self.queries:
            try:
                hits = search_fn(q["query"], 10)
            except Exception as e:
                logger.warning(f"Search error for '{q['query']}': {e}")
                hits = []

            # Score relevance of each result
            relevance_scores = []
            for h in hits:
                text = ""
                if isinstance(h, dict):
                    text = h.get("text", h.get("content", h.get("name", "")))
                elif isinstance(h, str):
                    text = h
                elif hasattr(h, "payload"):
                    text = str(h.payload.get("text", h.payload.get("content", "")))
                relevance_scores.append(self._compute_relevance(str(text), q["relevant_keywords"]))

            p5 = self._precision_at_k(relevance_scores, 5)
            r10 = self._recall_at_k(relevance_scores, 10)
            mrr = self._mrr(relevance_scores)
            ndcg = self._ndcg_at_k(relevance_scores, 10)

            all_p5.append(p5)
            all_r10.append(r10)
            all_mrr.append(mrr)
            all_ndcg.append(ndcg)

            result.per_query.append({
                "query": q["query"],
                "category": q["category"],
                "precision_at_5": round(p5, 4),
                "recall_at_10": round(r10, 4),
                "mrr": round(mrr, 4),
                "ndcg_at_10": round(ndcg, 4),
                "results_returned": len(hits),
            })

        result.avg_precision_at_5 = round(sum(all_p5) / max(1, len(all_p5)), 4)
        result.avg_recall_at_10 = round(sum(all_r10) / max(1, len(all_r10)), 4)
        result.avg_mrr = round(sum(all_mrr) / max(1, len(all_mrr)), 4)
        result.avg_ndcg_at_10 = round(sum(all_ndcg) / max(1, len(all_ndcg)), 4)

        return result

    def compare_methods(self, results: List[BenchmarkResult]) -> ComparisonReport:
        """
        Compare benchmark results across multiple methods.

        Args:
            results: List of BenchmarkResult from different methods

        Returns:
            ComparisonReport with comparison and improvement metrics
        """
        report = ComparisonReport(run_at=datetime.now().isoformat())

        for r in results:
            report.methods.append({
                "method": r.method,
                "precision_at_5": r.avg_precision_at_5,
                "recall_at_10": r.avg_recall_at_10,
                "mrr": r.avg_mrr,
                "ndcg_at_10": r.avg_ndcg_at_10,
            })

        # Find best method by average of all metrics
        best_score = -1
        for m in report.methods:
            avg = (m["precision_at_5"] + m["recall_at_10"] + m["mrr"] + m["ndcg_at_10"]) / 4
            if avg > best_score:
                best_score = avg
                report.best_method = m["method"]

        # Compute improvement of best over worst
        if len(report.methods) >= 2:
            scores = []
            for m in report.methods:
                scores.append((m["precision_at_5"] + m["recall_at_10"] + m["mrr"] + m["ndcg_at_10"]) / 4)
            worst = min(scores)
            best = max(scores)
            report.improvement_pct = round(((best - worst) / max(0.001, worst)) * 100, 1) if worst > 0 else 0

        return report

    def save_results(self, comparison: ComparisonReport):
        """Save benchmark results to disk."""
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        path = RESULTS_DIR / "benchmark_results.json"
        with open(path, "w") as f:
            json.dump(asdict(comparison), f, indent=2)
        logger.info(f"Benchmark results saved to {path}")

    def load_results(self) -> Optional[Dict]:
        """Load latest benchmark results."""
        path = RESULTS_DIR / "benchmark_results.json"
        if path.exists():
            with open(path, "r") as f:
                return json.load(f)
        return None

    def get_golden_queries(self) -> List[Dict]:
        """Get the golden test query set."""
        return [{"query": q["query"], "category": q["category"]} for q in self.queries]
