"""Phase 38A — Data Lineage Tracker

Track every data transformation from source to insight.
Full DAG provenance recording, lineage tracing, impact analysis, freshness reports.
"""

import hashlib
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# =========================================
# ENUMS
# =========================================

class NodeType(str, Enum):
    SOURCE = "source"
    RAW_RECORD = "raw_record"
    PROCESS = "process"
    ENRICHED_RECORD = "enriched_record"
    INSIGHT = "insight"


class SourceType(str, Enum):
    APIFY_SCRAPE = "apify_scrape"
    ZOOMINFO_EXPORT = "zoominfo_export"
    SAM_GOV = "sam_gov"
    MANUAL = "manual"
    BULLHORN_ETL = "bullhorn_etl"
    LINKEDIN = "linkedin"
    USAJOBS = "usajobs"


class TransformType(str, Enum):
    LLM_ENRICHMENT = "llm_enrichment"
    CLASSIFICATION = "classification"
    DEDUPLICATION = "deduplication"
    GEOCODING = "geocoding"
    EMBEDDING = "embedding"
    SCORING = "scoring"
    SELF_HEALING = "self_healing"
    PROGRAM_MAPPING = "program_mapping"
    TIER_ASSIGNMENT = "tier_assignment"
    PRIORITY_CALCULATION = "priority_calculation"


# =========================================
# DATA CLASSES
# =========================================

@dataclass
class DataSource:
    """Origin of data."""
    id: str
    source_type: str
    url: str = ""
    timestamp: str = ""
    actor_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TransformProcess:
    """A data transformation step."""
    name: str
    version: str = "1.0"
    model: str = ""
    params: Dict[str, Any] = field(default_factory=dict)
    transform_type: str = ""


@dataclass
class LineageNode:
    """A node in the lineage DAG."""
    id: str
    node_type: str  # source, raw_record, process, enriched_record, insight
    data_hash: str = ""
    confidence: float = 1.0
    created_at: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    record_id: str = ""  # Reference to the actual data record
    record_type: str = ""  # contacts, programs, jobs, etc.


@dataclass
class LineageEdge:
    """An edge in the lineage DAG."""
    id: str
    source_node_id: str
    target_node_id: str
    edge_type: str  # PRODUCED, FED_INTO, OUTPUT, TRANSFORMED_BY
    timestamp: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LineageGraph:
    """Full lineage trace result."""
    root: LineageNode
    nodes: List[LineageNode] = field(default_factory=list)
    edges: List[LineageEdge] = field(default_factory=list)
    depth: int = 0
    total_transformations: int = 0
    confidence_chain: List[float] = field(default_factory=list)
    sources: List[DataSource] = field(default_factory=list)


@dataclass
class ImpactAnalysis:
    """Forward impact analysis — what depends on this record."""
    record_id: str
    downstream_records: List[LineageNode] = field(default_factory=list)
    affected_reports: List[str] = field(default_factory=list)
    affected_campaigns: List[str] = field(default_factory=list)
    total_downstream: int = 0
    risk_level: str = "low"  # low, medium, high, critical


@dataclass
class FreshnessEntry:
    """Freshness data for a domain."""
    domain: str
    total_records: int = 0
    avg_age_days: float = 0.0
    updated_last_30: int = 0
    updated_last_60: int = 0
    updated_last_90: int = 0
    stale_count: int = 0  # Not updated in 90+ days
    oldest_record_date: str = ""
    freshest_record_date: str = ""


@dataclass
class FreshnessReport:
    """Platform-wide freshness report."""
    entries: List[FreshnessEntry] = field(default_factory=list)
    overall_freshness_score: float = 100.0
    generated_at: str = ""


# =========================================
# DATA LINEAGE TRACKER
# =========================================

