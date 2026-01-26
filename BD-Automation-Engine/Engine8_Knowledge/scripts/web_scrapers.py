"""
Web Scraping: Firecrawl + Crawl4AI
"""

import os
import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ScrapedContent:
    url: str
    title: str
    content: str
    metadata: Dict
    source: str


class FirecrawlScraper:
    """Firecrawl for JS-rendered sites."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("FIRECRAWL_API_KEY")
        self.app = None

        if self.api_key:
            try:
                from firecrawl import FirecrawlApp
                self.app = FirecrawlApp(api_key=self.api_key)
            except ImportError:
                logger.warning("firecrawl-py not installed")
            except Exception as e:
                logger.warning(f"Firecrawl init error: {e}")

    def scrape_url(self, url: str) -> Optional[ScrapedContent]:
        if not self.app:
            return None

        try:
            result = self.app.scrape_url(url, params={"formats": ["markdown"]})
            return ScrapedContent(
                url=url,
                title=result.get("metadata", {}).get("title", ""),
                content=result.get("markdown", ""),
                metadata=result.get("metadata", {}),
                source="firecrawl"
            )
        except Exception as e:
            logger.error(f"Firecrawl error: {e}")
            return None

    def crawl_site(self, url: str, max_pages: int = 10) -> List[ScrapedContent]:
        """Crawl entire site."""
        if not self.app:
            return []

        try:
            result = self.app.crawl_url(
                url,
                params={"limit": max_pages, "formats": ["markdown"]}
            )
            pages = result.get("data", [])
            return [
                ScrapedContent(
                    url=p.get("metadata", {}).get("url", url),
                    title=p.get("metadata", {}).get("title", ""),
                    content=p.get("markdown", ""),
                    metadata=p.get("metadata", {}),
                    source="firecrawl"
                )
                for p in pages
            ]
        except Exception as e:
            logger.error(f"Firecrawl crawl error: {e}")
            return []


class Crawl4AIScraper:
    """Crawl4AI for LLM-optimized extraction."""

    async def scrape_url(self, url: str) -> Optional[ScrapedContent]:
        try:
            from crawl4ai import AsyncWebCrawler

            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(url=url)
                return ScrapedContent(
                    url=url,
                    title=result.metadata.get("title", "") if result.metadata else "",
                    content=result.markdown or "",
                    metadata=result.metadata or {},
                    source="crawl4ai"
                )
        except ImportError:
            logger.warning("crawl4ai not installed")
            return None
        except Exception as e:
            logger.error(f"Crawl4AI error: {e}")
            return None

    async def scrape_multiple(self, urls: List[str]) -> List[ScrapedContent]:
        """Scrape multiple URLs concurrently."""
        results = []
        try:
            from crawl4ai import AsyncWebCrawler

            async with AsyncWebCrawler() as crawler:
                for url in urls:
                    try:
                        result = await crawler.arun(url=url)
                        results.append(ScrapedContent(
                            url=url,
                            title=result.metadata.get("title", "") if result.metadata else "",
                            content=result.markdown or "",
                            metadata=result.metadata or {},
                            source="crawl4ai"
                        ))
                    except Exception as e:
                        logger.error(f"Error scraping {url}: {e}")
        except ImportError:
            logger.warning("crawl4ai not installed")
        except Exception as e:
            logger.error(f"Crawl4AI batch error: {e}")

        return results


class UnifiedWebScraper:
    """Unified scraper using best method per URL."""

    def __init__(self):
        self.firecrawl = FirecrawlScraper()
        self.crawl4ai = Crawl4AIScraper()

        self.js_domains = ["linkedin.com", "sam.gov", "usajobs.gov", "twitter.com", "x.com"]

    def _needs_js(self, url: str) -> bool:
        return any(d in url for d in self.js_domains)

    async def scrape(self, url: str) -> Optional[ScrapedContent]:
        if self._needs_js(url) and self.firecrawl.app:
            return self.firecrawl.scrape_url(url)
        return await self.crawl4ai.scrape_url(url)

    def scrape_sync(self, url: str) -> Optional[ScrapedContent]:
        """Synchronous scrape for convenience."""
        return asyncio.run(self.scrape(url))

    async def scrape_multiple(self, urls: List[str]) -> List[ScrapedContent]:
        results = []
        for url in urls:
            content = await self.scrape(url)
            if content:
                results.append(content)
        return results

    async def scrape_federal_sites(self, sites: List[str] = None) -> List[ScrapedContent]:
        """Scrape common federal BD sites."""
        sites = sites or [
            "https://sam.gov/content/opportunities",
            "https://www.usajobs.gov/",
        ]
        return await self.scrape_multiple(sites)


_scraper_instance = None

def get_web_scraper() -> UnifiedWebScraper:
    global _scraper_instance
    if _scraper_instance is None:
        _scraper_instance = UnifiedWebScraper()
    return _scraper_instance
