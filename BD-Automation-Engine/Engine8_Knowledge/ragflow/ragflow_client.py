"""
RAGflow Client - Async client for RAGflow API interactions.

RAGflow is an open-source RAG engine with deep document parsing,
knowledge graph construction, and citation-backed responses.

Base URL: http://localhost:80/api (default Docker setup)
"""

import os
import asyncio
import structlog
from pathlib import Path
from typing import Dict, List, Optional, Any, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum

import httpx

logger = structlog.get_logger(__name__)


class ChunkMethod(str, Enum):
    """Document chunking methods supported by RAGflow."""
    NAIVE = "naive"           # Simple text splitting
    QA = "qa"                 # Q&A format extraction
    TABLE = "table"           # Table-aware parsing
    PAPER = "paper"           # Academic paper structure
    BOOK = "book"             # Book/chapter structure
    LAWS = "laws"             # Legal document structure
    PRESENTATION = "presentation"  # Slide-based content
    MANUAL = "manual"         # Technical manual format
    ONE = "one"               # Single chunk (small docs)


class DocumentStatus(str, Enum):
    """Document processing status in RAGflow."""
    PENDING = "pending"
    PARSING = "parsing"
    PARSED = "parsed"
    FAILED = "failed"
    CANCELED = "canceled"


@dataclass
class RAGflowConfig:
    """Configuration for RAGflow client."""
    api_key: str
    base_url: str = "http://localhost"
    llm_model: str = "gpt-4o"
    embedding_model: str = "BAAI/bge-large-en-v1.5"
    timeout: float = 300.0
    max_retries: int = 3

    @classmethod
    def from_env(cls) -> "RAGflowConfig":
        """Create config from environment variables."""
        return cls(
            api_key=os.getenv("RAGFLOW_API_KEY", ""),
            base_url=os.getenv("RAGFLOW_BASE_URL", "http://localhost"),
            llm_model=os.getenv("RAGFLOW_LLM_MODEL", "gpt-4o"),
            embedding_model=os.getenv("RAGFLOW_EMBEDDING_MODEL", "BAAI/bge-large-en-v1.5"),
        )


@dataclass
class QueryResult:
    """Result from a RAGflow query."""
    chunks: List[Dict[str, Any]] = field(default_factory=list)
    answer: Optional[str] = None
    citations: List[Dict[str, Any]] = field(default_factory=list)
    query_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunks": self.chunks,
            "answer": self.answer,
            "citations": self.citations,
            "query_time_ms": self.query_time_ms
        }


