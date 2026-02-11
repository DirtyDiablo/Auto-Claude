"""Phase 48A — Geocoding Engine.

Defense facility cache with 50+ locations, smart resolution pipeline
(cache → fuzzy match → fallback), batch geocoding for contacts, programs,
and jobs.  All coordinates use WGS-84 (lat/lng).
"""

from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


# =========================================
# DATA CLASSES
# =========================================

@dataclass
class GeoPoint:
    lat: float = 0.0
    lng: float = 0.0
    name: str = ""
    address: str = ""
    facility_type: str = ""  # base | scif | hq | lab | shipyard | arsenal | depot | center
    state: str = ""
    region: str = ""  # NCR | southeast | midwest | west | northeast | southwest
    source: str = "cache"  # cache | geocoded | manual

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lat": self.lat, "lng": self.lng, "name": self.name,
            "address": self.address, "facility_type": self.facility_type,
            "state": self.state, "region": self.region, "source": self.source,
        }


@dataclass
class GeocodedEntity:
    entity_id: str = ""
    entity_type: str = ""  # contact | program | job
    entity_name: str = ""
    location_text: str = ""
    geo: Optional[GeoPoint] = None
    resolved: bool = False
    resolution_method: str = ""  # cache | fuzzy | fallback

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id, "entity_type": self.entity_type,
            "entity_name": self.entity_name, "location_text": self.location_text,
            "resolved": self.resolved, "resolution_method": self.resolution_method,
            "geo": self.geo.to_dict() if self.geo else None,
        }


@dataclass
class BatchResult:
    id: str = ""
    total: int = 0
    resolved: int = 0
    failed: int = 0
    entities: List[GeocodedEntity] = field(default_factory=list)
    duration_sec: float = 0.0
    created_at: str = ""

    def __post_init__(self):
        if not self.id:
            raw = f"batch:{datetime.now(timezone.utc).isoformat()}"
            self.id = f"gbatch_{hashlib.md5(raw.encode()).hexdigest()[:10]}"
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


# =========================================
# DEFENSE FACILITY CACHE  (50+ locations)
# =========================================

