"""
Phase 21A — Neo4j Graph API Router

REST endpoints for graph queries, ingestion, and health.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/neo4j", tags=["neo4j-graph"])


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class IngestRequest(BaseModel):
    limit: Optional[int] = Field(None, description="Max records to ingest (None = all)")


# ---------------------------------------------------------------------------
# Health & Stats
# ---------------------------------------------------------------------------

@router.get("/health")
async def neo4j_health():
    """Neo4j connection health check."""
    from Engine8_Knowledge.graph.neo4j_manager import get_neo4j_manager
    mgr = get_neo4j_manager()
    return mgr.health_check()


@router.get("/stats")
async def neo4j_graph_stats():
    """Graph statistics: node/edge counts by type."""
    from Engine8_Knowledge.graph.queries import get_graph_queries
    gq = get_graph_queries()
    return gq.get_graph_stats()


@router.get("/schema")
async def neo4j_schema_info():
    """Current schema: constraints, indexes, node/relationship types."""
    from Engine8_Knowledge.graph.neo4j_manager import get_neo4j_manager
    from Engine8_Knowledge.graph.schema import get_schema_info
    mgr = get_neo4j_manager()
    return get_schema_info(mgr)


@router.post("/schema/apply")
async def apply_neo4j_schema():
    """Apply constraints and indexes (idempotent)."""
    from Engine8_Knowledge.graph.neo4j_manager import get_neo4j_manager
    from Engine8_Knowledge.graph.schema import apply_schema
    mgr = get_neo4j_manager()
    return apply_schema(mgr)


# ---------------------------------------------------------------------------
# Query Endpoints
# ---------------------------------------------------------------------------

@router.get("/contacts/{program}")
async def contacts_by_program(program: str):
    """Contacts on a program."""
    from Engine8_Knowledge.graph.queries import get_graph_queries
    gq = get_graph_queries()
    results = gq.find_contacts_by_program(program)
    return {"program": program, "contacts": results, "count": len(results)}


@router.get("/path/{person_a}/{person_b}")
async def shortest_path(person_a: str, person_b: str):
    """Shortest relationship path between two people."""
    from Engine8_Knowledge.graph.queries import get_graph_queries
    gq = get_graph_queries()
    return gq.find_shortest_path(person_a, person_b)


@router.get("/introduction/{target}")
async def introduction_path(target: str):
    """Warm introduction paths to a target person."""
    from Engine8_Knowledge.graph.queries import get_graph_queries
    gq = get_graph_queries()
    paths = gq.find_introduction_path(target)
    return {"target": target, "paths": paths, "count": len(paths)}


@router.get("/org-chart/{program}")
async def program_org_chart(program: str):
    """Program org chart data (JSON for D3.js)."""
    from Engine8_Knowledge.graph.queries import get_graph_queries
    gq = get_graph_queries()
    return gq.get_program_org_chart(program)


@router.get("/company/{name}")
async def company_network(name: str):
    """Company intelligence network."""
    from Engine8_Knowledge.graph.queries import get_graph_queries
    gq = get_graph_queries()
    return gq.get_company_network(name)


@router.get("/contact/{name}/360")
async def contact_360(name: str):
    """Full contact profile with relationships."""
    from Engine8_Knowledge.graph.queries import get_graph_queries
    gq = get_graph_queries()
    return gq.get_contact_360(name)


@router.get("/hiring-signals")
async def hiring_signals(days: int = Query(30)):
    """Programs with active hiring."""
    from Engine8_Knowledge.graph.queries import get_graph_queries
    gq = get_graph_queries()
    signals = gq.find_hiring_signals(days)
    return {"signals": signals, "count": len(signals)}


@router.get("/competitive/{company_a}/{company_b}")
async def competitive_overlap(company_a: str, company_b: str):
    """Programs where two companies compete."""
    from Engine8_Knowledge.graph.queries import get_graph_queries
    gq = get_graph_queries()
    return gq.find_competitive_overlap(company_a, company_b)


@router.get("/location/{city}")
async def location_intel(city: str):
    """Location intelligence: programs, people, jobs."""
    from Engine8_Knowledge.graph.queries import get_graph_queries
    gq = get_graph_queries()
    return gq.get_location_intel(city)


@router.get("/orphans")
async def orphan_contacts():
    """Contacts not connected to any program."""
    from Engine8_Knowledge.graph.queries import get_graph_queries
    gq = get_graph_queries()
    orphans = gq.find_orphan_contacts()
    return {"orphans": orphans, "count": len(orphans)}


# ---------------------------------------------------------------------------
# Ingestion Endpoints
# ---------------------------------------------------------------------------

@router.post("/ingest/contacts")
async def ingest_contacts(req: IngestRequest = IngestRequest()):
    """Trigger contact ingestion into Neo4j."""
    from Engine8_Knowledge.graph.neo4j_manager import get_neo4j_manager
    from Engine8_Knowledge.graph.ingestion import GraphIngestionEngine
    engine = GraphIngestionEngine(get_neo4j_manager())
    return engine.ingest_contacts(req.limit)


@router.post("/ingest/programs")
async def ingest_programs(req: IngestRequest = IngestRequest()):
    """Trigger program ingestion into Neo4j."""
    from Engine8_Knowledge.graph.neo4j_manager import get_neo4j_manager
    from Engine8_Knowledge.graph.ingestion import GraphIngestionEngine
    engine = GraphIngestionEngine(get_neo4j_manager())
    return engine.ingest_programs(req.limit)


@router.post("/ingest/jobs")
async def ingest_jobs(req: IngestRequest = IngestRequest()):
    """Trigger job ingestion into Neo4j."""
    from Engine8_Knowledge.graph.neo4j_manager import get_neo4j_manager
    from Engine8_Knowledge.graph.ingestion import GraphIngestionEngine
    engine = GraphIngestionEngine(get_neo4j_manager())
    return engine.ingest_jobs(req.limit)


@router.post("/ingest/interactions")
async def ingest_interactions(req: IngestRequest = IngestRequest()):
    """Trigger interaction ingestion into Neo4j."""
    from Engine8_Knowledge.graph.neo4j_manager import get_neo4j_manager
    from Engine8_Knowledge.graph.ingestion import GraphIngestionEngine
    engine = GraphIngestionEngine(get_neo4j_manager())
    return engine.ingest_interactions(req.limit)


@router.post("/ingest/locations")
async def ingest_locations():
    """Trigger location ingestion into Neo4j."""
    from Engine8_Knowledge.graph.neo4j_manager import get_neo4j_manager
    from Engine8_Knowledge.graph.ingestion import GraphIngestionEngine
    engine = GraphIngestionEngine(get_neo4j_manager())
    return engine.ingest_locations()


@router.post("/ingest/all")
async def ingest_all(req: IngestRequest = IngestRequest()):
    """Full graph rebuild from all sources."""
    from Engine8_Knowledge.graph.neo4j_manager import get_neo4j_manager
    from Engine8_Knowledge.graph.ingestion import GraphIngestionEngine
    engine = GraphIngestionEngine(get_neo4j_manager())
    return engine.ingest_all(req.limit)
