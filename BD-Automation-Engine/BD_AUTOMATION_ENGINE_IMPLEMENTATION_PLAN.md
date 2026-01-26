# BD-AUTOMATION-ENGINE: COMPREHENSIVE IMPLEMENTATION PLAN

## THE CENTRAL HUB - Prime Technical Services BD Intelligence System

**Project Location:** `C:\Users\gtmar\Projects\Auto-Claude\BD-Automation-Engine`  
**Role:** CENTRAL HUB - All other projects connect to this  
**API Endpoint:** `http://127.0.0.1:8100`  
**Git Branch:** `claude/setup-auto-claude-IrK21`

---

## TABLE OF CONTENTS

1. Executive Overview
2. Current State Analysis  
3. Target Architecture
4. Prerequisites & Environment Setup
5. Phase 1: Memory Layer (Mem0)
6. Phase 2: Knowledge Graph (LightRAG)
7. Phase 3: Hybrid Retrieval System
8. Phase 4: Query Router
9. Phase 5: Advanced Retrieval (PageIndex)
10. Phase 6: Caching Layer (Redis)
11. Phase 7: Document Processing (Docling)
12. Phase 8: Web Scraping Integration
13. Phase 9: Specialized BD Agents
14. Phase 10: Agent Orchestration (CrewAI)
15. Phase 11: Enhanced FastAPI Server
16. Phase 12: Enhanced MCP Server
17. Phase 13: YAML Pipelines (UltraRAG)
18. Phase 14: Evaluation Framework (RAGAS)
19. Phase 15: External Platform Integration
20. Phase 16: Data Migration & Sync
21. Phase 17: Testing & Validation
22. Phase 18: Deployment & Operations

---

## 1. EXECUTIVE OVERVIEW

### What Gets Built

| Component | Technology | Purpose | Priority |
|-----------|------------|---------|----------|
| Memory Layer | Mem0 | Cross-session BD context | CRITICAL |
| Knowledge Graph | LightRAG | Entity relationships | CRITICAL |
| Hybrid Retriever | BM25 + RRF + CrossEncoder | Optimal retrieval | HIGH |
| Query Router | Pattern matching | Intelligent routing | HIGH |
| Vectorless RAG | PageIndex | Audit trails | HIGH |
| Caching | Redis | 4x faster queries | MEDIUM |
| Document Processor | Docling | Federal PDFs | MEDIUM |
| Web Scrapers | Firecrawl + Crawl4AI | Web extraction | MEDIUM |
| BD Agents | 5 specialized agents | Intelligence | HIGH |
| Orchestration | CrewAI | Multi-agent workflows | MEDIUM |
| Evaluation | RAGAS | Quality metrics | MEDIUM |

### Repository References

| Repository | Stars | Purpose |
|------------|-------|---------|
| mem0ai/mem0 | 45,100+ | Memory layer |
| HKUDS/LightRAG | 25,400+ | Knowledge graph |
| VectifyAI/PageIndex | 7,700+ | Vectorless RAG |
| OpenBMB/UltraRAG | 3,700+ | YAML pipelines |
| docling-project/docling | 10,000+ | PDF processing |
| firecrawl/firecrawl | 77,100+ | Web scraping |
| unclecode/crawl4ai | 55,800+ | LLM-optimized scraping |
| crewAIInc/crewAI | 43,100+ | Agent orchestration |
| explodinggradients/ragas | 8,000+ | Evaluation |

---

## 2. CURRENT STATE ANALYSIS

### Existing Qdrant Collections

| Collection | Records | Purpose |
|------------|---------|---------|
| contacts | 7,337 | Cleared personnel |
| programs | 401 | Federal programs |
| documents | 205 | Indexed documents |
| activities | 500 | BD activities |
| jobs | 4 | Job postings |
| **TOTAL** | **8,447** | |

### Current MCP Tools (8 tools)

1. search_knowledge - Semantic search
2. add_document - Add to knowledge base
3. list_collections - List collections
4. get_collection_stats - Statistics
5. ask_knowledge - RAG Q&A
6. tag_document - Add tags
7. search_by_tag - Tag search
8. reindex_collection - Rebuild index

### Current FastAPI Endpoints (10 endpoints)

- /search (GET) - Semantic search
- /ask (GET) - RAG Q&A
- /collections (GET) - List collections
- /collections/{name}/stats (GET) - Stats
- /documents (POST) - Add document
- /documents/{id}/tags (POST) - Add tags
- /health (GET) - Health check

---

## 3. TARGET ARCHITECTURE

### After Implementation: Storage Layer

```
STORAGE LAYER
├── Qdrant (Vectors) - 15,000+ records
│   ├── contacts
│   ├── programs
│   ├── documents
│   ├── activities
│   └── jobs
├── Mem0 (Memory) - Unlimited memories
│   ├── interactions
│   ├── entity_facts
│   ├── bd_insights
│   └── scrape_results
├── LightRAG (Graph) - Dynamic
│   ├── entities
│   ├── relationships
│   └── networks
├── PageIndex (Vectorless) - Per-document trees
│   └── audit trails
└── Redis (Cache) - Query results
```

### After Implementation: API Layer

**FastAPI: 50+ endpoints**
**MCP: 40+ tools**

---

## 4. PREREQUISITES & ENVIRONMENT SETUP

### Step 1: Updated requirements.txt

```
# Core RAG
qdrant-client>=1.7.0
sentence-transformers>=2.2.0
llama-index>=0.10.0

# Memory (Mem0)
mem0ai>=0.1.0
chromadb>=0.4.0

# Knowledge Graph (LightRAG)
lightrag-hku>=0.1.0
networkx>=3.0

# Hybrid Retrieval
rank-bm25>=0.2.2

# Caching
redis>=5.0.0

# Document Processing
docling>=1.0.0

# Web Scraping
firecrawl-py>=0.0.16
crawl4ai>=0.3.0

# Agent Orchestration
crewai>=0.28.0

# Evaluation
ragas>=0.1.0
datasets>=2.14.0

# API
fastapi>=0.109.0
uvicorn>=0.27.0
pydantic>=2.5.0

# Anthropic
anthropic>=0.18.0

# Utilities
python-dotenv>=1.0.0
aiohttp>=3.9.0
numpy>=1.24.0
pyyaml>=6.0.0
```

### Step 2: Installation Commands

```bash
cd "C:\Users\gtmar\Projects\Auto-Claude\BD-Automation-Engine"
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

### Step 3: Directory Structure

```bash
mkdir -p Engine8_Knowledge/scripts
mkdir -p Engine8_Knowledge/agents
mkdir -p Engine8_Knowledge/pipelines
mkdir -p Engine8_Knowledge/evaluation
mkdir -p Engine8_Knowledge/integrations
mkdir -p Engine8_Knowledge/data/lightrag
mkdir -p Engine8_Knowledge/data/pageindex
mkdir -p Engine8_Knowledge/data/memory
```

### Step 4: Environment Variables (.env)

```
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
FIRECRAWL_API_KEY=fc-xxxxx
REDIS_URL=redis://localhost:6379
```

---

## 5. PHASE 1: MEMORY LAYER (Mem0)

### 5.1 File: `Engine8_Knowledge/scripts/memory_layer.py`

```python
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
            with open(self.memories_file, 'r') as f:
                data = json.load(f)
                self.memories = [MemoryEntry(**e) for e in data]
    
    def _save(self):
        os.makedirs(os.path.dirname(self.memories_file), exist_ok=True)
        with open(self.memories_file, 'w') as f:
            json.dump([asdict(m) for m in self.memories], f, indent=2)
    
    def add(self, content: str, memory_type: str, metadata: Dict) -> str:
        import uuid
        memory_id = str(uuid.uuid4())
        self.memories.append(MemoryEntry(
            id=memory_id,
            content=content,
            memory_type=memory_type,
            timestamp=datetime.now().isoformat(),
            metadata=metadata
        ))
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
            os.path.dirname(os.path.dirname(__file__)),
            "data", "memory"
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
                "provider": "anthropic",
                "config": {
                    "model": "claude-sonnet-4-20250514",
                    "api_key": os.getenv("ANTHROPIC_API_KEY"),
                }
            },
            "embedder": {
                "provider": "huggingface",
                "config": {"model": "sentence-transformers/all-MiniLM-L6-v2"}
            },
            "vector_store": {
                "provider": "chroma",
                "config": {
                    "collection_name": "bd_memory",
                    "path": self.storage_path
                }
            }
        }
        try:
            self.memory = Memory.from_config(config)
            self.backend = "mem0"
        except Exception as e:
            logger.error(f"Mem0 init failed: {e}")
            self._init_fallback()
    
    def _init_fallback(self):
        self.memory = FallbackMemory(self.storage_path)
        self.backend = "fallback"
    
    def add_interaction(self, interaction: str, metadata: Optional[Dict] = None) -> Dict:
        """Add query/response pair."""
        meta = metadata or {}
        meta["memory_type"] = "interaction"
        meta["timestamp"] = datetime.now().isoformat()
        
        if self.backend == "mem0":
            return self.memory.add([{"role": "user", "content": interaction}],
                                    user_id=self.user_id, metadata=meta)
        return {"id": self.memory.add(interaction, "interaction", meta)}
    
    def add_entity_fact(self, entity_name: str, entity_type: str, fact: str) -> Dict:
        """Add fact about company/program/contact."""
        structured = f"[{entity_type.upper()}] {entity_name}: {fact}"
        meta = {
            "memory_type": "entity_fact",
            "entity_name": entity_name,
            "entity_type": entity_type,
            "timestamp": datetime.now().isoformat()
        }
        if self.backend == "mem0":
            return self.memory.add([{"role": "user", "content": structured}],
                                    user_id=self.user_id, metadata=meta)
        return {"id": self.memory.add(structured, "entity_fact", meta)}
    
    def add_bd_insight(self, insight_type: str, insight: str, 
                       source: str = "analysis", confidence: float = 0.8) -> Dict:
        """Add opportunity/risk/relationship insight."""
        structured = f"[BD INSIGHT - {insight_type.upper()}] {insight}"
        meta = {
            "memory_type": "bd_insight",
            "insight_type": insight_type,
            "source": source,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat()
        }
        if self.backend == "mem0":
            return self.memory.add([{"role": "user", "content": structured}],
                                    user_id=self.user_id, metadata=meta)
        return {"id": self.memory.add(structured, "bd_insight", meta)}
    
    def add_scrape_result(self, scrape_type: str, summary: str, count: int) -> Dict:
        """Add scrape operation summary."""
        structured = f"[SCRAPE] {scrape_type}: {summary} ({count} records)"
        meta = {
            "memory_type": "scrape_result",
            "scrape_type": scrape_type,
            "record_count": count,
            "timestamp": datetime.now().isoformat()
        }
        if self.backend == "mem0":
            return self.memory.add([{"role": "user", "content": structured}],
                                    user_id=self.user_id, metadata=meta)
        return {"id": self.memory.add(structured, "scrape_result", meta)}
    
    def get_context(self, query: str, limit: int = 10) -> List[Dict]:
        """Retrieve relevant memories."""
        if self.backend == "mem0":
            results = self.memory.search(query=query, user_id=self.user_id, limit=limit)
            return results.get("results", [])
        return self.memory.search(query, limit)
    
    def get_entity_facts(self, entity_name: str, limit: int = 20) -> List[Dict]:
        return self.get_context(f"Facts about {entity_name}", limit)
    
    def get_recent_insights(self, insight_type: str = None, limit: int = 10) -> List[Dict]:
        query = f"BD insights {insight_type or 'all'}"
        return self.get_context(query, limit)
    
    def get_stats(self) -> Dict:
        if self.backend == "mem0":
            try:
                all_mem = self.memory.get_all(user_id=self.user_id)
                memories = all_mem.get("results", [])
            except:
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
            "backend": self.backend
        }


