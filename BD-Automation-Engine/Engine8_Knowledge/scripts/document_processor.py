"""
BD Document Processor - Process documents for knowledge base ingestion.
Uses Docling for high-accuracy document processing (97.9% table accuracy).
"""

import sys
import json
import hashlib
import logging
import csv
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BDDocumentProcessor")

# Check for optional dependencies
try:
    from docling.document_converter import DocumentConverter

    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False
    logger.warning("docling not installed. Install with: pip install docling")

try:
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    logger.warning(
        "python-magic not installed. Install with: pip install python-magic-bin"
    )

# =========================================
# CONFIGURATION
# =========================================

PROJECT_ROOT = Path(__file__).parent.parent.parent

# Document source paths
BULLHORN_EXPORTS_DIR = PROJECT_ROOT / "docs" / "Bullhorn Exports"
PROGRAM_DATA_DIR = PROJECT_ROOT / "Engine2_ProgramMapping" / "data"
PRIME_CONTACTS_DIR = PROJECT_ROOT / "Engine3_OrgChart" / "data" / "Prime_Contacts"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

# Supported file types
SUPPORTED_EXTENSIONS = {
    ".pdf": "document",
    ".docx": "document",
    ".doc": "document",
    ".xlsx": "spreadsheet",
    ".xls": "spreadsheet",
    ".csv": "data",
    ".txt": "text",
    ".md": "markdown",
    ".json": "data",
}

# Maximum chunk size for text splitting
DEFAULT_CHUNK_SIZE = 512
DEFAULT_CHUNK_OVERLAP = 50


@dataclass
class ProcessedDocument:
    """Represents a processed document with extracted content."""

    id: str
    title: str
    content: str
    summary: str = ""
    doc_type: str = "document"
    source_file: str = ""
    file_size: int = 0
    page_count: int = 0
    tables: List[Dict] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    chunks: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created_date: str = ""
    processed_at: str = ""

    def __post_init__(self):
        if not self.processed_at:
            self.processed_at = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "summary": self.summary,
            "doc_type": self.doc_type,
            "source_file": self.source_file,
            "file_size": self.file_size,
            "page_count": self.page_count,
            "tables": self.tables,
            "metadata": self.metadata,
            "chunks": self.chunks,
            "tags": self.tags,
            "created_date": self.created_date,
            "processed_at": self.processed_at,
        }


@dataclass
class ProcessingResult:
    """Result of document processing operation."""

    total_files: int
    processed: int
    errors: int
    documents: List[ProcessedDocument]
    error_files: List[Tuple[str, str]]  # (filename, error_message)
    duration_seconds: float


# =========================================
# TEXT CHUNKING
# =========================================


