"""
Phase 24A — Crawl4AI Engine Tests

Tests AI-native web crawler: initialization, URL crawling, site crawling,
schema extraction, competitor career pages, stealth, and singleton.
All external dependencies (crawl4ai, httpx) are mocked.
"""

import pytest
import sys
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from Engine8_Knowledge.scrapers.crawl4ai_engine import (
    Crawl4AIEngine,
    CrawlResult,
    JobExtraction,
    ContractExtraction,
    get_crawl4ai_engine,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def engine():
    """Fresh engine instance per test."""
    return Crawl4AIEngine(
        llm_model="gpt-4o-mini", stealth_level="medium", max_concurrent=5
    )


@pytest.fixture
def mock_crawl4ai_modules():
    """
    Inject fake crawl4ai modules into sys.modules so that inline imports
    inside crawl_url (from crawl4ai import CrawlerRunConfig, ...) succeed.
    """
    mock_crawl4ai = MagicMock()
    mock_extraction = MagicMock()

    # CrawlerRunConfig: just returns a MagicMock when instantiated
    mock_crawl4ai.CrawlerRunConfig = MagicMock()
    mock_extraction.LLMExtractionStrategy = MagicMock()

    originals = {}
    modules_to_mock = {
        "crawl4ai": mock_crawl4ai,
        "crawl4ai.extraction_strategy": mock_extraction,
    }
    for mod_name, mock_mod in modules_to_mock.items():
        originals[mod_name] = sys.modules.get(mod_name)
        sys.modules[mod_name] = mock_mod

    yield mock_crawl4ai, mock_extraction

    # Restore
    for mod_name in modules_to_mock:
        if originals[mod_name] is None:
            sys.modules.pop(mod_name, None)
        else:
            sys.modules[mod_name] = originals[mod_name]


@pytest.fixture
def mock_crawler_result():
    """Build a mock crawl4ai CrawlerRunResult."""
    result = MagicMock()
    result.html = "<html><body>Test</body></html>"
    result.markdown = "# Test Page\nSome content here"
    result.extracted_content = '[{"title": "Software Engineer", "company": "GDIT"}]'
    result.links = {"internal": [{"href": "https://example.com/page2"}]}
    result.title = "Test Page"
    result.status_code = 200
    return result


@pytest.fixture
def mock_httpx_module():
    """
    Create a mock httpx module for patching inline `import httpx`.
    """
    mock_response = MagicMock()
    mock_response.text = "<html><body>Fallback content</body></html>"
    mock_response.status_code = 200

    mock_client_instance = AsyncMock()
    mock_client_instance.get = AsyncMock(return_value=mock_response)
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=None)

    mock_httpx = MagicMock()
    mock_httpx.AsyncClient = MagicMock(return_value=mock_client_instance)

    return mock_httpx, mock_response


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------


class TestInit:
    def test_init(self, engine):
        assert engine.llm_model == "gpt-4o-mini"
        assert engine.stealth_level == "medium"
        assert engine.max_concurrent == 5
        assert engine._crawler is None
        assert "jobs" in engine._extraction_schemas
        assert "contracts" in engine._extraction_schemas
        assert "contacts" in engine._extraction_schemas

    def test_init_custom_model(self):
        eng = Crawl4AIEngine(
            llm_model="claude-3-haiku", stealth_level="high", max_concurrent=10
        )
        assert eng.llm_model == "claude-3-haiku"
        assert eng.stealth_level == "high"
        assert eng.max_concurrent == 10


# ---------------------------------------------------------------------------
# Crawl URL
# ---------------------------------------------------------------------------


