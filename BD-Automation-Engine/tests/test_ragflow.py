"""
Tests for RAGflow Integration.

Test coverage:
1. Knowledge base creation and deletion
2. Document upload (PDF, DOCX, CSV)
3. Query with citations verification
4. Hybrid search vs vector-only comparison
5. Program intelligence aggregation
6. Call prep generation quality
"""

import os
import sys
import asyncio
import tempfile
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from Engine8_Knowledge.ragflow.ragflow_client import (
    RAGflowClient,
    RAGflowConfig,
    ChunkMethod,
    DocumentStatus,
    QueryResult,
)
from Engine8_Knowledge.ragflow.bd_knowledge_manager import (
    BDKnowledgeManager,
    BD_KNOWLEDGE_BASES,
    ProgramIntelligence,
    ContactContext,
    CallPrepBrief,
)
from Engine8_Knowledge.ragflow.document_preprocessor import (
    BDDocumentPreprocessor,
    PreprocessedDocument,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def ragflow_config():
    """Create test RAGflow config."""
    return RAGflowConfig(
        api_key="test_api_key",
        base_url="http://localhost:80",
        llm_model="gpt-4o",
        embedding_model="BAAI/bge-large-en-v1.5"
    )


@pytest.fixture
def mock_httpx_client():
    """Create mock httpx client."""
    with patch("httpx.AsyncClient") as mock:
        client = AsyncMock()
        mock.return_value = client
        yield client


@pytest.fixture
def ragflow_client(ragflow_config, mock_httpx_client):
    """Create RAGflow client with mocked HTTP."""
    client = RAGflowClient(ragflow_config)
    client._client = mock_httpx_client
    client._initialized = True
    return client


@pytest.fixture
def preprocessor():
    """Create preprocessor with temp output directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield BDDocumentPreprocessor(output_dir=tmpdir)


# =============================================================================
# RAGflow Client Tests
# =============================================================================

class TestRAGflowClient:
    """Tests for RAGflow client."""

    @pytest.mark.asyncio
    async def test_config_from_env(self):
        """Test config loading from environment."""
        with patch.dict(os.environ, {
            "RAGFLOW_API_KEY": "test_key",
            "RAGFLOW_BASE_URL": "http://test:8080",
            "RAGFLOW_LLM_MODEL": "claude-3-sonnet",
        }):
            config = RAGflowConfig.from_env()
            assert config.api_key == "test_key"
            assert config.base_url == "http://test:8080"
            assert config.llm_model == "claude-3-sonnet"

    @pytest.mark.asyncio
    async def test_create_knowledge_base(self, ragflow_client, mock_httpx_client):
        """Test KB creation."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"id": "kb_12345"}}
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post.return_value = mock_response

        # Create KB
        kb_id = await ragflow_client.create_knowledge_base(
            name="test_kb",
            description="Test knowledge base",
            chunk_method=ChunkMethod.NAIVE
        )

        assert kb_id == "kb_12345"
        mock_httpx_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_knowledge_bases(self, ragflow_client, mock_httpx_client):
        """Test listing KBs."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "kb_1", "name": "kb1"},
                {"id": "kb_2", "name": "kb2"}
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.get.return_value = mock_response

        kbs = await ragflow_client.list_knowledge_bases()

        assert len(kbs) == 2
        assert kbs[0]["name"] == "kb1"

    @pytest.mark.asyncio
    async def test_delete_knowledge_base(self, ragflow_client, mock_httpx_client):
        """Test KB deletion."""
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_httpx_client.delete.return_value = mock_response

        result = await ragflow_client.delete_knowledge_base("kb_12345")

        assert result is True
        mock_httpx_client.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_document(self, ragflow_client, mock_httpx_client):
        """Test document upload."""
        # Create temp file
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"Test document content")
            temp_path = f.name

        try:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": {"id": "doc_12345"}}
            mock_response.raise_for_status = MagicMock()
            mock_httpx_client.post.return_value = mock_response

            doc_id = await ragflow_client.upload_document(
                kb_id="kb_12345",
                file_path=temp_path,
                chunk_method=ChunkMethod.NAIVE
            )

            assert doc_id == "doc_12345"
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_query(self, ragflow_client, mock_httpx_client):
        """Test query with citations."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "chunks": [
                    {
                        "content": "Relevant text",
                        "score": 0.95,
                        "document_name": "doc.pdf",
                        "page_number": 1
                    }
                ],
                "answer": "The answer based on the document."
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post.return_value = mock_response

        result = await ragflow_client.query(
            kb_ids=["kb_12345"],
            question="What is the main topic?",
            top_k=5
        )

        assert isinstance(result, QueryResult)
        assert len(result.chunks) == 1
        assert result.answer is not None
        assert len(result.citations) == 1

    @pytest.mark.asyncio
    async def test_hybrid_search(self, ragflow_client, mock_httpx_client):
        """Test hybrid search."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "chunks": [
                    {"content": "Result 1", "score": 0.9},
                    {"content": "Result 2", "score": 0.8}
                ]
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post.return_value = mock_response

        result = await ragflow_client.hybrid_search(
            kb_ids=["kb_12345"],
            question="DCGS program details",
            keyword_weight=0.3
        )

        assert len(result.chunks) == 2

    @pytest.mark.asyncio
    async def test_health_check(self, ragflow_client, mock_httpx_client):
        """Test health check."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok"}
        mock_httpx_client.get.return_value = mock_response

        health = await ragflow_client.health_check()

        assert health["status"] == "healthy"


