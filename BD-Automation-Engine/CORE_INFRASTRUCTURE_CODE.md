# CORE INFRASTRUCTURE ENHANCEMENT
## Practical Code Implementation Guide

**Generated:** January 26, 2026  
**Target:** BD-Automation-Engine (Terminal 1 - The Hub)

---

## 1. ENHANCED STORAGE ARCHITECTURE

### 1.1 Unified Qdrant Collections Schema

```python
# Engine8_Knowledge/schemas/vector_collections.py

"""
Enhanced Qdrant Collection Schemas
All collections unified with consistent metadata fields
"""

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue,
    PayloadSchemaType
)
from typing import List, Dict, Optional
import os

# Collection Definitions
COLLECTIONS = {
    "jobs": {
        "size": 1536,  # OpenAI embedding size
        "distance": Distance.COSINE,
        "payload_schema": {
            "job_id": PayloadSchemaType.KEYWORD,
            "title": PayloadSchemaType.TEXT,
            "company": PayloadSchemaType.KEYWORD,
            "location": PayloadSchemaType.KEYWORD,
            "clearance": PayloadSchemaType.KEYWORD,
            "program": PayloadSchemaType.KEYWORD,
            "bd_score": PayloadSchemaType.INTEGER,
            "scraped_at": PayloadSchemaType.DATETIME,
            "source": PayloadSchemaType.KEYWORD,
        }
    },
    "contacts": {
        "size": 1536,
        "distance": Distance.COSINE,
        "payload_schema": {
            "contact_id": PayloadSchemaType.KEYWORD,
            "name": PayloadSchemaType.TEXT,
            "title": PayloadSchemaType.TEXT,
            "company": PayloadSchemaType.KEYWORD,
            "program": PayloadSchemaType.KEYWORD,
            "tier": PayloadSchemaType.KEYWORD,
            "priority": PayloadSchemaType.KEYWORD,
            "location": PayloadSchemaType.KEYWORD,
            "email": PayloadSchemaType.KEYWORD,
        }
    },
    "programs": {
        "size": 1536,
        "distance": Distance.COSINE,
        "payload_schema": {
            "program_id": PayloadSchemaType.KEYWORD,
            "name": PayloadSchemaType.TEXT,
            "acronym": PayloadSchemaType.KEYWORD,
            "agency": PayloadSchemaType.KEYWORD,
            "prime": PayloadSchemaType.KEYWORD,
            "contract_value": PayloadSchemaType.FLOAT,
            "clearance": PayloadSchemaType.KEYWORD,
            "locations": PayloadSchemaType.KEYWORD,
        }
    },
    "documents": {
        "size": 1536,
        "distance": Distance.COSINE,
        "payload_schema": {
            "doc_id": PayloadSchemaType.KEYWORD,
            "title": PayloadSchemaType.TEXT,
            "doc_type": PayloadSchemaType.KEYWORD,
            "source": PayloadSchemaType.KEYWORD,
            "chunk_index": PayloadSchemaType.INTEGER,
            "total_chunks": PayloadSchemaType.INTEGER,
        }
    },
    "memories": {
        "size": 1536,
        "distance": Distance.COSINE,
        "payload_schema": {
            "memory_id": PayloadSchemaType.KEYWORD,
            "user_id": PayloadSchemaType.KEYWORD,
            "memory_type": PayloadSchemaType.KEYWORD,
            "content": PayloadSchemaType.TEXT,
            "created_at": PayloadSchemaType.DATETIME,
        }
    },
    "knowledge_graph": {
        "size": 1536,
        "distance": Distance.COSINE,
        "payload_schema": {
            "entity_id": PayloadSchemaType.KEYWORD,
            "entity_type": PayloadSchemaType.KEYWORD,
            "entity_name": PayloadSchemaType.TEXT,
            "relationships": PayloadSchemaType.TEXT,
        }
    }
}


class EnhancedQdrantStore:
    """Enhanced Qdrant storage with unified schema."""
    
    def __init__(self, path: str = "./data/qdrant"):
        self.client = QdrantClient(path=path)
        self._ensure_collections()
    
    def _ensure_collections(self):
        """Ensure all collections exist with correct schema."""
        existing = [c.name for c in self.client.get_collections().collections]
        
        for name, config in COLLECTIONS.items():
            if name not in existing:
                self.client.create_collection(
                    collection_name=name,
                    vectors_config=VectorParams(
                        size=config["size"],
                        distance=config["distance"]
                    )
                )
                print(f"Created collection: {name}")
    
    def upsert_vectors(
        self,
        collection: str,
        vectors: List[List[float]],
        payloads: List[Dict],
        ids: Optional[List[str]] = None
    ) -> int:
        """Upsert vectors with payloads."""
        if ids is None:
            import uuid
            ids = [str(uuid.uuid4()) for _ in vectors]
        
        points = [
            PointStruct(id=id, vector=vec, payload=payload)
            for id, vec, payload in zip(ids, vectors, payloads)
        ]
        
        self.client.upsert(collection_name=collection, points=points)
        return len(points)
    
    def search(
        self,
        collection: str,
        query_vector: List[float],
        limit: int = 10,
        filters: Dict = None
    ) -> List[Dict]:
        """Search with optional filters."""
        query_filter = None
        if filters:
            conditions = [
                FieldCondition(key=k, match=MatchValue(value=v))
                for k, v in filters.items()
            ]
            query_filter = Filter(must=conditions)
        
        results = self.client.search(
            collection_name=collection,
            query_vector=query_vector,
            limit=limit,
            query_filter=query_filter
        )
        
        return [
            {
                "id": r.id,
                "score": r.score,
                "payload": r.payload
            }
            for r in results
        ]
    
    def get_stats(self) -> Dict:
        """Get collection statistics."""
        stats = {}
        for name in COLLECTIONS.keys():
            try:
                info = self.client.get_collection(name)
                stats[name] = {
                    "vectors": info.vectors_count,
                    "points": info.points_count
                }
            except:
                stats[name] = {"vectors": 0, "points": 0}
        return stats


# Singleton
_store: Optional[EnhancedQdrantStore] = None

def get_vector_store() -> EnhancedQdrantStore:
    global _store
    if _store is None:
        _store = EnhancedQdrantStore()
    return _store
```

