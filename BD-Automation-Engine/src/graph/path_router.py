"""Phase 34A — Optimal Path Router

Dijkstra-based path routing through the contact graph:
  - Relationship strength as edge weight (inverted — stronger = shorter)
  - Multi-criteria: shortest, strongest, fastest (least decay)
  - Warm introduction chains: A knows B knows C knows target
  - Path scoring: geometric mean of segment strengths
  - Bottleneck detection: weakest link in the chain
  - Missing link identification for target programs
"""

import heapq
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


# =========================================
# DATA CLASSES
# =========================================

@dataclass
class PathOption:
    path: List[str]
    path_names: List[str]
    total_strength: float
    weakest_link: float
    weakest_link_segment: str
    hops: int
    strategy: str  # "strongest", "shortest", "warm_intro"
    introduction_script: str = ""


@dataclass
class WarmIntroChain:
    chain: List[dict]  # [{contact, name, relationship_to_next, strength}]
    total_strength: float
    hops: int
    feasibility: str  # "strong", "moderate", "weak"
    suggested_approach: str = ""


@dataclass
class MissingLink:
    target_program: str
    gap_type: str  # "no_contact", "weak_contact", "single_thread"
    description: str
    recommended_action: str
    priority: str  # "critical", "high", "medium", "low"


@dataclass
class NetworkGap:
    program: str
    contact_count: int
    avg_strength: float
    has_decision_maker: bool
    gap_severity: str  # "critical", "significant", "minor"
    recommendations: List[str] = field(default_factory=list)


