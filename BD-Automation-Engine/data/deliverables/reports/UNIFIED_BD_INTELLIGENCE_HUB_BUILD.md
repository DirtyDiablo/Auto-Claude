# UNIFIED BD INTELLIGENCE HUB - Master Build Plan

## 📋 Overview

This is a **MASTER implementation plan** that unifies three separate projects into one cohesive BD Intelligence system. This file contains instructions for **all three projects** with clear section markers.

### Architecture Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                    BD-INTELLIGENCE-HUB                          │
│                  (BD-Automation-Engine)                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Unified Components                                      │   │
│  │  • Qdrant Vector Store (ALL data)                       │   │
│  │  • Mem0 Memory Layer (user="pts_bd_unified")            │   │
│  │  • LightRAG Knowledge Graph                             │   │
│  │  • Query Router (intelligent routing)                   │   │
│  │  • HybridRetriever (semantic + BM25 + RRF)             │   │
│  │  • CrossEncoder Reranker                                │   │
│  │  • 5 Specialized BD Agents                              │   │
│  │  • FastAPI Server (:8100)                               │   │
│  │  • Unified MCP Server (30+ tools)                       │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
            ▲                           ▲
            │ WRITES DATA               │ CALLS TOOLS
            │                           │
┌───────────┴───────────┐   ┌──────────┴────────────┐
│    DATA-SCRAPER       │   │     N8N BUILDER       │
│    (Data Writer)      │   │    (Orchestrator)     │
│                       │   │                       │
│  • Apify scrapers     │   │  • n8n workflows      │
│  • Job standardization│   │  • Pipeline building  │
│  • Contact extraction │   │  • Automation         │
│  • Program mapping    │   │  • Document processing│
│                       │   │                       │
│  OUTPUTS TO:          │   │  CALLS:               │
│  Hub's Qdrant API     │   │  Hub's MCP tools      │
└───────────────────────┘   └───────────────────────┘
```

### Project Roles

| Project | New Role | What It Does |
|---------|----------|--------------|
| **BD-Automation-Engine** | CENTRAL HUB | Hosts all intelligence infrastructure, serves unified API |
| **Data-Scraper** | DATA WRITER | Scrapes jobs/contacts → writes to Hub's Qdrant via API |
| **N8N Builder** | ORCHESTRATOR | Builds n8n workflows that call Hub's MCP tools |

---

# ═══════════════════════════════════════════════════════════════
# SECTION 1: BD-AUTOMATION-ENGINE (THE HUB)
# Path: C:\Users\gtmar\Projects\Auto-Claude\BD-Automation-Engine
# ═══════════════════════════════════════════════════════════════

## 🎯 Hub Responsibilities

This project becomes the **central brain** that:
1. Stores ALL vector data (jobs, contacts, programs, documents, n8n docs)
2. Maintains unified memory across all sessions
3. Hosts the knowledge graph for entity relationships
4. Provides intelligent query routing
5. Exposes 30+ MCP tools for other projects

## Current State (Already Implemented)

| Component | Status | Details |
|-----------|--------|---------|
| Qdrant Vector DB | ✅ | 8,447 records, 5 collections |
| FastAPI Server | ✅ | Port 8100 |
| MCP Server | ✅ | `mcp/knowledge-mcp-server` |
| RAG Engine | ✅ Basic | Single-shot Q&A with Claude |
| Auto-Tagger | ✅ | Rule + LLM classification |

## Phase 1: Memory Layer (Mem0)

### 1.1 Install Dependencies
```bash
cd "C:\Users\gtmar\Projects\Auto-Claude\BD-Automation-Engine"
pip install mem0ai chromadb --break-system-packages
```

### 1.2 Create Memory Layer
**Create file:** `Engine8_Knowledge/scripts/memory_layer.py`

```python
"""
Unified Memory Layer for BD Intelligence Hub
Uses Mem0 for cross-session context and entity memory.
Single instance shared across all connected projects.
"""

import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger('BDMemory')

try:
    from mem0 import Memory
    MEM0_AVAILABLE = True
except ImportError:
    MEM0_AVAILABLE = False
    logger.warning("mem0ai not installed. Run: pip install mem0ai")

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent.parent
MEM0_DATA_PATH = PROJECT_ROOT / "Engine8_Knowledge" / "data" / "mem0_db"
UNIFIED_USER_ID = "pts_bd_unified"  # Single user ID for all projects