_FACILITIES: List[Dict[str, Any]] = [
    # === NCR (National Capital Region) ===
    {"name": "Pentagon", "lat": 38.8719, "lng": -77.0563, "state": "VA", "region": "NCR", "type": "hq", "aliases": ["Pentagon, VA", "The Pentagon"]},
    {"name": "Fort Belvoir", "lat": 38.7118, "lng": -77.1452, "state": "VA", "region": "NCR", "type": "base", "aliases": ["Ft Belvoir", "Fort Belvoir, VA"]},
    {"name": "Fort Meade", "lat": 39.1086, "lng": -76.7432, "state": "MD", "region": "NCR", "type": "base", "aliases": ["Ft Meade", "Fort Meade, MD", "NSA HQ"]},
    {"name": "Joint Base Andrews", "lat": 38.8108, "lng": -76.8660, "state": "MD", "region": "NCR", "type": "base", "aliases": ["JB Andrews", "Andrews AFB"]},
    {"name": "Joint Base Anacostia-Bolling", "lat": 38.8394, "lng": -77.0157, "state": "DC", "region": "NCR", "type": "base", "aliases": ["JBAB", "Bolling AFB", "Anacostia"]},
    {"name": "NGA Campus East", "lat": 38.7505, "lng": -77.1744, "state": "VA", "region": "NCR", "type": "center", "aliases": ["NGA East", "Springfield NGA"]},
    {"name": "NGA New Campus", "lat": 38.6335, "lng": -90.1906, "state": "MO", "region": "midwest", "type": "center", "aliases": ["NGA St Louis", "NGA West", "Next NGA West"]},
    {"name": "Reston", "lat": 38.9586, "lng": -77.3570, "state": "VA", "region": "NCR", "type": "hq", "aliases": ["Reston, VA", "Reston Town Center"]},
    {"name": "Tysons Corner", "lat": 38.9187, "lng": -77.2311, "state": "VA", "region": "NCR", "type": "hq", "aliases": ["Tysons, VA", "McLean, VA", "Tysons Corner, VA"]},
    {"name": "Chantilly", "lat": 38.8943, "lng": -77.4311, "state": "VA", "region": "NCR", "type": "hq", "aliases": ["Chantilly, VA", "NRO HQ"]},
    {"name": "GDIT HQ", "lat": 38.9256, "lng": -77.2386, "state": "VA", "region": "NCR", "type": "hq", "aliases": ["GDIT Falls Church", "Falls Church, VA"]},
    {"name": "Leidos HQ", "lat": 38.9570, "lng": -77.3550, "state": "VA", "region": "NCR", "type": "hq", "aliases": ["Leidos Reston", "1750 Presidents St"]},

    # === Virginia (non-NCR) ===
    {"name": "Langley AFB", "lat": 37.0833, "lng": -76.3605, "state": "VA", "region": "southeast", "type": "base", "aliases": ["Langley, VA", "JBLE Langley", "DGS-1", "Joint Base Langley-Eustis"]},
    {"name": "Naval Station Norfolk", "lat": 36.9466, "lng": -76.3036, "state": "VA", "region": "southeast", "type": "base", "aliases": ["NS Norfolk", "Norfolk Naval Station", "Norfolk, VA"]},
    {"name": "Dam Neck", "lat": 36.8113, "lng": -75.9665, "state": "VA", "region": "southeast", "type": "base", "aliases": ["Dam Neck Annex", "NSWC Dam Neck", "Virginia Beach, VA"]},
    {"name": "Quantico", "lat": 38.5227, "lng": -77.3178, "state": "VA", "region": "NCR", "type": "base", "aliases": ["MCB Quantico", "Quantico, VA", "FBI Academy"]},
    {"name": "Dahlgren", "lat": 38.3495, "lng": -77.0369, "state": "VA", "region": "NCR", "type": "base", "aliases": ["NSWC Dahlgren", "Dahlgren, VA"]},
    {"name": "Charlottesville", "lat": 38.0293, "lng": -78.4767, "state": "VA", "region": "southeast", "type": "center", "aliases": ["Charlottesville, VA", "NGIC"]},

    # === Maryland ===
    {"name": "Aberdeen Proving Ground", "lat": 39.4665, "lng": -76.1306, "state": "MD", "region": "NCR", "type": "base", "aliases": ["APG", "Aberdeen, MD", "Aberdeen Proving Ground, MD"]},
    {"name": "Patuxent River", "lat": 38.2851, "lng": -76.4113, "state": "MD", "region": "NCR", "type": "base", "aliases": ["Pax River", "NAS Patuxent River", "St. Inigoes, MD", "Pax River, MD"]},
    {"name": "Indian Head", "lat": 38.5986, "lng": -77.1608, "state": "MD", "region": "NCR", "type": "base", "aliases": ["NSWC Indian Head", "Indian Head, MD"]},
    {"name": "Annapolis Junction", "lat": 39.1227, "lng": -76.7784, "state": "MD", "region": "NCR", "type": "center", "aliases": ["Annapolis Junction, MD", "FANX"]},
    {"name": "Columbia", "lat": 39.2037, "lng": -76.8610, "state": "MD", "region": "NCR", "type": "hq", "aliases": ["Columbia, MD"]},

    # === California ===
    {"name": "Beale AFB", "lat": 39.1361, "lng": -121.4367, "state": "CA", "region": "west", "type": "base", "aliases": ["Beale, CA", "DGS-2"]},
    {"name": "Vandenberg SFB", "lat": 34.7420, "lng": -120.5724, "state": "CA", "region": "west", "type": "base", "aliases": ["Vandenberg, CA", "Vandenberg AFB"]},
    {"name": "San Diego", "lat": 32.7157, "lng": -117.1611, "state": "CA", "region": "west", "type": "base", "aliases": ["San Diego, CA", "SPAWAR", "NAVWAR"]},
    {"name": "Point Mugu", "lat": 34.1193, "lng": -119.1221, "state": "CA", "region": "west", "type": "base", "aliases": ["NAWC Point Mugu", "Point Mugu, CA"]},
    {"name": "China Lake", "lat": 35.6864, "lng": -117.6920, "state": "CA", "region": "west", "type": "base", "aliases": ["NAWC China Lake", "China Lake, CA", "Ridgecrest, CA"]},
    {"name": "El Segundo", "lat": 33.9192, "lng": -118.4165, "state": "CA", "region": "west", "type": "center", "aliases": ["El Segundo, CA", "Los Angeles AFB", "Space Systems Command"]},

    # === Texas ===
    {"name": "Fort Cavazos", "lat": 31.1339, "lng": -97.7753, "state": "TX", "region": "southwest", "type": "base", "aliases": ["Fort Hood", "Ft Cavazos", "Killeen, TX"]},
    {"name": "San Antonio", "lat": 29.4241, "lng": -98.4936, "state": "TX", "region": "southwest", "type": "base", "aliases": ["JBSA", "Lackland AFB", "San Antonio, TX", "Joint Base San Antonio"]},
    {"name": "Fort Bliss", "lat": 31.8112, "lng": -106.4213, "state": "TX", "region": "southwest", "type": "base", "aliases": ["Ft Bliss", "El Paso, TX"]},

    # === Ohio ===
    {"name": "Wright-Patterson AFB", "lat": 39.8261, "lng": -84.0483, "state": "OH", "region": "midwest", "type": "base", "aliases": ["Wright-Patt", "WPAFB", "Dayton, OH", "AFRL"]},

    # === Colorado ===
    {"name": "Peterson SFB", "lat": 38.8014, "lng": -104.7008, "state": "CO", "region": "west", "type": "base", "aliases": ["Peterson AFB", "Colorado Springs, CO", "NORAD"]},
    {"name": "Schriever SFB", "lat": 38.8055, "lng": -104.5257, "state": "CO", "region": "west", "type": "base", "aliases": ["Schriever AFB", "Space Delta"]},
    {"name": "Buckley SFB", "lat": 39.7174, "lng": -104.7520, "state": "CO", "region": "west", "type": "base", "aliases": ["Buckley AFB", "Aurora, CO", "DGS-3"]},

    # === Alabama / Georgia ===
    {"name": "Redstone Arsenal", "lat": 34.6847, "lng": -86.6477, "state": "AL", "region": "southeast", "type": "base", "aliases": ["Redstone", "Huntsville, AL", "MDA"]},
    {"name": "Fort Eisenhower", "lat": 33.4175, "lng": -82.1335, "state": "GA", "region": "southeast", "type": "base", "aliases": ["Fort Gordon", "Ft Eisenhower", "Augusta, GA", "Cyber Center of Excellence"]},
    {"name": "Robins AFB", "lat": 32.6401, "lng": -83.5920, "state": "GA", "region": "southeast", "type": "base", "aliases": ["Robins, GA", "Warner Robins, GA"]},

    # === Florida ===
    {"name": "Eglin AFB", "lat": 30.4633, "lng": -86.5478, "state": "FL", "region": "southeast", "type": "base", "aliases": ["Eglin, FL", "Valparaiso, FL"]},
    {"name": "Hurlburt Field", "lat": 30.4273, "lng": -86.6888, "state": "FL", "region": "southeast", "type": "base", "aliases": ["Hurlburt, FL", "AFSOC"]},
    {"name": "Patrick SFB", "lat": 28.2346, "lng": -80.6101, "state": "FL", "region": "southeast", "type": "base", "aliases": ["Patrick AFB", "Cape Canaveral, FL"]},
    {"name": "MacDill AFB", "lat": 27.8491, "lng": -82.5212, "state": "FL", "region": "southeast", "type": "base", "aliases": ["MacDill, FL", "Tampa, FL", "CENTCOM", "SOCOM"]},

    # === Other ===
    {"name": "Fort Liberty", "lat": 35.1390, "lng": -79.0063, "state": "NC", "region": "southeast", "type": "base", "aliases": ["Fort Bragg", "Ft Liberty", "Fayetteville, NC", "JSOC"]},
    {"name": "Hill AFB", "lat": 41.1197, "lng": -111.9661, "state": "UT", "region": "west", "type": "base", "aliases": ["Hill, UT", "Ogden, UT", "Hill AFB, UT"]},
    {"name": "Offutt AFB", "lat": 41.1186, "lng": -95.9125, "state": "NE", "region": "midwest", "type": "base", "aliases": ["Offutt, NE", "Bellevue, NE", "STRATCOM"]},
    {"name": "Joint Base Pearl Harbor-Hickam", "lat": 21.3469, "lng": -157.9740, "state": "HI", "region": "west", "type": "base", "aliases": ["Pearl Harbor", "JBPHH", "Hickam AFB", "INDOPACOM"]},
    {"name": "Hanscom AFB", "lat": 42.4596, "lng": -71.2890, "state": "MA", "region": "northeast", "type": "base", "aliases": ["Hanscom, MA", "Bedford, MA"]},
    {"name": "Rome Lab", "lat": 43.2128, "lng": -75.4557, "state": "NY", "region": "northeast", "type": "lab", "aliases": ["Rome, NY", "AFRL Rome", "Griffiss"]},

    # === Major Defense Contractor HQs ===
    {"name": "Northrop Grumman HQ", "lat": 38.9308, "lng": -77.2333, "state": "VA", "region": "NCR", "type": "hq", "aliases": ["Northrop Falls Church"]},
    {"name": "Raytheon HQ", "lat": 38.8700, "lng": -77.0600, "state": "VA", "region": "NCR", "type": "hq", "aliases": ["Raytheon Arlington"]},
    {"name": "BAE Systems US", "lat": 38.9342, "lng": -77.1776, "state": "VA", "region": "NCR", "type": "hq", "aliases": ["BAE Falls Church"]},
    {"name": "Booz Allen HQ", "lat": 38.9210, "lng": -77.2340, "state": "VA", "region": "NCR", "type": "hq", "aliases": ["Booz Allen McLean"]},
    {"name": "SAIC HQ", "lat": 38.9570, "lng": -77.3530, "state": "VA", "region": "NCR", "type": "hq", "aliases": ["SAIC Reston"]},
    {"name": "Peraton HQ", "lat": 38.9520, "lng": -77.3480, "state": "VA", "region": "NCR", "type": "hq", "aliases": ["Peraton Reston"]},
    {"name": "ManTech HQ", "lat": 38.9230, "lng": -77.2370, "state": "VA", "region": "NCR", "type": "hq", "aliases": ["ManTech Fairfax"]},
    {"name": "L3Harris Melbourne", "lat": 28.0836, "lng": -80.6081, "state": "FL", "region": "southeast", "type": "hq", "aliases": ["L3Harris HQ", "Melbourne, FL"]},
    {"name": "Boeing St. Louis", "lat": 38.7482, "lng": -90.3596, "state": "MO", "region": "midwest", "type": "hq", "aliases": ["Boeing Defense", "St. Louis, MO"]},
    {"name": "Lockheed Martin Bethesda", "lat": 38.9906, "lng": -77.0958, "state": "MD", "region": "NCR", "type": "hq", "aliases": ["Lockheed HQ", "Bethesda, MD"]},
]