class TestCrawlUrl:
    @pytest.mark.asyncio
    async def test_crawl_url_fallback(self, engine, mock_httpx_module):
        """When crawl4ai is not installed, uses httpx fallback."""
        mock_httpx, mock_response = mock_httpx_module

        with patch.object(engine, "_get_crawler", new=AsyncMock(return_value=None)):
            with patch.dict(sys.modules, {"httpx": mock_httpx}):
                result = await engine.crawl_url("https://example.com")

        assert isinstance(result, CrawlResult)
        assert result.url == "https://example.com"
        assert "Fallback content" in result.raw_html
        assert result.success is True

    @pytest.mark.asyncio
    async def test_crawl_url_success(
        self, engine, mock_crawler_result, mock_crawl4ai_modules
    ):
        """Successful crawl via AsyncWebCrawler."""
        mock_crawler = AsyncMock()
        mock_crawler.arun = AsyncMock(return_value=mock_crawler_result)

        with patch.object(
            engine, "_get_crawler", new=AsyncMock(return_value=mock_crawler)
        ):
            result = await engine.crawl_url(
                "https://example.com/jobs", extraction_strategy="auto"
            )

        assert result.success is True
        assert result.url == "https://example.com/jobs"
        assert result.raw_html == "<html><body>Test</body></html>"
        assert result.markdown == "# Test Page\nSome content here"
        assert len(result.extracted_data) == 1
        assert result.extracted_data[0]["title"] == "Software Engineer"
        assert result.crawl_time_ms >= 0

    @pytest.mark.asyncio
    async def test_crawl_url_error_handling(self, engine, mock_crawl4ai_modules):
        """Errors during crawl return a result with success=False."""
        mock_crawler = AsyncMock()
        mock_crawler.arun = AsyncMock(side_effect=Exception("Connection timeout"))

        with patch.object(
            engine, "_get_crawler", new=AsyncMock(return_value=mock_crawler)
        ):
            result = await engine.crawl_url("https://example.com/broken")

        assert result.success is False
        assert "Connection timeout" in result.error
        assert result.url == "https://example.com/broken"


# ---------------------------------------------------------------------------
# Crawl Site
# ---------------------------------------------------------------------------


class TestCrawlSite:
    @pytest.mark.asyncio
    async def test_crawl_site_basic(self, engine):
        """Crawl a site with internal link following."""
        page1 = CrawlResult(
            url="https://example.com",
            markdown="Page 1 content",
            links=["https://example.com/page2", "https://example.com/page3"],
            success=True,
        )
        page2 = CrawlResult(
            url="https://example.com/page2",
            markdown="Page 2 content",
            links=[],
            success=True,
        )
        page3 = CrawlResult(
            url="https://example.com/page3",
            markdown="Page 3 content",
            links=[],
            success=True,
        )

        async def mock_crawl_url(url, extraction_strategy="auto"):
            if url == "https://example.com":
                return page1
            elif url == "https://example.com/page2":
                return page2
            elif url == "https://example.com/page3":
                return page3
            return CrawlResult(url=url, success=False, error="not found")

        engine._seen_hashes = set()
        with patch.object(engine, "crawl_url", side_effect=mock_crawl_url):
            results = await engine.crawl_site("https://example.com", max_pages=10)

        assert len(results) >= 1
        assert all(isinstance(r, CrawlResult) for r in results)

    @pytest.mark.asyncio
    async def test_crawl_site_with_filter(self, engine):
        """URL filter restricts which pages are visited."""
        page1 = CrawlResult(
            url="https://example.com",
            markdown="Root",
            links=["https://example.com/jobs/1", "https://example.com/about"],
            success=True,
        )
        job_page = CrawlResult(
            url="https://example.com/jobs/1",
            markdown="Job posting",
            links=[],
            success=True,
        )

        async def mock_crawl_url(url, extraction_strategy="auto"):
            if url == "https://example.com":
                return page1
            elif url == "https://example.com/jobs/1":
                return job_page
            return CrawlResult(url=url, success=False, error="not found")

        engine._seen_hashes = set()
        with patch.object(engine, "crawl_url", side_effect=mock_crawl_url):
            results = await engine.crawl_site(
                "https://example.com",
                max_pages=10,
                url_filter=lambda u: "/jobs/" in u or u == "https://example.com",
            )

        urls = [r.url for r in results]
        assert "https://example.com/about" not in urls

    @pytest.mark.asyncio
    async def test_crawl_site_dedup(self, engine):
        """Duplicate content hashes are skipped."""
        same_hash = "abcdef1234567890"
        page1 = CrawlResult(
            url="https://example.com",
            markdown="Same content",
            content_hash=same_hash,
            links=["https://example.com/page2"],
            success=True,
        )
        page2 = CrawlResult(
            url="https://example.com/page2",
            markdown="Same content",
            content_hash=same_hash,
            links=[],
            success=True,
        )

        async def mock_crawl_url(url, extraction_strategy="auto"):
            if url == "https://example.com":
                return page1
            return page2

        engine._seen_hashes = set()
        with patch.object(engine, "crawl_url", side_effect=mock_crawl_url):
            results = await engine.crawl_site("https://example.com", max_pages=10)

        # Only the first page should be returned since page2 has the same hash
        assert len(results) == 1


