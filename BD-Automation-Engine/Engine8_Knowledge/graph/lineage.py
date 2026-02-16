"""
Neo4j File Lineage Tracking Module

Tracks data lineage through the BD pipeline using Neo4j graph model:
- (:File) nodes with path, type, hash, modified
- (:Process) nodes with name, script
- [:DERIVED_FROM] relationships with transform, timestamp
- [:DEPENDS_ON] relationships between files
- [:READS] / [:WRITES] between processes and files

Enables GDS algorithms:
- PageRank for critical file identification
- Community detection for file clusters
- Shortest path for lineage chains
- Betweenness centrality for bottleneck files

Usage:
    from Engine8_Knowledge.graph.lineage import LineageTracker
    tracker = LineageTracker(neo4j_manager)
    tracker.register_file("Engine2_ProgramMapping/data/output.csv")
    tracker.register_derivation(
        source="Engine1_Scraper/data/jobs_raw.json",
        target="Engine2_ProgramMapping/data/jobs_mapped.csv",
        process="Engine2_ProgramMapping/scripts/pipeline.py",
        transform="program_mapping"
    )
"""

import hashlib
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Extended Neo4j Schema for Lineage
# ---------------------------------------------------------------------------

LINEAGE_NODE_TYPES = {
    "File": {
        "description": "Data file in the pipeline (CSV, JSON, SQLite, etc.)",
        "properties": [
            "path",
            "name",
            "type",
            "extension",
            "size_bytes",
            "hash",
            "modified",
            "engine",
            "is_input",
            "is_output",
        ],
    },
    "Process": {
        "description": "Script or pipeline step that transforms data",
        "properties": [
            "name",
            "script_path",
            "engine",
            "description",
            "last_run",
            "run_count",
            "avg_duration_seconds",
        ],
    },
}

LINEAGE_RELATIONSHIP_TYPES = {
    "DERIVED_FROM": {
        "from": "File",
        "to": "File",
        "props": ["transform", "timestamp", "process_name"],
    },
    "DEPENDS_ON": {
        "from": "File",
        "to": "File",
        "props": ["dependency_type"],
    },
    "READS": {
        "from": "Process",
        "to": "File",
        "props": ["role"],
    },
    "WRITES": {
        "from": "Process",
        "to": "File",
        "props": ["role"],
    },
}

LINEAGE_CONSTRAINTS = [
    "CREATE CONSTRAINT file_path IF NOT EXISTS FOR (f:File) REQUIRE f.path IS UNIQUE",
    "CREATE CONSTRAINT process_script IF NOT EXISTS FOR (p:Process) REQUIRE p.script_path IS UNIQUE",
]

LINEAGE_INDEXES = [
    "CREATE INDEX file_engine IF NOT EXISTS FOR (f:File) ON (f.engine)",
    "CREATE INDEX file_type IF NOT EXISTS FOR (f:File) ON (f.type)",
    "CREATE INDEX process_engine IF NOT EXISTS FOR (p:Process) ON (p.engine)",
]


