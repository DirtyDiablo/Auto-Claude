"""Tests for Phase 28A - Topic Modeler (BERTopic clustering with keyword fallback)."""

import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from Engine8_Knowledge.ml.topic_modeler import (
    TopicModeler,
    TopicInfo,
    TopicResult,
    TopicTrend,
    get_topic_modeler,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def modeler():
    """Create a TopicModeler instance with BERTopic mocked out (fallback mode)."""
    with patch("Engine8_Knowledge.ml.topic_modeler.TopicModeler._initialize"):
        instance = TopicModeler()
        instance._model = None
        instance._topic_cache = {}
    return instance


@pytest.fixture
def sample_job_docs():
    """Sample job posting documents for clustering."""
    return [
        "Senior DCGS analyst needed for ISR intelligence processing at Fort Belvoir",
        "Software engineer for DCGS ground system modernization and DevSecOps pipeline",
        "Cybersecurity specialist for network defense and SIGINT analysis",
        "Systems administrator for DISA cloud migration and infrastructure",
        "Data analyst for intelligence surveillance reconnaissance reporting",
        "DevSecOps engineer for CI/CD pipeline and automated testing",
        "Program manager for electronic warfare system integration",
        "Network engineer for NGEN Navy enterprise network operations",
    ]


@pytest.fixture
def sample_note_docs():
    """Sample meeting/call notes for clustering."""
    return [
        "Call with Leidos PM about DCGS integration timeline and milestones",
        "Meeting notes: GDIT proposal strategy for ISR modernization contract",
        "Discussed Northrop Grumman subcontract opportunities for EW programs",
        "Follow-up with DISA on cloud migration schedule and security requirements",
        "Internal review of past performance on SIGINT processing systems",
    ]


# =============================================================================
# Initialization tests
# =============================================================================


class TestTopicModelerInit:
    """Tests for TopicModeler initialization."""

    def test_init_without_bertopic(self):
        """TopicModeler should initialize with _model=None when BERTopic is unavailable."""
        with patch.dict("sys.modules", {"bertopic": None}):
            with patch("Engine8_Knowledge.ml.topic_modeler.TopicModeler._initialize"):
                instance = TopicModeler()
                instance._model = None
        assert instance._model is None

    def test_init_has_empty_cache(self, modeler):
        """Freshly initialized modeler should have an empty topic cache."""
        assert modeler._topic_cache == {}


# =============================================================================
# Dataclass tests
# =============================================================================


class TestDataclasses:
    """Tests for topic modeler dataclasses."""

    def test_topic_info_fields(self):
        """TopicInfo should have topic_id, name, keywords, size, representative_docs."""
        topic = TopicInfo(
            topic_id=0,
            name="test_topic",
            keywords=["dcgs", "isr"],
            size=10,
            representative_docs=["doc1"],
        )
        assert topic.topic_id == 0
        assert topic.name == "test_topic"
        assert topic.keywords == ["dcgs", "isr"]
        assert topic.size == 10
        assert topic.representative_docs == ["doc1"]

    def test_topic_result_fields(self):
        """TopicResult should have topics, total_documents, total_topics, outlier_count, model_type."""
        result = TopicResult(topics=[], total_documents=5, total_topics=2)
        assert result.total_documents == 5
        assert result.total_topics == 2
        assert result.outlier_count == 0
        assert result.model_type == "bertopic"

    def test_topic_trend_fields(self):
        """TopicTrend should have topic_id, topic_name, data_points, trend."""
        trend = TopicTrend(topic_id=1, topic_name="ISR", data_points=[])
        assert trend.topic_id == 1
        assert trend.topic_name == "ISR"
        assert trend.data_points == []
        assert trend.trend == "stable"


# =============================================================================
# Keyword fallback clustering tests
# =============================================================================


class TestKeywordClustering:
    """Tests for the keyword-based fallback clustering."""

    def test_cluster_jobs_returns_topic_result(self, modeler, sample_job_docs):
        """cluster_jobs() should return a TopicResult with discovered topics."""
        result = asyncio.get_event_loop().run_until_complete(
            modeler.cluster_jobs(documents=sample_job_docs)
        )
        assert isinstance(result, TopicResult)
        assert result.total_documents == len(sample_job_docs)
        assert result.total_topics > 0
        assert result.model_type == "keyword_fallback"

    def test_cluster_jobs_empty_documents(self, modeler):
        """cluster_jobs() with no documents should return empty TopicResult."""
        result = asyncio.get_event_loop().run_until_complete(
            modeler.cluster_jobs(documents=[])
        )
        assert isinstance(result, TopicResult)
        assert result.total_documents == 0
        assert result.total_topics == 0
        assert result.topics == []

    def test_cluster_jobs_none_documents(self, modeler):
        """cluster_jobs() with None documents should return empty TopicResult."""
        result = asyncio.get_event_loop().run_until_complete(
            modeler.cluster_jobs(documents=None)
        )
        assert result.total_documents == 0

    def test_cluster_notes_returns_topic_result(self, modeler, sample_note_docs):
        """cluster_notes() should return a TopicResult with discovered topics."""
        result = asyncio.get_event_loop().run_until_complete(
            modeler.cluster_notes(documents=sample_note_docs)
        )
        assert isinstance(result, TopicResult)
        assert result.total_documents == len(sample_note_docs)
        assert result.total_topics > 0

    def test_cluster_documents_returns_topic_result(self, modeler, sample_job_docs):
        """cluster_documents() should return a TopicResult."""
        result = asyncio.get_event_loop().run_until_complete(
            modeler.cluster_documents(documents=sample_job_docs, doc_type="proposals")
        )
        assert isinstance(result, TopicResult)
        assert result.total_documents == len(sample_job_docs)

    def test_keyword_cluster_populates_cache(self, modeler, sample_job_docs):
        """After clustering, the topic cache should be populated for the source."""
        asyncio.get_event_loop().run_until_complete(
            modeler.cluster_jobs(documents=sample_job_docs)
        )
        assert "jobs" in modeler._topic_cache
        assert len(modeler._topic_cache["jobs"]) > 0

    def test_keyword_cluster_topics_have_keywords(self, modeler, sample_job_docs):
        """Each topic from keyword clustering should have at least one keyword."""
        result = asyncio.get_event_loop().run_until_complete(
            modeler.cluster_jobs(documents=sample_job_docs)
        )
        for topic in result.topics:
            assert len(topic.keywords) > 0

    def test_keyword_cluster_topics_have_representative_docs(self, modeler, sample_job_docs):
        """Each topic should have at most 3 representative docs."""
        result = asyncio.get_event_loop().run_until_complete(
            modeler.cluster_jobs(documents=sample_job_docs)
        )
        for topic in result.topics:
            assert len(topic.representative_docs) <= 3


# =============================================================================
# Topic trends tests
# =============================================================================


class TestTopicTrends:
    """Tests for topic trend retrieval."""

    def test_get_topic_trends_unknown_topic(self, modeler):
        """get_topic_trends() for an unknown topic_id should return 'Unknown' name."""
        trend = asyncio.get_event_loop().run_until_complete(
            modeler.get_topic_trends(topic_id=999)
        )
        assert isinstance(trend, TopicTrend)
        assert trend.topic_name == "Unknown"
        assert trend.trend == "stable"

    def test_get_topic_trends_cached_topic(self, modeler, sample_job_docs):
        """get_topic_trends() for a cached topic should return its name."""
        asyncio.get_event_loop().run_until_complete(
            modeler.cluster_jobs(documents=sample_job_docs)
        )
        # Use the first topic in the cache
        first_topic = modeler._topic_cache["jobs"][0]
        trend = asyncio.get_event_loop().run_until_complete(
            modeler.get_topic_trends(topic_id=first_topic.topic_id)
        )
        assert trend.topic_name == first_topic.name


# =============================================================================
# Stats tests
# =============================================================================


class TestStats:
    """Tests for modeler statistics."""

    def test_get_stats_no_model(self, modeler):
        """get_stats() should report has_model=False when BERTopic is unavailable."""
        stats = modeler.get_stats()
        assert stats["has_model"] is False
        assert stats["cached_sources"] == []
        assert stats["total_cached_topics"] == 0

    def test_get_stats_after_clustering(self, modeler, sample_job_docs):
        """get_stats() after clustering should report cached sources."""
        asyncio.get_event_loop().run_until_complete(
            modeler.cluster_jobs(documents=sample_job_docs)
        )
        stats = modeler.get_stats()
        assert "jobs" in stats["cached_sources"]
        assert stats["total_cached_topics"] > 0


# =============================================================================
# Singleton tests
# =============================================================================


class TestSingleton:
    """Tests for the module-level singleton accessor."""

    def test_get_topic_modeler_returns_instance(self):
        """get_topic_modeler() should return a TopicModeler instance."""
        import Engine8_Knowledge.ml.topic_modeler as mod
        mod._modeler = None
        instance = get_topic_modeler()
        assert isinstance(instance, TopicModeler)

    def test_get_topic_modeler_is_singleton(self):
        """Calling get_topic_modeler() twice should return the same instance."""
        import Engine8_Knowledge.ml.topic_modeler as mod
        mod._modeler = None
        a = get_topic_modeler()
        b = get_topic_modeler()
        assert a is b
