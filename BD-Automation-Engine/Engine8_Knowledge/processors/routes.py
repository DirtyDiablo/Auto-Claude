"""
FastAPI routes for Document Processing.
Import this into main api.py during integration step.
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File
from typing import Optional, List
from pathlib import Path
import tempfile
import shutil

try:
    from .document_pipeline import BDDocumentPipeline, process_document, batch_process_folder
except ImportError:
    from document_pipeline import BDDocumentPipeline, process_document, batch_process_folder

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


@router.post("/batch")
async def api_batch_process(
    folder_path: str,
    background_tasks: BackgroundTasks,
    recursive: bool = True
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
        "supported_types": [".pdf", ".docx", ".pptx"]
    }
