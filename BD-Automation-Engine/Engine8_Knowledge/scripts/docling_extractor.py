"""
Docling document extractor for processing XLSX, PDF, DOCX files
into structured Markdown/JSON for indexing into the knowledge base.

Uses IBM Docling for high-fidelity document parsing with table extraction,
OCR, and layout analysis.

Usage:
    from Engine8_Knowledge.scripts.docling_extractor import DoclingExtractor
    extractor = DoclingExtractor()
    result = extractor.extract("path/to/document.pdf")
    markdown = result.to_markdown()

Install:
    pip install docling
"""

import logging
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

try:
    from docling.document_converter import DocumentConverter
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False
    logger.warning("docling not installed. Install with: pip install docling")


@dataclass
class ExtractedTable:
    """A table extracted from a document."""
    page: int
    headers: List[str] = field(default_factory=list)
    rows: List[List[str]] = field(default_factory=list)
    caption: Optional[str] = None

    def to_markdown(self) -> str:
        """Convert table to Markdown."""
        if not self.headers and not self.rows:
            return ""
        lines = []
        if self.caption:
            lines.append(f"**{self.caption}**\n")
        if self.headers:
            lines.append("| " + " | ".join(self.headers) + " |")
            lines.append("| " + " | ".join(["---"] * len(self.headers)) + " |")
        for row in self.rows:
            lines.append("| " + " | ".join(row) + " |")
        return "\n".join(lines)

    def to_dict(self) -> Dict:
        """Convert table to list of dicts."""
        if not self.headers:
            return {"rows": self.rows}
        return [dict(zip(self.headers, row)) for row in self.rows]


@dataclass
class ExtractionResult:
    """Result from document extraction."""
    file_path: str
    file_type: str
    title: Optional[str] = None
    text: str = ""
    pages: int = 0
    tables: List[ExtractedTable] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        """Convert full extraction to Markdown."""
        parts = []
        if self.title:
            parts.append(f"# {self.title}\n")
        parts.append(self.text)
        if self.tables:
            parts.append("\n## Tables\n")
            for i, table in enumerate(self.tables):
                parts.append(f"\n### Table {i + 1} (Page {table.page})\n")
                parts.append(table.to_markdown())
        return "\n".join(parts)

    def to_chunks(self, chunk_size: int = 1000, overlap: int = 100) -> List[Dict]:
        """Split into indexable chunks with metadata."""
        text = self.to_markdown()
        chunks = []
        start = 0
        chunk_idx = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk_text = text[start:end]
            chunks.append({
                "text": chunk_text,
                "chunk_index": chunk_idx,
                "total_chunks": -1,  # Will be set after all chunks created
                "source_file": self.file_path,
                "file_type": self.file_type,
                "title": self.title,
            })
            chunk_idx += 1
            start = end - overlap if end < len(text) else end

        # Update total_chunks
        for chunk in chunks:
            chunk["total_chunks"] = len(chunks)

        return chunks


class DoclingExtractor:
    """Document extractor using IBM Docling."""

    def __init__(self):
        if not DOCLING_AVAILABLE:
            raise ImportError("docling is required. Install with: pip install docling")
        self.converter = DocumentConverter()

    def extract(self, file_path: str) -> ExtractionResult:
        """
        Extract structured content from a document.

        Supports: PDF, DOCX, XLSX, PPTX, HTML, Markdown, AsciiDoc, CSV

        Args:
            file_path: Path to document file

        Returns:
            ExtractionResult with text, tables, and metadata
        """
        path = Path(file_path)
        if not path.exists():
            return ExtractionResult(
                file_path=str(path),
                file_type=path.suffix,
                errors=[f"File not found: {path}"]
            )

        result = ExtractionResult(
            file_path=str(path),
            file_type=path.suffix.lower(),
        )

        try:
            doc_result = self.converter.convert(str(path))
            doc = doc_result.document

            # Extract text
            result.text = doc.export_to_markdown()
            result.title = getattr(doc, "title", None) or path.stem
            result.pages = getattr(doc, "num_pages", 0) or 0

            # Extract tables
            if hasattr(doc, "tables"):
                for table in doc.tables:
                    extracted = ExtractedTable(
                        page=getattr(table, "page_no", 0) or 0,
                    )
                    if hasattr(table, "export_to_dataframe"):
                        try:
                            df = table.export_to_dataframe()
                            extracted.headers = list(df.columns)
                            extracted.rows = df.values.tolist()
                        except Exception:
                            pass
                    result.tables.append(extracted)

            # Extract metadata
            result.metadata = {
                "file_name": path.name,
                "file_size_bytes": path.stat().st_size,
                "page_count": result.pages,
                "table_count": len(result.tables),
                "char_count": len(result.text),
            }

        except Exception as e:
            result.errors.append(f"Extraction error: {e}")
            logger.error("docling_extraction_failed", file=str(path), error=str(e))

        return result

    def extract_batch(self, file_paths: List[str]) -> List[ExtractionResult]:
        """Extract from multiple documents."""
        results = []
        for path in file_paths:
            try:
                results.append(self.extract(path))
            except Exception as e:
                results.append(ExtractionResult(
                    file_path=path,
                    file_type=Path(path).suffix,
                    errors=[str(e)]
                ))
        return results

    def extract_to_chunks(
        self, file_path: str, chunk_size: int = 1000, overlap: int = 100
    ) -> List[Dict]:
        """Extract and split into indexable chunks."""
        result = self.extract(file_path)
        return result.to_chunks(chunk_size=chunk_size, overlap=overlap)


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) < 2:
        print("Usage: python docling_extractor.py <file_path>")
        print("Supported: PDF, DOCX, XLSX, PPTX, HTML, Markdown, CSV")
        sys.exit(1)

    extractor = DoclingExtractor()
    result = extractor.extract(sys.argv[1])

    print(f"File: {result.file_path}")
    print(f"Type: {result.file_type}")
    print(f"Title: {result.title}")
    print(f"Pages: {result.pages}")
    print(f"Tables: {len(result.tables)}")
    print(f"Text length: {len(result.text)} chars")
    if result.errors:
        print(f"Errors: {result.errors}")

    # Print first 500 chars of markdown
    md = result.to_markdown()
    print(f"\n--- Preview (first 500 chars) ---\n{md[:500]}")
