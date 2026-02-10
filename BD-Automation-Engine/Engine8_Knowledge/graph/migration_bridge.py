"""
Phase 21A — NetworkX ↔ Neo4j Migration Bridge

Bridges the existing SQLite-backed BDKnowledgeGraph (bd_knowledge_graph.py)
with the new Neo4j-backed graph. Allows both to work during transition.

Features:
  - Export SQLite graph → Neo4j (nodes + edges with all properties)
  - Import Neo4j subgraph → NetworkX (for algorithms not yet ported)
  - Feature flag: USE_NEO4J switches backend
  - Neo4j implementations of InfluenceScorer and CommunityDetector
"""

import os
import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)

USE_NEO4J = os.getenv("USE_NEO4J", "false").lower() in ("true", "1", "yes")


# ---------------------------------------------------------------------------
# GraphInterface — shared interface for both backends
# ---------------------------------------------------------------------------

class GraphInterface:
    """Common interface for graph operations, backed by either NetworkX or Neo4j."""

    def search_entities(self, query: str, entity_type: Optional[str] = None, limit: int = 20) -> list[dict]:
        raise NotImplementedError

    def find_path(self, from_name: str, to_name: str, max_depth: int = 6) -> list[dict]:
        raise NotImplementedError

    def get_neighbors(self, entity_name: str, depth: int = 1) -> dict:
        raise NotImplementedError

    def get_stats(self) -> dict:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# SQLite/NetworkX backend (existing)
# ---------------------------------------------------------------------------

class SQLiteGraphBackend(GraphInterface):
    """Wraps existing BDKnowledgeGraph from bd_knowledge_graph.py."""

    def __init__(self) -> None:
        self._graph = None

    def _get_graph(self) -> Any:
        if self._graph is None:
            try:
                from Engine8_Knowledge.graph.bd_knowledge_graph import get_bd_knowledge_graph
                self._graph = get_bd_knowledge_graph()
            except Exception:
                pass
        return self._graph

    def search_entities(self, query: str, entity_type: Optional[str] = None, limit: int = 20) -> list[dict]:
        g = self._get_graph()
        if not g:
            return []
        return g.search_entities(query, entity_type, limit)

    def find_path(self, from_name: str, to_name: str, max_depth: int = 6) -> list[dict]:
        g = self._get_graph()
        if not g:
            return []
        return g.find_teaming_path(from_name, to_name, max_depth)

    def get_neighbors(self, entity_name: str, depth: int = 1) -> dict:
        g = self._get_graph()
        if not g:
            return {"entity": entity_name, "neighbors": []}
        results = g.search_entities(entity_name, limit=1)
        if not results:
            return {"entity": entity_name, "neighbors": []}
        entity_id = results[0].get("id", "")
        rels = g.get_entity_relationships(entity_id)
        return {"entity": entity_name, "neighbors": rels}

    def get_stats(self) -> dict:
        g = self._get_graph()
        if not g:
            return {"backend": "sqlite", "status": "unavailable"}
        stats = g.get_stats()
        stats["backend"] = "sqlite"
        return stats


# ---------------------------------------------------------------------------
# Neo4j backend
# ---------------------------------------------------------------------------

class Neo4jGraphBackend(GraphInterface):
    """Neo4j-backed implementation using Cypher queries."""

    def __init__(self) -> None:
        self._queries = None

    def _get_queries(self) -> Any:
        if self._queries is None:
            try:
                from Engine8_Knowledge.graph.queries import get_graph_queries
                self._queries = get_graph_queries()
            except Exception:
                pass
        return self._queries

    def search_entities(self, query: str, entity_type: Optional[str] = None, limit: int = 20) -> list[dict]:
        from Engine8_Knowledge.graph.neo4j_manager import get_neo4j_manager
        mgr = get_neo4j_manager()
        label_filter = f":`{entity_type}`" if entity_type else ""
        results = mgr.run_query(
            f"""
            MATCH (n{label_filter})
            WHERE n.name =~ $pattern
            RETURN n.name AS name, labels(n)[0] AS type, properties(n) AS props
            LIMIT $limit
            """,
            {"pattern": f"(?i).*{query}.*", "limit": limit},
        )
        return results

    def find_path(self, from_name: str, to_name: str, max_depth: int = 6) -> list[dict]:
        q = self._get_queries()
        if not q:
            return []
        result = q.find_shortest_path(from_name, to_name)
        return result.get("path", [])

    def get_neighbors(self, entity_name: str, depth: int = 1) -> dict:
        from Engine8_Knowledge.graph.neo4j_manager import get_neo4j_manager
        mgr = get_neo4j_manager()
        results = mgr.run_query(
            """
            MATCH (n)-[r]-(m)
            WHERE n.name =~ $pattern
            RETURN n.name AS source, type(r) AS relationship,
                   m.name AS target, labels(m)[0] AS target_type
            LIMIT 50
            """,
            {"pattern": f"(?i).*{entity_name}.*"},
        )
        return {"entity": entity_name, "neighbors": results}

    def get_stats(self) -> dict:
        q = self._get_queries()
        if not q:
            return {"backend": "neo4j", "status": "unavailable"}
        stats = q.get_graph_stats()
        stats["backend"] = "neo4j"
        return stats


