"""
Phase 24A — Scrape API v2 Tests

Tests all 20 FastAPI endpoints for AI-native scraping, SAM.gov contracts,
and federal document processing. Uses TestClient with mocked backends.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

try:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

from Engine8_Knowledge.api_routers.scrape_api_v2 import router
from Engine8_Knowledge.scrapers.crawl4ai_engine import CrawlResult
from Engine8_Knowledge.scrapers.sam_gov_sync import (
    ContractAward,
    ContractOpportunity,
    ContractAlert,
    WatchConfig,
)
from Engine8_Knowledge.scrapers.federal_doc_pipeline import (
    DocumentRef,
    ProcessedFederalDoc,
    BatchResult,
)
from Engine8_Knowledge.scrapers.scrape_orchestrator_v2 import (
    SourceConfig,
    SourceStatus,
    SourceHealth,
    OrchestratorReport,
    OrchestratorStats,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def app():
    if not FASTAPI_AVAILABLE:
        pytest.skip("FastAPI not installed")
    _app = FastAPI()
    _app.include_router(router)
    return _app


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def mock_crawl_engine():
    engine = AsyncMock()
    engine.crawl_url = AsyncMock(return_value=CrawlResult(
        url="https://example.com",
        raw_html="<html>test</html>",
        markdown="# Test",
        extracted_data=[{"title": "Test Job", "company": "GDIT"}],
        links=["https://example.com/page2"],
        metadata={"title": "Test", "status_code": 200},
        crawl_time_ms=150,
        extraction_strategy="auto",
        content_hash="abc123",
    ))
    engine.crawl_site = AsyncMock(return_value=[
        CrawlResult(url="https://example.com", markdown="Page 1"),
        CrawlResult(url="https://example.com/p2", markdown="Page 2"),
    ])
    engine.crawl_competitor_careers = AsyncMock(return_value=[
        {"title": "Sys Admin", "company": "GDIT"},
        {"title": "Analyst", "company": "GDIT"},
    ])
    return engine


@pytest.fixture
def mock_sam_sync():
    sam = MagicMock()
    sam.search_awards = AsyncMock(return_value=[
        ContractAward(
            award_id="AWD-001",
            title="DCGS Support",
            awardee="GDIT",
            value=10_000_000,
            naics="541512",
            agency="DoD",
        ),
    ])
    sam.search_opportunities = AsyncMock(return_value=[
        ContractOpportunity(
            notice_id="OPP-001",
            title="DCGS RFI",
            type="RFI",
            agency="DOD.AF",
        ),
    ])
    sam.monitor_awards = AsyncMock(return_value=[
        ContractAlert(
            alert_type="new_award",
            matched_watch="DCGS Watch",
            relevance_score=0.85,
        ),
    ])
    sam.list_watches = MagicMock(return_value=[
        WatchConfig(watch_id="w1", name="DCGS Monitor", keywords=["DCGS"]),
    ])
    sam.add_watch = MagicMock(return_value=WatchConfig(
        watch_id="w_new", name="ISR Watch", keywords=["ISR"],
        created_at="2025-01-01T00:00:00",
    ))
    sam.remove_watch = MagicMock(return_value=True)
    return sam


@pytest.fixture
def mock_doc_pipeline():
    doc = AsyncMock()
    doc.discover_documents = AsyncMock(return_value=[
        DocumentRef(doc_id="doc_001", url="https://sam.gov/doc.pdf", title="Test RFP"),
    ])
    doc.process_document = AsyncMock(return_value=ProcessedFederalDoc(
        source_path="/tmp/test.pdf",
        doc_type="RFP",
        title="DCGS RFP",
        agency="DoD",
        summary="[RFP] Summary text",
        full_text="full text here",
        content_hash="hash123",
    ))
    doc.process_batch = AsyncMock(return_value=BatchResult(
        total=2, processed=2, failed=0, duration_seconds=1.5,
    ))
    doc._output_dir = Path("/tmp/federal_docs_test")
    return doc


@pytest.fixture
def mock_orchestrator():
    orch = AsyncMock()
    orch.run_full_cycle = AsyncMock(return_value=OrchestratorReport(
        cycle_id="cycle_test",
        sources_scraped=3,
        jobs_found=10,
        contracts_found=2,
        duration_seconds=5.0,
    ))
    orch.list_sources = AsyncMock(return_value=[
        SourceStatus(
            config=SourceConfig(source_id="s1", name="GDIT Careers", source_type="career_page"),
            status="active",
            total_runs=5,
        ),
    ])
    orch.schedule_source = AsyncMock(return_value="src_new123")
    orch.get_source_health = AsyncMock(return_value=SourceHealth(
        source_id="s1",
        status="active",
        success_rate=0.95,
        total_items_scraped=150,
    ))
    orch.trigger_source = AsyncMock(return_value="run_abc123")
    orch.pause_source = AsyncMock(return_value=True)
    orch.resume_source = AsyncMock(return_value=True)
    orch.get_orchestrator_stats = AsyncMock(return_value=OrchestratorStats(
        total_sources=5,
        active_sources=3,
        paused_sources=1,
        errored_sources=1,
    ))
    return orch


# ---------------------------------------------------------------------------
# Crawl4AI Endpoints
# ---------------------------------------------------------------------------


class TestCrawlEndpoints:
    def test_crawl_url(self, client, mock_crawl_engine):
        with patch("Engine8_Knowledge.api_routers.scrape_api_v2._get_crawl_engine", return_value=mock_crawl_engine):
            resp = client.post("/scrape/crawl", json={
                "url": "https://example.com",
                "extraction_strategy": "auto",
            })
        assert resp.status_code == 200
        data = resp.json()
        assert data["url"] == "https://example.com"
        assert len(data["extracted_data"]) == 1
        assert data["extracted_data"][0]["title"] == "Test Job"

    def test_crawl_url_engine_unavailable(self, client):
        with patch("Engine8_Knowledge.api_routers.scrape_api_v2._get_crawl_engine", return_value=None):
            resp = client.post("/scrape/crawl", json={"url": "https://example.com"})
        assert resp.status_code == 503

    def test_crawl_site(self, client, mock_crawl_engine):
        with patch("Engine8_Knowledge.api_routers.scrape_api_v2._get_crawl_engine", return_value=mock_crawl_engine):
            resp = client.post("/scrape/crawl-site", json={
                "base_url": "https://example.com",
                "max_pages": 10,
            })
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert len(data["results"]) == 2

    def test_crawl_competitor(self, client, mock_crawl_engine):
        with patch("Engine8_Knowledge.api_routers.scrape_api_v2._get_crawl_engine", return_value=mock_crawl_engine):
            resp = client.post("/scrape/crawl-competitor", json={"company": "GDIT"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["company"] == "GDIT"
        assert data["total"] == 2
        assert len(data["jobs"]) == 2


# ---------------------------------------------------------------------------
# Orchestrator Endpoints
# ---------------------------------------------------------------------------


class TestOrchestratorEndpoints:
    def test_trigger_full_cycle(self, client, mock_orchestrator):
        with patch("Engine8_Knowledge.api_routers.scrape_api_v2._get_orchestrator", return_value=mock_orchestrator):
            resp = client.post("/scrape/cycle")
        assert resp.status_code == 200
        data = resp.json()
        assert data["cycle_id"] == "cycle_test"
        assert data["jobs_found"] == 10
        assert data["contracts_found"] == 2

    def test_list_sources(self, client, mock_orchestrator):
        with patch("Engine8_Knowledge.api_routers.scrape_api_v2._get_orchestrator", return_value=mock_orchestrator):
            resp = client.get("/scrape/sources")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["sources"][0]["config"]["name"] == "GDIT Careers"

    def test_add_source(self, client, mock_orchestrator):
        with patch("Engine8_Knowledge.api_routers.scrape_api_v2._get_orchestrator", return_value=mock_orchestrator):
            resp = client.post("/scrape/sources", json={
                "name": "Leidos Careers",
                "source_type": "career_page",
                "url": "https://careers.leidos.com",
            })
        assert resp.status_code == 200
        data = resp.json()
        assert data["source_id"] == "src_new123"
        assert data["name"] == "Leidos Careers"

    def test_get_source_health(self, client, mock_orchestrator):
        with patch("Engine8_Knowledge.api_routers.scrape_api_v2._get_orchestrator", return_value=mock_orchestrator):
            resp = client.get("/scrape/sources/s1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["source_id"] == "s1"
        assert data["status"] == "active"
        assert data["success_rate"] == 0.95

    def test_trigger_source(self, client, mock_orchestrator):
        with patch("Engine8_Knowledge.api_routers.scrape_api_v2._get_orchestrator", return_value=mock_orchestrator):
            resp = client.post("/scrape/sources/s1/trigger")
        assert resp.status_code == 200
        data = resp.json()
        assert data["run_id"] == "run_abc123"
        assert data["source_id"] == "s1"

    def test_trigger_source_not_found(self, client, mock_orchestrator):
        mock_orchestrator.trigger_source = AsyncMock(side_effect=ValueError("Source not found: bad_id"))
        with patch("Engine8_Knowledge.api_routers.scrape_api_v2._get_orchestrator", return_value=mock_orchestrator):
            resp = client.post("/scrape/sources/bad_id/trigger")
        assert resp.status_code == 404

    def test_toggle_source_pause(self, client, mock_orchestrator):
        with patch("Engine8_Knowledge.api_routers.scrape_api_v2._get_orchestrator", return_value=mock_orchestrator):
            resp = client.patch("/scrape/sources/s1/toggle?enabled=false")
        assert resp.status_code == 200
        data = resp.json()
        assert data["enabled"] is False
        assert data["success"] is True

    def test_toggle_source_resume(self, client, mock_orchestrator):
        with patch("Engine8_Knowledge.api_routers.scrape_api_v2._get_orchestrator", return_value=mock_orchestrator):
            resp = client.patch("/scrape/sources/s1/toggle?enabled=true")
        assert resp.status_code == 200
        data = resp.json()
        assert data["enabled"] is True

    def test_orchestrator_stats(self, client, mock_orchestrator):
        with patch("Engine8_Knowledge.api_routers.scrape_api_v2._get_orchestrator", return_value=mock_orchestrator):
            resp = client.get("/scrape/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_sources"] == 5
        assert data["active_sources"] == 3
        assert data["paused_sources"] == 1

    def test_orchestrator_unavailable(self, client):
        with patch("Engine8_Knowledge.api_routers.scrape_api_v2._get_orchestrator", return_value=None):
            resp = client.get("/scrape/sources")
        assert resp.status_code == 503


# ---------------------------------------------------------------------------
# SAM.gov Endpoints
# ---------------------------------------------------------------------------


class TestSAMEndpoints:
    def test_search_awards(self, client, mock_sam_sync):
        with patch("Engine8_Knowledge.api_routers.scrape_api_v2._get_sam_sync", return_value=mock_sam_sync):
            resp = client.post("/sam/search-awards", json={
                "keywords": ["DCGS"],
                "limit": 10,
            })
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["awards"][0]["award_id"] == "AWD-001"
        assert data["awards"][0]["awardee"] == "GDIT"

    def test_search_opportunities(self, client, mock_sam_sync):
        with patch("Engine8_Knowledge.api_routers.scrape_api_v2._get_sam_sync", return_value=mock_sam_sync):
            resp = client.post("/sam/search-opportunities", json={
                "keywords": ["DCGS"],
                "limit": 10,
            })
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["opportunities"][0]["notice_id"] == "OPP-001"

    def test_monitor_awards(self, client, mock_sam_sync):
        with patch("Engine8_Knowledge.api_routers.scrape_api_v2._get_sam_sync", return_value=mock_sam_sync):
            resp = client.post("/sam/monitor")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["alerts"][0]["alert_type"] == "new_award"

    def test_list_watches(self, client, mock_sam_sync):
        with patch("Engine8_Knowledge.api_routers.scrape_api_v2._get_sam_sync", return_value=mock_sam_sync):
            resp = client.get("/sam/watches")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["watches"][0]["name"] == "DCGS Monitor"

    def test_create_watch(self, client, mock_sam_sync):
        with patch("Engine8_Knowledge.api_routers.scrape_api_v2._get_sam_sync", return_value=mock_sam_sync):
            resp = client.post("/sam/watches", json={
                "name": "ISR Watch",
                "keywords": ["ISR", "surveillance"],
                "naics_codes": ["541512"],
            })
        assert resp.status_code == 200
        data = resp.json()
        assert data["watch_id"] == "w_new"
        assert data["name"] == "ISR Watch"

    def test_remove_watch(self, client, mock_sam_sync):
        with patch("Engine8_Knowledge.api_routers.scrape_api_v2._get_sam_sync", return_value=mock_sam_sync):
            resp = client.delete("/sam/watches/w1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["deleted"] is True
        assert data["watch_id"] == "w1"

    def test_remove_watch_not_found(self, client, mock_sam_sync):
        mock_sam_sync.remove_watch = MagicMock(return_value=False)
        with patch("Engine8_Knowledge.api_routers.scrape_api_v2._get_sam_sync", return_value=mock_sam_sync):
            resp = client.delete("/sam/watches/nonexistent")
        assert resp.status_code == 404

    def test_sam_unavailable(self, client):
        with patch("Engine8_Knowledge.api_routers.scrape_api_v2._get_sam_sync", return_value=None):
            resp = client.post("/sam/search-awards", json={"keywords": ["DCGS"]})
        assert resp.status_code == 503


# ---------------------------------------------------------------------------
# Federal Document Endpoints
# ---------------------------------------------------------------------------


class TestFederalDocEndpoints:
    def test_discover_docs(self, client, mock_doc_pipeline):
        with patch("Engine8_Knowledge.api_routers.scrape_api_v2._get_doc_pipeline", return_value=mock_doc_pipeline):
            resp = client.post("/federal-docs/discover", json={
                "source": "sam_gov",
                "keywords": ["DCGS"],
            })
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["documents"][0]["doc_id"] == "doc_001"

    def test_process_doc(self, client, mock_doc_pipeline):
        with patch("Engine8_Knowledge.api_routers.scrape_api_v2._get_doc_pipeline", return_value=mock_doc_pipeline):
            resp = client.post("/federal-docs/process", json={
                "file_path": "/tmp/test.pdf",
            })
        assert resp.status_code == 200
        data = resp.json()
        assert data["doc_type"] == "RFP"
        assert data["title"] == "DCGS RFP"

    def test_process_doc_not_found(self, client, mock_doc_pipeline):
        mock_doc_pipeline.process_document = AsyncMock(side_effect=FileNotFoundError("File not found: /tmp/missing.pdf"))
        with patch("Engine8_Knowledge.api_routers.scrape_api_v2._get_doc_pipeline", return_value=mock_doc_pipeline):
            resp = client.post("/federal-docs/process", json={
                "file_path": "/tmp/missing.pdf",
            })
        assert resp.status_code == 404

    def test_batch_process(self, client, mock_doc_pipeline):
        with patch("Engine8_Knowledge.api_routers.scrape_api_v2._get_doc_pipeline", return_value=mock_doc_pipeline):
            resp = client.post("/federal-docs/batch", json={
                "doc_refs": [
                    {"doc_id": "d1", "url": "https://sam.gov/doc1.pdf"},
                    {"doc_id": "d2", "url": "https://sam.gov/doc2.pdf"},
                ],
                "max_concurrent": 2,
            })
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert data["processed"] == 2
        assert data["failed"] == 0

    def test_recent_docs_empty(self, client, mock_doc_pipeline):
        """Recent docs with no index returns empty."""
        with patch("Engine8_Knowledge.api_routers.scrape_api_v2._get_doc_pipeline", return_value=mock_doc_pipeline):
            resp = client.get("/federal-docs/recent?limit=10")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["documents"] == []

    def test_doc_pipeline_unavailable(self, client):
        with patch("Engine8_Knowledge.api_routers.scrape_api_v2._get_doc_pipeline", return_value=None):
            resp = client.post("/federal-docs/discover", json={"keywords": ["DCGS"]})
        assert resp.status_code == 503
