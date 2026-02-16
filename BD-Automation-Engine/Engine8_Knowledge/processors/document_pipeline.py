"""
Document Processing Pipeline using Docling.
Processes PDFs, DOCX, PPTX into structured data for indexing.
"""

import fitz  # PyMuPDF as fallback
from pathlib import Path
from typing import List, Dict
from dataclasses import dataclass
import hashlib
import structlog
from datetime import datetime

logger = structlog.get_logger(__name__)


@dataclass
class ProcessedDocument:
    """Result of document processing."""

    document_id: str
    filename: str
    file_type: str
    num_pages: int
    text_content: str
    pages: List[Dict]
    tables: List[Dict]
    metadata: Dict
    processed_at: str


class BDDocumentPipeline:
    """
    Document processing pipeline for BD intelligence.
    Uses Docling when available, falls back to PyMuPDF.
    """

    def __init__(self, use_docling: bool = True):
        self.use_docling = use_docling
        self._docling_converter = None

        if use_docling:
            try:
                from docling.document_converter import DocumentConverter

                self._docling_converter = DocumentConverter()
                logger.info("docling_initialized")
            except ImportError:
                logger.warning("docling_not_available", fallback="PyMuPDF")
                self.use_docling = False

    def _generate_doc_id(self, file_path: str) -> str:
        """Generate unique document ID."""
        path = Path(file_path)
        with open(path, "rb") as f:
            content_hash = hashlib.md5(f.read()).hexdigest()[:8]
        return f"{path.stem}_{content_hash}"

    def _process_with_docling(self, file_path: str) -> ProcessedDocument:
        """Process document using Docling."""
        from docling.document_converter import DocumentConverter

        if not self._docling_converter:
            self._docling_converter = DocumentConverter()

        result = self._docling_converter.convert(file_path)
        doc = result.document

        # Extract text as markdown
        text_content = doc.export_to_markdown()

        # Extract tables
        tables = []
        for i, table in enumerate(doc.tables):
            try:
                df = table.export_to_dataframe()
                tables.append(
                    {
                        "index": i,
                        "rows": len(df),
                        "columns": list(df.columns),
                        "data": df.to_dict(orient="records")[:100],  # Limit rows
                    }
                )
            except Exception as e:
                logger.debug("table_export_failed: %s", e)

        # Build pages list
        pages = []
        # Docling doesn't directly expose page-by-page, approximate from text
        text_parts = text_content.split("\n\n")
        chunk_size = max(1, len(text_parts) // 10)  # Approximate 10 pages
        for i in range(0, len(text_parts), chunk_size):
            page_text = "\n\n".join(text_parts[i : i + chunk_size])
            if page_text.strip():
                pages.append({"page_number": len(pages) + 1, "content": page_text})

        path = Path(file_path)
        return ProcessedDocument(
            document_id=self._generate_doc_id(file_path),
            filename=path.name,
            file_type=path.suffix.lower(),
            num_pages=len(pages),
            text_content=text_content,
            pages=pages,
            tables=tables,
            metadata={"source": str(path), "processor": "docling"},
            processed_at=datetime.now().isoformat(),
        )

    def _process_with_pymupdf(self, file_path: str) -> ProcessedDocument:
        """Process PDF using PyMuPDF (fallback)."""
        path = Path(file_path)

        if path.suffix.lower() != ".pdf":
            raise ValueError(f"PyMuPDF only supports PDF files, got {path.suffix}")

        doc = fitz.open(file_path)

        pages = []
        all_text = []
        tables = []

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text()

            if text.strip():
                pages.append({"page_number": page_num + 1, "content": text})
                all_text.append(text)

            # Try to extract tables (basic)
            try:
                page_tables = page.find_tables()
                for i, table in enumerate(page_tables):
                    tables.append(
                        {
                            "page": page_num + 1,
                            "index": i,
                            "data": table.extract()[:50],  # Limit rows
                        }
                    )
            except Exception as e:
                logger.debug("pdf_table_extract_failed: %s", e)

        doc.close()

        return ProcessedDocument(
            document_id=self._generate_doc_id(file_path),
            filename=path.name,
            file_type=".pdf",
            num_pages=len(pages),
            text_content="\n\n".join(all_text),
            pages=pages,
            tables=tables,
            metadata={"source": str(path), "processor": "pymupdf"},
            processed_at=datetime.now().isoformat(),
        )

    def process(self, file_path: str) -> ProcessedDocument:
        """Process a document file."""
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if self.use_docling and self._docling_converter:
            try:
                return self._process_with_docling(file_path)
            except Exception as e:
                logger.warning(
                    "docling_processing_failed", fallback="PyMuPDF", error=str(e)
                )

        # Fallback to PyMuPDF for PDFs
        if path.suffix.lower() == ".pdf":
            return self._process_with_pymupdf(file_path)

        raise ValueError(f"Unsupported file type: {path.suffix}")

    def process_to_dict(self, file_path: str) -> Dict:
        """Process and return as dictionary."""
        result = self.process(file_path)
        return {
            "document_id": result.document_id,
            "filename": result.filename,
            "file_type": result.file_type,
            "num_pages": result.num_pages,
            "text_length": len(result.text_content),
            "pages": result.pages,
            "tables_count": len(result.tables),
            "tables": result.tables,
            "metadata": result.metadata,
            "processed_at": result.processed_at,
        }


def process_document(file_path: str) -> Dict:
    """Convenience function to process a single document."""
    pipeline = BDDocumentPipeline()
    return pipeline.process_to_dict(file_path)


def batch_process_folder(
    folder_path: str, extensions: List[str] = None, recursive: bool = True
) -> Dict:
    """Process all documents in a folder."""
    extensions = extensions or [".pdf", ".docx", ".pptx"]
    folder = Path(folder_path)

    if not folder.exists():
        raise FileNotFoundError(f"Folder not found: {folder_path}")

    pipeline = BDDocumentPipeline()

    results = {"processed": [], "failed": [], "total_pages": 0, "total_tables": 0}

    pattern = "**/*" if recursive else "*"

    for file_path in folder.glob(pattern):
        if file_path.suffix.lower() in extensions:
            try:
                result = pipeline.process_to_dict(str(file_path))
                results["processed"].append(
                    {
                        "file": file_path.name,
                        "document_id": result["document_id"],
                        "pages": result["num_pages"],
                        "tables": result["tables_count"],
                    }
                )
                results["total_pages"] += result["num_pages"]
                results["total_tables"] += result["tables_count"]
                logger.info("document_processed", filename=file_path.name)
            except Exception as e:
                results["failed"].append({"file": file_path.name, "error": str(e)})
                logger.error(
                    "document_processing_failed", filename=file_path.name, error=str(e)
                )

    return results
