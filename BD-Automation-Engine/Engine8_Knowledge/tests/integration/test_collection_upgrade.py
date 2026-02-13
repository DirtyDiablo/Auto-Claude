"""
Phase 22A — Collection Upgrade Tests

Tests BM25 sparse vector upgrade, verify, rollback, dry-run.
Uses mocking — does not require running Qdrant.
"""

from unittest.mock import MagicMock, patch
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from Engine8_Knowledge.search.collection_upgrade import (
    upgrade_collection, upgrade_all, verify_upgrade,
    rollback_upgrade, _extract_text, KNOWN_COLLECTIONS,
)


# ---------------------------------------------------------------------------
# TestUpgradeCollection
# ---------------------------------------------------------------------------

class TestUpgradeCollection:
    """Test single collection upgrade."""

    def test_already_upgraded(self):
        with patch("Engine8_Knowledge.search.collection_upgrade.QdrantClient") as MockClient:
            client = MockClient.return_value
            info = MagicMock()
            info.config.params.sparse_vectors = {"bm25": MagicMock()}
            info.vectors_count = 1000
            client.get_collection.return_value = info
            result = upgrade_collection("bd_contacts")
        assert result["status"] == "already_upgraded"

    def test_dry_run(self):
        with patch("Engine8_Knowledge.search.collection_upgrade.QdrantClient") as MockClient:
            client = MockClient.return_value
            info = MagicMock()
            info.config.params.sparse_vectors = None
            info.config.params.vectors = MagicMock(size=1536)
            info.vectors_count = 5000
            client.get_collection.return_value = info
            result = upgrade_collection("bd_contacts", dry_run=True)
        assert result["status"] == "dry_run"
        assert result["vectors_count"] == 5000
        assert result["estimated_batches"] == 10

    def test_upgrade_success(self):
        with patch("Engine8_Knowledge.search.collection_upgrade.QdrantClient") as MockClient, \
             patch("Engine8_Knowledge.search.collection_upgrade.SparseTextEmbedding") as MockSparse, \
             patch("Engine8_Knowledge.search.collection_upgrade._save_progress"), \
             patch("Engine8_Knowledge.search.collection_upgrade._clear_progress"):
            client = MockClient.return_value
            # Original collection info
            info = MagicMock()
            info.config.params.sparse_vectors = None
            info.config.params.vectors = MagicMock(size=1536)
            info.vectors_count = 2

            # New collection info after migration
            new_info = MagicMock()
            new_info.vectors_count = 2

            client.get_collection.side_effect = [info, new_info]

            # Scroll returns 2 points then empty
            pt1 = MagicMock()
            pt1.id = 1
            pt1.payload = {"text": "Alice"}
            pt1.vector = [0.1] * 1536
            pt2 = MagicMock()
            pt2.id = 2
            pt2.payload = {"text": "Bob"}
            pt2.vector = [0.2] * 1536
            client.scroll.side_effect = [
                ([pt1, pt2], None),
            ]

            # Sparse model
            sparse_emb = MagicMock()
            sparse_emb.indices.tolist.return_value = [1, 2]
            sparse_emb.values.tolist.return_value = [0.5, 0.3]
            MockSparse.return_value.embed.return_value = [sparse_emb]

            result = upgrade_collection("bd_contacts")
        assert result["status"] == "completed"
        assert result["migrated"] == 2

    def test_upgrade_qdrant_not_available(self):
        with patch("Engine8_Knowledge.search.collection_upgrade.QDRANT_AVAILABLE", False):
            result = upgrade_collection("test")
        assert result["status"] == "error"

    def test_upgrade_collection_not_found(self):
        with patch("Engine8_Knowledge.search.collection_upgrade.QdrantClient") as MockClient:
            client = MockClient.return_value
            client.get_collection.side_effect = Exception("not found")
            result = upgrade_collection("nonexistent")
        assert result["status"] == "error"


# ---------------------------------------------------------------------------
# TestUpgradeAll
# ---------------------------------------------------------------------------

class TestUpgradeAll:
    """Test bulk upgrade."""

    def test_upgrade_all_dry_run(self):
        with patch("Engine8_Knowledge.search.collection_upgrade.upgrade_collection") as mock_up:
            mock_up.return_value = {"status": "dry_run", "vectors_count": 100}
            results = upgrade_all(dry_run=True)
        assert len(results) == len(KNOWN_COLLECTIONS)
        assert mock_up.call_count == len(KNOWN_COLLECTIONS)

    def test_known_collections(self):
        assert "bd_contacts" in KNOWN_COLLECTIONS
        assert "bd_documents" in KNOWN_COLLECTIONS
        assert len(KNOWN_COLLECTIONS) == 5


# ---------------------------------------------------------------------------
# TestVerify
# ---------------------------------------------------------------------------

class TestVerify:
    """Test upgrade verification."""

    def test_verify_upgraded(self):
        with patch("Engine8_Knowledge.search.collection_upgrade.QdrantClient") as MockClient:
            client = MockClient.return_value
            info = MagicMock()
            info.config.params.sparse_vectors = {"bm25": MagicMock()}
            info.vectors_count = 5000
            client.get_collection.return_value = info
            result = verify_upgrade("bd_contacts")
        assert result["status"] == "upgraded"
        assert result["has_bm25"] is True

    def test_verify_not_upgraded(self):
        with patch("Engine8_Knowledge.search.collection_upgrade.QdrantClient") as MockClient:
            client = MockClient.return_value
            info = MagicMock()
            info.config.params.sparse_vectors = None
            info.vectors_count = 5000
            client.get_collection.return_value = info
            result = verify_upgrade("bd_contacts")
        assert result["status"] == "not_upgraded"
        assert result["has_bm25"] is False


# ---------------------------------------------------------------------------
# TestRollback
# ---------------------------------------------------------------------------

class TestRollback:
    """Test rollback of failed upgrade."""

    def test_rollback_deletes_temp(self):
        with patch("Engine8_Knowledge.search.collection_upgrade.QdrantClient") as MockClient, \
             patch("Engine8_Knowledge.search.collection_upgrade._clear_progress"):
            client = MockClient.return_value
            result = rollback_upgrade("bd_contacts")
        assert result["status"] == "rolled_back"
        client.delete_collection.assert_called_once_with("bd_contacts_hybrid_temp")

    def test_rollback_error(self):
        with patch("Engine8_Knowledge.search.collection_upgrade.QdrantClient") as MockClient:
            client = MockClient.return_value
            client.delete_collection.side_effect = Exception("not found")
            result = rollback_upgrade("bd_contacts")
        assert result["status"] == "error"


# ---------------------------------------------------------------------------
# TestHelpers
# ---------------------------------------------------------------------------

class TestHelpers:
    """Test helper functions."""

    def test_extract_text_from_text(self):
        assert "hello" in _extract_text({"text": "hello world"})

    def test_extract_text_from_name(self):
        assert "Alice" in _extract_text({"name": "Alice"})

    def test_extract_text_empty(self):
        assert _extract_text({}) == "empty"

    def test_extract_text_multiple_fields(self):
        text = _extract_text({"name": "Alice", "title": "PM", "description": "Program manager"})
        assert "Alice" in text
        assert "PM" in text
