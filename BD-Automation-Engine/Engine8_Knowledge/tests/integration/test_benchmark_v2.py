"""
Phase 22A — Search Benchmark v2 Tests

Tests golden query set, metrics computation, report export.
Uses mocking — does not require running search backends.
"""

from unittest.mock import MagicMock, patch
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from Engine8_Knowledge.search.benchmark_v2 import (
    SearchBenchmarkV2,
    BenchmarkResult,
    GOLDEN_QUERIES,
    precision_at_k,
    recall_at_k,
    mean_reciprocal_rank,
    ndcg_at_k,
    _is_relevant,
)


# ---------------------------------------------------------------------------
# TestGoldenSet
# ---------------------------------------------------------------------------


class TestGoldenSet:
    """Test golden query set structure."""

    def test_fifty_queries(self):
        assert len(GOLDEN_QUERIES) == 50

    def test_five_categories(self):
        cats = {q["category"] for q in GOLDEN_QUERIES}
        assert cats == {"entity", "relationship", "semantic", "keyword", "multihop"}

    def test_ten_per_category(self):
        for cat in ["entity", "relationship", "semantic", "keyword", "multihop"]:
            count = sum(1 for q in GOLDEN_QUERIES if q["category"] == cat)
            assert count == 10, f"{cat} has {count} queries, expected 10"

    def test_all_have_expected(self):
        for q in GOLDEN_QUERIES:
            assert "query" in q
            assert "expected" in q
            assert "category" in q
            assert len(q["expected"]) > 0


# ---------------------------------------------------------------------------
# TestMetrics
# ---------------------------------------------------------------------------


class TestMetrics:
    """Test metric computation functions."""

    def test_precision_at_5_perfect(self):
        retrieved = ["Alice", "Bob", "Carol", "Dave", "Eve"]
        expected = ["Alice", "Bob", "Carol", "Dave", "Eve"]
        assert precision_at_k(retrieved, expected, 5) == 1.0

    def test_precision_at_5_none(self):
        retrieved = ["X", "Y", "Z", "W", "V"]
        expected = ["Alice", "Bob"]
        assert precision_at_k(retrieved, expected, 5) == 0.0

    def test_precision_at_5_partial(self):
        retrieved = ["Alice is a PM", "Random text", "Bob works at GDIT", "X", "Y"]
        expected = ["Alice", "Bob"]
        p = precision_at_k(retrieved, expected, 5)
        assert p == 0.4  # 2/5

    def test_precision_empty(self):
        assert precision_at_k([], ["A"], 5) == 0.0

    def test_recall_at_10(self):
        retrieved = ["Alice is great", "Bob is here", "X"] + ["Y"] * 7
        expected = ["Alice", "Bob", "Carol"]
        r = recall_at_k(retrieved, expected, 10)
        assert abs(r - 2.0 / 3.0) < 0.01  # Found 2 of 3

    def test_recall_perfect(self):
        retrieved = ["Alice", "Bob"]
        expected = ["Alice", "Bob"]
        assert recall_at_k(retrieved, expected, 10) == 1.0

    def test_mrr_first_result(self):
        retrieved = ["Alice is here", "Bob"]
        expected = ["Alice"]
        assert mean_reciprocal_rank(retrieved, expected) == 1.0

    def test_mrr_second_result(self):
        retrieved = ["X", "Alice is here"]
        expected = ["Alice"]
        assert mean_reciprocal_rank(retrieved, expected) == 0.5

    def test_mrr_not_found(self):
        retrieved = ["X", "Y"]
        expected = ["Alice"]
        assert mean_reciprocal_rank(retrieved, expected) == 0.0

    def test_ndcg_at_10(self):
        retrieved = ["Alice"] + ["X"] * 9
        expected = ["Alice"]
        ndcg = ndcg_at_k(retrieved, expected, 10)
        assert ndcg == 1.0  # Perfect for single relevant at rank 1

    def test_ndcg_empty(self):
        assert ndcg_at_k([], [], 10) == 0.0

    def test_is_relevant_match(self):
        assert _is_relevant("Alice works at Leidos", ["Alice"]) is True

    def test_is_relevant_no_match(self):
        assert _is_relevant("Random text", ["Alice"]) is False

    def test_is_relevant_case_insensitive(self):
        assert _is_relevant("dcgs program details", ["DCGS"]) is True


# ---------------------------------------------------------------------------
# TestBenchmarkRun
# ---------------------------------------------------------------------------


class TestBenchmarkRun:
    """Test benchmark execution."""

    def test_run_benchmark_structure(self):
        from Engine8_Knowledge.search.hybrid_engine import SearchResponse, SearchResult

        mock_search = MagicMock()
        mock_search.search.return_value = SearchResponse(
            results=[
                SearchResult(id="1", content="Alice at DCGS", score=0.9, source="test")
            ],
            mode_used="hybrid",
            search_latency_ms=50,
            total_candidates=10,
            channels_used=["dense"],
        )
        bench = SearchBenchmarkV2(unified_search=mock_search)
        results = bench.run_benchmark(modes=["hybrid"], categories=["entity"])
        assert "hybrid" in results
        br = results["hybrid"]
        assert isinstance(br, BenchmarkResult)
        assert br.total_queries == 10

    def test_run_benchmark_handles_errors(self):
        mock_search = MagicMock()
        mock_search.search.side_effect = Exception("search failed")
        bench = SearchBenchmarkV2(unified_search=mock_search)
        results = bench.run_benchmark(modes=["hybrid"], categories=["entity"])
        # Should not crash
        assert "hybrid" in results

    def test_compare_modes(self):
        bench = SearchBenchmarkV2()
        results = {
            "hybrid": BenchmarkResult(
                mode="hybrid", precision_at_5=0.5, mrr=0.6, ndcg_at_10=0.55
            ),
            "graphrag": BenchmarkResult(
                mode="graphrag", precision_at_5=0.7, mrr=0.8, ndcg_at_10=0.75
            ),
        }
        rows = bench.compare_modes(results)
        assert len(rows) == 2
        assert rows[0]["mode"] == "hybrid"
        assert rows[1]["mode"] == "graphrag"


# ---------------------------------------------------------------------------
# TestReport
# ---------------------------------------------------------------------------


class TestReport:
    """Test report export."""

    def test_export_report(self, tmp_path):
        bench = SearchBenchmarkV2()
        results = {
            "hybrid": BenchmarkResult(
                mode="hybrid",
                precision_at_5=0.5,
                mrr=0.6,
                ndcg_at_10=0.55,
                total_queries=50,
            ),
        }
        path = str(tmp_path / "report.json")
        report = bench.export_report(results, path=path)
        assert "timestamp" in report
        assert "results" in report
        assert "hybrid" in report["results"]
        assert Path(path).exists()

    def test_get_latest_report_none(self):
        bench = SearchBenchmarkV2()
        with patch.object(Path, "exists", return_value=False):
            result = bench.get_latest_report()
        assert result is None
