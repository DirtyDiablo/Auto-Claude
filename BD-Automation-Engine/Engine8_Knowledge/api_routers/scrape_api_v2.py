"""
Phase 24A — Scrape API v2

20 FastAPI endpoints for AI-native scraping, SAM.gov contracts,
and federal document processing.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import structlog
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

logger = structlog.get_logger(__name__)

# Allowed document root for file processing
_ALLOWED_DOC_ROOT = Path(
    os.getenv("FEDERAL_DOCS_DIR", str(Path(__file__).resolve().parent.parent / "data"))
).resolve()

# Blocked URL patterns for SSRF prevention
_SSRF_BLOCKED_HOSTS = {
    "localhost", "127.0.0.1", "0.0.0.0", "::1",
    "169.254.169.254",  # AWS/GCP metadata
    "metadata.google.internal",
}
_SSRF_BLOCKED_PREFIXES = ("10.", "172.16.", "172.17.", "172.18.", "172.19.",
                          "172.20.", "172.21.", "172.22.", "172.23.", "172.24.",
                          "172.25.", "172.26.", "172.27.", "172.28.", "172.29.",
                          "172.30.", "172.31.", "192.168.")


def _validate_url(url: str) -> str:
    """Validate URL is not targeting internal/private networks."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(400, f"Only http/https URLs allowed, got: {parsed.scheme}")
    host = parsed.hostname or ""
    if host in _SSRF_BLOCKED_HOSTS or host.startswith(_SSRF_BLOCKED_PREFIXES):
        raise HTTPException(400, "URLs targeting internal/private networks are not allowed")
    return url


def _validate_file_path(file_path: str) -> Path:
    """Validate file path is within allowed document root."""
    resolved = Path(file_path).resolve()
    if not str(resolved).startswith(str(_ALLOWED_DOC_ROOT)):
        raise HTTPException(400, f"File path must be within {_ALLOWED_DOC_ROOT}")
    return resolved

router = APIRouter(tags=["scrape-v2"])


# ---------------------------------------------------------------------------
# Request/Response Models
# ---------------------------------------------------------------------------


class CrawlUrlRequest(BaseModel):
    url: str
    extraction_strategy: str = "auto"
    custom_schema: Optional[Dict[str, Any]] = None


class CrawlSiteRequest(BaseModel):
    base_url: str
    max_pages: int = 50
    extraction_strategy: str = "auto"


class CompetitorCrawlRequest(BaseModel):
    company: str


class AwardSearchRequest(BaseModel):
    keywords: List[str] = []
    naics_codes: List[str] = []
    set_aside: Optional[str] = None
    awardee: Optional[str] = None
    agency: Optional[str] = None
    min_value: Optional[float] = None
    limit: int = 50


class OpportunitySearchRequest(BaseModel):
    keywords: List[str] = []
    naics_codes: List[str] = []
    agency: Optional[str] = None
    set_aside: Optional[str] = None
    type_filter: Optional[str] = None
    limit: int = 50


class WatchConfigRequest(BaseModel):
    name: str
    keywords: List[str] = []
    naics_codes: List[str] = []
    companies: List[str] = []
    agencies: List[str] = []
    min_value: Optional[float] = None
    alert_on: List[str] = ["new_award", "new_opportunity"]


class SourceConfigRequest(BaseModel):
    name: str
    source_type: str
    url: Optional[str] = None
    cron_expression: str = "0 6 * * *"
    extraction_strategy: str = "auto"
    priority: str = "medium"
    enabled: bool = True


class DiscoverDocsRequest(BaseModel):
    source: str = "sam_gov"
    keywords: List[str] = []
    url: Optional[str] = None
    max_pages: int = 20


class ProcessDocRequest(BaseModel):
    file_path: str


class BatchProcessRequest(BaseModel):
    doc_refs: List[Dict[str, Any]]
    max_concurrent: int = 3


# ---------------------------------------------------------------------------
# Lazy dependency getters
# ---------------------------------------------------------------------------


def _get_crawl_engine():
    try:
        from Engine8_Knowledge.scrapers.crawl4ai_engine import get_crawl4ai_engine

        return get_crawl4ai_engine()
    except Exception as exc:
        logger.warning("crawl4ai_engine_unavailable", error=str(exc))
        return None


def _get_sam_sync():
    try:
        from Engine8_Knowledge.scrapers.sam_gov_sync import get_sam_gov_sync

        return get_sam_gov_sync()
    except Exception as exc:
        logger.warning("sam_sync_unavailable", error=str(exc))
        return None


def _get_doc_pipeline():
    try:
        from Engine8_Knowledge.scrapers.federal_doc_pipeline import (
            get_federal_doc_pipeline,
        )

        return get_federal_doc_pipeline()
    except Exception as exc:
        logger.warning("doc_pipeline_unavailable", error=str(exc))
        return None


def _get_orchestrator():
    try:
        from Engine8_Knowledge.scrapers.scrape_orchestrator_v2 import (
            get_scrape_orchestrator,
        )

        return get_scrape_orchestrator()
    except Exception as exc:
        logger.warning("orchestrator_unavailable", error=str(exc))
        return None