# ---------------------------------------------------------------------------
# Schema Extraction
# ---------------------------------------------------------------------------


class TestSchemaExtraction:
    @pytest.mark.asyncio
    async def test_crawl_with_schema(self, engine):
        """Extract data matching a Pydantic schema."""
        mock_result = CrawlResult(
            url="https://example.com/jobs",
            extracted_data=[
                {"title": "Engineer", "company": "GDIT", "location": "VA"},
                {"title": "Analyst", "company": "Leidos", "location": "MD"},
            ],
        )

        with patch.object(engine, "crawl_url", new=AsyncMock(return_value=mock_result)):
            items = await engine.crawl_with_schema(
                "https://example.com/jobs", JobExtraction
            )

        assert len(items) == 2
        assert all(isinstance(i, JobExtraction) for i in items)
        assert items[0].title == "Engineer"
        assert items[1].company == "Leidos"

    def test_job_extraction_schema(self):
        """JobExtraction schema validates correctly."""
        job = JobExtraction(
            title="DCGS Analyst",
            company="GDIT",
            location="San Diego, CA",
            clearance="TS/SCI",
            url="https://gdit.com/jobs/123",
        )
        assert job.title == "DCGS Analyst"
        assert job.clearance == "TS/SCI"
        assert job.requirements == []

    def test_contract_extraction_schema(self):
        """ContractExtraction schema validates correctly."""
        contract = ContractExtraction(
            award_title="DCGS Modernization",
            awardee="Raytheon",
            value="$500M",
            naics="541512",
            agency="Department of Defense",
        )
        assert contract.award_title == "DCGS Modernization"
        assert contract.naics == "541512"


# ---------------------------------------------------------------------------
# Competitor Career Crawl
# ---------------------------------------------------------------------------


class TestCompetitorCrawl:
    @pytest.mark.asyncio
    async def test_crawl_competitor_known(self, engine):
        """Known competitor (GDIT) uses pre-configured URL."""
        mock_result = CrawlResult(
            url="https://www.gdit.com/careers/",
            extracted_data=[
                {"title": "Sys Admin", "company": "GDIT"},
                {"title": "SW Dev", "company": "GDIT"},
            ],
        )

        with patch.object(engine, "crawl_url", new=AsyncMock(return_value=mock_result)):
            data = await engine.crawl_competitor_careers("GDIT")

        assert len(data) == 2
        assert data[0]["title"] == "Sys Admin"

    @pytest.mark.asyncio
    async def test_crawl_competitor_unknown(self, engine):
        """Unknown competitor falls back to auto-detection via search."""
        mock_result = CrawlResult(
            url="https://www.google.com/search?q=AcmeCorp+careers+jobs",
            extracted_data=[{"title": "Intern", "company": "AcmeCorp"}],
        )

        with patch.object(engine, "crawl_url", new=AsyncMock(return_value=mock_result)):
            data = await engine.crawl_competitor_careers("AcmeCorp")

        assert len(data) == 1
        assert data[0]["company"] == "AcmeCorp"


# ---------------------------------------------------------------------------
# Stealth Configuration
# ---------------------------------------------------------------------------


class TestStealth:
    def test_configure_stealth_low(self, engine):
        engine.configure_stealth("low")
        assert engine.stealth_level == "low"

    def test_configure_stealth_high(self, engine):
        engine.configure_stealth("high")
        assert engine.stealth_level == "high"


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------


class TestSingleton:
    def test_singleton(self):
        """get_crawl4ai_engine returns the same instance."""
        import Engine8_Knowledge.scrapers.crawl4ai_engine as mod

        mod._engine = None  # Reset
        e1 = get_crawl4ai_engine(llm_model="gpt-4o-mini")
        e2 = get_crawl4ai_engine()
        assert e1 is e2
        mod._engine = None  # Clean up
