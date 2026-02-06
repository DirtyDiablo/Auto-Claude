"""
Engine 6 Quality Monitor - Live data quality monitoring across all Qdrant collections.

Provides:
- Collection health checks (vector counts, segment status, index health)
- Data quality scoring (payload completeness, freshness)
- Aggregated quality report for dashboard consumption
"""
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional, Any

from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse

logger = logging.getLogger("BD-QualityMonitor")

REQUIRED_PAYLOAD_FIELDS = {
    "contacts": ["name", "company"],
    "programs": ["name"],
    "documents": ["title"],
    "activities": ["type"],
    "jobs": ["title"],
    "bullhorn_notes": ["action", "comments_text"],
    "federal_contracts": ["title"],
    "intelligence_reports": ["title"],
    "opportunities": ["title"],
    "primes": ["name"],
}


@dataclass
class CollectionHealth:
    name: str
    vector_count: int
    segment_count: int
    status: str  # green, yellow, red
    indexed: bool
    optimizer_status: str


@dataclass
class DataQualityScore:
    collection: str
    completeness: float  # 0.0-1.0: % of sampled points with required payload fields
    sample_size: int
    missing_fields: Dict[str, int]  # field -> count of points missing it


@dataclass
class QualityReport:
    timestamp: str
    collections: List[Dict[str, Any]]
    quality_scores: List[Dict[str, Any]]
    alerts: List[Dict[str, Any]]
    summary: Dict[str, Any]


KNOWN_COLLECTIONS = [
    "contacts", "programs", "documents", "activities", "jobs",
    "bullhorn_notes", "federal_contracts", "intelligence_reports", "opportunities",
]


class QualityMonitor:
    """Live quality monitoring for all Qdrant collections."""

    def __init__(self, qdrant_url: str = "http://localhost:6333", client: QdrantClient = None):
        self.client = client or QdrantClient(url=qdrant_url, timeout=15)

    def check_collection_health(self, name: str) -> CollectionHealth:
        """Check health of a single collection."""
        try:
            info = self.client.get_collection(name)
            vector_count = info.points_count or 0
            segments = info.segments_count or 0
            optimizer = info.optimizer_status
            opt_status = "ok" if optimizer and getattr(optimizer, 'ok', str(optimizer) == "ok") else "optimizing"
            indexed_count = getattr(info, 'indexed_vectors_count', vector_count) or 0
            indexed = indexed_count >= vector_count if vector_count > 0 else True

            if vector_count == 0:
                status = "red"
            elif not indexed or opt_status != "ok":
                status = "yellow"
            else:
                status = "green"

            return CollectionHealth(
                name=name,
                vector_count=vector_count,
                segment_count=segments,
                status=status,
                indexed=indexed,
                optimizer_status=opt_status,
            )
        except UnexpectedResponse:
            return CollectionHealth(
                name=name, vector_count=0, segment_count=0,
                status="red", indexed=False, optimizer_status="not_found",
            )

    def check_all_collections(self) -> List[CollectionHealth]:
        """Check health of all known collections."""
        results = []
        for name in KNOWN_COLLECTIONS:
            results.append(self.check_collection_health(name))
        return results

    def compute_quality_score(self, name: str, sample_size: int = 100) -> DataQualityScore:
        """Sample points from a collection and score payload completeness."""
        required = REQUIRED_PAYLOAD_FIELDS.get(name, ["title"])
        missing_counts: Dict[str, int] = {f: 0 for f in required}
        complete_count = 0

        try:
            points, _ = self.client.scroll(
                collection_name=name,
                limit=sample_size,
                with_payload=True,
                with_vectors=False,
            )
            actual_sample = len(points)
            if actual_sample == 0:
                return DataQualityScore(
                    collection=name, completeness=0.0,
                    sample_size=0, missing_fields=missing_counts,
                )

            for point in points:
                payload = point.payload or {}
                all_present = True
                for f in required:
                    if not payload.get(f):
                        missing_counts[f] += 1
                        all_present = False
                if all_present:
                    complete_count += 1

            completeness = complete_count / actual_sample
            return DataQualityScore(
                collection=name, completeness=round(completeness, 3),
                sample_size=actual_sample, missing_fields=missing_counts,
            )
        except Exception as e:
            logger.error(f"Quality score failed for {name}: {e}")
            return DataQualityScore(
                collection=name, completeness=0.0,
                sample_size=0, missing_fields=missing_counts,
            )

    def generate_report(self) -> QualityReport:
        """Generate a full quality report across all collections."""
        health_list = self.check_all_collections()
        quality_list = []
        for h in health_list:
            if h.vector_count > 0:
                quality_list.append(self.compute_quality_score(h.name))

        # Get alerts
        alerts = []
        try:
            from Engine6_QA.scripts.alerts import AlertEngine
            engine = AlertEngine()
            alerts = engine.get_recent_alerts(10)
        except Exception as e:
            logger.debug(f"Alerts unavailable: {e}")

        # Summary
        total_vectors = sum(h.vector_count for h in health_list)
        green = sum(1 for h in health_list if h.status == "green")
        yellow = sum(1 for h in health_list if h.status == "yellow")
        red = sum(1 for h in health_list if h.status == "red")
        avg_completeness = (
            sum(q.completeness for q in quality_list) / len(quality_list)
            if quality_list else 0.0
        )

        return QualityReport(
            timestamp=datetime.now().isoformat(),
            collections=[asdict(h) for h in health_list],
            quality_scores=[asdict(q) for q in quality_list],
            alerts=alerts,
            summary={
                "total_collections": len(health_list),
                "total_vectors": total_vectors,
                "health": {"green": green, "yellow": yellow, "red": red},
                "avg_completeness": round(avg_completeness, 3),
                "active_alerts": len(alerts),
            },
        )
