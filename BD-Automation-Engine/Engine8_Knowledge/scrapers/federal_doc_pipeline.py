"""
Phase 24A — Federal Document Pipeline

End-to-end pipeline: discover → download → process → index → alert.
Combines Crawl4AI for discovery with Docling (Phase 22B) for processing.
"""

import hashlib
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
class DocumentRef:
    """Reference to a discovered federal document."""
    doc_id: str = ""
    url: str = ""
    title: str = ""
    doc_type: str = ""  # RFI, RFP, SOW, contract_mod, award_notice, other
    agency: str = ""
    posted_date: Optional[str] = None
    size_estimate: Optional[int] = None
    content_type: str = ""  # application/pdf, application/docx
    source: str = ""  # sam_gov, fpds, agency_site
    discovered_at: Optional[str] = None


@dataclass
class ProcessedFederalDoc:
    """Fully processed federal document."""
    source_path: str = ""
    doc_type: str = ""
    title: str = ""
    agency: str = ""
    summary: str = ""
    entities: Dict[str, Any] = field(default_factory=dict)
    key_fields: Dict[str, Any] = field(default_factory=dict)
    full_text: str = ""
    tables: List[Dict[str, Any]] = field(default_factory=list)
    qdrant_id: Optional[str] = None
    neo4j_id: Optional[str] = None
    processing_time_seconds: float = 0.0
    content_hash: str = ""


@dataclass
class BatchResult:
    """Result from batch processing."""
    total: int = 0
    processed: int = 0
    failed: int = 0
    documents: List[ProcessedFederalDoc] = field(default_factory=list)
    errors: List[Dict[str, str]] = field(default_factory=list)
    duration_seconds: float = 0.0


@dataclass
class DocumentAlert:
    """Alert for new federal documents matching watch criteria."""
    alert_id: str = ""
    doc_ref: Optional[DocumentRef] = None
    matched_criteria: str = ""
    relevance_score: float = 0.0
    recommended_action: str = ""
    created_at: Optional[str] = None


# ---------------------------------------------------------------------------
# Classification Keywords
# ---------------------------------------------------------------------------

DOC_TYPE_KEYWORDS = {
    "RFP": ["request for proposal", "rfp", "solicitation", "full and open"],
    "RFI": ["request for information", "rfi", "sources sought", "market research"],
    "SOW": ["statement of work", "sow", "scope of work", "performance work statement", "pws"],
    "contract_mod": ["modification", "contract mod", "amendment", "change order"],
    "award_notice": ["award notice", "contract award", "task order award", "delivery order"],
}

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/msword",
}

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


# ---------------------------------------------------------------------------
# Federal Document Pipeline
# ---------------------------------------------------------------------------