# Build lookup indexes
_FACILITY_BY_NAME: Dict[str, Dict[str, Any]] = {}
_FACILITY_BY_ALIAS: Dict[str, Dict[str, Any]] = {}

for _f in _FACILITIES:
    _FACILITY_BY_NAME[_f["name"].lower()] = _f
    for _alias in _f.get("aliases", []):
        _FACILITY_BY_ALIAS[_alias.lower()] = _f


# =========================================
# SIMULATED ENTITIES
# =========================================

_CONTACTS = [
    {"id": "c001", "name": "Craig Lindahl", "location": "Langley AFB, VA", "company": "Leidos", "program": "DCGS-A"},
    {"id": "c002", "name": "Sarah Mitchell", "location": "Hill AFB, UT", "company": "Northrop Grumman", "program": "GBSD"},
    {"id": "c003", "name": "James Patel", "location": "St. Inigoes, MD", "company": "Raytheon", "program": "DCGS-N"},
    {"id": "c004", "name": "Amanda Chen", "location": "Pentagon, VA", "company": "GDIT", "program": "JADC2"},
    {"id": "c005", "name": "Robert Hayes", "location": "Aberdeen, MD", "company": "US Army", "program": "DCGS-A"},
    {"id": "c006", "name": "Diana Torres", "location": "St. Louis, MO", "company": "Boeing", "program": "MQ-25"},
    {"id": "c007", "name": "Kevin Park", "location": "Colorado Springs, CO", "company": "Northrop Grumman", "program": "SBIRS"},
    {"id": "c008", "name": "Lisa Wang", "location": "Huntsville, AL", "company": "Raytheon", "program": "THAAD"},
    {"id": "c009", "name": "Marcus Johnson", "location": "San Diego, CA", "company": "GDIT", "program": "DCGS-N"},
    {"id": "c010", "name": "Priya Sharma", "location": "Fort Meade, MD", "company": "Peraton", "program": "NSA-SIGINT"},
]

