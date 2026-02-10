"""
Phase 21A — Graph Data Ingestion Engine

Bulk ingestion from existing data sources into Neo4j:
  1. Contacts → Person + WORKS_AT + LOCATED_IN
  2. Programs → Program + Company + PRIMES_ON + LOCATED_AT
  3. Jobs → Job + POSTED_BY + MAPPED_TO + JOB_AT
  4. Interactions → Interaction + BETWEEN + ABOUT
  5. Locations → Location nodes with coordinates

Uses MERGE for idempotency and batch processing (500 per tx).
"""

import csv
import json
import logging
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# Data source paths (relative to project root)
PROJECT_ROOT = Path(__file__).parent.parent.parent
BULLHORN_DB = PROJECT_ROOT / "Engine7_BullhornETL" / "data" / "bullhorn_master.db"
MASTER_NOTES = PROJECT_ROOT / "Engine7_BullhornETL" / "colton_scurry_analysis" / "master_notes.csv"
CONTACTS_CSV = PROJECT_ROOT / "Engine7_BullhornETL" / "colton_scurry_analysis" / "contacts.csv"
FEDERAL_PROGRAMS = PROJECT_ROOT / "data" / "from_data_scraper" / "Federal_Programs_Enriched.csv"

BATCH_SIZE = 500

# Known defense locations with coordinates
LOCATION_COORDS: dict[str, tuple[float, float]] = {
    "Fort Meade": (39.1086, -76.7711),
    "Fort Belvoir": (38.7119, -77.1448),
    "Langley": (38.9330, -77.1753),
    "Wright-Patterson": (39.8261, -84.0486),
    "San Diego": (32.7157, -117.1611),
    "Norfolk": (36.8508, -76.2859),
    "Tampa": (27.9506, -82.4572),
    "Colorado Springs": (38.8339, -104.8214),
    "Falls Church": (38.8826, -77.1712),
    "Herndon": (38.9696, -77.3861),
    "Springfield": (38.7893, -77.1872),
    "Reston": (38.9587, -77.3570),
    "Aberdeen": (39.5096, -76.1641),
    "Huntsville": (34.7304, -86.5861),
    "St. Louis": (38.6270, -90.1994),
    "Dayton": (39.7589, -84.1916),
    "Augusta": (33.4735, -82.0105),
    "Fort Bragg": (35.1392, -79.0064),
    "Fort Hood": (31.1370, -97.7755),
    "Peterson": (38.8011, -104.7030),
    "Schriever": (38.8055, -104.5280),
    "Buckley": (39.7083, -104.7561),
    "Shaw": (33.9728, -80.4737),
    "Beale": (39.1361, -121.4364),
    "Creech": (36.5822, -115.6711),
    "Fort Gordon": (33.4206, -82.1548),
    "Joint Base Andrews": (38.8108, -76.8670),
    "Arlington": (38.8799, -77.1068),
    "McLean": (38.9343, -77.1773),
    "Chantilly": (38.8943, -77.4311),
}


# ---------------------------------------------------------------------------
# GraphIngestionEngine
# ---------------------------------------------------------------------------

