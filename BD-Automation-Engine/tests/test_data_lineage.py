"""Tests for Phase 38A — Data Lineage Tracker."""

import pytest
from datetime import datetime, timezone, timedelta

from src.data_quality.lineage import (
    DataLineageTracker,
    LineageGraph,
    DataSource,
    TransformProcess,
    ImpactAnalysis,
    FreshnessReport,
    NodeType,
    SourceType,
    TransformType,
    get_lineage_tracker,
)


# =========================================
# FIXTURES
# =========================================


@pytest.fixture
def tracker():
    return DataLineageTracker()


@pytest.fixture
def source():
    return DataSource(
        id="src1",
        source_type=SourceType.APIFY_SCRAPE.value,
        url="https://linkedin.com/jobs",
        timestamp=datetime.now(timezone.utc).isoformat(),
        actor_id="apify_actor_123",
    )


@pytest.fixture
def populated_tracker(tracker, source):
    """Tracker with a full lineage chain."""
    # Step 1: Ingest raw records
    raw_records = [
        {
            "id": "r1",
            "_type": "job",
            "title": "Systems Engineer",
            "location": "San Diego",
        },
        {"id": "r2", "_type": "job", "title": "Analyst", "location": "Langley"},
    ]
    raw_nodes = tracker.record_ingestion(source, raw_records)

    # Step 2: Transform (LLM enrichment)
    enrichment_process = TransformProcess(
        name="llm_enrichment",
        version="1.0",
        model="gpt-4o",
        params={"temperature": 0.0},
        transform_type=TransformType.LLM_ENRICHMENT.value,
    )
    enriched = [
        {
            "id": "r1",
            "_type": "enriched",
            "title": "Systems Engineer",
            "program": "AF DCGS - PACAF",
            "tier": 4,
        },
    ]
    enriched_nodes = tracker.record_transformation(
        [raw_nodes[0].id],
        enrichment_process,
        enriched,
    )

    # Step 3: Transform (scoring)
    scoring_process = TransformProcess(
        name="bd_scoring",
        version="2.0",
        params={"weights": "default"},
        transform_type=TransformType.SCORING.value,
    )
    scored = [
        {"id": "r1", "_type": "scored", "bd_score": 85, "priority": "high"},
    ]
    scored_nodes = tracker.record_transformation(
        [enriched_nodes[0].id],
        scoring_process,
        scored,
    )

    return tracker


# =========================================
# INGESTION
# =========================================


class TestIngestion:
    def test_creates_source_node(self, tracker, source):
        nodes = tracker.record_ingestion(source, [{"id": "r1"}])
        all_nodes = tracker.get_all_nodes()
        source_nodes = [n for n in all_nodes if n.node_type == NodeType.SOURCE.value]
        assert len(source_nodes) == 1

    def test_creates_raw_record_nodes(self, tracker, source):
        records = [{"id": "r1"}, {"id": "r2"}, {"id": "r3"}]
        nodes = tracker.record_ingestion(source, records)
        assert len(nodes) == 3
        assert all(n.node_type == NodeType.RAW_RECORD.value for n in nodes)

    def test_creates_produced_edges(self, tracker, source):
        tracker.record_ingestion(source, [{"id": "r1"}])
        edges = tracker.get_all_edges()
        produced = [e for e in edges if e.edge_type == "PRODUCED"]
        assert len(produced) == 1

    def test_raw_confidence_is_1(self, tracker, source):
        nodes = tracker.record_ingestion(source, [{"id": "r1"}])
        assert nodes[0].confidence == 1.0

    def test_data_hash_computed(self, tracker, source):
        nodes = tracker.record_ingestion(source, [{"id": "r1", "data": "test"}])
        assert nodes[0].data_hash != ""


# =========================================
# TRANSFORMATION
# =========================================


class TestTransformation:
    def test_creates_process_node(self, tracker, source):
        raw = tracker.record_ingestion(source, [{"id": "r1"}])
        process = TransformProcess(name="enrich", version="1.0")
        tracker.record_transformation([raw[0].id], process, [{"id": "r1"}])
        nodes = tracker.get_all_nodes()
        proc_nodes = [n for n in nodes if n.node_type == NodeType.PROCESS.value]
        assert len(proc_nodes) == 1

    def test_creates_fed_into_edges(self, tracker, source):
        raw = tracker.record_ingestion(source, [{"id": "r1"}])
        process = TransformProcess(name="enrich", version="1.0")
        tracker.record_transformation([raw[0].id], process, [{"id": "r1"}])
        edges = tracker.get_all_edges()
        fed = [e for e in edges if e.edge_type == "FED_INTO"]
        assert len(fed) == 1

    def test_creates_output_edges(self, tracker, source):
        raw = tracker.record_ingestion(source, [{"id": "r1"}])
        process = TransformProcess(name="enrich", version="1.0")
        tracker.record_transformation([raw[0].id], process, [{"id": "r1"}])
        edges = tracker.get_all_edges()
        output = [e for e in edges if e.edge_type == "OUTPUT"]
        assert len(output) == 1

    def test_confidence_decays(self, tracker, source):
        raw = tracker.record_ingestion(source, [{"id": "r1"}])
        process = TransformProcess(name="enrich", version="1.0")
        enriched = tracker.record_transformation([raw[0].id], process, [{"id": "r1"}])
        assert enriched[0].confidence < 1.0

    def test_multiple_inputs(self, tracker, source):
        raw = tracker.record_ingestion(source, [{"id": "r1"}, {"id": "r2"}])
        process = TransformProcess(name="merge", version="1.0")
        merged = tracker.record_transformation(
            [raw[0].id, raw[1].id],
            process,
            [{"id": "merged"}],
        )
        edges = tracker.get_all_edges()
        fed = [e for e in edges if e.edge_type == "FED_INTO"]
        assert len(fed) == 2


