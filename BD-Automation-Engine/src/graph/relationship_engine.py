"""Phase 34A — Relationship Strength Engine

Scores every relationship 0-100 based on 6 factors:
  1. Interaction recency   (25%) — exponential decay, halves every 30 days
  2. Interaction frequency  (20%) — normalized count over 90-day window
  3. Interaction quality    (20%) — meetings > calls > emails > LinkedIn
  4. Reciprocity           (15%) — two-way vs one-way communication
  5. Depth                 (10%) — shared programs, shared contacts, referrals
  6. Outcome history       (10%) — past placements, successful introductions
"""

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# =========================================
# DATA CLASSES
# =========================================

@dataclass
class RelationshipScore:
    contact_a: str
    contact_b: str
    total_score: float  # 0-100
    recency_score: float
    frequency_score: float
    quality_score: float
    reciprocity_score: float
    depth_score: float
    outcome_score: float
    factors: Dict[str, Any] = field(default_factory=dict)
    scored_at: str = ""


@dataclass
class DecayingRelationship:
    contact_a: str
    contact_b: str
    current_score: float
    days_since_contact: int
    projected_score_7d: float
    risk_level: str  # "critical", "warning", "watch"
    recommended_action: str = ""


@dataclass
class PathSegment:
    from_contact: str
    to_contact: str
    strength: float
    relationship_type: str = ""


@dataclass
class RankedPath:
    path: List[str]
    segments: List[PathSegment]
    total_strength: float
    weakest_link: float
    hops: int


# =========================================
# DIMENSION WEIGHTS
# =========================================

DIMENSION_WEIGHTS = {
    "recency": 0.25,
    "frequency": 0.20,
    "quality": 0.20,
    "reciprocity": 0.15,
    "depth": 0.10,
    "outcome": 0.10,
}

# Interaction quality scores
INTERACTION_QUALITY = {
    "meeting": 1.0,
    "in_person": 1.0,
    "video_call": 0.85,
    "call": 0.7,
    "phone": 0.7,
    "email": 0.4,
    "linkedin": 0.25,
    "message": 0.3,
    "referral": 0.9,
    "introduction": 0.85,
}

# Recency half-life in days
RECENCY_HALF_LIFE = 30