class RAGflowClient:
    """
    Async client for RAGflow API interactions.

    Features:
    - Knowledge base management (create, list, delete)
    - Document upload with automatic chunk method selection
    - Semantic search with hybrid (vector + BM25) support
    - GraphRAG for relationship-aware queries
    - Chat sessions with citation tracking

    Example:
        client = RAGflowClient(config)
        await client.initialize()

        # Create knowledge base
        kb_id = await client.create_knowledge_base("bd_playbooks", "BD strategy docs")

        # Upload documents
        doc_id = await client.upload_document(kb_id, "playbook.pdf", ChunkMethod.BOOK)

        # Query with citations
        result = await client.query([kb_id], "What is our DCGS strategy?")
        print(result.answer)
        for citation in result.citations:
            print(f"  - {citation['doc_name']} p.{citation['page']}")
    """

    def __init__(self, config: Optional[RAGflowConfig] = None):
        self.config = config or RAGflowConfig.from_env()
        self._client: Optional[httpx.AsyncClient] = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the HTTP client."""
        if self._initialized:
            return

        self._client = httpx.AsyncClient(
            timeout=self.config.timeout,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            },
            base_url=f"{self.config.base_url}/api/v1"
        )
        self._initialized = True
        logger.info("ragflow_client_initialized", base_url=self.config.base_url)

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
            self._initialized = False

    async def __aenter__(self) -> "RAGflowClient":
        await self.initialize()
        return self

    async def __aexit__(self, *args) -> None:
        await self.close()

    def _ensure_initialized(self) -> None:
        """Ensure client is initialized."""
        if not self._initialized or not self._client:
            raise RuntimeError("RAGflow client not initialized. Call initialize() first.")

    # =========================================================================
    # Health & Status
    # =========================================================================

    async def health_check(self) -> Dict[str, Any]:
        """Check RAGflow server health."""
        self._ensure_initialized()
        try:
            response = await self._client.get("/health")
            if response.status_code == 200:
                return {"status": "healthy", "data": response.json()}
            return {"status": "unhealthy", "code": response.status_code}
        except Exception as e:
            logger.error("health_check_failed", error=str(e))
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # Knowledge Base Management
    # =========================================================================

    async def create_knowledge_base(
        self,
        name: str,
        description: str = "",
        embedding_model: Optional[str] = None,
        permission: str = "me",
        chunk_method: ChunkMethod = ChunkMethod.NAIVE,
        parser_config: Optional[Dict] = None
    ) -> str:
        """
        Create a new knowledge base.

        Args:
            name: Unique name for the KB
            description: Description of KB contents
            embedding_model: Override default embedding model
            permission: Access level ("me", "team")
            chunk_method: Default chunking method for documents
            parser_config: Custom parser configuration

        Returns:
            kb_id: The created knowledge base ID
        """
        self._ensure_initialized()

        payload = {
            "name": name,
            "description": description,
            "embedding_model": embedding_model or self.config.embedding_model,
            "permission": permission,
            "chunk_method": chunk_method.value,
        }

        if parser_config:
            payload["parser_config"] = parser_config

        response = await self._client.post("/datasets", json=payload)
        response.raise_for_status()

        data = response.json()
        kb_id = data.get("data", {}).get("id") or data.get("id")
        logger.info("knowledge_base_created", name=name, kb_id=kb_id)
        return kb_id

    async def list_knowledge_bases(self) -> List[Dict[str, Any]]:
        """List all knowledge bases with stats."""
        self._ensure_initialized()

        response = await self._client.get("/datasets")
        response.raise_for_status()

        data = response.json()
        return data.get("data", [])

    async def get_knowledge_base(self, kb_id: str) -> Dict[str, Any]:
        """Get knowledge base details including document count."""
        self._ensure_initialized()

        response = await self._client.get(f"/datasets/{kb_id}")
        response.raise_for_status()

        return response.json().get("data", {})

    async def delete_knowledge_base(self, kb_id: str) -> bool:
        """Delete a knowledge base and all its documents."""
        self._ensure_initialized()

        response = await self._client.delete(f"/datasets/{kb_id}")
        success = response.status_code in (200, 204)

        if success:
            logger.info("knowledge_base_deleted", kb_id=kb_id)
        else:
            logger.warning("knowledge_base_delete_failed", kb_id=kb_id, status_code=response.status_code)

        return success

    async def get_or_create_knowledge_base(
        self,
        name: str,
        description: str = "",
        **kwargs
    ) -> str:
        """Get existing KB by name or create if not exists."""
        kbs = await self.list_knowledge_bases()

        for kb in kbs:
            if kb.get("name") == name:
                return kb.get("id")

        return await self.create_knowledge_base(name, description, **kwargs)

    # =========================================================================
    # Document Management
    # =========================================================================

    async def upload_document(
        self,
        kb_id: str,
        file_path: str,
        chunk_method: Optional[ChunkMethod] = None,
        run_immediately: bool = True
    ) -> str:
        """
        Upload a document to a knowledge base.

        Args:
            kb_id: Target knowledge base ID
            file_path: Path to the file to upload
            chunk_method: Override KB default chunk method
            run_immediately: Start parsing immediately

        Returns:
            doc_id: The uploaded document ID
        """
        self._ensure_initialized()

        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Determine content type
        content_types = {
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".doc": "application/msword",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".csv": "text/csv",
            ".txt": "text/plain",
            ".md": "text/markdown",
            ".html": "text/html",
            ".json": "application/json",
        }
        content_type = content_types.get(path.suffix.lower(), "application/octet-stream")

        # Build multipart form
        with open(file_path, "rb") as f:
            files = {"file": (path.name, f, content_type)}
            data = {"kb_id": kb_id}

            if chunk_method:
                data["chunk_method"] = chunk_method.value
            if run_immediately:
                data["run"] = "true"

            # Remove JSON content-type for multipart
            headers = {"Authorization": f"Bearer {self.config.api_key}"}

            response = await self._client.post(
                f"/datasets/{kb_id}/documents",
                files=files,
                data=data,
                headers=headers
            )

        response.raise_for_status()

        result = response.json()
        doc_id = result.get("data", {}).get("id") or result.get("id")
        logger.info("document_uploaded", filename=path.name, doc_id=doc_id)
        return doc_id

    async def upload_documents_batch(
        self,
        kb_id: str,
        file_paths: List[str],
        chunk_method: Optional[ChunkMethod] = None,
        max_concurrent: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Batch upload documents with parallel processing.

        Returns list of {file_path, doc_id, status, error?}
        """
        results = []
        semaphore = asyncio.Semaphore(max_concurrent)

        async def upload_one(file_path: str) -> Dict[str, Any]:
            async with semaphore:
                try:
                    doc_id = await self.upload_document(
                        kb_id, file_path, chunk_method
                    )
                    return {
                        "file_path": file_path,
                        "doc_id": doc_id,
                        "status": "uploaded"
                    }
                except Exception as e:
                    logger.error("document_upload_failed", file_path=file_path, error=str(e))
                    return {
                        "file_path": file_path,
                        "doc_id": None,
                        "status": "failed",
                        "error": str(e)
                    }

        tasks = [upload_one(fp) for fp in file_paths]
        results = await asyncio.gather(*tasks)

        success_count = sum(1 for r in results if r["status"] == "uploaded")
        logger.info("batch_upload_complete", succeeded=success_count, total=len(file_paths))

        return list(results)

    async def list_documents(self, kb_id: str) -> List[Dict[str, Any]]:
        """List all documents in a knowledge base with status."""
        self._ensure_initialized()

        response = await self._client.get(f"/datasets/{kb_id}/documents")
        response.raise_for_status()

        return response.json().get("data", [])

    async def get_document_status(self, kb_id: str, doc_id: str) -> DocumentStatus:
        """Get parsing status of a document."""
        self._ensure_initialized()

        response = await self._client.get(f"/datasets/{kb_id}/documents/{doc_id}")
        response.raise_for_status()

        status_str = response.json().get("data", {}).get("status", "pending")
        try:
            return DocumentStatus(status_str)
        except ValueError:
            return DocumentStatus.PENDING

    async def wait_for_parsing(
        self,
        kb_id: str,
        doc_id: str,
        timeout: float = 600.0,
        poll_interval: float = 5.0
    ) -> DocumentStatus:
        """Wait for document parsing to complete."""
        import time
        start = time.time()

        while time.time() - start < timeout:
            status = await self.get_document_status(kb_id, doc_id)

            if status in (DocumentStatus.PARSED, DocumentStatus.FAILED, DocumentStatus.CANCELED):
                return status

            await asyncio.sleep(poll_interval)

        logger.warning("document_parsing_timeout", doc_id=doc_id)
        return DocumentStatus.PENDING

    async def get_document_chunks(
        self,
        kb_id: str,
        doc_id: str,
        page: int = 1,
        page_size: int = 100
    ) -> List[Dict[str, Any]]:
        """Get parsed chunks for a document."""
        self._ensure_initialized()

        response = await self._client.get(
            f"/datasets/{kb_id}/documents/{doc_id}/chunks",
            params={"page": page, "page_size": page_size}
        )
        response.raise_for_status()

        return response.json().get("data", [])

    async def delete_document(self, kb_id: str, doc_id: str) -> bool:
        """Delete a document from a knowledge base."""
        self._ensure_initialized()

        response = await self._client.delete(
            f"/datasets/{kb_id}/documents/{doc_id}"
        )
        return response.status_code in (200, 204)

    # =========================================================================
    # Retrieval Operations
    # =========================================================================

    async def query(
        self,
        kb_ids: List[str],
        question: str,
        top_k: int = 5,
        similarity_threshold: float = 0.5,
        rerank: bool = True,
        with_answer: bool = True
    ) -> QueryResult:
        """
        Query knowledge bases with optional LLM answer generation.

        Args:
            kb_ids: List of knowledge base IDs to search
            question: The query question
            top_k: Maximum number of chunks to retrieve
            similarity_threshold: Minimum relevance score (0-1)
            rerank: Enable reranking for better relevance
            with_answer: Generate LLM answer from chunks

        Returns:
            QueryResult with chunks, answer, and citations
        """
        self._ensure_initialized()
        import time
        start = time.time()

        payload = {
            "dataset_ids": kb_ids,
            "question": question,
            "top_k": top_k,
            "similarity_threshold": similarity_threshold,
            "rerank": rerank,
        }

        if with_answer:
            payload["llm_model"] = self.config.llm_model

        response = await self._client.post("/retrieval", json=payload)
        response.raise_for_status()

        data = response.json().get("data", {})
        elapsed = (time.time() - start) * 1000

        # Parse chunks with citations
        chunks = []
        citations = []

        for chunk in data.get("chunks", []):
            chunk_data = {
                "text": chunk.get("content", ""),
                "score": chunk.get("score", 0.0),
                "source_doc": chunk.get("document_name", ""),
                "doc_id": chunk.get("document_id", ""),
                "page_num": chunk.get("page_number"),
                "chunk_id": chunk.get("id", ""),
            }
            chunks.append(chunk_data)

            # Build citation
            if chunk.get("document_name"):
                citations.append({
                    "doc_name": chunk.get("document_name"),
                    "page": chunk.get("page_number"),
                    "text": chunk.get("content", "")[:200] + "..."
                })

        return QueryResult(
            chunks=chunks,
            answer=data.get("answer"),
            citations=citations,
            query_time_ms=elapsed
        )

    async def hybrid_search(
        self,
        kb_ids: List[str],
        question: str,
        top_k: int = 5,
        keyword_weight: float = 0.3,
        similarity_threshold: float = 0.3
    ) -> QueryResult:
        """
        Hybrid vector + BM25 keyword search.

        Args:
            kb_ids: Knowledge bases to search
            question: Query text
            top_k: Max results
            keyword_weight: Weight for BM25 (0-1), rest is vector
            similarity_threshold: Min score threshold
        """
        self._ensure_initialized()
        import time
        start = time.time()

        payload = {
            "dataset_ids": kb_ids,
            "question": question,
            "top_k": top_k,
            "similarity_threshold": similarity_threshold,
            "hybrid_search": True,
            "keyword_weight": keyword_weight,
        }

        response = await self._client.post("/retrieval", json=payload)
        response.raise_for_status()

        data = response.json().get("data", {})
        elapsed = (time.time() - start) * 1000

        chunks = []
        for chunk in data.get("chunks", []):
            chunks.append({
                "text": chunk.get("content", ""),
                "score": chunk.get("score", 0.0),
                "source_doc": chunk.get("document_name", ""),
                "search_type": "hybrid"
            })

        return QueryResult(
            chunks=chunks,
            query_time_ms=elapsed
        )

    async def query_with_graph(
        self,
        kb_ids: List[str],
        question: str,
        top_k: int = 5,
        graph_depth: int = 2
    ) -> QueryResult:
        """
        GraphRAG query for relationship-aware retrieval.

        Uses knowledge graph to find related entities and context
        beyond simple semantic similarity.
        """
        self._ensure_initialized()
        import time
        start = time.time()

        payload = {
            "dataset_ids": kb_ids,
            "question": question,
            "top_k": top_k,
            "use_kg": True,
            "kg_depth": graph_depth,
        }

        response = await self._client.post("/retrieval", json=payload)
        response.raise_for_status()

        data = response.json().get("data", {})
        elapsed = (time.time() - start) * 1000

        chunks = []
        for chunk in data.get("chunks", []):
            chunks.append({
                "text": chunk.get("content", ""),
                "score": chunk.get("score", 0.0),
                "source_doc": chunk.get("document_name", ""),
                "entities": chunk.get("entities", []),
                "relationships": chunk.get("relationships", [])
            })

        return QueryResult(
            chunks=chunks,
            answer=data.get("answer"),
            citations=data.get("citations", []),
            query_time_ms=elapsed
        )

    # =========================================================================
    # Chat/Conversation
    # =========================================================================

    async def create_chat(
        self,
        name: str,
        kb_ids: List[str],
        llm_model: Optional[str] = None,
        system_prompt: str = "",
        top_k: int = 5
    ) -> str:
        """
        Create a chat assistant linked to knowledge bases.

        Returns:
            chat_id: The created chat assistant ID
        """
        self._ensure_initialized()

        payload = {
            "name": name,
            "dataset_ids": kb_ids,
            "llm_model": llm_model or self.config.llm_model,
            "prompt": system_prompt,
            "top_k": top_k,
        }

        response = await self._client.post("/chats", json=payload)
        response.raise_for_status()

        chat_id = response.json().get("data", {}).get("id")
        logger.info("chat_assistant_created", name=name, chat_id=chat_id)
        return chat_id

    async def send_message(
        self,
        chat_id: str,
        message: str,
        conversation_id: Optional[str] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Send a message to a chat assistant.

        Args:
            chat_id: Chat assistant ID
            message: User message
            conversation_id: Continue existing conversation (optional)
            stream: Enable streaming response

        Returns:
            {answer, citations, conversation_id}
        """
        self._ensure_initialized()

        payload = {
            "question": message,
            "stream": stream,
        }

        if conversation_id:
            payload["conversation_id"] = conversation_id

        response = await self._client.post(
            f"/chats/{chat_id}/completions",
            json=payload
        )
        response.raise_for_status()

        data = response.json().get("data", {})

        return {
            "answer": data.get("answer", ""),
            "citations": data.get("citations", []),
            "conversation_id": data.get("conversation_id"),
            "chunks_used": data.get("chunks", [])
        }

    async def stream_message(
        self,
        chat_id: str,
        message: str,
        conversation_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Stream a chat response token by token."""
        self._ensure_initialized()

        payload = {
            "question": message,
            "stream": True,
        }

        if conversation_id:
            payload["conversation_id"] = conversation_id

        async with self._client.stream(
            "POST",
            f"/chats/{chat_id}/completions",
            json=payload
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    yield line[5:].strip()

    # =========================================================================
    # GraphRAG Features
    # =========================================================================

    async def build_knowledge_graph(self, kb_id: str) -> str:
        """
        Trigger knowledge graph construction for a KB.

        This is an async task - use get_graph_status to check progress.

        Returns:
            task_id: The background task ID
        """
        self._ensure_initialized()

        response = await self._client.post(f"/datasets/{kb_id}/knowledge_graph/build")
        response.raise_for_status()

        task_id = response.json().get("data", {}).get("task_id")
        logger.info("knowledge_graph_build_started", kb_id=kb_id, task_id=task_id)
        return task_id

    async def get_graph_status(self, kb_id: str) -> Dict[str, Any]:
        """Check knowledge graph build progress."""
        self._ensure_initialized()

        response = await self._client.get(f"/datasets/{kb_id}/knowledge_graph/status")
        response.raise_for_status()

        return response.json().get("data", {})

    async def query_graph(
        self,
        kb_id: str,
        entity: str
    ) -> Dict[str, Any]:
        """
        Query the knowledge graph for entity relationships.

        Returns entities and their connections.
        """
        self._ensure_initialized()

        response = await self._client.get(
            f"/datasets/{kb_id}/knowledge_graph/query",
            params={"entity": entity}
        )
        response.raise_for_status()

        return response.json().get("data", {})

    async def get_graph_entities(
        self,
        kb_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get all entities in the knowledge graph."""
        self._ensure_initialized()

        response = await self._client.get(
            f"/datasets/{kb_id}/knowledge_graph/entities",
            params={"limit": limit}
        )
        response.raise_for_status()

        return response.json().get("data", [])


# =============================================================================
# Singleton Factory
# =============================================================================

_client: Optional[RAGflowClient] = None


async def get_ragflow_client() -> RAGflowClient:
    """
    Get or create the RAGflow client singleton.

    Uses lazy initialization pattern following project conventions.
    """
    global _client

    if _client is None:
        config = RAGflowConfig.from_env()

        if not config.api_key:
            logger.warning("RAGFLOW_API_KEY not set - RAGflow features disabled")
            raise RuntimeError("RAGFLOW_API_KEY environment variable required")

        _client = RAGflowClient(config)

    if not _client._initialized:
        await _client.initialize()

    return _client


async def close_ragflow_client() -> None:
    """Close the RAGflow client singleton."""
    global _client
    if _client:
        await _client.close()
        _client = None
