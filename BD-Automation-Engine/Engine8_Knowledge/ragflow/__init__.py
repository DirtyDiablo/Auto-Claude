"""
RAGflow Integration for BD Knowledge Intelligence.

This module provides:
- RAGflowClient: Async client for RAGflow API
- BDKnowledgeManager: BD-specific knowledge operations
- BDDocumentPreprocessor: Document preparation for optimal ingestion

Example Usage:
    from ragflow import get_ragflow_client, get_bd_knowledge_manager

    # Initialize client
    client = await get_ragflow_client()

    # Create BD knowledge bases
    manager = await get_bd_knowledge_manager()
    await manager.initialize_knowledge_bases()

    # Query intelligence
    result = await manager.query_bd_intelligence("DCGS program contacts", context="program")

    # Generate call prep
    prep = await manager.generate_call_prep("John Smith", "DCGS-A")
"""

from .ragflow_client import (
    RAGflowClient,
    RAGflowConfig,
    ChunkMethod,
    DocumentStatus,
    QueryResult,
    get_ragflow_client,
    close_ragflow_client,
)

from .bd_knowledge_manager import (
    BDKnowledgeManager,
    KnowledgeBaseConfig,
    BD_KNOWLEDGE_BASES,
    ProgramIntelligence,
    ContactContext,
    CallPrepBrief,
    get_bd_knowledge_manager,
    close_bd_knowledge_manager,
)

from .document_preprocessor import (
    BDDocumentPreprocessor,
    PreprocessedDocument,
)

# Re-export for convenience
__all__ = [
    # Client
    "RAGflowClient",
    "RAGflowConfig",
    "ChunkMethod",
    "DocumentStatus",
    "QueryResult",
    "get_ragflow_client",
    "close_ragflow_client",
    # Manager
    "BDKnowledgeManager",
    "KnowledgeBaseConfig",
    "BD_KNOWLEDGE_BASES",
    "ProgramIntelligence",
    "ContactContext",
    "CallPrepBrief",
    "get_bd_knowledge_manager",
    "close_bd_knowledge_manager",
    # Preprocessor
    "BDDocumentPreprocessor",
    "PreprocessedDocument",
]

# Alias for backward compatibility
BDKnowledgeBaseConfig = KnowledgeBaseConfig