class RelationshipStrengthModel:
    """Score every relationship 0-100 based on 6 factors."""

    def __init__(self, graph_client: Any = None):
        self._graph = graph_client
        self._scores_cache: Dict[str, RelationshipScore] = {}

    def set_graph_client(self, client: Any) -> None:
        self._graph = client

    async def score_relationship(
        self,
        contact_a: str,
        contact_b: str,
        interactions: Optional[List[dict]] = None,
        shared_data: Optional[dict] = None,
    ) -> RelationshipScore:
        """Score a single relationship across 6 dimensions."""
        interactions = interactions or []
        shared_data = shared_data or {}
        now = datetime.now(timezone.utc)

        # 1. Recency (25%) — exponential decay
        recency = self._score_recency(interactions, now)

        # 2. Frequency (20%) — interactions per 90-day window
        frequency = self._score_frequency(interactions, now)

        # 3. Quality (20%) — weighted interaction types
        quality = self._score_quality(interactions)

        # 4. Reciprocity (15%) — two-way vs one-way
        reciprocity = self._score_reciprocity(interactions, contact_a, contact_b)

        # 5. Depth (10%) — shared programs, contacts, referrals
        depth = self._score_depth(shared_data)

        # 6. Outcome (10%) — placements, introductions
        outcome = self._score_outcome(shared_data)

        total = (
            recency * DIMENSION_WEIGHTS["recency"]
            + frequency * DIMENSION_WEIGHTS["frequency"]
            + quality * DIMENSION_WEIGHTS["quality"]
            + reciprocity * DIMENSION_WEIGHTS["reciprocity"]
            + depth * DIMENSION_WEIGHTS["depth"]
            + outcome * DIMENSION_WEIGHTS["outcome"]
        )

        score = RelationshipScore(
            contact_a=contact_a,
            contact_b=contact_b,
            total_score=round(total, 1),
            recency_score=round(recency, 1),
            frequency_score=round(frequency, 1),
            quality_score=round(quality, 1),
            reciprocity_score=round(reciprocity, 1),
            depth_score=round(depth, 1),
            outcome_score=round(outcome, 1),
            factors={
                "interaction_count": len(interactions),
                "shared_programs": shared_data.get("shared_programs", 0),
                "shared_contacts": shared_data.get("shared_contacts", 0),
                "placements": shared_data.get("placements", 0),
            },
            scored_at=now.isoformat(),
        )

        cache_key = f"{contact_a}:{contact_b}"
        self._scores_cache[cache_key] = score
        return score

    async def score_all_relationships(
        self, relationships: Optional[List[dict]] = None,
    ) -> List[RelationshipScore]:
        """Batch score all relationships."""
        if relationships is None:
            relationships = await self._fetch_all_relationships()

        scores = []
        for rel in relationships:
            score = await self.score_relationship(
                contact_a=rel.get("contact_a", ""),
                contact_b=rel.get("contact_b", ""),
                interactions=rel.get("interactions", []),
                shared_data=rel.get("shared_data", {}),
            )
            scores.append(score)

        scores.sort(key=lambda s: s.total_score, reverse=True)
        return scores

    async def get_decaying_relationships(
        self, threshold: float = 30.0, days: int = 14,
    ) -> List[DecayingRelationship]:
        """Find relationships at risk of decay."""
        datetime.now(timezone.utc)
        decaying = []

        for key, score in self._scores_cache.items():
            if score.total_score < threshold:
                continue

            days_inactive = score.factors.get("days_since_contact", 0)
            if days_inactive < days:
                continue

            # Project score forward 7 days
            projected = score.total_score * math.pow(0.5, 7 / RECENCY_HALF_LIFE)

            if days_inactive > 30:
                risk = "critical"
                action = "Immediate outreach needed — schedule a call or meeting"
            elif days_inactive > 14:
                risk = "warning"
                action = "Follow up with a personalized email or LinkedIn message"
            else:
                risk = "watch"
                action = "Monitor — consider a casual touch point"

            decaying.append(DecayingRelationship(
                contact_a=score.contact_a,
                contact_b=score.contact_b,
                current_score=score.total_score,
                days_since_contact=days_inactive,
                projected_score_7d=round(projected, 1),
                risk_level=risk,
                recommended_action=action,
            ))

        decaying.sort(key=lambda d: d.days_since_contact, reverse=True)
        return decaying

    async def get_strongest_paths(
        self,
        from_contact: str,
        to_contact: str,
        graph_data: Optional[Dict[str, List[dict]]] = None,
        max_hops: int = 4,
    ) -> List[RankedPath]:
        """Find strongest paths between two contacts."""
        graph_data = graph_data or await self._fetch_graph_neighborhood(from_contact, max_hops)

        if not graph_data:
            return []

        # Build adjacency with strengths
        adjacency: Dict[str, Dict[str, float]] = {}
        edge_types: Dict[str, str] = {}
        for node_id, edges in graph_data.items():
            adjacency.setdefault(node_id, {})
            for edge in edges:
                neighbor = edge.get("to", edge.get("target", ""))
                strength = edge.get("strength", edge.get("score", 50.0))
                adjacency[node_id][neighbor] = strength
                adjacency.setdefault(neighbor, {})[node_id] = strength
                edge_types[f"{node_id}:{neighbor}"] = edge.get("type", "knows")

        # BFS with path tracking up to max_hops
        paths = self._find_all_paths(adjacency, from_contact, to_contact, max_hops)

        # Score and rank paths
        ranked = []
        for path in paths:
            segments = []
            strengths = []
            for i in range(len(path) - 1):
                a, b = path[i], path[i + 1]
                s = adjacency.get(a, {}).get(b, 0)
                strengths.append(s)
                segments.append(PathSegment(
                    from_contact=a,
                    to_contact=b,
                    strength=s,
                    relationship_type=edge_types.get(f"{a}:{b}", "knows"),
                ))

            if not strengths:
                continue

            # Path score: geometric mean of segment strengths
            product = 1.0
            for s in strengths:
                product *= max(s, 0.01) / 100.0
            total = (product ** (1.0 / len(strengths))) * 100

            ranked.append(RankedPath(
                path=path,
                segments=segments,
                total_strength=round(total, 1),
                weakest_link=round(min(strengths), 1),
                hops=len(path) - 1,
            ))

        ranked.sort(key=lambda r: r.total_strength, reverse=True)
        return ranked[:5]  # Top 5 paths

    # =========================================
    # DIMENSION SCORING
    # =========================================

    def _score_recency(self, interactions: List[dict], now: datetime) -> float:
        """Exponential decay based on most recent interaction."""
        if not interactions:
            return 0.0

        most_recent = self._most_recent_date(interactions, now)
        days_ago = (now - most_recent).days if most_recent else 90

        # Exponential decay: halves every RECENCY_HALF_LIFE days
        score = 100.0 * math.pow(0.5, days_ago / RECENCY_HALF_LIFE)
        return max(0, min(100, score))

    def _score_frequency(self, interactions: List[dict], now: datetime) -> float:
        """Normalized interaction count over 90-day window."""
        if not interactions:
            return 0.0

        cutoff = now - timedelta(days=90)
        recent = [i for i in interactions if self._interaction_date(i, now) >= cutoff]
        count = len(recent)

        # Normalize: 1/week = 50, 2/week = 75, daily = 95
        if count >= 90:
            return 95.0
        elif count >= 26:
            return 75.0 + (count - 26) * (20.0 / 64)
        elif count >= 12:
            return 50.0 + (count - 12) * (25.0 / 14)
        else:
            return count * (50.0 / 12)

    def _score_quality(self, interactions: List[dict]) -> float:
        """Weighted average of interaction types."""
        if not interactions:
            return 0.0

        total = 0.0
        for inter in interactions:
            itype = str(inter.get("type", inter.get("channel", "email"))).lower()
            total += INTERACTION_QUALITY.get(itype, 0.3)

        avg = total / len(interactions)
        return min(100, avg * 100)

    def _score_reciprocity(
        self, interactions: List[dict], contact_a: str, contact_b: str,
    ) -> float:
        """Two-way communication score."""
        if not interactions:
            return 0.0

        from_a = sum(1 for i in interactions if i.get("initiator") == contact_a)
        from_b = sum(1 for i in interactions if i.get("initiator") == contact_b)

        if from_a == 0 and from_b == 0:
            return 50.0  # Unknown direction → neutral

        total = from_a + from_b
        if total == 0:
            return 50.0

        ratio = min(from_a, from_b) / max(from_a, from_b) if max(from_a, from_b) > 0 else 0
        return min(100, ratio * 100)

    def _score_depth(self, shared_data: dict) -> float:
        """Shared programs, contacts, and referrals."""
        score = 0.0
        score += min(shared_data.get("shared_programs", 0) * 20, 40)
        score += min(shared_data.get("shared_contacts", 0) * 5, 30)
        score += min(shared_data.get("referrals", 0) * 15, 30)
        return min(100, score)

    def _score_outcome(self, shared_data: dict) -> float:
        """Past placements and successful introductions."""
        score = 0.0
        score += min(shared_data.get("placements", 0) * 30, 60)
        score += min(shared_data.get("introductions", 0) * 20, 40)
        return min(100, score)

    # =========================================
    # HELPERS
    # =========================================

    def _most_recent_date(self, interactions: List[dict], now: datetime) -> Optional[datetime]:
        """Get the most recent interaction date."""
        dates = []
        for i in interactions:
            d = self._interaction_date(i, now)
            dates.append(d)
        return max(dates) if dates else None

    def _interaction_date(self, interaction: dict, now: datetime) -> datetime:
        """Parse interaction date."""
        dt = interaction.get("date") or interaction.get("timestamp") or interaction.get("created_at")
        if isinstance(dt, datetime):
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        if isinstance(dt, str):
            try:
                parsed = datetime.fromisoformat(dt.replace("Z", "+00:00"))
                return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
            except Exception:
                pass
        return now - timedelta(days=90)  # Default to 90 days ago

    def _find_all_paths(
        self, adjacency: Dict[str, Dict[str, float]],
        start: str, end: str, max_hops: int,
    ) -> List[List[str]]:
        """BFS to find all paths up to max_hops."""
        if start not in adjacency:
            return []

        paths = []
        queue: List[List[str]] = [[start]]

        while queue:
            path = queue.pop(0)
            node = path[-1]

            if node == end and len(path) > 1:
                paths.append(path)
                continue

            if len(path) - 1 >= max_hops:
                continue

            for neighbor in adjacency.get(node, {}):
                if neighbor not in path:  # Avoid cycles
                    queue.append(path + [neighbor])

        return paths

    async def _fetch_all_relationships(self) -> List[dict]:
        """Fetch relationships from graph client."""
        if self._graph and hasattr(self._graph, "get_all_relationships"):
            return await self._graph.get_all_relationships()
        return []

    async def _fetch_graph_neighborhood(
        self, contact_id: str, max_hops: int,
    ) -> Dict[str, List[dict]]:
        """Fetch graph neighborhood from client."""
        if self._graph and hasattr(self._graph, "get_neighborhood"):
            return await self._graph.get_neighborhood(contact_id, max_hops)
        return {}


# =========================================
# SINGLETON
# =========================================

_model: Optional[RelationshipStrengthModel] = None


def get_relationship_model() -> RelationshipStrengthModel:
    global _model
    if _model is None:
        _model = RelationshipStrengthModel()
    return _model