_PROGRAM_LOCATIONS = [
    {"id": "prog_001", "name": "DCGS-A", "locations": ["Langley AFB, VA", "Fort Meade, MD", "Aberdeen, MD"]},
    {"id": "prog_002", "name": "DCGS-N", "locations": ["St. Inigoes, MD", "San Diego, CA", "Norfolk, VA"]},
    {"id": "prog_003", "name": "GBSD", "locations": ["Hill AFB, UT", "Vandenberg, CA"]},
    {"id": "prog_004", "name": "JADC2", "locations": ["Pentagon, VA", "Fort Meade, MD", "Colorado Springs, CO"]},
    {"id": "prog_005", "name": "MQ-25", "locations": ["St. Louis, MO", "Pax River, MD"]},
    {"id": "prog_006", "name": "ABMS", "locations": ["Hanscom, MA", "Wright-Patt", "Robins, GA"]},
    {"id": "prog_007", "name": "NGJ-MB", "locations": ["Point Mugu, CA", "China Lake, CA", "Pax River, MD"]},
    {"id": "prog_008", "name": "IVAS", "locations": ["Redstone Arsenal", "Aberdeen, MD", "Fort Liberty"]},
]

_JOB_LOCATIONS = [
    {"id": "job_001", "title": "Senior Cloud Architect", "location": "Langley AFB, VA", "program": "DCGS-A"},
    {"id": "job_002", "title": "Software Developer", "location": "Hill AFB, UT", "program": "GBSD"},
    {"id": "job_003", "title": "Kubernetes Engineer", "location": "St. Inigoes, MD", "program": "DCGS-N"},
    {"id": "job_004", "title": "Zero Trust Architect", "location": "Pentagon, VA", "program": "JADC2"},
    {"id": "job_005", "title": "Autonomy Engineer", "location": "St. Louis, MO", "program": "MQ-25"},
    {"id": "job_006", "title": "SIGINT Analyst", "location": "Langley AFB, VA", "program": "DCGS-A"},
    {"id": "job_007", "title": "RF Engineer", "location": "Point Mugu, CA", "program": "NGJ-MB"},
    {"id": "job_008", "title": "Data Scientist", "location": "Fort Meade, MD", "program": "JADC2"},
    {"id": "job_009", "title": "Systems Engineer", "location": "Huntsville, AL", "program": "IVAS"},
    {"id": "job_010", "title": "Cyber Analyst", "location": "Fort Eisenhower", "program": "CCoE"},
]


