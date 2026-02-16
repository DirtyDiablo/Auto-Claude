"""
Docling Document Processor - 30x faster PDF processing
Repository: https://github.com/docling-project/docling (10,000+ stars)
"""

import os
import re
from typing import Dict, List
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from docling.document_converter import DocumentConverter

    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False
    logger.warning("Docling not available, using basic processing")


class DoclingProcessor:
    """
    High-performance document processor.
    Extracts text, tables, and federal metadata from PDFs.
    """

    def __init__(self, output_dir: str = None):
        self.output_dir = output_dir or "./docling_output"
        os.makedirs(self.output_dir, exist_ok=True)

        if DOCLING_AVAILABLE:
            self.converter = DocumentConverter()
            self.backend = "docling"
        else:
            self.converter = None
            self.backend = "basic"

    def process_pdf(self, pdf_path: str) -> Dict:
        """Process a PDF document."""
        if self.backend == "docling":
            result = self.converter.convert(pdf_path)
            doc = result.document

            return {
                "filename": os.path.basename(pdf_path),
                "text": doc.export_to_markdown(),
                "pages": len(doc.pages) if hasattr(doc, "pages") else 0,
                "tables": self._extract_tables(doc),
                "metadata": self.extract_federal_metadata(
                    {"text": doc.export_to_markdown()}
                ),
            }
        else:
            # Basic fallback using pypdf
            try:
                from pypdf import PdfReader

                reader = PdfReader(pdf_path)
                text = "\n".join(page.extract_text() or "" for page in reader.pages)
                return {
                    "filename": os.path.basename(pdf_path),
                    "text": text,
                    "pages": len(reader.pages),
                    "tables": [],
                    "metadata": self.extract_federal_metadata({"text": text}),
                }
            except Exception as e:
                logger.error(f"PDF processing error: {e}")
                return {
                    "filename": os.path.basename(pdf_path),
                    "text": "",
                    "error": str(e),
                }

    def _extract_tables(self, doc) -> List[Dict]:
        tables = []
        if hasattr(doc, "tables"):
            for i, table in enumerate(doc.tables):
                tables.append({"id": i, "data": str(table)})
        return tables

    def process_directory(
        self, directory: str, extensions: List[str] = None
    ) -> List[Dict]:
        """Process all documents in directory."""
        extensions = extensions or [".pdf"]
        results = []
        path = Path(directory)

        for ext in extensions:
            for file_path in path.glob(f"**/*{ext}"):
                try:
                    result = self.process_pdf(str(file_path))
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")

        return results

    def extract_federal_metadata(self, doc: Dict) -> Dict:
        """Extract federal-specific metadata."""
        text = doc.get("text", "")

        return {
            "contract_numbers": re.findall(
                r"[A-Z]{1,2}\d{2}[A-Z]{3,4}-?\d{2}-[A-Z]-\d{4}", text
            ),
            "solicitation_numbers": re.findall(
                r"[A-Z0-9]{2,4}-\d{2}-[A-Z]-\d{4,6}", text
            ),
            "cage_codes": re.findall(r"\b[0-9A-Z]{5}\b", text)[:10],
            "naics_codes": re.findall(r"\b\d{6}\b", text)[:5],
        }

    def process_text(self, text: str, doc_id: str = "unknown") -> Dict:
        """Process raw text content."""
        return {
            "filename": doc_id,
            "text": text,
            "pages": 0,
            "tables": [],
            "metadata": self.extract_federal_metadata({"text": text}),
        }


_docling_instance = None


def get_docling(output_dir: str = None) -> DoclingProcessor:
    global _docling_instance
    if _docling_instance is None:
        _docling_instance = DoclingProcessor(output_dir)
    return _docling_instance
