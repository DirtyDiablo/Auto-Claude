"""
FastAPI routes for UltraRAG multi-step reasoning.
Import this into main api.py during integration step.
"""
from fastapi import APIRouter, HTTPException

try:
    from .ultra_rag_integration import BDUltraRAG
    from .page_index import PageIndex
except ImportError:
    from ultra_rag_integration import BDUltraRAG
    from page_index import PageIndex

router = APIRouter(prefix="/ultrarag", tags=["UltraRAG Multi-Step Reasoning"])

# UltraRAG instance
_ultra_rag = None


def get_ultra_rag() -> BDUltraRAG:
    """Get or create UltraRAG instance."""
    global _ultra_rag
    if _ultra_rag is None:
        # Get absolute path for PageIndex database
        import os
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(base_dir, "data", "page_index.db")

        # Initialize with PageIndex if available
        try:
            page_index = PageIndex(db_path=db_path)
            print(f"[OK] UltraRAG PageIndex loaded: {page_index.stats()}")
        except Exception as e:
            print(f"[WARN] PageIndex init failed: {e}")
            page_index = None

        _ultra_rag = BDUltraRAG(
            qdrant_client=None,  # Add your Qdrant client
            bm25_index=None,     # Add your BM25 index
            page_index=page_index,
            knowledge_graph=None,
            llm_client=None      # Add your LLM client
        )
    return _ultra_rag


@router.get("/query")
async def ultrarag_query(query: str, pipeline: str = "auto"):
    """
    Multi-step reasoning query with automatic pipeline selection.

    Pipelines:
    - auto: Automatic selection based on query
    - simple: Basic retrieval and synthesis
    - complex: Query decomposition for complex questions
    - factcheck: Strict verification with citations
    - multisource: Aggregation from all sources
    - bd_intelligence: BD-specific analysis
    """
    try:
        ultra = get_ultra_rag()
        plan = await ultra.ultra.query(query, pipeline)

        return {
            "query": query,
            "pipeline": plan.pipeline_used,
            "answer": plan.final_answer,
            "confidence": plan.confidence,
            "sub_queries": plan.sub_queries,
            "citations": plan.citations,
            "execution_time_ms": plan.execution_time_ms
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analyze-program/{program_name}")
async def ultrarag_analyze_program(program_name: str):
    """Deep program analysis using multi-step reasoning."""
    try:
        ultra = get_ultra_rag()
        return await ultra.analyze_program(program_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/research-contact/{contact_name}")
async def ultrarag_research_contact(contact_name: str):
    """Comprehensive contact research using multi-source retrieval."""
    try:
        ultra = get_ultra_rag()
        return await ultra.research_contact(contact_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compare-programs")
async def ultrarag_compare_programs(program1: str, program2: str):
    """Compare two programs using complex query decomposition."""
    try:
        ultra = get_ultra_rag()
        return await ultra.compare_programs(program1, program2)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/verify")
async def ultrarag_verify_fact(claim: str):
    """Verify a factual claim using the factcheck pipeline."""
    try:
        ultra = get_ultra_rag()
        return await ultra.verify_fact(claim)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pipelines")
async def list_pipelines():
    """List available reasoning pipelines."""
    ultra = get_ultra_rag()
    return {
        "pipelines": ultra.list_pipelines()
    }


@router.get("/status")
async def ultrarag_status():
    """Check UltraRAG status and configuration."""
    ultra = get_ultra_rag()
    return {
        "status": "ready",
        "pipelines_available": len(ultra.ultra.pipelines),
        "llm_enabled": ultra.llm is not None,
        "page_index_enabled": ultra.page_index is not None,
        "qdrant_enabled": ultra.qdrant is not None
    }