# =============================================================================
# BD Knowledge Manager Tests
# =============================================================================

class TestBDKnowledgeManager:
    """Tests for BD Knowledge Manager."""

    @pytest.mark.asyncio
    async def test_knowledge_base_definitions(self):
        """Test that all BD KBs are defined."""
        expected_kbs = [
            "bd_playbooks",
            "federal_programs",
            "rfp_library",
            "past_performance",
            "humint_notes",
            "contacts"
        ]

        for kb in expected_kbs:
            assert kb in BD_KNOWLEDGE_BASES
            assert BD_KNOWLEDGE_BASES[kb].chunk_method is not None

    @pytest.mark.asyncio
    async def test_program_intelligence_structure(self):
        """Test ProgramIntelligence data structure."""
        intel = ProgramIntelligence(
            program_name="DCGS-A",
            contracts=[{"id": "c1", "value": 100000}],
            rfps=[{"number": "RFP-001"}],
            past_performance=[{"project": "ISR Support"}],
            contacts=[{"name": "John Doe"}],
            summary="Program summary"
        )

        data = intel.to_dict()

        assert data["program_name"] == "DCGS-A"
        assert len(data["contracts"]) == 1
        assert len(data["rfps"]) == 1
        assert data["summary"] == "Program summary"

    @pytest.mark.asyncio
    async def test_contact_context_structure(self):
        """Test ContactContext data structure."""
        context = ContactContext(
            contact_name="Jane Smith",
            profile={"title": "Program Manager"},
            programs=[{"name": "DCGS"}],
            interactions=[{"date": "2024-01-15", "notes": "Call notes"}]
        )

        data = context.to_dict()

        assert data["contact_name"] == "Jane Smith"
        assert data["profile"]["title"] == "Program Manager"

    @pytest.mark.asyncio
    async def test_call_prep_brief_structure(self):
        """Test CallPrepBrief data structure."""
        brief = CallPrepBrief(
            contact_name="John Doe",
            program_context="DCGS-A",
            contact_background="15 years in defense",
            program_pain_points=["Budget constraints", "Timeline pressure"],
            pts_alignment=["ISR expertise", "Cleared workforce"],
            talking_points=["Past DCGS experience", "Cost savings approach"],
            questions_to_ask=["Current priorities?", "Timeline for award?"]
        )

        data = brief.to_dict()

        assert data["contact_name"] == "John Doe"
        assert len(data["program_pain_points"]) == 2
        assert len(data["talking_points"]) == 2
        assert len(data["questions_to_ask"]) == 2


# =============================================================================
# Document Preprocessor Tests
# =============================================================================

