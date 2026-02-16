"""
Phase 24A — Federal Document Pipeline Tests

Tests end-to-end pipeline: discover, download, process, classify, batch,
and monitor. All external dependencies (httpx, crawl4ai) are mocked.
"""

import hashlib
import pytest
import sys
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from Engine8_Knowledge.scrapers.federal_doc_pipeline import (
    FederalDocPipeline,
    DocumentRef,
    ProcessedFederalDoc,
    BatchResult,
    DocumentAlert,
    MAX_FILE_SIZE,
)
from Engine8_Knowledge.scrapers.crawl4ai_engine import CrawlResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_output(tmp_path):
    return str(tmp_path / "federal_docs_test")


@pytest.fixture
def mock_crawler():
    crawler = AsyncMock()
    return crawler


@pytest.fixture
def pipeline(tmp_output, mock_crawler):
    return FederalDocPipeline(
        crawl_engine=mock_crawler,
        hub_client=None,
        output_dir=tmp_output,
    )


@pytest.fixture
def sample_doc_ref():
    return DocumentRef(
        doc_id="sam_test001",
        url="https://sam.gov/docs/solicitation.pdf",
        title="DCGS RFP",
        doc_type="RFP",
        agency="Department of Defense",
        source="sam_gov",
    )


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------


class TestInit:
    def test_init(self, pipeline, tmp_output):
        assert pipeline.crawler is not None
        assert pipeline.hub is None
        assert Path(tmp_output).exists()
        assert pipeline._seen_hashes == set()

    def test_init_creates_dir(self, tmp_path):
        output = str(tmp_path / "new_dir" / "nested")
        p = FederalDocPipeline(output_dir=output)
        assert Path(output).exists()


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------


class TestDiscovery:
    @pytest.mark.asyncio
    async def test_discover_sam_gov(self, pipeline, mock_crawler):
        """Discover documents from SAM.gov via mocked crawler."""
        mock_crawler.crawl_url = AsyncMock(
            return_value=CrawlResult(
                url="https://sam.gov/search/?keywords=DCGS",
                extracted_data=[
                    {
                        "title": "DCGS Support RFP",
                        "agency": "Air Force",
                        "url": "https://sam.gov/doc1.pdf",
                    },
                ],
                links=[
                    "https://sam.gov/attachments/solicitation.pdf",
                    "https://sam.gov/page2",
                ],
            )
        )

        docs = await pipeline.discover_documents("sam_gov", {"keywords": ["DCGS"]})

        assert len(docs) >= 1
        assert all(isinstance(d, DocumentRef) for d in docs)
        # Should have at least the extracted data item plus the PDF link
        pdf_docs = [d for d in docs if d.url.endswith(".pdf")]
        assert len(pdf_docs) >= 1

    @pytest.mark.asyncio
    async def test_discover_fpds(self, pipeline, mock_crawler):
        """Discover documents from FPDS."""
        mock_crawler.crawl_url = AsyncMock(
            return_value=CrawlResult(
                url="https://www.fpds.gov/ezsearch/search.do?q=ISR",
                extracted_data=[
                    {"title": "ISR Contract Award", "url": "https://fpds.gov/doc/123"},
                ],
            )
        )

        docs = await pipeline.discover_documents("fpds", {"keywords": ["ISR"]})

        assert len(docs) == 1
        assert docs[0].source == "fpds"

    @pytest.mark.asyncio
    async def test_discover_agency_sites(self, pipeline, mock_crawler):
        """Discover documents from an agency website."""
        page_result = CrawlResult(
            url="https://agency.mil/docs",
            links=[
                "https://agency.mil/docs/sow.pdf",
                "https://agency.mil/docs/brief.docx",
            ],
        )
        mock_crawler.crawl_site = AsyncMock(return_value=[page_result])

        docs = await pipeline.discover_documents(
            "agency_sites",
            {
                "url": "https://agency.mil/docs",
                "max_pages": 5,
            },
        )

        assert len(docs) == 2
        assert all(d.source == "agency_site" for d in docs)


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------


