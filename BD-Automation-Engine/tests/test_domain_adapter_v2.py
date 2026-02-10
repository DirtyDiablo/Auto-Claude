"""Tests for Phase 28A - Domain Adapter v2 (defense-domain embedding adapter)."""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from Engine8_Knowledge.ml.domain_adapter_v2 import (
    DomainAdapterV2,
    BenchmarkResult,
    TrainingPair,
    DEFENSE_SYNONYMS,
    get_domain_adapter_v2,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def adapter():
    """Create a DomainAdapterV2 instance (no sentence-transformer loaded)."""
    instance = DomainAdapterV2()
    # Ensure model is not loaded (avoids ImportError in CI)
    instance._model = None
    return instance


# =============================================================================
# Initialization tests
# =============================================================================


class TestDomainAdapterV2Init:
    """Tests for DomainAdapterV2 initialization."""

    def test_init_default_base_model(self, adapter):
        """Default base model should be all-MiniLM-L6-v2."""
        assert adapter.base_model == "all-MiniLM-L6-v2"

    def test_init_custom_base_model(self):
        """Custom base model name should be stored."""
        instance = DomainAdapterV2(base_model="all-mpnet-base-v2")
        assert instance.base_model == "all-mpnet-base-v2"

    def test_init_not_trained(self, adapter):
        """Fresh adapter should not be marked as trained."""
        assert adapter._trained is False

    def test_init_synonyms_loaded(self, adapter):
        """Adapter should have a copy of DEFENSE_SYNONYMS on init."""
        assert len(adapter._synonyms) == len(DEFENSE_SYNONYMS)
        assert "DCGS" in adapter._synonyms
        assert "ISR" in adapter._synonyms

    def test_init_benchmark_result_is_none(self, adapter):
        """Benchmark result should be None before any evaluation."""
        assert adapter._benchmark_result is None


# =============================================================================
# DEFENSE_SYNONYMS constant tests
# =============================================================================


class TestDefenseSynonyms:
    """Tests for the DEFENSE_SYNONYMS dictionary."""

    def test_dcgs_synonyms(self):
        """DCGS should have known expansion terms."""
        assert "Distributed Common Ground System" in DEFENSE_SYNONYMS["DCGS"]

    def test_isr_synonyms(self):
        """ISR should include SIGINT, GEOINT, IMINT."""
        isr = DEFENSE_SYNONYMS["ISR"]
        assert "SIGINT" in isr
        assert "GEOINT" in isr

    def test_c2_synonyms(self):
        """C2 should include Command and Control and C4ISR."""
        c2 = DEFENSE_SYNONYMS["C2"]
        assert "Command and Control" in c2
        assert "C4ISR" in c2

    def test_devsecops_synonyms(self):
        """DevSecOps should include CI/CD."""
        ds = DEFENSE_SYNONYMS["DevSecOps"]
        assert "CI/CD" in ds

    def test_gbsd_synonyms(self):
        """GBSD should include Sentinel."""
        gbsd = DEFENSE_SYNONYMS["GBSD"]
        assert "Sentinel" in gbsd

    def test_all_synonym_keys_present(self):
        """All expected acronym keys should be present in the dict."""
        expected_keys = {"DCGS", "ISR", "C2", "EW", "SIGINT", "DevSecOps", "JADC2", "ABMS", "GBSD", "NGEN"}
        assert expected_keys == set(DEFENSE_SYNONYMS.keys())


# =============================================================================
# Query expansion tests
# =============================================================================


class TestExpandQuery:
    """Tests for defense acronym expansion in queries."""

    def test_expand_dcgs_query(self, adapter):
        """Expanding a DCGS query should add Distributed Common Ground System."""
        expanded = adapter.expand_query("DCGS analyst needed")
        assert "Distributed Common Ground System" in expanded

    def test_expand_isr_query(self, adapter):
        """Expanding an ISR query should add Intelligence Surveillance Reconnaissance."""
        expanded = adapter.expand_query("ISR modernization")
        assert "Intelligence Surveillance Reconnaissance" in expanded

    def test_expand_c2_query(self, adapter):
        """Expanding a C2 query should add Command and Control."""
        expanded = adapter.expand_query("C2 battle management system")
        assert "Command and Control" in expanded

    def test_expand_no_acronyms(self, adapter):
        """Expanding a query with no known acronyms should return it unchanged."""
        original = "general purpose software engineer"
        expanded = adapter.expand_query(original)
        assert expanded == original

    def test_expand_multiple_acronyms(self, adapter):
        """Expanding a query with multiple acronyms should add all expansions."""
        expanded = adapter.expand_query("DCGS ISR analyst")
        assert "Distributed Common Ground System" in expanded
        assert "Intelligence Surveillance Reconnaissance" in expanded

    def test_expand_case_insensitive(self, adapter):
        """Acronym matching should be case-insensitive."""
        expanded = adapter.expand_query("dcgs system engineer")
        assert "Distributed Common Ground System" in expanded

    def test_expand_preserves_original_query(self, adapter):
        """The original query text should still be present in the expanded result."""
        original = "DCGS analyst needed"
        expanded = adapter.expand_query(original)
        assert original in expanded


# =============================================================================
# Synonym management tests
# =============================================================================


class TestSynonymManagement:
    """Tests for adding custom synonyms."""

    def test_add_synonyms(self, adapter):
        """add_synonyms() should register new acronym expansions."""
        adapter.add_synonyms("JSTARS", ["Joint STARS", "Joint Surveillance Target Attack Radar System"])
        assert "JSTARS" in adapter._synonyms
        assert "Joint STARS" in adapter._synonyms["JSTARS"]

    def test_added_synonyms_used_in_expansion(self, adapter):
        """Newly added synonyms should be applied in expand_query()."""
        adapter.add_synonyms("AWACS", ["Airborne Warning", "E-3 Sentry"])
        expanded = adapter.expand_query("AWACS mission system")
        assert "Airborne Warning" in expanded


# =============================================================================
# Benchmark evaluation tests
# =============================================================================


class TestBenchmark:
    """Tests for embedding benchmark evaluation."""

    def test_evaluate_on_benchmark_returns_result(self, adapter):
        """evaluate_on_benchmark() should return a BenchmarkResult."""
        result = adapter.evaluate_on_benchmark()
        assert isinstance(result, BenchmarkResult)

    def test_evaluate_on_benchmark_has_metrics(self, adapter):
        """BenchmarkResult should have non-negative precision, recall, and MRR."""
        result = adapter.evaluate_on_benchmark()
        assert result.avg_precision >= 0.0
        assert result.avg_recall >= 0.0
        assert result.avg_mrr >= 0.0
        assert result.queries_tested > 0

    def test_evaluate_stores_result(self, adapter):
        """evaluate_on_benchmark() should cache the result on the adapter."""
        adapter.evaluate_on_benchmark()
        assert adapter._benchmark_result is not None

    def test_evaluate_with_custom_queries(self, adapter):
        """evaluate_on_benchmark() should accept custom benchmark queries."""
        custom = [
            {"query": "cyber defense", "relevant_terms": ["cyber"]},
            {"query": "SIGINT processing", "relevant_terms": ["sigint"]},
        ]
        result = adapter.evaluate_on_benchmark(queries=custom)
        assert result.queries_tested == 2

    def test_benchmark_result_dataclass(self):
        """BenchmarkResult should have all expected fields."""
        br = BenchmarkResult(avg_precision=0.8, avg_recall=0.7, avg_mrr=0.75, queries_tested=10)
        assert br.avg_precision == 0.8
        assert br.avg_recall == 0.7
        assert br.avg_mrr == 0.75
        assert br.queries_tested == 10
        assert br.improvements_over_v1 == 0.0


# =============================================================================
# Training tests
# =============================================================================


class TestTraining:
    """Tests for hard-negative training."""

    def test_train_without_model_returns_skipped(self, adapter):
        """train_with_hard_negatives() without model should return skipped status."""
        # Ensure _load_model also fails
        with patch.object(adapter, "_load_model"):
            adapter._model = None
            result = adapter.train_with_hard_negatives(
                positive_pairs=[TrainingPair(anchor="a", positive="b")]
            )
        assert result["status"] == "skipped"

    def test_training_pair_dataclass(self):
        """TrainingPair should have anchor, positive, negative fields."""
        pair = TrainingPair(anchor="DCGS analyst", positive="ground system engineer", negative="cooking recipe")
        assert pair.anchor == "DCGS analyst"
        assert pair.positive == "ground system engineer"
        assert pair.negative == "cooking recipe"

    def test_training_pair_default_negative(self):
        """TrainingPair negative should default to empty string."""
        pair = TrainingPair(anchor="a", positive="b")
        assert pair.negative == ""


# =============================================================================
# Stats tests
# =============================================================================


class TestStats:
    """Tests for adapter statistics."""

    def test_get_stats_untrained(self, adapter):
        """get_stats() on a fresh adapter should report not trained."""
        stats = adapter.get_stats()
        assert stats["trained"] is False
        assert stats["synonyms"] == len(DEFENSE_SYNONYMS)
        assert stats["base_model"] == "all-MiniLM-L6-v2"
        assert stats["benchmark"] is None


# =============================================================================
# Singleton tests
# =============================================================================


class TestSingleton:
    """Tests for the module-level singleton accessor."""

    def test_get_domain_adapter_v2_returns_instance(self):
        """get_domain_adapter_v2() should return a DomainAdapterV2 instance."""
        import Engine8_Knowledge.ml.domain_adapter_v2 as mod
        mod._adapter = None
        instance = get_domain_adapter_v2()
        assert isinstance(instance, DomainAdapterV2)

    def test_get_domain_adapter_v2_is_singleton(self):
        """Calling get_domain_adapter_v2() twice should return the same instance."""
        import Engine8_Knowledge.ml.domain_adapter_v2 as mod
        mod._adapter = None
        a = get_domain_adapter_v2()
        b = get_domain_adapter_v2()
        assert a is b
