"""
Phase 25A — Mem0 Core Manager

Core Mem0 integration with Qdrant backend for persistent agent memory.
Provides add, search, update, delete, history, and stats operations
scoped by user_id and agent_id.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------


@dataclass
class Memory:
    """A single memory entry."""

    memory_id: str = ""
    content: str = ""
    user_id: str = ""
    agent_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    score: float = 0.0


@dataclass
class MemoryVersion:
    """Version history entry for a memory."""

    version: int = 0
    content: str = ""
    updated_at: str = ""
    change_type: str = ""  # created, updated, deleted


@dataclass
class MemoryStats:
    """Aggregate memory statistics."""

    total_memories: int = 0
    by_user: Dict[str, int] = field(default_factory=dict)
    by_agent: Dict[str, int] = field(default_factory=dict)
    by_type: Dict[str, int] = field(default_factory=dict)
    storage_size_bytes: int = 0


# ---------------------------------------------------------------------------
# Mem0 Manager
# ---------------------------------------------------------------------------


class Mem0Manager:
    """Core Mem0 integration with Qdrant backend."""

    def __init__(
        self,
        qdrant_url: str = "localhost:6333",
        collection: str = "agent_memory",
        embedding_model: str = "text-embedding-3-small",
        llm_model: str = "gpt-4o-mini",
    ):
        self.qdrant_url = qdrant_url
        self.collection = collection
        self.embedding_model = embedding_model
        self.llm_model = llm_model
        self._client = None
        self._memories: Dict[str, Memory] = {}  # Fallback in-memory store
        self._history: Dict[str, List[MemoryVersion]] = {}
        self._initialized = False

        logger.info(
            "mem0_manager_init",
            qdrant_url=qdrant_url,
            collection=collection,
        )

    async def _ensure_client(self):
        """Lazy-initialize Mem0 client."""
        if self._initialized:
            return
        try:
            from mem0 import Memory as Mem0Memory

            config = {
                "vector_store": {
                    "provider": "qdrant",
                    "config": {
                        "url": self.qdrant_url,
                        "collection_name": self.collection,
                    },
                },
                "embedder": {
                    "provider": "openai",
                    "config": {"model": self.embedding_model},
                },
                "llm": {
                    "provider": "openai",
                    "config": {"model": self.llm_model},
                },
            }
            self._client = Mem0Memory.from_config(config)
            self._initialized = True
            logger.info("mem0_client_initialized")
        except ImportError:
            logger.warning("mem0_not_installed", hint="pip install mem0ai")
            self._initialized = True  # Use fallback
        except Exception as exc:
            logger.warning("mem0_init_error", error=str(exc))
            self._initialized = True

    # ------------------------------------------------------------------
    # Core Operations
    # ------------------------------------------------------------------

    async def add(
        self,
        content: str,
        user_id: str,
        agent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Add a memory scoped to user/agent."""
        await self._ensure_client()
        memory_id = f"mem_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow().isoformat()
        meta = metadata or {}
        meta["created_at"] = now

        if self._client:
            try:
                result = self._client.add(
                    content,
                    user_id=user_id,
                    agent_id=agent_id,
                    metadata=meta,
                )
                if result and isinstance(result, dict) and "id" in result:
                    memory_id = result["id"]
                elif result and isinstance(result, list) and len(result) > 0:
                    memory_id = result[0].get("id", memory_id)
            except Exception as exc:
                logger.warning("mem0_add_error", error=str(exc))

        # Always store in fallback
        self._memories[memory_id] = Memory(
            memory_id=memory_id,
            content=content,
            user_id=user_id,
            agent_id=agent_id,
            metadata=meta,
            created_at=now,
            updated_at=now,
        )
        self._history.setdefault(memory_id, []).append(
            MemoryVersion(
                version=1, content=content, updated_at=now, change_type="created"
            )
        )

        logger.info("memory_added", id=memory_id, user=user_id, agent=agent_id)
        return memory_id

    async def search(
        self,
        query: str,
        user_id: str,
        agent_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[Memory]:
        """Semantic search across memories for a user/agent scope."""
        await self._ensure_client()

        if self._client:
            try:
                results = self._client.search(
                    query,
                    user_id=user_id,
                    agent_id=agent_id,
                    limit=limit,
                )
                return [
                    Memory(
                        memory_id=r.get("id", ""),
                        content=r.get("memory", r.get("content", "")),
                        user_id=user_id,
                        agent_id=agent_id,
                        score=r.get("score", 0.0),
                        metadata=r.get("metadata", {}),
                    )
                    for r in (results if isinstance(results, list) else [])
                ]
            except Exception as exc:
                logger.warning("mem0_search_error", error=str(exc))

        # Fallback: simple keyword search
        query_lower = query.lower()
        matches = []
        for mem in self._memories.values():
            if mem.user_id != user_id:
                continue
            if agent_id and mem.agent_id != agent_id:
                continue
            if query_lower in mem.content.lower():
                mem.score = 0.8
                matches.append(mem)

        return sorted(matches, key=lambda m: m.score, reverse=True)[:limit]

    async def get_all(
        self, user_id: str, agent_id: Optional[str] = None
    ) -> List[Memory]:
        """All memories for a user/agent."""
        await self._ensure_client()

        if self._client:
            try:
                results = self._client.get_all(user_id=user_id, agent_id=agent_id)
                return [
                    Memory(
                        memory_id=r.get("id", ""),
                        content=r.get("memory", r.get("content", "")),
                        user_id=user_id,
                        agent_id=agent_id,
                        metadata=r.get("metadata", {}),
                    )
                    for r in (results if isinstance(results, list) else [])
                ]
            except Exception as exc:
                logger.warning("mem0_get_all_error", error=str(exc))

        return [
            m
            for m in self._memories.values()
            if m.user_id == user_id and (not agent_id or m.agent_id == agent_id)
        ]

    async def update(self, memory_id: str, content: str) -> bool:
        """Update a memory's content."""
        await self._ensure_client()
        now = datetime.utcnow().isoformat()

        if self._client:
            try:
                self._client.update(memory_id, content)
            except Exception as exc:
                logger.warning("mem0_update_error", error=str(exc))

        if memory_id in self._memories:
            self._memories[memory_id].content = content
            self._memories[memory_id].updated_at = now
            self._history.setdefault(memory_id, []).append(
                MemoryVersion(
                    version=len(self._history.get(memory_id, [])) + 1,
                    content=content,
                    updated_at=now,
                    change_type="updated",
                )
            )
            return True
        return False

    async def delete(self, memory_id: str) -> bool:
        """Delete a specific memory."""
        await self._ensure_client()

        if self._client:
            try:
                self._client.delete(memory_id)
            except Exception as exc:
                logger.warning("mem0_delete_error", error=str(exc))

        if memory_id in self._memories:
            now = datetime.utcnow().isoformat()
            self._history.setdefault(memory_id, []).append(
                MemoryVersion(
                    version=len(self._history.get(memory_id, [])) + 1,
                    content="[DELETED]",
                    updated_at=now,
                    change_type="deleted",
                )
            )
            del self._memories[memory_id]
            return True
        return False

    async def get_history(self, memory_id: str) -> List[MemoryVersion]:
        """Version history of a memory."""
        return self._history.get(memory_id, [])

    async def get_stats(self) -> MemoryStats:
        """Total memories, by user, by agent, by type."""
        by_user: Dict[str, int] = {}
        by_agent: Dict[str, int] = {}
        by_type: Dict[str, int] = {}

        for mem in self._memories.values():
            by_user[mem.user_id] = by_user.get(mem.user_id, 0) + 1
            if mem.agent_id:
                by_agent[mem.agent_id] = by_agent.get(mem.agent_id, 0) + 1
            mem_type = mem.metadata.get("type", "unknown")
            by_type[mem_type] = by_type.get(mem_type, 0) + 1

        return MemoryStats(
            total_memories=len(self._memories),
            by_user=by_user,
            by_agent=by_agent,
            by_type=by_type,
            storage_size_bytes=sum(len(m.content) for m in self._memories.values()),
        )


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_manager: Optional[Mem0Manager] = None


def get_mem0_manager(**kwargs) -> Mem0Manager:
    global _manager
    if _manager is None:
        _manager = Mem0Manager(**kwargs)
    return _manager
