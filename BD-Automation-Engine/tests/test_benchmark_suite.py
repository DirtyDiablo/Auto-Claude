"""Tests for Phase 47A — Embedding Quality Benchmark Suite."""

import pytest

from src.embeddings.benchmark_suite import (
    EmbeddingBenchmarkSuite,
    GoldenQuery,
    BenchmarkRun,
    QueryResult,
    BenchmarkCategory,
    get_benchmark_suite,
)


@pytest.fixture
def bench():
    return EmbeddingBenchmarkSuite()


# =========================================
# GOLDEN QUERIES
# =========================================

def test_golden_queries_loaded(bench):
    queries = bench.get_golden_queries()
    assert len(queries) >= 25  # we defined 27 golden queries


def test_golden_queries_have_ids(bench):
    for q in bench.get_golden_queries():
        assert q.id.startswith("gq_")


def test_golden_queries_all_categories(bench):
    categories = bench.get_categories()
    assert "acronym_resolution" in categories
    assert "program_mapping" in categories
    assert "contact_query" in categories
    assert "pain_point" in categories
    assert "job_mapping" in categories
    assert "past_performance" in categories


def test_filter_by_category(bench):
    acronym_qs = bench.get_golden_queries(category="acronym_resolution")
    assert len(acronym_qs) >= 5
    assert all(q.category == "acronym_resolution" for q in acronym_qs)


def test_golden_query_structure(bench):
    for q in bench.get_golden_queries():
        assert q.query != ""
        assert q.expected_document != ""
        assert len(q.expected_keywords) >= 1
        assert q.difficulty in ("easy", "medium", "hard")


def test_add_custom_golden_query(bench):
    before = len(bench.get_golden_queries())
    gq = GoldenQuery(
        category="custom",
        query="What is SOCOM?",
        expected_document="Special Operations Command",
        expected_keywords=["SOCOM", "Special Operations"],
        difficulty="easy",
    )
    bench.add_golden_query(gq)
    assert len(bench.get_golden_queries()) == before + 1


# =========================================
# BENCHMARK EXECUTION
# =========================================

def test_run_benchmark_baseline(bench):
    run = bench.run_benchmark("baseline_001", "all-MiniLM-L6-v2", is_fine_tuned=False)
    assert isinstance(run, BenchmarkRun)
    assert run.id.startswith("bench_")
    assert run.total_queries >= 25


def test_run_benchmark_fine_tuned(bench):
    run = bench.run_benchmark("ft_001", "bd-embed-v1", is_fine_tuned=True)
    assert run.total_queries >= 25
    assert run.overall_metrics["recall_at_10"] > 0


def test_fine_tuned_beats_baseline(bench):
    baseline = bench.run_benchmark("baseline_001", "baseline", is_fine_tuned=False)
    fine_tuned = bench.run_benchmark("ft_001", "fine_tuned", is_fine_tuned=True)
    # Fine-tuned should generally have higher recall
    assert fine_tuned.overall_metrics["recall_at_10"] > baseline.overall_metrics["recall_at_10"]


def test_benchmark_has_category_metrics(bench):
    run = bench.run_benchmark("model_001", "test", is_fine_tuned=False)
    assert len(run.metrics_by_category) >= 6
    for cat_metrics in run.metrics_by_category.values():
        assert "recall_at_1" in cat_metrics
        assert "recall_at_10" in cat_metrics
        assert "mrr" in cat_metrics


def test_benchmark_overall_metrics(bench):
    run = bench.run_benchmark("model_001", "test")
    m = run.overall_metrics
    assert "recall_at_1" in m
    assert "recall_at_5" in m
    assert "recall_at_10" in m
    assert "mrr" in m
    assert "avg_relevance" in m
    assert "keyword_recall" in m


def test_benchmark_results_per_query(bench):
    run = bench.run_benchmark("model_001", "test")
    assert len(run.results) == run.total_queries
    for r in run.results:
        assert isinstance(r, QueryResult)
        assert r.query != ""
        assert r.category != ""


# =========================================
# REGRESSION CHECKING
# =========================================

def test_regression_passes_for_improvement(bench):
    baseline = bench.run_benchmark("baseline_001", "baseline", is_fine_tuned=False)
    improved = bench.run_benchmark("ft_001", "fine_tuned", is_fine_tuned=True)
    assert improved.passed_regression is True


def test_regression_check_explicit(bench):
    baseline = bench.run_benchmark("baseline", "baseline", is_fine_tuned=False)
    current = bench.run_benchmark("ft_001", "fine_tuned", is_fine_tuned=True)
    result = bench.check_regression(current, baseline)
    assert result["passed"] is True


def test_regression_no_baseline(bench):
    """First run has no baseline to regress against."""
    run = bench.run_benchmark("first_model", "first")
    result = bench.check_regression(run)
    # First run checks against itself (first in _runs), should pass
    assert "passed" in result


# =========================================
# COMPARISON
# =========================================

def test_compare_runs(bench):
    run_a = bench.run_benchmark("baseline", "baseline", is_fine_tuned=False)
    run_b = bench.run_benchmark("ft_001", "fine_tuned", is_fine_tuned=True)
    comparison = bench.compare_runs(run_a.id, run_b.id)
    assert "run_a" in comparison
    assert "run_b" in comparison
    assert "deltas" in comparison
    assert "improved" in comparison


def test_compare_runs_not_found(bench):
    result = bench.compare_runs("bad_id", "other_bad_id")
    assert "error" in result


def test_compare_shows_improvement(bench):
    run_a = bench.run_benchmark("baseline", "baseline", is_fine_tuned=False)
    run_b = bench.run_benchmark("ft_001", "fine_tuned", is_fine_tuned=True)
    comparison = bench.compare_runs(run_a.id, run_b.id)
    assert comparison["improved"] is True
    assert comparison["deltas"]["recall_at_10"] > 0


# =========================================
# QUERIES & HISTORY
# =========================================

def test_get_run(bench):
    run = bench.run_benchmark("test_model", "test")
    retrieved = bench.get_run(run.id)
    assert retrieved is not None
    assert retrieved.id == run.id


def test_get_runs(bench):
    bench.run_benchmark("model_1", "m1")
    bench.run_benchmark("model_2", "m2")
    runs = bench.get_runs()
    assert len(runs) == 2
    assert all("id" in r and "overall_metrics" in r for r in runs)


# =========================================
# DIFFICULTY DISTRIBUTION
# =========================================

def test_difficulty_distribution(bench):
    stats = bench.get_stats()
    by_diff = stats["queries_by_difficulty"]
    assert by_diff["easy"] >= 1
    assert by_diff["medium"] >= 1
    assert by_diff["hard"] >= 1


# =========================================
# STATS
# =========================================

def test_stats(bench):
    bench.run_benchmark("m1", "model_1")
    stats = bench.get_stats()
    assert stats["total_golden_queries"] >= 25
    assert stats["total_runs"] == 1
    assert len(stats["categories"]) >= 6


# =========================================
# SINGLETON
# =========================================

def test_singleton():
    b1 = get_benchmark_suite()
    b2 = get_benchmark_suite()
    assert b1 is b2
