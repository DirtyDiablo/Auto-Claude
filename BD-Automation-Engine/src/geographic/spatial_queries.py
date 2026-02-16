"""Phase 48A — Spatial Query Processor.

Radius search, cluster analysis, geographic overlap, commute analysis,
competitive density, and heatmap data for Kepler.gl visualization.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.geographic.geocoding_engine import (
    GeocodingEngine,
    get_geocoding_engine,
    _FACILITIES,
    _CONTACTS,
    _PROGRAM_LOCATIONS,
    _JOB_LOCATIONS,
)


# =========================================
# CONSTANTS
# =========================================

EARTH_RADIUS_MILES = 3958.8
EARTH_RADIUS_KM = 6371.0


# =========================================
# DATA CLASSES
# =========================================


@dataclass
class RadiusResult:
    center: Dict[str, Any] = field(default_factory=dict)
    radius_miles: float = 0.0
    entities: List[Dict[str, Any]] = field(default_factory=list)
    total: int = 0


@dataclass
class GeoCluster:
    id: str = ""
    center_lat: float = 0.0
    center_lng: float = 0.0
    region: str = ""
    entities: List[Dict[str, Any]] = field(default_factory=list)
    total: int = 0
    dominant_programs: List[str] = field(default_factory=list)
    dominant_companies: List[str] = field(default_factory=list)


@dataclass
class OverlapResult:
    program_a: str = ""
    program_b: str = ""
    shared_locations: List[str] = field(default_factory=list)
    proximity_pairs: List[Dict[str, Any]] = field(default_factory=list)
    overlap_score: float = 0.0


@dataclass
class CommuteResult:
    origin: Dict[str, Any] = field(default_factory=dict)
    jobs_in_range: List[Dict[str, Any]] = field(default_factory=list)
    total: int = 0


@dataclass
class CompetitiveDensity:
    region: str = ""
    competitors: List[Dict[str, Any]] = field(default_factory=list)
    total_facilities: int = 0
    total_contacts: int = 0
    density_score: float = 0.0


# =========================================
# SPATIAL QUERY PROCESSOR
# =========================================


class SpatialQueryProcessor:
    """Processes geographic queries: radius, clusters, overlap, commute, density."""

    def __init__(self, geocoder: Optional[GeocodingEngine] = None) -> None:
        self._geocoder = geocoder or get_geocoding_engine()

    # --------------------------------------------------
    # HAVERSINE DISTANCE
    # --------------------------------------------------

    @staticmethod
    def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance in miles between two points (Haversine)."""
        lat1_r, lat2_r = math.radians(lat1), math.radians(lat2)
        dlat = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlng / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return EARTH_RADIUS_MILES * c

    # --------------------------------------------------
    # RADIUS SEARCH
    # --------------------------------------------------

    def find_within_radius(
        self,
        center_lat: float,
        center_lng: float,
        radius_miles: float = 30.0,
        entity_types: Optional[List[str]] = None,
    ) -> RadiusResult:
        """Find all entities within radius of a point."""
        if entity_types is None:
            entity_types = ["contact", "program", "job", "facility"]

        entities: List[Dict[str, Any]] = []

        # Facilities
        if "facility" in entity_types:
            for fac in _FACILITIES:
                dist = self.haversine(center_lat, center_lng, fac["lat"], fac["lng"])
                if dist <= radius_miles:
                    entities.append(
                        {
                            "entity_type": "facility",
                            "entity_id": fac["name"],
                            "name": fac["name"],
                            "lat": fac["lat"],
                            "lng": fac["lng"],
                            "distance_miles": round(dist, 2),
                            "facility_type": fac["type"],
                            "state": fac["state"],
                        }
                    )

        # Contacts
        if "contact" in entity_types:
            for c in _CONTACTS:
                geo = self._geocoder.geocode(c["location"])
                if geo:
                    dist = self.haversine(center_lat, center_lng, geo.lat, geo.lng)
                    if dist <= radius_miles:
                        entities.append(
                            {
                                "entity_type": "contact",
                                "entity_id": c["id"],
                                "name": c["name"],
                                "lat": geo.lat,
                                "lng": geo.lng,
                                "distance_miles": round(dist, 2),
                                "company": c["company"],
                                "program": c["program"],
                            }
                        )

        # Jobs
        if "job" in entity_types:
            for j in _JOB_LOCATIONS:
                geo = self._geocoder.geocode(j["location"])
                if geo:
                    dist = self.haversine(center_lat, center_lng, geo.lat, geo.lng)
                    if dist <= radius_miles:
                        entities.append(
                            {
                                "entity_type": "job",
                                "entity_id": j["id"],
                                "name": j["title"],
                                "lat": geo.lat,
                                "lng": geo.lng,
                                "distance_miles": round(dist, 2),
                                "program": j["program"],
                            }
                        )

        # Programs
        if "program" in entity_types:
            for prog in _PROGRAM_LOCATIONS:
                for loc in prog["locations"]:
                    geo = self._geocoder.geocode(loc)
                    if geo:
                        dist = self.haversine(center_lat, center_lng, geo.lat, geo.lng)
                        if dist <= radius_miles:
                            entities.append(
                                {
                                    "entity_type": "program",
                                    "entity_id": prog["id"],
                                    "name": prog["name"],
                                    "lat": geo.lat,
                                    "lng": geo.lng,
                                    "distance_miles": round(dist, 2),
                                    "location": loc,
                                }
                            )
                            break  # one match per program

        # Sort by distance
        entities.sort(key=lambda e: e["distance_miles"])

        return RadiusResult(
            center={"lat": center_lat, "lng": center_lng},
            radius_miles=radius_miles,
            entities=entities,
            total=len(entities),
        )

    # --------------------------------------------------
    # CLUSTER ANALYSIS
    # --------------------------------------------------

    def cluster_analysis(self, entity_type: str = "contact") -> List[GeoCluster]:
        """Group entities by geographic region into clusters."""
        clusters_map: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        if entity_type == "contact":
            for c in _CONTACTS:
                geo = self._geocoder.geocode(c["location"])
                if geo:
                    clusters_map[geo.region].append(
                        {
                            "entity_id": c["id"],
                            "name": c["name"],
                            "lat": geo.lat,
                            "lng": geo.lng,
                            "company": c["company"],
                            "program": c["program"],
                        }
                    )
        elif entity_type == "job":
            for j in _JOB_LOCATIONS:
                geo = self._geocoder.geocode(j["location"])
                if geo:
                    clusters_map[geo.region].append(
                        {
                            "entity_id": j["id"],
                            "name": j["title"],
                            "lat": geo.lat,
                            "lng": geo.lng,
                            "program": j["program"],
                        }
                    )
        elif entity_type == "facility":
            for fac in _FACILITIES:
                clusters_map[fac["region"]].append(
                    {
                        "entity_id": fac["name"],
                        "name": fac["name"],
                        "lat": fac["lat"],
                        "lng": fac["lng"],
                        "facility_type": fac["type"],
                    }
                )
        elif entity_type == "program":
            for prog in _PROGRAM_LOCATIONS:
                for loc in prog["locations"]:
                    geo = self._geocoder.geocode(loc)
                    if geo:
                        clusters_map[geo.region].append(
                            {
                                "entity_id": prog["id"],
                                "name": prog["name"],
                                "lat": geo.lat,
                                "lng": geo.lng,
                                "location": loc,
                            }
                        )

        clusters: List[GeoCluster] = []
        for region, entities in sorted(clusters_map.items()):
            if not entities:
                continue

            avg_lat = sum(e["lat"] for e in entities) / len(entities)
            avg_lng = sum(e["lng"] for e in entities) / len(entities)

            # Find dominant programs and companies
            programs = [e.get("program", "") for e in entities if e.get("program")]
            companies = [e.get("company", "") for e in entities if e.get("company")]

            prog_counts: Dict[str, int] = {}
            for p in programs:
                prog_counts[p] = prog_counts.get(p, 0) + 1
            comp_counts: Dict[str, int] = {}
            for c in companies:
                comp_counts[c] = comp_counts.get(c, 0) + 1

            top_progs = sorted(
                prog_counts.keys(), key=lambda p: prog_counts[p], reverse=True
            )[:3]
            top_comps = sorted(
                comp_counts.keys(), key=lambda c: comp_counts[c], reverse=True
            )[:3]

            clusters.append(
                GeoCluster(
                    id=f"cluster_{region}",
                    center_lat=round(avg_lat, 4),
                    center_lng=round(avg_lng, 4),
                    region=region,
                    entities=entities,
                    total=len(entities),
                    dominant_programs=top_progs,
                    dominant_companies=top_comps,
                )
            )

        return clusters

    # --------------------------------------------------
    # OVERLAP ANALYSIS
    # --------------------------------------------------

    def overlap_analysis(
        self, program_a: str, program_b: str, proximity_threshold_miles: float = 50.0
    ) -> OverlapResult:
        """Analyze geographic overlap between two programs."""
        prog_a = next((p for p in _PROGRAM_LOCATIONS if p["name"] == program_a), None)
        prog_b = next((p for p in _PROGRAM_LOCATIONS if p["name"] == program_b), None)

        if not prog_a or not prog_b:
            return OverlapResult(program_a=program_a, program_b=program_b)

        # Find shared locations (exact text match)
        shared = list(set(prog_a["locations"]) & set(prog_b["locations"]))

        # Find proximity pairs
        proximity_pairs: List[Dict[str, Any]] = []
        for loc_a in prog_a["locations"]:
            geo_a = self._geocoder.geocode(loc_a)
            if not geo_a:
                continue
            for loc_b in prog_b["locations"]:
                if loc_a == loc_b:
                    continue
                geo_b = self._geocoder.geocode(loc_b)
                if not geo_b:
                    continue
                dist = self.haversine(geo_a.lat, geo_a.lng, geo_b.lat, geo_b.lng)
                if dist <= proximity_threshold_miles:
                    proximity_pairs.append(
                        {
                            "location_a": loc_a,
                            "location_b": loc_b,
                            "distance_miles": round(dist, 2),
                        }
                    )

        # Overlap score: shared locations + proximity pairs weighted
        total_locations = len(set(prog_a["locations"]) | set(prog_b["locations"]))
        overlap_score = (len(shared) + len(proximity_pairs) * 0.5) / max(
            total_locations, 1
        )

        return OverlapResult(
            program_a=program_a,
            program_b=program_b,
            shared_locations=shared,
            proximity_pairs=proximity_pairs,
            overlap_score=round(min(overlap_score, 1.0), 4),
        )

    # --------------------------------------------------
    # COMMUTE ANALYSIS
    # --------------------------------------------------

    def commute_analysis(
        self, origin_lat: float, origin_lng: float, max_commute_miles: float = 50.0
    ) -> CommuteResult:
        """Find jobs within commute distance of an origin."""
        jobs_in_range: List[Dict[str, Any]] = []

        for j in _JOB_LOCATIONS:
            geo = self._geocoder.geocode(j["location"])
            if not geo:
                continue
            dist = self.haversine(origin_lat, origin_lng, geo.lat, geo.lng)
            if dist <= max_commute_miles:
                jobs_in_range.append(
                    {
                        "job_id": j["id"],
                        "title": j["title"],
                        "program": j["program"],
                        "location": j["location"],
                        "lat": geo.lat,
                        "lng": geo.lng,
                        "distance_miles": round(dist, 2),
                        "estimated_commute_min": round(dist * 2.0, 0),  # rough estimate
                    }
                )

        jobs_in_range.sort(key=lambda j: j["distance_miles"])

        return CommuteResult(
            origin={"lat": origin_lat, "lng": origin_lng},
            jobs_in_range=jobs_in_range,
            total=len(jobs_in_range),
        )

    # --------------------------------------------------
    # COMPETITIVE DENSITY
    # --------------------------------------------------

    def competitive_density(self, region: str) -> CompetitiveDensity:
        """Analyze competitor presence in a region."""
        # Count facilities by competitor in region
        competitor_facilities: Dict[str, int] = {}
        total_facilities = 0
        for fac in _FACILITIES:
            if fac["region"] != region:
                continue
            total_facilities += 1
            if fac["type"] == "hq":
                name = fac["name"]
                # Map to company
                for comp in [
                    "Northrop",
                    "Raytheon",
                    "BAE",
                    "Booz Allen",
                    "SAIC",
                    "Peraton",
                    "ManTech",
                    "GDIT",
                    "Leidos",
                    "Lockheed",
                    "L3Harris",
                    "Boeing",
                ]:
                    if comp.lower() in name.lower():
                        competitor_facilities[comp] = (
                            competitor_facilities.get(comp, 0) + 1
                        )
                        break

        # Count contacts by company in region
        competitor_contacts: Dict[str, int] = {}
        total_contacts = 0
        for c in _CONTACTS:
            geo = self._geocoder.geocode(c["location"])
            if not geo or geo.region != region:
                continue
            total_contacts += 1
            company = c["company"]
            competitor_contacts[company] = competitor_contacts.get(company, 0) + 1

        # Merge into competitor list
        all_comps = set(
            list(competitor_facilities.keys()) + list(competitor_contacts.keys())
        )
        competitors: List[Dict[str, Any]] = []
        for comp in sorted(all_comps):
            competitors.append(
                {
                    "company": comp,
                    "facilities": competitor_facilities.get(comp, 0),
                    "contacts": competitor_contacts.get(comp, 0),
                    "presence_score": round(
                        (
                            competitor_facilities.get(comp, 0) * 2
                            + competitor_contacts.get(comp, 0)
                        )
                        / max(total_facilities + total_contacts, 1),
                        4,
                    ),
                }
            )

        # Overall density score
        density = (
            len(all_comps) / max(total_facilities, 1) if total_facilities > 0 else 0
        )

        return CompetitiveDensity(
            region=region,
            competitors=competitors,
            total_facilities=total_facilities,
            total_contacts=total_contacts,
            density_score=round(min(density, 1.0), 4),
        )

    # --------------------------------------------------
    # HEATMAP DATA (for Kepler.gl)
    # --------------------------------------------------

    def generate_heatmap(self, entity_type: str = "contact") -> List[Dict[str, Any]]:
        """Generate heatmap point data for Kepler.gl visualization."""
        points: List[Dict[str, Any]] = []

        if entity_type == "contact":
            for c in _CONTACTS:
                geo = self._geocoder.geocode(c["location"])
                if geo:
                    points.append(
                        {
                            "lat": geo.lat,
                            "lng": geo.lng,
                            "weight": 1.0,
                            "name": c["name"],
                            "company": c["company"],
                            "program": c["program"],
                        }
                    )
        elif entity_type == "job":
            for j in _JOB_LOCATIONS:
                geo = self._geocoder.geocode(j["location"])
                if geo:
                    points.append(
                        {
                            "lat": geo.lat,
                            "lng": geo.lng,
                            "weight": 1.0,
                            "name": j["title"],
                            "program": j["program"],
                        }
                    )
        elif entity_type == "facility":
            for fac in _FACILITIES:
                points.append(
                    {
                        "lat": fac["lat"],
                        "lng": fac["lng"],
                        "weight": 1.0,
                        "name": fac["name"],
                        "facility_type": fac["type"],
                        "region": fac["region"],
                    }
                )
        elif entity_type == "program":
            for prog in _PROGRAM_LOCATIONS:
                for loc in prog["locations"]:
                    geo = self._geocoder.geocode(loc)
                    if geo:
                        points.append(
                            {
                                "lat": geo.lat,
                                "lng": geo.lng,
                                "weight": 1.0,
                                "name": prog["name"],
                                "location": loc,
                            }
                        )

        return points

    # --------------------------------------------------
    # STATS
    # --------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_contacts": len(_CONTACTS),
            "total_programs": len(_PROGRAM_LOCATIONS),
            "total_jobs": len(_JOB_LOCATIONS),
            "total_facilities": len(_FACILITIES),
            "regions": self._geocoder.get_regions(),
        }


# =========================================
# SINGLETON
# =========================================

_instance: Optional[SpatialQueryProcessor] = None


def get_spatial_processor() -> SpatialQueryProcessor:
    global _instance
    if _instance is None:
        _instance = SpatialQueryProcessor()
    return _instance
