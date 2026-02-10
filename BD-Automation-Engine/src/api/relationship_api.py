"""Phase 34A: Relationship Intelligence API — 14 endpoints.

GET    /relationships/score/{contact_a}/{contact_b}  — Relationship strength
GET    /relationships/scores/{contact_id}            — All relationships for a contact
GET    /relationships/decaying                       — Relationships at risk
GET    /relationships/influence/global               — Global influence rankings
GET    /relationships/influence/program/{name}       — Program-scoped influence
GET    /relationships/influence/{contact_id}/trend   — Influence trajectory
GET    /relationships/path/{from_id}/{to_id}         — Optimal path to target
GET    /relationships/warm-intro/{target}            — Warm intro chain
GET    /relationships/missing-links/{program}        — Network gaps for program
GET    /relationships/communities                    — Detected communities
GET    /relationships/bridges                        — Bridge contacts
GET    /relationships/network-density                — Network density report
GET    /relationships/network-growth                 — Growth trajectory
POST   /relationships/recompute                      — Force recomputation
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from src.graph.relationship_engine import RelationshipStrengthModel, get_relationship_model
from src.graph.influence_scorer import BDPageRank, get_influence_scorer
from src.graph.path_router import OptimalPathRouter, get_path_router
from src.graph.network_analysis import NetworkAnalyzer, get_network_analyzer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/relationships", tags=["relationship-intelligence"])


# =========================================
# REQUEST MODELS
# =========================================

class RecomputeRequest(BaseModel):
    scope: str = Field(default="all", description="Recompute scope: all, influence, strength, paths")


# =========================================
# MODULE STATE
# =========================================

_rel_model: Optional[RelationshipStrengthModel] = None
_influence: Optional[BDPageRank] = None
_path_router: Optional[OptimalPathRouter] = None
_network: Optional[NetworkAnalyzer] = None


def _get_rel_model() -> RelationshipStrengthModel:
    global _rel_model
    if _rel_model is None:
        _rel_model = get_relationship_model()
    return _rel_model


def _get_influence() -> BDPageRank:
    global _influence
    if _influence is None:
        _influence = get_influence_scorer()
    return _influence


def _get_path_router() -> OptimalPathRouter:
    global _path_router
    if _path_router is None:
        _path_router = get_path_router()
    return _path_router


def _get_network() -> NetworkAnalyzer:
    global _network
    if _network is None:
        _network = get_network_analyzer()
    return _network


# =========================================
# RELATIONSHIP STRENGTH ENDPOINTS
# =========================================

@router.get("/score/{contact_a}/{contact_b}")
async def get_relationship_score(contact_a: str, contact_b: str) -> Dict[str, Any]:
    """Score the relationship between two contacts."""
    model = _get_rel_model()
    score = await model.score_relationship(contact_a, contact_b)
    return {
        "contact_a": score.contact_a,
        "contact_b": score.contact_b,
        "total_score": score.total_score,
        "dimensions": {
            "recency": score.recency_score,
            "frequency": score.frequency_score,
            "quality": score.quality_score,
            "reciprocity": score.reciprocity_score,
            "depth": score.depth_score,
            "outcome": score.outcome_score,
        },
        "factors": score.factors,
        "scored_at": score.scored_at,
    }


@router.get("/scores/{contact_id}")
async def get_contact_relationships(contact_id: str) -> Dict[str, Any]:
    """Get all scored relationships for a contact."""
    model = _get_rel_model()
    all_scores = [
        s for s in model._scores_cache.values()
        if s.contact_a == contact_id or s.contact_b == contact_id
    ]
    all_scores.sort(key=lambda s: s.total_score, reverse=True)
    return {
        "contact_id": contact_id,
        "relationships": [
            {
                "other_contact": s.contact_b if s.contact_a == contact_id else s.contact_a,
                "score": s.total_score,
                "recency": s.recency_score,
                "quality": s.quality_score,
            }
            for s in all_scores
        ],
        "total": len(all_scores),
    }


@router.get("/decaying")
async def get_decaying_relationships(
    threshold: float = Query(default=30.0, ge=0, le=100),
    days: int = Query(default=14, ge=1, le=90),
) -> Dict[str, Any]:
    """Find relationships at risk of decay."""
    model = _get_rel_model()
    decaying = await model.get_decaying_relationships(threshold, days)
    return {
        "decaying": [
            {
                "contact_a": d.contact_a,
                "contact_b": d.contact_b,
                "current_score": d.current_score,
                "days_since_contact": d.days_since_contact,
                "projected_score_7d": d.projected_score_7d,
                "risk_level": d.risk_level,
                "recommended_action": d.recommended_action,
            }
            for d in decaying
        ],
        "total": len(decaying),
    }


# =========================================
# INFLUENCE ENDPOINTS
# =========================================

@router.get("/influence/global")
async def get_global_influence(
    limit: int = Query(default=50, ge=1, le=500),
) -> Dict[str, Any]:
    """Global influence rankings."""
    scorer = _get_influence()
    scores = await scorer.compute_influence_scores()
    return {
        "rankings": [
            {
                "rank": s.rank,
                "contact_id": s.contact_id,
                "name": s.name,
                "score": s.score,
                "tier": s.tier,
                "programs": s.programs,
                "connections": s.connections,
            }
            for s in scores[:limit]
        ],
        "total": len(scores),
    }


@router.get("/influence/program/{name}")
async def get_program_influence(name: str) -> Dict[str, Any]:
    """Program-scoped influence rankings."""
    scorer = _get_influence()
    scores = await scorer.compute_program_influence(name)
    return {
        "program": name,
        "rankings": [
            {
                "rank": s.rank,
                "contact_id": s.contact_id,
                "name": s.name,
                "score": s.score,
                "tier": s.tier,
            }
            for s in scores
        ],
        "total": len(scores),
    }


@router.get("/influence/{contact_id}/trend")
async def get_influence_trend(contact_id: str) -> Dict[str, Any]:
    """Influence trajectory for a contact."""
    scorer = _get_influence()
    traj = await scorer.get_influence_trajectory(contact_id)
    return {
        "contact_id": traj.contact_id,
        "current_score": traj.current_score,
        "trend": traj.trend,
        "change_pct": traj.change_pct,
        "history": traj.scores_over_time,
    }


# =========================================
# PATH ENDPOINTS
# =========================================

@router.get("/path/{from_id}/{to_id}")
async def get_optimal_path(
    from_id: str, to_id: str,
    max_hops: int = Query(default=5, ge=2, le=8),
) -> Dict[str, Any]:
    """Find optimal path between two contacts."""
    pr = _get_path_router()
    paths = await pr.find_optimal_path(from_id, to_id, max_hops)
    return {
        "from": from_id,
        "to": to_id,
        "paths": [
            {
                "path": p.path_names,
                "total_strength": p.total_strength,
                "weakest_link": p.weakest_link,
                "weakest_segment": p.weakest_link_segment,
                "hops": p.hops,
                "strategy": p.strategy,
            }
            for p in paths
        ],
        "total": len(paths),
    }


@router.get("/warm-intro/{target}")
async def get_warm_intro(target: str) -> Dict[str, Any]:
    """Find warm introduction chains to a target contact."""
    pr = _get_path_router()
    chains = await pr.find_warm_intro_chain(target)
    return {
        "target": target,
        "chains": [
            {
                "chain": c.chain,
                "total_strength": c.total_strength,
                "hops": c.hops,
                "feasibility": c.feasibility,
                "approach": c.suggested_approach,
            }
            for c in chains
        ],
        "total": len(chains),
    }


@router.get("/missing-links/{program}")
async def get_missing_links(program: str) -> Dict[str, Any]:
    """Identify missing connections for a program."""
    pr = _get_path_router()
    links = await pr.identify_missing_links(program)
    return {
        "program": program,
        "missing_links": [
            {
                "gap_type": l.gap_type,
                "description": l.description,
                "recommended_action": l.recommended_action,
                "priority": l.priority,
            }
            for l in links
        ],
        "total": len(links),
    }


# =========================================
# NETWORK ENDPOINTS
# =========================================

@router.get("/communities")
async def get_communities() -> Dict[str, Any]:
    """Detect contact communities."""
    analyzer = _get_network()
    communities = await analyzer.detect_communities()
    return {
        "communities": [
            {
                "id": c.id,
                "label": c.label,
                "size": c.size,
                "members": c.member_names,
                "avg_strength": c.avg_strength,
                "programs": c.programs,
                "key_member": c.key_member,
            }
            for c in communities
        ],
        "total": len(communities),
    }


@router.get("/bridges")
async def get_bridges() -> Dict[str, Any]:
    """Find bridge contacts connecting communities."""
    analyzer = _get_network()
    bridges = await analyzer.find_bridge_contacts()
    return {
        "bridges": [
            {
                "contact_id": b.contact_id,
                "name": b.name,
                "communities": b.community_labels,
                "bridge_score": b.bridge_score,
                "connections_across": b.connections_across,
            }
            for b in bridges
        ],
        "total": len(bridges),
    }


@router.get("/network-density")
async def get_network_density(
    program: Optional[str] = Query(default=None),
) -> Dict[str, Any]:
    """Network density report."""
    analyzer = _get_network()
    report = await analyzer.get_network_density(program)
    return {
        "scope": report.scope,
        "total_nodes": report.total_nodes,
        "total_edges": report.total_edges,
        "density": report.density,
        "avg_degree": report.avg_degree,
        "avg_strength": report.avg_strength,
        "clustering_coefficient": report.clustering_coefficient,
        "assessment": report.assessment,
    }


@router.get("/network-growth")
async def get_network_growth(
    days: int = Query(default=90, ge=7, le=365),
) -> Dict[str, Any]:
    """Network growth trajectory."""
    analyzer = _get_network()
    report = await analyzer.get_network_growth(days)
    return {
        "period_days": report.period_days,
        "new_contacts": report.new_contacts,
        "new_relationships": report.new_relationships,
        "lost_relationships": report.lost_relationships,
        "net_growth": report.net_growth,
        "growth_rate": report.growth_rate,
        "strongest_new": report.strongest_new,
        "assessment": report.assessment,
    }


# =========================================
# RECOMPUTE ENDPOINT
# =========================================

@router.post("/recompute")
async def recompute(request: RecomputeRequest) -> Dict[str, Any]:
    """Force recomputation of relationship intelligence."""
    results = {}
    scope = request.scope

    if scope in ("all", "influence"):
        scorer = _get_influence()
        scores = await scorer.compute_influence_scores()
        results["influence"] = f"Computed {len(scores)} influence scores"

    if scope in ("all", "strength"):
        model = _get_rel_model()
        all_scores = await model.score_all_relationships()
        results["strength"] = f"Scored {len(all_scores)} relationships"

    return {
        "status": "recomputed",
        "scope": scope,
        "results": results,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# =========================================
# ROUTER INTEGRATION
# =========================================

def configure_relationships(
    graph_client: Any = None,
    rel_model: Optional[RelationshipStrengthModel] = None,
    influence_scorer: Optional[BDPageRank] = None,
    path_router_instance: Optional[OptimalPathRouter] = None,
    network_analyzer: Optional[NetworkAnalyzer] = None,
) -> None:
    """Wire up relationship components during app startup."""
    global _rel_model, _influence, _path_router, _network
    if rel_model:
        _rel_model = rel_model
    if influence_scorer:
        _influence = influence_scorer
    if path_router_instance:
        _path_router = path_router_instance
    if network_analyzer:
        _network = network_analyzer
    if graph_client:
        _get_rel_model().set_graph_client(graph_client)
        _get_influence().set_graph_client(graph_client)


def include_relationship_router(app, **kwargs):
    """Include the Phase 34A relationship router in the main FastAPI app."""
    configure_relationships(**kwargs)
    app.include_router(router)
    logger.info("Phase 34A relationship routes enabled: /relationships/* (14 endpoints)")
