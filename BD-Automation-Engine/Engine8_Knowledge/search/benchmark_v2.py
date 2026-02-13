"""
Phase 22A — Search Quality Benchmark v2

Expanded benchmark suite with 50 queries across 5 categories.
Compares search modes: vector, hybrid, graph, graphrag.
Computes P@5, P@10, R@10, MRR, NDCG@10, latency.
"""

import json
import math
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

RESULTS_DIR = Path(__file__).parent.parent / "data" / "search"


# ---------------------------------------------------------------------------
# Golden query set
# ---------------------------------------------------------------------------

GOLDEN_QUERIES = [
    # ── Category 1: Entity queries (10) ──
    {"query": "Who is Kingsley Ero?", "expected": ["Kingsley Ero"], "category": "entity"},
    {"query": "What programs does GDIT run?", "expected": ["DCGS", "AF DCGS"], "category": "entity"},
    {"query": "What company is Leidos?", "expected": ["Leidos"], "category": "entity"},
    {"query": "Who works at Northrop Grumman?", "expected": ["Northrop Grumman"], "category": "entity"},
    {"query": "Tell me about SAIC", "expected": ["SAIC"], "category": "entity"},
    {"query": "What is the DCGS program?", "expected": ["DCGS", "Distributed Common Ground System"], "category": "entity"},
    {"query": "Who manages the JSTARS program?", "expected": ["JSTARS"], "category": "entity"},
    {"query": "What is Booz Allen Hamilton?", "expected": ["Booz Allen"], "category": "entity"},
    {"query": "Find contacts at Raytheon", "expected": ["Raytheon"], "category": "entity"},
    {"query": "What programs are in the Army?", "expected": ["Army"], "category": "entity"},

    # ── Category 2: Relationship queries (10) ──
    {"query": "How is David Winkelman connected to DCGS?", "expected": ["David Winkelman", "DCGS"], "category": "relationship"},
    {"query": "What companies compete on DCGS?", "expected": ["DCGS"], "category": "relationship"},
    {"query": "Find introduction path to the DCGS PM", "expected": ["DCGS"], "category": "relationship"},
    {"query": "Who knows someone at Lockheed Martin?", "expected": ["Lockheed"], "category": "relationship"},
    {"query": "What is the relationship between Leidos and SAIC?", "expected": ["Leidos", "SAIC"], "category": "relationship"},
    {"query": "Which programs connect Fort Meade and San Diego?", "expected": ["Fort Meade", "San Diego"], "category": "relationship"},
    {"query": "Who reports to the DCGS program manager?", "expected": ["DCGS"], "category": "relationship"},
    {"query": "How are Northrop and Raytheon connected?", "expected": ["Northrop", "Raytheon"], "category": "relationship"},
    {"query": "What team works on GBSD?", "expected": ["GBSD"], "category": "relationship"},
    {"query": "Find all subcontractors on DCGS", "expected": ["DCGS"], "category": "relationship"},

    # ── Category 3: Semantic queries (10) ──
    {"query": "ISR analyst burnout and retention challenges", "expected": ["ISR", "analyst"], "category": "semantic"},
    {"query": "Cloud migration strategies for defense programs", "expected": ["cloud", "defense"], "category": "semantic"},
    {"query": "Zero trust architecture implementation", "expected": ["zero trust"], "category": "semantic"},
    {"query": "AI/ML applications in intelligence analysis", "expected": ["AI", "ML", "intelligence"], "category": "semantic"},
    {"query": "Modernization challenges for legacy SIGINT systems", "expected": ["SIGINT", "modernization"], "category": "semantic"},
    {"query": "Cybersecurity requirements for classified networks", "expected": ["cybersecurity", "classified"], "category": "semantic"},
    {"query": "Agile software development in DoD programs", "expected": ["agile", "DoD"], "category": "semantic"},
    {"query": "Past performance on ISR programs", "expected": ["ISR", "past performance"], "category": "semantic"},
    {"query": "Digital engineering transformation", "expected": ["digital engineering"], "category": "semantic"},
    {"query": "Multi-domain operations concept of operations", "expected": ["multi-domain"], "category": "semantic"},

    # ── Category 4: Keyword queries (10) ──
    {"query": "TS/SCI CI Poly network engineer", "expected": ["TS/SCI", "network engineer"], "category": "keyword"},
    {"query": "Secret clearance Java developer Fort Meade", "expected": ["Java", "Fort Meade"], "category": "keyword"},
    {"query": "SIGINT analyst TS/SCI San Diego", "expected": ["SIGINT", "San Diego"], "category": "keyword"},
    {"query": "Program manager PMP certification", "expected": ["program manager", "PMP"], "category": "keyword"},
    {"query": "Cybersecurity CISSP Top Secret", "expected": ["CISSP", "Top Secret"], "category": "keyword"},
    {"query": "DevSecOps engineer cloud AWS", "expected": ["DevSecOps", "AWS"], "category": "keyword"},
    {"query": "Full stack developer React Python clearance", "expected": ["React", "Python"], "category": "keyword"},
    {"query": "Systems engineer MBSE DOORS", "expected": ["MBSE", "DOORS"], "category": "keyword"},
    {"query": "Data scientist machine learning TS/SCI", "expected": ["data scientist", "TS/SCI"], "category": "keyword"},
    {"query": "RF engineer electronic warfare", "expected": ["RF", "electronic warfare"], "category": "keyword"},

    # ── Category 5: Multi-hop queries (10) ──
    {"query": "Which company has the most open jobs at DCGS sites?", "expected": ["DCGS"], "category": "multihop"},
    {"query": "Who are Tier 1 contacts at companies priming on ISR programs?", "expected": ["Tier 1", "ISR"], "category": "multihop"},
    {"query": "What clearance do most DCGS contractor positions require?", "expected": ["DCGS", "clearance"], "category": "multihop"},
    {"query": "Which Fort Meade programs have recompetes in 2027?", "expected": ["Fort Meade", "2027"], "category": "multihop"},
    {"query": "Find Tier 1 contacts at Leidos working on Army programs", "expected": ["Leidos", "Army"], "category": "multihop"},
    {"query": "What programs overlap between Northrop and Raytheon in Colorado?", "expected": ["Northrop", "Raytheon", "Colorado"], "category": "multihop"},
    {"query": "Which hiring managers have the most BD interactions?", "expected": ["hiring", "BD"], "category": "multihop"},
    {"query": "Companies with jobs in both San Diego and Fort Meade", "expected": ["San Diego", "Fort Meade"], "category": "multihop"},
    {"query": "Programs losing incumbent contracts in the next 12 months", "expected": ["recompete"], "category": "multihop"},
    {"query": "Contacts who attended meetings about DCGS modernization", "expected": ["DCGS", "modernization"], "category": "multihop"},
]


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def precision_at_k(retrieved: list[str], expected: list[str], k: int) -> float:
    """Precision@K: fraction of top-K results that are relevant."""
    if not expected or k == 0:
        return 0.0
    top_k = retrieved[:k]
    relevant = sum(1 for r in top_k if _is_relevant(r, expected))
    return relevant / k


