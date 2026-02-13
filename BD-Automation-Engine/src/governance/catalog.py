"""Phase 43A — Data Catalog

Central catalog of every data asset in the platform with owner, schema,
description, quality metrics, lineage, and usage statistics.
Searchable, browsable, auto-populated.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# =========================================
# ENUMS
# =========================================

class AssetType(str, Enum):
    COLLECTION = "collection"       # Qdrant collection
    TABLE = "table"                 # SQLite/DB table
    FILE = "file"                   # CSV, JSON, etc.
    API_ENDPOINT = "api_endpoint"   # REST endpoint
    PIPELINE = "pipeline"           # Data pipeline
    MODEL = "model"                 # ML model
    GRAPH = "graph"                 # Knowledge graph


class AssetStatus(str, Enum):
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"
    DRAFT = "draft"


# =========================================
# DATA CLASSES
# =========================================

@dataclass
class DataLineage:
    """Tracks where data comes from and where it goes."""
    upstream: List[str] = field(default_factory=list)    # source asset IDs
    downstream: List[str] = field(default_factory=list)  # consumer asset IDs
    transformations: List[str] = field(default_factory=list)  # pipeline steps


@dataclass
class UsageStats:
    """Usage statistics for a data asset."""
    total_reads: int = 0
    total_writes: int = 0
    unique_consumers: int = 0
    last_read_at: str = ""
    last_write_at: str = ""
    avg_daily_reads: float = 0.0
    popularity_score: float = 0.0  # 0-1 based on usage


@dataclass
class QualityMetrics:
    """Quality metrics for a data asset."""
    completeness: float = 0.0    # % of non-null fields
    accuracy: float = 0.0        # validated accuracy score
    freshness_hours: float = 0.0 # hours since last update
    consistency: float = 0.0     # cross-source consistency
    overall_score: float = 0.0   # weighted composite


@dataclass
class DataAsset:
    """A data asset registered in the catalog."""
    id: str = ""
    name: str = ""
    description: str = ""
    asset_type: str = AssetType.COLLECTION.value
    status: str = AssetStatus.ACTIVE.value
    owner: str = ""
    domain: str = ""          # contacts, jobs, programs, documents, etc.
    schema_id: str = ""       # reference to schema registry
    tags: List[str] = field(default_factory=list)
    record_count: int = 0
    size_bytes: int = 0
    lineage: DataLineage = field(default_factory=DataLineage)
    usage: UsageStats = field(default_factory=UsageStats)
    quality: QualityMetrics = field(default_factory=QualityMetrics)
    created_at: str = ""
    updated_at: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


# =========================================
# DATA CATALOG
# =========================================

class DataCatalog:
    """Central catalog of all data assets in the platform."""

    def __init__(self):
        self._assets: Dict[str, DataAsset] = {}
        self._seed_defaults()

    def _seed_defaults(self) -> None:
        """Seed catalog with known platform data assets."""
        defaults = [
            DataAsset(
                id="contacts", name="Contacts", domain="contacts",
                description="CRM contacts with tier classification and org chart data",
                asset_type=AssetType.COLLECTION.value, owner="Engine7_BullhornETL",
                tags=["crm", "contacts", "tier", "org_chart"],
                record_count=7337,
                lineage=DataLineage(
                    upstream=["bullhorn_crm"],
                    downstream=["playbook_generator", "outreach_crafter"],
                ),
            ),
            DataAsset(
                id="programs", name="Federal Programs", domain="programs",
                description="388 federal programs and contracts with mapping data",
                asset_type=AssetType.COLLECTION.value, owner="Engine2_ProgramMapping",
                tags=["programs", "contracts", "federal", "defense"],
                record_count=401,
                lineage=DataLineage(
                    upstream=["federal_programs_csv"],
                    downstream=["program_intel_agent", "bd_scoring"],
                ),
            ),
            DataAsset(
                id="jobs", name="Job Postings", domain="jobs",
                description="Scraped job postings with BD scores and program mapping",
                asset_type=AssetType.COLLECTION.value, owner="Engine1_Scraper",
                tags=["jobs", "hiring", "scraping", "bd_score"],
                record_count=4,
                lineage=DataLineage(
                    upstream=["apify_scraper"],
                    downstream=["program_mapper", "job_intel_worker"],
                ),
            ),
            DataAsset(
                id="documents", name="Documents", domain="documents",
                description="Past performance, briefings, intel reports",
                asset_type=AssetType.COLLECTION.value, owner="Engine8_Knowledge",
                tags=["documents", "past_performance", "briefings"],
                record_count=205,
            ),
            DataAsset(
                id="activities", name="Activities", domain="activities",
                description="Call notes, meeting records, interaction logs",
                asset_type=AssetType.COLLECTION.value, owner="Engine8_Knowledge",
                tags=["activities", "calls", "meetings", "interactions"],
                record_count=500,
            ),
        ]
        now = datetime.now(timezone.utc).isoformat()
        for asset in defaults:
            asset.created_at = now
            asset.updated_at = now
            self._assets[asset.id] = asset

    # -----------------------------------------
    # CRUD
    # -----------------------------------------

    def register(self, asset: DataAsset) -> str:
        """Register a new data asset in the catalog."""
        if not asset.id:
            asset.id = uuid.uuid4().hex[:10]
        now = datetime.now(timezone.utc).isoformat()
        if not asset.created_at:
            asset.created_at = now
        asset.updated_at = now
        self._assets[asset.id] = asset
        logger.debug("Registered asset: %s (%s)", asset.name, asset.id)
        return asset.id

    def get(self, asset_id: str) -> Optional[DataAsset]:
        """Get a data asset by ID."""
        return self._assets.get(asset_id)

    def update(self, asset_id: str, updates: Dict[str, Any]) -> Optional[DataAsset]:
        """Update a data asset's fields."""
        asset = self._assets.get(asset_id)
        if not asset:
            return None
        for key, val in updates.items():
            if hasattr(asset, key) and key not in {"id", "created_at"}:
                setattr(asset, key, val)
        asset.updated_at = datetime.now(timezone.utc).isoformat()
        return asset

    def delete(self, asset_id: str) -> bool:
        """Remove a data asset from the catalog."""
        return self._assets.pop(asset_id, None) is not None

    def list_assets(
        self,
        domain: str = "",
        asset_type: str = "",
        status: str = "",
        limit: int = 100,
    ) -> List[DataAsset]:
        """List assets with optional filtering."""
        results = list(self._assets.values())
        if domain:
            results = [a for a in results if a.domain == domain]
        if asset_type:
            results = [a for a in results if a.asset_type == asset_type]
        if status:
            results = [a for a in results if a.status == status]
        return results[:limit]

    # -----------------------------------------
    # SEARCH
    # -----------------------------------------

    def search(self, query: str, limit: int = 20) -> List[DataAsset]:
        """Search catalog by name, description, tags, or domain."""
        query_lower = query.lower()
        query_tokens = set(query_lower.split())
        scored: List[tuple] = []

        for asset in self._assets.values():
            score = 0.0
            searchable = (
                f"{asset.name} {asset.description} {asset.domain} "
                f"{' '.join(asset.tags)}"
            ).lower()

            # Token match
            for token in query_tokens:
                if token in searchable:
                    score += 1.0
            # Exact name match bonus
            if query_lower in asset.name.lower():
                score += 2.0

            if score > 0:
                scored.append((score, asset))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [a for _, a in scored[:limit]]

    # -----------------------------------------
    # LINEAGE
    # -----------------------------------------

    def get_lineage(self, asset_id: str) -> Optional[Dict[str, Any]]:
        """Get full lineage graph for an asset."""
        asset = self._assets.get(asset_id)
        if not asset:
            return None

        upstream_assets = []
        for uid in asset.lineage.upstream:
            up = self._assets.get(uid)
            if up:
                upstream_assets.append({"id": up.id, "name": up.name, "type": up.asset_type})
            else:
                upstream_assets.append({"id": uid, "name": uid, "type": "external"})

        downstream_assets = []
        for did in asset.lineage.downstream:
            down = self._assets.get(did)
            if down:
                downstream_assets.append({"id": down.id, "name": down.name, "type": down.asset_type})
            else:
                downstream_assets.append({"id": did, "name": did, "type": "external"})

        return {
            "asset_id": asset_id,
            "asset_name": asset.name,
            "upstream": upstream_assets,
            "downstream": downstream_assets,
            "transformations": asset.lineage.transformations,
        }

    # -----------------------------------------
    # USAGE TRACKING
    # -----------------------------------------

    def record_read(self, asset_id: str, consumer: str = "") -> None:
        """Record a read access to an asset."""
        asset = self._assets.get(asset_id)
        if not asset:
            return
        asset.usage.total_reads += 1
        asset.usage.last_read_at = datetime.now(timezone.utc).isoformat()
        self._update_popularity(asset)

    def record_write(self, asset_id: str) -> None:
        """Record a write/update to an asset."""
        asset = self._assets.get(asset_id)
        if not asset:
            return
        asset.usage.total_writes += 1
        asset.usage.last_write_at = datetime.now(timezone.utc).isoformat()
        asset.updated_at = datetime.now(timezone.utc).isoformat()

    def _update_popularity(self, asset: DataAsset) -> None:
        """Recompute popularity score based on usage."""
        reads = asset.usage.total_reads
        # Logarithmic scale, capped at 1.0
        import math
        asset.usage.popularity_score = min(math.log1p(reads) / 10, 1.0)

    # -----------------------------------------
    # QUALITY UPDATES
    # -----------------------------------------

    def update_quality(self, asset_id: str, metrics: Dict[str, float]) -> Optional[QualityMetrics]:
        """Update quality metrics for an asset."""
        asset = self._assets.get(asset_id)
        if not asset:
            return None

        for key, val in metrics.items():
            if hasattr(asset.quality, key):
                setattr(asset.quality, key, val)

        # Recompute overall score
        asset.quality.overall_score = round(
            (asset.quality.completeness * 0.3
             + asset.quality.accuracy * 0.3
             + asset.quality.consistency * 0.2
             + max(0, 1.0 - asset.quality.freshness_hours / 168) * 0.2),  # 168h = 1 week
            4,
        )
        asset.updated_at = datetime.now(timezone.utc).isoformat()
        return asset.quality

    # -----------------------------------------
    # STATS
    # -----------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """Get catalog-level statistics."""
        assets = list(self._assets.values())
        domains = set(a.domain for a in assets)
        return {
            "total_assets": len(assets),
            "domains": list(domains),
            "by_type": {t.value: sum(1 for a in assets if a.asset_type == t.value) for t in AssetType},
            "by_status": {s.value: sum(1 for a in assets if a.status == s.value) for s in AssetStatus},
            "total_records": sum(a.record_count for a in assets),
        }


# =========================================
# SINGLETON
# =========================================

_catalog: Optional[DataCatalog] = None


def get_data_catalog() -> DataCatalog:
    global _catalog
    if _catalog is None:
        _catalog = DataCatalog()
    return _catalog