class OptimalPathRouter:
    """Find optimal paths through the contact graph."""

    def __init__(self, graph_client: Any = None):
        self._graph = graph_client
        self._adjacency: Dict[str, Dict[str, float]] = {}
        self._node_info: Dict[str, dict] = {}

    def set_graph_data(
        self,
        nodes: List[dict],
        edges: List[dict],
    ) -> None:
        """Load graph data for path computations."""
        self._node_info = {n.get("id", str(i)): n for i, n in enumerate(nodes)}
        self._adjacency = {nid: {} for nid in self._node_info}

        for edge in edges:
            src = edge.get("source", edge.get("from", ""))
            tgt = edge.get("target", edge.get("to", ""))
            strength = edge.get("strength", edge.get("weight", 50.0))

            if src in self._adjacency:
                self._adjacency[src][tgt] = strength
            if tgt in self._adjacency:
                self._adjacency.setdefault(tgt, {})[src] = strength

    async def find_optimal_path(
        self, from_contact: str, to_contact: str, max_hops: int = 5,
    ) -> List[PathOption]:
        """Find top paths from source to target contact."""
        if not self._adjacency:
            return []

        paths = []

        # Strategy 1: Strongest path (maximize minimum edge)
        strongest = self._dijkstra_strongest(from_contact, to_contact, max_hops)
        if strongest:
            paths.append(self._build_path_option(strongest, "strongest"))

        # Strategy 2: Shortest path (fewest hops)
        shortest = self._bfs_shortest(from_contact, to_contact, max_hops)
        if shortest and shortest != strongest:
            paths.append(self._build_path_option(shortest, "shortest"))

        # Strategy 3: All paths scored by total strength
        all_paths = self._find_k_paths(from_contact, to_contact, max_hops, k=5)
        for p in all_paths:
            if p not in [strongest, shortest]:
                paths.append(self._build_path_option(p, "alternative"))

        # Remove duplicates and sort by strength
        seen = set()
        unique = []
        for p in paths:
            key = tuple(p.path)
            if key not in seen:
                seen.add(key)
                unique.append(p)

        unique.sort(key=lambda p: p.total_strength, reverse=True)
        return unique[:5]

    async def find_warm_intro_chain(
        self, to_contact: str, our_contacts: Optional[List[str]] = None,
    ) -> List[WarmIntroChain]:
        """Find warm introduction chains to a target."""
        if not self._adjacency:
            return []

        # "Our contacts" = Tier 1-2 contacts or specified list
        if our_contacts is None:
            our_contacts = [
                nid for nid, info in self._node_info.items()
                if info.get("tier", 6) <= 2 and info.get("is_ours", False)
            ]
            if not our_contacts:
                our_contacts = list(self._adjacency.keys())[:5]

        chains = []
        for start in our_contacts:
            path = self._bfs_shortest(start, to_contact, max_hops=4)
            if path and len(path) > 1:
                chain_items = []
                strengths = []
                for i in range(len(path) - 1):
                    a, b = path[i], path[i + 1]
                    s = self._adjacency.get(a, {}).get(b, 0)
                    strengths.append(s)
                    chain_items.append({
                        "contact": a,
                        "name": self._node_info.get(a, {}).get("name", a),
                        "relationship_to_next": self._node_info.get(b, {}).get("name", b),
                        "strength": s,
                    })
                # Add final target
                chain_items.append({
                    "contact": path[-1],
                    "name": self._node_info.get(path[-1], {}).get("name", path[-1]),
                    "relationship_to_next": "",
                    "strength": 0,
                })

                avg_strength = sum(strengths) / len(strengths) if strengths else 0
                feasibility = "strong" if avg_strength >= 70 else "moderate" if avg_strength >= 40 else "weak"

                chains.append(WarmIntroChain(
                    chain=chain_items,
                    total_strength=round(avg_strength, 1),
                    hops=len(path) - 1,
                    feasibility=feasibility,
                    suggested_approach=self._suggest_approach(chain_items, feasibility),
                ))

        chains.sort(key=lambda c: c.total_strength, reverse=True)
        return chains[:5]

    async def identify_missing_links(
        self, target_program: str,
    ) -> List[MissingLink]:
        """Identify missing connections for a target program."""
        if not self._node_info:
            return []

        program_lower = target_program.lower()

        # Find contacts on this program
        program_contacts = [
            nid for nid, info in self._node_info.items()
            if program_lower in str(info.get("programs", [])).lower()
            or program_lower in str(info.get("program", "")).lower()
        ]

        links = []

        if not program_contacts:
            links.append(MissingLink(
                target_program=target_program,
                gap_type="no_contact",
                description=f"No contacts identified on {target_program}",
                recommended_action="Research key personnel and start outreach via LinkedIn or conferences",
                priority="critical",
            ))
            return links

        # Check for decision makers
        decision_makers = [
            c for c in program_contacts
            if self._node_info[c].get("tier", 6) <= 2
        ]
        if not decision_makers:
            links.append(MissingLink(
                target_program=target_program,
                gap_type="weak_contact",
                description=f"No Tier 1-2 decision makers on {target_program}",
                recommended_action="Leverage existing contacts to get introductions to program leadership",
                priority="high",
            ))

        # Check for single-threaded risk
        if len(program_contacts) == 1:
            links.append(MissingLink(
                target_program=target_program,
                gap_type="single_thread",
                description=f"Only 1 contact on {target_program} — single-threaded risk",
                recommended_action="Develop 2-3 additional relationships on this program for resilience",
                priority="high",
            ))

        # Check connection strength
        for cid in program_contacts:
            neighbors = self._adjacency.get(cid, {})
            our_strength = max(neighbors.values()) if neighbors else 0
            if our_strength < 30 and our_strength > 0:
                links.append(MissingLink(
                    target_program=target_program,
                    gap_type="weak_contact",
                    description=f"Weak relationship (score {our_strength:.0f}) with {self._node_info[cid].get('name', cid)}",
                    recommended_action="Increase touchpoints: schedule a call, offer value, attend same events",
                    priority="medium",
                ))

        return links

    async def get_network_gaps(
        self, programs: Optional[List[str]] = None,
    ) -> List[NetworkGap]:
        """Find programs where we lack connections."""
        if not self._node_info:
            return []

        # Get all programs from nodes
        if programs is None:
            all_progs: Set[str] = set()
            for info in self._node_info.values():
                progs = info.get("programs", [])
                if isinstance(progs, list):
                    all_progs.update(progs)
                elif isinstance(progs, str) and progs:
                    all_progs.add(progs)
            programs = list(all_progs)

        gaps = []
        for program in programs:
            prog_lower = program.lower()
            contacts = [
                nid for nid, info in self._node_info.items()
                if prog_lower in str(info.get("programs", [])).lower()
            ]

            # Calculate avg strength
            strengths = []
            for cid in contacts:
                for strength in self._adjacency.get(cid, {}).values():
                    strengths.append(strength)
            avg_str = sum(strengths) / len(strengths) if strengths else 0

            has_dm = any(
                self._node_info[c].get("tier", 6) <= 2
                for c in contacts
            )

            if not contacts:
                severity = "critical"
            elif not has_dm:
                severity = "significant"
            elif avg_str < 40:
                severity = "significant"
            elif len(contacts) < 3:
                severity = "minor"
            else:
                continue  # No gap

            recs = []
            if severity == "critical":
                recs.append(f"No contacts on {program} — prioritize initial outreach")
            if not has_dm:
                recs.append("No decision maker access — seek introductions to Tier 1-2 contacts")
            if avg_str < 40:
                recs.append("Weak relationships — increase interaction frequency and quality")
            if len(contacts) < 3:
                recs.append("Limited coverage — develop additional contacts for resilience")

            gaps.append(NetworkGap(
                program=program,
                contact_count=len(contacts),
                avg_strength=round(avg_str, 1),
                has_decision_maker=has_dm,
                gap_severity=severity,
                recommendations=recs,
            ))

        gaps.sort(key=lambda g: {"critical": 0, "significant": 1, "minor": 2}.get(g.gap_severity, 3))
        return gaps

    # =========================================
    # PATH ALGORITHMS
    # =========================================

    def _dijkstra_strongest(
        self, start: str, end: str, max_hops: int,
    ) -> Optional[List[str]]:
        """Modified Dijkstra: maximize minimum edge weight."""
        if start not in self._adjacency or end not in self._adjacency:
            return None

        # Priority queue: (-min_strength, node, path)
        heap: List[Tuple[float, str, List[str]]] = [(-100.0, start, [start])]
        visited: Set[str] = set()

        while heap:
            neg_strength, node, path = heapq.heappop(heap)

            if node == end and len(path) > 1:
                return path

            if node in visited or len(path) - 1 >= max_hops:
                continue
            visited.add(node)

            for neighbor, edge_strength in self._adjacency.get(node, {}).items():
                if neighbor not in visited:
                    min_str = min(-neg_strength, edge_strength)
                    heapq.heappush(heap, (-min_str, neighbor, path + [neighbor]))

        return None

    def _bfs_shortest(
        self, start: str, end: str, max_hops: int,
    ) -> Optional[List[str]]:
        """BFS for shortest path."""
        if start not in self._adjacency or end not in self._adjacency:
            return None

        queue: List[List[str]] = [[start]]
        visited: Set[str] = {start}

        while queue:
            path = queue.pop(0)
            node = path[-1]

            if node == end and len(path) > 1:
                return path

            if len(path) - 1 >= max_hops:
                continue

            for neighbor in self._adjacency.get(node, {}):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(path + [neighbor])

        return None

    def _find_k_paths(
        self, start: str, end: str, max_hops: int, k: int = 5,
    ) -> List[List[str]]:
        """Find k paths using BFS without full visited filtering."""
        if start not in self._adjacency:
            return []

        paths = []
        queue: List[List[str]] = [[start]]

        while queue and len(paths) < k * 3:
            path = queue.pop(0)
            node = path[-1]

            if node == end and len(path) > 1:
                paths.append(path)
                if len(paths) >= k:
                    break
                continue

            if len(path) - 1 >= max_hops:
                continue

            for neighbor in self._adjacency.get(node, {}):
                if neighbor not in path:
                    queue.append(path + [neighbor])

        return paths[:k]

    # =========================================
    # HELPERS
    # =========================================

    def _build_path_option(self, path: List[str], strategy: str) -> PathOption:
        """Build a PathOption from a raw path."""
        strengths = []
        for i in range(len(path) - 1):
            s = self._adjacency.get(path[i], {}).get(path[i + 1], 0)
            strengths.append(s)

        weakest = min(strengths) if strengths else 0
        weakest_idx = strengths.index(weakest) if strengths else 0

        # Geometric mean
        if strengths:
            product = 1.0
            for s in strengths:
                product *= max(s, 0.01) / 100.0
            total = (product ** (1.0 / len(strengths))) * 100
        else:
            total = 0

        weakest_seg = ""
        if strengths and len(path) > weakest_idx + 1:
            a = self._node_info.get(path[weakest_idx], {}).get("name", path[weakest_idx])
            b = self._node_info.get(path[weakest_idx + 1], {}).get("name", path[weakest_idx + 1])
            weakest_seg = f"{a} → {b}"

        return PathOption(
            path=path,
            path_names=[self._node_info.get(p, {}).get("name", p) for p in path],
            total_strength=round(total, 1),
            weakest_link=round(weakest, 1),
            weakest_link_segment=weakest_seg,
            hops=len(path) - 1,
            strategy=strategy,
        )

    def _suggest_approach(self, chain: List[dict], feasibility: str) -> str:
        if feasibility == "strong":
            return "Direct ask: request a warm introduction from your contact"
        elif feasibility == "moderate":
            return "Build rapport first, then ask for a casual introduction"
        return "Start with LinkedIn engagement, then request a conversation"


# =========================================
# SINGLETON
# =========================================

_router: Optional[OptimalPathRouter] = None


def get_path_router() -> OptimalPathRouter:
    global _router
    if _router is None:
        _router = OptimalPathRouter()
    return _router
