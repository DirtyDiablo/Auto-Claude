"""
BD Knowledge Graph - Graph database for BD relationship modeling.
Tracks relationships between contractors, programs, contacts, jobs, skills, and locations.
"""

import os
import sys
import json
import sqlite3
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add parent path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


# =========================================
# ENTITY & RELATIONSHIP DEFINITIONS
# =========================================

ENTITY_TYPES = {
    "Contractor": ["name", "type", "uei", "cage_code", "size", "headquarters"],
    "Program": ["name", "acronym", "agency", "prime", "value", "status", "clearance"],
    "Contact": ["name", "title", "company", "tier", "priority", "clearance", "email"],
    "Job": ["title", "location", "clearance", "program", "company", "bd_score"],
    "Skill": ["name", "category", "clearance_level", "demand_level"],
    "Location": ["city", "state", "base_name", "region"],
    "Meeting": ["title", "date", "attendees", "program", "notes"],
    "Placement": ["candidate", "job_title", "prime_contractor", "start_date", "status"],
}

RELATIONSHIP_TYPES = {
    # Contractor relationships
    "PRIMES_ON": ("Contractor", "Program"),  # GDIT primes on DCGS-A
    "SUBS_TO": ("Contractor", "Contractor"),  # PTS subs to GDIT
    "COMPETES_WITH": ("Contractor", "Contractor"),  # GDIT competes with Leidos
    "PARTNERS_WITH": ("Contractor", "Contractor"),  # Strategic partnership
    "HAS_PAST_PERF": ("Contractor", "Program"),  # PTS has past perf on BICES
    # Contact relationships
    "WORKS_ON": ("Contact", "Program"),  # John works on AF DCGS
    "WORKS_FOR": ("Contact", "Contractor"),  # John works for GDIT
    "MANAGES": ("Contact", "Contact"),  # Mary manages John
    "KNOWS": ("Contact", "Contact"),  # Professional connection
    "DECISION_MAKER_FOR": ("Contact", "Program"),  # Key decision maker
    # Job relationships
    "HAS_OPENING": ("Program", "Job"),  # AF DCGS has network engineer opening
    "POSTED_BY": ("Contractor", "Job"),  # GDIT posted job
    "REQUIRES": ("Job", "Skill"),  # Job requires TS/SCI
    # Location relationships
    "LOCATED_AT": ("Program", "Location"),  # AF DCGS located at Langley
    "HEADQUARTERED_AT": ("Contractor", "Location"),  # GDIT HQ in Falls Church
    "WORKS_AT": ("Contact", "Location"),  # Contact works at Langley
    # Skill relationships
    "REQUIRES_SKILL": ("Program", "Skill"),  # Program requires skill
    "HAS_SKILL": ("Contact", "Skill"),  # Contact has skill
    # Placement & Meeting relationships
    "PLACED_BY_PTS": ("Placement", "Contractor"),  # PTS placed candidate at contractor
    "ATTENDED": ("Contact", "Meeting"),  # Contact attended meeting
    "ABOUT_PROGRAM": ("Meeting", "Program"),  # Meeting was about a program
}


@dataclass
class Entity:
    """Represents a node in the knowledge graph."""

    id: str
    type: str
    name: str
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "properties": self.properties,
            "created_at": self.created_at,
        }


@dataclass
class Relationship:
    """Represents an edge in the knowledge graph."""

    id: str
    type: str
    from_entity_id: str
    to_entity_id: str
    properties: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    source: str = "manual"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.type,
            "from_entity_id": self.from_entity_id,
            "to_entity_id": self.to_entity_id,
            "properties": self.properties,
            "confidence": self.confidence,
            "source": self.source,
            "created_at": self.created_at,
        }


# =========================================
# KNOWLEDGE GRAPH IMPLEMENTATION
# =========================================


