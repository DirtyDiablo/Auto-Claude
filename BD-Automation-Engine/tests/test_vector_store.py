"""Tests for BDKnowledgeStore (Engine8_Knowledge/scripts/vector_store.py).

All Qdrant and OpenAI calls are mocked — no external services needed.
"""

import json
import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch, call

import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_qdrant():
    """A mock QdrantClient with typical return values."""
    client = MagicMock()
    client.get_collections.return_value = MagicMock(collections=[])
    client.create_collection.return_value = None
    client.delete_collection.return_value = None
    client.upsert.return_value = None
    # get_collection returns collection info
    info = MagicMock()
    info.points_count = 42
    info.vectors_count = 42
    info.indexed_vectors_count = 42
    info.status = MagicMock(name="green")
    client.get_collection.return_value = info
    # query_points returns empty by default
    client.query_points.return_value = MagicMock(points=[])
    return client


@pytest.fixture()
def mock_openai():
    """A mock OpenAI client for embeddings."""
    client = MagicMock()
    embedding = MagicMock()
    embedding.embedding = [0.1] * 1536
    embedding.index = 0
    response = MagicMock()
    response.data = [embedding]
    client.embeddings.create.return_value = response
    return client


@pytest.fixture()
def store(mock_qdrant, mock_openai):
    """Create a BDKnowledgeStore with mocked clients."""
    with patch("Engine8_Knowledge.scripts.vector_store.QdrantClient", return_value=mock_qdrant), \
         patch("Engine8_Knowledge.scripts.vector_store.openai") as mock_openai_mod:
        mock_openai_mod.OpenAI.return_value = mock_openai
        from Engine8_Knowledge.scripts.vector_store import BDKnowledgeStore
        s = BDKnowledgeStore(in_memory=True)
    # Replace the clients with our mocks (in case __init__ did something else)
    s.client = mock_qdrant
    s.openai_client = mock_openai
    return s


# ===================================================================
# Initialization
# ===================================================================


class TestInitialization:
    def test_store_created(self, store):
        assert store is not None
        assert store.configs is not None

    def test_configs_contain_expected_collections(self, store):
        expected = {"jobs", "contacts", "programs", "documents", "activities"}
        assert expected.issubset(set(store.configs.keys()))

    def test_embedding_cache_initialized(self, store):
        assert isinstance(store._embedding_cache, dict)
        assert store._embedding_cache_max == 256


# ===================================================================
# initialize_collections
# ===================================================================


class TestInitializeCollections:
    def test_creates_all_collections(self, store, mock_qdrant):
        results = store.initialize_collections()
        assert all(v is True for v in results.values())
        assert mock_qdrant.create_collection.call_count == len(store.configs)

    @staticmethod
    def _make_collection_mocks(names):
        """Create mock collection objects with real .name attributes.

        MagicMock(name=...) sets the mock's internal label, not a .name
        attribute. We create the mock first, then assign .name explicitly.
        """
        from types import SimpleNamespace
        return [SimpleNamespace(name=n) for n in names]

    def test_skips_existing_collections(self, store, mock_qdrant):
        # Simulate all collections already existing
        existing = self._make_collection_mocks(store.configs.keys())
        mock_qdrant.get_collections.return_value = MagicMock(collections=existing)
        results = store.initialize_collections()
        assert all(v is True for v in results.values())
        mock_qdrant.create_collection.assert_not_called()

    def test_force_recreate(self, store, mock_qdrant):
        existing = self._make_collection_mocks(store.configs.keys())
        mock_qdrant.get_collections.return_value = MagicMock(collections=existing)
        store.initialize_collections(force_recreate=True)
        assert mock_qdrant.delete_collection.call_count >= 1
        assert mock_qdrant.create_collection.call_count >= 1

    def test_handles_creation_error(self, store, mock_qdrant):
        mock_qdrant.create_collection.side_effect = RuntimeError("disk full")
        results = store.initialize_collections()
        assert any(v is False for v in results.values())


# ===================================================================
# get_collection_stats
# ===================================================================