---

## 2. ENHANCED RAG ENGINE

### 2.1 Hybrid Retriever (Vector + BM25)

```python
# Engine8_Knowledge/scripts/hybrid_retriever.py

"""
Hybrid Retriever combining:
- Dense retrieval (Qdrant vectors)
- Sparse retrieval (BM25 keyword search)
- Reciprocal Rank Fusion for combining results
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import numpy as np
from rank_bm25 import BM25Okapi
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """Unified retrieval result."""
    id: str
    content: str
    score: float
    source: str  # "dense", "sparse", or "hybrid"
    metadata: Dict


class BM25Index:
    """BM25 keyword search index."""
    
    def __init__(self):
        self.documents: List[str] = []
        self.doc_ids: List[str] = []
        self.metadata: List[Dict] = []
        self.bm25: Optional[BM25Okapi] = None
    
    def add_documents(
        self,
        documents: List[str],
        doc_ids: List[str],
        metadata: List[Dict] = None
    ):
        """Add documents to BM25 index."""
        self.documents.extend(documents)
        self.doc_ids.extend(doc_ids)
        self.metadata.extend(metadata or [{} for _ in documents])
        
        # Rebuild index
        tokenized = [doc.lower().split() for doc in self.documents]
        self.bm25 = BM25Okapi(tokenized)
        logger.info(f"BM25 index rebuilt with {len(self.documents)} documents")
    
    def search(self, query: str, k: int = 10) -> List[RetrievalResult]:
        """Search BM25 index."""
        if not self.bm25:
            return []
        
        tokenized_query = query.lower().split()
        scores = self.bm25.get_scores(tokenized_query)
        
        # Get top k
        top_indices = np.argsort(scores)[::-1][:k]
        
        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                results.append(RetrievalResult(
                    id=self.doc_ids[idx],
                    content=self.documents[idx],
                    score=float(scores[idx]),
                    source="sparse",
                    metadata=self.metadata[idx]
                ))
        
        return results


class HybridRetriever:
    """Combines dense and sparse retrieval with RRF."""
    
    def __init__(self, vector_store, bm25_index: BM25Index):
        self.vector_store = vector_store
        self.bm25_index = bm25_index
        self.embedder = None
        self._init_embedder()
    
    def _init_embedder(self):
        """Initialize embedding model."""
        try:
            from openai import OpenAI
            self.embedder = OpenAI()
            logger.info("OpenAI embedder initialized")
        except:
            logger.warning("OpenAI embedder not available")
    
    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for text."""
        if not self.embedder:
            return [0.0] * 1536
        
        response = self.embedder.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    
    def _reciprocal_rank_fusion(
        self,
        results_lists: List[List[RetrievalResult]],
        k: int = 60
    ) -> List[RetrievalResult]:
        """Combine results using Reciprocal Rank Fusion."""
        scores = {}
        content_map = {}
        
        for results in results_lists:
            for rank, result in enumerate(results):
                doc_id = result.id
                # RRF score
                if doc_id not in scores:
                    scores[doc_id] = 0
                    content_map[doc_id] = result
                scores[doc_id] += 1 / (k + rank + 1)
        
        # Sort by RRF score
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        
        fused_results = []
        for doc_id in sorted_ids:
            result = content_map[doc_id]
            fused_results.append(RetrievalResult(
                id=result.id,
                content=result.content,
                score=scores[doc_id],
                source="hybrid",
                metadata=result.metadata
            ))
        
        return fused_results
    
    def retrieve(
        self,
        query: str,
        collection: str = "documents",
        k: int = 10,
        dense_weight: float = 0.5,
        sparse_weight: float = 0.5
    ) -> List[RetrievalResult]:
        """Hybrid retrieval combining dense and sparse."""
        results_lists = []
        
        # Dense retrieval (Qdrant)
        if dense_weight > 0:
            query_vector = self._get_embedding(query)
            dense_results = self.vector_store.search(
                collection=collection,
                query_vector=query_vector,
                limit=k * 2
            )
            
            dense_list = [
                RetrievalResult(
                    id=str(r["id"]),
                    content=r["payload"].get("content", str(r["payload"])),
                    score=r["score"],
                    source="dense",
                    metadata=r["payload"]
                )
                for r in dense_results
            ]
            results_lists.append(dense_list)
        
        # Sparse retrieval (BM25)
        if sparse_weight > 0:
            sparse_results = self.bm25_index.search(query, k=k * 2)
            results_lists.append(sparse_results)
        
        # Fuse results
        if len(results_lists) > 1:
            fused = self._reciprocal_rank_fusion(results_lists)
            return fused[:k]
        elif results_lists:
            return results_lists[0][:k]
        
        return []


# Global instances
_bm25_index: Optional[BM25Index] = None
_hybrid_retriever: Optional[HybridRetriever] = None


def get_bm25_index() -> BM25Index:
    global _bm25_index
    if _bm25_index is None:
        _bm25_index = BM25Index()
    return _bm25_index


def get_hybrid_retriever() -> HybridRetriever:
    global _hybrid_retriever
    if _hybrid_retriever is None:
        from scripts.vector_collections import get_vector_store
        _hybrid_retriever = HybridRetriever(
            vector_store=get_vector_store(),
            bm25_index=get_bm25_index()
        )
    return _hybrid_retriever
```

