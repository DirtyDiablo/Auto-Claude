"""
Engine 8: Knowledge Management System
AI-powered file management and semantic search for BD intelligence data.

Components:
- vector_store.py: Qdrant vector database for unified knowledge storage
- indexer.py: Data ingestion and indexing pipeline
- document_processor.py: Document processing with Docling
- rag_engine.py: RAG-powered question answering
- auto_tagger.py: LLM-based document classification
- file_watcher.py: Auto-process new files
- api.py: FastAPI server for MCP integration

Usage:
    # Start the API server
    python Engine8_Knowledge/api.py

    # Index all data
    python Engine8_Knowledge/scripts/indexer.py --all

    # Search from CLI
    python Engine8_Knowledge/scripts/vector_store.py --search "DCGS analyst"

    # Start file watcher
    python Engine8_Knowledge/scripts/file_watcher.py
"""

from .scripts.vector_store import BDKnowledgeStore
from .scripts.indexer import BDIndexer

# Optional imports (may have missing dependencies)
try:
    from .scripts.rag_engine import BDRAGEngine
except ImportError:
    BDRAGEngine = None

try:
    from .scripts.auto_tagger import AutoTagger
except ImportError:
    AutoTagger = None

try:
    from .scripts.document_processor import BDDocumentProcessor
except ImportError:
    BDDocumentProcessor = None

__all__ = [
    "BDKnowledgeStore",
    "BDIndexer",
    "BDRAGEngine",
    "AutoTagger",
    "BDDocumentProcessor",
]
__version__ = "1.0.0"
