"""
Phase 24A — Scrape Orchestrator v2 Tests

Tests production orchestrator: source management, health tracking,
trigger/pause/resume, full cycle, stats, persistence, and singleton.
All external dependencies are mocked.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from Engine8_Knowledge.scrapers.scrape_orchestrator_v2 import (
    ScrapeOrchestratorV2,
    SourceConfig,
    SourceStatus,
    SourceHealth,
    OrchestratorReport,
    OrchestratorStats,
    get_scrape_orchestrator,
)
from Engine8_Knowledge.scrapers.crawl4ai_engine import CrawlResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_storage(tmp_path):
    return str(tmp_path / "orch_test")


@pytest.fixture
def mock_crawl_engine():
    engine = AsyncMock()
    engine.crawl_url = AsyncMock(return_value=CrawlResult(
        url="https://example.com",
        extracted_data=[{"title": "Job 1"}, {"title": "Job 2"}],
    ))
    engine.crawl_competitor_careers = AsyncMock(return_value=[
        {"title": "Job A"},
        {"title": "Job B"},
    ])
    return engine


@pytest.fixture
def mock_sam_sync():
    sam = AsyncMock()
    sam.monitor_awards = AsyncMock(return_value=[])
    sam.search_awards = AsyncMock(return_value=[])
    return sam


@pytest.fixture
def mock_doc_pipeline():
    doc = AsyncMock()
    doc.discover_documents = AsyncMock(return_value=[])
    doc.process_batch = AsyncMock(return_value=MagicMock(processed=0))
    return doc


@pytest.fixture
def orchestrator(tmp_storage, mock_crawl_engine, mock_sam_sync, mock_doc_pipeline):
    return ScrapeOrchestratorV2(
        crawl_engine=mock_crawl_engine,
        sam_sync=mock_sam_sync,
        doc_pipeline=mock_doc_pipeline,
        storage_path=tmp_storage,
    )


@pytest.fixture
def sample_career_source():
    return SourceConfig(
        name="GDIT Careers",
        source_type="career_page",
        url="https://www.gdit.com/careers/",
        extraction_strategy="jobs",
        priority="high",
        enabled=True,
    )


@pytest.fixture
def sample_sam_source():
    return SourceConfig(
        name="DCGS Awards",
        source_type="sam_gov",
        url="DCGS intelligence",
        enabled=True,
    )


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------


class TestInit:
    def test_init(self, orchestrator, tmp_storage):
        assert Path(tmp_storage).exists()
        assert orchestrator.crawl_engine is not None
        assert orchestrator.sam_sync is not None
        assert orchestrator.doc_pipeline is not None
        assert len(orchestrator._sources) == 0


# ---------------------------------------------------------------------------
# Source Management
# ---------------------------------------------------------------------------


class TestSourceManagement:
    @pytest.mark.asyncio
    async def test_schedule_source(self, orchestrator, sample_career_source):
        source_id = await orchestrator.schedule_source(sample_career_source)
        assert source_id.startswith("src_")
        assert source_id in orchestrator._sources
        assert source_id in orchestrator._statuses

    @pytest.mark.asyncio
    async def test_list_sources(self, orchestrator, sample_career_source):
        await orchestrator.schedule_source(sample_career_source)
        sources = await orchestrator.list_sources()
        assert len(sources) == 1
        assert isinstance(sources[0], SourceStatus)
        assert sources[0].config.name == "GDIT Careers"
        assert sources[0].status == "active"


# ---------------------------------------------------------------------------
# Source Health
# ---------------------------------------------------------------------------


class TestSourceHealth:
    @pytest.mark.asyncio
    async def test_get_source_health(self, orchestrator, sample_career_source):
        source_id = await orchestrator.schedule_source(sample_career_source)
        health = await orchestrator.get_source_health(source_id)
        assert isinstance(health, SourceHealth)
        assert health.source_id == source_id
        assert health.status == "active"

    @pytest.mark.asyncio
    async def test_get_source_health_not_found(self, orchestrator):
        health = await orchestrator.get_source_health("nonexistent_id")
        assert health.status == "not_found"


# ---------------------------------------------------------------------------
# Trigger / Pause / Resume
# ---------------------------------------------------------------------------


class TestTriggerAndControl:
    @pytest.mark.asyncio
    async def test_trigger_source(self, orchestrator, sample_career_source, mock_crawl_engine):
        """Trigger a career page scrape."""
        source_id = await orchestrator.schedule_source(sample_career_source)
        run_id = await orchestrator.trigger_source(source_id)

        assert run_id.startswith("run_")
        status = orchestrator._statuses[source_id]
        assert status.total_runs == 1
        assert status.last_success is not None
        assert status.status == "active"

    @pytest.mark.asyncio
    async def test_trigger_source_not_found(self, orchestrator):
        with pytest.raises(ValueError, match="Source not found"):
            await orchestrator.trigger_source("nonexistent")

    @pytest.mark.asyncio
    async def test_pause_resume_source(self, orchestrator, sample_career_source):
        source_id = await orchestrator.schedule_source(sample_career_source)

        # Pause
        ok = await orchestrator.pause_source(source_id)
        assert ok is True
        assert orchestrator._statuses[source_id].status == "paused"
        assert orchestrator._sources[source_id].enabled is False

        # Resume
        ok = await orchestrator.resume_source(source_id)
        assert ok is True
        assert orchestrator._statuses[source_id].status == "active"
        assert orchestrator._sources[source_id].enabled is True

        # Pause non-existent
        ok = await orchestrator.pause_source("nonexistent")
        assert ok is False


# ---------------------------------------------------------------------------
# Full Cycle
# ---------------------------------------------------------------------------


class TestFullCycle:
    @pytest.mark.asyncio
    async def test_run_full_cycle(self, orchestrator, sample_career_source, mock_crawl_engine, mock_sam_sync):
        """Full cycle scrapes career pages, monitors SAM, processes docs."""
        await orchestrator.schedule_source(sample_career_source)

        # SAM sync returns 2 alerts
        mock_sam_sync.monitor_awards = AsyncMock(return_value=[
            MagicMock(), MagicMock(),
        ])

        report = await orchestrator.run_full_cycle()

        assert isinstance(report, OrchestratorReport)
        assert report.cycle_id.startswith("cycle_")
        assert report.started_at is not None
        assert report.completed_at is not None
        assert report.sources_scraped >= 1
        assert report.jobs_found >= 0
        assert report.contracts_found == 2
        assert report.duration_seconds >= 0


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------


class TestStats:
    @pytest.mark.asyncio
    async def test_get_orchestrator_stats(self, orchestrator, sample_career_source):
        await orchestrator.schedule_source(sample_career_source)
        stats = await orchestrator.get_orchestrator_stats()

        assert isinstance(stats, OrchestratorStats)
        assert stats.total_sources == 1
        assert stats.active_sources == 1
        assert stats.paused_sources == 0


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------


class TestPersistence:
    @pytest.mark.asyncio
    async def test_save_load_sources(self, tmp_storage, mock_crawl_engine):
        """Sources persist to JSON and reload."""
        orch1 = ScrapeOrchestratorV2(
            crawl_engine=mock_crawl_engine,
            storage_path=tmp_storage,
        )
        src = SourceConfig(
            name="Leidos Careers",
            source_type="career_page",
            url="https://careers.leidos.com",
            enabled=True,
        )
        source_id = await orch1.schedule_source(src)

        # Verify JSON file exists
        sources_file = Path(tmp_storage) / "sources.json"
        assert sources_file.exists()

        # Create a new orchestrator that loads from disk
        orch2 = ScrapeOrchestratorV2(
            crawl_engine=mock_crawl_engine,
            storage_path=tmp_storage,
        )
        assert source_id in orch2._sources
        assert orch2._sources[source_id].name == "Leidos Careers"


# ---------------------------------------------------------------------------
# Run Source (career page variant)
# ---------------------------------------------------------------------------


class TestRunSource:
    @pytest.mark.asyncio
    async def test_run_source_career_page(self, orchestrator, mock_crawl_engine):
        """_run_source for a career_page with URL calls crawl_url."""
        cfg = SourceConfig(
            source_id="src_test",
            name="Test Careers",
            source_type="career_page",
            url="https://test.com/jobs",
            extraction_strategy="jobs",
        )
        items = await orchestrator._run_source(cfg)

        mock_crawl_engine.crawl_url.assert_called_once_with(
            "https://test.com/jobs",
            extraction_strategy="jobs",
        )
        # Mock returns 2 extracted_data items
        assert items == 2


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------


class TestSingleton:
    def test_singleton(self, tmp_storage):
        import Engine8_Knowledge.scrapers.scrape_orchestrator_v2 as mod
        mod._orchestrator = None  # Reset
        o1 = get_scrape_orchestrator(storage_path=tmp_storage)
        o2 = get_scrape_orchestrator()
        assert o1 is o2
        mod._orchestrator = None  # Clean up