class TestCollectionStats:
    def test_returns_stats_for_all_collections(self, store):
        stats = store.get_collection_stats()
        # Should have an entry for each configured collection
        for name in store.configs:
            assert name in stats

    def test_stats_contain_expected_fields(self, store):
        stats = store.get_collection_stats()
        first = list(stats.values())[0]
        assert "points_count" in first
        assert "vectors_count" in first

    def test_handles_error_gracefully(self, store, mock_qdrant):
        mock_qdrant.get_collection.side_effect = RuntimeError("timeout")
        stats = store.get_collection_stats()
        first = list(stats.values())[0]
        assert "error" in first


# ===================================================================
# _generate_embedding
# ===================================================================


class TestGenerateEmbedding:
    def test_returns_vector(self, store):
        vec = store._generate_embedding("test query")
        assert isinstance(vec, list)
        assert len(vec) == 1536

    def test_caches_results(self, store, mock_openai):
        store._generate_embedding("same text")
        store._generate_embedding("same text")
        # OpenAI should only be called once due to caching
        assert mock_openai.embeddings.create.call_count == 1

    def test_different_texts_call_api(self, store, mock_openai):
        store._generate_embedding("text one")
        store._generate_embedding("text two")
        assert mock_openai.embeddings.create.call_count == 2

    def test_empty_text_uses_placeholder(self, store, mock_openai):
        store._generate_embedding("")
        call_args = mock_openai.embeddings.create.call_args
        assert call_args[1]["input"] == "empty"

    def test_cache_eviction(self, store, mock_openai):
        store._embedding_cache_max = 2
        store._generate_embedding("a")
        store._generate_embedding("b")
        store._generate_embedding("c")  # should evict "a"
        assert "a" not in store._embedding_cache
        assert "c" in store._embedding_cache

    def test_api_error_propagates(self, store, mock_openai):
        mock_openai.embeddings.create.side_effect = RuntimeError("API error")
        with pytest.raises(RuntimeError, match="API error"):
            store._generate_embedding("will fail")


# ===================================================================
# _generate_embeddings_batch
# ===================================================================


class TestGenerateEmbeddingsBatch:
    def test_batch_returns_list(self, store, mock_openai):
        # Set up multi-item response
        items = []
        for i in range(3):
            item = MagicMock()
            item.embedding = [0.1 * (i + 1)] * 1536
            item.index = i
            items.append(item)
        response = MagicMock()
        response.data = items
        mock_openai.embeddings.create.return_value = response

        results = store._generate_embeddings_batch(["a", "b", "c"])
        assert len(results) == 3
        assert isinstance(results[0], list)

    def test_batch_sanitizes_empty_texts(self, store, mock_openai):
        item = MagicMock()
        item.embedding = [0.1] * 1536
        item.index = 0
        mock_openai.embeddings.create.return_value = MagicMock(data=[item])

        store._generate_embeddings_batch(["", None])
        call_args = mock_openai.embeddings.create.call_args
        assert call_args[1]["input"] == ["empty", "empty"]

    def test_batch_error_propagates(self, store, mock_openai):
        mock_openai.embeddings.create.side_effect = RuntimeError("rate limit")
        with pytest.raises(RuntimeError):
            store._generate_embeddings_batch(["text"])


# ===================================================================
# search
# ===================================================================