class LineageTracker:
    """Track data lineage through the BD pipeline using Neo4j."""

    def __init__(self, neo4j_manager=None):
        """
        Initialize lineage tracker.

        Args:
            neo4j_manager: Neo4jManager instance. If None, operates in dry-run mode.
        """
        self.manager = neo4j_manager
        self._dry_run = neo4j_manager is None
        if self._dry_run:
            logger.warning(
                "lineage_dry_run: No Neo4j manager provided, operating in dry-run mode"
            )

    def apply_schema(self) -> Dict:
        """Apply lineage-specific constraints and indexes to Neo4j."""
        if self._dry_run:
            return {
                "dry_run": True,
                "constraints": LINEAGE_CONSTRAINTS,
                "indexes": LINEAGE_INDEXES,
            }

        results = {"constraints": [], "indexes": [], "errors": []}

        for stmt in LINEAGE_CONSTRAINTS:
            try:
                self.manager.write_query(stmt)
                results["constraints"].append(stmt[:60])
            except Exception as e:
                if "already exists" not in str(e).lower():
                    results["errors"].append(str(e)[:100])

        for stmt in LINEAGE_INDEXES:
            try:
                self.manager.write_query(stmt)
                results["indexes"].append(stmt[:60])
            except Exception as e:
                if "already exists" not in str(e).lower():
                    results["errors"].append(str(e)[:100])

        return results

    def register_file(self, file_path: str, engine: str = None) -> Dict:
        """
        Register a file in the lineage graph.

        Args:
            file_path: Relative or absolute path to the file
            engine: Engine name (e.g., "Engine2_ProgramMapping")

        Returns:
            Dict with file node properties
        """
        path = Path(file_path)
        props = {
            "path": str(path),
            "name": path.name,
            "extension": path.suffix.lower(),
            "type": self._classify_file(path),
            "engine": engine or self._detect_engine(str(path)),
        }

        if path.exists():
            stat = path.stat()
            props["size_bytes"] = stat.st_size
            props["modified"] = datetime.fromtimestamp(stat.st_mtime).isoformat()
            props["hash"] = self._file_hash(path)

        if self._dry_run:
            return props

        query = """
        MERGE (f:File {path: $path})
        SET f += $props
        RETURN f
        """
        self.manager.write_query(query, {"path": str(path), "props": props})
        return props

    def register_process(
        self,
        script_path: str,
        name: str = None,
        engine: str = None,
        description: str = None,
    ) -> Dict:
        """
        Register a process/script in the lineage graph.

        Args:
            script_path: Path to the script
            name: Human-readable name
            engine: Engine name
            description: What the process does
        """
        props = {
            "script_path": script_path,
            "name": name or Path(script_path).stem,
            "engine": engine or self._detect_engine(script_path),
            "description": description or "",
        }

        if self._dry_run:
            return props

        query = """
        MERGE (p:Process {script_path: $script_path})
        SET p += $props
        RETURN p
        """
        self.manager.write_query(query, {"script_path": script_path, "props": props})
        return props

    def register_derivation(
        self,
        source: str,
        target: str,
        process: str = None,
        transform: str = None,
    ) -> Dict:
        """
        Register that target file was derived from source file.

        Args:
            source: Source file path
            target: Target (derived) file path
            process: Script that performed the transformation
            transform: Description of the transformation
        """
        rel_props = {
            "transform": transform or "unknown",
            "timestamp": datetime.now().isoformat(),
            "process_name": Path(process).stem if process else "",
        }

        if self._dry_run:
            return {"source": source, "target": target, **rel_props}

        # Ensure both files exist as nodes
        self.register_file(source)
        self.register_file(target)

        query = """
        MATCH (src:File {path: $source})
        MATCH (tgt:File {path: $target})
        MERGE (tgt)-[r:DERIVED_FROM]->(src)
        SET r += $props
        RETURN r
        """
        self.manager.write_query(
            query, {"source": source, "target": target, "props": rel_props}
        )

        # Also register process reads/writes
        if process:
            self.register_process(process)
            self._register_reads(process, source)
            self._register_writes(process, target)

        return {"source": source, "target": target, **rel_props}

    def register_dependency(
        self, file_path: str, depends_on: str, dep_type: str = "import"
    ) -> Dict:
        """Register that a file depends on another file."""
        if self._dry_run:
            return {"file": file_path, "depends_on": depends_on, "type": dep_type}

        self.register_file(file_path)
        self.register_file(depends_on)

        query = """
        MATCH (f:File {path: $file})
        MATCH (dep:File {path: $depends_on})
        MERGE (f)-[r:DEPENDS_ON]->(dep)
        SET r.dependency_type = $dep_type
        RETURN r
        """
        self.manager.write_query(
            query, {"file": file_path, "depends_on": depends_on, "dep_type": dep_type}
        )
        return {"file": file_path, "depends_on": depends_on, "type": dep_type}

    def _register_reads(self, process: str, file_path: str):
        """Register that a process reads a file."""
        query = """
        MATCH (p:Process {script_path: $process})
        MATCH (f:File {path: $file})
        MERGE (p)-[r:READS]->(f)
        RETURN r
        """
        self.manager.write_query(query, {"process": process, "file": file_path})

    def _register_writes(self, process: str, file_path: str):
        """Register that a process writes a file."""
        query = """
        MATCH (p:Process {script_path: $process})
        MATCH (f:File {path: $file})
        MERGE (p)-[r:WRITES]->(f)
        RETURN r
        """
        self.manager.write_query(query, {"process": process, "file": file_path})

    # -----------------------------------------------------------------------
    # Query Methods
    # -----------------------------------------------------------------------

    def get_lineage(self, file_path: str, depth: int = 5) -> Dict:
        """
        Get full lineage chain for a file (upstream and downstream).

        Args:
            file_path: File to trace lineage for
            depth: Maximum depth to traverse
        """
        if self._dry_run:
            return {"file": file_path, "dry_run": True}

        # Upstream (where did this file come from?)
        upstream_query = (
            """
        MATCH path = (f:File {path: $file})-[:DERIVED_FROM*1..%d]->(ancestor:File)
        RETURN [n IN nodes(path) | n.path] AS chain
        """
            % depth
        )
        upstream = self.manager.run_query(upstream_query, {"file": file_path})

        # Downstream (what was derived from this file?)
        downstream_query = (
            """
        MATCH path = (descendant:File)-[:DERIVED_FROM*1..%d]->(f:File {path: $file})
        RETURN [n IN nodes(path) | n.path] AS chain
        """
            % depth
        )
        downstream = self.manager.run_query(downstream_query, {"file": file_path})

        return {
            "file": file_path,
            "upstream": [dict(r) for r in upstream] if upstream else [],
            "downstream": [dict(r) for r in downstream] if downstream else [],
        }

    def get_critical_files(self, limit: int = 20) -> List[Dict]:
        """
        Use PageRank to identify the most critical files in the pipeline.
        Requires Neo4j GDS plugin.
        """
        if self._dry_run:
            return []

        try:
            query = """
            CALL gds.pageRank.stream({
                nodeProjection: 'File',
                relationshipProjection: 'DERIVED_FROM'
            })
            YIELD nodeId, score
            RETURN gds.util.asNode(nodeId).path AS file, score
            ORDER BY score DESC
            LIMIT $limit
            """
            results = self.manager.run_query(query, {"limit": limit})
            return [dict(r) for r in results]
        except Exception as e:
            logger.warning(
                "gds_pagerank_failed: %s (GDS plugin may not be installed)", e
            )
            return []

    def get_bottleneck_files(self, limit: int = 10) -> List[Dict]:
        """
        Use betweenness centrality to find bottleneck files.
        Requires Neo4j GDS plugin.
        """
        if self._dry_run:
            return []

        try:
            query = """
            CALL gds.betweenness.stream({
                nodeProjection: 'File',
                relationshipProjection: 'DERIVED_FROM'
            })
            YIELD nodeId, score
            RETURN gds.util.asNode(nodeId).path AS file, score
            ORDER BY score DESC
            LIMIT $limit
            """
            results = self.manager.run_query(query, {"limit": limit})
            return [dict(r) for r in results]
        except Exception as e:
            logger.warning("gds_betweenness_failed: %s", e)
            return []

    def get_file_communities(self) -> List[Dict]:
        """
        Detect file communities using Louvain algorithm.
        Requires Neo4j GDS plugin.
        """
        if self._dry_run:
            return []

        try:
            query = """
            CALL gds.louvain.stream({
                nodeProjection: 'File',
                relationshipProjection: {
                    DERIVED_FROM: {orientation: 'UNDIRECTED'},
                    DEPENDS_ON: {orientation: 'UNDIRECTED'}
                }
            })
            YIELD nodeId, communityId
            RETURN gds.util.asNode(nodeId).path AS file,
                   gds.util.asNode(nodeId).engine AS engine,
                   communityId
            ORDER BY communityId, file
            """
            results = self.manager.run_query(query)
            return [dict(r) for r in results]
        except Exception as e:
            logger.warning("gds_louvain_failed: %s", e)
            return []

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _classify_file(self, path: Path) -> str:
        """Classify a file by type."""
        ext = path.suffix.lower()
        type_map = {
            ".py": "python",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".js": "javascript",
            ".jsx": "javascript",
            ".csv": "csv",
            ".json": "json",
            ".xlsx": "excel",
            ".db": "sqlite",
            ".sql": "sql",
            ".md": "markdown",
            ".txt": "text",
            ".pdf": "pdf",
            ".docx": "word",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".html": "html",
            ".css": "css",
        }
        return type_map.get(ext, "other")

    def _detect_engine(self, path: str) -> str:
        """Detect which engine a file belongs to based on path."""
        path_str = str(path).replace("\\", "/")
        for i in range(1, 9):
            if f"Engine{i}_" in path_str:
                parts = path_str.split(f"Engine{i}_")
                if len(parts) > 1:
                    name = parts[1].split("/")[0]
                    return f"Engine{i}_{name}"
        if "dashboard" in path_str.lower():
            return "Dashboard"
        if "mcp" in path_str.lower():
            return "MCP"
        return "unknown"

    def _file_hash(self, path: Path) -> str:
        """Compute SHA-256 hash of file (first 64KB for large files)."""
        sha = hashlib.sha256()
        try:
            with open(path, "rb") as f:
                chunk = f.read(65536)  # First 64KB
                sha.update(chunk)
        except Exception:
            return ""
        return sha.hexdigest()[:16]

    def stats(self) -> Dict:
        """Get lineage graph statistics."""
        if self._dry_run:
            return {"dry_run": True}

        try:
            file_count = self.manager.run_query(
                "MATCH (f:File) RETURN count(f) AS count"
            )
            process_count = self.manager.run_query(
                "MATCH (p:Process) RETURN count(p) AS count"
            )
            derivation_count = self.manager.run_query(
                "MATCH ()-[r:DERIVED_FROM]->() RETURN count(r) AS count"
            )
            dependency_count = self.manager.run_query(
                "MATCH ()-[r:DEPENDS_ON]->() RETURN count(r) AS count"
            )

            return {
                "files": file_count[0]["count"] if file_count else 0,
                "processes": process_count[0]["count"] if process_count else 0,
                "derivations": derivation_count[0]["count"] if derivation_count else 0,
                "dependencies": dependency_count[0]["count"] if dependency_count else 0,
            }
        except Exception as e:
            return {"error": str(e)}