class DataLineageTracker:
    """Records the complete provenance chain for every data point."""

    def __init__(self):
        self._nodes: Dict[str, LineageNode] = {}
        self._edges: List[LineageEdge] = []
        self._sources: Dict[str, DataSource] = {}
        self._record_to_nodes: Dict[str, List[str]] = {}  # record_id -> [node_ids]
        self._node_children: Dict[str, List[str]] = {}  # node_id -> [child_node_ids]
        self._node_parents: Dict[str, List[str]] = {}   # node_id -> [parent_node_ids]

        # Data for freshness reports
        self._domain_records: Dict[str, List[Dict]] = {}

    def set_domain_records(self, domain: str, records: List[Dict[str, Any]]) -> None:
        """Load records for freshness analysis."""
        self._domain_records[domain] = records

    # -----------------------------------------
    # Record ingestion
    # -----------------------------------------

    def record_ingestion(
        self, source: DataSource, records: List[Dict[str, Any]],
    ) -> List[LineageNode]:
        """Record raw data ingestion from a source."""
        now = datetime.now(timezone.utc).isoformat()

        # Create source node
        source_node = LineageNode(
            id=f"src_{source.id}",
            node_type=NodeType.SOURCE.value,
            data_hash=self._hash_data({"source": source.url, "type": source.source_type}),
            confidence=1.0,
            created_at=source.timestamp or now,
            metadata={"source_type": source.source_type, "url": source.url,
                       "actor_id": source.actor_id},
        )
        self._nodes[source_node.id] = source_node
        self._sources[source.id] = source

        # Create raw record nodes
        raw_nodes = []
        for record in records:
            record_id = record.get("id", uuid.uuid4().hex[:8])
            raw_node = LineageNode(
                id=f"raw_{record_id}",
                node_type=NodeType.RAW_RECORD.value,
                data_hash=self._hash_data(record),
                confidence=1.0,
                created_at=now,
                metadata={"fields": list(record.keys()), "record_count": 1},
                record_id=record_id,
                record_type=record.get("_type", "unknown"),
            )
            self._nodes[raw_node.id] = raw_node
            raw_nodes.append(raw_node)

            # Create edge: source -> raw_record
            edge = LineageEdge(
                id=uuid.uuid4().hex[:8],
                source_node_id=source_node.id,
                target_node_id=raw_node.id,
                edge_type="PRODUCED",
                timestamp=now,
            )
            self._edges.append(edge)
            self._add_parent_child(source_node.id, raw_node.id)

            # Index
            if record_id not in self._record_to_nodes:
                self._record_to_nodes[record_id] = []
            self._record_to_nodes[record_id].append(raw_node.id)

        return raw_nodes

    # -----------------------------------------
    # Record transformation
    # -----------------------------------------

    def record_transformation(
        self,
        input_node_ids: List[str],
        process: TransformProcess,
        output_records: List[Dict[str, Any]],
    ) -> List[LineageNode]:
        """Record a data transformation step."""
        now = datetime.now(timezone.utc).isoformat()

        # Create process node
        process_node = LineageNode(
            id=f"proc_{uuid.uuid4().hex[:8]}",
            node_type=NodeType.PROCESS.value,
            data_hash=self._hash_data({
                "name": process.name, "version": process.version,
                "model": process.model,
            }),
            confidence=1.0,
            created_at=now,
            metadata={
                "process_name": process.name,
                "version": process.version,
                "model": process.model,
                "params": process.params,
                "transform_type": process.transform_type,
            },
        )
        self._nodes[process_node.id] = process_node

        # Connect inputs to process
        for input_id in input_node_ids:
            edge = LineageEdge(
                id=uuid.uuid4().hex[:8],
                source_node_id=input_id,
                target_node_id=process_node.id,
                edge_type="FED_INTO",
                timestamp=now,
            )
            self._edges.append(edge)
            self._add_parent_child(input_id, process_node.id)

        # Create output nodes
        output_nodes = []

        # Determine confidence from input nodes
        input_confidences = []
        for nid in input_node_ids:
            node = self._nodes.get(nid)
            if node:
                input_confidences.append(node.confidence)
        base_confidence = min(input_confidences) if input_confidences else 1.0

        # Slight decay per transformation
        output_confidence = round(base_confidence * 0.98, 4)

        for record in output_records:
            record_id = record.get("id", uuid.uuid4().hex[:8])
            output_node = LineageNode(
                id=f"enr_{record_id}_{uuid.uuid4().hex[:4]}",
                node_type=NodeType.ENRICHED_RECORD.value,
                data_hash=self._hash_data(record),
                confidence=output_confidence,
                created_at=now,
                metadata={
                    "fields": list(record.keys()),
                    "process": process.name,
                },
                record_id=record_id,
                record_type=record.get("_type", "enriched"),
            )
            self._nodes[output_node.id] = output_node
            output_nodes.append(output_node)

            # Edge: process -> output
            edge = LineageEdge(
                id=uuid.uuid4().hex[:8],
                source_node_id=process_node.id,
                target_node_id=output_node.id,
                edge_type="OUTPUT",
                timestamp=now,
            )
            self._edges.append(edge)
            self._add_parent_child(process_node.id, output_node.id)

            # Index
            if record_id not in self._record_to_nodes:
                self._record_to_nodes[record_id] = []
            self._record_to_nodes[record_id].append(output_node.id)

        return output_nodes

    # -----------------------------------------
    # Lineage tracing
    # -----------------------------------------

    def trace_lineage(self, record_id: str, depth: int = 10) -> Optional[LineageGraph]:
        """Trace a record's complete lineage back to its original source."""
        node_ids = self._record_to_nodes.get(record_id, [])
        if not node_ids:
            return None

        # Use the most recent node for this record
        latest_node_id = node_ids[-1]
        root = self._nodes.get(latest_node_id)
        if not root:
            return None

        # BFS backwards through parents
        visited_nodes: Dict[str, LineageNode] = {root.id: root}
        visited_edges: List[LineageEdge] = []
        queue = [root.id]
        current_depth = 0
        sources: List[DataSource] = []
        confidence_chain = [root.confidence]
        transformations = 0

        while queue and current_depth < depth:
            next_queue = []
            for node_id in queue:
                parents = self._node_parents.get(node_id, [])
                for parent_id in parents:
                    if parent_id not in visited_nodes:
                        parent_node = self._nodes.get(parent_id)
                        if parent_node:
                            visited_nodes[parent_id] = parent_node
                            next_queue.append(parent_id)
                            confidence_chain.append(parent_node.confidence)
                            if parent_node.node_type == NodeType.PROCESS.value:
                                transformations += 1
                            if parent_node.node_type == NodeType.SOURCE.value:
                                # Find source data
                                for src in self._sources.values():
                                    if f"src_{src.id}" == parent_id:
                                        sources.append(src)

                    # Find the edge
                    for edge in self._edges:
                        if edge.source_node_id == parent_id and edge.target_node_id == node_id:
                            if edge not in visited_edges:
                                visited_edges.append(edge)

            queue = next_queue
            current_depth += 1

        return LineageGraph(
            root=root,
            nodes=list(visited_nodes.values()),
            edges=visited_edges,
            depth=current_depth,
            total_transformations=transformations,
            confidence_chain=sorted(confidence_chain, reverse=True),
            sources=sources,
        )

    # -----------------------------------------
    # Impact analysis
    # -----------------------------------------

    def get_impact_analysis(self, record_id: str) -> ImpactAnalysis:
        """Forward trace: what downstream records depend on this record."""
        node_ids = self._record_to_nodes.get(record_id, [])
        if not node_ids:
            return ImpactAnalysis(record_id=record_id)

        # BFS forward through children
        downstream: List[LineageNode] = []
        visited = set()

        queue = list(node_ids)
        while queue:
            node_id = queue.pop(0)
            if node_id in visited:
                continue
            visited.add(node_id)

            children = self._node_children.get(node_id, [])
            for child_id in children:
                child = self._nodes.get(child_id)
                if child and child_id not in visited:
                    if child.node_type in (NodeType.ENRICHED_RECORD.value, NodeType.INSIGHT.value):
                        downstream.append(child)
                    queue.append(child_id)

        total = len(downstream)
        if total > 20:
            risk = "critical"
        elif total > 10:
            risk = "high"
        elif total > 3:
            risk = "medium"
        else:
            risk = "low"

        return ImpactAnalysis(
            record_id=record_id,
            downstream_records=downstream,
            total_downstream=total,
            risk_level=risk,
        )

    # -----------------------------------------
    # Freshness report
    # -----------------------------------------

    def get_freshness_report(self) -> FreshnessReport:
        """Analyze data freshness across the platform."""
        now = datetime.now(timezone.utc)
        entries = []
        scores = []

        for domain, records in self._domain_records.items():
            if not records:
                entries.append(FreshnessEntry(domain=domain))
                continue

            ages = []
            updated_30 = 0
            updated_60 = 0
            updated_90 = 0
            stale = 0
            oldest = None
            freshest = None

            for record in records:
                updated_str = record.get("last_updated", record.get("updated_at", ""))
                if not updated_str:
                    stale += 1
                    continue

                try:
                    updated = datetime.fromisoformat(updated_str.replace("Z", "+00:00"))
                    age = (now - updated).days
                    ages.append(age)

                    if age <= 30:
                        updated_30 += 1
                    if age <= 60:
                        updated_60 += 1
                    if age <= 90:
                        updated_90 += 1
                    if age > 90:
                        stale += 1

                    if oldest is None or updated < oldest:
                        oldest = updated
                    if freshest is None or updated > freshest:
                        freshest = updated

                except (ValueError, TypeError):
                    stale += 1

            avg_age = sum(ages) / len(ages) if ages else 0
            fresh_pct = updated_90 / len(records) * 100 if records else 100
            scores.append(fresh_pct)

            entries.append(FreshnessEntry(
                domain=domain,
                total_records=len(records),
                avg_age_days=round(avg_age, 1),
                updated_last_30=updated_30,
                updated_last_60=updated_60,
                updated_last_90=updated_90,
                stale_count=stale,
                oldest_record_date=oldest.isoformat() if oldest else "",
                freshest_record_date=freshest.isoformat() if freshest else "",
            ))

        overall = round(sum(scores) / len(scores), 1) if scores else 100.0

        return FreshnessReport(
            entries=entries,
            overall_freshness_score=overall,
            generated_at=now.isoformat(),
        )

    # -----------------------------------------
    # Query helpers
    # -----------------------------------------

    def get_node(self, node_id: str) -> Optional[LineageNode]:
        """Get a lineage node by ID."""
        return self._nodes.get(node_id)

    def get_all_nodes(self) -> List[LineageNode]:
        """Get all lineage nodes."""
        return list(self._nodes.values())

    def get_all_edges(self) -> List[LineageEdge]:
        """Get all lineage edges."""
        return self._edges

    def get_nodes_for_record(self, record_id: str) -> List[LineageNode]:
        """Get all lineage nodes for a record."""
        node_ids = self._record_to_nodes.get(record_id, [])
        return [self._nodes[nid] for nid in node_ids if nid in self._nodes]

    def get_stats(self) -> Dict[str, Any]:
        """Get lineage stats."""
        type_counts = {}
        for node in self._nodes.values():
            type_counts[node.node_type] = type_counts.get(node.node_type, 0) + 1
        return {
            "total_nodes": len(self._nodes),
            "total_edges": len(self._edges),
            "total_sources": len(self._sources),
            "tracked_records": len(self._record_to_nodes),
            "node_types": type_counts,
        }

    # -----------------------------------------
    # Internal
    # -----------------------------------------

    def _add_parent_child(self, parent_id: str, child_id: str) -> None:
        """Track parent-child relationships."""
        if parent_id not in self._node_children:
            self._node_children[parent_id] = []
        self._node_children[parent_id].append(child_id)

        if child_id not in self._node_parents:
            self._node_parents[child_id] = []
        self._node_parents[child_id].append(parent_id)

    @staticmethod
    def _hash_data(data: Any) -> str:
        """Create a content hash for change detection."""
        serialized = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()[:16]


# =========================================
# SINGLETON
# =========================================

_tracker: Optional[DataLineageTracker] = None


def get_lineage_tracker() -> DataLineageTracker:
    global _tracker
    if _tracker is None:
        _tracker = DataLineageTracker()
    return _tracker
