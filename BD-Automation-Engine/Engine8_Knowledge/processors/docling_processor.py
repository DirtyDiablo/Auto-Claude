"""
Docling Document Processor for BD Intelligence Hub.

Converts PDF/DOCX files into chunked, embedded vectors for Qdrant ingestion.
Optimized for federal defense documents with accurate table extraction.
"""

import uuid
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger("BD-DoclingProcessor")

try:
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False
    logger.warning("Docling not available")

try:
    from docling_core.transforms.chunker import HybridChunker
    CHUNKER_AVAILABLE = True
except (ImportError, RuntimeError):
    CHUNKER_AVAILABLE = False
    logger.warning("Docling chunker not available, using simple splitting")

try:
    from utils.llm_retry import openai_retry
except ImportError:
    # Fallback: identity decorator if utils not on path
    def openai_retry(fn):
        return fn


def _get_converter() -> "DocumentConverter":
    """Create a Docling converter optimized for federal documents."""
    pipeline_options = PdfPipelineOptions(do_table_structure=True)
    pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE

    return DocumentConverter(
        format_options={
            "pdf": PdfFormatOption(pipeline_options=pipeline_options),
        }
    )


def _simple_chunk(text: str, max_tokens: int = 512) -> List[str]:
    """Simple fallback chunker when HybridChunker unavailable."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), max_tokens):
        chunk = " ".join(words[i : i + max_tokens])
        if chunk.strip():
            chunks.append(chunk)
    return chunks


def process_document(
    file_path: str,
    collection: str = "federal_contracts",
    max_tokens: int = 512,
    doc_type: str = "unknown",
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Process a document with Docling and return chunks ready for Qdrant.

    Returns dict with 'chunks' list, each having 'text' and 'metadata'.
    """
    if not DOCLING_AVAILABLE:
        return {"error": "Docling not installed", "chunks": []}

    path = Path(file_path)
    if not path.exists():
        return {"error": f"File not found: {file_path}", "chunks": []}

    converter = _get_converter()

    try:
        result = converter.convert(str(path))
        doc = result.document
        full_text = doc.export_to_markdown()
    except Exception as e:
        logger.error("Docling conversion failed for %s: %s", file_path, e)
        return {"error": str(e), "chunks": []}

    # Chunk the document
    if CHUNKER_AVAILABLE:
        try:
            chunker = HybridChunker(max_tokens=max_tokens)
            chunk_iter = chunker.chunk(doc)
            texts = [chunk.text for chunk in chunk_iter if chunk.text.strip()]
        except Exception as e:
            logger.warning("HybridChunker failed, using simple: %s", e)
            texts = _simple_chunk(full_text, max_tokens)
    else:
        texts = _simple_chunk(full_text, max_tokens)

    if not texts:
        return {"error": "No chunks produced", "chunks": []}

    base_meta = {
        "source_file": path.name,
        "doc_type": doc_type,
        "collection": collection,
        "processed_at": datetime.now().isoformat(),
        "total_chunks": len(texts),
    }
    if metadata:
        base_meta.update(metadata)

    chunks = []
    for i, text in enumerate(texts):
        chunk_id = str(uuid.uuid5(
            uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8"),
            f"{path.name}:chunk:{i}",
        ))
        chunks.append({
            "id": chunk_id,
            "text": text,
            "metadata": {**base_meta, "chunk_index": i},
        })

    return {
        "file": path.name,
        "total_chunks": len(chunks),
        "chunks": chunks,
    }


@openai_retry
def _embed_batch(openai_client, model_name: str, texts: List[str]):
    """Generate embeddings for a batch of texts with retry."""
    resp = openai_client.embeddings.create(model=model_name, input=texts)
    return [d.embedding for d in resp.data]


def ingest_document_to_qdrant(
    file_path: str,
    store,
    collection: str = "federal_contracts",
    max_tokens: int = 512,
    doc_type: str = "unknown",
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Process a document and ingest all chunks into Qdrant."""
    from qdrant_client.models import PointStruct

    result = process_document(file_path, collection, max_tokens, doc_type, metadata)
    if "error" in result and not result.get("chunks"):
        return result

    client = store.client
    openai_client = store.openai_client
    model_name = store.model_name

    indexed = 0
    errors = 0

    # Batch embed
    texts = [c["text"] for c in result["chunks"]]
    batch_size = 100

    for start in range(0, len(texts), batch_size):
        batch = texts[start : start + batch_size]
        batch_chunks = result["chunks"][start : start + batch_size]

        try:
            embeddings = _embed_batch(openai_client, model_name, batch)
        except Exception as e:
            logger.error("Embedding batch failed: %s", e)
            errors += len(batch)
            continue

        points = []
        for chunk, embedding in zip(batch_chunks, embeddings):
            payload = {**chunk["metadata"], "text": chunk["text"][:2000]}
            points.append(PointStruct(
                id=chunk["id"],
                vector=embedding,
                payload=payload,
            ))

        try:
            client.upsert(collection_name=collection, points=points)
            indexed += len(points)
        except Exception as e:
            logger.error("Qdrant upsert failed: %s", e)
            errors += len(points)

    return {
        "file": result["file"],
        "collection": collection,
        "total_chunks": result["total_chunks"],
        "indexed": indexed,
        "errors": errors,
        "timestamp": datetime.now().isoformat(),
    }