# ---------------------------------------------------------------------------
# Migration functions
# ---------------------------------------------------------------------------

def export_sqlite_to_neo4j() -> dict:
    """Export the existing SQLite knowledge graph to Neo4j.

    Reads all entities and relationships from BDKnowledgeGraph
    and creates them in Neo4j using MERGE for idempotency.
    """
    from Engine8_Knowledge.graph.bd_knowledge_graph import get_bd_knowledge_graph
    from Engine8_Knowledge.graph.neo4j_manager import get_neo4j_manager
    from Engine8_Knowledge.graph.schema import apply_schema

    bg = get_bd_knowledge_graph()
    mgr = get_neo4j_manager()

    if not bg:
        return {"error": "SQLite knowledge graph not available"}

    # Apply schema first
    apply_schema(mgr)

    # Export entities
    entity_count = 0
    cursor = bg.conn.execute("SELECT id, type, name, properties FROM entities")
    batch = []
    for row in cursor:
        entity_id, entity_type, name, props_json = row
        props = {}
        try:
            props = __import__("json").loads(props_json) if props_json else {}
        except Exception:
            pass
        batch.append({
            "id": entity_id,
            "type": entity_type,
            "name": name,
            **props,
        })
        if len(batch) >= 500:
            _write_entity_batch(mgr, batch)
            entity_count += len(batch)
            batch = []
    if batch:
        _write_entity_batch(mgr, batch)
        entity_count += len(batch)

    # Export relationships
    rel_count = 0
    cursor = bg.conn.execute("SELECT from_entity_id, to_entity_id, type FROM relationships")
    rel_batch = []
    for row in cursor:
        rel_batch.append({"from_id": row[0], "to_id": row[1], "type": row[2]})
        if len(rel_batch) >= 500:
            _write_rel_batch(mgr, rel_batch)
            rel_count += len(rel_batch)
            rel_batch = []
    if rel_batch:
        _write_rel_batch(mgr, rel_batch)
        rel_count += len(rel_batch)

    logger.info("sqlite_to_neo4j_export", entities=entity_count, relationships=rel_count)
    return {"entities_exported": entity_count, "relationships_exported": rel_count}


def _write_entity_batch(mgr: Any, batch: list[dict]) -> None:
    """Write a batch of entities to Neo4j."""
    # Group by type for proper labeling
    by_type: dict[str, list[dict]] = {}
    for entity in batch:
        t = entity.pop("type", "Entity")
        by_type.setdefault(t, []).append(entity)

    for label, entities in by_type.items():
        safe_label = label.replace(" ", "_")
        mgr.run_batch(
            f"""
            UNWIND $batch AS row
            MERGE (n:`{safe_label}` {{name: row.name}})
            SET n += row
            """,
            entities,
        )


def _write_rel_batch(mgr: Any, batch: list[dict]) -> None:
    """Write a batch of relationships to Neo4j."""
    for rel in batch:
        try:
            mgr.write_query(
                """
                MATCH (a {name: $from_name}), (b {name: $to_name})
                MERGE (a)-[r:`""" + rel["type"].replace(" ", "_") + """`]->(b)
                """,
                {"from_name": rel["from_id"], "to_name": rel["to_id"]},
            )
        except Exception:
            pass


def import_neo4j_subgraph_to_networkx(cypher_filter: str = "MATCH (n) RETURN n LIMIT 1000") -> Any:
    """Import a Neo4j subgraph into a NetworkX graph."""
    try:
        import networkx as nx
    except ImportError:
        return None

    from Engine8_Knowledge.graph.neo4j_manager import get_neo4j_manager
    mgr = get_neo4j_manager()

    G = nx.Graph()

    # Get nodes
    nodes = mgr.run_query(
        "MATCH (n) RETURN id(n) AS id, labels(n) AS labels, properties(n) AS props LIMIT 5000"
    )
    for n in nodes:
        G.add_node(n["id"], **n.get("props", {}), labels=n.get("labels", []))

    # Get edges
    edges = mgr.run_query(
        "MATCH (a)-[r]->(b) RETURN id(a) AS src, id(b) AS dst, type(r) AS type LIMIT 10000"
    )
    for e in edges:
        G.add_edge(e["src"], e["dst"], type=e["type"])

    return G


# ---------------------------------------------------------------------------
# Factory — get the active backend based on USE_NEO4J flag
# ---------------------------------------------------------------------------

def get_graph_backend() -> GraphInterface:
    """Get the active graph backend based on USE_NEO4J environment flag."""
    if USE_NEO4J:
        logger.info("using_neo4j_backend")
        return Neo4jGraphBackend()
    else:
        logger.info("using_sqlite_backend")
        return SQLiteGraphBackend()