class TestSearch:
    def test_search_calls_query_points(self, store, mock_qdrant):
        results = store.search("DCGS analyst", "jobs")
        mock_qdrant.query_points.assert_called_once()
        assert isinstance(results, list)

    def test_search_returns_search_result_objects(self, store, mock_qdrant):
        point = MagicMock()
        point.id = "p1"
        point.score = 0.9
        point.payload = {"title": "Engineer"}
        mock_qdrant.query_points.return_value = MagicMock(points=[point])

        results = store.search("test", "jobs")
        assert len(results) == 1
        assert results[0].id == "p1"
        assert results[0].score == 0.9
        assert results[0].collection == "jobs"

    def test_search_with_filters(self, store, mock_qdrant):
        store.search("test", "contacts", filters={"company": "Leidos"})
        call_args = mock_qdrant.query_points.call_args
        assert call_args[1]["query_filter"] is not None

    def test_search_with_list_filter(self, store, mock_qdrant):
        store.search("test", "contacts", filters={"company": ["Leidos", "GDIT"]})
        call_args = mock_qdrant.query_points.call_args
        assert call_args[1]["query_filter"] is not None

    def test_search_unknown_collection_raises(self, store):
        with pytest.raises(ValueError, match="Unknown collection"):
            store.search("test", "nonexistent")

    def test_search_empty_results(self, store, mock_qdrant):
        mock_qdrant.query_points.return_value = MagicMock(points=[])
        results = store.search("test", "jobs")
        assert results == []

    def test_search_with_score_threshold(self, store, mock_qdrant):
        store.search("test", "jobs", score_threshold=0.7)
        call_args = mock_qdrant.query_points.call_args
        assert call_args[1]["score_threshold"] == 0.7

    def test_search_zero_threshold_passes_none(self, store, mock_qdrant):
        store.search("test", "jobs", score_threshold=0.0)
        call_args = mock_qdrant.query_points.call_args
        assert call_args[1]["score_threshold"] is None


# ===================================================================
# search_all
# ===================================================================


class TestSearchAll:
    def test_search_all_returns_dict(self, store, mock_qdrant):
        results = store.search_all("DCGS")
        assert isinstance(results, dict)
        # Should have an entry for each collection
        for name in store.configs:
            assert name in results

    def test_search_all_specific_collections(self, store, mock_qdrant):
        results = store.search_all("test", collections=["jobs", "contacts"])
        assert set(results.keys()) == {"jobs", "contacts"}

    def test_search_all_handles_per_collection_error(self, store, mock_qdrant):
        mock_qdrant.query_points.side_effect = RuntimeError("timeout")
        results = store.search_all("test", collections=["jobs"])
        assert results["jobs"] == []


# ===================================================================
# Indexing methods
# ===================================================================


class TestIndexing:
    def _make_batch_response(self, count):
        items = []
        for i in range(count):
            item = MagicMock()
            item.embedding = [0.1] * 1536
            item.index = i
            items.append(item)
        return MagicMock(data=items)

    def test_index_jobs(self, store, mock_qdrant, mock_openai):
        mock_openai.embeddings.create.return_value = self._make_batch_response(2)
        jobs = [
            {"title": "Engineer", "company": "Leidos"},
            {"title": "Analyst", "company": "GDIT"},
        ]
        indexed, errors = store.index_jobs(jobs)
        assert indexed == 2
        assert errors == 0
        mock_qdrant.upsert.assert_called_once()

    def test_index_contacts(self, store, mock_qdrant, mock_openai):
        mock_openai.embeddings.create.return_value = self._make_batch_response(1)
        contacts = [{"name": "Jane Doe", "company": "Leidos", "title": "VP"}]
        indexed, errors = store.index_contacts(contacts)
        assert indexed == 1
        assert errors == 0

    def test_index_programs(self, store, mock_qdrant, mock_openai):
        mock_openai.embeddings.create.return_value = self._make_batch_response(1)
        programs = [{"name": "DCGS-A", "prime_contractor": "Leidos"}]
        indexed, errors = store.index_programs(programs)
        assert indexed == 1

    def test_index_documents(self, store, mock_qdrant, mock_openai):
        mock_openai.embeddings.create.return_value = self._make_batch_response(1)
        docs = [{"content": "Test document", "title": "Report"}]
        indexed, errors = store.index_documents(docs)
        assert indexed == 1

    def test_index_unknown_collection_raises(self, store):
        with pytest.raises(ValueError, match="Unknown collection"):
            store._index_data("fake_collection", [{"test": "data"}])

    def test_index_empty_list(self, store, mock_qdrant):
        indexed, errors = store.index_jobs([])
        assert indexed == 0
        assert errors == 0
        mock_qdrant.upsert.assert_not_called()

    def test_index_upsert_error(self, store, mock_qdrant, mock_openai):
        mock_openai.embeddings.create.return_value = self._make_batch_response(1)
        mock_qdrant.upsert.side_effect = RuntimeError("Qdrant down")
        indexed, errors = store.index_jobs([{"title": "Test"}])
        assert errors > 0

    def test_index_embedding_error(self, store, mock_openai):
        mock_openai.embeddings.create.side_effect = RuntimeError("API error")
        indexed, errors = store.index_jobs([{"title": "Test"}])
        assert errors > 0
        assert indexed == 0