# ---------------------------------------------------------------------------
# Crawl4AI Endpoints
# ---------------------------------------------------------------------------


@router.post("/scrape/crawl")
async def crawl_url(req: CrawlUrlRequest):
    """Crawl a URL with Crawl4AI."""
    _validate_url(req.url)
    engine = _get_crawl_engine()
    if not engine:
        raise HTTPException(503, "Crawl4AI engine not available")
    from dataclasses import asdict

    result = await engine.crawl_url(req.url, req.extraction_strategy)
    return asdict(result)


@router.post("/scrape/crawl-site")
async def crawl_site(req: CrawlSiteRequest):
    """Crawl an entire site."""
    _validate_url(req.base_url)
    engine = _get_crawl_engine()
    if not engine:
        raise HTTPException(503, "Crawl4AI engine not available")
    from dataclasses import asdict

    results = await engine.crawl_site(
        req.base_url, req.max_pages, req.extraction_strategy
    )
    return {"results": [asdict(r) for r in results], "total": len(results)}


@router.post("/scrape/crawl-competitor")
async def crawl_competitor(req: CompetitorCrawlRequest):
    """Crawl a competitor career page by company name."""
    engine = _get_crawl_engine()
    if not engine:
        raise HTTPException(503, "Crawl4AI engine not available")
    data = await engine.crawl_competitor_careers(req.company)
    return {"company": req.company, "jobs": data, "total": len(data)}


# ---------------------------------------------------------------------------
# Orchestrator Endpoints
# ---------------------------------------------------------------------------


@router.post("/scrape/cycle")
async def trigger_full_cycle():
    """Trigger a full scrape cycle."""
    orch = _get_orchestrator()
    if not orch:
        raise HTTPException(503, "Scrape orchestrator not available")
    from dataclasses import asdict

    report = await orch.run_full_cycle()
    return asdict(report)


@router.get("/scrape/sources")
async def list_sources():
    """List all configured scrape sources."""
    orch = _get_orchestrator()
    if not orch:
        raise HTTPException(503, "Scrape orchestrator not available")
    from dataclasses import asdict

    sources = await orch.list_sources()
    return {"sources": [asdict(s) for s in sources], "total": len(sources)}


@router.post("/scrape/sources")
async def add_source(req: SourceConfigRequest):
    """Add a new scrape source."""
    orch = _get_orchestrator()
    if not orch:
        raise HTTPException(503, "Scrape orchestrator not available")
    from Engine8_Knowledge.scrapers.scrape_orchestrator_v2 import SourceConfig

    cfg = SourceConfig(
        name=req.name,
        source_type=req.source_type,
        url=req.url,
        cron_expression=req.cron_expression,
        extraction_strategy=req.extraction_strategy,
        priority=req.priority,
        enabled=req.enabled,
    )
    source_id = await orch.schedule_source(cfg)
    return {"source_id": source_id, "name": req.name}


@router.get("/scrape/sources/{source_id}/health")
async def get_source_health(source_id: str):
    """Get source health details."""
    orch = _get_orchestrator()
    if not orch:
        raise HTTPException(503, "Scrape orchestrator not available")
    from dataclasses import asdict

    health = await orch.get_source_health(source_id)
    return asdict(health)


@router.post("/scrape/sources/{source_id}/trigger")
async def trigger_source(source_id: str):
    """Manually trigger a source."""
    orch = _get_orchestrator()
    if not orch:
        raise HTTPException(503, "Scrape orchestrator not available")
    try:
        run_id = await orch.trigger_source(source_id)
        return {"run_id": run_id, "source_id": source_id}
    except ValueError as exc:
        raise HTTPException(404, str(exc))


@router.patch("/scrape/sources/{source_id}/toggle")
async def toggle_source(source_id: str, enabled: bool = Query(True)):
    """Pause/resume a source."""
    orch = _get_orchestrator()
    if not orch:
        raise HTTPException(503, "Scrape orchestrator not available")
    if enabled:
        ok = await orch.resume_source(source_id)
    else:
        ok = await orch.pause_source(source_id)
    return {"source_id": source_id, "enabled": enabled, "success": ok}


@router.get("/scrape/stats")
async def orchestrator_stats():
    """Orchestrator aggregate statistics."""
    orch = _get_orchestrator()
    if not orch:
        raise HTTPException(503, "Scrape orchestrator not available")
    from dataclasses import asdict

    stats = await orch.get_orchestrator_stats()
    return asdict(stats)


# ---------------------------------------------------------------------------
# SAM.gov Endpoints
# ---------------------------------------------------------------------------


@router.post("/sam/search-awards")
async def search_awards(req: AwardSearchRequest):
    """Search SAM.gov contract awards."""
    sam = _get_sam_sync()
    if not sam:
        raise HTTPException(503, "SAM.gov sync not available")
    from Engine8_Knowledge.scrapers.sam_gov_sync import SearchQuery
    from dataclasses import asdict

    query = SearchQuery(
        keywords=req.keywords,
        naics_codes=req.naics_codes,
        set_aside=req.set_aside,
        awardee=req.awardee,
        agency=req.agency,
        min_value=req.min_value,
        limit=req.limit,
    )
    awards = await sam.search_awards(query)
    return {"awards": [asdict(a) for a in awards], "total": len(awards)}