class BDKnowledgeGraph:
    """
    Graph database for BD relationship modeling.
    Uses SQLite for persistence with in-memory caching for performance.
    """

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "data", "bd_graph.db"
            )

        self.db_path = db_path
        Path(os.path.dirname(db_path)).mkdir(parents=True, exist_ok=True)

        self.conn = None
        self._entity_cache: Dict[str, Entity] = {}
        self._adjacency: Dict[
            str, Set[str]
        ] = {}  # entity_id -> set of connected entity_ids

        self._init_database()
        self._load_cache()

        logger.info(f"BD Knowledge Graph initialized at {db_path}")

    def _init_database(self):
        """Initialize SQLite database schema."""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)

        # Entities table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS entities (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                name TEXT NOT NULL,
                properties TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Relationships table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS relationships (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                from_entity_id TEXT NOT NULL,
                to_entity_id TEXT NOT NULL,
                properties TEXT,
                confidence REAL DEFAULT 1.0,
                source TEXT DEFAULT 'manual',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (from_entity_id) REFERENCES entities(id),
                FOREIGN KEY (to_entity_id) REFERENCES entities(id)
            )
        """)

        # Indexes for common queries
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(type)"
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name)"
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_rel_type ON relationships(type)"
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_rel_from ON relationships(from_entity_id)"
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_rel_to ON relationships(to_entity_id)"
        )

        self.conn.commit()

    def _load_cache(self):
        """Load entities into cache for fast lookup."""
        cursor = self.conn.execute(
            "SELECT id, type, name, properties, created_at FROM entities"
        )
        for row in cursor:
            entity = Entity(
                id=row[0],
                type=row[1],
                name=row[2],
                properties=json.loads(row[3]) if row[3] else {},
                created_at=row[4],
            )
            self._entity_cache[entity.id] = entity

        # Build adjacency list
        cursor = self.conn.execute(
            "SELECT from_entity_id, to_entity_id FROM relationships"
        )
        for row in cursor:
            if row[0] not in self._adjacency:
                self._adjacency[row[0]] = set()
            if row[1] not in self._adjacency:
                self._adjacency[row[1]] = set()
            self._adjacency[row[0]].add(row[1])
            self._adjacency[row[1]].add(row[0])

        logger.info(f"Loaded {len(self._entity_cache)} entities into cache")

    # =========================================
    # ENTITY OPERATIONS
    # =========================================

    def add_entity(
        self,
        entity_type: str,
        name: str,
        properties: Dict = None,
        entity_id: str = None,
    ) -> Entity:
        """
        Add an entity to the graph.

        Args:
            entity_type: One of ENTITY_TYPES keys
            name: Display name
            properties: Additional properties dict
            entity_id: Optional custom ID (auto-generated if not provided)

        Returns:
            Created Entity
        """
        if entity_type not in ENTITY_TYPES:
            raise ValueError(
                f"Unknown entity type: {entity_type}. Valid: {list(ENTITY_TYPES.keys())}"
            )

        # Generate ID if not provided
        if not entity_id:
            import hashlib

            hash_input = f"{entity_type}:{name}".lower()
            entity_id = hashlib.md5(hash_input.encode()).hexdigest()[:12]

        # Check if exists
        if entity_id in self._entity_cache:
            # Update properties
            existing = self._entity_cache[entity_id]
            if properties:
                existing.properties.update(properties)
                self.conn.execute(
                    "UPDATE entities SET properties = ? WHERE id = ?",
                    (json.dumps(existing.properties), entity_id),
                )
                self.conn.commit()
            return existing

        entity = Entity(
            id=entity_id, type=entity_type, name=name, properties=properties or {}
        )

        self.conn.execute(
            "INSERT INTO entities (id, type, name, properties, created_at) VALUES (?, ?, ?, ?, ?)",
            (
                entity.id,
                entity.type,
                entity.name,
                json.dumps(entity.properties),
                entity.created_at,
            ),
        )
        self.conn.commit()

        self._entity_cache[entity.id] = entity
        return entity

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get entity by ID."""
        return self._entity_cache.get(entity_id)

    def find_entity(self, name: str, entity_type: str = None) -> Optional[Entity]:
        """Find entity by name (case-insensitive)."""
        name_lower = name.lower()
        for entity in self._entity_cache.values():
            if entity.name.lower() == name_lower:
                if entity_type is None or entity.type == entity_type:
                    return entity
        return None

    def search_entities(
        self, query: str, entity_type: str = None, limit: int = 10
    ) -> List[Entity]:
        """Search entities by name (partial match)."""
        query_lower = query.lower()
        results = []

        for entity in self._entity_cache.values():
            if query_lower in entity.name.lower():
                if entity_type is None or entity.type == entity_type:
                    results.append(entity)
                    if len(results) >= limit:
                        break

        return results

    def get_entities_by_type(self, entity_type: str) -> List[Entity]:
        """Get all entities of a specific type."""
        return [e for e in self._entity_cache.values() if e.type == entity_type]

    # =========================================
    # RELATIONSHIP OPERATIONS
    # =========================================

    def add_relationship(
        self,
        from_entity: str,
        rel_type: str,
        to_entity: str,
        properties: Dict = None,
        confidence: float = 1.0,
        source: str = "manual",
    ) -> Relationship:
        """
        Add a relationship between entities.

        Args:
            from_entity: ID or name of source entity
            rel_type: One of RELATIONSHIP_TYPES keys
            to_entity: ID or name of target entity
            properties: Additional properties
            confidence: Confidence score (0-1)
            source: Source of this relationship

        Returns:
            Created Relationship
        """
        if rel_type not in RELATIONSHIP_TYPES:
            raise ValueError(f"Unknown relationship type: {rel_type}")

        # Resolve entity IDs
        from_id = self._resolve_entity_id(from_entity)
        to_id = self._resolve_entity_id(to_entity)

        if not from_id or not to_id:
            raise ValueError(
                f"Could not resolve entities: {from_entity} -> {to_entity}"
            )

        # Generate relationship ID
        import hashlib

        rel_id = hashlib.md5(f"{from_id}:{rel_type}:{to_id}".encode()).hexdigest()[:12]

        # Check if exists
        cursor = self.conn.execute(
            "SELECT id FROM relationships WHERE id = ?", (rel_id,)
        )
        if cursor.fetchone():
            # Update confidence
            self.conn.execute(
                "UPDATE relationships SET confidence = ?, properties = ? WHERE id = ?",
                (confidence, json.dumps(properties or {}), rel_id),
            )
            self.conn.commit()
            return Relationship(
                id=rel_id,
                type=rel_type,
                from_entity_id=from_id,
                to_entity_id=to_id,
                properties=properties or {},
                confidence=confidence,
                source=source,
            )

        rel = Relationship(
            id=rel_id,
            type=rel_type,
            from_entity_id=from_id,
            to_entity_id=to_id,
            properties=properties or {},
            confidence=confidence,
            source=source,
        )

        self.conn.execute(
            """INSERT INTO relationships
               (id, type, from_entity_id, to_entity_id, properties, confidence, source, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                rel.id,
                rel.type,
                rel.from_entity_id,
                rel.to_entity_id,
                json.dumps(rel.properties),
                rel.confidence,
                rel.source,
                rel.created_at,
            ),
        )
        self.conn.commit()

        # Update adjacency
        if from_id not in self._adjacency:
            self._adjacency[from_id] = set()
        if to_id not in self._adjacency:
            self._adjacency[to_id] = set()
        self._adjacency[from_id].add(to_id)
        self._adjacency[to_id].add(from_id)

        return rel

    def _resolve_entity_id(self, entity_ref: str) -> Optional[str]:
        """Resolve entity reference (ID or name) to ID."""
        if entity_ref in self._entity_cache:
            return entity_ref

        entity = self.find_entity(entity_ref)
        return entity.id if entity else None

    def get_relationships(
        self, entity_id: str, rel_type: str = None, direction: str = "both"
    ) -> List[Relationship]:
        """
        Get relationships for an entity.

        Args:
            entity_id: Entity ID
            rel_type: Filter by relationship type
            direction: "outgoing", "incoming", or "both"

        Returns:
            List of Relationships
        """
        relationships = []

        sql_parts = []
        params = []

        if direction in ["outgoing", "both"]:
            sql_parts.append("from_entity_id = ?")
            params.append(entity_id)

        if direction in ["incoming", "both"]:
            if sql_parts:
                sql_parts[-1] = f"({sql_parts[-1]} OR to_entity_id = ?)"
                params.append(entity_id)
            else:
                sql_parts.append("to_entity_id = ?")
                params.append(entity_id)

        sql = f"SELECT * FROM relationships WHERE {' AND '.join(sql_parts)}"

        if rel_type:
            sql += " AND type = ?"
            params.append(rel_type)

        cursor = self.conn.execute(sql, params)
        for row in cursor:
            rel = Relationship(
                id=row[0],
                type=row[1],
                from_entity_id=row[2],
                to_entity_id=row[3],
                properties=json.loads(row[4]) if row[4] else {},
                confidence=row[5],
                source=row[6],
                created_at=row[7],
            )
            relationships.append(rel)

        return relationships

    # =========================================
    # GRAPH QUERIES
    # =========================================

    def query(self, natural_language_query: str) -> List[Dict]:
        """
        Query the graph using natural language.
        Parses the query and routes to appropriate method.
        """
        query_lower = natural_language_query.lower()

        # Pattern: "Who works on <program>?"
        if "who works on" in query_lower:
            program_name = query_lower.split("who works on")[-1].strip().rstrip("?")
            return self.get_program_contacts(program_name)

        # Pattern: "What programs does <contractor> prime on?"
        if "programs" in query_lower and (
            "prime" in query_lower or "work" in query_lower
        ):
            for entity in self._entity_cache.values():
                if entity.type == "Contractor" and entity.name.lower() in query_lower:
                    return self.get_contractor_programs(entity.name)

        # Pattern: "Who is the prime on <program>?"
        if "prime on" in query_lower or "prime for" in query_lower:
            for entity in self._entity_cache.values():
                if entity.type == "Program" and entity.name.lower() in query_lower:
                    return self.get_program_primes(entity.name)

        # Pattern: "<contractor> teaming with <contractor>"
        if "teaming" in query_lower or "partner" in query_lower:
            contractors = [
                e
                for e in self._entity_cache.values()
                if e.type == "Contractor" and e.name.lower() in query_lower
            ]
            if len(contractors) >= 2:
                return self.find_teaming_path(contractors[0].name, contractors[1].name)

        # Default: search all relevant entities
        return self.search_entities(natural_language_query, limit=10)

    def get_program_ecosystem(self, program_name: str) -> Dict:
        """
        Get the full ecosystem around a program.
        Includes: primes, subs, contacts, jobs, locations.
        """
        program = self.find_entity(program_name, "Program")
        if not program:
            return {"error": f"Program not found: {program_name}"}

        relationships = self.get_relationships(program.id)

        ecosystem = {
            "program": program.to_dict(),
            "primes": [],
            "subcontractors": [],
            "contacts": [],
            "jobs": [],
            "locations": [],
            "skills_required": [],
        }

        for rel in relationships:
            other_id = (
                rel.to_entity_id
                if rel.from_entity_id == program.id
                else rel.from_entity_id
            )
            other = self.get_entity(other_id)
            if not other:
                continue

            if rel.type == "PRIMES_ON" and other.type == "Contractor":
                ecosystem["primes"].append(other.to_dict())
            elif rel.type == "HAS_PAST_PERF" and other.type == "Contractor":
                ecosystem["subcontractors"].append(other.to_dict())
            elif rel.type == "WORKS_ON" and other.type == "Contact":
                ecosystem["contacts"].append(other.to_dict())
            elif rel.type == "HAS_OPENING" and other.type == "Job":
                ecosystem["jobs"].append(other.to_dict())
            elif rel.type == "LOCATED_AT" and other.type == "Location":
                ecosystem["locations"].append(other.to_dict())
            elif rel.type == "REQUIRES_SKILL" and other.type == "Skill":
                ecosystem["skills_required"].append(other.to_dict())

        return ecosystem

    def find_teaming_path(
        self, from_contractor: str, to_program: str, max_depth: int = 4
    ) -> List[Dict]:
        """
        Find a path from a contractor to a program through teaming relationships.
        Uses BFS to find shortest path.
        """
        from_entity = self.find_entity(from_contractor, "Contractor")
        to_entity = self.find_entity(to_program)

        if not from_entity:
            return [{"error": f"Contractor not found: {from_contractor}"}]
        if not to_entity:
            return [{"error": f"Entity not found: {to_program}"}]

        # BFS for shortest path
        from collections import deque

        queue = deque([(from_entity.id, [from_entity.to_dict()])])
        visited = {from_entity.id}

        while queue:
            current_id, path = queue.popleft()

            if current_id == to_entity.id:
                return path

            if len(path) >= max_depth:
                continue

            # Get all connected entities
            for rel in self.get_relationships(current_id):
                next_id = (
                    rel.to_entity_id
                    if rel.from_entity_id == current_id
                    else rel.from_entity_id
                )

                if next_id not in visited:
                    visited.add(next_id)
                    next_entity = self.get_entity(next_id)
                    if next_entity:
                        new_path = path + [
                            {"relationship": rel.type, "entity": next_entity.to_dict()}
                        ]
                        queue.append((next_id, new_path))

        return [{"error": "No path found", "from": from_contractor, "to": to_program}]

    def get_contact_network(self, contact_name: str) -> Dict:
        """
        Get a contact's professional network.
        Includes: company, programs, managers, direct reports, connections.
        """
        contact = self.find_entity(contact_name, "Contact")
        if not contact:
            return {"error": f"Contact not found: {contact_name}"}

        relationships = self.get_relationships(contact.id)

        network = {
            "contact": contact.to_dict(),
            "employer": None,
            "programs": [],
            "manages": [],
            "managed_by": [],
            "connections": [],
            "skills": [],
        }

        for rel in relationships:
            other_id = (
                rel.to_entity_id
                if rel.from_entity_id == contact.id
                else rel.from_entity_id
            )
            other = self.get_entity(other_id)
            if not other:
                continue

            if rel.type == "WORKS_FOR" and other.type == "Contractor":
                network["employer"] = other.to_dict()
            elif rel.type == "WORKS_ON" and other.type == "Program":
                network["programs"].append(other.to_dict())
            elif rel.type == "MANAGES":
                if rel.from_entity_id == contact.id:
                    network["manages"].append(other.to_dict())
                else:
                    network["managed_by"].append(other.to_dict())
            elif rel.type == "KNOWS" and other.type == "Contact":
                network["connections"].append(other.to_dict())
            elif rel.type == "HAS_SKILL" and other.type == "Skill":
                network["skills"].append(other.to_dict())

        return network

    def get_program_contacts(self, program_name: str) -> List[Dict]:
        """Get all contacts associated with a program."""
        program = self.find_entity(program_name, "Program")
        if not program:
            return []

        contacts = []
        relationships = self.get_relationships(program.id, rel_type="WORKS_ON")

        for rel in relationships:
            contact_id = rel.from_entity_id  # WORKS_ON: Contact -> Program
            contact = self.get_entity(contact_id)
            if contact and contact.type == "Contact":
                contacts.append(
                    {
                        "contact": contact.to_dict(),
                        "role": rel.properties.get("role", "Unknown"),
                        "confidence": rel.confidence,
                    }
                )

        return contacts

    def get_contractor_programs(self, contractor_name: str) -> List[Dict]:
        """Get all programs a contractor is involved with."""
        contractor = self.find_entity(contractor_name, "Contractor")
        if not contractor:
            return []

        programs = []

        for rel in self.get_relationships(contractor.id):
            if rel.type in ["PRIMES_ON", "HAS_PAST_PERF"]:
                program_id = rel.to_entity_id
                program = self.get_entity(program_id)
                if program and program.type == "Program":
                    programs.append(
                        {
                            "program": program.to_dict(),
                            "relationship": rel.type,
                            "confidence": rel.confidence,
                        }
                    )

        return programs

    def get_program_primes(self, program_name: str) -> List[Dict]:
        """Get prime contractors for a program."""
        program = self.find_entity(program_name, "Program")
        if not program:
            return []

        primes = []
        relationships = self.get_relationships(program.id, rel_type="PRIMES_ON")

        for rel in relationships:
            contractor = self.get_entity(rel.from_entity_id)
            if contractor and contractor.type == "Contractor":
                primes.append(
                    {"contractor": contractor.to_dict(), "confidence": rel.confidence}
                )

        return primes

    # =========================================
    # DATA POPULATION
    # =========================================

    def populate_from_vector_store(self, vector_store):
        """
        Populate graph from existing vector store collections.
        Infers relationships from data fields.
        """
        logger.info("Populating graph from vector store...")

        # Populate programs
        try:
            programs = vector_store.get_all("programs", limit=500)
            for p in programs:
                payload = p.payload if hasattr(p, "payload") else p
                self.add_entity(
                    "Program",
                    payload.get("name", payload.get("program_name", "Unknown")),
                    {
                        "acronym": payload.get("acronym", ""),
                        "agency": payload.get("agency", ""),
                        "prime": payload.get("prime", ""),
                        "value": payload.get(
                            "value", payload.get("contract_value", "")
                        ),
                        "status": payload.get("status", ""),
                        "clearance": payload.get("clearance", ""),
                    },
                )
            logger.info(f"Added {len(programs)} programs")
        except Exception as e:
            logger.warning(f"Error loading programs: {e}")

        # Populate contacts
        try:
            contacts = vector_store.get_all("contacts", limit=8000)
            for c in contacts:
                payload = c.payload if hasattr(c, "payload") else c
                name = payload.get("name", payload.get("full_name", "Unknown"))
                company = payload.get("company", payload.get("employer", ""))

                contact = self.add_entity(
                    "Contact",
                    name,
                    {
                        "title": payload.get("title", payload.get("job_title", "")),
                        "company": company,
                        "tier": payload.get("tier", ""),
                        "priority": payload.get("priority", 0),
                        "clearance": payload.get("clearance", ""),
                        "email": payload.get("email", ""),
                    },
                )

                # Create relationship to company
                if company:
                    contractor = self.find_entity(company, "Contractor")
                    if not contractor:
                        contractor = self.add_entity(
                            "Contractor", company, {"type": "unknown"}
                        )
                    self.add_relationship(
                        contact.id, "WORKS_FOR", contractor.id, source="inferred"
                    )

            logger.info(f"Added {len(contacts)} contacts")
        except Exception as e:
            logger.warning(f"Error loading contacts: {e}")

        # Populate jobs and infer relationships
        try:
            jobs = vector_store.get_all("jobs", limit=1000)
            for j in jobs:
                payload = j.payload if hasattr(j, "payload") else j
                company = payload.get("company", "")
                program = payload.get("mapped_program", "")

                job = self.add_entity(
                    "Job",
                    payload.get("title", "Unknown Position"),
                    {
                        "location": payload.get("location", ""),
                        "clearance": payload.get(
                            "clearance", payload.get("clearance_required", "")
                        ),
                        "program": program,
                        "company": company,
                        "bd_score": payload.get("bd_priority_score", 0),
                    },
                )

                # Link job to contractor
                if company:
                    contractor = self.find_entity(company, "Contractor")
                    if not contractor:
                        contractor = self.add_entity(
                            "Contractor", company, {"type": "prime"}
                        )
                    self.add_relationship(
                        contractor.id, "POSTED_BY", job.id, source="inferred"
                    )

                # Link job to program
                if program:
                    prog_entity = self.find_entity(program, "Program")
                    if prog_entity:
                        self.add_relationship(
                            prog_entity.id, "HAS_OPENING", job.id, source="inferred"
                        )

            logger.info(f"Added {len(jobs)} jobs")
        except Exception as e:
            logger.warning(f"Error loading jobs: {e}")

        # Infer contractor-program relationships from data
        self._infer_contractor_program_relationships()

        logger.info(f"Graph populated: {len(self._entity_cache)} entities")

    def _infer_contractor_program_relationships(self):
        """Infer PRIMES_ON relationships from program data."""
        programs = self.get_entities_by_type("Program")

        for program in programs:
            prime_name = program.properties.get("prime", "")
            if prime_name:
                contractor = self.find_entity(prime_name, "Contractor")
                if not contractor:
                    contractor = self.add_entity(
                        "Contractor", prime_name, {"type": "prime"}
                    )
                self.add_relationship(
                    contractor.id,
                    "PRIMES_ON",
                    program.id,
                    source="inferred",
                    confidence=0.9,
                )

    # =========================================
    # STATISTICS & EXPORT
    # =========================================

    def get_stats(self) -> Dict:
        """Get graph statistics."""
        entity_counts = {}
        for entity in self._entity_cache.values():
            entity_counts[entity.type] = entity_counts.get(entity.type, 0) + 1

        cursor = self.conn.execute(
            "SELECT type, COUNT(*) FROM relationships GROUP BY type"
        )
        rel_counts = {row[0]: row[1] for row in cursor}

        return {
            "total_entities": len(self._entity_cache),
            "entities_by_type": entity_counts,
            "total_relationships": sum(rel_counts.values()),
            "relationships_by_type": rel_counts,
        }

    def export_to_json(self, file_path: str):
        """Export graph to JSON file."""
        data = {
            "entities": [e.to_dict() for e in self._entity_cache.values()],
            "relationships": [],
        }

        cursor = self.conn.execute("SELECT * FROM relationships")
        for row in cursor:
            data["relationships"].append(
                {
                    "id": row[0],
                    "type": row[1],
                    "from_entity_id": row[2],
                    "to_entity_id": row[3],
                    "properties": json.loads(row[4]) if row[4] else {},
                    "confidence": row[5],
                    "source": row[6],
                    "created_at": row[7],
                }
            )

        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Exported graph to {file_path}")


# =========================================
# SINGLETON & FACTORY
# =========================================

_graph_instance: Optional[BDKnowledgeGraph] = None


def get_knowledge_graph(db_path: str = None) -> BDKnowledgeGraph:
    """Get knowledge graph singleton."""
    global _graph_instance
    if _graph_instance is None:
        _graph_instance = BDKnowledgeGraph(db_path)
    return _graph_instance
