"""
Enhanced Memory System with Multiple Backends:
- Mem0: Long-term conversational memory
- Redis-VL: Semantic caching (optional)
- SQLite: Structured memory persistence
"""

import os
import json
import sqlite3
from typing import Optional, List, Dict
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MemoryDatabase:
    """SQLite-backed structured memory storage."""

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "data", "memories.db"
            )

        self.db_path = db_path
        Path(os.path.dirname(db_path)).mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    user_id TEXT DEFAULT 'default',
                    memory_type TEXT,
                    content TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contact_name TEXT,
                    interaction_type TEXT,
                    notes TEXT,
                    outcome TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS insights (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_type TEXT,
                    entity_name TEXT,
                    insight TEXT,
                    source TEXT,
                    confidence REAL DEFAULT 0.8,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_user ON memories(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(memory_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_interactions_contact ON interactions(contact_name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_insights_entity ON insights(entity_type, entity_name)")

    def add_memory(
        self,
        content: str,
        memory_type: str = "general",
        user_id: str = "default",
        metadata: Dict = None
    ) -> str:
        """Add a memory to the database."""
        import uuid
        memory_id = str(uuid.uuid4())

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO memories (id, user_id, memory_type, content, metadata)
                   VALUES (?, ?, ?, ?, ?)""",
                (memory_id, user_id, memory_type, content, json.dumps(metadata or {}))
            )

        return memory_id

    def search_memories(
        self,
        query: str = None,
        memory_type: str = None,
        user_id: str = "default",
        limit: int = 10
    ) -> List[Dict]:
        """Search memories with optional filters."""
        sql = "SELECT * FROM memories WHERE user_id = ?"
        params = [user_id]

        if memory_type:
            sql += " AND memory_type = ?"
            params.append(memory_type)

        if query:
            sql += " AND content LIKE ?"
            params.append(f"%{query}%")

        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]

    def add_interaction(
        self,
        contact_name: str,
        interaction_type: str,
        notes: str,
        outcome: str = None
    ) -> int:
        """Record a contact interaction."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """INSERT INTO interactions (contact_name, interaction_type, notes, outcome)
                   VALUES (?, ?, ?, ?)""",
                (contact_name, interaction_type, notes, outcome)
            )
            return cursor.lastrowid

    def get_contact_history(self, contact_name: str) -> List[Dict]:
        """Get interaction history for a contact."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM interactions WHERE contact_name = ? ORDER BY timestamp DESC",
                (contact_name,)
            )
            return [dict(row) for row in cursor.fetchall()]

    def add_insight(
        self,
        entity_type: str,
        entity_name: str,
        insight: str,
        source: str = None,
        confidence: float = 0.8
    ) -> int:
        """Add an insight about an entity."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """INSERT INTO insights (entity_type, entity_name, insight, source, confidence)
                   VALUES (?, ?, ?, ?, ?)""",
                (entity_type, entity_name, insight, source, confidence)
            )
            return cursor.lastrowid

    def get_entity_insights(self, entity_type: str, entity_name: str) -> List[Dict]:
        """Get insights for an entity."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """SELECT * FROM insights
                   WHERE entity_type = ? AND entity_name = ?
                   ORDER BY confidence DESC, timestamp DESC""",
                (entity_type, entity_name)
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_stats(self) -> Dict:
        """Get database statistics."""
        with sqlite3.connect(self.db_path) as conn:
            memories = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
            interactions = conn.execute("SELECT COUNT(*) FROM interactions").fetchone()[0]
            insights = conn.execute("SELECT COUNT(*) FROM insights").fetchone()[0]

            return {
                "memories": memories,
                "interactions": interactions,
                "insights": insights
            }


class EnhancedMemorySystem:
    """Combined memory system with multiple backends."""

    def __init__(self, data_path: str = None):
        if data_path is None:
            data_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "data"
            )

        self.data_path = data_path
        self.db = MemoryDatabase(os.path.join(data_path, "memories.db"))
        self.mem0 = None
        self.redis_cache = None
        self._init_backends()

    def _init_backends(self):
        """Initialize optional backends."""
        # Mem0 for semantic memory
        try:
            from mem0 import Memory
            config = {
                "vector_store": {
                    "provider": "qdrant",
                    "config": {"path": os.path.join(self.data_path, "qdrant")}
                },
                "llm": {
                    "provider": "anthropic",
                    "config": {
                        "model": "claude-sonnet-4-20250514",
                        "api_key": os.getenv("ANTHROPIC_API_KEY")
                    }
                }
            }
            self.mem0 = Memory.from_config(config)
            logger.info("Mem0 initialized with Qdrant backend")
        except Exception as e:
            logger.warning(f"Mem0 not available: {e}")

        # Redis-VL for caching (optional)
        try:
            from redisvl.extensions.llmcache import SemanticCache
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            self.redis_cache = SemanticCache(name="bd_cache", redis_url=redis_url)
            logger.info("Redis-VL cache initialized")
        except Exception as e:
            logger.warning(f"Redis-VL not available: {e}")

    # ========================================================================
    # Unified Memory Interface
    # ========================================================================

    def remember(
        self,
        content: str,
        memory_type: str = "general",
        metadata: Dict = None
    ) -> str:
        """Add memory to all backends."""
        # Always add to SQLite (reliable)
        memory_id = self.db.add_memory(content, memory_type, metadata=metadata)

        # Also add to Mem0 for semantic search
        if self.mem0:
            try:
                self.mem0.add(content, metadata={"type": memory_type, **(metadata or {})})
            except Exception as e:
                logger.warning(f"Mem0 add failed: {e}")

        return memory_id

    def recall(
        self,
        query: str,
        memory_type: str = None,
        limit: int = 10
    ) -> List[Dict]:
        """Recall memories matching query."""
        # Try Mem0 first (semantic)
        if self.mem0:
            try:
                results = self.mem0.search(query, limit=limit)
                if results.get("results"):
                    return results["results"]
            except Exception as e:
                logger.warning(f"Mem0 search failed: {e}")

        # Fall back to SQLite
        return self.db.search_memories(query, memory_type, limit=limit)

    def cache_response(self, prompt: str, response: str, ttl: int = 3600):
        """Cache a prompt-response pair."""
        if self.redis_cache:
            try:
                self.redis_cache.store(prompt=prompt, response=response, ttl=ttl)
                return True
            except Exception as e:
                logger.warning(f"Cache store failed: {e}")
        return False

    def get_cached(self, prompt: str) -> Optional[str]:
        """Get cached response."""
        if self.redis_cache:
            try:
                result = self.redis_cache.check(prompt=prompt)
                if result:
                    return result[0].get("response")
            except Exception as e:
                logger.warning(f"Cache check failed: {e}")
        return None

    # ========================================================================
    # BD-Specific Memory Operations
    # ========================================================================

    def log_contact_interaction(
        self,
        contact: str,
        type: str,
        notes: str,
        outcome: str = None
    ):
        """Log interaction with BD contact."""
        self.db.add_interaction(contact, type, notes, outcome)
        self.remember(
            f"Interaction with {contact}: {type} - {notes}",
            memory_type="interaction",
            metadata={"contact": contact, "type": type, "outcome": outcome}
        )

    def log_program_insight(
        self,
        program: str,
        insight: str,
        source: str = None
    ):
        """Log insight about a program."""
        self.db.add_insight("program", program, insight, source)
        self.remember(
            f"Program insight for {program}: {insight}",
            memory_type="insight",
            metadata={"program": program, "source": source}
        )

    def get_program_context(self, program: str) -> Dict:
        """Get all context about a program."""
        return {
            "insights": self.db.get_entity_insights("program", program),
            "memories": self.recall(program, memory_type="insight", limit=5)
        }

    def get_contact_context(self, contact: str) -> Dict:
        """Get all context about a contact."""
        return {
            "interactions": self.db.get_contact_history(contact),
            "memories": self.recall(contact, memory_type="interaction", limit=5)
        }

    def get_stats(self) -> Dict:
        """Get comprehensive memory statistics."""
        stats = self.db.get_stats()
        stats["backends"] = {
            "sqlite": True,
            "mem0": self.mem0 is not None,
            "redis": self.redis_cache is not None
        }
        return stats


# Singleton
_memory_system: Optional[EnhancedMemorySystem] = None


def get_memory_system(data_path: str = None) -> EnhancedMemorySystem:
    """Get memory system singleton."""
    global _memory_system
    if _memory_system is None:
        _memory_system = EnhancedMemorySystem(data_path)
    return _memory_system