class FederalDocPipeline:
    """End-to-end pipeline: discover → download → process → index → alert."""

    def __init__(
        self,
        crawl_engine=None,
        hub_client=None,
        output_dir: str = "Engine8_Knowledge/data/federal_docs",
    ):
        self.crawler = crawl_engine
        self.hub = hub_client
        self._output_dir = Path(output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._seen_hashes: set = set()
        self._index_path = self._output_dir / "index.json"
        logger.info("federal_doc_pipeline_init", output_dir=str(self._output_dir))

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    async def discover_documents(
        self, source: str, query: Dict[str, Any]
    ) -> List[DocumentRef]:
        """
        Discover documents from federal sources:
        - "sam_gov": Search SAM.gov attachments for solicitations
        - "fpds": FPDS contract documents
        - "agency_sites": Agency-specific document repositories
        """
        docs: List[DocumentRef] = []

        if source == "sam_gov":
            docs = await self._discover_sam_gov(query)
        elif source == "fpds":
            docs = await self._discover_fpds(query)
        elif source == "agency_sites":
            docs = await self._discover_agency_sites(query)
        else:
            logger.warning("unknown_source", source=source)

        logger.info("discover_documents", source=source, found=len(docs))
        return docs

    async def _discover_sam_gov(self, query: Dict[str, Any]) -> List[DocumentRef]:
        """Discover documents from SAM.gov."""
        docs = []
        if not self.crawler:
            return docs

        keywords = query.get("keywords", [])
        url = f"https://sam.gov/search/?keywords={'+'.join(keywords)}&sort=-relevance&index=opp"

        result = await self.crawler.crawl_url(url, extraction_strategy="contracts")
        for item in result.extracted_data:
            doc = DocumentRef(
                doc_id=f"sam_{uuid.uuid4().hex[:8]}",
                url=item.get("url", ""),
                title=item.get("title", item.get("award_title", "")),
                agency=item.get("agency", ""),
                source="sam_gov",
                discovered_at=datetime.utcnow().isoformat(),
            )
            docs.append(doc)

        for link in result.links:
            if any(ext in link.lower() for ext in [".pdf", ".docx", ".xlsx"]):
                docs.append(DocumentRef(
                    doc_id=f"sam_{uuid.uuid4().hex[:8]}",
                    url=link,
                    source="sam_gov",
                    content_type=self._guess_content_type(link),
                    discovered_at=datetime.utcnow().isoformat(),
                ))
        return docs

    async def _discover_fpds(self, query: Dict[str, Any]) -> List[DocumentRef]:
        """Discover documents from FPDS."""
        if not self.crawler:
            return []
        keywords = query.get("keywords", [])
        url = f"https://www.fpds.gov/ezsearch/search.do?q={'+'.join(keywords)}"
        result = await self.crawler.crawl_url(url, extraction_strategy="contracts")
        docs = []
        for item in result.extracted_data:
            docs.append(DocumentRef(
                doc_id=f"fpds_{uuid.uuid4().hex[:8]}",
                url=item.get("url", ""),
                title=item.get("title", ""),
                source="fpds",
                discovered_at=datetime.utcnow().isoformat(),
            ))
        return docs

    async def _discover_agency_sites(self, query: Dict[str, Any]) -> List[DocumentRef]:
        """Discover documents from agency websites."""
        if not self.crawler:
            return []
        url = query.get("url", "")
        if not url:
            return []
        results = await self.crawler.crawl_site(
            url,
            max_pages=query.get("max_pages", 20),
            url_filter=lambda u: any(ext in u.lower() for ext in [".pdf", ".docx", "document"]),
        )
        docs = []
        for r in results:
            for link in r.links:
                if any(ext in link.lower() for ext in [".pdf", ".docx", ".xlsx"]):
                    docs.append(DocumentRef(
                        doc_id=f"agency_{uuid.uuid4().hex[:8]}",
                        url=link,
                        source="agency_site",
                        content_type=self._guess_content_type(link),
                        discovered_at=datetime.utcnow().isoformat(),
                    ))
        return docs

    # ------------------------------------------------------------------
    # Download
    # ------------------------------------------------------------------

    async def download_document(
        self, doc_ref: DocumentRef, output_dir: Optional[str] = None
    ) -> str:
        """
        Download document with validation and dedup.
        Returns local file path.
        """
        dest_dir = Path(output_dir) if output_dir else self._output_dir
        dest_dir.mkdir(parents=True, exist_ok=True)

        if not doc_ref.url:
            raise ValueError("Document URL is empty")

        try:
            import httpx
            async with httpx.AsyncClient(
                follow_redirects=True, timeout=60.0
            ) as client:
                resp = await client.get(doc_ref.url)
                resp.raise_for_status()

                content_type = resp.headers.get("content-type", "").split(";")[0].strip()
                if content_type and content_type not in ALLOWED_CONTENT_TYPES:
                    # Still allow if extension matches
                    if not any(doc_ref.url.lower().endswith(ext) for ext in [".pdf", ".docx", ".xlsx"]):
                        raise ValueError(f"Disallowed content type: {content_type}")

                content = resp.content
                if len(content) > MAX_FILE_SIZE:
                    raise ValueError(f"File too large: {len(content)} bytes")

                content_hash = hashlib.sha256(content).hexdigest()[:16]
                if content_hash in self._seen_hashes:
                    logger.info("download_dedup", url=doc_ref.url, hash=content_hash)
                    existing = list(dest_dir.glob(f"*_{content_hash}.*"))
                    if existing:
                        return str(existing[0])

                self._seen_hashes.add(content_hash)
                ext = self._url_extension(doc_ref.url) or ".pdf"
                filename = f"{doc_ref.doc_id}_{content_hash}{ext}"
                filepath = dest_dir / filename
                filepath.write_bytes(content)

                logger.info(
                    "download_complete",
                    url=doc_ref.url,
                    size=len(content),
                    path=str(filepath),
                )
                return str(filepath)

        except Exception as exc:
            logger.error("download_error", url=doc_ref.url, error=str(exc))
            raise

    # ------------------------------------------------------------------
    # Processing
    # ------------------------------------------------------------------

    async def process_document(self, file_path: str) -> ProcessedFederalDoc:
        """
        Full processing pipeline:
        1. Extract text/tables via Docling (Hub API)
        2. Run NER for entities
        3. Classify document type
        4. Extract key fields
        5. Generate summary
        6. Index in Qdrant and Neo4j
        """
        start = time.time()
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        content_hash = hashlib.sha256(path.read_bytes()).hexdigest()[:16]

        # Step 1: Extract text
        full_text = ""
        tables = []
        if self.hub:
            try:
                import httpx
                async with httpx.AsyncClient(timeout=120.0) as client:
                    with open(file_path, "rb") as f:
                        resp = await client.post(
                            f"{self.hub}/ingest/process",
                            files={"file": (path.name, f)},
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            full_text = data.get("text", "")
                            tables = data.get("tables", [])
            except Exception as exc:
                logger.warning("docling_process_error", error=str(exc))

        if not full_text:
            full_text = self._basic_text_extract(file_path)

        # Step 2-3: Classify and extract entities
        doc_type = self._classify_doc_type(full_text)
        entities = self._extract_entities(full_text)

        # Step 4: Extract key fields based on type
        key_fields = self._extract_key_fields(full_text, doc_type)

        # Step 5: Generate summary
        summary = self._generate_summary(full_text, doc_type)

        # Step 6: Index
        qdrant_id = None
        neo4j_id = None
        if self.hub:
            try:
                import httpx
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(
                        f"{self.hub}/search",
                        json={
                            "text": summary,
                            "collection": "federal_docs",
                            "metadata": {
                                "doc_type": doc_type,
                                "title": entities.get("title", path.stem),
                                "agency": entities.get("agency", ""),
                            },
                        },
                    )
                    if resp.status_code == 200:
                        qdrant_id = resp.json().get("id")
            except Exception:
                pass

        elapsed = time.time() - start

        result = ProcessedFederalDoc(
            source_path=file_path,
            doc_type=doc_type,
            title=entities.get("title", path.stem),
            agency=entities.get("agency", "Unknown"),
            summary=summary,
            entities=entities,
            key_fields=key_fields,
            full_text=full_text[:50000],
            tables=tables,
            qdrant_id=qdrant_id,
            neo4j_id=neo4j_id,
            processing_time_seconds=round(elapsed, 2),
            content_hash=content_hash,
        )

        logger.info(
            "process_document_complete",
            doc_type=doc_type,
            path=file_path,
            seconds=round(elapsed, 2),
        )
        return result

    async def process_batch(
        self, doc_refs: List[DocumentRef], max_concurrent: int = 3
    ) -> BatchResult:
        """Process multiple documents with progress tracking."""
        import asyncio

        start = time.time()
        result = BatchResult(total=len(doc_refs))
        semaphore = asyncio.Semaphore(max_concurrent)

        async def _process_one(ref: DocumentRef):
            async with semaphore:
                try:
                    path = await self.download_document(ref)
                    doc = await self.process_document(path)
                    result.processed += 1
                    result.documents.append(doc)
                except Exception as exc:
                    result.failed += 1
                    result.errors.append({
                        "doc_id": ref.doc_id,
                        "url": ref.url,
                        "error": str(exc),
                    })

        tasks = [_process_one(ref) for ref in doc_refs]
        await asyncio.gather(*tasks)

        result.duration_seconds = round(time.time() - start, 2)
        logger.info(
            "batch_process_complete",
            total=result.total,
            processed=result.processed,
            failed=result.failed,
            seconds=result.duration_seconds,
        )
        return result

    async def monitor_new_documents(
        self, watch_configs: List[Dict[str, Any]]
    ) -> List[DocumentAlert]:
        """Check for new documents matching watch criteria."""
        alerts: List[DocumentAlert] = []

        for config in watch_configs:
            source = config.get("source", "sam_gov")
            docs = await self.discover_documents(source, config)

            for doc in docs:
                relevance = self._score_relevance(doc, config)
                if relevance >= 0.3:
                    alerts.append(DocumentAlert(
                        alert_id=f"alert_{uuid.uuid4().hex[:8]}",
                        doc_ref=doc,
                        matched_criteria=config.get("name", source),
                        relevance_score=relevance,
                        recommended_action="Review and process document",
                        created_at=datetime.utcnow().isoformat(),
                    ))

        logger.info("monitor_new_documents", configs=len(watch_configs), alerts=len(alerts))
        return alerts

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _classify_doc_type(self, text: str) -> str:
        text_lower = text[:3000].lower()
        best_type = "other"
        best_score = 0
        for doc_type, keywords in DOC_TYPE_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > best_score:
                best_score = score
                best_type = doc_type
        return best_type

    def _extract_entities(self, text: str) -> Dict[str, Any]:
        """Basic entity extraction from text."""
        import re
        entities: Dict[str, Any] = {}
        title_match = re.search(r"(?:Subject|Title|RE):\s*(.+?)(?:\n|$)", text[:2000], re.I)
        if title_match:
            entities["title"] = title_match.group(1).strip()

        agency_keywords = [
            "Department of Defense", "Department of the Air Force",
            "Department of the Army", "Department of the Navy",
            "Defense Intelligence Agency", "National Security Agency",
            "NGA", "NRO", "DISA", "DARPA",
        ]
        for agency in agency_keywords:
            if agency.lower() in text[:5000].lower():
                entities["agency"] = agency
                break

        naics_match = re.search(r"NAICS[:\s]+(\d{6})", text[:5000])
        if naics_match:
            entities["naics"] = naics_match.group(1)

        value_match = re.search(r"\$[\d,]+(?:\.\d{2})?(?:\s*(?:million|billion|M|B))?", text[:5000])
        if value_match:
            entities["value"] = value_match.group(0)

        return entities

    def _extract_key_fields(self, text: str, doc_type: str) -> Dict[str, Any]:
        """Extract type-specific key fields."""
        fields: Dict[str, Any] = {}
        text_lower = text[:10000].lower()

        if doc_type == "RFP":
            if "evaluation criteria" in text_lower:
                fields["has_evaluation_criteria"] = True
            if "set-aside" in text_lower or "set aside" in text_lower:
                fields["has_set_aside"] = True
        elif doc_type == "SOW":
            if "deliverable" in text_lower:
                fields["has_deliverables"] = True
            if "clearance" in text_lower or "security" in text_lower:
                fields["has_clearance_req"] = True
        elif doc_type == "award_notice":
            if "period of performance" in text_lower:
                fields["has_pop"] = True

        return fields

    def _generate_summary(self, text: str, doc_type: str) -> str:
        """Generate a basic summary (first 500 chars of meaningful text)."""
        lines = [l.strip() for l in text.split("\n") if len(l.strip()) > 20]
        summary_text = " ".join(lines[:10])[:500]
        return f"[{doc_type.upper()}] {summary_text}"

    def _basic_text_extract(self, file_path: str) -> str:
        """Fallback text extraction."""
        try:
            return Path(file_path).read_text(errors="ignore")[:50000]
        except Exception:
            return ""

    def _guess_content_type(self, url: str) -> str:
        url_lower = url.lower()
        if ".pdf" in url_lower:
            return "application/pdf"
        elif ".docx" in url_lower:
            return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        elif ".xlsx" in url_lower:
            return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        return ""

    def _url_extension(self, url: str) -> str:
        for ext in [".pdf", ".docx", ".xlsx", ".doc", ".xls"]:
            if ext in url.lower():
                return ext
        return ".pdf"

    def _score_relevance(self, doc: DocumentRef, config: Dict[str, Any]) -> float:
        score = 0.0
        text = f"{doc.title} {doc.agency}".lower()
        keywords = config.get("keywords", [])
        if keywords:
            matches = sum(1 for kw in keywords if kw.lower() in text)
            score += 0.6 * (matches / max(len(keywords), 1))
        if config.get("agency") and config["agency"].lower() in doc.agency.lower():
            score += 0.4
        return min(score, 1.0)


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_pipeline: Optional[FederalDocPipeline] = None


def get_federal_doc_pipeline(**kwargs) -> FederalDocPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = FederalDocPipeline(**kwargs)
    return _pipeline