# ===================================================================
# bulk_upsert_from_scraper
# ===================================================================


class TestBulkUpsertFromScraper:
    def test_normalizes_contact_fields(self, store, mock_qdrant, mock_openai):
        item = MagicMock()
        item.embedding = [0.1] * 1536
        item.index = 0
        mock_openai.embeddings.create.return_value = MagicMock(data=[item])

        records = [{"Name": "Jane Doe", "Company": "Leidos", "Title": "VP"}]
        indexed, errors = store.bulk_upsert_from_scraper("contacts", records)
        assert indexed == 1

        # Verify the upserted point has normalized field names
        upsert_call = mock_qdrant.upsert.call_args
        points = upsert_call[1]["points"]
        payload = points[0].payload
        assert payload.get("name") == "Jane Doe"
        assert payload.get("_source") == "data_scraper"
        assert payload.get("_ingested_from_scraper") is True

    def test_normalizes_program_fields(self, store, mock_qdrant, mock_openai):
        item = MagicMock()
        item.embedding = [0.1] * 1536
        item.index = 0
        mock_openai.embeddings.create.return_value = MagicMock(data=[item])

        records = [{"Name": "DCGS-A", "Prime": "Leidos", "Agency": "Army"}]
        indexed, _ = store.bulk_upsert_from_scraper("programs", records)
        assert indexed == 1

    def test_custom_source_tag(self, store, mock_qdrant, mock_openai):
        item = MagicMock()
        item.embedding = [0.1] * 1536
        item.index = 0
        mock_openai.embeddings.create.return_value = MagicMock(data=[item])

        records = [{"name": "Test", "company": "GDIT"}]
        store.bulk_upsert_from_scraper("contacts", records, source_tag="custom_source")
        points = mock_qdrant.upsert.call_args[1]["points"]
        assert points[0].payload["_source"] == "custom_source"


# ===================================================================
# Helper methods
# ===================================================================


class TestHelperMethods:
    def test_generate_text_for_embedding(self, store):
        from Engine8_Knowledge.scripts.vector_store import COLLECTION_CONFIGS

        config = COLLECTION_CONFIGS["jobs"]
        data = {"title": "Engineer", "company": "Leidos", "location": "VA"}
        text = store._generate_text_for_embedding(data, config)
        assert "Engineer" in text
        assert "Leidos" in text
        assert "VA" in text

    def test_generate_text_handles_list_fields(self, store):
        from Engine8_Knowledge.scripts.vector_store import COLLECTION_CONFIGS

        config = COLLECTION_CONFIGS["jobs"]
        data = {"title": "Engineer", "company": "Leidos", "clearance": ["TS", "SCI"]}
        text = store._generate_text_for_embedding(data, config)
        assert "TS" in text

    def test_generate_point_id_with_uuid(self, store):
        test_uuid = str(uuid.uuid4())
        data = {"id": test_uuid}
        result = store._generate_point_id(data, "jobs")
        assert result == test_uuid

    def test_generate_point_id_deterministic(self, store):
        data = {"title": "Test", "company": "ABC"}
        id1 = store._generate_point_id(data, "jobs")
        id2 = store._generate_point_id(data, "jobs")
        assert id1 == id2

    def test_generate_point_id_different_collections(self, store):
        data = {"title": "Test"}
        id1 = store._generate_point_id(data, "jobs")
        id2 = store._generate_point_id(data, "contacts")
        assert id1 != id2