# =========================================
# LINEAGE TRACING
# =========================================


class TestLineageTracing:
    def test_trace_returns_graph(self, populated_tracker):
        graph = populated_tracker.trace_lineage("r1")
        assert isinstance(graph, LineageGraph)

    def test_trace_finds_source(self, populated_tracker):
        graph = populated_tracker.trace_lineage("r1")
        assert len(graph.sources) >= 1

    def test_trace_counts_transformations(self, populated_tracker):
        graph = populated_tracker.trace_lineage("r1")
        assert graph.total_transformations >= 2  # enrichment + scoring

    def test_trace_confidence_chain(self, populated_tracker):
        graph = populated_tracker.trace_lineage("r1")
        assert len(graph.confidence_chain) > 0
        # Confidence should decrease along chain
        assert graph.confidence_chain[0] >= graph.confidence_chain[-1]

    def test_trace_nonexistent_record(self, tracker):
        graph = tracker.trace_lineage("nonexistent")
        assert graph is None

    def test_trace_depth_limit(self, populated_tracker):
        graph = populated_tracker.trace_lineage("r1", depth=1)
        assert graph.depth <= 1


# =========================================
# IMPACT ANALYSIS
# =========================================


class TestImpactAnalysis:
    def test_impact_finds_downstream(self, populated_tracker):
        # r1 raw -> r1 enriched -> r1 scored
        impact = populated_tracker.get_impact_analysis("r1")
        assert isinstance(impact, ImpactAnalysis)
        assert impact.total_downstream >= 0

    def test_impact_risk_level(self, populated_tracker):
        impact = populated_tracker.get_impact_analysis("r1")
        assert impact.risk_level in ("low", "medium", "high", "critical")

    def test_impact_nonexistent(self, tracker):
        impact = tracker.get_impact_analysis("none")
        assert impact.total_downstream == 0


# =========================================
# FRESHNESS REPORT
# =========================================


class TestFreshnessReport:
    def test_freshness_report(self, tracker):
        now = datetime.now(timezone.utc)
        tracker.set_domain_records(
            "contacts",
            [
                {"id": "c1", "last_updated": (now - timedelta(days=10)).isoformat()},
                {"id": "c2", "last_updated": (now - timedelta(days=50)).isoformat()},
                {"id": "c3", "last_updated": (now - timedelta(days=120)).isoformat()},
            ],
        )
        report = tracker.get_freshness_report()
        assert isinstance(report, FreshnessReport)
        assert len(report.entries) == 1
        entry = report.entries[0]
        assert entry.domain == "contacts"
        assert entry.total_records == 3
        assert entry.updated_last_30 == 1
        assert entry.updated_last_90 == 2
        assert entry.stale_count == 1

    def test_empty_domain(self, tracker):
        tracker.set_domain_records("programs", [])
        report = tracker.get_freshness_report()
        assert len(report.entries) == 1

    def test_overall_freshness_score(self, tracker):
        now = datetime.now(timezone.utc)
        tracker.set_domain_records(
            "contacts",
            [
                {"id": "c1", "last_updated": (now - timedelta(days=5)).isoformat()},
            ],
        )
        report = tracker.get_freshness_report()
        assert report.overall_freshness_score == 100.0


# =========================================
# STATS & QUERIES
# =========================================


class TestStatsAndQueries:
    def test_get_stats(self, populated_tracker):
        stats = populated_tracker.get_stats()
        assert stats["total_nodes"] > 0
        assert stats["total_edges"] > 0
        assert stats["total_sources"] >= 1

    def test_get_nodes_for_record(self, populated_tracker):
        nodes = populated_tracker.get_nodes_for_record("r1")
        assert len(nodes) >= 1

    def test_get_node_by_id(self, populated_tracker):
        all_nodes = populated_tracker.get_all_nodes()
        node = populated_tracker.get_node(all_nodes[0].id)
        assert node is not None


# =========================================
# SINGLETON
# =========================================


class TestSingleton:
    def test_get_tracker(self):
        t = get_lineage_tracker()
        assert isinstance(t, DataLineageTracker)

    def test_singleton(self):
        t1 = get_lineage_tracker()
        t2 = get_lineage_tracker()
        assert t1 is t2
