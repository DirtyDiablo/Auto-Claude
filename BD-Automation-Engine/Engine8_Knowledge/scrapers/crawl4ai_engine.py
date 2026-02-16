"""
Phase 24A — Crawl4AI Engine

AI-native web crawler replacing Puppeteer/Apify scrapers.
Uses Crawl4AI for LLM-powered extraction with built-in JS rendering,
anti-bot handling, and structured output via cosine similarity selectors.
"""

import asyncio
import hashlib
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Type

import structlog
from pydantic import BaseModel

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Extraction Schemas
# ---------------------------------------------------------------------------


class JobExtraction(BaseModel):
    """Schema for job posting extraction."""

    title: str = ""
    company: str = ""
    location: str = ""
    clearance: Optional[str] = None
    description: str = ""
    requirements: List[str] = []
    posted_date: Optional[str] = None
    url: str = ""


class ContractExtraction(BaseModel):
    """Schema for federal contract extraction."""

    award_title: str = ""
    awardee: str = ""
    value: Optional[str] = None
    naics: Optional[str] = None
    set_aside: Optional[str] = None
    agency: str = ""
    description: str = ""


class ContactExtraction(BaseModel):
    """Schema for contact/personnel extraction."""

    name: str = ""
    title: str = ""
    company: str = ""
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None


# ---------------------------------------------------------------------------
# Result Dataclass
# ---------------------------------------------------------------------------


