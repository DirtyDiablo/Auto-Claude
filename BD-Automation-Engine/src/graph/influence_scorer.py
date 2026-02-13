"""Phase 34A — BD PageRank Influence Scorer

Custom PageRank variant optimized for BD influence networks:
  - Node weight: contact tier level (Tier 1 = 10x, Tier 6 = 1x)
  - Edge weight: relationship strength score
  - Damping factor: 0.85 (tuned for BD networks)
  - Program-scoped: influence within a specific program vs overall
  - Temporal: influence based on recent interactions vs all-time
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# =========================================
# DATA CLASSES
# =========================================

@dataclass
class InfluenceScore:
    contact_id: str
    name: str
    score: float  # 0-100 normalized
    raw_score: float
    tier: int
    programs: List[str] = field(default_factory=list)
    connections: int = 0
    rank: int = 0


@dataclass
class InfluenceTrajectory:
    contact_id: str
    current_score: float
    scores_over_time: List[Dict[str, Any]] = field(default_factory=list)
    trend: str = "stable"  # increasing, decreasing, stable
    change_pct: float = 0.0


@dataclass
class KeyConnector:
    contact_id: str
    name: str
    influence_score: float
    programs_bridged: List[str] = field(default_factory=list)
    communities_linked: int = 0
    betweenness: float = 0.0


# =========================================
# TIER WEIGHTS
# =========================================

TIER_WEIGHTS = {
    1: 10.0,  # C-suite / VP
    2: 7.0,   # Director / Senior PM
    3: 5.0,   # Manager / PM
    4: 3.0,   # Senior Individual
    5: 2.0,   # Individual
    6: 1.0,   # Entry / Unknown
}

DAMPING_FACTOR = 0.85
MAX_ITERATIONS = 50
CONVERGENCE_THRESHOLD = 1e-6


class BDPageRank:
    """Custom PageRank for BD influence scoring."""

    def __init__(self, graph_client: Any = None):
        self._graph = graph_client
        self._scores: Dict[str, float] = {}
        self._history: List[Dict[str, Dict[str, float]]] = []

    def set_graph_client(self, client: Any) -> None:
        self._graph = client

    async def compute_influence_scores(
        self,
        nodes: Optional[List[dict]] = None,
        edges: Optional[List[dict]] = None,
        scope: str = "global",
    ) -> List[InfluenceScore]:
        """Compute PageRank-style influence scores."""
        nodes = nodes or await self._fetch_nodes(scope)
        edges = edges or await self._fetch_edges(scope)

        if not nodes:
            return []

        # Build graph structures
        node_map = {n.get("id", str(i)): n for i, n in enumerate(nodes)}
        node_ids = list(node_map.keys())
        n = len(node_ids)

        if n == 0:
            return []

        # Build adjacency with weights
        outgoing: Dict[str, Dict[str, float]] = {nid: {} for nid in node_ids}
        incoming: Dict[str, Dict[str, float]] = {nid: {} for nid in node_ids}

        for edge in edges:
            src = edge.get("source", edge.get("from", ""))
            tgt = edge.get("target", edge.get("to", ""))
            weight = edge.get("weight", edge.get("strength", 50.0)) / 100.0

            if src in outgoing and tgt in incoming:
                outgoing[src][tgt] = weight
                incoming[tgt][src] = weight

        # Tier-weighted personalization vector
        tier_total = sum(
            TIER_WEIGHTS.get(node_map[nid].get("tier", 6), 1.0)
            for nid in node_ids
        )
        personalization = {
            nid: TIER_WEIGHTS.get(node_map[nid].get("tier", 6), 1.0) / tier_total
            for nid in node_ids
        }

        # Initialize scores
        scores = {nid: 1.0 / n for nid in node_ids}

        # Iterate until convergence
        for iteration in range(MAX_ITERATIONS):
            new_scores = {}
            for nid in node_ids:
                # Sum of weighted incoming contributions
                incoming_sum = 0.0
                for src, weight in incoming[nid].items():
                    out_total = sum(outgoing[src].values()) or 1.0
                    incoming_sum += scores[src] * weight / out_total

                new_scores[nid] = (
                    (1 - DAMPING_FACTOR) * personalization[nid]
                    + DAMPING_FACTOR * incoming_sum
                )

            # Check convergence
            diff = sum(abs(new_scores[nid] - scores[nid]) for nid in node_ids)
            scores = new_scores

            if diff < CONVERGENCE_THRESHOLD:
                logger.debug(f"PageRank converged in {iteration + 1} iterations")
                break

        # Apply tier authority to raw PageRank scores
        for nid in node_ids:
            tier = node_map[nid].get("tier", 6)
            tier_w = TIER_WEIGHTS.get(tier, 1.0)
            scores[nid] *= tier_w

        # Normalize to 0-100
        max_score = max(scores.values()) if scores else 1.0
        if max_score == 0:
            max_score = 1.0

        self._scores = scores

        # Save history snapshot
        self._history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "scores": dict(scores),
        })

        results = []
        for nid in node_ids:
            node = node_map[nid]
            normalized = (scores[nid] / max_score) * 100
            results.append(InfluenceScore(
                contact_id=nid,
                name=node.get("name", nid),
                score=round(normalized, 2),
                raw_score=round(scores[nid], 6),
                tier=node.get("tier", 6),
                programs=node.get("programs", []),
                connections=len(outgoing.get(nid, {})) + len(incoming.get(nid, {})),
            ))

        results.sort(key=lambda r: r.score, reverse=True)
        for i, r in enumerate(results):
            r.rank = i + 1

        return results

    async def compute_program_influence(
        self,
        program: str,
        nodes: Optional[List[dict]] = None,
        edges: Optional[List[dict]] = None,
    ) -> List[InfluenceScore]:
        """Compute influence scoped to a specific program."""
        nodes = nodes or await self._fetch_nodes("global")
        edges = edges or await self._fetch_edges("global")

        # Filter to program participants
        program_lower = program.lower()
        program_nodes = [
            n for n in nodes
            if program_lower in str(n.get("programs", [])).lower()
            or program_lower in str(n.get("program", "")).lower()
        ]

        if not program_nodes:
            return []

        program_ids = {n.get("id", str(i)) for i, n in enumerate(program_nodes)}
        program_edges = [
            e for e in edges
            if (e.get("source", e.get("from", "")) in program_ids
                or e.get("target", e.get("to", "")) in program_ids)
        ]

        return await self.compute_influence_scores(program_nodes, program_edges, scope=program)

    async def get_key_connectors(
        self,
        nodes: Optional[List[dict]] = None,
        edges: Optional[List[dict]] = None,
        top_n: int = 10,
    ) -> List[KeyConnector]:
        """Find contacts who bridge multiple programs/communities."""
        nodes = nodes or await self._fetch_nodes("global")
        edges = edges or await self._fetch_edges("global")

        if not nodes or not edges:
            return []

        node_map = {n.get("id", str(i)): n for i, n in enumerate(nodes)}

        # Count unique programs each node connects
        node_programs: Dict[str, set] = {}
        for edge in edges:
            src = edge.get("source", edge.get("from", ""))
            tgt = edge.get("target", edge.get("to", ""))
            for nid in [src, tgt]:
                if nid in node_map:
                    progs = node_map[nid].get("programs", [])
                    node_programs.setdefault(nid, set()).update(
                        progs if isinstance(progs, list) else [progs]
                    )

        # Count edge connections
        connection_count: Dict[str, int] = {}
        for edge in edges:
            src = edge.get("source", edge.get("from", ""))
            tgt = edge.get("target", edge.get("to", ""))
            connection_count[src] = connection_count.get(src, 0) + 1
            connection_count[tgt] = connection_count.get(tgt, 0) + 1

        # Compute betweenness-like score
        connectors = []
        for nid, node in node_map.items():
            programs = list(node_programs.get(nid, set()))
            conns = connection_count.get(nid, 0)

            if len(programs) < 2 and conns < 3:
                continue

            influence = self._scores.get(nid, 0)
            betweenness = len(programs) * conns  # Simplified betweenness

            connectors.append(KeyConnector(
                contact_id=nid,
                name=node.get("name", nid),
                influence_score=round(influence * 100, 2) if influence else 0,
                programs_bridged=programs,
                communities_linked=len(programs),
                betweenness=round(betweenness, 2),
            ))

        connectors.sort(key=lambda c: c.betweenness, reverse=True)
        return connectors[:top_n]

    async def get_influence_trajectory(
        self, contact_id: str, days: int = 90,
    ) -> InfluenceTrajectory:
        """Track how a contact's influence has changed over time."""
        scores_over_time = []
        for snapshot in self._history:
            score = snapshot.get("scores", {}).get(contact_id, 0)
            scores_over_time.append({
                "timestamp": snapshot.get("timestamp", ""),
                "score": score,
            })

        current = self._scores.get(contact_id, 0)

        # Determine trend
        if len(scores_over_time) >= 2:
            first = scores_over_time[0]["score"]
            last = scores_over_time[-1]["score"]
            if first > 0:
                change_pct = ((last - first) / first) * 100
            else:
                change_pct = 0
            trend = "increasing" if change_pct > 5 else "decreasing" if change_pct < -5 else "stable"
        else:
            change_pct = 0
            trend = "stable"

        return InfluenceTrajectory(
            contact_id=contact_id,
            current_score=round(current, 6),
            scores_over_time=scores_over_time,
            trend=trend,
            change_pct=round(change_pct, 2),
        )

    # =========================================
    # GRAPH DATA FETCHING
    # =========================================

    async def _fetch_nodes(self, scope: str) -> List[dict]:
        if self._graph and hasattr(self._graph, "get_nodes"):
            return await self._graph.get_nodes(scope)
        return []

    async def _fetch_edges(self, scope: str) -> List[dict]:
        if self._graph and hasattr(self._graph, "get_edges"):
            return await self._graph.get_edges(scope)
        return []


# =========================================
# SINGLETON
# =========================================

_scorer: Optional[BDPageRank] = None


def get_influence_scorer() -> BDPageRank:
    global _scorer
    if _scorer is None:
        _scorer = BDPageRank()
    return _scorer
