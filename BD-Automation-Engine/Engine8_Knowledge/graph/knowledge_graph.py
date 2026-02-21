"""
BDKnowledgeGraph - Enhanced graph layer for defense BD intelligence.

Provides entity/relationship management, BFS shortest path, community detection,
teaming partner recommendations, and competitive landscape analysis.

Uses an in-memory dict-based graph with optional LightRAG integration.
Serializable to JSON for persistence.
"""

import hashlib
import json
import os
from collections import deque
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

try:
    import structlog

    logger = structlog.get_logger(__name__)
except ImportError:
    import logging

    logger = logging.getLogger(__name__)

# Valid entity and relationship types for the defense BD domain
ENTITY_TYPES = frozenset(
    {"PROGRAM", "COMPANY", "PERSON", "AGENCY", "INSTALLATION", "CONTRACT"}
)

RELATIONSHIP_TYPES = frozenset(
    {
        "PRIMES",
        "WORKS_ON",
        "COMPETES_WITH",
        "SUBCONTRACTS",
        "LOCATED_AT",
        "AWARDED_BY",
        "EMPLOYS",
    }
)


def _make_id(name: str, entity_type: str) -> str:
    """Generate a deterministic entity ID from name and type."""
    raw = f"{entity_type}:{name}".lower()
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