# Singleton
_memory_instance = None

def get_memory(storage_path: str = None) -> BDMemoryLayer:
    global _memory_instance
    if _memory_instance is None:
        _memory_instance = BDMemoryLayer(storage_path)
    return _memory_instance
```

### 5.2 Test Memory Layer

```bash
cd Engine8_Knowledge
python -c "
from scripts.memory_layer import get_memory
m = get_memory()
m.add_entity_fact('Leidos', 'company', 'Prime on DCGS-A')
m.add_bd_insight('opportunity', 'DCGS-A recompete Q2 2026')
print(m.get_stats())
print(m.get_context('DCGS'))
"
```

### 5.3 Phase 1 Verification Checklist

- [ ] memory_layer.py created
- [ ] data/memory directory exists
- [ ] Test script runs without errors
- [ ] Memories persist across restarts
- [ ] get_stats() returns correct counts

---

## 6. PHASE 2: KNOWLEDGE GRAPH (LightRAG)

### 6.1 File: `Engine8_Knowledge/scripts/lightrag_engine.py`

```python
"""
LightRAG Knowledge Graph for BD Intelligence Hub
Repository: https://github.com/HKUDS/LightRAG (25,400+ stars)
"""

import os
import asyncio
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from lightrag import LightRAG, QueryParam
    from lightrag.llm import anthropic_complete
    from lightrag.utils import EmbeddingFunc
    LIGHTRAG_AVAILABLE = True
except ImportError:
    LIGHTRAG_AVAILABLE = False
    logger.warning("LightRAG not available, using fallback")