def recall_at_k(retrieved: list[str], expected: list[str], k: int) -> float:
    """Recall@K: fraction of expected results found in top-K."""
    if not expected:
        return 0.0
    top_k = retrieved[:k]
    found = sum(1 for e in expected if any(_is_relevant(r, [e]) for r in top_k))
    return found / len(expected)


def mean_reciprocal_rank(retrieved: list[str], expected: list[str]) -> float:
    """MRR: 1/rank of first relevant result."""
    for i, r in enumerate(retrieved):
        if _is_relevant(r, expected):
            return 1.0 / (i + 1)
    return 0.0


def ndcg_at_k(retrieved: list[str], expected: list[str], k: int) -> float:
    """Normalized Discounted Cumulative Gain @K."""
    if not expected or k == 0:
        return 0.0
    dcg = 0.0
    for i, r in enumerate(retrieved[:k]):
        rel = 1.0 if _is_relevant(r, expected) else 0.0
        dcg += rel / math.log2(i + 2)
    # Ideal DCG
    ideal_rels = min(len(expected), k)
    idcg = sum(1.0 / math.log2(i + 2) for i in range(ideal_rels))
    return dcg / idcg if idcg > 0 else 0.0


def _is_relevant(result_text: str, expected: list[str]) -> bool:
    """Check if a result text matches any expected term."""
    lower = result_text.lower()
    return any(e.lower() in lower for e in expected)


# ---------------------------------------------------------------------------
# SearchBenchmarkV2
# ---------------------------------------------------------------------------

@dataclass
class BenchmarkResult:
    """Results for a single search mode."""
    mode: str
    precision_at_5: float = 0.0
    precision_at_10: float = 0.0
    recall_at_10: float = 0.0
    mrr: float = 0.0
    ndcg_at_10: float = 0.0
    mean_latency_ms: float = 0.0
    category_scores: dict = field(default_factory=dict)
    total_queries: int = 0
    queries_with_results: int = 0


