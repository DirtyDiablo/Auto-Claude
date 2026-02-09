"""
LightRAG wrapper for BD Intelligence Hub.
Provides graph-based reasoning on top of existing Qdrant vectors.
"""
import os
import asyncio
from enum import Enum
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from pathlib import Path

from lightrag import LightRAG, QueryParam
from utils.llm_retry import anthropic_retry
import structlog

logger = structlog.get_logger(__name__)


class QueryMode(str, Enum):
    """Query modes for LightRAG."""
    LOCAL = "local"      # Focus on specific entities
    GLOBAL = "global"    # High-level summaries
    HYBRID = "hybrid"    # Combined local + global
    NAIVE = "naive"      # Simple vector search


@dataclass
class QueryResult:
    """Result from a LightRAG query."""
    query: str
    mode: QueryMode
    answer: str
    entities_found: List[str]
    relationships: List[Dict]
    sources: List[str]


class BDGraphRAG:
    """
    BD-specific LightRAG integration with graph-based reasoning.
    Enables relationship-aware retrieval for contractor teaming and program connections.
    """

    def __init__(
        self,
        working_dir: str = None,
        use_qdrant: bool = False,
        qdrant_url: str = "http://localhost:6333",
        llm_provider: str = "openai",  # "openai", "anthropic", or "ollama"
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        """
        Initialize BDGraphRAG.

        Args:
            working_dir: Directory for LightRAG data storage
            use_qdrant: Whether to use Qdrant for vector storage
            qdrant_url: URL for Qdrant server (if use_qdrant=True)
            llm_provider: LLM provider for entity extraction
            embedding_model: Sentence transformer model for embeddings
        """
        # Set working directory
        if working_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            working_dir = os.path.join(base_dir, "data", "lightrag")

        self.working_dir = working_dir
        Path(working_dir).mkdir(parents=True, exist_ok=True)

        # Configure storage
        vector_storage = "QdrantVectorDBStorage" if use_qdrant else "NanoVectorDBStorage"

        # Configure vector storage kwargs for Qdrant
        vector_db_kwargs = {}
        if use_qdrant:
            vector_db_kwargs = {
                "url": qdrant_url,
                "collection_name": "bd_lightrag"
            }

        # Get LLM and embedding functions
        llm_func = self._get_llm_func(llm_provider)
        embedding_func = self._get_embedding_func(embedding_model)

        # Initialize LightRAG
        self.rag = LightRAG(
            working_dir=working_dir,
            vector_storage=vector_storage,
            vector_db_storage_cls_kwargs=vector_db_kwargs,
            llm_model_func=llm_func,
            embedding_func=embedding_func,
            chunk_token_size=1200,
            chunk_overlap_token_size=100,
            entity_extract_max_gleaning=1,
            top_k=20,
            cosine_threshold=0.2
        )

        self.llm_provider = llm_provider
        self._initialized = False  # Will be True after async init
        self._storage_initialized = False

    async def initialize(self):
        """Initialize async storages. Must be called before use."""
        # Debug to file
        import os
        debug_file = os.path.join(self.working_dir, "debug_init.log")
        with open(debug_file, "a") as f:
            f.write(f"[{__import__('datetime').datetime.now()}] initialize() called, _storage_initialized: {self._storage_initialized}\n")

        if not self._storage_initialized:
            try:
                with open(debug_file, "a") as f:
                    f.write(f"[{__import__('datetime').datetime.now()}] Calling rag.initialize_storages()...\n")

                await self.rag.initialize_storages()
                self._storage_initialized = True
                self._initialized = True

                with open(debug_file, "a") as f:
                    f.write(f"[{__import__('datetime').datetime.now()}] LightRAG storages initialized OK\n")
            except Exception as e:
                with open(debug_file, "a") as f:
                    f.write(f"[{__import__('datetime').datetime.now()}] ERROR: {e}\n")
                    import traceback
                    f.write(traceback.format_exc())
                raise

    def _get_llm_func(self, provider: str):
        """Get LLM function based on provider."""
        from functools import partial

        if provider == "openai":
            from lightrag.llm.openai import openai_complete_if_cache
            # Must use partial to pre-bind model name
            return partial(openai_complete_if_cache, "gpt-4o-mini")
        elif provider == "anthropic":
            # Custom Anthropic wrapper
            return self._anthropic_complete
        elif provider == "ollama":
            from lightrag.llm.ollama import ollama_model_complete
            return partial(ollama_model_complete, "llama3.2")
        else:
            # Fallback to OpenAI
            from lightrag.llm.openai import openai_complete_if_cache
            return partial(openai_complete_if_cache, "gpt-4o-mini")

    def _get_embedding_func(self, model_name: str):
        """Get embedding function using sentence-transformers."""
        try:
            import numpy as np
            from sentence_transformers import SentenceTransformer
            from lightrag.base import EmbeddingFunc

            model = SentenceTransformer(model_name)
            embedding_dim = model.get_sentence_embedding_dimension()

            async def embed_texts(texts: List[str]):
                embeddings = model.encode(texts, convert_to_numpy=True)
                return np.array(embeddings)  # Return numpy array, not list

            return EmbeddingFunc(
                embedding_dim=embedding_dim,
                func=embed_texts,
                max_token_size=8192,
                model_name=model_name
            )
        except Exception as e:
            logger.warning("embedding_function_creation_failed", error=str(e))
            # Return None - LightRAG will fail but we'll handle in caller
            return None

    @anthropic_retry
    async def _anthropic_complete(
        self,
        prompt: str,
        system_prompt: str = None,
        history_messages: List = None,
        **kwargs
    ) -> str:
        """Anthropic completion function for LightRAG."""
        try:
            import anthropic
            client = anthropic.Anthropic()

            messages = []
            if history_messages:
                messages.extend(history_messages)
            messages.append({"role": "user", "content": prompt})

            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=2000,
                system=system_prompt or "You are a helpful assistant for knowledge extraction.",
                messages=messages
            )
            return response.content[0].text
        except Exception as e:
            logger.warning("anthropic_completion_failed", error=str(e))
            return ""

    async def insert_documents(self, documents: List[str], metadata: List[Dict] = None) -> Dict:
        """
        Incrementally add documents with entity extraction.

        Args:
            documents: List of document texts
            metadata: Optional metadata for each document

        Returns:
            Dict with insertion stats
        """
        # Debug to file
        import os
        debug_file = os.path.join(self.working_dir, "debug_insert.log")
        with open(debug_file, "a") as f:
            f.write(f"[{__import__('datetime').datetime.now()}] insert_documents called, _storage_initialized: {self._storage_initialized}\n")

        # Ensure storages are initialized before inserting
        if not self._storage_initialized:
            with open(debug_file, "a") as f:
                f.write(f"[{__import__('datetime').datetime.now()}] Calling initialize from insert_documents...\n")
            await self.initialize()
            with open(debug_file, "a") as f:
                f.write(f"[{__import__('datetime').datetime.now()}] After initialize, _storage_initialized: {self._storage_initialized}\n")

        inserted = 0
        errors = []

        for i, doc in enumerate(documents):
            try:
                # Add metadata as prefix if provided
                if metadata and i < len(metadata):
                    meta = metadata[i]
                    prefix = f"[Source: {meta.get('source', 'unknown')}] "
                    if meta.get('program'):
                        prefix += f"[Program: {meta['program']}] "
                    if meta.get('contractor'):
                        prefix += f"[Contractor: {meta['contractor']}] "
                    doc = prefix + doc

                await self.rag.ainsert(doc)
                inserted += 1
            except Exception as e:
                errors.append({"doc_index": i, "error": str(e)})

        return {
            "documents_inserted": inserted,
            "errors": errors,
            "total_submitted": len(documents)
        }

    def insert_documents_sync(self, documents: List[str], metadata: List[Dict] = None) -> Dict:
        """Synchronous wrapper for insert_documents."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Running in async context, use nest_asyncio or run in thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.insert_documents(documents, metadata))
                    return future.result()
            else:
                return loop.run_until_complete(self.insert_documents(documents, metadata))
        except RuntimeError:
            return asyncio.run(self.insert_documents(documents, metadata))

    async def query(self, query: str, mode: QueryMode = QueryMode.HYBRID) -> QueryResult:
        """
        Query the graph RAG with specified mode.

        Args:
            query: Natural language query
            mode: Query mode (local, global, hybrid, naive)

        Returns:
            QueryResult with answer and metadata
        """
        try:
            param = QueryParam(mode=mode.value)
            result = await self.rag.aquery(query, param=param)

            # Extract entities and relationships from result
            entities = self._extract_entities_from_result(result)
            relationships = self._extract_relationships_from_result(result)
            sources = self._extract_sources_from_result(result)

            return QueryResult(
                query=query,
                mode=mode,
                answer=result,
                entities_found=entities,
                relationships=relationships,
                sources=sources
            )
        except Exception as e:
            return QueryResult(
                query=query,
                mode=mode,
                answer=f"Query failed: {str(e)}",
                entities_found=[],
                relationships=[],
                sources=[]
            )

    def query_sync(self, query: str, mode: QueryMode = QueryMode.HYBRID) -> QueryResult:
        """Synchronous wrapper for query."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.query(query, mode))
                    return future.result()
            else:
                return loop.run_until_complete(self.query(query, mode))
        except RuntimeError:
            return asyncio.run(self.query(query, mode))

    async def query_local(self, query: str) -> str:
        """Query focusing on specific entities."""
        result = await self.query(query, QueryMode.LOCAL)
        return result.answer

    async def query_global(self, query: str) -> str:
        """Query for high-level summaries."""
        result = await self.query(query, QueryMode.GLOBAL)
        return result.answer

    async def query_hybrid(self, query: str) -> str:
        """Combined local + global reasoning."""
        result = await self.query(query, QueryMode.HYBRID)
        return result.answer

    def get_entity_graph(self, entity_name: str) -> Dict:
        """
        Get relationship graph for a specific entity.

        Args:
            entity_name: Name of entity to look up

        Returns:
            Dict with entity info and relationships
        """
        try:
            # Access the graph storage directly
            if hasattr(self.rag, '_graph_storage') and self.rag._graph_storage:
                graph = self.rag._graph_storage
                # Get entity data
                entity_data = graph.get_node(entity_name) if hasattr(graph, 'get_node') else None

                # Get relationships
                relationships = []
                if hasattr(graph, 'get_edges'):
                    edges = graph.get_edges(entity_name)
                    relationships = [{"source": e[0], "target": e[1], "type": e.get("type", "related")} for e in edges]

                return {
                    "entity": entity_name,
                    "data": entity_data,
                    "relationships": relationships,
                    "found": entity_data is not None
                }
        except Exception as e:
            pass

        # Fallback: query for entity info
        query_result = self.query_sync(f"What do we know about {entity_name}?", QueryMode.LOCAL)
        return {
            "entity": entity_name,
            "data": {"description": query_result.answer},
            "relationships": query_result.relationships,
            "found": len(query_result.answer) > 0
        }

    def get_contractor_relationships(self, contractor_name: str = None) -> List[Dict]:
        """
        Get contractor teaming relationships.

        Args:
            contractor_name: Specific contractor or None for all

        Returns:
            List of contractor relationships
        """
        if contractor_name:
            query = f"What programs and teaming relationships does {contractor_name} have?"
        else:
            query = "What are the major contractor teaming relationships in defense programs?"

        result = self.query_sync(query, QueryMode.GLOBAL)
        return result.relationships or [{"summary": result.answer}]

    def get_program_contractors(self, program_name: str) -> Dict:
        """
        Get contractors associated with a program.

        Args:
            program_name: Name of the program

        Returns:
            Dict with program info and contractors
        """
        result = self.query_sync(
            f"Who are the contractors working on {program_name}? Include prime and subcontractors.",
            QueryMode.HYBRID
        )
        return {
            "program": program_name,
            "answer": result.answer,
            "contractors": result.entities_found,
            "relationships": result.relationships
        }

    def find_teaming_path(self, contractor1: str, contractor2: str) -> Dict:
        """
        Find relationship path between two contractors.

        Args:
            contractor1: First contractor
            contractor2: Second contractor

        Returns:
            Dict with teaming path information
        """
        result = self.query_sync(
            f"How are {contractor1} and {contractor2} connected? What programs do they work on together?",
            QueryMode.HYBRID
        )
        return {
            "from": contractor1,
            "to": contractor2,
            "answer": result.answer,
            "shared_programs": result.entities_found,
            "relationships": result.relationships
        }

    def _extract_entities_from_result(self, result: str) -> List[str]:
        """Extract entity names mentioned in result."""
        # Known BD entities to look for
        bd_entities = [
            "GDIT", "General Dynamics", "Leidos", "SAIC", "Northrop Grumman",
            "Raytheon", "Lockheed Martin", "BAE Systems", "Booz Allen",
            "AF DCGS", "DCGS", "BICES", "GSM-O", "GBSD", "ABMS",
            "Langley", "San Diego", "Norfolk", "Fort Meade",
            "ISR", "SIGINT", "Cyber", "C4ISR"
        ]

        found = []
        result_lower = result.lower()
        for entity in bd_entities:
            if entity.lower() in result_lower:
                found.append(entity)
        return found

    def _extract_relationships_from_result(self, result: str) -> List[Dict]:
        """Extract relationship mentions from result."""
        relationships = []
        # Look for relationship patterns
        patterns = [
            ("prime contractor", "primes"),
            ("subcontractor", "subs"),
            ("teaming", "teams_with"),
            ("partner", "partners_with"),
            ("works on", "works_on"),
            ("supports", "supports")
        ]

        for pattern, rel_type in patterns:
            if pattern.lower() in result.lower():
                relationships.append({"type": rel_type, "mentioned": True})

        return relationships

    def _extract_sources_from_result(self, result: str) -> List[str]:
        """Extract source references from result."""
        sources = []
        # Look for source markers
        if "[Source:" in result:
            import re
            matches = re.findall(r'\[Source:\s*([^\]]+)\]', result)
            sources.extend(matches)
        return sources

    def stats(self) -> Dict:
        """Get statistics about the graph RAG."""
        try:
            stats = {
                "working_dir": self.working_dir,
                "llm_provider": self.llm_provider,
                "initialized": self._initialized
            }

            # Try to get storage stats
            if hasattr(self.rag, '_graph_storage') and self.rag._graph_storage:
                if hasattr(self.rag._graph_storage, 'get_statistics'):
                    stats["graph"] = self.rag._graph_storage.get_statistics()

            return stats
        except Exception as e:
            return {"error": str(e), "initialized": self._initialized}
