"""Retrieval module for BD Intelligence System."""

from .page_index import PageIndex, PageIndexRAG, PageRecord, RetrievalResult
from .page_index_loader import extract_pdf_pages, generate_document_id, index_pdf_folder
from .ultra_rag import (
    UltraRAG,
    PipelineConfig,
    QueryPlan,
    RetrievalStrategy,
    ReasoningStep,
)
from .ultra_rag_integration import BDUltraRAG

__all__ = [
    # PageIndex
    "PageIndex",
    "PageIndexRAG",
    "PageRecord",
    "RetrievalResult",
    "extract_pdf_pages",
    "generate_document_id",
    "index_pdf_folder",
    # UltraRAG
    "UltraRAG",
    "PipelineConfig",
    "QueryPlan",
    "RetrievalStrategy",
    "ReasoningStep",
    "BDUltraRAG",
]