@router.post("/sam/search-opportunities")
async def search_opportunities(req: OpportunitySearchRequest):
    """Search active solicitations."""
    sam = _get_sam_sync()
    if not sam:
        raise HTTPException(503, "SAM.gov sync not available")
    from Engine8_Knowledge.scrapers.sam_gov_sync import OpportunityQuery
    from dataclasses import asdict

    query = OpportunityQuery(
        keywords=req.keywords,
        naics_codes=req.naics_codes,
        agency=req.agency,
        set_aside=req.set_aside,
        type_filter=req.type_filter,
        limit=req.limit,
    )
    opps = await sam.search_opportunities(query)
    return {"opportunities": [asdict(o) for o in opps], "total": len(opps)}


@router.post("/sam/monitor")
async def monitor_awards():
    """Run award monitoring against watch list."""
    sam = _get_sam_sync()
    if not sam:
        raise HTTPException(503, "SAM.gov sync not available")
    from dataclasses import asdict

    alerts = await sam.monitor_awards()
    return {"alerts": [asdict(a) for a in alerts], "total": len(alerts)}


@router.get("/sam/watches")
async def list_watches():
    """List watch configurations."""
    sam = _get_sam_sync()
    if not sam:
        raise HTTPException(503, "SAM.gov sync not available")
    from dataclasses import asdict

    watches = sam.list_watches()
    return {"watches": [asdict(w) for w in watches], "total": len(watches)}


@router.post("/sam/watches")
async def create_watch(req: WatchConfigRequest):
    """Create a watch configuration."""
    sam = _get_sam_sync()
    if not sam:
        raise HTTPException(503, "SAM.gov sync not available")
    from Engine8_Knowledge.scrapers.sam_gov_sync import WatchConfig
    from dataclasses import asdict

    watch = WatchConfig(
        name=req.name,
        keywords=req.keywords,
        naics_codes=req.naics_codes,
        companies=req.companies,
        agencies=req.agencies,
        min_value=req.min_value,
        alert_on=req.alert_on,
    )
    created = sam.add_watch(watch)
    return asdict(created)


@router.delete("/sam/watches/{watch_id}")
async def remove_watch(watch_id: str):
    """Remove a watch configuration."""
    sam = _get_sam_sync()
    if not sam:
        raise HTTPException(503, "SAM.gov sync not available")
    ok = sam.remove_watch(watch_id)
    if not ok:
        raise HTTPException(404, f"Watch not found: {watch_id}")
    return {"deleted": True, "watch_id": watch_id}


# ---------------------------------------------------------------------------
# Federal Document Endpoints
# ---------------------------------------------------------------------------


@router.post("/federal-docs/discover")
async def discover_docs(req: DiscoverDocsRequest):
    """Discover federal documents from a source."""
    pipeline = _get_doc_pipeline()
    if not pipeline:
        raise HTTPException(503, "Federal doc pipeline not available")
    from dataclasses import asdict

    docs = await pipeline.discover_documents(
        req.source,
        {"keywords": req.keywords, "url": req.url, "max_pages": req.max_pages},
    )
    return {"documents": [asdict(d) for d in docs], "total": len(docs)}


@router.post("/federal-docs/process")
async def process_doc(req: ProcessDocRequest):
    """Process a downloaded federal document."""
    safe_path = _validate_file_path(req.file_path)
    pipeline = _get_doc_pipeline()
    if not pipeline:
        raise HTTPException(503, "Federal doc pipeline not available")
    from dataclasses import asdict

    try:
        result = await pipeline.process_document(str(safe_path))
        return asdict(result)
    except FileNotFoundError:
        raise HTTPException(404, "File not found")


@router.post("/federal-docs/batch")
async def batch_process(req: BatchProcessRequest):
    """Batch process multiple documents."""
    pipeline = _get_doc_pipeline()
    if not pipeline:
        raise HTTPException(503, "Federal doc pipeline not available")
    from Engine8_Knowledge.scrapers.federal_doc_pipeline import DocumentRef
    from dataclasses import asdict

    refs = [DocumentRef(**d) for d in req.doc_refs]
    result = await pipeline.process_batch(refs, req.max_concurrent)
    return asdict(result)


@router.get("/federal-docs/recent")
async def recent_docs(limit: int = Query(20)):
    """List recently processed documents."""
    # Return from index file
    pipeline = _get_doc_pipeline()
    if not pipeline:
        return {"documents": [], "total": 0}
    index_path = pipeline._output_dir / "index.json"
    if index_path.exists():
        import json

        try:
            data = json.loads(index_path.read_text())
            return {"documents": data[-limit:], "total": len(data)}
        except Exception:
            pass
    return {"documents": [], "total": 0}
