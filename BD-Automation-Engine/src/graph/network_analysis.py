"""Phase 34A — Network Analysis Engine

Graph-level analytics: community detection, bridge identification,
density measurement, and growth tracking.
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


# =========================================
# DATA CLASSES
# =========================================

@dataclass
class Community:
    id: int
    label: str
    members: List[str]
    member_names: List[str]
    size: int
    avg_strength: float
    programs: List[str] = field(default_factory=list)
    key_member: str = ""


@dataclass
class BridgeContact:
    contact_id: str
    name: str
    communities: List[int]
    community_labels: List[str]
    bridge_score: float  # 0-100
    connections_across: int


@dataclass
class DensityReport:
    scope: str  # "global" or program name
    total_nodes: int
    total_edges: int
    density: float  # 0-1
    avg_degree: float
    avg_strength: float
    clustering_coefficient: float
    assessment: str  # "dense", "moderate", "sparse"


@dataclass
class GrowthReport:
    period_days: int
    new_contacts: int
    new_relationships: int
    lost_relationships: int
    net_growth: int
    growth_rate: float  # percent
    strongest_new: List[str]
    assessment: str  # "expanding", "stable", "contracting"


class NetworkAnalyzer:
    """Graph-level analytics for the contact network."""

    def __init__(self, graph_client: Any = None):
        self._graph = graph_client
        self._nodes: Dict[str, dict] = {}
        self._adjacency: Dict[str, Dict[str, float]] = {}

    def set_graph_data(self, nodes: List[dict], edges: List[dict]) -> None:
        """Load graph data for analysis."""
        self._nodes = {n.get("id", str(i)): n for i, n in enumerate(nodes)}
        self._adjacency = {nid: {} for nid in self._nodes}
        for edge in edges:
            src = edge.get("source", edge.get("from", ""))
            tgt = edge.get("target", edge.get("to", ""))
            strength = edge.get("strength", edge.get("weight", 50.0))
            if src in self._adjacency:
                self._adjacency[src][tgt] = strength
            if tgt in self._adjacency:
                self._adjacency.setdefault(tgt, {})[src] = strength

    async def detect_communities(
        self,
        min_community_size: int = 2,
    ) -> List[Community]:
        """Detect communities using label propagation algorithm."""
        if not self._adjacency:
            return []

        # Label propagation
        labels: Dict[str, int] = {nid: i for i, nid in enumerate(self._nodes)}
        node_ids = list(self._nodes.keys())

        for _ in range(20):  # Max iterations
            changed = False
            for nid in node_ids:
                neighbors = self._adjacency.get(nid, {})
                if not neighbors:
                    continue

                # Weighted vote for labels
                label_weights: Dict[int, float] = defaultdict(float)
                for neighbor, strength in neighbors.items():
                    label_weights[labels.get(neighbor, -1)] += strength

                if label_weights:
                    best_label = max(label_weights, key=label_weights.get)
                    if best_label != labels[nid]:
                        labels[nid] = best_label
                        changed = True

            if not changed:
                break

        # Group by label
        groups: Dict[int, List[str]] = defaultdict(list)
        for nid, label in labels.items():
            groups[label].append(nid)

        # Build communities
        communities = []
        for i, (label, members) in enumerate(
            sorted(groups.items(), key=lambda x: len(x[1]), reverse=True)
        ):
            if len(members) < min_community_size:
                continue

            # Calculate stats
            strengths = []
            programs: Set[str] = set()
            for m in members:
                for neighbor, s in self._adjacency.get(m, {}).items():
                    if neighbor in members:
                        strengths.append(s)
                node_progs = self._nodes[m].get("programs", [])
                if isinstance(node_progs, list):
                    programs.update(node_progs)
                elif isinstance(node_progs, str) and node_progs:
                    programs.add(node_progs)

            avg_str = sum(strengths) / len(strengths) if strengths else 0

            # Key member: highest-tier or most connections
            key = max(
                members,
                key=lambda m: (
                    (7 - self._nodes.get(m, {}).get("tier", 6)),
                    len(self._adjacency.get(m, {})),
                ),
            )

            # Auto-label from dominant program
            prog_list = list(programs)
            label_str = prog_list[0] if prog_list else f"Cluster {i + 1}"

            communities.append(Community(
                id=i,
                label=label_str,
                members=members,
                member_names=[self._nodes.get(m, {}).get("name", m) for m in members],
                size=len(members),
                avg_strength=round(avg_str, 1),
                programs=prog_list,
                key_member=self._nodes.get(key, {}).get("name", key),
            ))

        return communities

    async def find_bridge_contacts(
        self,
        communities: Optional[List[Community]] = None,
    ) -> List[BridgeContact]:
        """Find contacts connecting otherwise separate communities."""
        if communities is None:
            communities = await self.detect_communities()

        if not communities:
            return []

        # Build node → community membership
        node_communities: Dict[str, List[int]] = defaultdict(list)
        community_labels: Dict[int, str] = {}
        for comm in communities:
            community_labels[comm.id] = comm.label
            for member in comm.members:
                node_communities[member].append(comm.id)

        # Bridges are nodes connecting multiple communities
        bridges = []
        for nid, comms in node_communities.items():
            if len(comms) < 2:
                # Check if they connect TO nodes in other communities
                neighbor_comms: Set[int] = set()
                for neighbor in self._adjacency.get(nid, {}):
                    for c in node_communities.get(neighbor, []):
                        if c not in comms:
                            neighbor_comms.add(c)
                if not neighbor_comms:
                    continue
                all_comms = list(set(comms) | neighbor_comms)
            else:
                all_comms = comms

            connections_across = sum(
                1 for neighbor in self._adjacency.get(nid, {})
                if any(c not in comms for c in node_communities.get(neighbor, []))
            )

            score = min(100, len(all_comms) * 25 + connections_across * 10)

            bridges.append(BridgeContact(
                contact_id=nid,
                name=self._nodes.get(nid, {}).get("name", nid),
                communities=all_comms,
                community_labels=[community_labels.get(c, f"C{c}") for c in all_comms],
                bridge_score=round(score, 1),
                connections_across=connections_across,
            ))

        bridges.sort(key=lambda b: b.bridge_score, reverse=True)
        return bridges

    async def get_network_density(
        self, program: Optional[str] = None,
    ) -> DensityReport:
        """Calculate network density metrics."""
        if program:
            prog_lower = program.lower()
            nodes = {
                nid: info for nid, info in self._nodes.items()
                if prog_lower in str(info.get("programs", [])).lower()
            }
            adjacency = {
                nid: {k: v for k, v in self._adjacency.get(nid, {}).items() if k in nodes}
                for nid in nodes
            }
            scope = program
        else:
            nodes = self._nodes
            adjacency = self._adjacency
            scope = "global"

        n = len(nodes)
        if n < 2:
            return DensityReport(
                scope=scope, total_nodes=n, total_edges=0,
                density=0, avg_degree=0, avg_strength=0,
                clustering_coefficient=0, assessment="sparse",
            )

        # Count edges (undirected — avoid double-counting)
        edge_set: Set[tuple] = set()
        strengths = []
        for nid, neighbors in adjacency.items():
            for neighbor, s in neighbors.items():
                edge_key = tuple(sorted([nid, neighbor]))
                if edge_key not in edge_set:
                    edge_set.add(edge_key)
                    strengths.append(s)

        total_edges = len(edge_set)
        max_edges = n * (n - 1) / 2
        density = total_edges / max_edges if max_edges > 0 else 0
        avg_degree = (2 * total_edges) / n if n > 0 else 0
        avg_str = sum(strengths) / len(strengths) if strengths else 0

        # Clustering coefficient (fraction of possible triangles)
        triangles = 0
        possible_triangles = 0
        for nid in nodes:
            neighbors = set(adjacency.get(nid, {}).keys())
            if len(neighbors) < 2:
                continue
            possible_triangles += len(neighbors) * (len(neighbors) - 1) / 2
            for n1 in neighbors:
                for n2 in neighbors:
                    if n1 < n2 and n2 in adjacency.get(n1, {}):
                        triangles += 1
        cc = triangles / possible_triangles if possible_triangles > 0 else 0

        if density > 0.3:
            assessment = "dense"
        elif density > 0.1:
            assessment = "moderate"
        else:
            assessment = "sparse"

        return DensityReport(
            scope=scope,
            total_nodes=n,
            total_edges=total_edges,
            density=round(density, 4),
            avg_degree=round(avg_degree, 2),
            avg_strength=round(avg_str, 1),
            clustering_coefficient=round(cc, 4),
            assessment=assessment,
        )

    async def get_network_growth(
        self,
        days: int = 90,
        history: Optional[List[dict]] = None,
    ) -> GrowthReport:
        """Track network expansion or contraction."""
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=days)

        # Count new contacts
        new_contacts = 0
        new_relationships = 0
        lost_relationships = 0
        strongest_new: List[str] = []

        if history:
            for event in history:
                event_date = event.get("date", "")
                if isinstance(event_date, str):
                    try:
                        dt = datetime.fromisoformat(event_date.replace("Z", "+00:00"))
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=timezone.utc)
                    except Exception:
                        continue
                else:
                    continue

                if dt < cutoff:
                    continue

                etype = event.get("type", "")
                if etype == "new_contact":
                    new_contacts += 1
                elif etype == "new_relationship":
                    new_relationships += 1
                    name = event.get("name", event.get("contact", ""))
                    if name:
                        strongest_new.append(name)
                elif etype == "lost_relationship":
                    lost_relationships += 1
        else:
            # Estimate from node dates
            for nid, info in self._nodes.items():
                created = info.get("created_at") or info.get("added_date")
                if created:
                    try:
                        if isinstance(created, str):
                            dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                            if dt.tzinfo is None:
                                dt = dt.replace(tzinfo=timezone.utc)
                        elif isinstance(created, datetime):
                            dt = created if created.tzinfo else created.replace(tzinfo=timezone.utc)
                        else:
                            continue
                        if dt >= cutoff:
                            new_contacts += 1
                            strongest_new.append(info.get("name", nid))
                    except Exception:
                        pass

        net = new_contacts + new_relationships - lost_relationships
        total = len(self._nodes)
        rate = (net / total * 100) if total > 0 else 0

        if rate > 5:
            assessment = "expanding"
        elif rate < -5:
            assessment = "contracting"
        else:
            assessment = "stable"

        return GrowthReport(
            period_days=days,
            new_contacts=new_contacts,
            new_relationships=new_relationships,
            lost_relationships=lost_relationships,
            net_growth=net,
            growth_rate=round(rate, 2),
            strongest_new=strongest_new[:10],
            assessment=assessment,
        )


# =========================================
# SINGLETON
# =========================================

_analyzer: Optional[NetworkAnalyzer] = None


def get_network_analyzer() -> NetworkAnalyzer:
    global _analyzer
    if _analyzer is None:
        _analyzer = NetworkAnalyzer()
    return _analyzer
