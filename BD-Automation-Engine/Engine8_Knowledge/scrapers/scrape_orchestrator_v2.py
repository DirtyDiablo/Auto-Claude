"""
Phase 24A — Scrape Orchestrator v2

Production scrape orchestrator coordinating all crawling engines.
Replaces Phase 15 basic orchestrator with intelligent scheduling
and source health tracking.
"""

import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------


@dataclass
class SourceConfig:
    """Configuration for a scraping source."""

    source_id: str = ""
    name: str = ""
    source_type: str = ""  # career_page, sam_gov, federal_docs, news
    url: Optional[str] = None
    api_config: Optional[Dict[str, Any]] = None
    cron_expression: str = "0 6 * * *"
    extraction_strategy: str = "auto"
    priority: str = "medium"
    enabled: bool = True
    created_at: Optional[str] = None


@dataclass
class SourceStatus:
    """Runtime status for a configured source."""

    config: Optional[SourceConfig] = None
    status: str = "never_run"  # active, paused, errored, never_run
    last_run: Optional[str] = None
    last_success: Optional[str] = None
    last_error: Optional[str] = None
    total_runs: int = 0
    success_rate: float = 0.0
    avg_items_per_run: float = 0.0


@dataclass
class SourceHealth:
    """Detailed health metrics for a source."""

    source_id: str = ""
    status: str = "unknown"
    success_rate: float = 0.0
    avg_crawl_time_ms: int = 0
    last_errors: List[str] = field(default_factory=list)
    data_quality_score: float = 0.0
    total_items_scraped: int = 0
    uptime_percent: float = 100.0


@dataclass
class OrchestratorReport:
    """Report from a complete scrape cycle."""

    cycle_id: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    sources_scraped: int = 0
    jobs_found: int = 0
    contracts_found: int = 0
    documents_processed: int = 0
    alerts_generated: int = 0
    errors: List[Dict[str, str]] = field(default_factory=list)
    routed_to_enrichment: int = 0
    duration_seconds: float = 0.0


@dataclass
class OrchestratorStats:
    """Aggregate orchestrator statistics."""

    total_sources: int = 0
    active_sources: int = 0
    paused_sources: int = 0
    errored_sources: int = 0
    jobs_today: int = 0
    jobs_week: int = 0
    jobs_month: int = 0
    documents_today: int = 0
    documents_week: int = 0
    contract_alerts: int = 0
    avg_scrape_duration_ms: int = 0
    last_full_cycle: Optional[str] = None


# ---------------------------------------------------------------------------
# Scrape Orchestrator v2
# ---------------------------------------------------------------------------


