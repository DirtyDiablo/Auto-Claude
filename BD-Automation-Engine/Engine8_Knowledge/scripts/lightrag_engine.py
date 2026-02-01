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
    from lightrag.llm.anthropic import anthropic_complete
    from lightrag.utils import EmbeddingFunc
    LIGHTRAG_AVAILABLE = True
except ImportError as e:
    LIGHTRAG_AVAILABLE = False
    logger.warning(f"LightRAG not available, using fallback: {e}")


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
