"""
Feature 16 — Stable Mem0 Conversational Memory

Per-user conversational memory with error isolation.
Tries mem0ai first, falls back to a fully functional dict-based
memory with JSON persistence, deduplication, and TTL cleanup.
"""

import hashlib
import json
import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_TTL_DAYS = 90
DEFAULT_STORAGE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "memory"
)
_MEMORIES_FILENAME = "stable_memories.json"


def _content_hash(content: str) -> str:
    """Deterministic hash for deduplication."""
    return hashlib.sha256(content.strip().lower().encode("utf-8")).hexdigest()[:16]


# ---------------------------------------------------------------------------
# StableMemoryManager
# ---------------------------------------------------------------------------


class StableMemoryManager:
    """Per-user conversational memory with error isolation.

    Design principles:
    - Per-user scoping (user_id required on every call)
    - Graceful fallback to dict-based memory when mem0 is unavailable
    - Error isolation: mem0 errors never crash the API
    - Content deduplication per user
    - TTL-based cleanup (default 90 days)
    - JSON file persistence for the fallback store
    """

    def __init__(
        self,
        backend: str = "qdrant",
        storage_dir: str = DEFAULT_STORAGE_DIR,
        ttl_days: int = DEFAULT_TTL_DAYS,
    ):
        self._backend = backend
        self._storage_dir = storage_dir
        self._ttl_days = ttl_days

        # Fallback store: {user_id: [{"id", "content", "content_hash", "metadata", "created_at"}]}
        self._memories: Dict[str, List[Dict[str, Any]]] = {}

        # Track content hashes per user for dedup: {user_id: set(hash)}
        self._hashes: Dict[str, set] = {}

        self._mem0 = None
        self._mem0_available = False

        # Ensure storage directory
        Path(self._storage_dir).mkdir(parents=True, exist_ok=True)

        # Load persisted fallback memories
        self._load_from_disk()

        # Try to initialise mem0
        self._init_mem0()

    # ------------------------------------------------------------------
    # Initialisation helpers
    # ------------------------------------------------------------------

    def _init_mem0(self):
        """Initialize mem0 with full error handling."""
        try:
            from mem0 import Memory

            config: Dict[str, Any] = {
                "vector_store": {
                    "provider": "qdrant",
                    "config": {
                        "url": os.getenv("QDRANT_URL", "http://localhost:6333"),
                        "collection_name": "stable_memory",
                    },
                },
                "embedder": {
                    "provider": "openai",
                    "config": {
                        "model": os.getenv(
                            "EMBEDDING_MODEL", "text-embedding-3-small"
                        ),
                    },
                },
                "llm": {
                    "provider": "openai",
                    "config": {
                        "model": os.getenv("LLM_MODEL", "gpt-4o-mini"),
                    },
                },
            }
            self._mem0 = Memory.from_config(config)
            self._mem0_available = True
            logger.info("stable_mem0_initialized", backend=self._backend)
        except ImportError:
            logger.warning(
                "mem0_unavailable",
                fallback="dict_memory",
                error="mem0ai not installed",
            )
        except Exception as e:
            logger.warning(
                "mem0_unavailable",
                fallback="dict_memory",
                error=str(e),
            )

    def _persistence_path(self) -> Path:
        return Path(self._storage_dir) / _MEMORIES_FILENAME

    def _load_from_disk(self):
        """Load persisted fallback memories from JSON."""
        path = self._persistence_path()
        if not path.exists():
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                self._memories = data
                # Rebuild hash index
                for user_id, entries in self._memories.items():
                    self._hashes[user_id] = {
                        e.get("content_hash", "")
                        for e in entries
                        if e.get("content_hash")
                    }
            logger.info(
                "stable_mem0_loaded",
                users=len(self._memories),
                total=sum(len(v) for v in self._memories.values()),
            )
        except Exception as e:
            logger.warning("stable_mem0_load_error", error=str(e))

    def _save_to_disk(self):
        """Persist fallback memories to JSON."""
        try:
            path = self._persistence_path()
            path.write_text(
                json.dumps(self._memories, indent=2, default=str),
                encoding="utf-8",
            )
        except Exception as e:
            logger.warning("stable_mem0_save_error", error=str(e))

    # ------------------------------------------------------------------
    # Core operations
    # ------------------------------------------------------------------

    def add(
        self,
        user_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Add a memory entry. Returns memory ID.

        Deduplicates: if identical content already exists for this user,
        returns the existing memory's ID without creating a duplicate.
        """
        if not user_id or not content:
            raise ValueError("user_id and content are required")

        c_hash = _content_hash(content)

        # Dedup check
        if c_hash in self._hashes.get(user_id, set()):
            # Find and return existing id
            for entry in self._memories.get(user_id, []):
                if entry.get("content_hash") == c_hash:
                    logger.debug(
                        "memory_dedup_hit", user_id=user_id, hash=c_hash
                    )
                    return entry["id"]

        memory_id = f"smem_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        meta = metadata.copy() if metadata else {}

        # Try mem0 first
        if self._mem0_available and self._mem0 is not None:
            try:
                result = self._mem0.add(
                    content, user_id=user_id, metadata=meta
                )
                if result and isinstance(result, dict) and "id" in result:
                    memory_id = result["id"]
                elif (
                    result
                    and isinstance(result, list)
                    and len(result) > 0
                ):
                    memory_id = result[0].get("id", memory_id)
            except Exception as e:
                logger.warning("stable_mem0_add_error", error=str(e))

        # Always store in fallback
        entry = {
            "id": memory_id,
            "content": content,
            "content_hash": c_hash,
            "metadata": meta,
            "created_at": now,
        }
        self._memories.setdefault(user_id, []).append(entry)
        self._hashes.setdefault(user_id, set()).add(c_hash)

        self._save_to_disk()

        logger.info("memory_added", id=memory_id, user_id=user_id)
        return memory_id

    def search(
        self, user_id: str, query: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search user memories by semantic similarity (mem0) or keyword fallback."""
        if not user_id or not query:
            return []

        # Try mem0 first
        if self._mem0_available and self._mem0 is not None:
            try:
                results = self._mem0.search(
                    query, user_id=user_id, limit=limit
                )
                if isinstance(results, list):
                    return [
                        {
                            "id": r.get("id", ""),
                            "content": r.get("memory", r.get("content", "")),
                            "score": r.get("score", 0.0),
                            "metadata": r.get("metadata", {}),
                        }
                        for r in results[:limit]
                    ]
                if isinstance(results, dict) and "results" in results:
                    return [
                        {
                            "id": r.get("id", ""),
                            "content": r.get("memory", r.get("content", "")),
                            "score": r.get("score", 0.0),
                            "metadata": r.get("metadata", {}),
                        }
                        for r in results["results"][:limit]
                    ]
            except Exception as e:
                logger.warning("stable_mem0_search_error", error=str(e))

        # Fallback: keyword search
        query_lower = query.lower()
        user_memories = self._memories.get(user_id, [])
        matches = []
        for entry in user_memories:
            content = entry.get("content", "")
            if query_lower in content.lower():
                matches.append(
                    {
                        "id": entry["id"],
                        "content": content,
                        "score": 0.8,
                        "metadata": entry.get("metadata", {}),
                    }
                )
        return matches[:limit]

    def get_all(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all memories for a user."""
        if not user_id:
            return []

        # Try mem0
        if self._mem0_available and self._mem0 is not None:
            try:
                results = self._mem0.get_all(user_id=user_id)
                if isinstance(results, list) and results:
                    return [
                        {
                            "id": r.get("id", ""),
                            "content": r.get("memory", r.get("content", "")),
                            "metadata": r.get("metadata", {}),
                            "created_at": r.get("created_at", ""),
                        }
                        for r in results
                    ]
            except Exception as e:
                logger.warning("stable_mem0_get_all_error", error=str(e))

        # Fallback
        return [
            {
                "id": e["id"],
                "content": e["content"],
                "metadata": e.get("metadata", {}),
                "created_at": e.get("created_at", ""),
            }
            for e in self._memories.get(user_id, [])
        ]

    def delete(self, user_id: str, memory_id: str) -> bool:
        """Delete a specific memory for a user."""
        if not user_id or not memory_id:
            return False

        # Try mem0
        if self._mem0_available and self._mem0 is not None:
            try:
                self._mem0.delete(memory_id)
            except Exception as e:
                logger.warning("stable_mem0_delete_error", error=str(e))

        # Remove from fallback
        user_entries = self._memories.get(user_id, [])
        for i, entry in enumerate(user_entries):
            if entry["id"] == memory_id:
                removed = user_entries.pop(i)
                c_hash = removed.get("content_hash", "")
                if c_hash and user_id in self._hashes:
                    self._hashes[user_id].discard(c_hash)
                self._save_to_disk()
                logger.info(
                    "memory_deleted",
                    id=memory_id,
                    user_id=user_id,
                )
                return True
        return False

    def clear(self, user_id: str) -> int:
        """Clear all memories for a user. Returns count deleted."""
        if not user_id:
            return 0

        count = len(self._memories.get(user_id, []))

        # Try mem0 clear
        if self._mem0_available and self._mem0 is not None:
            try:
                all_mems = self._mem0.get_all(user_id=user_id)
                if isinstance(all_mems, list):
                    for m in all_mems:
                        mid = m.get("id")
                        if mid:
                            self._mem0.delete(mid)
            except Exception as e:
                logger.warning("stable_mem0_clear_error", error=str(e))

        # Clear fallback
        self._memories.pop(user_id, None)
        self._hashes.pop(user_id, None)
        self._save_to_disk()

        logger.info("memories_cleared", user_id=user_id, count=count)
        return count

    def get_context(
        self, user_id: str, query: str, max_tokens: int = 2000
    ) -> str:
        """Get relevant context string for RAG augmentation.

        Searches memories for the user and assembles a context string
        that fits within the approximate token budget.
        """
        if not user_id or not query:
            return ""

        results = self.search(user_id, query, limit=10)
        if not results:
            return ""

        lines: List[str] = ["Relevant memories:"]
        char_budget = max_tokens * 4  # ~4 chars per token approximation
        used = len(lines[0])

        for i, r in enumerate(results, 1):
            content = r.get("content", "")
            line = f"  {i}. {content}"
            if used + len(line) > char_budget:
                break
            lines.append(line)
            used += len(line)

        return "\n".join(lines)

    def get_stats(self) -> Dict[str, Any]:
        """Memory system stats: user count, total entries, backend status."""
        total = sum(len(v) for v in self._memories.values())
        return {
            "backend": "mem0" if self._mem0_available else "dict_fallback",
            "mem0_available": self._mem0_available,
            "user_count": len(self._memories),
            "total_memories": total,
            "per_user": {
                uid: len(entries)
                for uid, entries in self._memories.items()
            },
            "storage_dir": self._storage_dir,
        }

    def cleanup_expired(self, ttl_days: Optional[int] = None) -> int:
        """Remove memories older than TTL. Returns count removed."""
        days = ttl_days if ttl_days is not None else self._ttl_days
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        removed = 0

        for user_id in list(self._memories.keys()):
            entries = self._memories[user_id]
            before = len(entries)
            kept = []
            for entry in entries:
                created = entry.get("created_at", "")
                if created and created < cutoff:
                    # Remove hash
                    c_hash = entry.get("content_hash", "")
                    if c_hash and user_id in self._hashes:
                        self._hashes[user_id].discard(c_hash)
                    removed += 1
                else:
                    kept.append(entry)
            self._memories[user_id] = kept
            if not kept:
                self._memories.pop(user_id, None)
                self._hashes.pop(user_id, None)

        if removed > 0:
            self._save_to_disk()
            logger.info("memory_cleanup", removed=removed, ttl_days=days)

        return removed


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_manager: Optional[StableMemoryManager] = None


def get_stable_memory_manager(**kwargs) -> StableMemoryManager:
    """Get or create the singleton StableMemoryManager."""
    global _manager
    if _manager is None:
        _manager = StableMemoryManager(**kwargs)
    return _manager


def reset_stable_memory_manager():
    """Reset singleton (for testing)."""
    global _manager
    _manager = None
