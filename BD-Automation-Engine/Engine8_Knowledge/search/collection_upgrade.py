"""
Phase 22A — BM25 Collection Upgrade

Upgrades existing Qdrant collections to support BM25 sparse vectors.
Uses Qdrant-native sparse vector config with Modifier.IDF.

Strategy:
  1. Check if collection already has sparse vector config → skip
  2. Create new collection with hybrid config (dense + bm25)
  3. Scroll old collection in batches of 500, generate BM25 sparse vectors
  4. Upsert to new collection with both dense + sparse
  5. Rename: old → backup, new → original name
  6. Resume support via progress file
"""

import json
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Any

logger = logging.getLogger(__name__)

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        VectorParams, SparseVectorParams, Distance, Modifier,
        PointStruct, SparseVector,
    )
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

try:
    from fastembed import SparseTextEmbedding
    FASTEMBED_AVAILABLE = True
except ImportError:
    FASTEMBED_AVAILABLE = False

QDRANT_URL = "http://localhost:6333"
PROGRESS_FILE = Path(__file__).parent.parent / "data" / "search" / "upgrade_progress.json"
BATCH_SIZE = 500
KNOWN_COLLECTIONS = ["bd_contacts", "bd_documents", "bd_activities", "bd_programs", "bd_jobs"]


# ---------------------------------------------------------------------------
# Upgrade functions
# ---------------------------------------------------------------------------

def upgrade_collection(
    collection_name: str,
    qdrant_url: str = QDRANT_URL,
    dry_run: bool = False,
) -> dict:
    """
    Upgrade a single collection to support BM25 sparse vectors.

    Steps:
    1. Check if collection has sparse config → skip if yes
    2. Create temp collection with hybrid config
    3. Scroll + generate BM25 + upsert batches
    4. Rename old → backup, temp → original
    """
    if not QDRANT_AVAILABLE:
        return {"status": "error", "error": "qdrant_client not installed"}

    client = QdrantClient(url=qdrant_url, timeout=60)
    result = {"collection": collection_name, "status": "pending"}

    # Check if already upgraded
    try:
        info = client.get_collection(collection_name)
        sparse_config = getattr(info.config.params, "sparse_vectors", None)
        if sparse_config and "bm25" in (sparse_config or {}):
            result["status"] = "already_upgraded"
            result["vectors_count"] = info.vectors_count
            logger.info("collection_already_upgraded", collection=collection_name)
            return result
    except Exception as e:
        result["status"] = "error"
        result["error"] = f"Failed to get collection info: {str(e)[:100]}"
        return result

    # Get existing config
    vectors_count = info.vectors_count or 0
    dense_config = info.config.params.vectors
    if isinstance(dense_config, dict):
        # Named vectors
        vec_size = list(dense_config.values())[0].size
    else:
        vec_size = getattr(dense_config, "size", 1536)

    if dry_run:
        result["status"] = "dry_run"
        result["vectors_count"] = vectors_count
        result["estimated_batches"] = (vectors_count + BATCH_SIZE - 1) // BATCH_SIZE
        result["note"] = "Would create new collection with BM25 sparse config, migrate vectors, and rename"
        return result

    temp_name = f"{collection_name}_hybrid_temp"
    started = time.time()

    # Load BM25 model
    if not FASTEMBED_AVAILABLE:
        return {"status": "error", "error": "fastembed not installed — pip install fastembed"}
    sparse_model = SparseTextEmbedding("Qdrant/bm25")

    try:
        # Create temp collection with hybrid config
        client.create_collection(
            collection_name=temp_name,
            vectors_config={
                "dense": VectorParams(size=vec_size, distance=Distance.COSINE),
            },
            sparse_vectors_config={
                "bm25": SparseVectorParams(modifier=Modifier.IDF),
            },
        )
        logger.info("temp_collection_created", name=temp_name, size=vec_size)

        # Load progress
        progress = _load_progress(collection_name)
        offset = progress.get("last_offset")
        migrated = progress.get("migrated", 0)

        # Scroll and migrate
        while True:
            points, next_offset = client.scroll(
                collection_name=collection_name,
                limit=BATCH_SIZE,
                offset=offset,
                with_vectors=True,
                with_payload=True,
            )

            if not points:
                break

            # Generate BM25 sparse vectors
            batch_points = []
            for pt in points:
                payload = pt.payload or {}
                text = _extract_text(payload)

                # Get existing dense vector
                dense_vec = pt.vector
                if isinstance(dense_vec, dict):
                    dense_vec = list(dense_vec.values())[0]

                # Generate sparse
                sparse_embeddings = list(sparse_model.embed([text]))
                if sparse_embeddings:
                    sparse = sparse_embeddings[0]
                    sparse_vec = SparseVector(
                        indices=sparse.indices.tolist(),
                        values=sparse.values.tolist(),
                    )
                else:
                    sparse_vec = SparseVector(indices=[], values=[])

                batch_points.append(PointStruct(
                    id=pt.id,
                    vector={
                        "dense": dense_vec if isinstance(dense_vec, list) else list(dense_vec),
                        "bm25": sparse_vec,
                    },
                    payload=payload,
                ))

            # Upsert batch
            client.upsert(collection_name=temp_name, points=batch_points)
            migrated += len(batch_points)

            # Save progress
            _save_progress(collection_name, {
                "last_offset": next_offset,
                "migrated": migrated,
                "timestamp": datetime.now().isoformat(),
            })

            logger.info("batch_migrated", collection=collection_name, migrated=migrated, total=vectors_count)

            if next_offset is None:
                break
            offset = next_offset

        # Verify counts
        new_info = client.get_collection(temp_name)
        new_count = new_info.vectors_count or 0

        if new_count < vectors_count * 0.95:
            result["status"] = "error"
            result["error"] = f"Count mismatch: old={vectors_count}, new={new_count}"
            return result

        # Rename: old → backup, temp → original
        backup_name = f"{collection_name}_pre_bm25"
        try:
            client.delete_collection(backup_name)
        except Exception:
            pass  # backup might not exist

        # Qdrant doesn't support rename, so we use aliases or recreate
        # For safety, keep both and log
        result["status"] = "completed"
        result["migrated"] = migrated
        result["old_collection"] = collection_name
        result["new_collection"] = temp_name
        result["elapsed_sec"] = round(time.time() - started, 1)
        result["note"] = f"Upgraded collection at {temp_name}. Set alias or update config to use it."

        # Clear progress
        _clear_progress(collection_name)

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)[:200]
        logger.error("upgrade_failed", collection=collection_name, error=str(e)[:200])

    return result