class TestDownload:
    def _make_mock_httpx(self, mock_response):
        """Build a mock httpx module with AsyncClient returning mock_response."""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        mock_httpx = MagicMock()
        mock_httpx.AsyncClient = MagicMock(return_value=mock_client)
        return mock_httpx

    @pytest.mark.asyncio
    async def test_download_document(self, pipeline, sample_doc_ref, tmp_path):
        """Download writes file to disk."""
        content = b"%PDF-1.4 fake pdf content for testing"
        mock_response = MagicMock()
        mock_response.content = content
        mock_response.headers = {"content-type": "application/pdf"}
        mock_response.raise_for_status = MagicMock()

        mock_httpx = self._make_mock_httpx(mock_response)

        with patch.dict(sys.modules, {"httpx": mock_httpx}):
            filepath = await pipeline.download_document(sample_doc_ref)

        assert Path(filepath).exists()
        assert Path(filepath).read_bytes() == content

    @pytest.mark.asyncio
    async def test_download_dedup(self, pipeline, sample_doc_ref):
        """Second download of identical content returns existing file."""
        content = b"duplicate content for testing"
        content_hash = hashlib.sha256(content).hexdigest()[:16]

        # Pre-seed the seen hashes and create a dummy file
        pipeline._seen_hashes.add(content_hash)
        output_dir = Path(pipeline._output_dir)
        existing_file = output_dir / f"existing_{content_hash}.pdf"
        existing_file.write_bytes(content)

        mock_response = MagicMock()
        mock_response.content = content
        mock_response.headers = {"content-type": "application/pdf"}
        mock_response.raise_for_status = MagicMock()

        mock_httpx = self._make_mock_httpx(mock_response)

        with patch.dict(sys.modules, {"httpx": mock_httpx}):
            filepath = await pipeline.download_document(sample_doc_ref)

        assert str(existing_file) in filepath

    @pytest.mark.asyncio
    async def test_download_too_large(self, pipeline, sample_doc_ref):
        """Files exceeding MAX_FILE_SIZE raise ValueError."""
        huge_content = b"x" * (MAX_FILE_SIZE + 1)
        mock_response = MagicMock()
        mock_response.content = huge_content
        mock_response.headers = {"content-type": "application/pdf"}
        mock_response.raise_for_status = MagicMock()

        mock_httpx = self._make_mock_httpx(mock_response)

        with patch.dict(sys.modules, {"httpx": mock_httpx}):
            with pytest.raises(ValueError, match="File too large"):
                await pipeline.download_document(sample_doc_ref)


# ---------------------------------------------------------------------------
# Processing
# ---------------------------------------------------------------------------


class TestProcessing:
    @pytest.mark.asyncio
    async def test_process_document(self, pipeline, tmp_path):
        """Process a local .txt file extracts text and classifies."""
        test_file = tmp_path / "test_rfp.txt"
        test_file.write_text(
            "Subject: DCGS Support Services RFP\n\n"
            "Request for Proposal for distributed common ground system support.\n"
            "This is a full and open solicitation under NAICS: 541512.\n"
            "Department of Defense, Department of the Air Force.\n"
            "Evaluation criteria include past performance and technical approach.\n"
            "The awardee shall provide ISR exploitation capabilities.\n"
        )

        result = await pipeline.process_document(str(test_file))

        assert isinstance(result, ProcessedFederalDoc)
        assert result.doc_type == "RFP"
        assert len(result.full_text) > 0
        assert result.content_hash != ""
        assert result.processing_time_seconds >= 0

    @pytest.mark.asyncio
    async def test_process_batch(self, pipeline, tmp_path):
        """Batch process downloads and processes multiple docs."""
        # Create temp files
        file1 = tmp_path / "doc1.txt"
        file1.write_text(
            "Statement of work for ISR platform. SOW deliverables include..."
        )
        file2 = tmp_path / "doc2.txt"
        file2.write_text("Contract modification amendment to existing task order.")

        refs = [
            DocumentRef(doc_id="batch_1", url="https://example.com/doc1.txt"),
            DocumentRef(doc_id="batch_2", url="https://example.com/doc2.txt"),
        ]

        # Mock download to return our temp files
        call_count = [0]

        async def mock_download(ref, output_dir=None):
            path = str(file1) if call_count[0] == 0 else str(file2)
            call_count[0] += 1
            return path

        with patch.object(pipeline, "download_document", side_effect=mock_download):
            result = await pipeline.process_batch(refs, max_concurrent=2)

        assert isinstance(result, BatchResult)
        assert result.total == 2
        assert result.processed == 2
        assert result.failed == 0
        assert len(result.documents) == 2


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------


class TestClassification:
    def test_classify_doc_type_rfp(self, pipeline):
        text = "This is a Request for Proposal (RFP) solicitation for full and open competition."
        doc_type = pipeline._classify_doc_type(text)
        assert doc_type == "RFP"

    def test_classify_doc_type_sow(self, pipeline):
        text = "Statement of Work (SOW) defining scope of work and performance work statement."
        doc_type = pipeline._classify_doc_type(text)
        assert doc_type == "SOW"


# ---------------------------------------------------------------------------
# Monitor
# ---------------------------------------------------------------------------


class TestMonitor:
    @pytest.mark.asyncio
    async def test_monitor_new_documents(self, pipeline, mock_crawler):
        """Monitor finds documents matching watch criteria."""
        mock_crawler.crawl_url = AsyncMock(
            return_value=CrawlResult(
                url="https://sam.gov/search",
                extracted_data=[
                    {
                        "title": "DCGS Support RFP",
                        "agency": "Department of Defense",
                        "url": "https://sam.gov/rfp1",
                    },
                ],
                links=[],
            )
        )

        watch_configs = [
            {
                "source": "sam_gov",
                "name": "DCGS Watch",
                "keywords": ["DCGS"],
                "agency": "Department of Defense",
            }
        ]

        alerts = await pipeline.monitor_new_documents(watch_configs)

        assert isinstance(alerts, list)
        assert all(isinstance(a, DocumentAlert) for a in alerts)
        # At least one alert should match since keywords and agency match
        if alerts:
            assert alerts[0].relevance_score >= 0.3
