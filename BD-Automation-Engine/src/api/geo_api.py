"""Phase 48A — Geographic Intelligence API (10 endpoints).

REST endpoints for geocoding, radius search, cluster analysis,
overlap analysis, commute analysis, competitive density, heatmaps,
and facility queries.
"""

import logging
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from src.geographic.geocoding_engine import (
    get_geocoding_engine,
)
from src.geographic.spatial_queries import (
    get_spatial_processor,
)

logger = logging.getLogger(__name__)


# =========================================
# REQUEST MODELS
# =========================================

class GeocodeRequest(BaseModel):
    location: str


class BatchGeocodeRequest(BaseModel):
    entity_type: str = "all"  # contact | program | job | all


class RadiusRequest(BaseModel):
    lat: float
    lng: float
    radius_miles: float = 30.0
    entity_types: Optional[List[str]] = None


class OverlapRequest(BaseModel):
    program_a: str
    program_b: str
    proximity_threshold_miles: float = 50.0


class CommuteRequest(BaseModel):
    lat: float
    lng: float
    max_commute_miles: float = 50.0


# =========================================
# ROUTE SETUP
# =========================================

def include_geo_router(app: FastAPI) -> None:
    """Register all geographic intelligence endpoints on the FastAPI app."""

    geocoder = get_geocoding_engine()
    spatial = get_spatial_processor()

    # --------------------------------------------------
    # 1. POST /api/geo/geocode — Geocode a location string
    # --------------------------------------------------
    @app.post("/api/geo/geocode")
    async def geo_geocode(req: GeocodeRequest):
        """Geocode a location string to coordinates."""
        geo = geocoder.geocode(req.location)
        if not geo:
            return {"resolved": False, "location": req.location, "geo": None}
        return {"resolved": True, "location": req.location, "geo": geo.to_dict()}

    # --------------------------------------------------
    # 2. POST /api/geo/geocode/batch — Batch geocode entities
    # --------------------------------------------------
    @app.post("/api/geo/geocode/batch")
    async def geo_geocode_batch(req: BatchGeocodeRequest):
        """Batch geocode contacts, programs, and/or jobs."""
        if req.entity_type == "all":
            results = geocoder.batch_geocode_all()
            return {
                "contacts": {
                    "total": results["contacts"].total,
                    "resolved": results["contacts"].resolved,
                    "failed": results["contacts"].failed,
                },
                "programs": {
                    "total": results["programs"].total,
                    "resolved": results["programs"].resolved,
                    "failed": results["programs"].failed,
                },
                "jobs": {
                    "total": results["jobs"].total,
                    "resolved": results["jobs"].resolved,
                    "failed": results["jobs"].failed,
                },
            }
        elif req.entity_type == "contact":
            result = geocoder.batch_geocode_contacts()
        elif req.entity_type == "program":
            result = geocoder.batch_geocode_programs()
        elif req.entity_type == "job":
            result = geocoder.batch_geocode_jobs()
        else:
            raise HTTPException(400, f"Unknown entity type: {req.entity_type}")

        return {
            "total": result.total,
            "resolved": result.resolved,
            "failed": result.failed,
            "entities": [e.to_dict() for e in result.entities],
        }

    # --------------------------------------------------
    # 3. POST /api/geo/radius — Find entities within radius
    # --------------------------------------------------
    @app.post("/api/geo/radius")
    async def geo_radius(req: RadiusRequest):
        """Find all entities within radius of a point."""
        result = spatial.find_within_radius(
            center_lat=req.lat, center_lng=req.lng,
            radius_miles=req.radius_miles,
            entity_types=req.entity_types,
        )
        return {
            "center": result.center,
            "radius_miles": result.radius_miles,
            "entities": result.entities,
            "total": result.total,
        }

    # --------------------------------------------------
    # 4. GET /api/geo/clusters/{entity_type} — Geographic clusters
    # --------------------------------------------------
    @app.get("/api/geo/clusters/{entity_type}")
    async def geo_clusters(entity_type: str):
        """Get geographic clusters for an entity type."""
        if entity_type not in ("contact", "program", "job", "facility"):
            raise HTTPException(400, f"Invalid entity type: {entity_type}")

        clusters = spatial.cluster_analysis(entity_type)
        return {
            "entity_type": entity_type,
            "clusters": [
                {
                    "id": c.id, "region": c.region,
                    "center_lat": c.center_lat, "center_lng": c.center_lng,
                    "total": c.total,
                    "dominant_programs": c.dominant_programs,
                    "dominant_companies": c.dominant_companies,
                    "entities": c.entities,
                }
                for c in clusters
            ],
            "total_clusters": len(clusters),
        }

    # --------------------------------------------------
    # 5. POST /api/geo/overlap — Program geographic overlap
    # --------------------------------------------------
    @app.post("/api/geo/overlap")
    async def geo_overlap(req: OverlapRequest):
        """Analyze geographic overlap between two programs."""
        result = spatial.overlap_analysis(
            req.program_a, req.program_b, req.proximity_threshold_miles,
        )
        return {
            "program_a": result.program_a,
            "program_b": result.program_b,
            "shared_locations": result.shared_locations,
            "proximity_pairs": result.proximity_pairs,
            "overlap_score": result.overlap_score,
        }

    # --------------------------------------------------
    # 6. POST /api/geo/commute — Commute analysis for candidate
    # --------------------------------------------------
    @app.post("/api/geo/commute")
    async def geo_commute(req: CommuteRequest):
        """Find jobs within commute distance."""
        result = spatial.commute_analysis(
            req.lat, req.lng, req.max_commute_miles,
        )
        return {
            "origin": result.origin,
            "max_commute_miles": req.max_commute_miles,
            "jobs_in_range": result.jobs_in_range,
            "total": result.total,
        }

    # --------------------------------------------------
    # 7. GET /api/geo/competitive-density/{region} — Competitor density
    # --------------------------------------------------
    @app.get("/api/geo/competitive-density/{region}")
    async def geo_competitive_density(region: str):
        """Analyze competitor presence in a region."""
        result = spatial.competitive_density(region)
        return {
            "region": result.region,
            "competitors": result.competitors,
            "total_facilities": result.total_facilities,
            "total_contacts": result.total_contacts,
            "density_score": result.density_score,
        }

    # --------------------------------------------------
    # 8. GET /api/geo/heatmap/{entity_type} — Heatmap data for Kepler.gl
    # --------------------------------------------------
    @app.get("/api/geo/heatmap/{entity_type}")
    async def geo_heatmap(entity_type: str):
        """Generate heatmap data points for Kepler.gl visualization."""
        if entity_type not in ("contact", "program", "job", "facility"):
            raise HTTPException(400, f"Invalid entity type: {entity_type}")

        points = spatial.generate_heatmap(entity_type)
        return {
            "entity_type": entity_type,
            "points": points,
            "total": len(points),
        }

    # --------------------------------------------------
    # 9. GET /api/geo/facilities — All defense facilities
    # --------------------------------------------------
    @app.get("/api/geo/facilities")
    async def geo_facilities(
        region: str = Query("", description="Filter by region"),
        facility_type: str = Query("", description="Filter by type"),
        state: str = Query("", description="Filter by state"),
    ):
        """Get all defense facilities with coordinates."""
        facilities = geocoder.get_facilities(
            region=region, facility_type=facility_type, state=state,
        )
        return {
            "facilities": [f.to_dict() for f in facilities],
            "total": len(facilities),
        }

    # --------------------------------------------------
    # 10. GET /api/geo/stats — Geographic intelligence stats
    # --------------------------------------------------
    @app.get("/api/geo/stats")
    async def geo_stats():
        """Geographic intelligence statistics."""
        geo_stats = geocoder.get_stats()
        spatial_stats = spatial.get_stats()
        return {**geo_stats, **spatial_stats}

    logger.info("Geographic Intelligence API: 10 endpoints registered under /api/geo/*")