class TextChunker:
    """Split text into semantic chunks for embedding."""

    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks.

        Uses sentence-aware splitting when possible.
        """
        if not text or len(text) <= self.chunk_size:
            return [text] if text else []

        chunks = []
        sentences = self._split_sentences(text)

        current_chunk = []
        current_length = 0

        for sentence in sentences:
            sentence_length = len(sentence)

            if current_length + sentence_length <= self.chunk_size:
                current_chunk.append(sentence)
                current_length += sentence_length
            else:
                if current_chunk:
                    chunks.append(" ".join(current_chunk))

                # Start new chunk with overlap
                overlap_text = self._get_overlap(current_chunk)
                if overlap_text:
                    current_chunk = [overlap_text, sentence]
                    current_length = len(overlap_text) + sentence_length
                else:
                    current_chunk = [sentence]
                    current_length = sentence_length

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        import re

        # Simple sentence splitting (handles common cases)
        sentence_endings = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")
        sentences = sentence_endings.split(text)

        # Handle very long sentences by splitting on other punctuation
        result = []
        for sentence in sentences:
            if len(sentence) > self.chunk_size:
                # Split on semicolons, colons
                sub_parts = re.split(r"[;:]\s+", sentence)
                result.extend(sub_parts)
            else:
                result.append(sentence)

        return [s.strip() for s in result if s.strip()]

    def _get_overlap(self, chunks: List[str]) -> str:
        """Get overlap text from previous chunks."""
        if not chunks:
            return ""

        overlap = " ".join(chunks)
        if len(overlap) <= self.chunk_overlap:
            return overlap

        # Get last N characters
        return overlap[-self.chunk_overlap :]


# =========================================
# DOCUMENT PROCESSOR CLASS
# =========================================


class BDDocumentProcessor:
    """
    Process documents for knowledge base ingestion.

    Supports PDF, DOCX, XLSX, CSV, TXT, MD, JSON files.
    Uses Docling for advanced document processing when available.
    """

    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    ):
        self.chunker = TextChunker(chunk_size, chunk_overlap)

        if DOCLING_AVAILABLE:
            self.converter = DocumentConverter()
            logger.info("Using Docling for document processing")
        else:
            self.converter = None
            logger.info("Using fallback document processing (Docling not available)")

    def process_file(self, path: Path) -> Optional[ProcessedDocument]:
        """
        Extract text and metadata from a file.

        Args:
            path: Path to the file.

        Returns:
            ProcessedDocument or None if processing failed.
        """
        path = Path(path)

        if not path.exists():
            logger.warning(f"File not found: {path}")
            return None

        ext = path.suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            logger.warning(f"Unsupported file type: {ext}")
            return None

        doc_type = SUPPORTED_EXTENSIONS[ext]

        try:
            # Generate document ID
            doc_id = self._generate_doc_id(path)

            # Get file metadata
            stat = path.stat()
            file_size = stat.st_size
            created_date = datetime.fromtimestamp(stat.st_mtime).isoformat()

            # Extract content based on file type
            if ext in [".pdf", ".docx", ".doc"] and self.converter:
                content, tables, page_count = self._process_with_docling(path)
            elif ext in [".xlsx", ".xls"]:
                content, tables = self._process_spreadsheet(path)
                page_count = len(tables)
            elif ext == ".csv":
                content, tables = self._process_csv(path)
                page_count = 1
            elif ext == ".json":
                content, tables = self._process_json(path)
                page_count = 1
            elif ext in [".txt", ".md"]:
                content = self._process_text(path)
                tables = []
                page_count = 1
            else:
                content = self._process_text(path)
                tables = []
                page_count = 1

            # Chunk the content
            chunks = self.chunker.chunk_text(content)

            # Generate summary (first chunk or first 200 chars)
            summary = chunks[0][:200] if chunks else content[:200]

            # Extract tags from filename and path
            tags = self._extract_tags(path)

            return ProcessedDocument(
                id=doc_id,
                title=path.stem,
                content=content,
                summary=summary,
                doc_type=doc_type,
                source_file=str(path),
                file_size=file_size,
                page_count=page_count,
                tables=tables,
                chunks=chunks,
                tags=tags,
                created_date=created_date,
            )

        except Exception as e:
            logger.error(f"Failed to process {path}: {e}")
            return None

    def _generate_doc_id(self, path: Path) -> str:
        """Generate unique document ID."""
        content = f"{path.absolute()}_{path.stat().st_mtime}"
        return hashlib.md5(content.encode()).hexdigest()[:16]

    def _process_with_docling(self, path: Path) -> Tuple[str, List[Dict], int]:
        """Process document using Docling."""
        result = self.converter.convert(str(path))

        # Extract text
        content = result.document.export_to_text()

        # Extract tables
        tables = []
        for table in result.document.tables:
            tables.append(
                {
                    "content": table.export_to_text(),
                    "rows": len(table.grid) if hasattr(table, "grid") else 0,
                }
            )

        page_count = (
            result.document.num_pages if hasattr(result.document, "num_pages") else 1
        )

        return content, tables, page_count

    def _process_spreadsheet(self, path: Path) -> Tuple[str, List[Dict]]:
        """Process Excel spreadsheet."""
        try:
            import pandas as pd

            # Read all sheets
            xl = pd.ExcelFile(path)
            content_parts = []
            tables = []

            for sheet_name in xl.sheet_names:
                df = pd.read_excel(xl, sheet_name=sheet_name)

                # Convert to text
                text = f"Sheet: {sheet_name}\n"
                text += df.to_string(index=False)
                content_parts.append(text)

                # Store as table
                tables.append(
                    {
                        "sheet": sheet_name,
                        "rows": len(df),
                        "columns": list(df.columns),
                        "content": text,
                    }
                )

            return "\n\n".join(content_parts), tables

        except Exception as e:
            logger.warning(f"Pandas not available or error: {e}")
            return self._process_text(path), []

    def _process_csv(self, path: Path) -> Tuple[str, List[Dict]]:
        """Process CSV file."""
        content_parts = []
        tables = []

        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.reader(f)
            rows = list(reader)

            if rows:
                headers = rows[0]
                content_parts.append(f"Columns: {', '.join(headers)}")

                for row in rows[1:]:
                    row_dict = dict(zip(headers, row))
                    content_parts.append(str(row_dict))

                tables.append({"rows": len(rows) - 1, "columns": headers})

        return "\n".join(content_parts), tables

    def _process_json(self, path: Path) -> Tuple[str, List[Dict]]:
        """Process JSON file."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        content = json.dumps(data, indent=2, default=str)

        # Try to extract structured data
        tables = []
        if isinstance(data, list) and data:
            tables.append(
                {
                    "type": "array",
                    "length": len(data),
                    "sample_keys": list(data[0].keys())
                    if isinstance(data[0], dict)
                    else [],
                }
            )
        elif isinstance(data, dict):
            tables.append({"type": "object", "keys": list(data.keys())})

        return content, tables

    def _process_text(self, path: Path) -> str:
        """Process plain text file."""
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    def _extract_tags(self, path: Path) -> List[str]:
        """Extract tags from filename and path."""
        tags = []

        # Add extension-based tag
        ext = path.suffix.lower().replace(".", "")
        if ext:
            tags.append(ext)

        # Add parent directory name
        parent = path.parent.name.lower()
        if parent and parent not in [".", "..", "data", "exports"]:
            tags.append(parent.replace(" ", "_"))

        # Extract common keywords from filename
        filename = path.stem.lower()
        keywords = [
            "bullhorn",
            "contact",
            "job",
            "placement",
            "activity",
            "note",
            "report",
            "summary",
        ]
        for keyword in keywords:
            if keyword in filename:
                tags.append(keyword)

        return list(set(tags))

    # =========================================
    # BATCH PROCESSING
    # =========================================

    def process_directory(
        self,
        directory: Path,
        recursive: bool = True,
        extensions: Optional[List[str]] = None,
    ) -> ProcessingResult:
        """
        Process all documents in a directory.

        Args:
            directory: Directory to process.
            recursive: If True, process subdirectories.
            extensions: List of extensions to process (all if None).

        Returns:
            ProcessingResult with all processed documents.
        """
        start_time = datetime.now()
        directory = Path(directory)

        if not directory.exists():
            logger.error(f"Directory not found: {directory}")
            return ProcessingResult(0, 0, 0, [], [], 0.0)

        # Find files
        pattern = "**/*" if recursive else "*"
        files = []
        for f in directory.glob(pattern):
            if f.is_file():
                ext = f.suffix.lower()
                if extensions is None or ext in extensions:
                    if ext in SUPPORTED_EXTENSIONS:
                        files.append(f)

        logger.info(f"Found {len(files)} files to process in {directory}")

        documents = []
        error_files = []

        for file in files:
            doc = self.process_file(file)
            if doc:
                documents.append(doc)
            else:
                error_files.append((str(file), "Processing failed"))

        duration = (datetime.now() - start_time).total_seconds()

        return ProcessingResult(
            total_files=len(files),
            processed=len(documents),
            errors=len(error_files),
            documents=documents,
            error_files=error_files,
            duration_seconds=duration,
        )

    def process_bullhorn_exports(self) -> ProcessingResult:
        """Process all Bullhorn export files."""
        if not BULLHORN_EXPORTS_DIR.exists():
            logger.warning(
                f"Bullhorn exports directory not found: {BULLHORN_EXPORTS_DIR}"
            )
            return ProcessingResult(0, 0, 0, [], [], 0.0)

        return self.process_directory(
            BULLHORN_EXPORTS_DIR,
            recursive=True,
            extensions=[".xls", ".xlsx", ".csv", ".txt"],
        )

    def process_prime_contacts(self) -> ProcessingResult:
        """Process prime contractor contact files."""
        if not PRIME_CONTACTS_DIR.exists():
            logger.warning(f"Prime contacts directory not found: {PRIME_CONTACTS_DIR}")
            return ProcessingResult(0, 0, 0, [], [], 0.0)

        return self.process_directory(
            PRIME_CONTACTS_DIR, recursive=True, extensions=[".csv", ".json"]
        )

    def process_outputs(self) -> ProcessingResult:
        """Process generated output files (briefings, playbooks)."""
        if not OUTPUTS_DIR.exists():
            logger.warning(f"Outputs directory not found: {OUTPUTS_DIR}")
            return ProcessingResult(0, 0, 0, [], [], 0.0)

        return self.process_directory(
            OUTPUTS_DIR, recursive=True, extensions=[".md", ".txt", ".json"]
        )


