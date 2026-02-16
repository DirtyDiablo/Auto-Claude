"""
Phase 22A — Neo4j Graph Retriever

Graph-aware retrieval that returns context-enriched results from Neo4j.
Maps search queries to Cypher patterns, expands context by traversing
relationships, and formats results as text chunks suitable for RAG.
"""

import re
import logging
from typing import Optional, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class GraphResult:
    """A single graph retrieval result."""

    id: str
    name: str
    entity_type: str
    context_text: str
    relationships: list[dict] = field(default_factory=list)
    properties: dict = field(default_factory=dict)
    score: float = 0.0


class GraphRetriever:
    """Neo4j graph-aware retrieval for enriching search results."""

    def __init__(self, neo4j_manager: Any = None) -> None:
        self._mgr = neo4j_manager

    @property
    def mgr(self) -> Any:
        if self._mgr is None:
            try:
                from Engine8_Knowledge.graph.neo4j_manager import get_neo4j_manager

                self._mgr = get_neo4j_manager()
            except Exception:
                raise RuntimeError("Neo4j manager not available")
        return self._mgr

    def retrieve(
        self,
        query: str,
        entity_type: Optional[str] = None,
        depth: int = 2,
        limit: int = 20,
    ) -> list[GraphResult]:
        """
        Retrieve graph context for a search query.

        Strategy:
        1. Extract entities from query (keyword matching)
        2. Look up entities in Neo4j
        3. Expand context by traversing relationships up to depth hops
        4. Collect connected entities and their properties
        5. Format as GraphResult with relationship context
        """
        entities = self._extract_entities(query)
        results = []

        for entity_name in entities[:5]:  # limit entity lookups
            matches = self.entity_lookup(entity_name, entity_type)
            for match in matches[:3]:
                context = self.expand_context(
                    match["name"],
                    match.get("type", ""),
                    depth,
                )
                context_text = self._format_context_text(match, context)
                results.append(
                    GraphResult(
                        id=f"graph_{match.get('name', '')}",
                        name=match.get("name", ""),
                        entity_type=match.get("type", "Unknown"),
                        context_text=context_text,
                        relationships=context.get("relationships", []),
                        properties=match,
                        score=1.0 / (len(results) + 1),
                    )
                )

        # If no entity matches, try full-text search
        if not results:
            ft_results = self._fulltext_search(query, limit)
            for rank, ft in enumerate(ft_results):
                results.append(
                    GraphResult(
                        id=f"graph_ft_{rank}",
                        name=ft.get("name", ""),
                        entity_type=ft.get("type", ""),
                        context_text=ft.get("name", "") + " — " + ft.get("title", ""),
                        properties=ft,
                        score=ft.get("score", 0.0),
                    )
                )

        return results[:limit]

    def entity_lookup(self, name: str, entity_type: Optional[str] = None) -> list[dict]:
        """Find entity by name across all node types using fulltext index."""
        try:
            if entity_type:
                results = self.mgr.run_query(
                    f"""
                    MATCH (n:`{entity_type}`)
                    WHERE n.name =~ $pattern
                    RETURN n.name AS name, labels(n)[0] AS type,
                           properties(n) AS props
                    LIMIT 5
                    """,
                    {"pattern": f"(?i).*{re.escape(name)}.*"},
                )
            else:
                results = self.mgr.run_query(
                    """
                    MATCH (n)
                    WHERE n.name =~ $pattern
                    RETURN n.name AS name, labels(n)[0] AS type,
                           properties(n) AS props
                    LIMIT 10
                    """,
                    {"pattern": f"(?i).*{re.escape(name)}.*"},
                )
            return [
                {"name": r["name"], "type": r["type"], **r.get("props", {})}
                for r in results
            ]
        except Exception as e:
            logger.warning("entity_lookup_error", name=name, error=str(e)[:100])
            return []

    def expand_context(
        self, entity_name: str, entity_type: str, depth: int = 2
    ) -> dict:
        """Get all connected entities within depth hops."""
        try:
            results = self.mgr.run_query(
                """
                MATCH (n)-[r*1..2]-(m)
                WHERE n.name = $name
                RETURN DISTINCT m.name AS connected_name,
                       labels(m)[0] AS connected_type,
                       [rel IN r | type(rel)] AS rel_types,
                       properties(m) AS props
                LIMIT 50
                """,
                {"name": entity_name},
            )
            relationships = []
            connected = []
            for r in results:
                rel_chain = r.get("rel_types", [])
                relationships.append(
                    {
                        "target": r["connected_name"],
                        "target_type": r["connected_type"],
                        "relationship": " → ".join(rel_chain)
                        if rel_chain
                        else "CONNECTED",
                    }
                )
                connected.append(
                    {
                        "name": r["connected_name"],
                        "type": r["connected_type"],
                        **r.get("props", {}),
                    }
                )
            return {"relationships": relationships, "connected": connected}
        except Exception as e:
            logger.warning(
                "expand_context_error", entity=entity_name, error=str(e)[:100]
            )
            return {"relationships": [], "connected": []}

    def program_context(self, program_name: str) -> dict:
        """Full context for a program: people, companies, jobs, contracts."""
        try:
            result = self.mgr.run_single(
                """
                MATCH (pr:Program)
                WHERE pr.name =~ $pattern OR pr.acronym =~ $pattern
                WITH pr
                OPTIONAL MATCH (c:Company)-[:PRIMES_ON]->(pr)
                WITH pr, collect(DISTINCT c.name) AS primes
                OPTIONAL MATCH (p:Person)-[:MANAGES]->(pr)
                WITH pr, primes, collect(DISTINCT {name: p.name, title: p.title, tier: p.tier}) AS managers
                OPTIONAL MATCH (j:Job)-[:MAPPED_TO]->(pr)
                WITH pr, primes, managers, count(j) AS job_count
                RETURN pr.name AS name, pr.acronym AS acronym,
                       pr.value AS value, pr.agency_owner AS agency,
                       primes, managers, job_count
                """,
                {"pattern": f"(?i).*{re.escape(program_name)}.*"},
            )
            return result or {"name": program_name, "found": False}
        except Exception as e:
            logger.warning("program_context_error", error=str(e)[:100])
            return {"name": program_name, "found": False}

    def contact_context(self, person_name: str) -> dict:
        """Full context for a contact: company, programs, interactions, connections."""
        try:
            result = self.mgr.run_single(
                """
                MATCH (p:Person)
                WHERE p.name =~ $pattern
                WITH p
                OPTIONAL MATCH (p)-[:WORKS_AT]->(c:Company)
                OPTIONAL MATCH (p)-[:MANAGES]->(pr:Program)
                WITH p, c, collect(DISTINCT pr.name) AS programs
                OPTIONAL MATCH (p)-[:CONTACTED_BY]->(i:Interaction)
                WITH p, c, programs, count(i) AS interaction_count
                OPTIONAL MATCH (p)-[r]-(other:Person)
                WITH p, c, programs, interaction_count,
                     collect(DISTINCT {name: other.name, rel: type(r)})[0..5] AS connections
                RETURN p.name AS name, p.title AS title, p.tier AS tier,
                       p.email AS email, c.name AS company,
                       programs, interaction_count, connections
                """,
                {"pattern": f"(?i).*{re.escape(person_name)}.*"},
            )
            return result or {"name": person_name, "found": False}
        except Exception as e:
            logger.warning("contact_context_error", error=str(e)[:100])
            return {"name": person_name, "found": False}

    def relationship_context(self, person_a: str, person_b: str) -> dict:
        """All relationship paths and shared context between two people."""
        try:
            result = self.mgr.run_single(
                """
                MATCH (a:Person), (b:Person),
                      path = shortestPath((a)-[*..6]-(b))
                WHERE a.name =~ $pattern_a AND b.name =~ $pattern_b
                RETURN [n IN nodes(path) | coalesce(n.name, labels(n)[0])] AS path_names,
                       [r IN relationships(path) | type(r)] AS path_rels,
                       length(path) AS hops
                """,
                {
                    "pattern_a": f"(?i).*{re.escape(person_a)}.*",
                    "pattern_b": f"(?i).*{re.escape(person_b)}.*",
                },
            )
            if not result:
                return {"from": person_a, "to": person_b, "found": False}
            return {
                "from": person_a,
                "to": person_b,
                "found": True,
                "path": result.get("path_names", []),
                "relationships": result.get("path_rels", []),
                "hops": result.get("hops", 0),
            }
        except Exception as e:
            logger.warning("relationship_context_error", error=str(e)[:100])
            return {"from": person_a, "to": person_b, "found": False}

    # -- Internal helpers --

    def _extract_entities(self, query: str) -> list[str]:
        """Extract potential entity names from query text using heuristics."""
        entities = []

        # Look for capitalized multi-word names (e.g., "John Smith", "Northrop Grumman")
        name_pattern = re.findall(r"[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+", query)
        entities.extend(name_pattern)

        # Look for all-caps acronyms (e.g., DCGS, GDIT, SAIC)
        acronyms = re.findall(r"\b[A-Z]{2,10}\b", query)
        entities.extend(acronyms)

        # Look for quoted strings
        quoted = re.findall(r'"([^"]+)"', query)
        entities.extend(quoted)

        return list(dict.fromkeys(entities))  # dedupe preserving order

    def _fulltext_search(self, query: str, limit: int = 10) -> list[dict]:
        """Fallback fulltext search across all node types."""
        try:
            # Try person fulltext index first
            results = self.mgr.run_query(
                """
                CALL db.index.fulltext.queryNodes('person_fulltext', $query)
                YIELD node, score
                RETURN node.name AS name, node.title AS title,
                       labels(node)[0] AS type, score
                LIMIT $limit
                """,
                {"query": query, "limit": limit},
            )
            return results
        except Exception:
            return []

    def _format_context_text(self, entity: dict, context: dict) -> str:
        """Convert entity + context to a text chunk suitable for RAG."""
        parts = []

        name = entity.get("name", "Unknown")
        etype = entity.get("type", "Entity")
        title = entity.get("title", "")
        company = entity.get("company", "")

        header = f"{name} is a {etype}"
        if title:
            header += f", {title}"
        if company:
            header += f" at {company}"
        parts.append(header + ".")

        # Add relationship summary
        rels = context.get("relationships", [])
        if rels:
            rel_summary = []
            for r in rels[:10]:
                rel_summary.append(
                    f"{r['relationship']} → {r['target']} ({r['target_type']})"
                )
            parts.append("Connections: " + "; ".join(rel_summary) + ".")

        return " ".join(parts)


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_instance: Optional[GraphRetriever] = None


def get_graph_retriever() -> GraphRetriever:
    global _instance
    if _instance is None:
        _instance = GraphRetriever()
    return _instance