---

## 3. ENHANCED MEMORY LAYER

### 3.1 Multi-Backend Memory System

```python
# Engine8_Knowledge/scripts/memory_system.py

"""
Enhanced Memory System with Multiple Backends:
- Mem0: Long-term conversational memory
- Redis-VL: Semantic caching
- SQLite: Structured memory persistence
"""

import os
import json
import sqlite3
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MemoryDatabase:
    """SQLite-backed structured memory storage."""
    
    def __init__(self, db_path: str = "./data/memories.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
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


class EnhancedMemorySystem:
    """Combined memory system with multiple backends."""
    
    def __init__(self):
        self.db = MemoryDatabase()
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
                    "config": {"path": "./data/qdrant"}
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
            logger.info("Mem0 initialized")
        except Exception as e:
            logger.warning(f"Mem0 not available: {e}")
        
        # Redis-VL for caching
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
            except:
                pass
        
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
            except:
                pass
        
        # Fall back to SQLite
        return self.db.search_memories(query, memory_type, limit=limit)
    
    def cache_response(self, prompt: str, response: str, ttl: int = 3600):
        """Cache a prompt-response pair."""
        if self.redis_cache:
            try:
                self.redis_cache.store(prompt=prompt, response=response, ttl=ttl)
                return True
            except:
                pass
        return False
    
    def get_cached(self, prompt: str) -> Optional[str]:
        """Get cached response."""
        if self.redis_cache:
            try:
                result = self.redis_cache.check(prompt=prompt)
                if result:
                    return result[0].get("response")
            except:
                pass
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


# Singleton
_memory_system: Optional[EnhancedMemorySystem] = None


def get_memory_system() -> EnhancedMemorySystem:
    global _memory_system
    if _memory_system is None:
        _memory_system = EnhancedMemorySystem()
    return _memory_system
```

