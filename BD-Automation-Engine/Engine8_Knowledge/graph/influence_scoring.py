"""
Influence Scoring - PageRank, Betweenness, Eigenvector centrality for BD entities.

Computes composite influence scores for contacts, contractors, and programs
using graph centrality algorithms. Identifies hidden gems (high centrality
but low tier/priority) and key bridge nodes.
"""

import os
import sys
import math
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from Engine8_Knowledge.graph.bd_knowledge_graph import (
    BDKnowledgeGraph,
    get_knowledge_graph,
)

logger = logging.getLogger(__name__)


@dataclass
class InfluenceScore:
    """Composite influence score for an entity."""

    entity_id: str
    entity_name: str
    entity_type: str
    pagerank: float = 0.0
    betweenness: float = 0.0
    eigenvector: float = 0.0
    degree: int = 0
    composite: float = 0.0
    rank: int = 0
    is_hidden_gem: bool = False
    properties: Dict = field(default_factory=dict)


class InfluenceScorer:
    """
    Computes influence scores using graph centrality algorithms.

    Composite score formula:
      PageRank (0.35) + Betweenness (0.25) + Eigenvector (0.25) + Degree-norm (0.15)
    """

    PAGERANK_WEIGHT = 0.35
    BETWEENNESS_WEIGHT = 0.25
    EIGENVECTOR_WEIGHT = 0.25
    DEGREE_WEIGHT = 0.15

    def __init__(self, graph: Optional[BDKnowledgeGraph] = None):
        self.graph = graph or get_knowledge_graph()
        self._adjacency: Dict[str, set] = {}
        self._scores: Dict[str, InfluenceScore] = {}
        self._computed = False

    def _build_adjacency(self):
        """Build undirected adjacency list from graph relationships."""
        self._adjacency.clear()
        cursor = self.graph.conn.execute(
            "SELECT from_entity_id, to_entity_id FROM relationships"
        )
        for from_id, to_id in cursor:
            self._adjacency.setdefault(from_id, set()).add(to_id)
            self._adjacency.setdefault(to_id, set()).add(from_id)

    def compute_pagerank(
        self, damping: float = 0.85, iterations: int = 50, tol: float = 1e-6
    ) -> Dict[str, float]:
        """
        Compute PageRank scores using power iteration.

        Args:
            damping: Damping factor (default 0.85)
            iterations: Max iterations
            tol: Convergence tolerance

        Returns:
            Dict mapping entity_id to PageRank score
        """
        nodes = list(self._adjacency.keys())
        n = len(nodes)
        if n == 0:
            return {}

        # Initialize uniform
        pr = {nid: 1.0 / n for nid in nodes}
        base = (1.0 - damping) / n

        for _ in range(iterations):
            new_pr = {}
            diff = 0.0

            for nid in nodes:
                rank_sum = 0.0
                for neighbor in self._adjacency.get(nid, set()):
                    out_degree = len(self._adjacency.get(neighbor, set()))
                    if out_degree > 0:
                        rank_sum += pr[neighbor] / out_degree

                new_pr[nid] = base + damping * rank_sum
                diff += abs(new_pr[nid] - pr[nid])

            pr = new_pr
            if diff < tol:
                break

        return pr

    def compute_betweenness(self, sample_size: int = 200) -> Dict[str, float]:
        """
        Compute approximate betweenness centrality using Brandes' algorithm
        with sampling for large graphs.

        Args:
            sample_size: Number of source nodes to sample

        Returns:
            Dict mapping entity_id to betweenness centrality
        """
        from collections import deque
        import random

        nodes = list(self._adjacency.keys())
        n = len(nodes)
        if n == 0:
            return {}

        betweenness = {nid: 0.0 for nid in nodes}

        # Sample source nodes for large graphs
        sources = random.sample(nodes, min(sample_size, n))

        for s in sources:
            # BFS from s
            stack = []
            predecessors: Dict[str, List[str]] = {nid: [] for nid in nodes}
            sigma = {nid: 0.0 for nid in nodes}
            sigma[s] = 1.0
            dist = {nid: -1 for nid in nodes}
            dist[s] = 0

            queue = deque([s])

            while queue:
                v = queue.popleft()
                stack.append(v)
                for w in self._adjacency.get(v, set()):
                    # First time visiting w
                    if dist[w] < 0:
                        dist[w] = dist[v] + 1
                        queue.append(w)
                    # Shortest path to w via v
                    if dist[w] == dist[v] + 1:
                        sigma[w] += sigma[v]
                        predecessors[w].append(v)

            # Back-propagation
            delta = {nid: 0.0 for nid in nodes}
            while stack:
                w = stack.pop()
                for v in predecessors[w]:
                    if sigma[w] > 0:
                        delta[v] += (sigma[v] / sigma[w]) * (1.0 + delta[w])
                if w != s:
                    betweenness[w] += delta[w]

        # Normalize
        scale = 1.0 / (len(sources) * max(1, n - 1) * max(1, n - 2))
        for nid in betweenness:
            betweenness[nid] *= scale

        return betweenness

    def compute_eigenvector(
        self, iterations: int = 50, tol: float = 1e-6
    ) -> Dict[str, float]:
        """
        Compute eigenvector centrality using power iteration.

        Returns:
            Dict mapping entity_id to eigenvector centrality
        """
        nodes = list(self._adjacency.keys())
        n = len(nodes)
        if n == 0:
            return {}

        # Initialize uniform
        ev = {nid: 1.0 / math.sqrt(n) for nid in nodes}

        for _ in range(iterations):
            new_ev = {}
            for nid in nodes:
                new_ev[nid] = sum(
                    ev.get(nb, 0.0) for nb in self._adjacency.get(nid, set())
                )

            # Normalize
            norm = math.sqrt(sum(v * v for v in new_ev.values()))
            if norm > 0:
                for nid in new_ev:
                    new_ev[nid] /= norm

            # Check convergence
            diff = sum(abs(new_ev[nid] - ev[nid]) for nid in nodes)
            ev = new_ev
            if diff < tol:
                break

        return ev

    def compute_all(self) -> Dict[str, InfluenceScore]:
        """
        Compute all centrality metrics and composite influence scores.
        Results are cached.
        """
        if self._computed and self._scores:
            return self._scores

        self._build_adjacency()

        logger.info("Computing PageRank...")
        pagerank = self.compute_pagerank()

        logger.info("Computing betweenness centrality...")
        betweenness = self.compute_betweenness()

        logger.info("Computing eigenvector centrality...")
        eigenvector = self.compute_eigenvector()

        # Normalize each metric to [0, 1]
        def normalize(scores: Dict[str, float]) -> Dict[str, float]:
            if not scores:
                return scores
            max_val = max(scores.values())
            min_val = min(scores.values())
            rng = max_val - min_val
            if rng == 0:
                return {k: 0.5 for k in scores}
            return {k: (v - min_val) / rng for k, v in scores.items()}

        pr_norm = normalize(pagerank)
        bt_norm = normalize(betweenness)
        ev_norm = normalize(eigenvector)

        # Compute degree
        degrees = {nid: len(neighbors) for nid, neighbors in self._adjacency.items()}
        max_degree = max(degrees.values()) if degrees else 1
        deg_norm = {nid: d / max_degree for nid, d in degrees.items()}

        # Build influence scores
        self._scores.clear()
        for eid in self._adjacency:
            entity = self.graph.get_entity(eid)
            if not entity:
                continue

            pr = pr_norm.get(eid, 0.0)
            bt = bt_norm.get(eid, 0.0)
            ev = ev_norm.get(eid, 0.0)
            dg = deg_norm.get(eid, 0.0)

            composite = (
                self.PAGERANK_WEIGHT * pr
                + self.BETWEENNESS_WEIGHT * bt
                + self.EIGENVECTOR_WEIGHT * ev
                + self.DEGREE_WEIGHT * dg
            )

            # Detect hidden gems: high influence but low tier/priority
            is_hidden_gem = False
            if entity.type == "Contact":
                tier = entity.properties.get("tier", "")
                try:
                    tier_num = int(tier) if tier else 0
                except (ValueError, TypeError):
                    tier_num = 0
                # High composite but low tier (4+) = hidden gem
                if composite > 0.5 and tier_num >= 4:
                    is_hidden_gem = True

            self._scores[eid] = InfluenceScore(
                entity_id=eid,
                entity_name=entity.name,
                entity_type=entity.type,
                pagerank=round(pr, 4),
                betweenness=round(bt, 4),
                eigenvector=round(ev, 4),
                degree=degrees.get(eid, 0),
                composite=round(composite, 4),
                is_hidden_gem=is_hidden_gem,
                properties=entity.properties,
            )

        # Assign ranks
        sorted_scores = sorted(
            self._scores.values(), key=lambda s: s.composite, reverse=True
        )
        for i, score in enumerate(sorted_scores):
            score.rank = i + 1

        self._computed = True
        logger.info(f"Computed influence scores for {len(self._scores)} entities")

        return self._scores

    def get_leaderboard(
        self, entity_type: Optional[str] = None, limit: int = 25
    ) -> List[Dict]:
        """
        Get ranked leaderboard of entities by composite influence score.

        Args:
            entity_type: Filter by entity type (Contact, Contractor, Program)
            limit: Max results

        Returns:
            List of dicts with score details
        """
        scores = self.compute_all()

        filtered = sorted(
            (
                s
                for s in scores.values()
                if not entity_type or s.entity_type == entity_type
            ),
            key=lambda s: s.composite,
            reverse=True,
        )[:limit]

        return [
            {
                "entity_id": s.entity_id,
                "name": s.entity_name,
                "type": s.entity_type,
                "pagerank": s.pagerank,
                "betweenness": s.betweenness,
                "eigenvector": s.eigenvector,
                "degree": s.degree,
                "composite": s.composite,
                "rank": s.rank,
                "is_hidden_gem": s.is_hidden_gem,
                "properties": s.properties,
            }
            for s in filtered
        ]

    def get_hidden_gems(self, limit: int = 20) -> List[Dict]:
        """Get entities with high centrality but low official tier/priority."""
        scores = self.compute_all()

        gems = sorted(
            (s for s in scores.values() if s.is_hidden_gem),
            key=lambda s: s.composite,
            reverse=True,
        )[:limit]

        return [
            {
                "entity_id": s.entity_id,
                "name": s.entity_name,
                "type": s.entity_type,
                "composite": s.composite,
                "pagerank": s.pagerank,
                "betweenness": s.betweenness,
                "degree": s.degree,
                "tier": s.properties.get("tier", ""),
                "company": s.properties.get("company", ""),
                "title": s.properties.get("title", ""),
            }
            for s in gems
        ]

    def get_bridges(self, limit: int = 20) -> List[Dict]:
        """
        Get bridge nodes - entities with high betweenness centrality
        that connect otherwise disconnected clusters.
        """
        scores = self.compute_all()

        bridges = sorted(
            scores.values(),
            key=lambda s: s.betweenness,
            reverse=True,
        )[:limit]

        return [
            {
                "entity_id": s.entity_id,
                "name": s.entity_name,
                "type": s.entity_type,
                "betweenness": s.betweenness,
                "degree": s.degree,
                "composite": s.composite,
                "properties": s.properties,
            }
            for s in bridges
        ]

    def get_entity_influence(self, entity_name: str) -> Optional[Dict]:
        """Get influence details for a specific entity."""
        scores = self.compute_all()

        entity = self.graph.find_entity(entity_name)
        if not entity or entity.id not in scores:
            return None

        s = scores[entity.id]
        return {
            "entity_id": s.entity_id,
            "name": s.entity_name,
            "type": s.entity_type,
            "pagerank": s.pagerank,
            "betweenness": s.betweenness,
            "eigenvector": s.eigenvector,
            "degree": s.degree,
            "composite": s.composite,
            "rank": s.rank,
            "is_hidden_gem": s.is_hidden_gem,
            "total_entities": len(scores),
            "percentile": round((1 - s.rank / len(scores)) * 100, 1) if scores else 0,
        }

    def invalidate(self):
        """Force recomputation on next call."""
        self._computed = False
        self._scores.clear()


# Singleton
_scorer_instance: Optional[InfluenceScorer] = None


def get_influence_scorer() -> InfluenceScorer:
    """Get influence scorer singleton."""
    global _scorer_instance
    if _scorer_instance is None:
        _scorer_instance = InfluenceScorer()
    return _scorer_instance