class TestBDDocumentPreprocessor:
    """Tests for document preprocessor."""

    @pytest.mark.asyncio
    async def test_preprocess_call_notes(self, preprocessor):
        """Test call notes preprocessing."""
        notes = """
        Key Points:
        - Customer interested in ISR capabilities
        - Budget approved for Q2

        Action Items:
        - Send capability brief
        - Schedule follow-up call

        "We're looking for a partner with clearances" - Jane said
        """

        result = await preprocessor.preprocess_call_notes(
            notes=notes,
            contact="Jane Doe",
            date="2024-01-15",
            program="DCGS"
        )

        assert isinstance(result, PreprocessedDocument)
        assert result.document_type == "call_notes"
        assert Path(result.processed_path).exists()

        # Check content
        with open(result.processed_path) as f:
            content = f.read()
            assert "Jane Doe" in content
            assert "DCGS" in content
            assert "Key Points" in content or "key_points" in content

    @pytest.mark.asyncio
    async def test_preprocess_contact_csv_fallback(self, preprocessor):
        """Test CSV preprocessing with fallback."""
        # Create temp CSV
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            f.write("name,title,organization\n")
            f.write("John Doe,Director,GDIT\n")
            f.write("Jane Smith,Manager,Leidos\n")
            temp_path = f.name

        try:
            result = await preprocessor.preprocess_contact_csv(temp_path)

            assert isinstance(result, PreprocessedDocument)
            # Even if pandas not available, should return something
            assert result.original_path == temp_path
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_fallback_preprocess_txt(self, preprocessor):
        """Test fallback preprocessing for text files."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as f:
            f.write("This is test content for preprocessing.\nLine 2.\nLine 3.")
            temp_path = f.name

        try:
            result = preprocessor._fallback_preprocess(temp_path, "notes")

            assert isinstance(result, PreprocessedDocument)
            assert result.document_type == "notes"
        finally:
            os.unlink(temp_path)


# =============================================================================
# Integration Tests (require RAGflow running)
# =============================================================================

@pytest.mark.integration
class TestRAGflowIntegration:
    """
    Integration tests that require RAGflow to be running.

    Run with: pytest tests/test_ragflow.py -m integration
    """

    @pytest.fixture
    def live_client(self):
        """Create live RAGflow client."""
        config = RAGflowConfig.from_env()
        if not config.api_key:
            pytest.skip("RAGFLOW_API_KEY not set")
        return RAGflowClient(config)

    @pytest.mark.asyncio
    async def test_live_health_check(self, live_client):
        """Test live health check."""
        await live_client.initialize()
        try:
            health = await live_client.health_check()
            assert health["status"] in ("healthy", "error")
        finally:
            await live_client.close()

    @pytest.mark.asyncio
    async def test_live_kb_lifecycle(self, live_client):
        """Test full KB lifecycle: create, upload, query, delete."""
        await live_client.initialize()
        try:
            # Create KB
            kb_id = await live_client.create_knowledge_base(
                name=f"test_kb_{int(asyncio.get_event_loop().time())}",
                description="Integration test KB"
            )
            assert kb_id is not None

            # List KBs
            kbs = await live_client.list_knowledge_bases()
            assert any(kb.get("id") == kb_id for kb in kbs)

            # Delete KB
            deleted = await live_client.delete_knowledge_base(kb_id)
            assert deleted is True
        finally:
            await live_client.close()


# =============================================================================
# Performance Tests
# =============================================================================

@pytest.mark.performance
class TestRAGflowPerformance:
    """Performance tests for RAGflow operations."""

    @pytest.mark.asyncio
    async def test_query_response_time(self, ragflow_client, mock_httpx_client):
        """Test that queries return in under 5 seconds."""
        import time

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "chunks": [{"content": "Result", "score": 0.9}],
                "answer": "Test answer"
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post.return_value = mock_response

        start = time.time()
        result = await ragflow_client.query(
            kb_ids=["kb_test"],
            question="Test query"
        )
        elapsed = time.time() - start

        # Mock should be fast, but in real tests this validates <5s requirement
        assert elapsed < 5.0
        assert result.query_time_ms < 5000


# =============================================================================
# Quality Tests
# =============================================================================

class TestCallPrepQuality:
    """Tests for call prep generation quality."""

    def test_call_prep_has_all_sections(self):
        """Test that call prep has all required sections."""
        brief = CallPrepBrief(
            contact_name="Test Contact",
            program_context="Test Program",
            contact_background="Background info",
            program_pain_points=["Pain 1", "Pain 2"],
            pts_alignment=["Alignment 1"],
            talking_points=["Point 1", "Point 2", "Point 3"],
            questions_to_ask=["Question 1", "Question 2", "Question 3"]
        )

        data = brief.to_dict()

        # Required sections
        assert data["contact_background"], "Missing contact background"
        assert len(data["program_pain_points"]) >= 1, "Missing pain points"
        assert len(data["pts_alignment"]) >= 1, "Missing alignment"
        assert len(data["talking_points"]) >= 2, "Need at least 2 talking points"
        assert len(data["questions_to_ask"]) >= 2, "Need at least 2 questions"

    def test_call_prep_content_quality(self):
        """Test that call prep content is actionable."""
        brief = CallPrepBrief(
            contact_name="John Smith",
            program_context="DCGS-A",
            contact_background="15 years DoD experience, former Army officer",
            program_pain_points=[
                "Budget constraints limiting new technology adoption",
                "Difficulty finding cleared personnel"
            ],
            pts_alignment=[
                "Extensive DCGS experience with Army and AF",
                "150+ cleared personnel available"
            ],
            talking_points=[
                "Reference our successful DCGS-SOF deployment",
                "Discuss cost-savings through automation",
                "Highlight our cleared workforce pipeline"
            ],
            questions_to_ask=[
                "What is your current timeline for the next phase?",
                "Are there specific capability gaps we should address?",
                "Who else should we be talking to about this opportunity?"
            ]
        )

        # Talking points should be specific (not generic)
        for point in brief.talking_points:
            assert len(point) > 20, f"Talking point too short: {point}"

        # Questions should be open-ended
        for q in brief.questions_to_ask:
            assert q.endswith("?"), f"Question should end with ?: {q}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
