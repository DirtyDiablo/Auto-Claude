"""
Utilities for loading documents into PageIndex.
"""

from pathlib import Path
from typing import List, Dict
import fitz  # PyMuPDF
import hashlib
import structlog

logger = structlog.get_logger(__name__)


def extract_pdf_pages(pdf_path: str) -> List[Dict]:
    """Extract pages from a PDF file."""
    pages = []
    doc = fitz.open(pdf_path)

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text()

        if text.strip():  # Only add non-empty pages
            pages.append({"page_number": page_num + 1, "content": text})

    doc.close()
    return pages


def generate_document_id(file_path: str) -> str:
    """Generate a unique document ID from file path and content hash."""
    path = Path(file_path)
    with open(path, "rb") as f:
        content_hash = hashlib.md5(f.read()).hexdigest()[:8]
    return f"{path.stem}_{content_hash}"


def index_pdf_folder(page_index, folder_path: str, recursive: bool = True) -> Dict:
    """Index all PDFs in a folder."""
    folder = Path(folder_path)
    pattern = "**/*.pdf" if recursive else "*.pdf"

    stats = {"indexed": 0, "pages": 0, "errors": []}

    for pdf_path in folder.glob(pattern):
        try:
            doc_id = generate_document_id(str(pdf_path))
            pages = extract_pdf_pages(str(pdf_path))

            num_indexed = page_index.index_document(
                document_id=doc_id,
                document_name=pdf_path.name,
                pages=pages,
                metadata={"source_path": str(pdf_path)},
            )

            stats["indexed"] += 1
            stats["pages"] += num_indexed
            logger.info(
                "pdf_indexed", filename=pdf_path.name, pages_indexed=num_indexed
            )

        except Exception as e:
            stats["errors"].append({"file": str(pdf_path), "error": str(e)})
            logger.error("pdf_indexing_failed", filename=pdf_path.name, error=str(e))

    return stats


def index_from_docling(page_index, processed_doc: Dict, metadata: Dict = None) -> int:
    """
    Index a document processed by Docling/BDDocumentPipeline.

    Args:
        page_index: PageIndex instance
        processed_doc: Output from BDDocumentPipeline.process_to_dict()
        metadata: Additional metadata to attach

    Returns:
        Number of pages indexed
    """
    doc_id = processed_doc.get("document_id")
    doc_name = processed_doc.get("filename")
    pages = processed_doc.get("pages", [])

    # Convert page format
    formatted_pages = [
        {"page_number": p["page_number"], "content": p["content"]} for p in pages
    ]

    # Merge metadata
    full_metadata = processed_doc.get("metadata", {})
    if metadata:
        full_metadata.update(metadata)

    return page_index.index_document(
        document_id=doc_id,
        document_name=doc_name,
        pages=formatted_pages,
        metadata=full_metadata,
    )
