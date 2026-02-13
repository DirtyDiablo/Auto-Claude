"""
Graph RAG Engine - Combines knowledge graph traversal with vector retrieval.

Flow:
1. Extract entity mentions from query
2. Traverse graph neighborhood around those entities
3. Combine graph context with Qdrant vector search results
4. Return merged, ranked results with provenance
"""

import os
import sys
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from Engine8_Knowledge.graph.bd_knowledge_graph import (
    BDKnowledgeGraph,
    get_knowledge_graph,
    Entity,
)

logger = logging.getLogger(__name__)


@dataclass
class GraphRAGResult:
    """Result from Graph RAG query."""
    query: str
    answer: str
    graph_entities: List[Dict] = field(default_factory=list)
    graph_relationships: List[Dict] = field(default_factory=list)
    vector_results: List[Dict] = field(default_factory=list)
    merged_context: str = ""
    provenance: Dict[str, int] = field(default_factory=dict)
    confidence: float = 0.0
    elapsed_ms: int = 0


class GraphRAGEngine:
    """
    Hybrid retrieval engine combining knowledge graph traversal
    with vector similarity search for richer, more accurate answers.
    """

    def __init__(self, graph: Optional[BDKnowledgeGraph] = None, vector_store=None):
        self.graph = graph or get_knowledge_graph()
        self.vector_store = vector_store
        self._entity_index: Dict[str, str] = {}  # lowercase name -> entity_id
        self._rebuild_entity_index()

    def _rebuild_entity_index(self):
        """Build lowercase name lookup for fast entity extraction."""
        self._entity_index.clear()
        for eid, entity in self.graph._entity_cache.items():
            self._entity_index[entity.name.lower()] = eid
            # Also index acronyms from properties
            acronym = entity.properties.get("acronym", "")
            if acronym:
                self._entity_index[acronym.lower()] = eid

    def extract_entities(self, query: str) -> List[Entity]:
        """
        Extract known entities mentioned in the query.
        Uses exact and partial matching against the entity cache.
        """
        query_lower = query.lower()
        found: Dict[str, Entity] = {}

        # Exact match on entity names (longest first to avoid partial overlaps)
        names_sorted = sorted(self._entity_index.keys(), key=len, reverse=True)
        remaining = query_lower

        for name in names_sorted:
            if len(name) < 3:
                continue
            if name in remaining:
                eid = self._entity_index[name]
                entity = self.graph.get_entity(eid)
                if entity and eid not in found:
                    found[eid] = entity
                # Remove match to avoid double-counting
                remaining = remaining.replace(name, " ", 1)

        return list(found.values())

    def get_graph_neighborhood(
        self, entities: List[Entity], max_hops: int = 2, max_neighbors: int = 50
    ) -> tuple[List[Dict], List[Dict]]:
        """
        Traverse the graph neighborhood around seed entities.
        Returns (entities_found, relationships_found).
        """
        visited_entities: Dict[str, Dict] = {}
        relationships_found: List[Dict] = []

        # Seed entities
        for e in entities:
            visited_entities[e.id] = {
                "id": e.id,
                "type": e.type,
                "name": e.name,
                "hop": 0,
                **e.properties,
            }

        # BFS expansion
        frontier = [(e.id, 0) for e in entities]

        while frontier and len(visited_entities) < max_neighbors:
            next_frontier = []
            for eid, hop in frontier:
                if hop >= max_hops:
                    continue
                rels = self.graph.get_relationships(eid)
                for rel in rels:
                    other_id = (
                        rel.to_entity_id
                        if rel.from_entity_id == eid
                        else rel.from_entity_id
                    )
                    # Record relationship
                    relationships_found.append({
                        "from": rel.from_entity_id,
                        "to": rel.to_entity_id,
                        "type": rel.type,
                        "confidence": rel.confidence,
                    })

                    if other_id not in visited_entities:
                        other = self.graph.get_entity(other_id)
                        if other:
                            visited_entities[other_id] = {
                                "id": other.id,
                                "type": other.type,
                                "name": other.name,
                                "hop": hop + 1,
                                **other.properties,
                            }
                            next_frontier.append((other_id, hop + 1))

                    if len(visited_entities) >= max_neighbors:
                        break

            frontier = next_frontier

        return list(visited_entities.values()), relationships_found

    def _build_graph_context(
        self, entities: List[Dict], relationships: List[Dict]
    ) -> str:
        """Build a textual context string from graph neighborhood."""
        lines = []

        # Group entities by type
        by_type: Dict[str, List[Dict]] = {}
        for e in entities:
            t = e.get("type", "Unknown")
            by_type.setdefault(t, []).append(e)

        for etype, ents in by_type.items():
            lines.append(f"\n=== {etype}s ({len(ents)}) ===")
            for e in ents[:15]:
                props = {k: v for k, v in e.items() if k not in ("id", "type", "name", "hop") and v}
                prop_str = ", ".join(f"{k}={v}" for k, v in props.items())
                lines.append(f"  - {e['name']}" + (f" ({prop_str})" if prop_str else ""))

        if relationships:
            # Deduplicate relationships
            seen = set()
            unique_rels = []
            for r in relationships:
                key = (r["from"], r["to"], r["type"])
                if key not in seen:
                    seen.add(key)
                    unique_rels.append(r)

            lines.append(f"\n=== Relationships ({len(unique_rels)}) ===")
            # Build name lookup
            name_map = {e["id"]: e["name"] for e in entities}
            for r in unique_rels[:30]:
                from_name = name_map.get(r["from"], r["from"][:8])
                to_name = name_map.get(r["to"], r["to"][:8])
                lines.append(f"  - {from_name} --[{r['type']}]--> {to_name}")

        return "\n".join(lines)

    def _get_vector_results(self, query: str, limit: int = 10) -> List[Dict]:
        """Fetch vector search results from Qdrant store."""
        if not self.vector_store:
            return []

        results = []
        try:
            for collection in ["contacts", "programs", "jobs", "documents"]:
                try:
                    hits = self.vector_store.search(query, collection=collection, limit=max(3, limit // 4))
                    for h in hits:
                        payload = h.payload if hasattr(h, "payload") else (h if isinstance(h, dict) else {})
                        results.append({
                            "collection": collection,
                            "score": getattr(h, "score", 0.0) if hasattr(h, "score") else payload.get("score", 0),
                            "text": payload.get("text", payload.get("content", payload.get("name", ""))),
                            "metadata": {k: v for k, v in payload.items() if k not in ("text", "content", "vector")},
                        })
                except Exception:
                    continue

            # Sort by score descending
            results.sort(key=lambda r: r.get("score", 0), reverse=True)
        except Exception as e:
            logger.warning(f"Vector search error: {e}")

        return results[:limit]

    def query(
        self,
        question: str,
        max_hops: int = 2,
        vector_limit: int = 10,
        max_neighbors: int = 50,
    ) -> GraphRAGResult:
        """
        Execute a Graph RAG query.

        1. Extract entities from the question
        2. Traverse graph neighborhood
        3. Fetch vector results
        4. Merge context
        5. Return combined result
        """
        import time
        start = time.time()

        # Step 1: Entity extraction
        seed_entities = self.extract_entities(question)

        # Step 2: Graph neighborhood
        graph_entities = []
        graph_rels = []
        if seed_entities:
            graph_entities, graph_rels = self.get_graph_neighborhood(
                seed_entities, max_hops=max_hops, max_neighbors=max_neighbors
            )

        # Step 3: Vector search
        vector_results = self._get_vector_results(question, limit=vector_limit)

        # Step 4: Build merged context
        graph_context = self._build_graph_context(graph_entities, graph_rels)

        vector_context = ""
        if vector_results:
            vector_context = "\n=== Vector Search Results ===\n"
            for vr in vector_results[:8]:
                text = str(vr.get("text", ""))[:200]
                vector_context += f"  [{vr['collection']}] {text}\n"

        merged = graph_context + "\n" + vector_context if vector_context else graph_context

        # Step 5: Build answer summary
        if seed_entities:
            entity_names = [e.name for e in seed_entities]
            answer = (
                f"Found {len(graph_entities)} related entities and "
                f"{len(graph_rels)} relationships in the knowledge graph "
                f"around: {', '.join(entity_names)}. "
                f"Also retrieved {len(vector_results)} vector search results."
            )
            confidence = min(0.95, 0.5 + 0.1 * len(seed_entities) + 0.05 * min(len(graph_entities), 10))
        else:
            answer = (
                f"No known entities detected in query. "
                f"Retrieved {len(vector_results)} results from vector search."
            )
            confidence = 0.3 if vector_results else 0.1

        elapsed_ms = int((time.time() - start) * 1000)

        return GraphRAGResult(
            query=question,
            answer=answer,
            graph_entities=graph_entities,
            graph_relationships=graph_rels,
            vector_results=vector_results,
            merged_context=merged,
            provenance={
                "graph_entities": len(graph_entities),
                "graph_relationships": len(graph_rels),
                "vector_results": len(vector_results),
                "seed_entities": len(seed_entities),
            },
            confidence=confidence,
            elapsed_ms=elapsed_ms,
        )

    def get_entity_context(self, entity_name: str) -> Dict:
        """Get rich context for a specific entity (for detail panels)."""
        entity = self.graph.find_entity(entity_name)
        if not entity:
            return {"error": f"Entity not found: {entity_name}"}

        entities, rels = self.get_graph_neighborhood([entity], max_hops=1, max_neighbors=30)
        vector_hits = self._get_vector_results(entity_name, limit=5)

        return {
            "entity": entity.to_dict(),
            "neighbors": [e for e in entities if e["id"] != entity.id],
            "relationships": rels,
            "vector_hits": vector_hits,
        }


# Singleton
_graph_rag_instance: Optional[GraphRAGEngine] = None


def get_graph_rag(vector_store=None) -> GraphRAGEngine:
    """Get Graph RAG singleton."""
    global _graph_rag_instance
    if _graph_rag_instance is None:
        _graph_rag_instance = GraphRAGEngine(vector_store=vector_store)
    return _graph_rag_instance