# =========================================
# CLI INTERFACE
# =========================================


def main():
    """CLI for the BD Document Processor."""
    import argparse

    parser = argparse.ArgumentParser(description="BD Document Processor")
    parser.add_argument("--file", type=str, help="Process single file")
    parser.add_argument("--dir", type=str, help="Process directory")
    parser.add_argument(
        "--bullhorn", action="store_true", help="Process Bullhorn exports"
    )
    parser.add_argument(
        "--contacts", action="store_true", help="Process prime contacts"
    )
    parser.add_argument("--outputs", action="store_true", help="Process output files")
    parser.add_argument("--all", action="store_true", help="Process all sources")
    parser.add_argument("--output", type=str, help="Output JSON file")
    parser.add_argument(
        "--recursive", action="store_true", default=True, help="Process subdirectories"
    )

    args = parser.parse_args()

    processor = BDDocumentProcessor()
    all_results = []

    if args.file:
        doc = processor.process_file(Path(args.file))
        if doc:
            print(f"Processed: {doc.title}")
            print(f"  Type: {doc.doc_type}")
            print(f"  Chunks: {len(doc.chunks)}")
            print(f"  Tables: {len(doc.tables)}")
            print(f"  Tags: {doc.tags}")
            all_results.append(doc)

    if args.dir:
        result = processor.process_directory(Path(args.dir), recursive=args.recursive)
        print(
            f"\nProcessed {result.processed}/{result.total_files} files ({result.errors} errors)"
        )
        print(f"Duration: {result.duration_seconds:.1f}s")
        all_results.extend(result.documents)

    if args.bullhorn or args.all:
        print("\nProcessing Bullhorn exports...")
        result = processor.process_bullhorn_exports()
        print(f"  Processed: {result.processed}/{result.total_files}")
        all_results.extend(result.documents)

    if args.contacts or args.all:
        print("\nProcessing prime contacts...")
        result = processor.process_prime_contacts()
        print(f"  Processed: {result.processed}/{result.total_files}")
        all_results.extend(result.documents)

    if args.outputs or args.all:
        print("\nProcessing outputs...")
        result = processor.process_outputs()
        print(f"  Processed: {result.processed}/{result.total_files}")
        all_results.extend(result.documents)

    # Save results
    if args.output and all_results:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump([d.to_dict() for d in all_results], f, indent=2)

        print(f"\nSaved {len(all_results)} documents to {output_path}")


if __name__ == "__main__":
    main()