class FallbackKnowledgeGraph:
    """Simple JSON-based fallback."""
    
    def __init__(self, working_dir: str):
        self.working_dir = working_dir
        self.docs_file = os.path.join(working_dir, "documents.json")
        self.documents: List[Dict] = []
        self._load()
    
    def _load(self):
        if os.path.exists(self.docs_file):
            with open(self.docs_file, 'r') as f:
                self.documents = json.load(f)
    
    def _save(self):
        os.makedirs(self.working_dir, exist_ok=True)
        with open(self.docs_file, 'w') as f:
            json.dump(self.documents, f, indent=2)
    
    async def insert(self, content: str) -> bool:
        self.documents.append({
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self._save()
        return True
    
    async def query(self, query: str, mode: str = "hybrid") -> str:
        query_lower = query.lower()
        relevant = [d["content"] for d in self.documents 
                   if any(w in d["content"].lower() for w in query_lower.split())]
        if relevant:
            return "Based on knowledge graph:\n\n" + "\n\n".join(relevant[:3])
        return "No relevant information found."


class BDKnowledgeGraph:
    """
    Knowledge graph for entity relationships.
    
    Query modes:
    - local: Entity-specific facts (who, what, when)
    - global: Abstract themes (how, why)
    - hybrid: Both combined (recommended)
    """
    
    def __init__(self, working_dir: str = None):
        self.working_dir = working_dir or os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "data", "lightrag"
        )
        os.makedirs(self.working_dir, exist_ok=True)
        
        if LIGHTRAG_AVAILABLE:
            self._init_lightrag()
        else:
            self._init_fallback()
    
    def _init_lightrag(self):
        try:
            from sentence_transformers import SentenceTransformer
            embedder = SentenceTransformer('all-MiniLM-L6-v2')
            
            async def embed_func(texts):
                return embedder.encode(texts).tolist()
            
            self.rag = LightRAG(
                working_dir=self.working_dir,
                llm_model_func=anthropic_complete,
                llm_model_name="claude-sonnet-4-20250514",
                embedding_func=EmbeddingFunc(
                    embedding_dim=384, max_token_size=512, func=embed_func
                ),
            )
            self.backend = "lightrag"
        except Exception as e:
            logger.error(f"LightRAG init failed: {e}")
            self._init_fallback()
    
    def _init_fallback(self):
        self.rag = FallbackKnowledgeGraph(self.working_dir)
        self.backend = "fallback"
    
    async def insert_document(self, content: str) -> bool:
        """Insert document, extract entities/relationships."""
        try:
            if self.backend == "lightrag":
                await self.rag.ainsert(content)
            else:
                await self.rag.insert(content)
            return True
        except Exception as e:
            logger.error(f"Insert error: {e}")
            return False
    
    def insert_document_sync(self, content: str) -> bool:
        return asyncio.run(self.insert_document(content))
    
    async def insert_program(self, program: Dict) -> bool:
        """Insert federal program."""
        content = f"""
FEDERAL PROGRAM: {program.get('name', 'Unknown')}
Description: {program.get('description', '')}
Agency: {program.get('agency', '')}
Prime Contractors: {', '.join(program.get('primes', []))}
Contract Value: {program.get('value', '')}
Clearance: {program.get('clearance', '')}
Technologies: {', '.join(program.get('technologies', []))}
"""
        return await self.insert_document(content)
    
    async def insert_company(self, company: Dict) -> bool:
        """Insert company profile."""
        content = f"""
COMPANY: {company.get('name', 'Unknown')}
Type: {company.get('type', '')}
Capabilities: {', '.join(company.get('capabilities', []))}
Programs: {', '.join(company.get('programs', []))}
Partners: {', '.join(company.get('partners', []))}
Locations: {', '.join(company.get('locations', []))}
"""
        return await self.insert_document(content)
    
    async def insert_contact(self, contact: Dict) -> bool:
        """Insert contact profile."""
        content = f"""
CONTACT: {contact.get('name', 'Unknown')}
Company: {contact.get('company', '')}
Title: {contact.get('title', '')}
Programs: {', '.join(contact.get('programs', []))}
Clearance: {contact.get('clearance', '')}
"""
        return await self.insert_document(content)
    
    async def query(self, query: str, mode: str = "hybrid") -> str:
        """Query the knowledge graph."""
        try:
            if self.backend == "lightrag":
                param = QueryParam(mode=mode)
                return await self.rag.aquery(query, param=param)
            return await self.rag.query(query, mode)
        except Exception as e:
            logger.error(f"Query error: {e}")
            return f"Error: {str(e)}"
    
    def query_sync(self, query: str, mode: str = "hybrid") -> str:
        return asyncio.run(self.query(query, mode))
    
    async def find_relationships(self, entity_name: str) -> Dict:
        """Find all relationships for an entity."""
        response = await self.query(
            f"What are all relationships for {entity_name}?",
            mode="local"
        )
        return {"entity": entity_name, "relationships": response}
    
    async def analyze_network(self, company_name: str) -> str:
        """Analyze contractor network."""
        return await self.query(
            f"Analyze network of {company_name}: partners, programs, positioning",
            mode="global"
        )
    
    def get_stats(self) -> Dict:
        files = os.listdir(self.working_dir) if os.path.exists(self.working_dir) else []
        return {
            "working_dir": self.working_dir,
            "backend": self.backend,
            "files": len(files)
        }


# Singleton
_graph_instance = None

def get_knowledge_graph(working_dir: str = None) -> BDKnowledgeGraph:
    global _graph_instance
    if _graph_instance is None:
        _graph_instance = BDKnowledgeGraph(working_dir)
    return _graph_instance
```

### 6.2 Test Knowledge Graph

```bash
cd Engine8_Knowledge
python -c "
import asyncio
from scripts.lightrag_engine import get_knowledge_graph

async def test():
    graph = get_knowledge_graph()
    
    # Insert program
    await graph.insert_program({
        'name': 'DCGS-A',
        'description': 'Distributed Common Ground System - Army',
        'agency': 'US Army',
        'primes': ['Leidos', 'General Dynamics'],
        'value': '\$950M',
        'clearance': 'TS/SCI'
    })
    
    # Query
    result = await graph.query('Who are primes on DCGS-A?', mode='local')
    print(result)
    print(graph.get_stats())

asyncio.run(test())
"
```

### 6.3 Phase 2 Verification Checklist

- [ ] lightrag_engine.py created
- [ ] data/lightrag directory exists
- [ ] Can insert programs, companies, contacts
- [ ] Can query with local, global, hybrid modes
- [ ] Relationships are extracted

---

## 7. PHASE 3: HYBRID RETRIEVAL SYSTEM

### 7.1 File: `Engine8_Knowledge/scripts/hybrid_retriever.py`

```python
"""
Hybrid Retriever: Semantic + BM25 + CrossEncoder Reranking
30-50% better recall than semantic-only
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import numpy as np
import logging

from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer, CrossEncoder
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    id: str
    text: str
    score: float
    source: str  # semantic, keyword, hybrid
    metadata: Dict[str, Any]


class HybridRetriever:
    """
    Hybrid retrieval combining:
    1. Semantic search (Qdrant)
    2. BM25 keyword search
    3. Reciprocal Rank Fusion (RRF)
    4. CrossEncoder reranking
    """
    
    def __init__(
        self,
        qdrant_path: str = "./data/qdrant",
        collection_name: str = "bd_knowledge",
        use_reranker: bool = True
    ):
        # Qdrant
        self.qdrant = QdrantClient(path=qdrant_path)
        self.collection_name = collection_name
        
        # Embedder
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Reranker
        self.use_reranker = use_reranker
        if use_reranker:
            self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        
        # BM25 indices (built on-demand)
        self._bm25_indices: Dict[str, BM25Okapi] = {}
        self._bm25_docs: Dict[str, List[Dict]] = {}
    
    def _build_bm25_index(self, collection: str, documents: List[Dict]):
        """Build BM25 index for collection."""
        tokenized = [doc.get('text', '').lower().split() for doc in documents]
        self._bm25_indices[collection] = BM25Okapi(tokenized)
        self._bm25_docs[collection] = documents
    
    def _semantic_search(
        self, query: str, collection: str, limit: int = 20
    ) -> List[SearchResult]:
        """Qdrant semantic search."""
        query_vector = self.embedder.encode(query).tolist()
        
        try:
            results = self.qdrant.search(
                collection_name=collection,
                query_vector=query_vector,
                limit=limit
            )
            return [
                SearchResult(
                    id=str(r.id),
                    text=r.payload.get('text', ''),
                    score=r.score,
                    source='semantic',
                    metadata=r.payload
                )
                for r in results
            ]
        except Exception as e:
            logger.error(f"Semantic search error: {e}")
            return []
    
    def _keyword_search(
        self, query: str, collection: str, limit: int = 20
    ) -> List[SearchResult]:
        """BM25 keyword search."""
        if collection not in self._bm25_indices:
            docs = self._fetch_all_docs(collection)
            self._build_bm25_index(collection, docs)
        
        bm25 = self._bm25_indices[collection]
        docs = self._bm25_docs[collection]
        
        tokenized_query = query.lower().split()
        scores = bm25.get_scores(tokenized_query)
        
        top_indices = np.argsort(scores)[::-1][:limit]
        
        return [
            SearchResult(
                id=docs[idx].get('id', str(idx)),
                text=docs[idx].get('text', ''),
                score=float(scores[idx]),
                source='keyword',
                metadata=docs[idx]
            )
            for idx in top_indices if scores[idx] > 0
        ]
    
    def _fetch_all_docs(self, collection: str) -> List[Dict]:
        """Fetch all docs from Qdrant for BM25 indexing."""
        docs = []
        offset = None
        
        try:
            while True:
                results, offset = self.qdrant.scroll(
                    collection_name=collection,
                    limit=100,
                    offset=offset,
                    with_payload=True
                )
                for r in results:
                    docs.append({
                        'id': str(r.id),
                        'text': r.payload.get('text', ''),
                        **r.payload
                    })
                if offset is None:
                    break
        except Exception as e:
            logger.error(f"Fetch error: {e}")
        
        return docs
    
    def _reciprocal_rank_fusion(
        self, rankings: List[List[SearchResult]], k: int = 60
    ) -> List[SearchResult]:
        """Combine rankings with RRF."""
        scores: Dict[str, float] = {}
        results_map: Dict[str, SearchResult] = {}
        
        for ranking in rankings:
            for rank, result in enumerate(ranking):
                doc_id = result.id
                if doc_id not in scores:
                    scores[doc_id] = 0
                    results_map[doc_id] = result
                scores[doc_id] += 1 / (k + rank + 1)
        
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        
        final = []
        for doc_id in sorted_ids:
            result = results_map[doc_id]
            result.score = scores[doc_id]
            result.source = 'hybrid'
            final.append(result)
        
        return final
    
    def _rerank(
        self, query: str, results: List[SearchResult], top_k: int = 10
    ) -> List[SearchResult]:
        """Rerank with CrossEncoder."""
        if not self.use_reranker or not results:
            return results[:top_k]
        
        pairs = [(query, r.text) for r in results]
        scores = self.reranker.predict(pairs)
        
        scored = list(zip(results, scores))
        scored.sort(key=lambda x: x[1], reverse=True)
        
        final = []
        for result, score in scored[:top_k]:
            result.score = float(score)
            final.append(result)
        
        return final
    
    def search(
        self,
        query: str,
        collection: str = "bd_knowledge",
        limit: int = 10,
        use_hybrid: bool = True,
        use_rerank: bool = True
    ) -> List[SearchResult]:
        """
        Main search method.
        
        Args:
            query: Search query
            collection: Qdrant collection
            limit: Results to return
            use_hybrid: Combine semantic + keyword
            use_rerank: Apply CrossEncoder
        """
        # Semantic search
        semantic_results = self._semantic_search(query, collection, limit * 3)
        
        if not use_hybrid:
            if use_rerank:
                return self._rerank(query, semantic_results, limit)
            return semantic_results[:limit]
        
        # Keyword search
        keyword_results = self._keyword_search(query, collection, limit * 3)
        
        # RRF fusion
        hybrid_results = self._reciprocal_rank_fusion(
            [semantic_results, keyword_results]
        )
        
        # Rerank
        if use_rerank:
            return self._rerank(query, hybrid_results, limit)
        
        return hybrid_results[:limit]
    
    def search_all(
        self, query: str, collections: List[str], limit_per: int = 5
    ) -> Dict[str, List[SearchResult]]:
        """Search across multiple collections."""
        return {
            col: self.search(query, col, limit_per)
            for col in collections
        }


# Singleton
_retriever_instance = None

def get_hybrid_retriever() -> HybridRetriever:
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = HybridRetriever()
    return _retriever_instance
```

### 7.2 Test Hybrid Retriever

```bash
cd Engine8_Knowledge
python -c "
from scripts.hybrid_retriever import get_hybrid_retriever

retriever = get_hybrid_retriever()
results = retriever.search(
    'DCGS software engineer',
    collection='contacts',
    limit=5,
    use_hybrid=True,
    use_rerank=True
)
for r in results:
    print(f'[{r.source}] {r.score:.3f}: {r.text[:80]}...')
"
```

### 7.3 Phase 3 Verification Checklist

- [ ] hybrid_retriever.py created
- [ ] Semantic search works
- [ ] BM25 keyword search works
- [ ] RRF fusion combines results
- [ ] CrossEncoder reranking improves order

---

## 8. PHASE 4: QUERY ROUTER

### 8.1 File: `Engine8_Knowledge/scripts/query_router.py`

```python
"""
Query Router - Routes queries to optimal retrieval system(s)
"""

import re
import asyncio
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass
import logging

from scripts.memory_layer import get_memory
from scripts.lightrag_engine import get_knowledge_graph
from scripts.hybrid_retriever import get_hybrid_retriever

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QueryType(Enum):
    FACTUAL = "factual"           # → Qdrant semantic
    RELATIONAL = "relational"     # → LightRAG graph
    COMPREHENSIVE = "comprehensive"  # → All systems
    MEMORY = "memory"             # → Mem0
    KEYWORD = "keyword"           # → BM25


@dataclass
class RouteDecision:
    query_type: QueryType
    systems: List[str]
    confidence: float
    reasoning: str


@dataclass
class QueryResult:
    answer: str
    sources: List[Dict]
    query_type: QueryType
    systems_used: List[str]


class QueryRouter:
    """
    Routes queries to optimal retrieval system(s).
    
    Query Classification:
    - FACTUAL: Simple facts → Qdrant
    - RELATIONAL: Entity connections → LightRAG
    - COMPREHENSIVE: Complex analysis → All systems
    - MEMORY: Past context → Mem0
    - KEYWORD: Exact match → BM25
    """
    
    def __init__(self):
        self.memory = get_memory()
        self.graph = get_knowledge_graph()
        self.retriever = get_hybrid_retriever()
        
        self.patterns = {
            QueryType.RELATIONAL: [
                r"relationship|connected|related|partner|teaming",
                r"who works with|network|associates",
                r"prime|sub|contractor relationship"
            ],
            QueryType.MEMORY: [
                r"remember|recall|last time|previously",
                r"we discussed|you mentioned|history"
            ],
            QueryType.COMPREHENSIVE: [
                r"comprehensive|complete|detailed|everything",
                r"analysis|analyze|evaluate|compare|strategy"
            ],
            QueryType.KEYWORD: [
                r"exact|specifically|contract number",
                r"cage code|duns|naics|solicitation"
            ]
        }
    
    def _classify_query(self, query: str) -> RouteDecision:
        """Classify query and determine routing."""
        query_lower = query.lower()
        
        matches = {}
        for qt, patterns in self.patterns.items():
            count = sum(1 for p in patterns if re.search(p, query_lower))
            if count > 0:
                matches[qt] = count
        
        if not matches:
            return RouteDecision(
                query_type=QueryType.FACTUAL,
                systems=["qdrant"],
                confidence=0.6,
                reasoning="Default to semantic search"
            )
        
        best_type = max(matches, key=matches.get)
        confidence = min(0.9, 0.5 + matches[best_type] * 0.15)
        
        system_map = {
            QueryType.FACTUAL: ["qdrant"],
            QueryType.RELATIONAL: ["lightrag"],
            QueryType.COMPREHENSIVE: ["qdrant", "lightrag", "mem0"],
            QueryType.MEMORY: ["mem0"],
            QueryType.KEYWORD: ["bm25"]
        }
        
        return RouteDecision(
            query_type=best_type,
            systems=system_map[best_type],
            confidence=confidence,
            reasoning=f"Matched patterns for {best_type.value}"
        )
    
    async def _query_qdrant(self, query: str, limit: int = 10) -> List[Dict]:
        results = self.retriever.search(query, "bd_knowledge", limit, True, True)
        return [{"text": r.text, "score": r.score, "source": "qdrant"} for r in results]
    
    async def _query_lightrag(self, query: str) -> List[Dict]:
        response = await self.graph.query(query, mode="hybrid")
        return [{"text": response, "score": 1.0, "source": "lightrag"}]
    
    async def _query_mem0(self, query: str, limit: int = 10) -> List[Dict]:
        results = self.memory.get_context(query, limit)
        return [{"text": r.get("memory", ""), "score": r.get("score", 0), "source": "mem0"} for r in results]
    
    async def _query_bm25(self, query: str, limit: int = 10) -> List[Dict]:
        results = self.retriever._keyword_search(query, "bd_knowledge", limit)
        return [{"text": r.text, "score": r.score, "source": "bm25"} for r in results]
    
    async def smart_query(
        self, query: str, override_type: Optional[QueryType] = None
    ) -> QueryResult:
        """
        Intelligently route and execute query.
        
        Args:
            query: Natural language query
            override_type: Force specific query type
        """
        if override_type:
            decision = RouteDecision(
                query_type=override_type,
                systems=self._get_systems(override_type),
                confidence=1.0,
                reasoning="User override"
            )
        else:
            decision = self._classify_query(query)
        
        all_results = []
        systems_used = []
        
        for system in decision.systems:
            try:
                if system == "qdrant":
                    results = await self._query_qdrant(query)
                elif system == "lightrag":
                    results = await self._query_lightrag(query)
                elif system == "mem0":
                    results = await self._query_mem0(query)
                elif system == "bm25":
                    results = await self._query_bm25(query)
                else:
                    continue
                all_results.extend(results)
                systems_used.append(system)
            except Exception as e:
                logger.error(f"Error querying {system}: {e}")
        
        answer = self._synthesize(query, all_results)
        
        return QueryResult(
            answer=answer,
            sources=all_results,
            query_type=decision.query_type,
            systems_used=systems_used
        )
    
    def _get_systems(self, qt: QueryType) -> List[str]:
        return {
            QueryType.FACTUAL: ["qdrant"],
            QueryType.RELATIONAL: ["lightrag"],
            QueryType.COMPREHENSIVE: ["qdrant", "lightrag", "mem0"],
            QueryType.MEMORY: ["mem0"],
            QueryType.KEYWORD: ["bm25"]
        }.get(qt, ["qdrant"])
    
    def _synthesize(self, query: str, results: List[Dict]) -> str:
        if not results:
            return "No relevant information found."
        
        top = sorted(results, key=lambda x: x.get('score', 0), reverse=True)[:5]
        parts = [f"[{r['source']}] {r['text'][:500]}" for r in top]
        return "\n\n".join(parts)


async def smart_query(query: str) -> QueryResult:
    """Convenience function for smart querying."""
    router = QueryRouter()
    return await router.smart_query(query)
```

### 8.2 Test Query Router

```bash
cd Engine8_Knowledge
python -c "
import asyncio
from scripts.query_router import QueryRouter

router = QueryRouter()

# Test classification
queries = [
    'What companies are connected to DCGS-A?',  # Relational
    'Find DCGS engineer positions',              # Factual
    'Comprehensive analysis of Leidos',          # Comprehensive
    'What did we discuss about Navy?',           # Memory
    'Find contract W15QKN-21-C-0034',            # Keyword
]

for q in queries:
    decision = router._classify_query(q)
    print(f'{q[:40]}... → {decision.query_type.value} ({decision.confidence:.2f})')
"
```

### 8.3 Phase 4 Verification Checklist

- [ ] query_router.py created
- [ ] Correctly classifies query types
- [ ] Routes to appropriate systems
- [ ] Synthesizes multi-source results

---

## 9. PHASE 5: ADVANCED RETRIEVAL (PageIndex)

### 9.1 File: `Engine8_Knowledge/scripts/pageindex_engine.py`

```python
"""
PageIndex Vectorless RAG - 98.7% accuracy with audit trails
Repository: https://github.com/VectifyAI/PageIndex (7,700+ stars)
"""

import os
import json
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PageNode:
    id: str
    title: str
    content: str
    level: int
    children: List[str]
    parent: Optional[str]


@dataclass
class RetrievalPath:
    query: str
    path: List[Dict]
    final_answer: str
    confidence: float


class PageIndexEngine:
    """
    Vectorless RAG with hierarchical tree search.
    Provides explainable audit trails for federal compliance.
    """
    
    def __init__(self, index_dir: str = None):
        self.index_dir = index_dir or os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "data", "pageindex"
        )
        os.makedirs(self.index_dir, exist_ok=True)
        self.trees: Dict[str, Dict[str, PageNode]] = {}
        self._load_indices()
    
    def _load_indices(self):
        index_file = os.path.join(self.index_dir, "indices.json")
        if os.path.exists(index_file):
            with open(index_file, 'r') as f:
                data = json.load(f)
                for doc_id, tree in data.items():
                    self.trees[doc_id] = {
                        nid: PageNode(**node) for nid, node in tree.items()
                    }
    
    def _save_indices(self):
        index_file = os.path.join(self.index_dir, "indices.json")
        data = {
            doc_id: {nid: asdict(node) for nid, node in tree.items()}
            for doc_id, tree in self.trees.items()
        }
        with open(index_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def index_document(self, doc_id: str, content: str) -> bool:
        """Index document by building hierarchical tree."""
        tree = {}
        root_id = f"{doc_id}_root"
        
        tree[root_id] = PageNode(
            id=root_id, title=f"Document: {doc_id}",
            content="", level=0, children=[], parent=None
        )
        
        lines = content.split('\n')
        node_counter = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                title = line.lstrip('#').strip()
                node_id = f"{doc_id}_node_{node_counter}"
                node_counter += 1
                
                tree[node_id] = PageNode(
                    id=node_id, title=title, content="",
                    level=level, children=[], parent=root_id
                )
                tree[root_id].children.append(node_id)
            else:
                if tree[root_id].children:
                    last_node = tree[root_id].children[-1]
                    tree[last_node].content += line + "\n"
                else:
                    tree[root_id].content += line + "\n"
        
        self.trees[doc_id] = tree
        self._save_indices()
        return True
    
    def query(self, query: str, doc_ids: List[str] = None) -> RetrievalPath:
        """Query using tree-search with audit trail."""
        search_trees = {
            did: self.trees[did] for did in (doc_ids or self.trees.keys())
            if did in self.trees
        }
        
        path = []
        best_nodes = []
        
        for doc_id, tree in search_trees.items():
            for node_id, node in tree.items():
                relevance = self._compute_relevance(query, node)
                if relevance > 0.3:
                    best_nodes.append((node, relevance, doc_id))
                    path.append({
                        "node_id": node_id,
                        "doc_id": doc_id,
                        "title": node.title,
                        "relevance": relevance
                    })
        
        best_nodes.sort(key=lambda x: x[1], reverse=True)
        
        if best_nodes:
            top_node, score, _ = best_nodes[0]
            answer = f"From '{top_node.title}': {top_node.content[:500]}"
        else:
            answer = "No relevant information found."
            score = 0.0
        
        return RetrievalPath(query=query, path=path[:5], final_answer=answer, confidence=score)
    
    def _compute_relevance(self, query: str, node: PageNode) -> float:
        query_terms = set(query.lower().split())
        node_text = f"{node.title} {node.content}".lower()
        node_terms = set(node_text.split())
        if not query_terms:
            return 0.0
        return len(query_terms & node_terms) / len(query_terms)
    
    def get_audit_trail(self, result: RetrievalPath) -> List[Dict]:
        """Get audit trail for compliance."""
        return [
            {"step": i+1, "node": p["node_id"], "doc": p["doc_id"],
             "section": p["title"], "relevance": p["relevance"]}
            for i, p in enumerate(result.path)
        ]
    
    def get_stats(self) -> Dict:
        return {
            "documents": len(self.trees),
            "total_nodes": sum(len(t) for t in self.trees.values()),
            "index_dir": self.index_dir
        }


_pageindex_instance = None

def get_pageindex() -> PageIndexEngine:
    global _pageindex_instance
    if _pageindex_instance is None:
        _pageindex_instance = PageIndexEngine()
    return _pageindex_instance
```

### 9.2 Phase 5 Verification Checklist

- [ ] pageindex_engine.py created
- [ ] Can index documents with headers
- [ ] Query returns RetrievalPath with audit trail
- [ ] get_audit_trail() works for compliance

---

## 10. PHASE 6: CACHING LAYER (Redis)

### 10.1 File: `Engine8_Knowledge/scripts/redis_cache.py`

```python
"""
Redis Semantic Cache - 4x latency reduction for repeated queries
"""

import os
import json
import hashlib
from typing import Dict, List, Optional
from datetime import timedelta
import logging

import numpy as np
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class InMemoryCache:
    """Fallback when Redis unavailable."""
    
    def __init__(self):
        self.cache: Dict[str, Dict] = {}
    
    def get(self, key: str) -> Optional[Dict]:
        return self.cache.get(key)
    
    def set(self, key: str, value: Dict, ttl: int = 3600):
        self.cache[key] = value
    
    def delete(self, key: str):
        self.cache.pop(key, None)
    
    def clear(self):
        self.cache.clear()


class SemanticCache:
    """
    Semantic cache with similarity matching.
    Caches query results and finds similar cached queries.
    """
    
    def __init__(
        self,
        redis_url: str = None,
        similarity_threshold: float = 0.85,
        ttl_hours: int = 24
    ):
        redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.similarity_threshold = similarity_threshold
        self.ttl = timedelta(hours=ttl_hours)
        
        if REDIS_AVAILABLE:
            try:
                self.redis = redis.from_url(redis_url)
                self.redis.ping()
                self.backend = "redis"
            except:
                self.redis = InMemoryCache()
                self.backend = "memory"
        else:
            self.redis = InMemoryCache()
            self.backend = "memory"
        
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        self.CACHE_PREFIX = "bd_cache:"
        self.EMBED_PREFIX = "bd_embed:"
        self.INDEX_KEY = "bd_cache_index"
    
    def _get_embedding(self, text: str) -> List[float]:
        return self.embedder.encode(text).tolist()
    
    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        a, b = np.array(v1), np.array(v2)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
    
    def _generate_key(self, query: str) -> str:
        return hashlib.md5(query.encode()).hexdigest()
    
    def get(self, query: str) -> Optional[Dict]:
        """Get cached result with semantic similarity."""
        query_embedding = self._get_embedding(query)
        
        # Get index
        if self.backend == "redis":
            index = self.redis.smembers(self.INDEX_KEY) or set()
        else:
            index = set(self.redis.cache.keys())
        
        best_match = None
        best_sim = 0.0
        
        for cached_key in index:
            if isinstance(cached_key, bytes):
                cached_key = cached_key.decode()
            
            # Get embedding
            if self.backend == "redis":
                embed_data = self.redis.get(f"{self.EMBED_PREFIX}{cached_key}")
                if embed_data:
                    cached_embed = json.loads(embed_data)
                else:
                    continue
            else:
                entry = self.redis.get(cached_key)
                if entry and 'embedding' in entry:
                    cached_embed = entry['embedding']
                else:
                    continue
            
            sim = self._cosine_similarity(query_embedding, cached_embed)
            if sim > best_sim and sim >= self.similarity_threshold:
                best_sim = sim
                best_match = cached_key
        
        if best_match:
            if self.backend == "redis":
                data = self.redis.get(f"{self.CACHE_PREFIX}{best_match}")
                if data:
                    result = json.loads(data)
                    result['cache_hit'] = True
                    result['similarity'] = best_sim
                    return result
            else:
                entry = self.redis.get(best_match)
                if entry:
                    entry['cache_hit'] = True
                    entry['similarity'] = best_sim
                    return entry
        
        return None
    
    def set(self, query: str, result: Dict) -> bool:
        """Cache a query result."""
        key = self._generate_key(query)
        embedding = self._get_embedding(query)
        
        cache_data = {
            "query": query,
            "result": result,
            "embedding": embedding
        }
        
        if self.backend == "redis":
            self.redis.setex(
                f"{self.CACHE_PREFIX}{key}",
                self.ttl,
                json.dumps({"query": query, "result": result})
            )
            self.redis.setex(
                f"{self.EMBED_PREFIX}{key}",
                self.ttl,
                json.dumps(embedding)
            )
            self.redis.sadd(self.INDEX_KEY, key)
        else:
            self.redis.set(key, cache_data)
        
        return True
    
    def invalidate(self, query: str) -> bool:
        key = self._generate_key(query)
        if self.backend == "redis":
            self.redis.delete(f"{self.CACHE_PREFIX}{key}")
            self.redis.delete(f"{self.EMBED_PREFIX}{key}")
            self.redis.srem(self.INDEX_KEY, key)
        else:
            self.redis.delete(key)
        return True
    
    def clear_all(self) -> int:
        if self.backend == "redis":
            index = self.redis.smembers(self.INDEX_KEY) or set()
            for key in index:
                if isinstance(key, bytes):
                    key = key.decode()
                self.redis.delete(f"{self.CACHE_PREFIX}{key}")
                self.redis.delete(f"{self.EMBED_PREFIX}{key}")
            self.redis.delete(self.INDEX_KEY)
            return len(index)
        else:
            count = len(self.redis.cache)
            self.redis.clear()
            return count
    
    def get_stats(self) -> Dict:
        if self.backend == "redis":
            index = self.redis.smembers(self.INDEX_KEY) or set()
            count = len(index)
        else:
            count = len(self.redis.cache)
        
        return {
            "cached_queries": count,
            "backend": self.backend,
            "threshold": self.similarity_threshold
        }


_cache_instance = None

def get_cache() -> SemanticCache:
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = SemanticCache()
    return _cache_instance
```

### 10.2 Phase 6 Verification Checklist

- [ ] redis_cache.py created
- [ ] Cache set/get works
- [ ] Semantic similarity matching works
- [ ] Falls back to in-memory when Redis unavailable

---

## 11. PHASE 7: DOCUMENT PROCESSING (Docling)

### 11.1 File: `Engine8_Knowledge/scripts/docling_processor.py`

```python
"""
Docling Document Processor - 30x faster PDF processing
Repository: https://github.com/docling-project/docling (10,000+ stars)
"""

import os
import re
from typing import Dict, List, Optional
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from docling.document_converter import DocumentConverter
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False
    logger.warning("Docling not available, using basic processing")


class DoclingProcessor:
    """
    High-performance document processor.
    Extracts text, tables, and federal metadata from PDFs.
    """
    
    def __init__(self, output_dir: str = None):
        self.output_dir = output_dir or "./docling_output"
        os.makedirs(self.output_dir, exist_ok=True)
        
        if DOCLING_AVAILABLE:
            self.converter = DocumentConverter()
            self.backend = "docling"
        else:
            self.converter = None
            self.backend = "basic"
    
    def process_pdf(self, pdf_path: str) -> Dict:
        """Process a PDF document."""
        if self.backend == "docling":
            result = self.converter.convert(pdf_path)
            doc = result.document
            
            return {
                "filename": os.path.basename(pdf_path),
                "text": doc.export_to_markdown(),
                "pages": len(doc.pages) if hasattr(doc, 'pages') else 0,
                "tables": self._extract_tables(doc),
                "metadata": self.extract_federal_metadata({"text": doc.export_to_markdown()})
            }
        else:
            # Basic fallback using pypdf
            try:
                from pypdf import PdfReader
                reader = PdfReader(pdf_path)
                text = "\n".join(page.extract_text() or "" for page in reader.pages)
                return {
                    "filename": os.path.basename(pdf_path),
                    "text": text,
                    "pages": len(reader.pages),
                    "tables": [],
                    "metadata": self.extract_federal_metadata({"text": text})
                }
            except:
                return {"filename": os.path.basename(pdf_path), "text": "", "error": "Could not process"}
    
    def _extract_tables(self, doc) -> List[Dict]:
        tables = []
        if hasattr(doc, 'tables'):
            for i, table in enumerate(doc.tables):
                tables.append({"id": i, "data": str(table)})
        return tables
    
    def process_directory(self, directory: str, extensions: List[str] = [".pdf"]) -> List[Dict]:
        """Process all documents in directory."""
        results = []
        path = Path(directory)
        
        for ext in extensions:
            for file_path in path.glob(f"**/*{ext}"):
                try:
                    result = self.process_pdf(str(file_path))
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")
        
        return results
    
    def extract_federal_metadata(self, doc: Dict) -> Dict:
        """Extract federal-specific metadata."""
        text = doc.get("text", "")
        
        return {
            "contract_numbers": re.findall(
                r'[A-Z]{1,2}\d{2}[A-Z]{3,4}-?\d{2}-[A-Z]-\d{4}', text
            ),
            "solicitation_numbers": re.findall(
                r'[A-Z0-9]{2,4}-\d{2}-[A-Z]-\d{4,6}', text
            ),
            "cage_codes": re.findall(r'\b[0-9A-Z]{5}\b', text)[:10],
            "naics_codes": re.findall(r'\b\d{6}\b', text)[:5]
        }


_docling_instance = None

def get_docling() -> DoclingProcessor:
    global _docling_instance
    if _docling_instance is None:
        _docling_instance = DoclingProcessor()
    return _docling_instance
```

### 11.2 Phase 7 Verification Checklist

- [ ] docling_processor.py created
- [ ] Can process PDF files
- [ ] Federal metadata extraction works
- [ ] Falls back when Docling unavailable

---

## 12. PHASE 8: WEB SCRAPING INTEGRATION

### 12.1 File: `Engine8_Knowledge/scripts/web_scrapers.py`

```python
"""
Web Scraping: Firecrawl + Crawl4AI
"""

import os
import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ScrapedContent:
    url: str
    title: str
    content: str
    metadata: Dict
    source: str


class FirecrawlScraper:
    """Firecrawl for JS-rendered sites."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("FIRECRAWL_API_KEY")
        self.app = None
        
        if self.api_key:
            try:
                from firecrawl import FirecrawlApp
                self.app = FirecrawlApp(api_key=self.api_key)
            except:
                pass
    
    def scrape_url(self, url: str) -> Optional[ScrapedContent]:
        if not self.app:
            return None
        
        try:
            result = self.app.scrape_url(url, params={"formats": ["markdown"]})
            return ScrapedContent(
                url=url,
                title=result.get("metadata", {}).get("title", ""),
                content=result.get("markdown", ""),
                metadata=result.get("metadata", {}),
                source="firecrawl"
            )
        except Exception as e:
            logger.error(f"Firecrawl error: {e}")
            return None


class Crawl4AIScraper:
    """Crawl4AI for LLM-optimized extraction."""
    
    async def scrape_url(self, url: str) -> Optional[ScrapedContent]:
        try:
            from crawl4ai import AsyncWebCrawler
            
            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(url=url)
                return ScrapedContent(
                    url=url,
                    title=result.metadata.get("title", "") if result.metadata else "",
                    content=result.markdown or "",
                    metadata=result.metadata or {},
                    source="crawl4ai"
                )
        except Exception as e:
            logger.error(f"Crawl4AI error: {e}")
            return None


class UnifiedWebScraper:
    """Unified scraper using best method per URL."""
    
    def __init__(self):
        self.firecrawl = FirecrawlScraper()
        self.crawl4ai = Crawl4AIScraper()
        
        self.js_domains = ["linkedin.com", "sam.gov", "usajobs.gov"]
    
    def _needs_js(self, url: str) -> bool:
        return any(d in url for d in self.js_domains)
    
    async def scrape(self, url: str) -> Optional[ScrapedContent]:
        if self._needs_js(url) and self.firecrawl.app:
            return self.firecrawl.scrape_url(url)
        return await self.crawl4ai.scrape_url(url)
    
    async def scrape_multiple(self, urls: List[str]) -> List[ScrapedContent]:
        results = []
        for url in urls:
            content = await self.scrape(url)
            if content:
                results.append(content)
        return results


_scraper_instance = None

def get_web_scraper() -> UnifiedWebScraper:
    global _scraper_instance
    if _scraper_instance is None:
        _scraper_instance = UnifiedWebScraper()
    return _scraper_instance
```

### 12.2 Phase 8 Verification Checklist

- [ ] web_scrapers.py created
- [ ] Firecrawl works (if API key set)
- [ ] Crawl4AI works for static sites
- [ ] Unified scraper routes correctly

---

## 13. PHASE 9: SPECIALIZED BD AGENTS

### 13.1 File: `Engine8_Knowledge/agents/base_agent.py`

```python
"""
Base Agent Class for BD Intelligence Hub
"""

import os
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import anthropic

import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from scripts.memory_layer import get_memory
from scripts.lightrag_engine import get_knowledge_graph
from scripts.hybrid_retriever import get_hybrid_retriever


@dataclass
class AgentResponse:
    success: bool
    content: str
    sources: List[Dict]
    confidence: float
    agent_name: str
    metadata: Dict[str, Any]


class BDAgent(ABC):
    """Base class for BD specialized agents."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        
        self.memory = get_memory()
        self.graph = get_knowledge_graph()
        self.retriever = get_hybrid_retriever()
        
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self) -> str:
        return f"""You are {self.name}, a specialized BD intelligence agent.

Role: {self.description}

You have access to:
- Federal program data (DCGS portfolio, DoD contracts)
- Company intelligence (prime contractors, teaming partners)
- Contact information (cleared personnel, decision makers)
- Historical BD interactions and insights

Guidelines:
1. Always cite sources
2. Provide actionable intelligence
3. Flag uncertainty
4. Consider clearance requirements
5. Focus on DCGS, IC, DoD opportunities"""
    
    @abstractmethod
    async def process(self, query: str, context: Optional[Dict] = None) -> AgentResponse:
        pass
    
    async def _call_claude(self, prompt: str, context: str = "", max_tokens: int = 2000) -> str:
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=max_tokens,
            system=self.system_prompt,
            messages=[{"role": "user", "content": f"{context}\n\n{prompt}" if context else prompt}]
        )
        return response.content[0].text
    
    async def _get_context(self, query: str, collections: List[str] = None) -> str:
        collections = collections or ["programs", "contacts", "companies"]
        parts = []
        
        # Memory context
        memories = self.memory.get_context(query, limit=5)
        if memories:
            parts.append("## Past Context")
            for m in memories:
                parts.append(f"- {m.get('memory', '')[:200]}")
        
        # Retrieved docs
        for col in collections:
            try:
                results = self.retriever.search(query, col, limit=3)
                if results:
                    parts.append(f"\n## From {col.title()}")
                    for r in results:
                        parts.append(f"- {r.text[:200]}...")
            except:
                pass
        
        return "\n".join(parts)
    
    def _store_interaction(self, query: str, response: AgentResponse):
        self.memory.add_interaction(
            f"[{self.name}] Q: {query[:100]}\nA: {response.content[:300]}",
            metadata={"agent": self.name, "success": response.success}
        )
```

### 13.2 File: `Engine8_Knowledge/agents/program_intel_agent.py`

```python
"""Program Intelligence Agent"""

from typing import Dict, Optional
from base_agent import BDAgent, AgentResponse


class ProgramIntelAgent(BDAgent):
    """Analyzes federal programs and contract opportunities."""
    
    def __init__(self):
        super().__init__(
            name="Program Intelligence Agent",
            description="Analyze federal programs, contracts, and opportunities. "
                       "Expert in DCGS portfolio, IC programs, DoD contracts."
        )
    
    async def process(self, query: str, context: Optional[Dict] = None) -> AgentResponse:
        ctx = await self._get_context(query, ["programs", "contracts"])
        
        # Get graph insights
        try:
            graph_result = await self.graph.query(
                f"Program relationships: {query}", mode="hybrid"
            )
            ctx += f"\n\n## Graph Insights\n{graph_result}"
        except:
            pass
        
        prompt = f"""Analyze this program intelligence request:

Query: {query}

Provide:
1. Program Overview
2. Contract Structure (prime/sub, vehicles, values)
3. Opportunity Assessment
4. Incumbent Analysis
5. Recommended Actions"""
        
        response_text = await self._call_claude(prompt, ctx)
        
        response = AgentResponse(
            success=True, content=response_text,
            sources=[{"context": ctx[:500]}],
            confidence=0.85, agent_name=self.name,
            metadata={"query": query}
        )
        self._store_interaction(query, response)
        return response
    
    async def analyze_program(self, program_name: str) -> AgentResponse:
        return await self.process(f"Comprehensive analysis of {program_name}")
    
    async def find_recompetes(self, months: int = 12) -> AgentResponse:
        return await self.process(f"Find recompetes in next {months} months for DCGS/IC")
```

### 13.3 File: `Engine8_Knowledge/agents/company_research_agent.py`

```python
"""Company Research Agent"""

from typing import Dict, List, Optional
from base_agent import BDAgent, AgentResponse


class CompanyResearchAgent(BDAgent):
    """Researches competitors and teaming partners."""
    
    def __init__(self):
        super().__init__(
            name="Company Research Agent",
            description="Research federal contractors. Expert in prime/sub relationships, "
                       "capabilities, teaming history, competitive positioning."
        )
    
    async def process(self, query: str, context: Optional[Dict] = None) -> AgentResponse:
        ctx = await self._get_context(query, ["companies", "contracts"])
        
        try:
            network = await self.graph.query(
                f"Company network: {query}", mode="global"
            )
            ctx += f"\n\n## Network Analysis\n{network}"
        except:
            pass
        
        prompt = f"""Company research request:

Query: {query}

Provide:
1. Company Profile
2. Contract Portfolio
3. Competitive Position
4. Teaming History
5. BD Implications"""
        
        response_text = await self._call_claude(prompt, ctx)
        
        response = AgentResponse(
            success=True, content=response_text,
            sources=[{"context": ctx[:500]}],
            confidence=0.82, agent_name=self.name,
            metadata={"query": query}
        )
        self._store_interaction(query, response)
        return response
    
    async def analyze_competitor(self, company: str) -> AgentResponse:
        return await self.process(f"Competitor analysis of {company}")
    
    async def find_teaming_partners(self, gaps: List[str]) -> AgentResponse:
        return await self.process(f"Find partners for capabilities: {', '.join(gaps)}")
```

### 13.4 File: `Engine8_Knowledge/agents/contact_finder_agent.py`

```python
"""Contact Finder Agent"""

from typing import Dict, Optional
from base_agent import BDAgent, AgentResponse


class ContactFinderAgent(BDAgent):
    """Identifies key personnel and decision makers."""
    
    def __init__(self):
        super().__init__(
            name="Contact Finder Agent",
            description="Identify key personnel for BD opportunities. "
                       "Expert in org structures, clearance levels, decision makers."
        )
    
    async def process(self, query: str, context: Optional[Dict] = None) -> AgentResponse:
        ctx = await self._get_context(query, ["contacts", "companies", "programs"])
        
        prompt = f"""Contact finder request:

Query: {query}

Provide:
1. Relevant Contacts
2. Their Roles/Titles
3. Program Affiliations
4. Clearance Levels (if known)
5. Outreach Recommendations"""
        
        response_text = await self._call_claude(prompt, ctx)
        
        response = AgentResponse(
            success=True, content=response_text,
            sources=[{"context": ctx[:500]}],
            confidence=0.80, agent_name=self.name,
            metadata={"query": query}
        )
        self._store_interaction(query, response)
        return response
    
    async def find_decision_makers(self, program: str) -> AgentResponse:
        return await self.process(f"Decision makers for {program}")
    
    async def find_by_clearance(self, clearance: str, location: str = None) -> AgentResponse:
        q = f"Contacts with {clearance} clearance"
        if location:
            q += f" in {location}"
        return await self.process(q)
```

### 13.5 File: `Engine8_Knowledge/agents/bd_strategy_agent.py`

```python
"""BD Strategy Agent"""

from typing import Dict, Optional
from base_agent import BDAgent, AgentResponse


class BDStrategyAgent(BDAgent):
    """Synthesizes intelligence into BD strategy."""
    
    def __init__(self):
        super().__init__(
            name="BD Strategy Agent",
            description="Develop winning BD strategies. Expert at synthesizing "
                       "intelligence into actionable capture plans."
        )
    
    async def process(self, query: str, context: Optional[Dict] = None) -> AgentResponse:
        ctx = await self._get_context(query, ["programs", "companies", "contacts"])
        
        # Get comprehensive graph analysis
        try:
            analysis = await self.graph.query(
                f"Strategic analysis: {query}", mode="hybrid"
            )
            ctx += f"\n\n## Strategic Analysis\n{analysis}"
        except:
            pass
        
        prompt = f"""BD strategy request:

Query: {query}

Develop strategy with:
1. Opportunity Assessment (win probability)
2. Key Win Themes
3. Teaming Strategy
4. Competitive Differentiation
5. 90-Day Action Plan
6. Risk Mitigation"""
        
        response_text = await self._call_claude(prompt, ctx)
        
        response = AgentResponse(
            success=True, content=response_text,
            sources=[{"context": ctx[:500]}],
            confidence=0.85, agent_name=self.name,
            metadata={"query": query}
        )
        self._store_interaction(query, response)
        return response
    
    async def create_capture_plan(self, opportunity: str) -> AgentResponse:
        return await self.process(f"Create capture plan for {opportunity}")
    
    async def assess_win_probability(self, opportunity: str) -> AgentResponse:
        return await self.process(f"Assess win probability for {opportunity}")
```

### 13.6 Phase 9 Verification Checklist

- [ ] base_agent.py created
- [ ] program_intel_agent.py created
- [ ] company_research_agent.py created
- [ ] contact_finder_agent.py created
- [ ] bd_strategy_agent.py created
- [ ] Agents can be instantiated
- [ ] Agents call Claude API successfully
- [ ] Memory stores agent interactions

king."""
    results = retriever.search(q, collection, limit, True, use_rerank)
    return {"results": [{"id": r.id, "text": r.text, "score": r.score, "source": r.source} for r in results]}


# ==================== GRAPH ENDPOINTS ====================

@app.get("/graph/query")
async def query_graph(
    q: str,
    mode: str = Query("hybrid", regex="^(naive|local|global|hybrid)$")
):
    """Query knowledge graph."""
    result = await graph.query(q, mode)
    return {"query": q, "mode": mode, "result": result}

@app.get("/graph/relationships")
async def get_relationships(entity: str):
    """Get relationships for entity."""
    result = await graph.find_relationships(entity)
    return result

@app.get("/graph/network")
async def analyze_network(company: str):
    """Analyze company network."""
    result = await graph.analyze_network(company)
    return {"company": company, "analysis": result}


# ==================== MEMORY ENDPOINTS ====================

@app.post("/memory/add")
async def add_memory(data: MemoryInput):
    """Add memory."""
    result = memory.add_interaction(data.content, data.metadata)
    return {"success": True, "result": result}

@app.post("/memory/entity")
async def add_entity_fact(
    entity_name: str,
    entity_type: str,
    fact: str
):
    """Add entity fact."""
    result = memory.add_entity_fact(entity_name, entity_type, fact)
    return {"success": True, "result": result}

@app.post("/memory/insight")
async def add_insight(data: InsightInput):
    """Add BD insight."""
    result = memory.add_bd_insight(data.insight_type, data.insight, data.source, data.confidence)
    return {"success": True, "result": result}

@app.get("/memory/search")
async def search_memory(q: str, limit: int = 10):
    """Search memories."""
    results = memory.get_context(q, limit)
    return {"results": results}

@app.get("/memory/entity/{entity_name}")
async def get_entity_facts(entity_name: str, limit: int = 20):
    """Get facts about entity."""
    results = memory.get_entity_facts(entity_name, limit)
    return {"entity": entity_name, "facts": results}

@app.get("/memory/insights")
async def get_insights(insight_type: str = None, limit: int = 10):
    """Get BD insights."""
    results = memory.get_recent_insights(insight_type, limit)
    return {"insights": results}


# ==================== INGEST ENDPOINTS ====================

@app.post("/ingest/document")
async def ingest_document(data: DocumentInput):
    """Ingest document to Qdrant and graph."""
    # Add to graph for entity extraction
    await graph.insert_document(data.text)
    # Store summary in memory
    memory.add_interaction(f"Ingested document: {data.text[:200]}...")
    return {"success": True, "message": "Document ingested"}

@app.post("/ingest/program")
async def ingest_program(data: ProgramInput):
    """Ingest program."""
    await graph.insert_program(data.dict())
    memory.add_entity_fact(data.name, "program", f"Value: {data.value}, Clearance: {data.clearance}")
    return {"success": True, "program": data.name}

@app.post("/ingest/company")
async def ingest_company(data: CompanyInput):
    """Ingest company."""
    await graph.insert_company(data.dict())
    memory.add_entity_fact(data.name, "company", f"Type: {data.type}, Programs: {len(data.programs)}")
    return {"success": True, "company": data.name}

@app.post("/ingest/contact")
async def ingest_contact(data: ContactInput):
    """Ingest contact."""
    await graph.insert_contact(data.dict())
    memory.add_entity_fact(data.name, "contact", f"Company: {data.company}, Title: {data.title}")
    return {"success": True, "contact": data.name}

@app.post("/ingest/jobs")
async def ingest_jobs(jobs: List[JobInput]):
    """Ingest multiple jobs (for Data-Scraper)."""
    count = 0
    for job in jobs:
        await graph.insert_document(
            f"JOB: {job.title} at {job.company}\n"
            f"Location: {job.location}\n"
            f"Clearance: {job.clearance}\n"
            f"Description: {job.description}"
        )
        count += 1
    memory.add_scrape_result("jobs", f"Ingested {count} jobs", count)
    return {"success": True, "count": count}


# ==================== AGENT ENDPOINTS ====================

@app.get("/agent/program")
async def agent_program_intel(q: str):
    """Program intelligence agent."""
    result = await program_agent.process(q)
    return {"agent": result.agent_name, "response": result.content, "confidence": result.confidence}

@app.get("/agent/company")
async def agent_company_research(q: str):
    """Company research agent."""
    result = await company_agent.process(q)
    return {"agent": result.agent_name, "response": result.content, "confidence": result.confidence}

@app.get("/agent/contact")
async def agent_contact_finder(q: str):
    """Contact finder agent."""
    result = await contact_agent.process(q)
    return {"agent": result.agent_name, "response": result.content, "confidence": result.confidence}

@app.get("/agent/strategy")
async def agent_bd_strategy(q: str):
    """BD strategy agent."""
    result = await strategy_agent.process(q)
    return {"agent": result.agent_name, "response": result.content, "confidence": result.confidence}


# ==================== PAGEINDEX ENDPOINTS ====================

@app.post("/pageindex/index")
async def index_for_audit(doc_id: str, content: str):
    """Index document for audit trail."""
    success = pageindex.index_document(doc_id, content)
    return {"success": success, "doc_id": doc_id}

@app.get("/pageindex/query")
async def query_with_audit(q: str, doc_ids: str = None):
    """Query with audit trail."""
    docs = doc_ids.split(",") if doc_ids else None
    result = pageindex.query(q, docs)
    trail = pageindex.get_audit_trail(result)
    return {"answer": result.final_answer, "confidence": result.confidence, "audit_trail": trail}


# ==================== CACHE ENDPOINTS ====================

@app.get("/cache/stats")
async def cache_stats():
    """Get cache statistics."""
    return cache.get_stats()

@app.delete("/cache/clear")
async def clear_cache():
    """Clear all cache."""
    count = cache.clear_all()
    return {"cleared": count}


# ==================== RUN SERVER ====================

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8100)
```

### 15.2 Phase 11 Verification Checklist

- [ ] Enhanced api.py created
- [ ] All endpoints respond correctly
- [ ] /ask/smart routes queries properly
- [ ] /ingest/* endpoints work
- [ ] /agent/* endpoints call agents
- [ ] /memory/* endpoints work
- [ ] /graph/* endpoints work

---

## 16. PHASE 12: ENHANCED MCP SERVER

### 16.1 File: `mcp/knowledge-mcp-server/src/index.ts` (Enhanced)

```typescript
#!/usr/bin/env node