---

## 4. ENHANCED API GATEWAY

### 4.1 Unified API with All Features

```python
# Engine8_Knowledge/api_enhanced.py

"""
Enhanced FastAPI Gateway with all features integrated
"""

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import uvicorn

app = FastAPI(
    title="PTS BD Intelligence Hub",
    description="Central API for BD operations",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


# ============================================================================
# Health & Status
# ============================================================================

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "version": "2.0.0"}


@app.get("/stats")
async def stats():
    """Get system statistics."""
    from scripts.vector_collections import get_vector_store
    from scripts.memory_system import get_memory_system
    
    vector_store = get_vector_store()
    
    return {
        "vector_collections": vector_store.get_stats(),
        "memory_system": "active"
    }


# ============================================================================
# Search Endpoints
# ============================================================================

@app.get("/search")
async def search(
    q: str = Query(..., description="Search query"),
    collection: str = Query("documents", description="Collection to search"),
    limit: int = Query(10, description="Max results"),
    filters: str = Query(None, description="JSON filters")
):
    """Semantic vector search."""
    from scripts.vector_collections import get_vector_store
    from openai import OpenAI
    import json
    
    client = OpenAI()
    embedding = client.embeddings.create(
        model="text-embedding-3-small",
        input=q
    ).data[0].embedding
    
    store = get_vector_store()
    filter_dict = json.loads(filters) if filters else None
    
    results = store.search(
        collection=collection,
        query_vector=embedding,
        limit=limit,
        filters=filter_dict
    )
    
    return {"query": q, "collection": collection, "results": results}


@app.get("/search/hybrid")
async def hybrid_search(
    q: str = Query(..., description="Search query"),
    collection: str = Query("documents"),
    limit: int = Query(10),
    dense_weight: float = Query(0.5),
    sparse_weight: float = Query(0.5)
):
    """Hybrid search (vector + BM25)."""
    from scripts.hybrid_retriever import get_hybrid_retriever
    
    retriever = get_hybrid_retriever()
    results = retriever.retrieve(
        query=q,
        collection=collection,
        k=limit,
        dense_weight=dense_weight,
        sparse_weight=sparse_weight
    )
    
    return {
        "query": q,
        "strategy": "hybrid",
        "results": [vars(r) for r in results]
    }


# ============================================================================
# RAG Endpoints
# ============================================================================

@app.get("/rag/query")
async def rag_query(
    q: str = Query(..., description="Question"),
    strategy: str = Query("auto", description="Retrieval strategy"),
    limit: int = Query(10)
):
    """RAG query with strategy selection."""
    from scripts.rag_router import get_rag_router, RetrievalStrategy
    
    router = get_rag_router()
    return router.retrieve(q, RetrievalStrategy(strategy), limit)


@app.get("/rag/lightrag")
async def lightrag_query(
    q: str = Query(..., description="Question"),
    mode: str = Query("hybrid", description="Query mode: naive, local, global, hybrid")
):
    """Direct LightRAG query."""
    try:
        from scripts.lightrag_engine import get_lightrag_engine
        engine = get_lightrag_engine()
        result = engine.query(q, param={"mode": mode})
        return {"query": q, "mode": mode, "result": result}
    except Exception as e:
        return {"error": str(e)}


# ============================================================================
# Memory Endpoints
# ============================================================================

class MemoryInput(BaseModel):
    content: str
    memory_type: str = "general"
    metadata: Dict = None


@app.post("/memory/add")
async def add_memory(memory: MemoryInput):
    """Add a memory."""
    from scripts.memory_system import get_memory_system
    system = get_memory_system()
    memory_id = system.remember(memory.content, memory.memory_type, memory.metadata)
    return {"success": True, "id": memory_id}


@app.get("/memory/search")
async def search_memory(
    q: str = Query(...),
    memory_type: str = Query(None),
    limit: int = Query(10)
):
    """Search memories."""
    from scripts.memory_system import get_memory_system
    system = get_memory_system()
    results = system.recall(q, memory_type, limit)
    return {"query": q, "results": results}


class InteractionInput(BaseModel):
    contact: str
    type: str
    notes: str
    outcome: str = None


@app.post("/memory/interaction")
async def log_interaction(interaction: InteractionInput):
    """Log contact interaction."""
    from scripts.memory_system import get_memory_system
    system = get_memory_system()
    system.log_contact_interaction(
        interaction.contact,
        interaction.type,
        interaction.notes,
        interaction.outcome
    )
    return {"success": True}


@app.get("/memory/contact/{contact_name}")
async def get_contact_context(contact_name: str):
    """Get context for a contact."""
    from scripts.memory_system import get_memory_system
    system = get_memory_system()
    return system.get_contact_context(contact_name)


@app.get("/memory/program/{program_name}")
async def get_program_context(program_name: str):
    """Get context for a program."""
    from scripts.memory_system import get_memory_system
    system = get_memory_system()
    return system.get_program_context(program_name)


# ============================================================================
# Knowledge Graph Endpoints
# ============================================================================

@app.get("/graph/ecosystem/{program_name}")
async def get_program_ecosystem(program_name: str):
    """Get full ecosystem for a program."""
    from scripts.knowledge_graph import get_knowledge_graph
    graph = get_knowledge_graph()
    return graph.get_program_ecosystem(program_name)


@app.get("/graph/teaming/{contractor_name}")
async def get_teaming_partners(contractor_name: str):
    """Find teaming partners for a contractor."""
    from scripts.knowledge_graph import get_knowledge_graph
    graph = get_knowledge_graph()
    return graph.find_teaming_partners(contractor_name)


@app.get("/graph/query")
async def query_graph(q: str = Query(...)):
    """Natural language query of knowledge graph."""
    from scripts.knowledge_graph import get_knowledge_graph
    graph = get_knowledge_graph()
    return graph.query_graph(q)


# ============================================================================
# Ingestion Endpoints
# ============================================================================

class JobsInput(BaseModel):
    jobs: List[Dict]


@app.post("/ingest/jobs")
async def ingest_jobs(data: JobsInput, background_tasks: BackgroundTasks):
    """Ingest jobs into the system."""
    from scripts.vector_collections import get_vector_store
    from scripts.hybrid_retriever import get_bm25_index
    from openai import OpenAI
    
    client = OpenAI()
    store = get_vector_store()
    bm25 = get_bm25_index()
    
    # Generate embeddings
    texts = [f"{j.get('title', '')} {j.get('description', '')}" for j in data.jobs]
    embeddings = []
    
    for text in texts:
        emb = client.embeddings.create(
            model="text-embedding-3-small",
            input=text[:8000]
        ).data[0].embedding
        embeddings.append(emb)
    
    # Add to vector store
    ids = [j.get("job_id", str(i)) for i, j in enumerate(data.jobs)]
    store.upsert_vectors("jobs", embeddings, data.jobs, ids)
    
    # Add to BM25 index
    bm25.add_documents(texts, ids, data.jobs)
    
    return {"success": True, "count": len(data.jobs)}


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8100)
```

