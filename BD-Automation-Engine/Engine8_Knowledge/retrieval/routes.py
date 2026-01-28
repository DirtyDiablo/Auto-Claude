"""
FastAPI routes for PageIndex retrieval.
Import this into main api.py during integration step.
"""
from fastapi import APIRouter, HTTPException
from typing import Optional
from pathlib import Path

try:
    from .page_index import PageIndex, PageIndexRAG
    from .page_index_loader import extract_pdf_pages, generate_document_id
except ImportError:
    from page_index import PageIndex, PageIndexRAG
    from page_index_loader import extract_pdf_pages, generate_document_id

router = APIRouter(prefix="/pageindex", tags=["PageIndex Retrieval"])

# PageIndex instance
_page_index = None
_page_rag = None


def get_page_index() -> PageIndex:
    global _page_index
    if _page_index is None:
        _page_index = PageIndex(db_path="data/page_index.db")
    return _page_index


def get_page_rag() -> PageIndexRAG:
    global _page_rag
    if _page_rag is None:
        _page_rag = PageIndexRAG(get_page_index())
    return _page_rag


@router.get("/search")
async def pageindex_search(
    query: str,
    top_k: int = 5,
    document_filter: Optional[str] = None
):
    """Search with explainable page-level retrieval."""
    index = get_page_index()
    results = index.search(query, top_k=top_k, document_filter=document_filter)
    return {
        "query": query,
        "results": [
            {
                "citation": r.citation,
                "content": r.content[:1000],
                "score": r.score,
                "matched_terms": r.matched_terms,
                "page_id": r.page_id
            }
            for r in results
        ]
    }


@router.get("/citation/{page_id}")
async def get_citation(page_id: str, context_pages: int = 1):
    """Get full citation context for a page."""
    index = get_page_index()
    result = index.get_citation_context(page_id, context_pages)
    if not result:
        raise HTTPException(status_code=404, detail="Page not found")
    return result


@router.post("/index-document")
async def index_document(file_path: str):
    """Index a PDF document."""
    path = Path(file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    if path.suffix.lower() != '.pdf':
        raise HTTPException(status_code=400, detail="Only PDF files supported")

    try:
        doc_id = generate_document_id(file_path)
        pages = extract_pdf_pages(file_path)

        index = get_page_index()
        num_indexed = index.index_document(
            document_id=doc_id,
            document_name=path.name,
            pages=pages
        )

        return {"document_id": doc_id, "pages_indexed": num_indexed}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/document/{document_id}")
async def delete_document(document_id: str):
    """Delete a document from the index."""
    index = get_page_index()
    deleted = index.delete_document(document_id)
    return {"document_id": document_id, "pages_deleted": deleted}


@router.get("/stats")
async def pageindex_stats():
    """Get PageIndex statistics."""
    index = get_page_index()
    return index.stats()


@router.post("/answer")
async def answer_with_citations(question: str, top_k: int = 5):
    """Answer question with full citations."""
    rag = get_page_rag()
    return rag.answer_with_citations(question, top_k=top_k)