# ---------------------------------------------------------------------------
# Pre-built BD Pipeline Lineage Registration
# ---------------------------------------------------------------------------

BD_PIPELINE_LINEAGE = [
    # Engine 1 → Engine 2
    {
        "source": "Engine1_Scraper/data/jobs_raw.json",
        "target": "Engine2_ProgramMapping/data/jobs_standardized.csv",
        "process": "Engine2_ProgramMapping/scripts/job_standardizer.py",
        "transform": "job_field_extraction_and_standardization",
    },
    {
        "source": "Engine2_ProgramMapping/data/jobs_standardized.csv",
        "target": "Engine2_ProgramMapping/data/jobs_mapped.csv",
        "process": "Engine2_ProgramMapping/scripts/program_mapper.py",
        "transform": "program_matching",
    },
    # Engine 2 → Engine 5
    {
        "source": "Engine2_ProgramMapping/data/jobs_mapped.csv",
        "target": "Engine5_Scoring/data/jobs_scored.csv",
        "process": "Engine5_Scoring/scripts/bd_scoring.py",
        "transform": "bd_priority_scoring",
    },
    # Engine 7 → SQLite
    {
        "source": "Engine7_BullhornETL/data/raw_exports/",
        "target": "Engine7_BullhornETL/data/bullhorn_master.db",
        "process": "Engine7_BullhornETL/scripts/database_schema.py",
        "transform": "bullhorn_csv_to_sqlite_etl",
    },
    # Engine 3 → Dashboard
    {
        "source": "Engine3_OrgChart/data/contacts_raw.csv",
        "target": "dashboard/public/data/contacts.json",
        "process": "Engine3_OrgChart/scripts/contact_classifier.py",
        "transform": "6_tier_contact_classification",
    },
    # Engine 8 → Qdrant
    {
        "source": "Engine7_BullhornETL/data/bullhorn_master.db",
        "target": "Engine8_Knowledge/data/qdrant/activities",
        "process": "Engine8_Knowledge/scripts/vector_store.py",
        "transform": "activity_vectorization",
    },
    # Dashboard feeds
    {
        "source": "Engine7_BullhornETL/data/bullhorn_master.db",
        "target": "dashboard/public/data/placements.json",
        "process": "Engine8_Knowledge/api.py",
        "transform": "placement_json_export",
    },
]


def register_bd_pipeline_lineage(tracker: LineageTracker):
    """Register the standard BD pipeline lineage."""
    for entry in BD_PIPELINE_LINEAGE:
        tracker.register_derivation(**entry)
    logger.info("bd_pipeline_lineage_registered", entries=len(BD_PIPELINE_LINEAGE))