class BDKnowledgeGraph:
    """Defense BD knowledge graph with relationship queries.

    Core data structures:
        _graph: {entity_id: {id, name, type, metadata, relations: [{target, relation_type, weight}]}}

    All graph operations are performed in-memory with no external dependencies.
    """

    def __init__(self, persist_path: str = None):
        self._graph: Dict[str, Dict[str, Any]] = {}
        self._name_index: Dict[str, str] = {}  # lowercase name -> entity_id
        self._lightrag = None
        self._persist_path = persist_path
        self._init_lightrag()
        if persist_path and os.path.exists(persist_path):
            self._load(persist_path)

    def _init_lightrag(self):
        """Attempt to initialize LightRAG engine for augmented queries."""
        try:
            from Engine8_Knowledge.scripts.lightrag_engine import get_knowledge_graph

            self._lightrag = get_knowledge_graph()
            logger.info("lightrag_integration_enabled")
        except (ImportError, Exception) as exc:
            logger.info("lightrag_not_available", reason=str(exc))
            self._lightrag = None

    # ------------------------------------------------------------------
    # Entity operations
    # ------------------------------------------------------------------

    def add_entity(
        self, name: str, entity_type: str, metadata: Optional[Dict] = None
    ) -> str:
        """Add an entity to the graph.

        Args:
            name: Entity display name.
            entity_type: One of ENTITY_TYPES (PROGRAM, COMPANY, PERSON, ...).
            metadata: Optional key-value metadata.

        Returns:
            The entity ID (deterministic, based on name+type).

        Raises:
            ValueError: If entity_type is not in ENTITY_TYPES.
        """
        if entity_type not in ENTITY_TYPES:
            raise ValueError(
                f"Unknown entity type '{entity_type}'. "
                f"Valid types: {sorted(ENTITY_TYPES)}"
            )

        entity_id = _make_id(name, entity_type)

        if entity_id in self._graph:
            # Merge metadata into existing entity
            if metadata:
                self._graph[entity_id]["metadata"].update(metadata)
            return entity_id

        self._graph[entity_id] = {
            "id": entity_id,
            "name": name,
            "type": entity_type,
            "metadata": metadata or {},
            "relations": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._name_index[name.lower()] = entity_id
        return entity_id

    def get_entity(self, entity_id: str) -> Optional[Dict]:
        """Get entity with all relationships by ID."""
        node = self._graph.get(entity_id)
        if node is None:
            return None
        return dict(node)

    def get_relationships(
        self, entity_id: str, relation_type: Optional[str] = None
    ) -> List[Dict]:
        """Get entity relationships, optionally filtered by type.

        Args:
            entity_id: The entity to query.
            relation_type: If set, only return relations of this type.

        Returns:
            List of relation dicts with keys: target, relation_type, weight.
        """
        node = self._graph.get(entity_id)
        if node is None:
            return []

        relations = node["relations"]
        if relation_type is not None:
            relations = [r for r in relations if r["relation_type"] == relation_type]
        return list(relations)

    def search_entities(
        self,
        query: str,
        entity_type: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict]:
        """Search entities by name (case-insensitive substring match).

        Args:
            query: Search string.
            entity_type: Optional filter by entity type.
            limit: Max results to return.

        Returns:
            List of matching entity dicts (without relations for brevity).
        """
        query_lower = query.lower()
        results: List[Dict] = []

        for node in self._graph.values():
            if entity_type and node["type"] != entity_type:
                continue
            if query_lower in node["name"].lower():
                results.append(
                    {
                        "id": node["id"],
                        "name": node["name"],
                        "type": node["type"],
                        "metadata": node["metadata"],
                    }
                )
                if len(results) >= limit:
                    break

        return results

    # ------------------------------------------------------------------
    # Relationship operations
    # ------------------------------------------------------------------

    def add_relationship(
        self,
        source: str,
        target: str,
        relation_type: str,
        weight: float = 1.0,
    ) -> None:
        """Add a directed relationship between two entities.

        Args:
            source: Source entity ID.
            target: Target entity ID.
            relation_type: One of RELATIONSHIP_TYPES.
            weight: Relationship strength (0.0 - 1.0).

        Raises:
            ValueError: If source/target not found or relation_type invalid.
        """
        if relation_type not in RELATIONSHIP_TYPES:
            raise ValueError(
                f"Unknown relation type '{relation_type}'. "
                f"Valid types: {sorted(RELATIONSHIP_TYPES)}"
            )
        if source not in self._graph:
            raise ValueError(f"Source entity not found: {source}")
        if target not in self._graph:
            raise ValueError(f"Target entity not found: {target}")

        # Avoid exact duplicate relations
        for rel in self._graph[source]["relations"]:
            if rel["target"] == target and rel["relation_type"] == relation_type:
                rel["weight"] = weight  # update weight
                return

        self._graph[source]["relations"].append(
            {
                "target": target,
                "relation_type": relation_type,
                "weight": weight,
            }
        )

    # ------------------------------------------------------------------
    # Graph algorithms
    # ------------------------------------------------------------------

    def shortest_path(
        self, source: str, target: str, max_depth: int = 5
    ) -> List[Dict]:
        """Find shortest path between two entities using BFS.

        Args:
            source: Start entity ID.
            target: End entity ID.
            max_depth: Maximum hops to search.

        Returns:
            Ordered list of entity dicts along the path (including source
            and target). Empty list if no path exists.
        """
        if source not in self._graph or target not in self._graph:
            return []
        if source == target:
            return [self._path_node(source)]

        # Build undirected adjacency for BFS
        adjacency = self._build_adjacency()

        visited = {source}
        queue: deque = deque()
        queue.append((source, [source]))

        while queue:
            current, path = queue.popleft()
            if len(path) > max_depth:
                continue

            for neighbor in adjacency.get(current, set()):
                if neighbor == target:
                    full = path + [neighbor]
                    return [self._path_node(nid) for nid in full]

                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        return []

    def _path_node(self, entity_id: str) -> Dict:
        """Return a lightweight dict for path output."""
        node = self._graph[entity_id]
        return {"id": node["id"], "name": node["name"], "type": node["type"]}

    def _build_adjacency(self) -> Dict[str, set]:
        """Build undirected adjacency map from all relations."""
        adj: Dict[str, set] = {}
        for eid, node in self._graph.items():
            if eid not in adj:
                adj[eid] = set()
            for rel in node["relations"]:
                t = rel["target"]
                adj[eid].add(t)
                if t not in adj:
                    adj[t] = set()
                adj[t].add(eid)
        return adj

    def find_communities(self, min_size: int = 3) -> List[List[Dict]]:
        """Detect communities using connected components (BFS).

        Args:
            min_size: Minimum component size to include.

        Returns:
            List of communities, each a list of entity summary dicts.
        """
        adjacency = self._build_adjacency()
        visited: set = set()
        communities: List[List[Dict]] = []

        for entity_id in self._graph:
            if entity_id in visited:
                continue
            # BFS to find connected component
            component: List[str] = []
            queue: deque = deque([entity_id])
            visited.add(entity_id)
            while queue:
                current = queue.popleft()
                component.append(current)
                for neighbor in adjacency.get(current, set()):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)

            if len(component) >= min_size:
                communities.append([self._path_node(eid) for eid in component])

        return communities

    # ------------------------------------------------------------------
    # BD-specific queries
    # ------------------------------------------------------------------

    def get_teaming_partners(
        self, company: str, program: Optional[str] = None
    ) -> List[Dict]:
        """Recommend teaming partners based on graph relationships.

        Finds companies connected to the given company via SUBCONTRACTS,
        PRIMES (shared programs), or WORKS_ON relationships. Optionally
        filters by a specific program.

        Args:
            company: Company name (case-insensitive lookup).
            program: Optional program name filter.

        Returns:
            List of partner dicts with name, relationship path, and score.
        """
        company_id = self._resolve_name(company)
        if company_id is None:
            return []

        program_id = self._resolve_name(program) if program else None

        partners: Dict[str, Dict] = {}
        adjacency = self._build_adjacency()

        # Direct relationships (1 hop)
        for rel in self._graph[company_id]["relations"]:
            tid = rel["target"]
            tnode = self._graph.get(tid)
            if tnode and tnode["type"] == "COMPANY" and tid != company_id:
                partners[tid] = {
                    "id": tid,
                    "name": tnode["name"],
                    "relation": rel["relation_type"],
                    "weight": rel["weight"],
                    "hops": 1,
                }

        # Also check reverse edges (incoming relations)
        for eid, node in self._graph.items():
            if eid == company_id:
                continue
            if node["type"] != "COMPANY":
                continue
            for rel in node["relations"]:
                if rel["target"] == company_id and eid not in partners:
                    partners[eid] = {
                        "id": eid,
                        "name": node["name"],
                        "relation": rel["relation_type"],
                        "weight": rel["weight"],
                        "hops": 1,
                    }

        # 2-hop: companies sharing a program
        for rel in self._graph[company_id]["relations"]:
            mid = rel["target"]
            mid_node = self._graph.get(mid)
            if not mid_node or mid_node["type"] != "PROGRAM":
                continue
            if program_id and mid != program_id:
                continue
            # Find other companies connected to this program
            for eid, node in self._graph.items():
                if node["type"] != "COMPANY" or eid == company_id:
                    continue
                for r2 in node["relations"]:
                    if r2["target"] == mid and eid not in partners:
                        partners[eid] = {
                            "id": eid,
                            "name": node["name"],
                            "relation": f"shared_program:{mid_node['name']}",
                            "weight": r2["weight"] * rel["weight"],
                            "hops": 2,
                        }

        result = sorted(partners.values(), key=lambda p: (-p["weight"], p["hops"]))
        return result

    def get_competitive_landscape(self, program: str) -> Dict:
        """Get all competitors, subs, and incumbents for a program.

        Args:
            program: Program name (case-insensitive).

        Returns:
            Dict with program info, incumbents, competitors, and
            subcontractors lists.
        """
        program_id = self._resolve_name(program)
        if program_id is None:
            return {"error": f"Program not found: {program}"}

        pnode = self._graph[program_id]
        landscape: Dict[str, Any] = {
            "program": self._path_node(program_id),
            "incumbents": [],
            "competitors": [],
            "subcontractors": [],
        }

        # Find companies connected to this program
        connected_companies: Dict[str, Dict] = {}

        # Outgoing from program
        for rel in pnode["relations"]:
            tnode = self._graph.get(rel["target"])
            if tnode and tnode["type"] == "COMPANY":
                connected_companies[rel["target"]] = {
                    "entity": self._path_node(rel["target"]),
                    "relation": rel["relation_type"],
                    "weight": rel["weight"],
                }

        # Incoming to program
        for eid, node in self._graph.items():
            if node["type"] != "COMPANY":
                continue
            for rel in node["relations"]:
                if rel["target"] == program_id and eid not in connected_companies:
                    connected_companies[eid] = {
                        "entity": self._path_node(eid),
                        "relation": rel["relation_type"],
                        "weight": rel["weight"],
                    }

        # Classify
        for info in connected_companies.values():
            rtype = info["relation"]
            entry = {"company": info["entity"], "weight": info["weight"]}

            if rtype == "PRIMES":
                landscape["incumbents"].append(entry)
            elif rtype == "SUBCONTRACTS":
                landscape["subcontractors"].append(entry)
            elif rtype == "COMPETES_WITH":
                landscape["competitors"].append(entry)
            else:
                # Any other link (WORKS_ON, etc.) — treat as incumbent
                landscape["incumbents"].append(entry)

        # Also find companies that compete with incumbents
        incumbent_ids = {
            e["company"]["id"] for e in landscape["incumbents"]
        }
        for iid in list(incumbent_ids):
            inode = self._graph.get(iid)
            if not inode:
                continue
            for rel in inode["relations"]:
                if rel["relation_type"] == "COMPETES_WITH":
                    comp = self._graph.get(rel["target"])
                    if comp and rel["target"] not in incumbent_ids:
                        already = {c["company"]["id"] for c in landscape["competitors"]}
                        if rel["target"] not in already:
                            landscape["competitors"].append(
                                {
                                    "company": self._path_node(rel["target"]),
                                    "weight": rel["weight"],
                                    "via_incumbent": inode["name"],
                                }
                            )

        return landscape

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    def get_stats(self) -> Dict:
        """Graph statistics: entity counts by type, relationship counts, community count."""
        type_counts: Dict[str, int] = {}
        rel_type_counts: Dict[str, int] = {}
        total_relations = 0

        for node in self._graph.values():
            type_counts[node["type"]] = type_counts.get(node["type"], 0) + 1
            for rel in node["relations"]:
                rt = rel["relation_type"]
                rel_type_counts[rt] = rel_type_counts.get(rt, 0) + 1
                total_relations += 1

        communities = self.find_communities(min_size=2)

        return {
            "total_entities": len(self._graph),
            "entities_by_type": type_counts,
            "total_relationships": total_relations,
            "relationships_by_type": rel_type_counts,
            "community_count": len(communities),
        }

    # ------------------------------------------------------------------
    # Build from Qdrant
    # ------------------------------------------------------------------

    def build_from_qdrant(self) -> Dict:
        """Build graph from existing Qdrant collections (programs, contacts, jobs).

        Returns:
            Summary dict with counts of entities and relationships added.
        """
        try:
            from Engine8_Knowledge.scripts.vector_store import BDKnowledgeStore

            store = BDKnowledgeStore()
        except Exception as exc:
            logger.warning("qdrant_not_available", error=str(exc))
            return {"error": f"Qdrant not available: {exc}", "added": 0}

        added_entities = 0
        added_relations = 0

        # Programs
        try:
            programs = store.get_all("programs", limit=500)
            for p in programs:
                payload = p.payload if hasattr(p, "payload") else p
                name = payload.get("name", payload.get("program_name", ""))
                if not name:
                    continue
                pid = self.add_entity(
                    name,
                    "PROGRAM",
                    {
                        "agency": payload.get("agency", ""),
                        "value": payload.get("value", payload.get("contract_value", "")),
                        "status": payload.get("status", ""),
                        "clearance": payload.get("clearance", ""),
                    },
                )
                added_entities += 1

                # Agency relationship
                agency = payload.get("agency", "")
                if agency:
                    aid = self.add_entity(agency, "AGENCY")
                    self.add_relationship(pid, aid, "AWARDED_BY")
                    added_relations += 1

                # Prime contractor
                prime = payload.get("prime", "")
                if prime:
                    cid = self.add_entity(prime, "COMPANY")
                    self.add_relationship(cid, pid, "PRIMES")
                    added_entities += 1
                    added_relations += 1

        except Exception as exc:
            logger.warning("qdrant_programs_error", error=str(exc))

        # Contacts
        try:
            contacts = store.get_all("contacts", limit=8000)
            for c in contacts:
                payload = c.payload if hasattr(c, "payload") else c
                name = payload.get("name", payload.get("full_name", ""))
                if not name:
                    continue
                cid = self.add_entity(
                    name,
                    "PERSON",
                    {
                        "title": payload.get("title", payload.get("job_title", "")),
                        "tier": payload.get("tier", ""),
                        "email": payload.get("email", ""),
                    },
                )
                added_entities += 1

                company = payload.get("company", payload.get("employer", ""))
                if company:
                    comp_id = self.add_entity(company, "COMPANY")
                    self.add_relationship(comp_id, cid, "EMPLOYS")
                    added_relations += 1

        except Exception as exc:
            logger.warning("qdrant_contacts_error", error=str(exc))

        # Jobs
        try:
            jobs = store.get_all("jobs", limit=1000)
            for j in jobs:
                payload = j.payload if hasattr(j, "payload") else j
                company = payload.get("company", "")
                program = payload.get("mapped_program", "")

                if company:
                    self.add_entity(company, "COMPANY")
                    added_entities += 1

                if program:
                    prog_id = self._resolve_name(program)
                    if prog_id and company:
                        comp_id = self._resolve_name(company)
                        if comp_id:
                            self.add_relationship(comp_id, prog_id, "WORKS_ON")
                            added_relations += 1

        except Exception as exc:
            logger.warning("qdrant_jobs_error", error=str(exc))

        summary = {
            "entities_added": added_entities,
            "relationships_added": added_relations,
            "stats": self.get_stats(),
        }
        logger.info("graph_built_from_qdrant", **summary)
        return summary

    # ------------------------------------------------------------------
    # Persistence (JSON serialization)
    # ------------------------------------------------------------------

    def to_json(self) -> str:
        """Serialize the full graph to a JSON string."""
        return json.dumps(self._graph, indent=2, default=str)

    def save(self, path: str = None) -> None:
        """Save graph to a JSON file."""
        path = path or self._persist_path
        if not path:
            raise ValueError("No persist path specified")
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w") as f:
            f.write(self.to_json())
        logger.info("graph_saved", path=path, entities=len(self._graph))

    def _load(self, path: str) -> None:
        """Load graph from a JSON file."""
        try:
            with open(path, "r") as f:
                data = json.load(f)
            self._graph = data
            # Rebuild name index
            self._name_index = {}
            for eid, node in self._graph.items():
                self._name_index[node["name"].lower()] = eid
            logger.info("graph_loaded", path=path, entities=len(self._graph))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("graph_load_failed", path=path, error=str(exc))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _resolve_name(self, name: str) -> Optional[str]:
        """Resolve an entity name to its ID (case-insensitive)."""
        if not name:
            return None
        # Direct ID lookup
        if name in self._graph:
            return name
        # Name index lookup
        return self._name_index.get(name.lower())


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_instance: Optional[BDKnowledgeGraph] = None


def get_graph(persist_path: str = None) -> BDKnowledgeGraph:
    """Get or create the BDKnowledgeGraph singleton."""
    global _instance
    if _instance is None:
        if persist_path is None:
            persist_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "data",
                "knowledge_graph.json",
            )
        _instance = BDKnowledgeGraph(persist_path=persist_path)
    return _instance


def reset_graph() -> None:
    """Reset the singleton (mainly for testing)."""
    global _instance
    _instance = None