class SearchBenchmarkV2:
    """Expanded benchmark suite comparing search modes."""

    def __init__(self, unified_search: Optional["UnifiedSearch"] = None) -> None:
        self._search = unified_search
        self.golden_queries = GOLDEN_QUERIES

    @property
    def search(self) -> "UnifiedSearch":
        if self._search is None:
            from Engine8_Knowledge.search.unified_search import get_unified_search
            self._search = get_unified_search()
        return self._search

    def run_benchmark(
        self,
        modes: list[str] | None = None,
        categories: list[str] | None = None,
    ) -> dict[str, BenchmarkResult]:
        """Run all queries across search modes, compute metrics."""
        if modes is None:
            modes = ["vector", "hybrid", "graphrag"]

        queries = self.golden_queries
        if categories:
            queries = [q for q in queries if q["category"] in categories]

        results: dict[str, BenchmarkResult] = {}

        for mode in modes:
            br = BenchmarkResult(mode=mode, total_queries=len(queries))
            cat_scores: dict[str, list[dict]] = {}
            latencies = []

            for gq in queries:
                try:
                    resp = self.search.search(
                        gq["query"], mode=mode, top_k=10, expand_query=False,
                    )
                    retrieved = [r.content for r in resp.results]
                    expected = gq["expected"]

                    p5 = precision_at_k(retrieved, expected, 5)
                    p10 = precision_at_k(retrieved, expected, 10)
                    r10 = recall_at_k(retrieved, expected, 10)
                    mrr = mean_reciprocal_rank(retrieved, expected)
                    ndcg = ndcg_at_k(retrieved, expected, 10)

                    cat = gq["category"]
                    cat_scores.setdefault(cat, []).append({
                        "p5": p5, "p10": p10, "r10": r10, "mrr": mrr, "ndcg": ndcg,
                    })
                    latencies.append(resp.search_latency_ms)

                    if resp.results:
                        br.queries_with_results += 1

                except Exception as e:
                    logger.warning("benchmark_query_error", query=gq["query"][:30], mode=mode, error=str(e)[:80])
                    cat = gq["category"]
                    cat_scores.setdefault(cat, []).append({
                        "p5": 0, "p10": 0, "r10": 0, "mrr": 0, "ndcg": 0,
                    })

            # Aggregate
            all_scores = [s for cat_list in cat_scores.values() for s in cat_list]
            n = len(all_scores) or 1
            br.precision_at_5 = round(sum(s["p5"] for s in all_scores) / n, 4)
            br.precision_at_10 = round(sum(s["p10"] for s in all_scores) / n, 4)
            br.recall_at_10 = round(sum(s["r10"] for s in all_scores) / n, 4)
            br.mrr = round(sum(s["mrr"] for s in all_scores) / n, 4)
            br.ndcg_at_10 = round(sum(s["ndcg"] for s in all_scores) / n, 4)
            br.mean_latency_ms = round(sum(latencies) / max(len(latencies), 1), 1)

            # Per-category
            for cat, scores in cat_scores.items():
                cn = len(scores) or 1
                br.category_scores[cat] = {
                    "p5": round(sum(s["p5"] for s in scores) / cn, 4),
                    "mrr": round(sum(s["mrr"] for s in scores) / cn, 4),
                    "ndcg": round(sum(s["ndcg"] for s in scores) / cn, 4),
                    "count": len(scores),
                }

            results[mode] = br
            logger.info(
                "benchmark_mode_complete", mode=mode,
                p5=br.precision_at_5, mrr=br.mrr, ndcg=br.ndcg_at_10,
                latency=br.mean_latency_ms,
            )

        return results

    def compare_modes(self, results: Optional[dict[str, BenchmarkResult]] = None) -> list[dict]:
        """Side-by-side comparison table."""
        if results is None:
            results = self.run_benchmark()

        rows = []
        for mode, br in results.items():
            rows.append({
                "mode": mode,
                "P@5": br.precision_at_5,
                "P@10": br.precision_at_10,
                "R@10": br.recall_at_10,
                "MRR": br.mrr,
                "NDCG@10": br.ndcg_at_10,
                "Latency (ms)": br.mean_latency_ms,
                "Queries with results": br.queries_with_results,
            })
        return rows

    def export_report(self, results: dict[str, BenchmarkResult], path: Optional[str] = None) -> dict:
        """Export benchmark results to JSON."""
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        report = {
            "timestamp": datetime.now().isoformat(),
            "total_queries": len(self.golden_queries),
            "categories": list({q["category"] for q in self.golden_queries}),
            "results": {},
        }

        for mode, br in results.items():
            report["results"][mode] = {
                "precision_at_5": br.precision_at_5,
                "precision_at_10": br.precision_at_10,
                "recall_at_10": br.recall_at_10,
                "mrr": br.mrr,
                "ndcg_at_10": br.ndcg_at_10,
                "mean_latency_ms": br.mean_latency_ms,
                "queries_with_results": br.queries_with_results,
                "total_queries": br.total_queries,
                "category_scores": br.category_scores,
            }

        # Save JSON
        json_path = path or str(RESULTS_DIR / f"benchmark_v2_{timestamp}.json")
        Path(json_path).write_text(json.dumps(report, indent=2))

        # Save latest pointer
        latest_path = RESULTS_DIR / "benchmark_v2_latest.json"
        latest_path.write_text(json.dumps(report, indent=2))

        logger.info("benchmark_report_exported", path=json_path)
        return report

    def get_latest_report(self) -> Optional[dict]:
        """Load most recent benchmark results."""
        latest = RESULTS_DIR / "benchmark_v2_latest.json"
        if latest.exists():
            return json.loads(latest.read_text())
        return None