class ScrapeOrchestratorV2:
    """Coordinates all scraping across all sources."""

    def __init__(
        self,
        crawl_engine=None,
        sam_sync=None,
        doc_pipeline=None,
        scraper_client=None,
        storage_path: str = "Engine8_Knowledge/data/scrape_orchestrator",
    ):
        self.crawl_engine = crawl_engine
        self.sam_sync = sam_sync
        self.doc_pipeline = doc_pipeline
        self.scraper_client = scraper_client  # calls :8200

        self._storage = Path(storage_path)
        self._storage.mkdir(parents=True, exist_ok=True)
        self._sources_path = self._storage / "sources.json"
        self._stats_path = self._storage / "stats.json"
        self._history_path = self._storage / "history.json"

        self._sources: Dict[str, SourceConfig] = {}
        self._statuses: Dict[str, SourceStatus] = {}
        self._load_sources()

        logger.info(
            "scrape_orchestrator_v2_init",
            sources=len(self._sources),
        )

    # ------------------------------------------------------------------
    # Source Management
    # ------------------------------------------------------------------

    def _load_sources(self):
        if self._sources_path.exists():
            try:
                data = json.loads(self._sources_path.read_text())
                for item in data:
                    cfg = SourceConfig(**item)
                    self._sources[cfg.source_id] = cfg
                    self._statuses[cfg.source_id] = SourceStatus(
                        config=cfg,
                        status="active" if cfg.enabled else "paused",
                    )
            except Exception:
                pass

    def _save_sources(self):
        from dataclasses import asdict

        data = [asdict(cfg) for cfg in self._sources.values()]
        self._sources_path.write_text(json.dumps(data, indent=2, default=str))

    async def schedule_source(self, source: SourceConfig) -> str:
        """Add or update a scraping source."""
        if not source.source_id:
            source.source_id = f"src_{uuid.uuid4().hex[:8]}"
        if not source.created_at:
            source.created_at = datetime.utcnow().isoformat()

        self._sources[source.source_id] = source
        self._statuses[source.source_id] = SourceStatus(
            config=source,
            status="active" if source.enabled else "paused",
        )
        self._save_sources()
        logger.info("source_scheduled", id=source.source_id, name=source.name)
        return source.source_id

    async def list_sources(self) -> List[SourceStatus]:
        """All configured sources with status."""
        return list(self._statuses.values())

    async def get_source_health(self, source_id: str) -> SourceHealth:
        """Detailed health for a specific source."""
        status = self._statuses.get(source_id)
        if not status:
            return SourceHealth(source_id=source_id, status="not_found")

        return SourceHealth(
            source_id=source_id,
            status=status.status,
            success_rate=status.success_rate,
            avg_crawl_time_ms=0,
            last_errors=[status.last_error] if status.last_error else [],
            data_quality_score=status.success_rate,
            total_items_scraped=int(status.avg_items_per_run * status.total_runs),
            uptime_percent=status.success_rate * 100,
        )

    async def trigger_source(self, source_id: str) -> str:
        """Manually trigger a scrape for a specific source."""
        config = self._sources.get(source_id)
        if not config:
            raise ValueError(f"Source not found: {source_id}")

        run_id = f"run_{uuid.uuid4().hex[:8]}"
        logger.info("source_triggered", source_id=source_id, run_id=run_id)

        try:
            result = await self._run_source(config)
            status = self._statuses[source_id]
            status.last_run = datetime.utcnow().isoformat()
            status.last_success = status.last_run
            status.total_runs += 1
            status.status = "active"
            status.avg_items_per_run = (
                status.avg_items_per_run * (status.total_runs - 1) + result
            ) / status.total_runs
            status.success_rate = (
                status.success_rate * (status.total_runs - 1) + 1.0
            ) / status.total_runs
        except Exception as exc:
            status = self._statuses[source_id]
            status.last_run = datetime.utcnow().isoformat()
            status.last_error = str(exc)
            status.total_runs += 1
            status.status = "errored"
            status.success_rate = (
                status.success_rate * (status.total_runs - 1)
            ) / status.total_runs

        return run_id

    async def pause_source(self, source_id: str) -> bool:
        if source_id in self._statuses:
            self._statuses[source_id].status = "paused"
            if source_id in self._sources:
                self._sources[source_id].enabled = False
                self._save_sources()
            return True
        return False

    async def resume_source(self, source_id: str) -> bool:
        if source_id in self._statuses:
            self._statuses[source_id].status = "active"
            if source_id in self._sources:
                self._sources[source_id].enabled = True
                self._save_sources()
            return True
        return False

    # ------------------------------------------------------------------
    # Full Cycle
    # ------------------------------------------------------------------

    async def run_full_cycle(self) -> OrchestratorReport:
        """
        Complete scraping cycle:
        1. Job scraping across competitor career pages
        2. SAM.gov award monitoring
        3. Federal document discovery and processing
        4. Dedup across all sources
        5. Route to enrichment pipeline
        6. Generate cycle report
        """
        start = time.time()
        report = OrchestratorReport(
            cycle_id=f"cycle_{uuid.uuid4().hex[:8]}",
            started_at=datetime.utcnow().isoformat(),
        )

        # Phase 1: Job scraping
        for source_id, config in self._sources.items():
            if not config.enabled:
                continue
            if config.source_type != "career_page":
                continue
            try:
                items = await self._run_source(config)
                report.jobs_found += items
                report.sources_scraped += 1
            except Exception as exc:
                report.errors.append(
                    {
                        "source": config.name,
                        "error": str(exc),
                    }
                )

        # Phase 2: SAM.gov monitoring
        if self.sam_sync:
            try:
                alerts = await self.sam_sync.monitor_awards()
                report.contracts_found += len(alerts)
                report.alerts_generated += len(alerts)
            except Exception as exc:
                report.errors.append({"source": "sam_gov", "error": str(exc)})

        # Phase 3: Federal document processing
        if self.doc_pipeline:
            for source_id, config in self._sources.items():
                if not config.enabled or config.source_type != "federal_docs":
                    continue
                try:
                    docs = await self.doc_pipeline.discover_documents(
                        "sam_gov",
                        {"keywords": config.url.split() if config.url else []},
                    )
                    if docs:
                        batch = await self.doc_pipeline.process_batch(docs[:5])
                        report.documents_processed += batch.processed
                except Exception as exc:
                    report.errors.append(
                        {
                            "source": config.name,
                            "error": str(exc),
                        }
                    )

        # Phase 4: Route to enrichment via Data-Scraper
        if self.scraper_client and report.jobs_found > 0:
            try:
                import httpx

                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(
                        f"{self.scraper_client}/api/enrich",
                        json={"count": report.jobs_found},
                    )
                    if resp.status_code == 200:
                        report.routed_to_enrichment = report.jobs_found
            except Exception:
                pass

        elapsed = time.time() - start
        report.completed_at = datetime.utcnow().isoformat()
        report.duration_seconds = round(elapsed, 2)

        self._save_report(report)
        logger.info(
            "full_cycle_complete",
            cycle_id=report.cycle_id,
            jobs=report.jobs_found,
            contracts=report.contracts_found,
            docs=report.documents_processed,
            seconds=report.duration_seconds,
        )
        return report

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    async def get_orchestrator_stats(self) -> OrchestratorStats:
        """Aggregate statistics."""
        active = sum(1 for s in self._statuses.values() if s.status == "active")
        paused = sum(1 for s in self._statuses.values() if s.status == "paused")
        errored = sum(1 for s in self._statuses.values() if s.status == "errored")

        return OrchestratorStats(
            total_sources=len(self._sources),
            active_sources=active,
            paused_sources=paused,
            errored_sources=errored,
            last_full_cycle=self._get_last_cycle_time(),
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _run_source(self, config: SourceConfig) -> int:
        """Run a single source and return item count."""
        items = 0

        if config.source_type == "career_page" and self.crawl_engine:
            if config.url:
                result = await self.crawl_engine.crawl_url(
                    config.url,
                    extraction_strategy=config.extraction_strategy,
                )
                items = len(result.extracted_data)
            else:
                company = config.name.lower().replace(" careers", "")
                data = await self.crawl_engine.crawl_competitor_careers(company)
                items = len(data)

        elif config.source_type == "sam_gov" and self.sam_sync:
            from Engine8_Knowledge.scrapers.sam_gov_sync import SearchQuery

            query = SearchQuery(
                keywords=config.url.split() if config.url else [],
                limit=20,
            )
            awards = await self.sam_sync.search_awards(query)
            items = len(awards)

        elif config.source_type == "federal_docs" and self.doc_pipeline:
            docs = await self.doc_pipeline.discover_documents(
                "sam_gov", {"keywords": config.url.split() if config.url else []}
            )
            items = len(docs)

        return items

    def _save_report(self, report: OrchestratorReport):
        from dataclasses import asdict

        history = []
        if self._history_path.exists():
            try:
                history = json.loads(self._history_path.read_text())
            except Exception:
                pass
        history.append(asdict(report))
        history = history[-100:]  # Keep last 100
        self._history_path.write_text(json.dumps(history, indent=2, default=str))

    def _get_last_cycle_time(self) -> Optional[str]:
        if self._history_path.exists():
            try:
                history = json.loads(self._history_path.read_text())
                if history:
                    return history[-1].get("completed_at")
            except Exception:
                pass
        return None


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_orchestrator: Optional[ScrapeOrchestratorV2] = None


def get_scrape_orchestrator(**kwargs) -> ScrapeOrchestratorV2:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = ScrapeOrchestratorV2(**kwargs)
    return _orchestrator
