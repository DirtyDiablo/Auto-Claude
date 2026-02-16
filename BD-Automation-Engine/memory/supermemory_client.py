"""
Supermemory AI Memory Integration for BD Intelligence.

Provides document-level memory storage and retrieval complementing Mem0's
conversation memory. Supports URLs, PDFs, plain text, and integrations
with Notion, Google Drive, OneDrive.

Usage:
    async with SupermemoryClient(api_key) as client:
        # Add memory
        result = await client.add_memory("Important BD intel about DCGS")

        # Search
        results = await client.search("DCGS contract details")

        # Chat with memories
        response = await client.chat("What do we know about DCGS?")
"""

import os
import httpx
import mimetypes
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class SupermemoryClient:
    """
    Async client for Supermemory AI memory API.

    Handles document storage, semantic search, and AI chat with citations.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.supermemory.ai",
        timeout: float = 30.0,
    ):
        """
        Initialize Supermemory client.

        Args:
            api_key: Supermemory API key (or set SUPERMEMORY_API_KEY env var)
            base_url: API base URL
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or os.getenv("SUPERMEMORY_API_KEY")
        if not self.api_key:
            logger.warning(
                "No Supermemory API key provided. Set SUPERMEMORY_API_KEY env var."
            )

        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=self.timeout,
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> "SupermemoryClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, _exc_type, _exc_val, _exc_tb) -> None:
        """Async context manager exit."""
        await self.close()

    def _get_mime_type(self, extension: str) -> str:
        """Get MIME type for file extension."""
        mime_types = {
            ".pdf": "application/pdf",
            ".doc": "application/msword",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".txt": "text/plain",
            ".md": "text/markdown",
            ".html": "text/html",
            ".csv": "text/csv",
            ".json": "application/json",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        }
        return mime_types.get(
            extension.lower(),
            mimetypes.guess_type(f"file{extension}")[0] or "application/octet-stream",
        )

    # =========================================================================
    # MEMORY MANAGEMENT
    # =========================================================================

    async def add_memory(
        self,
        content: str,
        source_type: str = "text",
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Add a text memory.

        Args:
            content: The text content to store
            source_type: Type of source ('text', 'note', 'snippet')
            metadata: Optional metadata dict
            tags: Optional list of tags for categorization

        Returns:
            Memory creation response with ID
        """
        client = await self._get_client()

        payload = {
            "content": content,
            "source_type": source_type,
            "metadata": metadata or {},
            "tags": tags or [],
            "created_at": datetime.now().isoformat(),
        }

        try:
            response = await client.post("/v1/memories", json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to add memory: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error adding memory: {e}")
            raise

    async def add_url(
        self,
        url: str,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Add a URL to memory (content will be extracted).

        Args:
            url: The URL to save and index
            tags: Optional list of tags

        Returns:
            Memory creation response
        """
        client = await self._get_client()

        payload = {
            "url": url,
            "source_type": "url",
            "tags": tags or [],
        }

        try:
            response = await client.post("/v1/memories/url", json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to add URL: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error adding URL: {e}")
            raise

    async def add_document(
        self,
        file_path: str,
        title: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Upload and add a document to memory.

        Args:
            file_path: Path to the document file
            title: Optional title (defaults to filename)
            tags: Optional list of tags

        Returns:
            Memory creation response
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")

        mime_type = self._get_mime_type(path.suffix)
        title = title or path.stem

        # Create a new client for multipart upload
        async with httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=60.0,  # Longer timeout for uploads
        ) as upload_client:
            with open(path, "rb") as f:
                files = {
                    "file": (path.name, f, mime_type),
                }
                data = {
                    "title": title,
                    "tags": ",".join(tags) if tags else "",
                }

                try:
                    response = await upload_client.post(
                        "/v1/memories/upload",
                        files=files,
                        data=data,
                    )
                    response.raise_for_status()
                    return response.json()
                except httpx.HTTPStatusError as e:
                    logger.error(f"Failed to upload document: {e.response.text}")
                    raise
                except Exception as e:
                    logger.error(f"Error uploading document: {e}")
                    raise

    async def get_memory(self, memory_id: str) -> Dict[str, Any]:
        """
        Get a specific memory by ID.

        Args:
            memory_id: The memory ID

        Returns:
            Memory details
        """
        client = await self._get_client()

        try:
            response = await client.get(f"/v1/memories/{memory_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return {}
            logger.error(f"Failed to get memory: {e.response.text}")
            raise

    async def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory.

        Args:
            memory_id: The memory ID to delete

        Returns:
            True if deleted successfully
        """
        client = await self._get_client()

        try:
            response = await client.delete(f"/v1/memories/{memory_id}")
            response.raise_for_status()
            return True
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to delete memory: {e.response.text}")
            return False

    async def list_memories(
        self,
        limit: int = 50,
        offset: int = 0,
        tags: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        List memories with pagination and optional tag filtering.

        Args:
            limit: Maximum number of memories to return
            offset: Pagination offset
            tags: Filter by tags

        Returns:
            List of memories
        """
        client = await self._get_client()

        params = {
            "limit": limit,
            "offset": offset,
        }
        if tags:
            params["tags"] = ",".join(tags)

        try:
            response = await client.get("/v1/memories", params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("memories", data) if isinstance(data, dict) else data
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to list memories: {e.response.text}")
            raise

    # =========================================================================
    # SEARCH
    # =========================================================================

    async def search(
        self,
        query: str,
        top_k: int = 10,
        tags: Optional[List[str]] = None,
        min_score: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        Semantic search across memories.

        Args:
            query: Search query
            top_k: Maximum results to return
            tags: Filter by tags
            min_score: Minimum relevance score (0-1)

        Returns:
            List of matching memories with scores
        """
        client = await self._get_client()

        payload = {
            "query": query,
            "top_k": top_k,
            "min_score": min_score,
        }
        if tags:
            payload["tags"] = tags

        try:
            response = await client.post("/v1/search", json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("results", data) if isinstance(data, dict) else data
        except httpx.HTTPStatusError as e:
            logger.error(f"Search failed: {e.response.text}")
            raise

    async def search_by_document_type(
        self,
        query: str,
        doc_type: str,
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Search within a specific document type.

        Args:
            query: Search query
            doc_type: Document type (pdf, url, text, etc.)
            top_k: Maximum results

        Returns:
            List of matching memories
        """
        client = await self._get_client()

        payload = {
            "query": query,
            "top_k": top_k,
            "filters": {
                "source_type": doc_type,
            },
        }

        try:
            response = await client.post("/v1/search", json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("results", data) if isinstance(data, dict) else data
        except httpx.HTTPStatusError as e:
            logger.error(f"Search by type failed: {e.response.text}")
            raise

    # =========================================================================
    # CHAT
    # =========================================================================

    async def chat(
        self,
        message: str,
        conversation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Chat with AI using memories as context (RAG).

        Args:
            message: User message/question
            conversation_id: Optional conversation ID for continuity

        Returns:
            AI response with citations to relevant memories
        """
        client = await self._get_client()

        payload = {
            "message": message,
        }
        if conversation_id:
            payload["conversation_id"] = conversation_id

        try:
            response = await client.post("/v1/chat", json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Chat failed: {e.response.text}")
            raise

    # =========================================================================
    # INTEGRATIONS
    # =========================================================================

    async def sync_notion(
        self,
        workspace_id: str,
        database_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Sync content from Notion.

        Args:
            workspace_id: Notion workspace ID
            database_id: Optional specific database ID

        Returns:
            Sync status and results
        """
        client = await self._get_client()

        payload = {
            "workspace_id": workspace_id,
        }
        if database_id:
            payload["database_id"] = database_id

        try:
            response = await client.post("/v1/integrations/notion/sync", json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Notion sync failed: {e.response.text}")
            raise

    async def sync_google_drive(
        self,
        folder_id: str,
    ) -> Dict[str, Any]:
        """
        Sync content from Google Drive folder.

        Args:
            folder_id: Google Drive folder ID

        Returns:
            Sync status and results
        """
        client = await self._get_client()

        payload = {
            "folder_id": folder_id,
        }

        try:
            response = await client.post("/v1/integrations/gdrive/sync", json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Google Drive sync failed: {e.response.text}")
            raise

    async def get_sync_status(self) -> Dict[str, Any]:
        """
        Get status of all integration syncs.

        Returns:
            Sync status for all integrations
        """
        client = await self._get_client()

        try:
            response = await client.get("/v1/integrations/status")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to get sync status: {e.response.text}")
            raise

    # =========================================================================
    # COLLECTIONS
    # =========================================================================

    async def create_collection(
        self,
        name: str,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a collection for organizing memories.

        Args:
            name: Collection name
            description: Optional description

        Returns:
            Collection details with ID
        """
        client = await self._get_client()

        payload = {
            "name": name,
            "description": description or "",
        }

        try:
            response = await client.post("/v1/collections", json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to create collection: {e.response.text}")
            raise

    async def add_to_collection(
        self,
        collection_id: str,
        memory_ids: List[str],
    ) -> Dict[str, Any]:
        """
        Add memories to a collection.

        Args:
            collection_id: Collection ID
            memory_ids: List of memory IDs to add

        Returns:
            Update result
        """
        client = await self._get_client()

        payload = {
            "memory_ids": memory_ids,
        }

        try:
            response = await client.post(
                f"/v1/collections/{collection_id}/memories",
                json=payload,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to add to collection: {e.response.text}")
            raise


class BDMemoryManager:
    """
    BD-specific memory manager using Supermemory.

    Provides specialized methods for storing and retrieving BD artifacts
    like RFPs, contracts, proposals, and capability statements.
    """

    # BD document type tags
    DOC_TAGS = {
        "rfp": "bd:rfp",
        "contract": "bd:contract",
        "proposal": "bd:proposal",
        "capability": "bd:capability",
        "past_performance": "bd:past_performance",
        "contact_research": "bd:contact_research",
        "competitor": "bd:competitor",
        "program_intel": "bd:program_intel",
        "meeting_notes": "bd:meeting_notes",
        "call_notes": "bd:call_notes",
    }

    def __init__(
        self,
        supermemory_key: Optional[str] = None,
        mem0_client: Optional[Any] = None,
    ):
        """
        Initialize BD Memory Manager.

        Args:
            supermemory_key: Supermemory API key
            mem0_client: Optional Mem0 client for conversation memory
        """
        self.supermemory = SupermemoryClient(api_key=supermemory_key)
        self.mem0 = mem0_client

    async def close(self) -> None:
        """Close all clients."""
        await self.supermemory.close()

    async def __aenter__(self) -> "BDMemoryManager":
        """Async context manager entry."""
        return self

    async def __aexit__(self, _exc_type, _exc_val, _exc_tb) -> None:
        """Async context manager exit."""
        await self.close()

    # =========================================================================
    # RFP METHODS
    # =========================================================================

    async def store_rfp(
        self,
        file_path: str,
        title: str,
        agency: Optional[str] = None,
        deadline: Optional[str] = None,
        program: Optional[str] = None,
        solicitation_number: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Store an RFP document.

        Args:
            file_path: Path to RFP document
            title: RFP title
            agency: Issuing agency
            deadline: Response deadline
            program: Associated program name
            solicitation_number: Solicitation/RFP number

        Returns:
            Memory creation result
        """
        tags = [self.DOC_TAGS["rfp"]]
        if agency:
            tags.append(f"agency:{agency.lower().replace(' ', '_')}")
        if program:
            tags.append(f"program:{program.lower().replace(' ', '_')}")

        # First upload the document
        result = await self.supermemory.add_document(file_path, title, tags)

        # Add metadata as a linked text memory
        metadata_text = f"""
RFP: {title}
Solicitation Number: {solicitation_number or "N/A"}
Agency: {agency or "Unknown"}
Program: {program or "N/A"}
Response Deadline: {deadline or "Unknown"}
Document ID: {result.get("id", "N/A")}
"""
        await self.supermemory.add_memory(
            metadata_text,
            source_type="note",
            tags=tags + ["bd:metadata"],
            metadata={
                "rfp_title": title,
                "agency": agency,
                "deadline": deadline,
                "solicitation_number": solicitation_number,
                "document_id": result.get("id"),
            },
        )

        return result

    async def search_rfps(
        self,
        query: str,
        agency: Optional[str] = None,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Search RFP documents.

        Args:
            query: Search query
            agency: Filter by agency
            top_k: Maximum results

        Returns:
            Matching RFPs
        """
        tags = [self.DOC_TAGS["rfp"]]
        if agency:
            tags.append(f"agency:{agency.lower().replace(' ', '_')}")

        return await self.supermemory.search(query, top_k=top_k, tags=tags)

    # =========================================================================
    # CONTRACT METHODS
    # =========================================================================

    async def store_contract(
        self,
        file_path: str,
        contract_number: str,
        contractor: Optional[str] = None,
        agency: Optional[str] = None,
        program: Optional[str] = None,
        value: Optional[str] = None,
        pop_end: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Store a contract document.

        Args:
            file_path: Path to contract document
            contract_number: Contract number
            contractor: Contractor name
            agency: Contracting agency
            program: Associated program
            value: Contract value
            pop_end: Period of performance end date

        Returns:
            Memory creation result
        """
        title = f"Contract {contract_number}"
        tags = [self.DOC_TAGS["contract"]]
        if contractor:
            tags.append(f"contractor:{contractor.lower().replace(' ', '_')}")
        if agency:
            tags.append(f"agency:{agency.lower().replace(' ', '_')}")
        if program:
            tags.append(f"program:{program.lower().replace(' ', '_')}")

        result = await self.supermemory.add_document(file_path, title, tags)

        # Add metadata
        metadata_text = f"""
Contract: {contract_number}
Contractor: {contractor or "Unknown"}
Agency: {agency or "Unknown"}
Program: {program or "N/A"}
Value: {value or "Unknown"}
POP End: {pop_end or "Unknown"}
Document ID: {result.get("id", "N/A")}
"""
        await self.supermemory.add_memory(
            metadata_text,
            source_type="note",
            tags=tags + ["bd:metadata"],
            metadata={
                "contract_number": contract_number,
                "contractor": contractor,
                "agency": agency,
                "program": program,
                "value": value,
                "pop_end": pop_end,
                "document_id": result.get("id"),
            },
        )

        return result

    async def search_contracts(
        self,
        query: str,
        contractor: Optional[str] = None,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Search contract documents.

        Args:
            query: Search query
            contractor: Filter by contractor
            top_k: Maximum results

        Returns:
            Matching contracts
        """
        tags = [self.DOC_TAGS["contract"]]
        if contractor:
            tags.append(f"contractor:{contractor.lower().replace(' ', '_')}")

        return await self.supermemory.search(query, top_k=top_k, tags=tags)

    # =========================================================================
    # GENERAL BD METHODS
    # =========================================================================

    async def store_capability_statement(
        self,
        file_path: str,
        company: str,
        capabilities: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Store a capability statement."""
        tags = [
            self.DOC_TAGS["capability"],
            f"company:{company.lower().replace(' ', '_')}",
        ]
        title = f"{company} Capability Statement"
        return await self.supermemory.add_document(file_path, title, tags)

    async def store_past_performance(
        self,
        file_path: str,
        title: str,
        program: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Store a past performance document."""
        tags = [self.DOC_TAGS["past_performance"]]
        if program:
            tags.append(f"program:{program.lower().replace(' ', '_')}")
        return await self.supermemory.add_document(file_path, title, tags)

    async def store_competitor_intel(
        self,
        content: str,
        competitor: str,
        intel_type: str = "general",
    ) -> Dict[str, Any]:
        """Store competitor intelligence."""
        tags = [
            self.DOC_TAGS["competitor"],
            f"competitor:{competitor.lower().replace(' ', '_')}",
            f"intel_type:{intel_type}",
        ]
        return await self.supermemory.add_memory(content, source_type="note", tags=tags)

    async def store_program_intel(
        self,
        content: str,
        program: str,
        intel_type: str = "general",
    ) -> Dict[str, Any]:
        """Store program intelligence."""
        tags = [
            self.DOC_TAGS["program_intel"],
            f"program:{program.lower().replace(' ', '_')}",
            f"intel_type:{intel_type}",
        ]
        return await self.supermemory.add_memory(content, source_type="note", tags=tags)

    async def store_meeting_notes(
        self,
        content: str,
        attendees: List[str],
        program: Optional[str] = None,
        company: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Store meeting notes."""
        tags = [self.DOC_TAGS["meeting_notes"]]
        if program:
            tags.append(f"program:{program.lower().replace(' ', '_')}")
        if company:
            tags.append(f"company:{company.lower().replace(' ', '_')}")

        metadata = {
            "attendees": attendees,
            "program": program,
            "company": company,
            "date": datetime.now().isoformat(),
        }
        return await self.supermemory.add_memory(
            content, source_type="note", tags=tags, metadata=metadata
        )

    async def ask_about_documents(
        self,
        question: str,
        conversation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Ask a question using RAG over stored documents.

        Args:
            question: Question to ask
            conversation_id: Optional conversation ID for continuity

        Returns:
            AI response with citations
        """
        return await self.supermemory.chat(question, conversation_id)

    async def search_all(
        self,
        query: str,
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """Search across all BD documents."""
        return await self.supermemory.search(query, top_k=top_k)

    async def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        try:
            memories = await self.supermemory.list_memories(limit=1)
            return {
                "available": True,
                "total_memories": len(memories),
            }
        except Exception as e:
            return {
                "available": False,
                "error": str(e),
            }


# Singleton instance
_bd_memory_manager: Optional[BDMemoryManager] = None


def get_bd_memory_manager() -> BDMemoryManager:
    """Get or create the BD Memory Manager singleton."""
    global _bd_memory_manager
    if _bd_memory_manager is None:
        _bd_memory_manager = BDMemoryManager()
    return _bd_memory_manager