---

## 5. INSTALLATION SCRIPT

```bash
#!/bin/bash
# install_enhancements.sh

echo "Installing BD Hub Enhancements..."

# Core packages
pip install rank-bm25  # BM25 search
pip install mem0ai     # Memory layer
pip install redisvl    # Redis semantic cache
pip install redis      # Redis client

# RAG packages
pip install pageindex  # Vectorless RAG
pip install ultrarag   # Multi-step RAG

# Knowledge graph
pip install graphrag   # Entity extraction

# Agents
pip install crewai langgraph langchain-anthropic

# Document processing
pip install docling extract-thinker

# Evaluation
pip install ragas

echo "Installation complete!"
echo "Run: python api_enhanced.py"
```

---

## TESTING THE ENHANCED SYSTEM

```bash
# Start the enhanced API
python api_enhanced.py

# Test health
curl http://localhost:8100/health

# Test hybrid search
curl "http://localhost:8100/search/hybrid?q=DCGS+network+engineer&limit=10"

# Test memory
curl -X POST http://localhost:8100/memory/add \
  -H "Content-Type: application/json" \
  -d '{"content": "PACAF site is understaffed", "memory_type": "insight"}'

# Test RAG router
curl "http://localhost:8100/rag/query?q=Who%20are%20the%20contacts%20at%20Langley&strategy=auto"

# Test knowledge graph
curl "http://localhost:8100/graph/ecosystem/AF%20DCGS"
```

---

*Implementation Guide Generated: January 26, 2026*