# =========================================
# GEOCODING ENGINE
# =========================================

class GeocodingEngine:
    """Geocode location strings to lat/lng using defense facility cache."""

    def __init__(self) -> None:
        self._cache: Dict[str, GeoPoint] = {}
        self._batch_results: Dict[str, BatchResult] = {}
        self._geocode_count: int = 0

        # Pre-populate cache from facilities
        for fac in _FACILITIES:
            point = GeoPoint(
                lat=fac["lat"], lng=fac["lng"], name=fac["name"],
                address=fac["name"] + ", " + fac["state"],
                facility_type=fac["type"], state=fac["state"],
                region=fac["region"], source="cache",
            )
            self._cache[fac["name"].lower()] = point
            for alias in fac.get("aliases", []):
                self._cache[alias.lower()] = point

    # --------------------------------------------------
    # GEOCODE SINGLE
    # --------------------------------------------------

    def geocode(self, location_text: str) -> Optional[GeoPoint]:
        """Geocode a location string. Returns GeoPoint or None."""
        if not location_text or not location_text.strip():
            return None

        self._geocode_count += 1
        text = location_text.strip()
        text_lower = text.lower()

        # 1) Exact cache hit
        if text_lower in self._cache:
            return self._cache[text_lower]

        # 2) Fuzzy match: check if any cache key is contained in the query
        for key, point in self._cache.items():
            if key in text_lower or text_lower in key:
                self._cache[text_lower] = point  # memoize
                return point

        # 3) Token-based fuzzy: split and match significant tokens
        tokens = set(re.split(r'[\s,/]+', text_lower))
        best_match: Optional[GeoPoint] = None
        best_score = 0

        for key, point in self._cache.items():
            key_tokens = set(re.split(r'[\s,/]+', key))
            overlap = len(tokens & key_tokens)
            if overlap > best_score and overlap >= 2:
                best_score = overlap
                best_match = point

        if best_match:
            self._cache[text_lower] = best_match
            return best_match

        # 4) State-based fallback: if we can extract a state
        state = self._extract_state(text)
        if state:
            state_facilities = [f for f in _FACILITIES if f["state"] == state]
            if state_facilities:
                fac = state_facilities[0]
                point = GeoPoint(
                    lat=fac["lat"], lng=fac["lng"], name=text,
                    address=text, facility_type="unknown", state=state,
                    region=fac["region"], source="fallback",
                )
                self._cache[text_lower] = point
                return point

        return None

    def _extract_state(self, text: str) -> str:
        """Extract US state abbreviation from text."""
        states = {
            "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
            "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
            "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
            "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
            "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC",
        }
        match = re.search(r'\b([A-Z]{2})\b', text)
        if match and match.group(1) in states:
            return match.group(1)
        return ""

    # --------------------------------------------------
    # GEOCODE ENTITY
    # --------------------------------------------------

    def geocode_entity(self, entity_id: str, entity_type: str,
                       entity_name: str, location_text: str) -> GeocodedEntity:
        """Geocode an entity and return enriched result."""
        geo = self.geocode(location_text)
        method = ""
        if geo:
            method = geo.source

        return GeocodedEntity(
            entity_id=entity_id, entity_type=entity_type,
            entity_name=entity_name, location_text=location_text,
            geo=geo, resolved=geo is not None, resolution_method=method,
        )

    # --------------------------------------------------
    # BATCH GEOCODE
    # --------------------------------------------------

    def batch_geocode_contacts(self) -> BatchResult:
        """Batch geocode all contacts."""
        import time
        start = time.time()
        entities: List[GeocodedEntity] = []
        for c in _CONTACTS:
            ge = self.geocode_entity(c["id"], "contact", c["name"], c["location"])
            entities.append(ge)

        result = BatchResult(
            total=len(entities),
            resolved=sum(1 for e in entities if e.resolved),
            failed=sum(1 for e in entities if not e.resolved),
            entities=entities,
            duration_sec=round(time.time() - start, 4),
        )
        self._batch_results[result.id] = result
        return result

    def batch_geocode_programs(self) -> BatchResult:
        """Batch geocode all program locations."""
        import time
        start = time.time()
        entities: List[GeocodedEntity] = []
        for prog in _PROGRAM_LOCATIONS:
            for loc in prog["locations"]:
                ge = self.geocode_entity(prog["id"], "program", prog["name"], loc)
                entities.append(ge)

        result = BatchResult(
            total=len(entities),
            resolved=sum(1 for e in entities if e.resolved),
            failed=sum(1 for e in entities if not e.resolved),
            entities=entities,
            duration_sec=round(time.time() - start, 4),
        )
        self._batch_results[result.id] = result
        return result

    def batch_geocode_jobs(self) -> BatchResult:
        """Batch geocode all job locations."""
        import time
        start = time.time()
        entities: List[GeocodedEntity] = []
        for job in _JOB_LOCATIONS:
            ge = self.geocode_entity(job["id"], "job", job["title"], job["location"])
            entities.append(ge)

        result = BatchResult(
            total=len(entities),
            resolved=sum(1 for e in entities if e.resolved),
            failed=sum(1 for e in entities if not e.resolved),
            entities=entities,
            duration_sec=round(time.time() - start, 4),
        )
        self._batch_results[result.id] = result
        return result

    def batch_geocode_all(self) -> Dict[str, BatchResult]:
        """Batch geocode contacts, programs, and jobs."""
        return {
            "contacts": self.batch_geocode_contacts(),
            "programs": self.batch_geocode_programs(),
            "jobs": self.batch_geocode_jobs(),
        }

    # --------------------------------------------------
    # FACILITIES & QUERIES
    # --------------------------------------------------

    def get_facilities(self, region: str = "", facility_type: str = "",
                       state: str = "") -> List[GeoPoint]:
        """Get defense facilities, optionally filtered."""
        results: List[GeoPoint] = []
        for fac in _FACILITIES:
            if region and fac["region"] != region:
                continue
            if facility_type and fac["type"] != facility_type:
                continue
            if state and fac["state"] != state:
                continue
            results.append(GeoPoint(
                lat=fac["lat"], lng=fac["lng"], name=fac["name"],
                address=fac["name"] + ", " + fac["state"],
                facility_type=fac["type"], state=fac["state"],
                region=fac["region"], source="cache",
            ))
        return results

    def get_facility(self, name: str) -> Optional[GeoPoint]:
        """Get a specific facility by name or alias."""
        return self.geocode(name)

    def get_regions(self) -> List[str]:
        """Get all unique regions."""
        return sorted(set(f["region"] for f in _FACILITIES))

    def get_stats(self) -> Dict[str, Any]:
        by_region: Dict[str, int] = {}
        by_type: Dict[str, int] = {}
        for fac in _FACILITIES:
            by_region[fac["region"]] = by_region.get(fac["region"], 0) + 1
            by_type[fac["type"]] = by_type.get(fac["type"], 0) + 1
        return {
            "total_facilities": len(_FACILITIES),
            "by_region": by_region,
            "by_type": by_type,
            "total_geocodes": self._geocode_count,
            "cache_size": len(self._cache),
            "total_batch_runs": len(self._batch_results),
        }


# =========================================
# SINGLETON
# =========================================

_instance: Optional[GeocodingEngine] = None


def get_geocoding_engine() -> GeocodingEngine:
    global _instance
    if _instance is None:
        _instance = GeocodingEngine()
    return _instance