/**
 * Enhanced MCP Server for BD Intelligence Hub
 * 40+ tools for comprehensive BD operations
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

const API_URL = process.env.KNOWLEDGE_API_URL || "http://127.0.0.1:8100";

// Helper to call API
async function callAPI(endpoint: string, method: string = "GET", body?: any) {
  const options: RequestInit = {
    method,
    headers: { "Content-Type": "application/json" },
  };
  if (body) options.body = JSON.stringify(body);
  
  const response = await fetch(`${API_URL}${endpoint}`, options);
  return response.json();
}

// Create server
const server = new Server(
  { name: "bd-intelligence-hub", version: "2.0.0" },
  { capabilities: { tools: {} } }
);

// Tool definitions
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    // ==================== SMART QUERY ====================
    {
      name: "smart_ask",
      description: "Intelligent query that routes to optimal system(s). Use for any BD question.",
      inputSchema: {
        type: "object",
        properties: {
          query: { type: "string", description: "Your BD question" },
          use_cache: { type: "boolean", default: true }
        },
        required: ["query"]
      }
    },
    
    // ==================== SEARCH TOOLS ====================
    {
      name: "semantic_search",
      description: "Search using semantic similarity",
      inputSchema: {
        type: "object",
        properties: {
          query: { type: "string" },
          collection: { type: "string", default: "bd_knowledge" },
          limit: { type: "number", default: 10 }
        },
        required: ["query"]
      }
    },
    {
      name: "keyword_search",
      description: "Search using exact keyword matching (BM25)",
      inputSchema: {
        type: "object",
        properties: {
          query: { type: "string" },
          collection: { type: "string", default: "bd_knowledge" },
          limit: { type: "number", default: 10 }
        },
        required: ["query"]
      }
    },
    {
      name: "hybrid_search",
      description: "Combined semantic + keyword search with reranking",
      inputSchema: {
        type: "object",
        properties: {
          query: { type: "string" },
          collection: { type: "string", default: "bd_knowledge" },
          limit: { type: "number", default: 10 },
          use_rerank: { type: "boolean", default: true }
        },
        required: ["query"]
      }
    },
    
    // ==================== GRAPH TOOLS ====================
    {
      name: "query_knowledge_graph",
      description: "Query entity relationships and networks",
      inputSchema: {
        type: "object",
        properties: {
          query: { type: "string" },
          mode: { type: "string", enum: ["local", "global", "hybrid"], default: "hybrid" }
        },
        required: ["query"]
      }
    },
    {
      name: "find_relationships",
      description: "Find all relationships for a company/program/contact",
      inputSchema: {
        type: "object",
        properties: {
          entity: { type: "string", description: "Entity name" }
        },
        required: ["entity"]
      }
    },
    {
      name: "analyze_network",
      description: "Analyze a company's partner/competitor network",
      inputSchema: {
        type: "object",
        properties: {
          company: { type: "string" }
        },
        required: ["company"]
      }
    },
    
    // ==================== MEMORY TOOLS ====================
    {
      name: "memory_add",
      description: "Add information to memory for future reference",
      inputSchema: {
        type: "object",
        properties: {
          content: { type: "string" },
          memory_type: { type: "string", default: "interaction" }
        },
        required: ["content"]
      }
    },
    {
      name: "memory_add_entity",
      description: "Add a fact about a company/program/contact",
      inputSchema: {
        type: "object",
        properties: {
          entity_name: { type: "string" },
          entity_type: { type: "string", enum: ["company", "program", "contact", "contract"] },
          fact: { type: "string" }
        },
        required: ["entity_name", "entity_type", "fact"]
      }
    },
    {
      name: "memory_add_insight",
      description: "Add a BD insight (opportunity, risk, relationship)",
      inputSchema: {
        type: "object",
        properties: {
          insight_type: { type: "string", enum: ["opportunity", "risk", "relationship", "strategy"] },
          insight: { type: "string" },
          source: { type: "string", default: "user" },
          confidence: { type: "number", default: 0.8 }
        },
        required: ["insight_type", "insight"]
      }
    },
    {
      name: "memory_search",
      description: "Search past memories and interactions",
      inputSchema: {
        type: "object",
        properties: {
          query: { type: "string" },
          limit: { type: "number", default: 10 }
        },
        required: ["query"]
      }
    },
    {
      name: "memory_get_entity",
      description: "Get all facts about a specific entity",
      inputSchema: {
        type: "object",
        properties: {
          entity_name: { type: "string" }
        },
        required: ["entity_name"]
      }
    },
    {
      name: "memory_get_insights",
      description: "Get BD insights",
      inputSchema: {
        type: "object",
        properties: {
          insight_type: { type: "string" },
          limit: { type: "number", default: 10 }
        }
      }
    },
    
    // ==================== INGEST TOOLS ====================
    {
      name: "ingest_program",
      description: "Add a federal program to the knowledge base",
      inputSchema: {
        type: "object",
        properties: {
          name: { type: "string" },
          description: { type: "string" },
          agency: { type: "string" },
          primes: { type: "array", items: { type: "string" } },
          value: { type: "string" },
          clearance: { type: "string" },
          technologies: { type: "array", items: { type: "string" } }
        },
        required: ["name"]
      }
    },
    {
      name: "ingest_company",
      description: "Add a company to the knowledge base",
      inputSchema: {
        type: "object",
        properties: {
          name: { type: "string" },
          type: { type: "string" },
          capabilities: { type: "array", items: { type: "string" } },
          programs: { type: "array", items: { type: "string" } },
          partners: { type: "array", items: { type: "string" } }
        },
        required: ["name"]
      }
    },
    {
      name: "ingest_contact",
      description: "Add a contact to the knowledge base",
      inputSchema: {
        type: "object",
        properties: {
          name: { type: "string" },
          company: { type: "string" },
          title: { type: "string" },
          programs: { type: "array", items: { type: "string" } },
          clearance: { type: "string" }
        },
        required: ["name"]
      }
    },
    
    // ==================== AGENT TOOLS ====================
    {
      name: "agent_program_intel",
      description: "Use Program Intelligence Agent for program analysis",
      inputSchema: {
        type: "object",
        properties: {
          query: { type: "string" }
        },
        required: ["query"]
      }
    },
    {
      name: "agent_company_research",
      description: "Use Company Research Agent for competitor/partner analysis",
      inputSchema: {
        type: "object",
        properties: {
          query: { type: "string" }
        },
        required: ["query"]
      }
    },
    {
      name: "agent_contact_finder",
      description: "Use Contact Finder Agent to identify key personnel",
      inputSchema: {
        type: "object",
        properties: {
          query: { type: "string" }
        },
        required: ["query"]
      }
    },
    {
      name: "agent_bd_strategy",
      description: "Use BD Strategy Agent for strategy development",
      inputSchema: {
        type: "object",
        properties: {
          query: { type: "string" }
        },
        required: ["query"]
      }
    },
    
    // ==================== PAGEINDEX TOOLS ====================
    {
      name: "index_document_audit",
      description: "Index document for audit trail queries",
      inputSchema: {
        type: "object",
        properties: {
          doc_id: { type: "string" },
          content: { type: "string" }
        },
        required: ["doc_id", "content"]
      }
    },
    {
      name: "query_with_audit",
      description: "Query with audit trail for compliance",
      inputSchema: {
        type: "object",
        properties: {
          query: { type: "string" },
          doc_ids: { type: "string", description: "Comma-separated doc IDs" }
        },
        required: ["query"]
      }
    },
    
    // ==================== SYSTEM TOOLS ====================
    {
      name: "get_system_stats",
      description: "Get system statistics",
      inputSchema: { type: "object", properties: {} }
    },
    {
      name: "get_cache_stats",
      description: "Get cache statistics",
      inputSchema: { type: "object", properties: {} }
    },
    {
      name: "clear_cache",
      description: "Clear query cache",
      inputSchema: { type: "object", properties: {} }
    }
  ]
}));

// Tool handlers
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  
  try {
    let result;
    
    switch (name) {
      // Smart Query
      case "smart_ask":
        result = await callAPI(`/ask/smart?q=${encodeURIComponent(args.query)}&use_cache=${args.use_cache ?? true}`);
        break;
      
      // Search
      case "semantic_search":
        result = await callAPI(`/search/semantic?q=${encodeURIComponent(args.query)}&collection=${args.collection || 'bd_knowledge'}&limit=${args.limit || 10}`);
        break;
      case "keyword_search":
        result = await callAPI(`/search/keyword?q=${encodeURIComponent(args.query)}&collection=${args.collection || 'bd_knowledge'}&limit=${args.limit || 10}`);
        break;
      case "hybrid_search":
        result = await callAPI(`/search/hybrid?q=${encodeURIComponent(args.query)}&collection=${args.collection || 'bd_knowledge'}&limit=${args.limit || 10}&use_rerank=${args.use_rerank ?? true}`);
        break;
      
      // Graph
      case "query_knowledge_graph":
        result = await callAPI(`/graph/query?q=${encodeURIComponent(args.query)}&mode=${args.mode || 'hybrid'}`);
        break;
      case "find_relationships":
        result = await callAPI(`/graph/relationships?entity=${encodeURIComponent(args.entity)}`);
        break;
      case "analyze_network":
        result = await callAPI(`/graph/network?company=${encodeURIComponent(args.company)}`);
        break;
      
      // Memory
      case "memory_add":
        result = await callAPI("/memory/add", "POST", { content: args.content, memory_type: args.memory_type });
        break;
      case "memory_add_entity":
        result = await callAPI(`/memory/entity?entity_name=${encodeURIComponent(args.entity_name)}&entity_type=${args.entity_type}&fact=${encodeURIComponent(args.fact)}`, "POST");
        break;
      case "memory_add_insight":
        result = await callAPI("/memory/insight", "POST", args);
        break;
      case "memory_search":
        result = await callAPI(`/memory/search?q=${encodeURIComponent(args.query)}&limit=${args.limit || 10}`);
        break;
      case "memory_get_entity":
        result = await callAPI(`/memory/entity/${encodeURIComponent(args.entity_name)}`);
        break;
      case "memory_get_insights":
        result = await callAPI(`/memory/insights?${args.insight_type ? `insight_type=${args.insight_type}&` : ''}limit=${args.limit || 10}`);
        break;
      
      // Ingest
      case "ingest_program":
        result = await callAPI("/ingest/program", "POST", args);
        break;
      case "ingest_company":
        result = await callAPI("/ingest/company", "POST", args);
        break;
      case "ingest_contact":
        result = await callAPI("/ingest/contact", "POST", args);
        break;
      
      // Agents
      case "agent_program_intel":
        result = await callAPI(`/agent/program?q=${encodeURIComponent(args.query)}`);
        break;
      case "agent_company_research":
        result = await callAPI(`/agent/company?q=${encodeURIComponent(args.query)}`);
        break;
      case "agent_contact_finder":
        result = await callAPI(`/agent/contact?q=${encodeURIComponent(args.query)}`);
        break;
      case "agent_bd_strategy":
        result = await callAPI(`/agent/strategy?q=${encodeURIComponent(args.query)}`);
        break;
      
      // PageIndex
      case "index_document_audit":
        result = await callAPI(`/pageindex/index?doc_id=${encodeURIComponent(args.doc_id)}&content=${encodeURIComponent(args.content)}`, "POST");
        break;
      case "query_with_audit":
        result = await callAPI(`/pageindex/query?q=${encodeURIComponent(args.query)}${args.doc_ids ? `&doc_ids=${args.doc_ids}` : ''}`);
        break;
      
      // System
      case "get_system_stats":
        result = await callAPI("/stats");
        break;
      case "get_cache_stats":
        result = await callAPI("/cache/stats");
        break;
      case "clear_cache":
        result = await callAPI("/cache/clear", "DELETE");
        break;
      
      default:
        throw new Error(`Unknown tool: ${name}`);
    }
    
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
    
  } catch (error) {
    return { content: [{ type: "text", text: `Error: ${error.message}` }], isError: true };
  }
});

// Start server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("BD Intelligence Hub MCP Server running");
}

main().catch(console.error);
```

### 16.2 Rebuild MCP Server

```bash
cd mcp/knowledge-mcp-server
npm run build
```

### 16.3 Phase 12 Verification Checklist

- [ ] Enhanced index.ts created
- [ ] npm run build succeeds
- [ ] All 30+ tools listed
- [ ] Tools call correct API endpoints

---

## 17. PHASE 13: YAML PIPELINES (UltraRAG)

### 17.1 File: `Engine8_Knowledge/pipelines/capture_strategy.yaml`

```yaml
# UltraRAG Pipeline: BD Capture Strategy
name: capture_strategy_pipeline
version: "1.0"
description: Generate comprehensive capture strategy for federal opportunity

stages:
  - name: opportunity_analysis
    type: retrieval
    config:
      source: qdrant
      collection: programs
      top_k: 10
      query_template: "Federal program {program_name} contract details"
    
  - name: competitor_research
    type: retrieval
    config:
      source: lightrag
      mode: hybrid
      query_template: "Competitors on {program_name}"
    
  - name: past_performance
    type: retrieval
    config:
      source: qdrant
      collection: contracts
      query_template: "PTS past performance for {program_name}"
    
  - name: synthesis
    type: llm
    config:
      model: claude-sonnet-4-20250514
      prompt_template: |
        Based on the following intelligence:
        
        ## Opportunity
        {opportunity_analysis}
        
        ## Competitors
        {competitor_research}
        
        ## Past Performance
        {past_performance}
        
        Generate capture strategy with:
        1. Win probability
        2. Key win themes
        3. Teaming strategy
        4. Price-to-win
        5. 90-day action plan
```

### 17.2 File: `Engine8_Knowledge/pipelines/competitor_analysis.yaml`

```yaml
name: competitor_analysis_pipeline
version: "1.0"
description: Deep competitor analysis

stages:
  - name: company_profile
    type: retrieval
    config:
      source: lightrag
      mode: local
      query_template: "Company profile for {company_name}"
    
  - name: contract_history
    type: retrieval
    config:
      source: qdrant
      collection: contracts
      query_template: "{company_name} contract awards"
    
  - name: teaming_network
    type: retrieval
    config:
      source: lightrag
      mode: global
      query_template: "Teaming network of {company_name}"
    
  - name: analysis
    type: llm
    config:
      model: claude-sonnet-4-20250514
      prompt_template: |
        Analyze competitor {company_name}:
        
        Profile: {company_profile}
        Contracts: {contract_history}
        Network: {teaming_network}
        
        Provide:
        1. Strengths/Weaknesses
        2. Competitive positioning
        3. Vulnerability assessment
        4. Counter-strategy
```

### 17.3 Phase 13 Verification Checklist

- [ ] capture_strategy.yaml created
- [ ] competitor_analysis.yaml created
- [ ] YAML syntax is valid
- [ ] Pipeline stages defined correctly

---

## 18. PHASE 14: EVALUATION FRAMEWORK (RAGAS)

### 18.1 File: `Engine8_Knowledge/evaluation/ragas_evaluator.py`

```python
"""
RAGAS Evaluation Framework
Repository: https://github.com/explodinggradients/ragas (8,000+ stars)
"""

from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from datasets import Dataset
    from ragas import evaluate
    from ragas.metrics import (
        faithfulness,
        answer_relevancy,
        context_precision,
        context_recall,
        answer_correctness
    )
    RAGAS_AVAILABLE = True
except ImportError:
    RAGAS_AVAILABLE = False
    logger.warning("RAGAS not available")


class RAGASEvaluator:
    """Evaluate RAG pipeline quality."""
    
    def __init__(self):
        if RAGAS_AVAILABLE:
            self.metrics = [
                faithfulness,
                answer_relevancy,
                context_precision,
                context_recall,
                answer_correctness
            ]
        else:
            self.metrics = []
    
    def evaluate_responses(
        self,
        questions: List[str],
        answers: List[str],
        contexts: List[List[str]],
        ground_truths: List[str]
    ) -> Dict:
        """Evaluate RAG responses."""
        if not RAGAS_AVAILABLE:
            return {"error": "RAGAS not available"}
        
        data = {
            "question": questions,
            "answer": answers,
            "contexts": contexts,
            "ground_truth": ground_truths
        }
        dataset = Dataset.from_dict(data)
        
        results = evaluate(dataset, metrics=self.metrics)
        
        return {
            "faithfulness": results.get("faithfulness", 0),
            "answer_relevancy": results.get("answer_relevancy", 0),
            "context_precision": results.get("context_precision", 0),
            "context_recall": results.get("context_recall", 0),
            "answer_correctness": results.get("answer_correctness", 0),
            "overall": sum(results.values()) / len(results) if results else 0
        }
    
    def evaluate_single(
        self,
        question: str,
        answer: str,
        contexts: List[str],
        ground_truth: str
    ) -> Dict:
        """Evaluate single response."""
        return self.evaluate_responses(
            [question], [answer], [contexts], [ground_truth]
        )


def get_evaluator() -> RAGASEvaluator:
    return RAGASEvaluator()
```

### 18.2 File: `Engine8_Knowledge/evaluation/test_cases.json`

```json
{
  "test_cases": [
    {
      "question": "Who are the prime contractors on DCGS-A?",
      "ground_truth": "Leidos and General Dynamics are the primary prime contractors on DCGS-A.",
      "expected_entities": ["Leidos", "General Dynamics", "DCGS-A"]
    },
    {
      "question": "What is the contract value of DCGS-A?",
      "ground_truth": "DCGS-A is valued at approximately $950 million.",
      "expected_entities": ["DCGS-A", "$950M"]
    },
    {
      "question": "What clearance is required for DCGS programs?",
      "ground_truth": "DCGS programs typically require TS/SCI clearance.",
      "expected_entities": ["DCGS", "TS/SCI"]
    }
  ]
}
```

### 18.3 File: `Engine8_Knowledge/evaluation/run_evaluation.py`

```python
"""Run RAGAS evaluation on the BD Intelligence Hub."""

import json
import asyncio
from ragas_evaluator import get_evaluator

import sys
sys.path.append("..")
from scripts.query_router import QueryRouter


async def run_evaluation():
    evaluator = get_evaluator()
    router = QueryRouter()
    
    # Load test cases
    with open("test_cases.json") as f:
        test_data = json.load(f)
    
    results = []
    
    for tc in test_data["test_cases"]:
        # Get system response
        response = await router.smart_query(tc["question"])
        
        # Evaluate
        eval_result = evaluator.evaluate_single(
            question=tc["question"],
            answer=response.answer,
            contexts=[s.get("text", "") for s in response.sources[:3]],
            ground_truth=tc["ground_truth"]
        )
        
        results.append({
            "question": tc["question"],
            "system_answer": response.answer[:200],
            "metrics": eval_result
        })
        
        print(f"\nQ: {tc['question']}")
        print(f"Score: {eval_result.get('overall', 0):.2f}")
    
    # Average scores
    if results:
        avg_score = sum(r["metrics"].get("overall", 0) for r in results) / len(results)
        print(f"\n\nOverall Average: {avg_score:.2f}")
    
    return results


if __name__ == "__main__":
    asyncio.run(run_evaluation())
```

### 18.4 Phase 14 Verification Checklist

- [ ] ragas_evaluator.py created
- [ ] test_cases.json created
- [ ] run_evaluation.py created
- [ ] Evaluation runs without errors
- [ ] Metrics are reasonable (>0.5)

---

## 19. PHASE 15-18: REMAINING PHASES

### 19.1 Phase 15: External Platform Integration

Create integrations for:
- RAGFlow: `Engine8_Knowledge/integrations/ragflow_client.py`
- MindsDB: `Engine8_Knowledge/integrations/mindsdb_client.py`
- External APIs: `Engine8_Knowledge/integrations/external_apis.py`

### 19.2 Phase 16: Data Migration & Sync

1. Sync existing Qdrant data to LightRAG graph
2. Import Data-Scraper knowledge to Hub
3. Create sync utilities

### 19.3 Phase 17: Testing & Validation

1. Unit tests for each component
2. Integration tests for API
3. End-to-end tests for workflows

### 19.4 Phase 18: Deployment & Operations

1. Update CLAUDE.md with new capabilities
2. Update .claude/settings.local.json with MCP config
3. Create startup scripts
4. Document operational procedures

---

## 20. IMPLEMENTATION ORDER SUMMARY

### Quick Start (Copy to Project)

```bash
# 1. Navigate to project
cd "C:\Users\gtmar\Projects\Auto-Claude\BD-Automation-Engine"

# 2. Create directories
mkdir -p Engine8_Knowledge/scripts
mkdir -p Engine8_Knowledge/agents
mkdir -p Engine8_Knowledge/pipelines
mkdir -p Engine8_Knowledge/evaluation
mkdir -p Engine8_Knowledge/integrations
mkdir -p Engine8_Knowledge/data/lightrag
mkdir -p Engine8_Knowledge/data/pageindex
mkdir -p Engine8_Knowledge/data/memory

# 3. Install dependencies
pip install mem0ai lightrag-hku rank-bm25 redis docling firecrawl-py crawl4ai crewai ragas

# 4. Create files in order:
# - scripts/memory_layer.py
# - scripts/lightrag_engine.py
# - scripts/hybrid_retriever.py
# - scripts/query_router.py
# - scripts/pageindex_engine.py
# - scripts/redis_cache.py
# - scripts/docling_processor.py
# - scripts/web_scrapers.py
# - agents/base_agent.py
# - agents/program_intel_agent.py
# - agents/company_research_agent.py
# - agents/contact_finder_agent.py
# - agents/bd_strategy_agent.py
# - agents/crewai_orchestrator.py
# - Enhanced api.py
# - Enhanced mcp/knowledge-mcp-server/src/index.ts

# 5. Start the hub
python Engine8_Knowledge/api.py

# 6. Test
curl "http://localhost:8100/ask/smart?q=Who%20are%20primes%20on%20DCGS"
```

### Claude Code Instructions

**Tell Claude Code:**

"Read BD_AUTOMATION_ENGINE_IMPLEMENTATION_PLAN.md and implement all phases in order. Start with Phase 1 (Memory Layer) and work through Phase 18. Test each phase before moving to the next."

---

## END OF BD-AUTOMATION-ENGINE IMPLEMENTATION PLAN

**Total Files to Create:** ~25
**Total New Endpoints:** 50+
**Total New MCP Tools:** 30+
**Estimated Implementation Time:** 40-60 hours