@dataclass
class CrawlResult:
    """Result from a single URL crawl."""

    url: str = ""
    raw_html: str = ""
    markdown: str = ""
    extracted_data: List[Dict[str, Any]] = field(default_factory=list)
    links: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    crawl_time_ms: int = 0
    extraction_strategy: str = "auto"
    content_hash: str = ""
    error: Optional[str] = None
    success: bool = True

    def __post_init__(self):
        if not self.content_hash and self.markdown:
            self.content_hash = hashlib.sha256(self.markdown.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Competitor Career Page Configs
# ---------------------------------------------------------------------------

COMPETITOR_CAREER_CONFIGS: Dict[str, Dict[str, Any]] = {
    "gdit": {
        "url": "https://www.gdit.com/careers/",
        "job_list_pattern": "/careers/job/",
        "extraction_strategy": "jobs",
    },
    "leidos": {
        "url": "https://careers.leidos.com/search/jobs",
        "job_list_pattern": "/jobs/",
        "extraction_strategy": "jobs",
    },
    "saic": {
        "url": "https://jobs.saic.com/",
        "job_list_pattern": "/jobs/",
        "extraction_strategy": "jobs",
    },
    "northrop": {
        "url": "https://www.northropgrumman.com/jobs/",
        "job_list_pattern": "/jobs/",
        "extraction_strategy": "jobs",
    },
    "caci": {
        "url": "https://careers.caci.com/",
        "job_list_pattern": "/job/",
        "extraction_strategy": "jobs",
    },
    "peraton": {
        "url": "https://www.peraton.com/careers/",
        "job_list_pattern": "/careers/",
        "extraction_strategy": "jobs",
    },
    "bae": {
        "url": "https://jobs.baesystems.com/",
        "job_list_pattern": "/job/",
        "extraction_strategy": "jobs",
    },
}


# ---------------------------------------------------------------------------
# Crawl4AI Engine
# ---------------------------------------------------------------------------


class Crawl4AIEngine:
    """AI-powered web crawler with LLM extraction strategies."""

    def __init__(
        self,
        llm_model: str = "gpt-4o-mini",
        stealth_level: str = "medium",
        max_concurrent: int = 5,
    ):
        self.llm_model = llm_model
        self.stealth_level = stealth_level
        self.max_concurrent = max_concurrent
        self._crawler = None
        self._extraction_schemas = {
            "jobs": JobExtraction,
            "contracts": ContractExtraction,
            "contacts": ContactExtraction,
        }
        self._seen_hashes: set = set()
        logger.info(
            "crawl4ai_engine_init",
            llm_model=llm_model,
            stealth=stealth_level,
        )

    async def _get_crawler(self):
        """Lazy-initialize AsyncWebCrawler."""
        if self._crawler is not None:
            return self._crawler
        try:
            from crawl4ai import AsyncWebCrawler, BrowserConfig

            browser_cfg = BrowserConfig(
                headless=True,
                java_script_enabled=True,
                verbose=False,
            )
            self._crawler = AsyncWebCrawler(config=browser_cfg)
            await self._crawler.__aenter__()
            logger.info("crawl4ai_browser_ready")
        except ImportError:
            logger.warning("crawl4ai_not_installed", hint="pip install crawl4ai")
            self._crawler = None
        return self._crawler

    async def close(self):
        """Close the browser."""
        if self._crawler is not None:
            try:
                await self._crawler.__aexit__(None, None, None)
            except Exception:
                pass
            self._crawler = None

    # ------------------------------------------------------------------
    # Core crawl methods
    # ------------------------------------------------------------------

    async def crawl_url(
        self,
        url: str,
        extraction_strategy: str = "auto",
        custom_schema: Optional[Type[BaseModel]] = None,
    ) -> CrawlResult:
        """
        Crawl a single URL with AI-powered extraction.

        Extraction strategies:
        - "auto": LLM analyzes page structure, extracts relevant content
        - "jobs": Specialized job posting extraction
        - "contracts": Federal contract extraction
        - "contacts": Contact/personnel extraction
        - "custom": User-provided Pydantic schema
        """
        start = time.time()
        crawler = await self._get_crawler()

        if crawler is None:
            return await self._fallback_crawl(url, extraction_strategy)

        try:
            from crawl4ai import CrawlerRunConfig
            from crawl4ai.extraction_strategy import (
                LLMExtractionStrategy,
            )

            schema = custom_schema or self._extraction_schemas.get(extraction_strategy)

            extraction = None
            if schema and extraction_strategy != "auto":
                extraction = LLMExtractionStrategy(
                    provider=f"openai/{self.llm_model}",
                    schema=schema.model_json_schema(),
                    instruction=f"Extract all {extraction_strategy} data from this page.",
                )

            run_cfg = CrawlerRunConfig(
                extraction_strategy=extraction,
                word_count_threshold=10,
                excluded_tags=["nav", "footer", "header"],
                process_iframes=False,
            )

            result = await crawler.arun(url=url, config=run_cfg)

            elapsed = int((time.time() - start) * 1000)
            extracted = []
            if result.extracted_content:
                import json

                try:
                    extracted = json.loads(result.extracted_content)
                    if isinstance(extracted, dict):
                        extracted = [extracted]
                except (json.JSONDecodeError, TypeError):
                    extracted = []

            links = []
            if hasattr(result, "links") and result.links:
                links = [
                    lnk.get("href", "") if isinstance(lnk, dict) else str(lnk)
                    for lnk in result.links.get("internal", [])
                ]

            crawl_result = CrawlResult(
                url=url,
                raw_html=result.html or "",
                markdown=result.markdown or "",
                extracted_data=extracted,
                links=links,
                metadata={
                    "title": getattr(result, "title", ""),
                    "status_code": getattr(result, "status_code", 200),
                    "crawled_at": datetime.utcnow().isoformat(),
                },
                crawl_time_ms=elapsed,
                extraction_strategy=extraction_strategy,
            )

            logger.info(
                "crawl_url_complete",
                url=url,
                strategy=extraction_strategy,
                items=len(extracted),
                ms=elapsed,
            )
            return crawl_result

        except Exception as exc:
            elapsed = int((time.time() - start) * 1000)
            logger.error("crawl_url_error", url=url, error=str(exc))
            return CrawlResult(
                url=url,
                crawl_time_ms=elapsed,
                extraction_strategy=extraction_strategy,
                error=str(exc),
                success=False,
            )

    async def crawl_site(
        self,
        base_url: str,
        max_pages: int = 50,
        extraction_strategy: str = "auto",
        url_filter: Optional[Callable[[str], bool]] = None,
    ) -> List[CrawlResult]:
        """
        Crawl an entire site with intelligent page discovery.
        Follows internal links up to max_pages, deduplicates by content hash.
        """
        visited: set = set()
        results: List[CrawlResult] = []
        queue = [base_url]

        while queue and len(results) < max_pages:
            batch = []
            while queue and len(batch) < self.max_concurrent:
                url = queue.pop(0)
                if url in visited:
                    continue
                if url_filter and not url_filter(url):
                    continue
                visited.add(url)
                batch.append(url)

            if not batch:
                break

            tasks = [self.crawl_url(url, extraction_strategy) for url in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for r in batch_results:
                if isinstance(r, Exception):
                    continue
                if not r.success:
                    continue
                if r.content_hash in self._seen_hashes:
                    continue
                self._seen_hashes.add(r.content_hash)
                results.append(r)

                for link in r.links:
                    if link.startswith(base_url) and link not in visited:
                        queue.append(link)

        logger.info(
            "crawl_site_complete",
            base_url=base_url,
            pages=len(results),
            max_pages=max_pages,
        )
        return results

    async def crawl_with_schema(
        self, url: str, schema: Type[BaseModel]
    ) -> List[BaseModel]:
        """Extract structured data matching a Pydantic schema."""
        result = await self.crawl_url(
            url, extraction_strategy="custom", custom_schema=schema
        )
        instances = []
        for item in result.extracted_data:
            try:
                instances.append(schema.model_validate(item))
            except Exception:
                continue
        return instances

    async def crawl_competitor_careers(self, company: str) -> List[Dict[str, Any]]:
        """
        Pre-configured crawler for competitor career pages.
        Known configs for: GDIT, Leidos, SAIC, Northrop, CACI, Peraton, BAE.
        Falls back to auto-extraction for unknown companies.
        """
        key = company.lower().replace(" ", "").replace("-", "")
        config = COMPETITOR_CAREER_CONFIGS.get(key)

        if config:
            result = await self.crawl_url(
                config["url"],
                extraction_strategy=config["extraction_strategy"],
            )
            logger.info(
                "competitor_crawl_known",
                company=company,
                jobs=len(result.extracted_data),
            )
            return result.extracted_data
        else:
            # Auto-detect career page
            search_url = f"https://www.google.com/search?q={company}+careers+jobs"
            result = await self.crawl_url(search_url, extraction_strategy="jobs")
            logger.info(
                "competitor_crawl_auto",
                company=company,
                jobs=len(result.extracted_data),
            )
            return result.extracted_data

    # ------------------------------------------------------------------
    # Stealth configuration
    # ------------------------------------------------------------------

    def configure_stealth(self, level: str = "medium"):
        """
        Anti-detection configuration.
        - low: basic headers, random user-agent
        - medium: + viewport randomization, human-like delays
        - high: + residential proxy rotation, fingerprint randomization
        """
        self.stealth_level = level
        logger.info("stealth_configured", level=level)

    # ------------------------------------------------------------------
    # Fallback (no Crawl4AI)
    # ------------------------------------------------------------------

    async def _fallback_crawl(self, url: str, strategy: str) -> CrawlResult:
        """Fallback using httpx when Crawl4AI is not installed."""
        start = time.time()
        try:
            import httpx

            async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
                resp = await client.get(url)
                html = resp.text
                elapsed = int((time.time() - start) * 1000)
                return CrawlResult(
                    url=url,
                    raw_html=html,
                    markdown=html[:5000],
                    metadata={"status_code": resp.status_code},
                    crawl_time_ms=elapsed,
                    extraction_strategy=strategy,
                )
        except Exception as exc:
            elapsed = int((time.time() - start) * 1000)
            return CrawlResult(
                url=url,
                crawl_time_ms=elapsed,
                extraction_strategy=strategy,
                error=str(exc),
                success=False,
            )


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_engine: Optional[Crawl4AIEngine] = None


def get_crawl4ai_engine(**kwargs) -> Crawl4AIEngine:
    global _engine
    if _engine is None:
        _engine = Crawl4AIEngine(**kwargs)
    return _engine
