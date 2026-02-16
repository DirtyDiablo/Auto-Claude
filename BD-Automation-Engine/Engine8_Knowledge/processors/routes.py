"""
FastAPI routes for Document Processing.
Import this into main api.py during integration step.
"""

import os
import structlog
from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File
from pathlib import Path
import tempfile
import shutil

try:
    from .document_pipeline import (
        BDDocumentPipeline,
        process_document,
        batch_process_folder,
    )
except ImportError:
    from document_pipeline import (
        BDDocumentPipeline,
        process_document,
        batch_process_folder,
    )

try:
    from .docling_processor import ingest_document_to_qdrant
except ImportError:
    from docling_processor import ingest_document_to_qdrant

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/documents", tags=["Document Processing"])

# Pipeline instance
_pipeline = None


def get_pipeline() -> BDDocumentPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = BDDocumentPipeline()
    return _pipeline


@router.post("/process")
async def api_process_document(file_path: str):
    """Process a document from file path."""
    try:
        result = process_document(file_path)
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload")
async def upload_and_process(file: UploadFile = File(...)):
    """Upload and process a document."""
    # Save to temp file
    suffix = Path(file.filename).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        result = process_document(tmp_path)
        result["original_filename"] = file.filename
        return result
    finally:
        Path(tmp_path).unlink(missing_ok=True)


@router.post("/ingest")
async def ingest_document(
    file: UploadFile = File(...),
    collection: str = "documents",
    doc_type: str = "unknown",
):
    """Upload a document, parse with Docling, embed, and index into Qdrant."""
    suffix = Path(file.filename).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        # Get or build a lightweight store object for Qdrant + OpenAI access
        store = _get_ingest_store()
        if store is None:
            raise HTTPException(
                status_code=503,
                detail="Qdrant/OpenAI not available for ingestion",
            )

        result = ingest_document_to_qdrant(
            file_path=tmp_path,
            store=store,
            collection=collection,
            doc_type=doc_type,
            metadata={"original_filename": file.filename},
        )

        if "error" in result and not result.get("chunks"):
            raise HTTPException(status_code=422, detail=result["error"])

        result["original_filename"] = file.filename
        logger.info(
            "document_ingested",
            file=file.filename,
            collection=collection,
            chunks=result.get("total_chunks", 0),
            indexed=result.get("indexed", 0),
        )
        return result
    finally:
        Path(tmp_path).unlink(missing_ok=True)


# Lightweight store for ingest endpoint
_ingest_store = None


def _get_ingest_store():
    """Build a minimal store object with .client, .openai_client, .model_name."""
    global _ingest_store
    if _ingest_store is not None:
        return _ingest_store

    try:
        from qdrant_client import QdrantClient
        import openai

        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        client = QdrantClient(url=qdrant_url, timeout=30)
        openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        class _IngestStore:
            pass

        store = _IngestStore()
        store.client = client
        store.openai_client = openai_client
        store.model_name = "text-embedding-3-small"
        _ingest_store = store
        return store
    except Exception as e:
        logger.warning("ingest_store_init_failed", error=str(e))
        return None


@router.post("/batch")
async def api_batch_process(
    folder_path: str, _background_tasks: BackgroundTasks, recursive: bool = True
):
    """Process all documents in a folder."""
    try:
        # For large folders, could run in background
        result = batch_process_folder(folder_path, recursive=recursive)
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Folder not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def processor_status():
    """Check document processor status."""
    pipeline = get_pipeline()
    return {
        "status": "ready",
        "docling_available": pipeline.use_docling,
        "fallback": "pymupdf",
        "supported_types": [".pdf", ".docx", ".pptx"],
    }