def upgrade_all(qdrant_url: str = QDRANT_URL, dry_run: bool = False) -> dict:
    """Upgrade all known collections."""
    results = {}
    for coll in KNOWN_COLLECTIONS:
        results[coll] = upgrade_collection(coll, qdrant_url, dry_run)
    return results


def verify_upgrade(collection_name: str, qdrant_url: str = QDRANT_URL) -> dict:
    """Verify a collection has working BM25 sparse vectors."""
    if not QDRANT_AVAILABLE:
        return {"status": "error", "error": "qdrant_client not installed"}

    client = QdrantClient(url=qdrant_url, timeout=30)
    try:
        info = client.get_collection(collection_name)
        sparse_config = getattr(info.config.params, "sparse_vectors", None)
        has_bm25 = sparse_config is not None and "bm25" in (sparse_config or {})

        return {
            "collection": collection_name,
            "has_bm25": has_bm25,
            "vectors_count": info.vectors_count or 0,
            "status": "upgraded" if has_bm25 else "not_upgraded",
        }
    except Exception as e:
        return {"collection": collection_name, "status": "error", "error": str(e)[:100]}


def rollback_upgrade(collection_name: str, qdrant_url: str = QDRANT_URL) -> dict:
    """Remove temp hybrid collection if upgrade failed."""
    if not QDRANT_AVAILABLE:
        return {"status": "error", "error": "qdrant_client not installed"}

    client = QdrantClient(url=qdrant_url, timeout=30)
    temp_name = f"{collection_name}_hybrid_temp"
    try:
        client.delete_collection(temp_name)
        _clear_progress(collection_name)
        return {"status": "rolled_back", "deleted": temp_name}
    except Exception as e:
        return {"status": "error", "error": str(e)[:100]}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_text(payload: dict) -> str:
    """Extract searchable text from a point payload."""
    parts = []
    for key in ("text", "content", "name", "title", "description", "note_body", "summary"):
        val = payload.get(key)
        if val and isinstance(val, str):
            parts.append(val)
    return " ".join(parts)[:2000] if parts else "empty"


def _load_progress(collection_name: str) -> dict:
    """Load migration progress from file."""
    try:
        if PROGRESS_FILE.exists():
            data = json.loads(PROGRESS_FILE.read_text())
            return data.get(collection_name, {})
    except Exception:
        pass
    return {}


def _save_progress(collection_name: str, progress: dict) -> None:
    """Save migration progress to file."""
    try:
        PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = {}
        if PROGRESS_FILE.exists():
            data = json.loads(PROGRESS_FILE.read_text())
        data[collection_name] = progress
        PROGRESS_FILE.write_text(json.dumps(data, indent=2))
    except Exception as e:
        logger.warning("progress_save_error", error=str(e)[:100])


def _clear_progress(collection_name: str) -> None:
    """Clear progress for a collection."""
    try:
        if PROGRESS_FILE.exists():
            data = json.loads(PROGRESS_FILE.read_text())
            data.pop(collection_name, None)
            PROGRESS_FILE.write_text(json.dumps(data, indent=2))
    except Exception:
        pass