class GraphIngestionEngine:
    """Bulk data ingestion from BD platform sources into Neo4j."""

    def __init__(self, manager: "Neo4jManager") -> None:
        from Engine8_Knowledge.graph.neo4j_manager import Neo4jManager
        self._mgr = manager
        self._stats: dict[str, int] = {}

    def _reset_stats(self) -> None:
        self._stats = {
            "persons": 0, "companies": 0, "programs": 0,
            "jobs": 0, "locations": 0, "interactions": 0,
            "relationships": 0, "errors": 0, "skipped": 0,
        }

    # ── 1. Contacts ──────────────────────────────────────

    def ingest_contacts(self, limit: Optional[int] = None) -> dict:
        """Ingest contacts from CSV into Person nodes."""
        self._reset_stats()
        contacts = self._load_contacts_csv(limit)
        if not contacts:
            return {"status": "no_data", "source": str(CONTACTS_CSV)}

        # Batch MERGE persons
        person_cypher = """
        UNWIND $batch AS row
        MERGE (p:Person {email: coalesce(row.email, row.name + '@unknown.com')})
        SET p.name = row.name,
            p.title = row.title,
            p.company = row.company,
            p.tier = toInteger(row.tier),
            p.bd_priority = row.bd_priority,
            p.phone = row.phone,
            p.linkedin = row.linkedin,
            p.program = row.program,
            p.source_db = row.source_db,
            p.location_hub = row.location
        WITH p, row
        WHERE row.company IS NOT NULL AND row.company <> ''
        MERGE (c:Company {name: row.company})
        MERGE (p)-[:WORKS_AT]->(c)
        """
        result = self._mgr.run_batch(person_cypher, contacts, BATCH_SIZE)
        self._stats["persons"] = result.get("nodes_created", 0)
        self._stats["relationships"] = result.get("relationships_created", 0)

        logger.info("contacts_ingested", count=len(contacts), **self._stats)
        return {"status": "completed", "ingested": len(contacts), **self._stats}

    def _load_contacts_csv(self, limit: Optional[int] = None) -> list[dict]:
        """Load contacts from CSV."""
        if not CONTACTS_CSV.exists():
            logger.warning("contacts_csv_not_found", path=str(CONTACTS_CSV))
            return []
        contacts = []
        try:
            with open(CONTACTS_CSV, "r", encoding="utf-8", errors="replace") as f:
                reader = csv.DictReader(f)
                for i, row in enumerate(reader):
                    if limit and i >= limit:
                        break
                    contacts.append({
                        "name": (row.get("name") or row.get("Name") or "").strip(),
                        "title": (row.get("title") or row.get("Title") or "").strip(),
                        "email": (row.get("email") or row.get("Email") or "").strip(),
                        "phone": (row.get("phone") or row.get("Phone") or "").strip(),
                        "company": (row.get("company") or row.get("Company") or "").strip(),
                        "linkedin": (row.get("linkedin") or row.get("LinkedIn") or "").strip(),
                        "program": (row.get("program") or row.get("Program") or "").strip(),
                        "tier": row.get("tier") or row.get("Tier") or "5",
                        "bd_priority": (row.get("bd_priority") or row.get("BD Priority") or "").strip(),
                        "source_db": (row.get("source_db") or row.get("Source") or "csv").strip(),
                        "location": (row.get("location") or row.get("Location") or "").strip(),
                    })
        except Exception as e:
            logger.error("contacts_csv_error", error=str(e))
        return contacts

    # ── 2. Programs ──────────────────────────────────────

    def ingest_programs(self, limit: Optional[int] = None) -> dict:
        """Ingest federal programs from CSV."""
        self._reset_stats()
        programs = self._load_programs_csv(limit)
        if not programs:
            return {"status": "no_data", "source": str(FEDERAL_PROGRAMS)}

        program_cypher = """
        UNWIND $batch AS row
        MERGE (pr:Program {acronym: coalesce(row.acronym, row.name)})
        SET pr.name = row.name,
            pr.value = row.value,
            pr.agency_owner = row.agency_owner,
            pr.prime_contractor = row.prime_contractor,
            pr.clearance_req = row.clearance_req,
            pr.program_type = row.program_type,
            pr.contract_vehicle = row.contract_vehicle,
            pr.hiring_velocity = row.hiring_velocity,
            pr.recompete_date = row.recompete_date,
            pr.confidence_level = row.confidence_level
        WITH pr, row
        WHERE row.prime_contractor IS NOT NULL AND row.prime_contractor <> ''
        MERGE (c:Company {name: row.prime_contractor})
        SET c.is_defense_prime = true
        MERGE (c)-[:PRIMES_ON]->(pr)
        """
        result = self._mgr.run_batch(program_cypher, programs, BATCH_SIZE)
        self._stats["programs"] = result.get("nodes_created", 0)
        self._stats["relationships"] = result.get("relationships_created", 0)

        # Ingest subcontractors
        for prog in programs:
            subs = prog.get("subcontractors", "")
            if subs:
                for sub_name in [s.strip() for s in subs.split(",") if s.strip()]:
                    try:
                        self._mgr.write_query(
                            """
                            MATCH (pr:Program {acronym: $acronym})
                            MERGE (sub:Company {name: $sub_name})
                            MERGE (sub)-[:SUBS_TO {on_program: $program}]->(pr)
                            """,
                            {"acronym": prog.get("acronym", prog["name"]), "sub_name": sub_name, "program": prog["name"]},
                        )
                    except Exception:
                        self._stats["errors"] += 1

        logger.info("programs_ingested", count=len(programs), **self._stats)
        return {"status": "completed", "ingested": len(programs), **self._stats}

    def _load_programs_csv(self, limit: Optional[int] = None) -> list[dict]:
        """Load federal programs from CSV."""
        if not FEDERAL_PROGRAMS.exists():
            logger.warning("programs_csv_not_found", path=str(FEDERAL_PROGRAMS))
            return []
        programs = []
        try:
            with open(FEDERAL_PROGRAMS, "r", encoding="utf-8", errors="replace") as f:
                reader = csv.DictReader(f)
                for i, row in enumerate(reader):
                    if limit and i >= limit:
                        break
                    programs.append({
                        "name": (row.get("Program Name") or "").strip(),
                        "acronym": (row.get("Acronym") or row.get("Program Name", "")).strip(),
                        "value": (row.get("Contract Value") or "").strip(),
                        "agency_owner": (row.get("Agency Owner") or "").strip(),
                        "prime_contractor": (row.get("Prime Contractor") or "").strip(),
                        "clearance_req": (row.get("Clearance Requirements") or "").strip(),
                        "program_type": (row.get("Program Type") or "").strip(),
                        "contract_vehicle": (row.get("Contract Vehicle") or "").strip(),
                        "hiring_velocity": (row.get("Hiring Velocity") or "").strip(),
                        "recompete_date": (row.get("Recompete Date") or "").strip(),
                        "confidence_level": (row.get("Confidence Level") or "").strip(),
                        "subcontractors": (row.get("Known Subcontractors") or "").strip(),
                    })
        except Exception as e:
            logger.error("programs_csv_error", error=str(e))
        return programs

    # ── 3. Jobs ──────────────────────────────────────────

    def ingest_jobs(self, limit: Optional[int] = None) -> dict:
        """Ingest jobs from API or Qdrant."""
        self._reset_stats()

        # Try loading from the Hub API
        jobs = self._load_jobs_from_api(limit)
        if not jobs:
            return {"status": "no_data", "note": "Start Hub API to ingest jobs"}

        job_cypher = """
        UNWIND $batch AS row
        MERGE (j:Job {title: row.title, date_added: coalesce(row.date_added, '')})
        SET j.status = row.status,
            j.clearance = row.clearance,
            j.location = row.location,
            j.source_url = row.source_url,
            j.bd_priority = row.bd_priority,
            j.functional_area = row.functional_area
        WITH j, row
        WHERE row.company IS NOT NULL AND row.company <> ''
        MERGE (c:Company {name: row.company})
        MERGE (j)-[:POSTED_BY]->(c)
        WITH j, row
        WHERE row.program IS NOT NULL AND row.program <> ''
        MERGE (pr:Program {acronym: row.program})
        MERGE (j)-[:MAPPED_TO]->(pr)
        """
        result = self._mgr.run_batch(job_cypher, jobs, BATCH_SIZE)
        self._stats["jobs"] = result.get("nodes_created", 0)
        self._stats["relationships"] = result.get("relationships_created", 0)

        logger.info("jobs_ingested", count=len(jobs), **self._stats)
        return {"status": "completed", "ingested": len(jobs), **self._stats}

    def _load_jobs_from_api(self, limit: Optional[int] = None) -> list[dict]:
        """Load jobs from the Hub API."""
        try:
            import httpx
            r = httpx.get(
                "http://127.0.0.1:8100/api/v2/jobs",
                params={"limit": limit or 1000},
                timeout=15,
            )
            if r.status_code == 200:
                data = r.json()
                jobs_raw = data.get("jobs", [])
                return [
                    {
                        "title": j.get("title", ""),
                        "status": j.get("status", ""),
                        "clearance": j.get("clearance", ""),
                        "location": j.get("location", ""),
                        "company": j.get("company", ""),
                        "program": j.get("program", j.get("program_name", "")),
                        "source_url": j.get("source_url", ""),
                        "bd_priority": str(j.get("bd_priority", "")),
                        "functional_area": j.get("functional_area", ""),
                        "date_added": j.get("scraped_at", ""),
                    }
                    for j in jobs_raw
                ]
        except Exception as e:
            logger.warning("jobs_api_unavailable", error=str(e)[:100])
        return []

    # ── 4. Interactions ──────────────────────────────────

    def ingest_interactions(self, limit: Optional[int] = None) -> dict:
        """Ingest call notes / interactions from master_notes.csv."""
        self._reset_stats()
        interactions = self._load_interactions_csv(limit)
        if not interactions:
            return {"status": "no_data", "source": str(MASTER_NOTES)}

        interaction_cypher = """
        UNWIND $batch AS row
        CREATE (i:Interaction {
            date: row.date,
            type: row.type,
            action: row.action,
            status: row.status,
            summary: left(row.summary, 500),
            author: row.author
        })
        WITH i, row
        WHERE row.about IS NOT NULL AND row.about <> ''
        MERGE (p:Person {name: row.about})
        MERGE (i)-[:BETWEEN]->(p)
        WITH i, row
        WHERE row.author IS NOT NULL AND row.author <> ''
        MERGE (author:Person {name: row.author})
        MERGE (i)-[:BY_USER]->(author)
        """
        result = self._mgr.run_batch(interaction_cypher, interactions, BATCH_SIZE)
        self._stats["interactions"] = result.get("nodes_created", 0)
        self._stats["relationships"] = result.get("relationships_created", 0)

        logger.info("interactions_ingested", count=len(interactions), **self._stats)
        return {"status": "completed", "ingested": len(interactions), **self._stats}

    def _load_interactions_csv(self, limit: Optional[int] = None) -> list[dict]:
        """Load interactions from master_notes.csv."""
        if not MASTER_NOTES.exists():
            logger.warning("master_notes_not_found", path=str(MASTER_NOTES))
            return []
        interactions = []
        try:
            with open(MASTER_NOTES, "r", encoding="utf-8", errors="replace") as f:
                reader = csv.DictReader(f)
                for i, row in enumerate(reader):
                    if limit and i >= limit:
                        break
                    interactions.append({
                        "date": (row.get("date_added") or "").strip(),
                        "type": (row.get("type") or "note").strip(),
                        "action": (row.get("action") or "").strip(),
                        "status": (row.get("status") or "").strip(),
                        "summary": (row.get("note_body_clean") or row.get("note_body_raw") or "").strip()[:500],
                        "about": (row.get("about") or "").strip(),
                        "author": (row.get("note_author") or "").strip(),
                    })
        except Exception as e:
            logger.error("interactions_csv_error", error=str(e))
        return interactions

    # ── 5. Locations ─────────────────────────────────────

    def ingest_locations(self) -> dict:
        """Create Location nodes from known defense locations."""
        self._reset_stats()

        location_cypher = """
        UNWIND $batch AS row
        MERGE (l:Location {hub_name: row.hub_name})
        SET l.city = row.city,
            l.state = row.state,
            l.coordinates_lat = row.lat,
            l.coordinates_lon = row.lon,
            l.military_installation = row.military
        """
        locations = []
        for name, (lat, lon) in LOCATION_COORDS.items():
            # Parse city/state from name
            city = name
            state = ""
            locations.append({
                "hub_name": name,
                "city": city,
                "state": state,
                "lat": lat,
                "lon": lon,
                "military": name.startswith("Fort") or name in ("Shaw", "Beale", "Creech", "Peterson", "Schriever", "Buckley"),
            })

        result = self._mgr.run_batch(location_cypher, locations, BATCH_SIZE)
        self._stats["locations"] = result.get("nodes_created", 0)

        logger.info("locations_ingested", count=len(locations), **self._stats)
        return {"status": "completed", "ingested": len(locations), **self._stats}

    # ── Full rebuild ─────────────────────────────────────

    def ingest_all(self, limit: Optional[int] = None) -> dict:
        """Run full graph ingestion from all sources."""
        started = datetime.now()
        results = {
            "locations": self.ingest_locations(),
            "contacts": self.ingest_contacts(limit),
            "programs": self.ingest_programs(limit),
            "jobs": self.ingest_jobs(limit),
            "interactions": self.ingest_interactions(limit),
        }
        elapsed = (datetime.now() - started).total_seconds()
        results["elapsed_sec"] = round(elapsed, 1)
        results["timestamp"] = datetime.now().isoformat()
        logger.info("full_ingestion_complete", elapsed_sec=elapsed)
        return results
