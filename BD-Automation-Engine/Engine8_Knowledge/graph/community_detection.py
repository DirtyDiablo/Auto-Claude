"""
Community Detection - Louvain algorithm for finding clusters in the BD knowledge graph.

Identifies communities of closely-connected entities (e.g., program ecosystems,
contractor partnerships, contact clusters) and provides cross-community bridge analysis.
"""

import os
import sys
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from Engine8_Knowledge.graph.bd_knowledge_graph import (
    BDKnowledgeGraph,
    get_knowledge_graph,
)

logger = logging.getLogger(__name__)

try:
    import networkx as nx
    import community as community_louvain  # python-louvain
    LOUVAIN_AVAILABLE = True
except ImportError:
    LOUVAIN_AVAILABLE = False
    logger.warning("python-louvain or networkx not installed. pip install python-louvain networkx")


@dataclass
class Community:
    """A detected community/cluster in the graph."""
    id: int
    entities: List[Dict] = field(default_factory=list)
    size: int = 0
    dominant_type: str = ""
    type_distribution: Dict[str, int] = field(default_factory=dict)
    key_entities: List[str] = field(default_factory=list)
    label: str = ""
    density: float = 0.0


class CommunityDetector:
    """
    Detects communities in the BD knowledge graph using the Louvain algorithm.
    Provides community summaries, cross-community bridges, and membership queries.
    """

    def __init__(self, graph: Optional[BDKnowledgeGraph] = None):
        self.graph = graph or get_knowledge_graph()
        self._communities: Dict[int, Community] = {}
        self._entity_to_community: Dict[str, int] = {}
        self._nx_graph: Optional["nx.Graph"] = None
        self._computed = False

    def _build_networkx_graph(self) -> "nx.Graph":
        """Build a NetworkX graph from the BD knowledge graph."""
        if not LOUVAIN_AVAILABLE:
            raise RuntimeError("python-louvain and networkx are required for community detection")

        G = nx.Graph()

        # Add nodes with attributes
        for eid, entity in self.graph._entity_cache.items():
            G.add_node(eid, name=entity.name, type=entity.type, **entity.properties)

        # Add edges from relationships
        cursor = self.graph.conn.execute(
            "SELECT from_entity_id, to_entity_id, type, confidence FROM relationships"
        )
        for from_id, to_id, rel_type, confidence in cursor:
            if from_id in self.graph._entity_cache and to_id in self.graph._entity_cache:
                G.add_edge(from_id, to_id, type=rel_type, weight=confidence or 1.0)

        self._nx_graph = G
        return G

    def detect_communities(self, resolution: float = 1.0) -> Dict[int, Community]:
        """
        Run Louvain community detection.

        Args:
            resolution: Louvain resolution parameter. Higher = more communities.

        Returns:
            Dict mapping community ID to Community objects
        """
        if self._computed and self._communities:
            return self._communities

        G = self._build_networkx_graph()

        if G.number_of_nodes() == 0:
            logger.warning("Graph has no nodes — cannot detect communities")
            self._computed = True
            return {}

        # Run Louvain
        partition = community_louvain.best_partition(G, resolution=resolution)
        modularity = community_louvain.modularity(partition, G)
        logger.info(f"Louvain detected {len(set(partition.values()))} communities (modularity={modularity:.3f})")

        # Store entity-to-community mapping
        self._entity_to_community = partition

        # Build community objects
        community_members: Dict[int, List[str]] = defaultdict(list)
        for entity_id, comm_id in partition.items():
            community_members[comm_id].append(entity_id)

        self._communities.clear()
        for comm_id, members in community_members.items():
            # Compute type distribution
            type_dist: Dict[str, int] = defaultdict(int)
            entities_list = []

            for eid in members:
                entity = self.graph.get_entity(eid)
                if entity:
                    type_dist[entity.type] += 1
                    entities_list.append({
                        "id": entity.id,
                        "name": entity.name,
                        "type": entity.type,
                    })

            # Dominant type
            dominant = max(type_dist, key=type_dist.get) if type_dist else "Unknown"

            # Key entities: those with highest degree within the community
            member_degrees = [(eid, G.degree(eid)) for eid in members if eid in G]
            member_degrees.sort(key=lambda x: x[1], reverse=True)
            key_entities = []
            for eid, _ in member_degrees[:5]:
                entity = self.graph.get_entity(eid)
                if entity:
                    key_entities.append(entity.name)

            # Compute subgraph density
            subgraph = G.subgraph(members)
            density = nx.density(subgraph) if len(members) > 1 else 0.0

            # Auto-label based on key entities and dominant type
            label = f"{dominant} cluster"
            if key_entities:
                label = f"{key_entities[0]} / {dominant}s ({len(members)})"

            self._communities[comm_id] = Community(
                id=comm_id,
                entities=entities_list,
                size=len(members),
                dominant_type=dominant,
                type_distribution=dict(type_dist),
                key_entities=key_entities,
                label=label,
                density=round(density, 4),
            )

        self._computed = True
        return self._communities

    def get_community_summary(self) -> Dict:
        """Get high-level summary of all communities."""
        communities = self.detect_communities()

        return {
            "total_communities": len(communities),
            "total_entities": sum(c.size for c in communities.values()),
            "modularity": self._get_modularity(),
            "communities": [
                {
                    "id": c.id,
                    "label": c.label,
                    "size": c.size,
                    "dominant_type": c.dominant_type,
                    "type_distribution": c.type_distribution,
                    "key_entities": c.key_entities,
                    "density": c.density,
                }
                for c in sorted(communities.values(), key=lambda c: c.size, reverse=True)
            ],
        }

    def _get_modularity(self) -> float:
        """Compute modularity score of current partition."""
        if not self._nx_graph or not self._entity_to_community:
            return 0.0
        try:
            return round(
                community_louvain.modularity(self._entity_to_community, self._nx_graph),
                4,
            )
        except Exception:
            return 0.0

    def get_community_detail(self, community_id: int) -> Optional[Dict]:
        """Get detailed view of a specific community."""
        communities = self.detect_communities()
        comm = communities.get(community_id)
        if not comm:
            return None

        return {
            "id": comm.id,
            "label": comm.label,
            "size": comm.size,
            "dominant_type": comm.dominant_type,
            "type_distribution": comm.type_distribution,
            "key_entities": comm.key_entities,
            "density": comm.density,
            "entities": comm.entities,
        }

    def get_entity_community(self, entity_name: str) -> Optional[Dict]:
        """Find which community an entity belongs to."""
        self.detect_communities()

        entity = self.graph.find_entity(entity_name)
        if not entity:
            return None

        comm_id = self._entity_to_community.get(entity.id)
        if comm_id is None:
            return None

        comm = self._communities.get(comm_id)
        if not comm:
            return None

        return {
            "entity": {"id": entity.id, "name": entity.name, "type": entity.type},
            "community_id": comm_id,
            "community_label": comm.label,
            "community_size": comm.size,
            "co_members": [
                e for e in comm.entities if e["id"] != entity.id
            ][:20],
        }

    def get_cross_community_bridges(self, limit: int = 20) -> List[Dict]:
        """
        Find entities that bridge multiple communities.
        These are nodes with edges to entities in different communities.
        """
        self.detect_communities()

        if not self._nx_graph or not self._entity_to_community:
            return []

        bridge_scores: Dict[str, Dict] = {}

        for eid in self._nx_graph.nodes():
            my_comm = self._entity_to_community.get(eid)
            if my_comm is None:
                continue

            neighbor_comms = set()
            for neighbor in self._nx_graph.neighbors(eid):
                nb_comm = self._entity_to_community.get(neighbor)
                if nb_comm is not None and nb_comm != my_comm:
                    neighbor_comms.add(nb_comm)

            if neighbor_comms:
                entity = self.graph.get_entity(eid)
                if entity:
                    bridge_scores[eid] = {
                        "entity_id": eid,
                        "name": entity.name,
                        "type": entity.type,
                        "own_community": my_comm,
                        "connected_communities": sorted(neighbor_comms),
                        "bridge_count": len(neighbor_comms),
                        "properties": entity.properties,
                    }

        # Sort by number of cross-community connections
        bridges = sorted(bridge_scores.values(), key=lambda b: b["bridge_count"], reverse=True)
        return bridges[:limit]

    def get_community_graph(self) -> Dict:
        """
        Get community-level graph (meta-graph where nodes are communities
        and edges are cross-community relationships).
        """
        self.detect_communities()

        if not self._nx_graph or not self._entity_to_community:
            return {"nodes": [], "edges": []}

        # Count cross-community edges
        inter_edges: Dict[tuple, int] = defaultdict(int)
        for u, v in self._nx_graph.edges():
            cu = self._entity_to_community.get(u)
            cv = self._entity_to_community.get(v)
            if cu is not None and cv is not None and cu != cv:
                key = (min(cu, cv), max(cu, cv))
                inter_edges[key] += 1

        nodes = [
            {
                "id": c.id,
                "label": c.label,
                "size": c.size,
                "dominant_type": c.dominant_type,
            }
            for c in self._communities.values()
        ]

        edges = [
            {"source": k[0], "target": k[1], "weight": v}
            for k, v in inter_edges.items()
        ]

        return {"nodes": nodes, "edges": edges}

    def invalidate(self):
        """Force recomputation."""
        self._computed = False
        self._communities.clear()
        self._entity_to_community.clear()
        self._nx_graph = None


# Singleton
_detector_instance: Optional[CommunityDetector] = None


def get_community_detector() -> CommunityDetector:
    """Get community detector singleton."""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = CommunityDetector()
    return _detector_instance