class BDMemoryLayer:
    """
    Universal memory layer for BD Intelligence.
    Maintains context across sessions, remembers user preferences,
    tracks entity relationships over time.
    
    CRITICAL: Uses unified user_id="pts_bd_unified" for ALL operations
    to ensure cross-project memory sharing.
    """
    
    def __init__(self, user_id: str = UNIFIED_USER_ID):
        if not MEM0_AVAILABLE:
            raise ImportError("mem0ai required. Install with: pip install mem0ai")
        
        MEM0_DATA_PATH.mkdir(parents=True, exist_ok=True)
        
        config = {
            "vector_store": {
                "provider": "chroma",
                "config": {
                    "collection_name": "bd_unified_memories",
                    "path": str(MEM0_DATA_PATH)
                }
            }
        }
        
        self.memory = Memory.from_config(config)
        self.user_id = user_id
        logger.info(f"Memory layer initialized with user_id={user_id}")
    
    def add_interaction(self, query: str, response: str, 
                       source_project: str = "hub",
                       metadata: Optional[Dict] = None):
        """Store query-response pair with source tracking."""
        content = f"Query: {query}\nResponse: {response}"
        self.memory.add(
            content,
            user_id=self.user_id,
            metadata={
                "type": "interaction",
                "source_project": source_project,
                "timestamp": datetime.now().isoformat(),
                **(metadata or {})
            }
        )
    
    def add_entity_fact(self, entity_type: str, entity_name: str, fact: str,
                       source_project: str = "hub"):
        """Store a fact about an entity (program, company, contact)."""
        content = f"{entity_type.upper()} '{entity_name}': {fact}"
        self.memory.add(
            content,
            user_id=self.user_id,
            metadata={
                "type": "entity_fact",
                "entity_type": entity_type,
                "entity_name": entity_name,
                "source_project": source_project,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def add_bd_insight(self, insight: str, 
                      programs: List[str] = None, 
                      companies: List[str] = None,
                      source_project: str = "hub"):
        """Store a BD insight with related entities."""
        self.memory.add(
            f"BD Insight: {insight}",
            user_id=self.user_id,
            metadata={
                "type": "bd_insight",
                "programs": programs or [],
                "companies": companies or [],
                "source_project": source_project,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def add_scrape_result(self, source: str, record_count: int, 
                         summary: str, source_project: str = "data-scraper"):
        """Store scrape operation results for tracking."""
        self.memory.add(
            f"Scrape from {source}: {record_count} records. {summary}",
            user_id=self.user_id,
            metadata={
                "type": "scrape_result",
                "source": source,
                "record_count": record_count,
                "source_project": source_project,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def get_context(self, query: str, limit: int = 10) -> List[Dict]:
        """Retrieve relevant memories for a query."""
        results = self.memory.search(query, user_id=self.user_id, limit=limit)
        return results
    
    def get_entity_facts(self, entity_name: str, limit: int = 20) -> List[Dict]:
        """Get all facts about a specific entity."""
        return self.memory.search(
            entity_name,
            user_id=self.user_id,
            limit=limit
        )
    
    def get_recent_insights(self, limit: int = 10) -> List[Dict]:
        """Get recent BD insights."""
        return self.memory.search(
            "BD insight opportunity strategy capture",
            user_id=self.user_id,
            limit=limit
        )
    
    def get_project_activity(self, project_name: str, limit: int = 20) -> List[Dict]:
        """Get recent activity from a specific project."""
        return self.memory.search(
            f"source_project:{project_name}",
            user_id=self.user_id,
            limit=limit
        )
    
    def clear_all(self):
        """Clear all memories (use with extreme caution)."""
        self.memory.delete_all(user_id=self.user_id)
        logger.warning("All memories cleared!")


# Singleton instance
_memory_instance: Optional[BDMemoryLayer] = None

def get_memory() -> BDMemoryLayer:
    """Get or create the singleton memory instance."""
    global _memory_instance
    if _memory_instance is None:
        _memory_instance = BDMemoryLayer()
    return _memory_instance


# CLI for testing
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='BD Memory Layer')
    parser.add_argument('--add', help='Add a memory')
    parser.add_argument('--search', help='Search memories')
    parser.add_argument('--entity', help='Get entity facts')
    parser.add_argument('--insights', action='store_true', help='Get recent insights')
    
    args = parser.parse_args()
    
    memory = get_memory()
    
    if args.add:
        memory.memory.add(args.add, user_id=memory.user_id)
        print(f"Added: {args.add}")
    
    if args.search:
        results = memory.get_context(args.search)
        print(f"Found {len(results)} results:")
        for r in results:
            print(f"  - {r}")
    
    if args.entity:
        results = memory.get_entity_facts(args.entity)
        print(f"Facts about {args.entity}:")
        for r in results:
            print(f"  - {r}")
    
    if args.insights:
        results = memory.get_recent_insights()
        print("Recent BD Insights:")
        for r in results:
            print(f"  - {r}")
```

### 1.3 Integrate Memory with RAG Engine
**Modify file:** `Engine8_Knowledge/scripts/rag_engine.py`

Add at the top after other imports:
```python
from Engine8_Knowledge.scripts.memory_layer import get_memory
```

Add to `BDRAGEngine.__init__`:
```python
        # Initialize memory layer
        try:
            self.memory = get_memory()
            logger.info("Memory layer connected")
        except Exception as e:
            self.memory = None
            logger.warning(f"Memory layer not available: {e}")
```

Add to `BDRAGEngine.ask` method, just before the final return statement:
```python
        # Store interaction in memory for cross-session context
        if self.memory:
            try:
                self.memory.add_interaction(
                    query=question,
                    response=answer,
                    source_project="hub",
                    metadata={
                        "collection_searched": collection_searched,
                        "confidence": confidence,
                        "source_count": len(sources)
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to store in memory: {e}")
```

---

## Phase 2: LightRAG Knowledge Graph

### 2.1 Install Dependencies
```bash
pip install lightrag-hku networkx --break-system-packages
```

### 2.2 Create LightRAG Integration
**Create file:** `Engine8_Knowledge/scripts/lightrag_engine.py`

```python
"""
LightRAG Knowledge Graph Engine for BD Intelligence Hub
Provides dual-level retrieval: specific entities + abstract themes
10x token reduction vs standard RAG
"""

import os
import sys
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger('BDLightRAG')

try:
    from lightrag import LightRAG, QueryParam
    from lightrag.llm import openai_complete_if_cache, openai_embedding
    LIGHTRAG_AVAILABLE = True
except ImportError:
    LIGHTRAG_AVAILABLE = False
    logger.warning("lightrag-hku not installed. Run: pip install lightrag-hku")

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent.parent
LIGHTRAG_DATA_PATH = PROJECT_ROOT / "Engine8_Knowledge" / "data" / "lightrag"


class BDKnowledgeGraph:
    """
    Knowledge Graph RAG for BD Intelligence.
    
    Provides:
    - Entity extraction and relationship mapping
    - Dual-level retrieval (local entities + global themes)
    - 10x token reduction vs standard RAG
    - Cross-entity queries (e.g., "Who at Leidos works on DCGS?")
    """
    
    def __init__(self, working_dir: str = None):
        if not LIGHTRAG_AVAILABLE:
            raise ImportError("lightrag-hku required. Install with: pip install lightrag-hku")
        
        self.working_dir = working_dir or str(LIGHTRAG_DATA_PATH)
        os.makedirs(self.working_dir, exist_ok=True)
        
        # Check for OpenAI key (required for embeddings)
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY required for LightRAG embeddings")
        
        self.rag = LightRAG(
            working_dir=self.working_dir,
            llm_model_func=openai_complete_if_cache,
            llm_model_name="gpt-4o-mini",  # Cost-effective for graph building
            embedding_func=openai_embedding,
        )
        
        logger.info(f"LightRAG initialized at {self.working_dir}")
    
    async def insert_document(self, text: str):
        """Insert a document and extract entities/relationships."""
        await self.rag.ainsert(text)
    
    async def insert_program(self, program_data: Dict):
        """Insert a federal program into the knowledge graph."""
        text = f"""
        Federal Program: {program_data.get('name', 'Unknown')}
        Prime Contractor: {program_data.get('prime_contractor', 'Unknown')}
        Agency: {program_data.get('agency', 'Unknown')}
        Contract Value: {program_data.get('contract_value', 'Unknown')}
        Location: {program_data.get('location', 'Unknown')}
        Mission Area: {program_data.get('mission_area', 'Unknown')}
        Status: {program_data.get('status', 'Active')}
        Description: {program_data.get('description', '')}
        """
        await self.insert_document(text.strip())
    
    async def insert_contact(self, contact_data: Dict):
        """Insert a contact into the knowledge graph."""
        name = f"{contact_data.get('first_name', '')} {contact_data.get('last_name', '')}".strip()
        name = name or contact_data.get('name', 'Unknown')
        
        text = f"""
        Person: {name}
        Title: {contact_data.get('title', 'Unknown')}
        Company: {contact_data.get('company', 'Unknown')}
        Program: {contact_data.get('program', 'Unknown')}
        Location: {contact_data.get('location', 'Unknown')}
        Tier: {contact_data.get('tier', 'Unknown')}
        """
        await self.insert_document(text.strip())
    
    async def insert_company(self, company_data: Dict):
        """Insert a company into the knowledge graph."""
        text = f"""
        Company: {company_data.get('name', 'Unknown')}
        Type: {company_data.get('type', 'Defense Contractor')}
        Programs: {company_data.get('programs', 'Unknown')}
        Relationship: {company_data.get('relationship_tier', 'Unknown')}
        Contract Value: {company_data.get('total_contract_value', 'Unknown')}
        """
        await self.insert_document(text.strip())
    
    async def query_naive(self, query: str) -> str:
        """Standard RAG query (no graph enhancement)."""
        return await self.rag.aquery(query, param=QueryParam(mode="naive"))
    
    async def query_local(self, query: str) -> str:
        """Query focusing on specific entities (low-level, precise)."""
        return await self.rag.aquery(query, param=QueryParam(mode="local"))
    
    async def query_global(self, query: str) -> str:
        """Query focusing on abstract themes (high-level, broad)."""
        return await self.rag.aquery(query, param=QueryParam(mode="global"))
    
    async def query_hybrid(self, query: str) -> str:
        """Combined local + global retrieval (best quality)."""
        return await self.rag.aquery(query, param=QueryParam(mode="hybrid"))
    
    def query_sync(self, query: str, mode: str = "hybrid") -> str:
        """Synchronous query wrapper for API use."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            if mode == "naive":
                result = loop.run_until_complete(self.query_naive(query))
            elif mode == "local":
                result = loop.run_until_complete(self.query_local(query))
            elif mode == "global":
                result = loop.run_until_complete(self.query_global(query))
            else:
                result = loop.run_until_complete(self.query_hybrid(query))
            return result
        finally:
            loop.close()


# Singleton instance
_kg_instance: Optional[BDKnowledgeGraph] = None

def get_knowledge_graph() -> BDKnowledgeGraph:
    """Get or create the singleton knowledge graph instance."""
    global _kg_instance
    if _kg_instance is None:
        _kg_instance = BDKnowledgeGraph()
    return _kg_instance


# CLI for testing
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='BD Knowledge Graph')
    parser.add_argument('--query', help='Query the knowledge graph')
    parser.add_argument('--mode', default='hybrid', 
                       choices=['naive', 'local', 'global', 'hybrid'])
    parser.add_argument('--insert', help='Insert text into graph')
    
    args = parser.parse_args()
    
    kg = get_knowledge_graph()
    
    if args.insert:
        asyncio.run(kg.insert_document(args.insert))
        print(f"Inserted into knowledge graph")
    
    if args.query:
        result = kg.query_sync(args.query, mode=args.mode)
        print(f"\nQuery: {args.query}")
        print(f"Mode: {args.mode}")
        print(f"\nAnswer:\n{result}")
```

### 2.3 Create Graph Builder from Qdrant
**Create file:** `Engine8_Knowledge/scripts/build_knowledge_graph.py`

```python
"""
Build LightRAG knowledge graph from existing Qdrant data
Run this after initial setup to populate the graph
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from Engine8_Knowledge.scripts.vector_store import BDKnowledgeStore
from Engine8_Knowledge.scripts.lightrag_engine import BDKnowledgeGraph


async def build_graph_from_qdrant(limit_per_collection: int = 500):
    """Build knowledge graph from existing Qdrant data."""
    
    print("=" * 60)
    print("BUILDING KNOWLEDGE GRAPH FROM QDRANT")
    print("=" * 60)
    
    store = BDKnowledgeStore()
    kg = BDKnowledgeGraph()
    
    # Index programs
    print("\n[1/3] Indexing programs...")
    try:
        programs = store.search(
            "federal program contract", 
            collection="programs", 
            limit=limit_per_collection
        )
        for i, p in enumerate(programs):
            await kg.insert_program(p.payload)
            if (i + 1) % 50 == 0:
                print(f"  Processed {i + 1}/{len(programs)} programs")
        print(f"  ✓ Indexed {len(programs)} programs")
    except Exception as e:
        print(f"  ✗ Error indexing programs: {e}")
    
    # Index key contacts (Tier 1 and Tier 2)
    print("\n[2/3] Indexing key contacts...")
    try:
        contacts = store.search(
            "decision maker tier manager director", 
            collection="contacts", 
            limit=limit_per_collection
        )
        for i, c in enumerate(contacts):
            await kg.insert_contact(c.payload)
            if (i + 1) % 100 == 0:
                print(f"  Processed {i + 1}/{len(contacts)} contacts")
        print(f"  ✓ Indexed {len(contacts)} contacts")
    except Exception as e:
        print(f"  ✗ Error indexing contacts: {e}")
    
    # Index companies
    print("\n[3/3] Indexing companies...")
    try:
        # Search for companies (may be in programs or separate collection)
        companies = store.search(
            "contractor company prime subcontractor", 
            collection="programs", 
            limit=100
        )
        unique_companies = set()
        for p in companies:
            prime = p.payload.get('prime_contractor')
            if prime and prime not in unique_companies:
                unique_companies.add(prime)
                await kg.insert_company({
                    "name": prime,
                    "type": "Prime Contractor"
                })
        print(f"  ✓ Indexed {len(unique_companies)} companies")
    except Exception as e:
        print(f"  ✗ Error indexing companies: {e}")
    
    print("\n" + "=" * 60)
    print("KNOWLEDGE GRAPH BUILD COMPLETE")
    print("=" * 60)
    
    # Test query
    print("\n[TEST] Running test query...")
    result = kg.query_sync("What programs does Leidos work on?", mode="hybrid")
    print(f"Test result: {result[:200]}...")


if __name__ == "__main__":
    asyncio.run(build_graph_from_qdrant())
```

---

## Phase 3: Hybrid Retriever with Reranking

### 3.1 Install Dependencies
```bash
pip install rank-bm25 sentence-transformers --break-system-packages
```

### 3.2 Create Hybrid Retriever
**Create file:** `Engine8_Knowledge/scripts/hybrid_retriever.py`

```python
"""
Hybrid Retriever for BD Intelligence Hub
Combines semantic search + BM25 keyword search + Reciprocal Rank Fusion
Provides 30-50% better recall than semantic-only search
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger('HybridRetriever')

try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False
    logger.warning("rank-bm25 not installed. Run: pip install rank-bm25")

from Engine8_Knowledge.scripts.vector_store import BDKnowledgeStore, SearchResult


@dataclass
class HybridResult:
    """Result from hybrid retrieval with combined score."""
    id: str
    score: float
    semantic_score: float
    bm25_score: float
    rrf_score: float
    payload: Dict[str, Any]
    collection: str


class HybridRetriever:
    """
    Hybrid retrieval combining:
    1. Semantic search (Qdrant embeddings)
    2. BM25 keyword search
    3. Reciprocal Rank Fusion for score combination
    
    Provides 30-50% better recall than semantic-only search.
    """
    
    def __init__(self, store: BDKnowledgeStore = None, rrf_k: int = 60):
        """
        Initialize hybrid retriever.
        
        Args:
            store: BDKnowledgeStore instance
            rrf_k: RRF constant (default 60, higher = more weight to lower ranks)
        """
        self.store = store or BDKnowledgeStore()
        self.rrf_k = rrf_k
        
        # BM25 indexes per collection (built on-demand)
        self._bm25_indexes: Dict[str, Tuple[BM25Okapi, List[Dict]]] = {}
    
    def _build_bm25_index(self, collection: str, documents: List[SearchResult]):
        """Build BM25 index from documents."""
        if not BM25_AVAILABLE:
            return None, []
        
        # Tokenize documents
        texts = []
        for doc in documents:
            payload = doc.payload
            # Combine text fields for indexing
            text_parts = []
            for field in ['name', 'title', 'content', 'company', 'program_name', 
                         'location', 'description', 'notes']:
                if field in payload and payload[field]:
                    text_parts.append(str(payload[field]))
            texts.append(' '.join(text_parts).lower().split())
        
        if not texts:
            return None, []
        
        bm25 = BM25Okapi(texts)
        return bm25, documents
    
    def _get_bm25_scores(self, query: str, collection: str, 
                        semantic_results: List[SearchResult]) -> Dict[str, float]:
        """Get BM25 scores for documents."""
        if not BM25_AVAILABLE or not semantic_results:
            return {}
        
        # Build or get BM25 index
        if collection not in self._bm25_indexes:
            bm25, docs = self._build_bm25_index(collection, semantic_results)
            self._bm25_indexes[collection] = (bm25, docs)
        else:
            bm25, docs = self._bm25_indexes[collection]
        
        if bm25 is None:
            return {}
        
        # Get BM25 scores
        query_tokens = query.lower().split()
        scores = bm25.get_scores(query_tokens)
        
        # Map scores to document IDs
        score_map = {}
        for i, doc in enumerate(docs):
            if i < len(scores):
                score_map[doc.id] = scores[i]
        
        return score_map
    
    def _reciprocal_rank_fusion(self, 
                                semantic_results: List[SearchResult],
                                bm25_scores: Dict[str, float]) -> List[HybridResult]:
        """
        Combine semantic and BM25 rankings using Reciprocal Rank Fusion.
        
        RRF score = sum(1 / (k + rank_i)) for each ranking method
        """
        # Build semantic ranking
        semantic_ranking = {r.id: i for i, r in enumerate(semantic_results)}
        
        # Build BM25 ranking (sort by score descending)
        bm25_ranking = {}
        if bm25_scores:
            sorted_bm25 = sorted(bm25_scores.items(), key=lambda x: x[1], reverse=True)
            bm25_ranking = {doc_id: i for i, (doc_id, _) in enumerate(sorted_bm25)}
        
        # Calculate RRF scores
        all_doc_ids = set(semantic_ranking.keys()) | set(bm25_ranking.keys())
        rrf_scores = {}
        
        for doc_id in all_doc_ids:
            score = 0.0
            
            # Semantic contribution
            if doc_id in semantic_ranking:
                score += 1.0 / (self.rrf_k + semantic_ranking[doc_id])
            
            # BM25 contribution
            if doc_id in bm25_ranking:
                score += 1.0 / (self.rrf_k + bm25_ranking[doc_id])
            
            rrf_scores[doc_id] = score
        
        # Build final results
        results = []
        doc_lookup = {r.id: r for r in semantic_results}
        
        for doc_id, rrf_score in sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True):
            if doc_id in doc_lookup:
                doc = doc_lookup[doc_id]
                results.append(HybridResult(
                    id=doc_id,
                    score=rrf_score,
                    semantic_score=doc.score,
                    bm25_score=bm25_scores.get(doc_id, 0.0),
                    rrf_score=rrf_score,
                    payload=doc.payload,
                    collection=doc.collection
                ))
        
        return results
    
    def search(self, query: str, collection: str, 
               limit: int = 20,
               semantic_weight: float = 0.7,
               bm25_weight: float = 0.3) -> List[HybridResult]:
        """
        Perform hybrid search.
        
        Args:
            query: Search query
            collection: Collection to search
            limit: Maximum results
            semantic_weight: Weight for semantic scores (0-1)
            bm25_weight: Weight for BM25 scores (0-1)
        
        Returns:
            List of HybridResult objects sorted by combined score
        """
        # Get semantic results (fetch more for better BM25 coverage)
        semantic_results = self.store.search(
            query=query,
            collection=collection,
            limit=limit * 3,
            score_threshold=0.1
        )
        
        if not semantic_results:
            return []
        
        # Get BM25 scores
        bm25_scores = self._get_bm25_scores(query, collection, semantic_results)
        
        # Combine with RRF
        hybrid_results = self._reciprocal_rank_fusion(semantic_results, bm25_scores)
        
        return hybrid_results[:limit]
    
    def search_all(self, query: str, 
                   limit_per_collection: int = 10) -> Dict[str, List[HybridResult]]:
        """Search all collections with hybrid retrieval."""
        collections = ['jobs', 'contacts', 'programs', 'documents', 'activities']
        results = {}
        
        for collection in collections:
            try:
                results[collection] = self.search(query, collection, limit_per_collection)
            except Exception as e:
                logger.warning(f"Hybrid search failed for {collection}: {e}")
                results[collection] = []
        
        return results


# CLI for testing
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Hybrid Retriever')
    parser.add_argument('query', help='Search query')
    parser.add_argument('--collection', '-c', default='contacts', help='Collection')
    parser.add_argument('--limit', '-n', type=int, default=10, help='Max results')
    
    args = parser.parse_args()
    
    retriever = HybridRetriever()
    results = retriever.search(args.query, args.collection, args.limit)
    
    print(f"\nHybrid search for: {args.query}")
    print(f"Collection: {args.collection}")
    print(f"Results: {len(results)}\n")
    
    for i, r in enumerate(results, 1):
        name = r.payload.get('name', r.payload.get('title', r.id))
        print(f"{i}. {name}")
        print(f"   RRF: {r.rrf_score:.4f} | Semantic: {r.semantic_score:.4f} | BM25: {r.bm25_score:.4f}")
```

---

## Phase 4: Query Router

### 4.1 Create Intelligent Query Router
**Create file:** `Engine8_Knowledge/scripts/query_router.py`

```python
"""
Intelligent Query Router for BD Intelligence Hub
Routes queries to optimal RAG system based on query type
"""

import re
import sys
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import logging

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger('QueryRouter')


class QueryType(Enum):
    FACTUAL = "factual"           # Simple lookups -> Qdrant semantic
    RELATIONAL = "relational"     # Entity relationships -> LightRAG
    COMPREHENSIVE = "comprehensive"  # Full analysis -> Multi-source
    MEMORY = "memory"             # Past interactions -> Mem0
    KEYWORD = "keyword"           # Specific terms -> Hybrid retrieval


@dataclass
class RouteResult:
    """Result from query classification."""
    query_type: QueryType
    primary_system: str
    secondary_systems: List[str]
    reasoning: str
    confidence: float


class QueryRouter:
    """
    Intelligent query router that selects optimal RAG system.
    
    Routing Logic:
    - Relational queries (relationships, connections) -> LightRAG
    - Memory queries (remember, previous, earlier) -> Mem0
    - Comprehensive queries (analyze, strategy, report) -> Multi-source
    - Keyword-heavy queries -> Hybrid retrieval
    - Default factual queries -> Qdrant semantic
    """
    
    PATTERNS = {
        QueryType.RELATIONAL: [
            r"relationship",
            r"connected to",
            r"works with",
            r"teaming",
            r"partner",
            r"competitor",
            r"who works",
            r"between .* and",
            r"subcontract",
            r"prime.*sub",
        ],
        QueryType.COMPREHENSIVE: [
            r"capture strategy",
            r"win strategy",
            r"analyze",
            r"compare",
            r"comprehensive",
            r"deep dive",
            r"full report",
            r"build.*strategy",
            r"complete.*overview",
            r"all.*about",
        ],
        QueryType.MEMORY: [
            r"remember",
            r"we discussed",
            r"last time",
            r"previously",
            r"you told me",
            r"earlier",
            r"mentioned before",
            r"our conversation",
        ],
        QueryType.KEYWORD: [
            r"clearance",
            r"ts/sci",
            r"secret",
            r"location",
            r"salary",
            r"contract number",
            r"naics",
            r"cage code",
        ],
    }
    
    def classify(self, query: str) -> RouteResult:
        """Classify query and determine routing."""
        query_lower = query.lower()
        
        # Check patterns in order of specificity
        for query_type, patterns in self.PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    return self._build_route(query_type, query)
        
        # Default to factual (Qdrant semantic search)
        return self._build_route(QueryType.FACTUAL, query)
    
    def _build_route(self, query_type: QueryType, query: str) -> RouteResult:
        """Build routing result based on query type."""
        
        if query_type == QueryType.FACTUAL:
            return RouteResult(
                query_type=query_type,
                primary_system="qdrant",
                secondary_systems=["memory"],
                reasoning="Factual query - using Qdrant semantic search with memory context",
                confidence=0.8
            )
        
        elif query_type == QueryType.RELATIONAL:
            return RouteResult(
                query_type=query_type,
                primary_system="lightrag",
                secondary_systems=["qdrant", "memory"],
                reasoning="Relationship query - using LightRAG knowledge graph for entity connections",
                confidence=0.9
            )
        
        elif query_type == QueryType.COMPREHENSIVE:
            return RouteResult(
                query_type=query_type,
                primary_system="multi",
                secondary_systems=["qdrant", "lightrag", "memory", "hybrid"],
                reasoning="Comprehensive analysis - using all systems for maximum coverage",
                confidence=0.85
            )
        
        elif query_type == QueryType.MEMORY:
            return RouteResult(
                query_type=query_type,
                primary_system="memory",
                secondary_systems=["qdrant"],
                reasoning="Memory query - checking past interactions first",
                confidence=0.9
            )
        
        elif query_type == QueryType.KEYWORD:
            return RouteResult(
                query_type=query_type,
                primary_system="hybrid",
                secondary_systems=["qdrant"],
                reasoning="Keyword-specific query - using hybrid retrieval (semantic + BM25)",
                confidence=0.85
            )
        
        return RouteResult(
            query_type=QueryType.FACTUAL,
            primary_system="qdrant",
            secondary_systems=[],
            reasoning="Default routing to Qdrant semantic search",
            confidence=0.7
        )


async def smart_query(query: str) -> Dict[str, Any]:
    """
    Execute intelligent query using the router.
    Automatically selects and queries optimal system(s).
    """
    from Engine8_Knowledge.scripts.vector_store import BDKnowledgeStore
    from Engine8_Knowledge.scripts.memory_layer import get_memory
    from Engine8_Knowledge.scripts.hybrid_retriever import HybridRetriever
    
    router = QueryRouter()
    route = router.classify(query)
    
    results = {
        "query": query,
        "route": {
            "type": route.query_type.value,
            "primary": route.primary_system,
            "secondary": route.secondary_systems,
            "reasoning": route.reasoning,
            "confidence": route.confidence
        },
        "answers": {}
    }
    
    # Execute based on routing
    store = BDKnowledgeStore()
    
    # Memory (if applicable)
    if route.primary_system == "memory" or "memory" in route.secondary_systems:
        try:
            memory = get_memory()
            memory_results = memory.get_context(query, limit=5)
            results["answers"]["memory"] = memory_results
        except Exception as e:
            results["answers"]["memory"] = {"error": str(e)}
    
    # Qdrant semantic search
    if route.primary_system == "qdrant" or "qdrant" in route.secondary_systems:
        try:
            qdrant_results = store.search_all(query, limit_per_collection=5)
            results["answers"]["qdrant"] = {
                coll: [r.to_dict() for r in items]
                for coll, items in qdrant_results.items()
            }
        except Exception as e:
            results["answers"]["qdrant"] = {"error": str(e)}
    
    # Hybrid retrieval
    if route.primary_system == "hybrid" or "hybrid" in route.secondary_systems:
        try:
            retriever = HybridRetriever(store)
            hybrid_results = retriever.search_all(query, limit_per_collection=5)
            results["answers"]["hybrid"] = {
                coll: [{"id": r.id, "score": r.score, "payload": r.payload}
                       for r in items]
                for coll, items in hybrid_results.items()
            }
        except Exception as e:
            results["answers"]["hybrid"] = {"error": str(e)}
    
    # LightRAG knowledge graph
    if route.primary_system == "lightrag" or "lightrag" in route.secondary_systems:
        try:
            from Engine8_Knowledge.scripts.lightrag_engine import get_knowledge_graph
            kg = get_knowledge_graph()
            kg_result = kg.query_sync(query, mode="hybrid")
            results["answers"]["lightrag"] = kg_result
        except Exception as e:
            results["answers"]["lightrag"] = {"error": str(e)}
    
    return results


# CLI for testing
if __name__ == "__main__":
    import asyncio
    import argparse
    
    parser = argparse.ArgumentParser(description='Query Router')
    parser.add_argument('query', help='Query to route and execute')
    parser.add_argument('--classify-only', action='store_true', 
                       help='Only classify, do not execute')
    
    args = parser.parse_args()
    
    router = QueryRouter()
    route = router.classify(args.query)
    
    print(f"\nQuery: {args.query}")
    print(f"Type: {route.query_type.value}")
    print(f"Primary: {route.primary_system}")
    print(f"Secondary: {route.secondary_systems}")
    print(f"Reasoning: {route.reasoning}")
    print(f"Confidence: {route.confidence}")
    
    if not args.classify_only:
        print("\nExecuting query...")
        result = asyncio.run(smart_query(args.query))
        print(f"\nResults: {result}")
```

---

## Phase 5: Update FastAPI Endpoints

### 5.1 Update API with New Endpoints
**Modify file:** `Engine8_Knowledge/api.py`

Add these imports at the top:
```python
from Engine8_Knowledge.scripts.memory_layer import get_memory, BDMemoryLayer
from Engine8_Knowledge.scripts.query_router import QueryRouter, smart_query
from Engine8_Knowledge.scripts.hybrid_retriever import HybridRetriever
```

Add these endpoint classes after existing Pydantic models:
```python
# =========================================
# NEW PYDANTIC MODELS
# =========================================

class MemoryAddRequest(BaseModel):
    content: str
    metadata: Optional[Dict[str, Any]] = None
    source_project: str = "api"

class EntityFactRequest(BaseModel):
    entity_type: str  # program, company, contact
    entity_name: str
    fact: str
    source_project: str = "api"

class MemorySearchRequest(BaseModel):
    query: str
    limit: int = 10

class SmartQueryRequest(BaseModel):
    question: str

class LightRAGQueryRequest(BaseModel):
    query: str
    mode: str = "hybrid"  # naive, local, global, hybrid

class HybridSearchRequest(BaseModel):
    query: str
    collection: str
    limit: int = 20
```

Add these endpoints at the end of the file (before `def main()`):
```python
# =========================================
# MEMORY ENDPOINTS
# =========================================

@app.post("/memory/add")
async def add_memory(request: MemoryAddRequest):
    """Add content to unified memory."""
    memory = get_memory()
    memory.memory.add(
        request.content,
        user_id=memory.user_id,
        metadata={
            "source_project": request.source_project,
            **(request.metadata or {})
        }
    )
    return {"status": "success", "message": "Memory added"}

@app.post("/memory/entity")
async def add_entity_fact(request: EntityFactRequest):
    """Add a fact about an entity to memory."""
    memory = get_memory()
    memory.add_entity_fact(
        request.entity_type,
        request.entity_name,
        request.fact,
        source_project=request.source_project
    )
    return {"status": "success", "entity": request.entity_name}

@app.post("/memory/search")
async def search_memory(request: MemorySearchRequest):
    """Search memory for relevant context."""
    memory = get_memory()
    results = memory.get_context(request.query, limit=request.limit)
    return {"query": request.query, "results": results}

@app.get("/memory/entity/{entity_name}")
async def get_entity_memory(entity_name: str, limit: int = 20):
    """Get all memories about an entity."""
    memory = get_memory()
    results = memory.get_entity_facts(entity_name, limit=limit)
    return {"entity": entity_name, "facts": results}

@app.get("/memory/insights")
async def get_insights(limit: int = 10):
    """Get recent BD insights from memory."""
    memory = get_memory()
    results = memory.get_recent_insights(limit=limit)
    return {"insights": results}

# =========================================
# SMART QUERY ENDPOINTS
# =========================================

@app.post("/ask/smart")
async def smart_ask(request: SmartQueryRequest):
    """
    Intelligent query routing - automatically selects best RAG system.
    Returns result with routing explanation.
    """
    result = await smart_query(request.question)
    return result

@app.get("/ask/smart")
async def smart_ask_get(q: str = Query(..., description="Question")):
    """GET endpoint for smart ask."""
    result = await smart_query(q)
    return result

@app.get("/route/classify")
async def classify_query(q: str = Query(..., description="Query to classify")):
    """Classify a query to see how it would be routed."""
    router = QueryRouter()
    route = router.classify(q)
    return {
        "query": q,
        "type": route.query_type.value,
        "primary_system": route.primary_system,
        "secondary_systems": route.secondary_systems,
        "reasoning": route.reasoning,
        "confidence": route.confidence
    }

# =========================================
# HYBRID SEARCH ENDPOINTS
# =========================================

@app.post("/search/hybrid")
async def hybrid_search(request: HybridSearchRequest):
    """Hybrid search combining semantic + BM25 + RRF."""
    retriever = HybridRetriever()
    results = retriever.search(
        request.query, 
        request.collection, 
        request.limit
    )
    return {
        "query": request.query,
        "collection": request.collection,
        "results": [
            {
                "id": r.id,
                "score": r.score,
                "semantic_score": r.semantic_score,
                "bm25_score": r.bm25_score,
                "payload": r.payload
            }
            for r in results
        ]
    }

# =========================================
# LIGHTRAG / KNOWLEDGE GRAPH ENDPOINTS
# =========================================

@app.post("/lightrag/query")
async def lightrag_query(request: LightRAGQueryRequest):
    """Query knowledge graph."""
    try:
        from Engine8_Knowledge.scripts.lightrag_engine import get_knowledge_graph
        kg = get_knowledge_graph()
        result = kg.query_sync(request.query, mode=request.mode)
        return {
            "query": request.query,
            "mode": request.mode,
            "answer": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/lightrag/build")
async def build_knowledge_graph():
    """Rebuild knowledge graph from Qdrant data."""
    try:
        from Engine8_Knowledge.scripts.build_knowledge_graph import build_graph_from_qdrant
        import asyncio
        await build_graph_from_qdrant()
        return {"status": "success", "message": "Knowledge graph rebuilt"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =========================================
# EXTERNAL PROJECT ENDPOINTS
# =========================================

@app.post("/ingest/jobs")
async def ingest_jobs(jobs: List[Dict], source: str = "data-scraper"):
    """
    Ingest jobs from external project (e.g., Data-Scraper).
    Writes to unified Qdrant and logs to memory.
    """
    if not indexer:
        raise HTTPException(status_code=503, detail="Indexer not initialized")
    
    result = store.index_jobs(jobs)
    
    # Log to memory
    memory = get_memory()
    memory.add_scrape_result(
        source=source,
        record_count=result[0],
        summary=f"Ingested {result[0]} jobs, {result[1]} errors"
    )
    
    return {
        "status": "success",
        "indexed": result[0],
        "errors": result[1],
        "source": source
    }

@app.post("/ingest/contacts")
async def ingest_contacts(contacts: List[Dict], source: str = "data-scraper"):
    """Ingest contacts from external project."""
    if not indexer:
        raise HTTPException(status_code=503, detail="Indexer not initialized")
    
    result = store.index_contacts(contacts)
    
    memory = get_memory()
    memory.add_scrape_result(
        source=source,
        record_count=result[0],
        summary=f"Ingested {result[0]} contacts, {result[1]} errors"
    )
    
    return {
        "status": "success",
        "indexed": result[0],
        "errors": result[1],
        "source": source
    }
```

---

## Phase 6: Update MCP Server

### 6.1 Add New Tools to MCP Server
**Modify file:** `mcp/knowledge-mcp-server/src/index.ts`

Add these new tool definitions to the tools array:

```typescript
// Memory tools
{
  name: "memory_add",
  description: "Add context to unified BD memory for cross-session persistence",
  inputSchema: {
    type: "object",
    properties: {
      content: { type: "string", description: "Content to remember" },
      metadata: { type: "object", description: "Optional metadata" }
    },
    required: ["content"]
  }
},
{
  name: "memory_search",
  description: "Search past interactions and stored BD context",
  inputSchema: {
    type: "object",
    properties: {
      query: { type: "string", description: "Search query" },
      limit: { type: "number", default: 10 }
    },
    required: ["query"]
  }
},
{
  name: "memory_entity",
  description: "Get all known facts about an entity (program, company, contact)",
  inputSchema: {
    type: "object",
    properties: {
      entity_name: { type: "string", description: "Entity name" },
      limit: { type: "number", default: 20 }
    },
    required: ["entity_name"]
  }
},

// Smart query
{
  name: "smart_ask",
  description: "Intelligent query routing - automatically selects best RAG system",
  inputSchema: {
    type: "object",
    properties: {
      question: { type: "string", description: "Question to ask" }
    },
    required: ["question"]
  }
},

// Knowledge graph
{
  name: "query_knowledge_graph",
  description: "Query LightRAG knowledge graph for entity relationships",
  inputSchema: {
    type: "object",
    properties: {
      query: { type: "string", description: "Query about relationships" },
      mode: { 
        type: "string", 
        enum: ["naive", "local", "global", "hybrid"],
        default: "hybrid"
      }
    },
    required: ["query"]
  }
},

// Hybrid search
{
  name: "hybrid_search",
  description: "Hybrid search combining semantic + BM25 keyword matching",
  inputSchema: {
    type: "object",
    properties: {
      query: { type: "string", description: "Search query" },
      collection: { 
        type: "string", 
        enum: ["jobs", "contacts", "programs", "documents", "activities"]
      },
      limit: { type: "number", default: 20 }
    },
    required: ["query", "collection"]
  }
}
```

Add corresponding handlers that call the FastAPI endpoints.

---

## Phase 7: Update requirements.txt

**Modify file:** `requirements.txt` - Add these dependencies:

```
# ============================================
# UNIFIED HUB ADDITIONS
# ============================================

# Memory Layer
mem0ai>=0.1.0

# Knowledge Graph
lightrag-hku>=0.1.0
networkx>=3.0

# Hybrid Retrieval
rank-bm25>=0.2.2

# Caching (optional, for future)
redis>=5.0.0

# Testing/Evaluation (optional)
# ragas>=0.1.0
```

---

## ✅ Hub Verification Checklist

Run these tests after completing the Hub build:

```bash
cd "C:\Users\gtmar\Projects\Auto-Claude\BD-Automation-Engine"

# 1. Test Memory Layer
python -c "from Engine8_Knowledge.scripts.memory_layer import get_memory; m = get_memory(); m.memory.add('test', user_id=m.user_id); print('Memory OK')"

# 2. Test LightRAG (requires OPENAI_API_KEY)
python Engine8_Knowledge/scripts/lightrag_engine.py --query "test query" --mode naive

# 3. Test Hybrid Retriever
python Engine8_Knowledge/scripts/hybrid_retriever.py "DCGS analyst" --collection contacts

# 4. Test Query Router
python Engine8_Knowledge/scripts/query_router.py "Who works on DCGS at Leidos?"

# 5. Start API and test endpoints
python Engine8_Knowledge/api.py &
curl http://localhost:8100/health
curl "http://localhost:8100/ask/smart?q=Find%20contacts%20at%20Leidos"

# 6. Build Knowledge Graph (run after API is stable)
python Engine8_Knowledge/scripts/build_knowledge_graph.py
```

---

# ═══════════════════════════════════════════════════════════════
# SECTION 2: DATA-SCRAPER (DATA WRITER)
# Path: C:\data-scraper\data-scraper
# ═══════════════════════════════════════════════════════════════

## 🎯 Data-Scraper Responsibilities

This project becomes a **DATA WRITER** that:
1. Scrapes jobs from Apex, Insight Global, TEKsystems, etc.
2. Extracts contacts from LinkedIn, ZoomInfo, etc.
3. Maps jobs to federal programs
4. **WRITES ALL DATA TO HUB** via API (not local storage)

## Current State

| Component | Status | Details |
|-----------|--------|---------|
| ChromaDB | ✅ | Local vector DB (will be deprecated) |
| SQLite | ✅ | knowledge.db with programs, companies, contacts |
| MCP Server | ✅ | 8 tools in `scripts/knowledge/mcp_server_stdio.py` |
| Apify Scrapers | ✅ | Job scraping configured |

## Phase 1: Create Hub Client

### 1.1 Create Hub API Client
**Create file:** `scripts/hub_client.py`

```python
"""
BD Intelligence Hub Client
Connects Data-Scraper to the central Hub API
All scraped data should be written through this client
"""

import os
import requests
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger('HubClient')

# Hub Configuration
HUB_API_URL = os.getenv("BD_HUB_API_URL", "http://127.0.0.1:8100")


@dataclass
class HubResponse:
    success: bool
    message: str
    data: Optional[Dict] = None


class BDHubClient:
    """
    Client for interacting with the BD Intelligence Hub API.
    
    Usage:
        client = BDHubClient()
        client.ingest_jobs(jobs_list)
        client.ingest_contacts(contacts_list)
        results = client.search("DCGS analyst")
    """
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or HUB_API_URL
        self.session = requests.Session()
        self.source = "data-scraper"
        
        # Verify connection
        try:
            resp = self.session.get(f"{self.base_url}/health", timeout=5)
            if resp.status_code == 200:
                logger.info(f"Connected to Hub at {self.base_url}")
            else:
                logger.warning(f"Hub health check failed: {resp.status_code}")
        except Exception as e:
            logger.error(f"Cannot connect to Hub at {self.base_url}: {e}")
    
    # =========================================
    # DATA INGESTION
    # =========================================
    
    def ingest_jobs(self, jobs: List[Dict]) -> HubResponse:
        """
        Send scraped jobs to the Hub for indexing.
        
        Args:
            jobs: List of job dictionaries with fields:
                - title, company, location, clearance, program_name, etc.
        
        Returns:
            HubResponse with indexed count
        """
        try:
            resp = self.session.post(
                f"{self.base_url}/ingest/jobs",
                json=jobs,
                params={"source": self.source},
                timeout=60
            )
            data = resp.json()
            return HubResponse(
                success=data.get("status") == "success",
                message=f"Indexed {data.get('indexed', 0)} jobs",
                data=data
            )
        except Exception as e:
            return HubResponse(success=False, message=str(e))
    
    def ingest_contacts(self, contacts: List[Dict]) -> HubResponse:
        """
        Send extracted contacts to the Hub for indexing.
        
        Args:
            contacts: List of contact dictionaries with fields:
                - name, first_name, last_name, title, company, email, etc.
        """
        try:
            resp = self.session.post(
                f"{self.base_url}/ingest/contacts",
                json=contacts,
                params={"source": self.source},
                timeout=60
            )
            data = resp.json()
            return HubResponse(
                success=data.get("status") == "success",
                message=f"Indexed {data.get('indexed', 0)} contacts",
                data=data
            )
        except Exception as e:
            return HubResponse(success=False, message=str(e))
    
    def ingest_programs(self, programs: List[Dict]) -> HubResponse:
        """Send program data to the Hub."""
        try:
            resp = self.session.post(
                f"{self.base_url}/index/programs",
                json=programs,
                timeout=60
            )
            return HubResponse(success=True, message="Programs indexed", data=resp.json())
        except Exception as e:
            return HubResponse(success=False, message=str(e))
    
    # =========================================
    # SEARCH (Read from Hub)
    # =========================================
    
    def search(self, query: str, collection: str = None, limit: int = 10) -> Dict:
        """
        Search the Hub's unified knowledge base.
        
        Args:
            query: Natural language query
            collection: Optional collection filter (jobs, contacts, programs, etc.)
            limit: Maximum results
        """
        try:
            params = {"query": query, "limit": limit}
            if collection:
                params["collection"] = collection
            
            resp = self.session.post(
                f"{self.base_url}/search",
                json=params,
                timeout=30
            )
            return resp.json()
        except Exception as e:
            return {"error": str(e)}
    
    def smart_ask(self, question: str) -> Dict:
        """
        Ask a question using the Hub's intelligent routing.
        Automatically selects best RAG system.
        """
        try:
            resp = self.session.get(
                f"{self.base_url}/ask/smart",
                params={"q": question},
                timeout=60
            )
            return resp.json()
        except Exception as e:
            return {"error": str(e)}
    
    def search_knowledge_graph(self, query: str, mode: str = "hybrid") -> Dict:
        """Query the Hub's knowledge graph for entity relationships."""
        try:
            resp = self.session.post(
                f"{self.base_url}/lightrag/query",
                json={"query": query, "mode": mode},
                timeout=60
            )
            return resp.json()
        except Exception as e:
            return {"error": str(e)}
    
    # =========================================
    # MEMORY
    # =========================================
    
    def add_memory(self, content: str, metadata: Dict = None) -> HubResponse:
        """Add context to Hub's unified memory."""
        try:
            resp = self.session.post(
                f"{self.base_url}/memory/add",
                json={
                    "content": content,
                    "metadata": metadata,
                    "source_project": self.source
                },
                timeout=10
            )
            return HubResponse(success=True, message="Memory added", data=resp.json())
        except Exception as e:
            return HubResponse(success=False, message=str(e))
    
    def search_memory(self, query: str, limit: int = 10) -> List[Dict]:
        """Search Hub's memory for relevant context."""
        try:
            resp = self.session.post(
                f"{self.base_url}/memory/search",
                json={"query": query, "limit": limit},
                timeout=10
            )
            return resp.json().get("results", [])
        except Exception as e:
            return []
    
    # =========================================
    # STATS
    # =========================================
    
    def get_hub_stats(self) -> Dict:
        """Get Hub's collection statistics."""
        try:
            resp = self.session.get(f"{self.base_url}/stats", timeout=10)
            return resp.json()
        except Exception as e:
            return {"error": str(e)}


# Singleton instance
_client: Optional[BDHubClient] = None

def get_hub_client() -> BDHubClient:
    """Get or create singleton Hub client."""
    global _client
    if _client is None:
        _client = BDHubClient()
    return _client


# CLI for testing
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Hub Client')
    parser.add_argument('--search', help='Search query')
    parser.add_argument('--ask', help='Ask question (smart routing)')
    parser.add_argument('--stats', action='store_true', help='Get Hub stats')
    
    args = parser.parse_args()
    
    client = get_hub_client()
    
    if args.search:
        results = client.search(args.search)
        print(f"Search results: {results}")
    
    if args.ask:
        results = client.smart_ask(args.ask)
        print(f"Answer: {results}")
    
    if args.stats:
        stats = client.get_hub_stats()
        print(f"Hub stats: {stats}")
```

---

## Phase 2: Update Scrapers to Write to Hub

### 2.1 Modify Job Scraper Pipeline
**Modify file:** `scripts/knowledge/index_files.py` or wherever jobs are processed

Add at the end of job processing:
```python
from scripts.hub_client import get_hub_client

def send_jobs_to_hub(jobs: List[Dict]):
    """Send processed jobs to the Hub."""
    client = get_hub_client()
    
    # Transform to Hub format if needed
    hub_jobs = []
    for job in jobs:
        hub_jobs.append({
            "title": job.get("job_title") or job.get("title"),
            "company": job.get("company"),
            "location": job.get("location"),
            "clearance": job.get("clearance"),
            "program_name": job.get("program_name") or job.get("mapped_program"),
            "bd_score": job.get("bd_score", 0),
            "bd_priority": job.get("bd_priority", "research"),
            "source": job.get("source", "data-scraper"),
            "url": job.get("url"),
        })
    
    result = client.ingest_jobs(hub_jobs)
    print(f"Hub ingestion: {result.message}")
    return result
```

### 2.2 Create Contact Sync Script
**Create file:** `scripts/sync_to_hub.py`

```python
"""
Sync local Data-Scraper data to the BD Intelligence Hub
Run this to migrate existing data or after batch scrapes
"""

import sqlite3
import json
from pathlib import Path
from scripts.hub_client import get_hub_client

DB_PATH = Path("knowledge/_index/knowledge.db")


def sync_contacts_to_hub(limit: int = None):
    """Sync contacts from local SQLite to Hub."""
    client = get_hub_client()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    query = """
        SELECT contact_id, full_name, title, company, location, 
               clearance, programs, email, phone, source
        FROM contacts
        WHERE is_active = 1
    """
    if limit:
        query += f" LIMIT {limit}"
    
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    
    contacts = []
    for row in rows:
        contacts.append({
            "id": row[0],
            "name": row[1],
            "title": row[2],
            "company": row[3],
            "location": row[4],
            "clearance": row[5],
            "program": row[6],
            "email": row[7],
            "phone": row[8],
            "source": row[9] or "data-scraper"
        })
    
    print(f"Syncing {len(contacts)} contacts to Hub...")
    
    # Send in batches
    batch_size = 100
    for i in range(0, len(contacts), batch_size):
        batch = contacts[i:i + batch_size]
        result = client.ingest_contacts(batch)
        print(f"  Batch {i//batch_size + 1}: {result.message}")
    
    return len(contacts)


def sync_programs_to_hub(limit: int = None):
    """Sync programs from local SQLite to Hub."""
    client = get_hub_client()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    query = """
        SELECT program_id, program_name, primes, agency, 
               locations, total_jobs, bd_status
        FROM programs
    """
    if limit:
        query += f" LIMIT {limit}"
    
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    
    programs = []
    for row in rows:
        programs.append({
            "id": row[0],
            "name": row[1],
            "prime_contractor": row[2],
            "agency": row[3],
            "location": row[4],
            "total_jobs": row[5],
            "status": row[6] or "research"
        })
    
    print(f"Syncing {len(programs)} programs to Hub...")
    result = client.ingest_programs(programs)
    print(f"Result: {result.message}")
    
    return len(programs)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Sync to Hub')
    parser.add_argument('--contacts', action='store_true', help='Sync contacts')
    parser.add_argument('--programs', action='store_true', help='Sync programs')
    parser.add_argument('--all', action='store_true', help='Sync everything')
    parser.add_argument('--limit', type=int, help='Limit records')
    
    args = parser.parse_args()
    
    if args.all or args.contacts:
        sync_contacts_to_hub(args.limit)
    
    if args.all or args.programs:
        sync_programs_to_hub(args.limit)
```

---

## Phase 3: Update MCP Server to Use Hub

### 3.1 Modify MCP Server
**Modify file:** `scripts/knowledge/mcp_server_stdio.py`

Add Hub client import at the top:
```python
from scripts.hub_client import get_hub_client, BDHubClient
```

Add new tool for Hub queries:
```python
# Add to TOOLS list:
{
    "name": "hub_smart_ask",
    "description": "Ask the BD Intelligence Hub using intelligent routing. Best for complex questions about programs, contacts, relationships.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "Question to ask the Hub"
            }
        },
        "required": ["question"]
    }
},
{
    "name": "hub_search",
    "description": "Search the unified BD Intelligence Hub knowledge base",
    "inputSchema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query"
            },
            "collection": {
                "type": "string",
                "enum": ["jobs", "contacts", "programs", "documents", "activities"],
                "description": "Collection to search (optional)"
            },
            "limit": {
                "type": "integer",
                "default": 10
            }
        },
        "required": ["query"]
    }
}
```

Add handlers:
```python
def hub_smart_ask(question: str) -> dict:
    """Ask the Hub using smart routing."""
    client = get_hub_client()
    return client.smart_ask(question)

def hub_search(query: str, collection: str = None, limit: int = 10) -> dict:
    """Search the Hub."""
    client = get_hub_client()
    return client.search(query, collection, limit)

# Add to tools_map in handle_tool_call:
"hub_smart_ask": lambda **args: hub_smart_ask(args.get("question", "")),
"hub_search": lambda **args: hub_search(
    args.get("query", ""),
    args.get("collection"),
    args.get("limit", 10)
),
```

---

## ✅ Data-Scraper Verification Checklist

```bash
cd "C:\data-scraper\data-scraper"

# 1. Ensure Hub is running first
curl http://localhost:8100/health

# 2. Test Hub client
python scripts/hub_client.py --stats
python scripts/hub_client.py --search "DCGS"
python scripts/hub_client.py --ask "Who are the key contacts at Leidos?"

# 3. Sync existing data to Hub
python scripts/sync_to_hub.py --contacts --limit 100
python scripts/sync_to_hub.py --programs

# 4. Verify data in Hub
curl "http://localhost:8100/stats"
```

---

# ═══════════════════════════════════════════════════════════════
# SECTION 3: N8N BUILDER (ORCHESTRATOR)
# Path: C:\N8N Builder
# ═══════════════════════════════════════════════════════════════

## 🎯 N8N Builder Responsibilities

This project becomes an **ORCHESTRATOR** that:
1. Builds n8n workflows that call Hub's MCP tools
2. Processes documents and sends to Hub
3. Uses Hub for all BD intelligence queries
4. Keeps local LanceDB for n8n-specific docs only (optional)

## Current State

| Component | Status | Details |
|-----------|--------|---------|
| LanceDB | ✅ | 3,319 chunks (n8n docs) |
| MCP Server | ✅ | 14 tools in `src/knowledge_base/mcp_server.py` |
| Document Processor | ✅ | PDF/DOCX processing |
| File Categorizer | ✅ | Domain tagging |

## Phase 1: Add Hub MCP Config

### 1.1 Update .mcp.json
**Modify file:** `.mcp.json`

Add the Hub MCP server:
```json
{
  "mcpServers": {
    "n8n-mcp": {
      "command": "npx",
      "args": ["-y", "n8n-mcp"],
      "env": {
        "N8N_API_URL": "https://primetech.app.n8n.cloud",
        "N8N_API_KEY": "..."
      }
    },
    "bd-intelligence-hub": {
      "command": "node",
      "args": ["C:/Users/gtmar/Projects/Auto-Claude/BD-Automation-Engine/mcp/knowledge-mcp-server/build/index.js"],
      "timeout": 300000,
      "env": {
        "KNOWLEDGE_API_URL": "http://127.0.0.1:8100"
      },
      "description": "BD Intelligence Hub - unified search, memory, knowledge graph"
    },
    "knowledge-base": {
      "command": "python",
      "args": ["-m", "src.knowledge_base.mcp_server"],
      "cwd": "C:\\N8N Builder",
      "description": "Local n8n docs only"
    }
  }
}
```

---

## Phase 2: Create Hub Integration

### 2.1 Create Hub Client
**Create file:** `src/hub_client.py`

```python
"""
BD Intelligence Hub Client for N8N Builder
Use this for all BD intelligence queries instead of local search
"""

import os
import requests
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger('HubClient')

HUB_API_URL = os.getenv("BD_HUB_API_URL", "http://127.0.0.1:8100")


class BDHubClient:
    """Client for BD Intelligence Hub API."""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or HUB_API_URL
        self.session = requests.Session()
        self.source = "n8n-builder"
    
    def smart_ask(self, question: str) -> Dict:
        """Ask using intelligent routing."""
        try:
            resp = self.session.get(
                f"{self.base_url}/ask/smart",
                params={"q": question},
                timeout=60
            )
            return resp.json()
        except Exception as e:
            return {"error": str(e)}
    
    def search(self, query: str, collection: str = None, limit: int = 10) -> Dict:
        """Search Hub's knowledge base."""
        try:
            params = {"query": query, "limit": limit}
            if collection:
                params["collection"] = collection
            resp = self.session.post(
                f"{self.base_url}/search",
                json=params,
                timeout=30
            )
            return resp.json()
        except Exception as e:
            return {"error": str(e)}
    
    def query_knowledge_graph(self, query: str, mode: str = "hybrid") -> Dict:
        """Query knowledge graph for relationships."""
        try:
            resp = self.session.post(
                f"{self.base_url}/lightrag/query",
                json={"query": query, "mode": mode},
                timeout=60
            )
            return resp.json()
        except Exception as e:
            return {"error": str(e)}
    
    def add_memory(self, content: str, metadata: Dict = None) -> Dict:
        """Add to Hub's unified memory."""
        try:
            resp = self.session.post(
                f"{self.base_url}/memory/add",
                json={
                    "content": content,
                    "metadata": metadata,
                    "source_project": self.source
                },
                timeout=10
            )
            return resp.json()
        except Exception as e:
            return {"error": str(e)}
    
    def search_memory(self, query: str, limit: int = 10) -> List[Dict]:
        """Search Hub's memory."""
        try:
            resp = self.session.post(
                f"{self.base_url}/memory/search",
                json={"query": query, "limit": limit},
                timeout=10
            )
            return resp.json().get("results", [])
        except Exception as e:
            return []
    
    def get_program_intel(self, program_name: str) -> Dict:
        """Get full program intelligence report."""
        try:
            resp = self.session.get(
                f"{self.base_url}/program/{program_name}",
                timeout=30
            )
            return resp.json()
        except Exception as e:
            return {"error": str(e)}
    
    def get_company_contacts(self, company_name: str, limit: int = 20) -> Dict:
        """Get contacts at a company."""
        try:
            resp = self.session.get(
                f"{self.base_url}/contacts/at/{company_name}",
                params={"limit": limit},
                timeout=30
            )
            return resp.json()
        except Exception as e:
            return {"error": str(e)}


# Singleton
_client: Optional[BDHubClient] = None

def get_hub_client() -> BDHubClient:
    global _client
    if _client is None:
        _client = BDHubClient()
    return _client
```

### 2.2 Add Hub Tools to MCP Server
**Modify file:** `src/knowledge_base/mcp_server.py`

Add import:
```python
from src.hub_client import get_hub_client
```

Add new tools to `_list_tools`:
```python
{
    'name': 'hub_ask',
    'description': 'Ask the BD Intelligence Hub (smart routing to best RAG system)',
    'inputSchema': {
        'type': 'object',
        'properties': {
            'question': {
                'type': 'string',
                'description': 'Question about BD intelligence, programs, contacts, etc.'
            }
        },
        'required': ['question']
    }
},
{
    'name': 'hub_search',
    'description': 'Search BD Intelligence Hub for jobs, contacts, programs',
    'inputSchema': {
        'type': 'object',
        'properties': {
            'query': {'type': 'string'},
            'collection': {
                'type': 'string',
                'enum': ['jobs', 'contacts', 'programs', 'documents', 'activities']
            },
            'limit': {'type': 'integer', 'default': 10}
        },
        'required': ['query']
    }
},
{
    'name': 'hub_program_intel',
    'description': 'Get comprehensive intelligence report for a federal program',
    'inputSchema': {
        'type': 'object',
        'properties': {
            'program_name': {'type': 'string'}
        },
        'required': ['program_name']
    }
},
{
    'name': 'hub_company_contacts',
    'description': 'Find contacts at a specific company',
    'inputSchema': {
        'type': 'object',
        'properties': {
            'company_name': {'type': 'string'},
            'limit': {'type': 'integer', 'default': 20}
        },
        'required': ['company_name']
    }
}
```

Add handlers:
```python
def _tool_hub_ask(self, args: dict) -> dict:
    client = get_hub_client()
    return client.smart_ask(args.get('question', ''))

def _tool_hub_search(self, args: dict) -> dict:
    client = get_hub_client()
    return client.search(
        args.get('query', ''),
        args.get('collection'),
        args.get('limit', 10)
    )

def _tool_hub_program_intel(self, args: dict) -> dict:
    client = get_hub_client()
    return client.get_program_intel(args.get('program_name', ''))

def _tool_hub_company_contacts(self, args: dict) -> dict:
    client = get_hub_client()
    return client.get_company_contacts(
        args.get('company_name', ''),
        args.get('limit', 20)
    )
```

Add to handlers dict in `_call_tool`:
```python
'hub_ask': self._tool_hub_ask,
'hub_search': self._tool_hub_search,
'hub_program_intel': self._tool_hub_program_intel,
'hub_company_contacts': self._tool_hub_company_contacts,
```

---

## ✅ N8N Builder Verification Checklist

```bash
cd "C:\N8N Builder"

# 1. Ensure Hub is running
curl http://localhost:8100/health

# 2. Test Hub client
python -c "from src.hub_client import get_hub_client; c = get_hub_client(); print(c.smart_ask('Who works on DCGS?'))"

# 3. Test MCP server with new tools
python -m src.knowledge_base.mcp_server --list-tools | grep hub_

# 4. Test in Claude Code (after restarting)
# The hub_ask, hub_search tools should be available
```

---

# ═══════════════════════════════════════════════════════════════
# SECTION 4: FINAL MERGE & CONSOLIDATION
# (Run after all projects are updated)
# ═══════════════════════════════════════════════════════════════

## Post-Implementation Tasks

### 1. Sync All Existing Data to Hub

```bash
# From Data-Scraper - sync contacts and programs
cd "C:\data-scraper\data-scraper"
python scripts/sync_to_hub.py --all

# Verify in Hub
curl "http://localhost:8100/stats"
```

### 2. Build Knowledge Graph

```bash
# From BD-Automation-Engine
cd "C:\Users\gtmar\Projects\Auto-Claude\BD-Automation-Engine"
python Engine8_Knowledge/scripts/build_knowledge_graph.py
```

### 3. Test Cross-Project Queries

```bash
# Test that N8N Builder can query Data-Scraper's contacts through Hub
cd "C:\N8N Builder"
python -c "
from src.hub_client import get_hub_client
client = get_hub_client()
print(client.smart_ask('Find TS/SCI cleared analysts at Leidos working on DCGS'))
"
```

### 4. Update CLAUDE.md Files

Each project's CLAUDE.md should be updated to reference the Hub:

**BD-Automation-Engine/CLAUDE.md** - Add:
```markdown
## BD Intelligence Hub

This project IS the central BD Intelligence Hub. All other projects (Data-Scraper, N8N Builder) connect here.

### Starting the Hub
```bash
python Engine8_Knowledge/api.py
```

### Hub Capabilities
- Unified Qdrant vector store (all jobs, contacts, programs)
- Mem0 memory layer (cross-session context)
- LightRAG knowledge graph (entity relationships)
- Hybrid retriever (semantic + BM25 + RRF)
- Smart query routing
- 30+ MCP tools
```

**Data-Scraper CLAUDE.md** - Add:
```markdown
## Hub Integration

This project writes data to the BD Intelligence Hub. Do NOT store data locally.

### Ingesting Data
```python
from scripts.hub_client import get_hub_client
client = get_hub_client()
client.ingest_jobs(jobs_list)
client.ingest_contacts(contacts_list)
```

### Querying Data
```python
client.smart_ask("Find contacts at Leidos")
client.search("DCGS", collection="jobs")
```
```

**N8N Builder CLAUDE.md** - Add:
```markdown
## Hub Integration

For BD intelligence queries, use the Hub instead of local search.

### MCP Tools
- `hub_ask` - Smart query routing
- `hub_search` - Search Hub collections
- `hub_program_intel` - Full program report
- `hub_company_contacts` - Find contacts at company

### Python Client
```python
from src.hub_client import get_hub_client
client = get_hub_client()
result = client.smart_ask("Who works on DCGS at Leidos?")
```
```

---

## 📊 Final Architecture Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                    BD INTELLIGENCE HUB                          │
│              (BD-Automation-Engine @ :8100)                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  UNIFIED STORAGE                                         │   │
│  │  ├── Qdrant: 15,000+ vectors (jobs+contacts+programs)   │   │
│  │  ├── Mem0: Cross-session memory (user=pts_bd_unified)   │   │
│  │  └── LightRAG: Entity relationship graph                │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  RETRIEVAL SYSTEMS                                       │   │
│  │  ├── Semantic: Qdrant embeddings                        │   │
│  │  ├── Keyword: BM25 indexing                             │   │
│  │  ├── Hybrid: Semantic + BM25 + RRF fusion               │   │
│  │  └── Graph: LightRAG local/global/hybrid                │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  INTERFACES                                              │   │
│  │  ├── FastAPI: REST endpoints @ :8100                    │   │
│  │  ├── MCP Server: 30+ tools for Claude Code              │   │
│  │  └── Query Router: Intelligent system selection         │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
         ▲                                    ▲
         │ WRITES                             │ READS
         │                                    │
┌────────┴────────┐                 ┌────────┴────────┐
│  DATA-SCRAPER   │                 │   N8N BUILDER   │
│                 │                 │                 │
│ • Apify scrapes │                 │ • n8n workflows │
│ • Job mapping   │                 │ • Document proc │
│ • Contact ETL   │                 │ • Automation    │
│                 │                 │                 │
│ hub_client.py   │                 │ hub_client.py   │
│ sync_to_hub.py  │                 │ hub_* MCP tools │
└─────────────────┘                 └─────────────────┘
```

---

## 🚀 Quick Start Commands

```bash
# 1. Start the Hub (must be first)
cd "C:\Users\gtmar\Projects\Auto-Claude\BD-Automation-Engine"
python Engine8_Knowledge/api.py

# 2. In another terminal - Sync Data-Scraper data
cd "C:\data-scraper\data-scraper"
python scripts/sync_to_hub.py --all

# 3. Build Knowledge Graph
cd "C:\Users\gtmar\Projects\Auto-Claude\BD-Automation-Engine"
python Engine8_Knowledge/scripts/build_knowledge_graph.py

# 4. Test from any project
curl "http://localhost:8100/ask/smart?q=Find%20DCGS%20contacts%20at%20Leidos"
```

---

## ✅ Master Verification Checklist

### Hub (BD-Automation-Engine)
- [ ] FastAPI running on :8100
- [ ] `/health` returns 200
- [ ] `/stats` shows all collections
- [ ] `/ask/smart` returns routed results
- [ ] `/memory/add` and `/memory/search` work
- [ ] `/lightrag/query` returns graph results
- [ ] MCP server has 30+ tools

### Data-Scraper
- [ ] `hub_client.py` can connect to Hub
- [ ] `sync_to_hub.py --all` succeeds
- [ ] MCP server has `hub_smart_ask` tool
- [ ] New scrapes automatically write to Hub

### N8N Builder
- [ ] `hub_client.py` can connect to Hub
- [ ] MCP server has `hub_ask`, `hub_search` tools
- [ ] `.mcp.json` includes `bd-intelligence-hub` server
- [ ] Can query BD data from n8n workflow context

---

**END OF UNIFIED BUILD PLAN**
