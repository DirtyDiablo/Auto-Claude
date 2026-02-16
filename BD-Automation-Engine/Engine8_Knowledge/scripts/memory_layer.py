"""
Mem0 Memory Layer for BD Intelligence Hub
Repository: https://github.com/mem0ai/mem0 (45,100+ stars)
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from mem0 import Memory

    MEM0_AVAILABLE = True
except ImportError:
    MEM0_AVAILABLE = False
    logger.warning("Mem0 not available, using fallback")


@dataclass
class MemoryEntry:
    id: str
    content: str
    memory_type: str
    timestamp: str
    metadata: Dict[str, Any]


class FallbackMemory:
    """Simple JSON-based fallback when Mem0 unavailable."""

    def __init__(self, storage_path: str):
        self.storage_path = storage_path
        self.memories_file = os.path.join(storage_path, "memories.json")
        self.memories: List[MemoryEntry] = []
        self._load()

    def _load(self):
        if os.path.exists(self.memories_file):
            with open(self.memories_file, "r") as f:
                data = json.load(f)
                self.memories = [MemoryEntry(**e) for e in data]

    def _save(self):
        os.makedirs(os.path.dirname(self.memories_file), exist_ok=True)
        with open(self.memories_file, "w") as f:
            json.dump([asdict(m) for m in self.memories], f, indent=2)

    def add(self, content: str, memory_type: str, metadata: Dict) -> str:
        import uuid

        memory_id = str(uuid.uuid4())
        self.memories.append(
            MemoryEntry(
                id=memory_id,
                content=content,
                memory_type=memory_type,
                timestamp=datetime.now().isoformat(),
                metadata=metadata,
            )
        )
        self._save()
        return memory_id

    def search(self, query: str, limit: int = 10) -> List[Dict]:
        query_lower = query.lower()
        results = [
            {"id": m.id, "memory": m.content, "score": 1.0, "metadata": m.metadata}
            for m in self.memories
            if query_lower in m.content.lower()
        ]
        return results[:limit]

    def get_all(self) -> List[Dict]:
        return [asdict(m) for m in self.memories]

    def delete_all(self):
        self.memories = []
        self._save()


class BDMemoryLayer:
    """Cross-session memory for BD Intelligence Hub."""

    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "data", "memory"
        )
        os.makedirs(self.storage_path, exist_ok=True)
        self.user_id = "pts_bd_unified"

        if MEM0_AVAILABLE:
            self._init_mem0()
        else:
            self._init_fallback()

    def _init_mem0(self):
        config = {
            "llm": {
                "provider": "openai",
                "config": {
                    "model": "gpt-4o-mini",
                    "api_key": os.getenv("OPENAI_API_KEY"),
                },
            },
            "embedder": {
                "provider": "openai",
                "config": {
                    "model": "text-embedding-3-small",
                    "api_key": os.getenv("OPENAI_API_KEY"),
                },
            },
            "vector_store": {
                "provider": "qdrant",
                "config": {
                    "collection_name": "bd_memories",
                    "host": "localhost",
                    "port": 6333,
                    "embedding_model_dims": 1536,
                },
            },
            "graph_store": {
                "provider": "neo4j",
                "config": {
                    "url": os.getenv("NEO4J_URI", "bolt://localhost:7687"),
                    "username": "neo4j",
                    "password": os.getenv("NEO4J_PASSWORD", "pts_bd_2026"),
                },
                "custom_prompt": (
                    "Extract people, organizations, programs, contracts, "
                    "agencies, and their relationships from business "
                    "development intelligence."
                ),
            },
            "version": "v1.1",
        }
        try:
            self.memory = Memory.from_config(config)
            self.backend = "mem0"
        except BaseException as e:
            logger.error(f"Mem0 init failed: {e}")
            self._init_fallback()

    def _init_fallback(self):
        self.memory = FallbackMemory(self.storage_path)
        self.backend = "fallback"

    def add_interaction(
        self, interaction: str, metadata: Optional[Dict] = None
    ) -> Dict:
        """Add query/response pair."""
        meta = metadata or {}
        meta["memory_type"] = "interaction"
        meta["timestamp"] = datetime.now().isoformat()

        if self.backend == "mem0":
            return self.memory.add(
                [{"role": "user", "content": interaction}],
                user_id=self.user_id,
                metadata=meta,
            )
        return {"id": self.memory.add(interaction, "interaction", meta)}

    def add_entity_fact(self, entity_name: str, entity_type: str, fact: str) -> Dict:
        """Add fact about company/program/contact."""
        structured = f"[{entity_type.upper()}] {entity_name}: {fact}"
        meta = {
            "memory_type": "entity_fact",
            "entity_name": entity_name,
            "entity_type": entity_type,
            "timestamp": datetime.now().isoformat(),
        }
        if self.backend == "mem0":
            return self.memory.add(
                [{"role": "user", "content": structured}],
                user_id=self.user_id,
                metadata=meta,
            )
        return {"id": self.memory.add(structured, "entity_fact", meta)}

    def add_bd_insight(
        self,
        insight_type: str,
        insight: str,
        source: str = "analysis",
        confidence: float = 0.8,
    ) -> Dict:
        """Add opportunity/risk/relationship insight."""
        structured = f"[BD INSIGHT - {insight_type.upper()}] {insight}"
        meta = {
            "memory_type": "bd_insight",
            "insight_type": insight_type,
            "source": source,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat(),
        }
        if self.backend == "mem0":
            return self.memory.add(
                [{"role": "user", "content": structured}],
                user_id=self.user_id,
                metadata=meta,
            )
        return {"id": self.memory.add(structured, "bd_insight", meta)}

    def add_scrape_result(self, scrape_type: str, summary: str, count: int) -> Dict:
        """Add scrape operation summary."""
        structured = f"[SCRAPE] {scrape_type}: {summary} ({count} records)"
        meta = {
            "memory_type": "scrape_result",
            "scrape_type": scrape_type,
            "record_count": count,
            "timestamp": datetime.now().isoformat(),
        }
        if self.backend == "mem0":
            return self.memory.add(
                [{"role": "user", "content": structured}],
                user_id=self.user_id,
                metadata=meta,
            )
        return {"id": self.memory.add(structured, "scrape_result", meta)}

    def get_context(self, query: str, limit: int = 10) -> List[Dict]:
        """Retrieve relevant memories."""
        if self.backend == "mem0":
            results = self.memory.search(query=query, user_id=self.user_id, limit=limit)
            return results.get("results", [])
        return self.memory.search(query, limit)

    def get_entity_facts(self, entity_name: str, limit: int = 20) -> List[Dict]:
        return self.get_context(f"Facts about {entity_name}", limit)

    def get_recent_insights(
        self, insight_type: str = None, limit: int = 10
    ) -> List[Dict]:
        query = f"BD insights {insight_type or 'all'}"
        return self.get_context(query, limit)

    def get_stats(self) -> Dict:
        if self.backend == "mem0":
            try:
                all_mem = self.memory.get_all(user_id=self.user_id)
                memories = all_mem.get("results", [])
            except Exception as e:
                logger.error("memory_fetch_failed: %s", e)
                memories = []
        else:
            memories = self.memory.get_all()

        type_counts = {}
        for m in memories:
            t = m.get("metadata", {}).get("memory_type", "unknown")
            type_counts[t] = type_counts.get(t, 0) + 1

        return {
            "total_memories": len(memories),
            "by_type": type_counts,
            "backend": self.backend,
        }


# Singleton
_memory_instance = None


def get_memory(storage_path: str = None) -> BDMemoryLayer:
    global _memory_instance
    if _memory_instance is None:
        _memory_instance = BDMemoryLayer(storage_path)
    return _memory_instance
