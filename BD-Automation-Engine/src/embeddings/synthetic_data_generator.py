"""Phase 47A — Synthetic Training Data Generator.

Generates (query, positive, negative) triplets from master_notes, programs,
contacts, jobs, and acronyms for fine-tuning domain-specific embeddings.
Seven query generation strategies with hard negative mining.
"""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


# =========================================
# ENUMS & DATA CLASSES
# =========================================

class QueryStrategy(str, Enum):
    ENTITY_CENTRIC = "entity_centric"
    ROLE_CENTRIC = "role_centric"
    PAIN_POINT = "pain_point"
    RELATIONSHIP = "relationship"
    JOB_MAPPING = "job_mapping"
    ACRONYM = "acronym"
    TEMPORAL = "temporal"


@dataclass
class Triplet:
    query: str = ""
    positive: str = ""
    negative: str = ""
    strategy: str = ""
    source_collection: str = ""
    difficulty: str = "medium"  # easy | medium | hard
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def id(self) -> str:
        raw = f"{self.query}:{self.positive[:50]}"
        return f"trip_{hashlib.md5(raw.encode()).hexdigest()[:12]}"


@dataclass
class GenerationJob:
    id: str = ""
    strategies: List[str] = field(default_factory=list)
    total_triplets: int = 0
    triplets_by_strategy: Dict[str, int] = field(default_factory=dict)
    triplets_by_source: Dict[str, int] = field(default_factory=dict)
    triplets_by_difficulty: Dict[str, int] = field(default_factory=dict)
    created_at: str = ""
    duration_sec: float = 0.0
    status: str = "completed"

    def __post_init__(self):
        if not self.id:
            raw = f"gen:{datetime.now(timezone.utc).isoformat()}"
            self.id = f"gen_{hashlib.md5(raw.encode()).hexdigest()[:10]}"
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


# =========================================
# SIMULATED DATA STORES
# =========================================

_PROGRAMS = [
    {"id": "prog_001", "name": "DCGS-A", "full_name": "Distributed Common Ground System - Army",
     "prime": "Leidos", "domain": "ISR", "value_m": 450,
     "description": "Army's primary intelligence, surveillance, and reconnaissance ground processing system. Provides multi-INT fusion and exploitation capabilities to tactical commanders."},
    {"id": "prog_002", "name": "DCGS-N", "full_name": "Distributed Common Ground System - Navy",
     "prime": "Raytheon", "domain": "ISR", "value_m": 280,
     "description": "Navy variant of DCGS providing maritime ISR processing, PED capabilities, and intelligence dissemination for fleet operations."},
    {"id": "prog_003", "name": "GBSD", "full_name": "Ground Based Strategic Deterrent",
     "prime": "Northrop Grumman", "domain": "Strategic", "value_m": 95000,
     "description": "Next-generation ICBM system replacing Minuteman III. Includes weapon system, command and control, ground subsystems, and flight test."},
    {"id": "prog_004", "name": "JADC2", "full_name": "Joint All-Domain Command and Control",
     "prime": "Multiple", "domain": "C2", "value_m": 1200,
     "description": "DOD initiative connecting sensors and shooters across all domains. Enables rapid decision-making through shared data and AI-enabled analytics."},
    {"id": "prog_005", "name": "ABMS", "full_name": "Advanced Battle Management System",
     "prime": "Multiple", "domain": "C2", "value_m": 3500,
     "description": "Air Force contribution to JADC2. Digital infrastructure connecting joint force through cloud, AI, and open architecture."},
    {"id": "prog_006", "name": "MQ-25 Stingray", "full_name": "MQ-25 Stingray UAS",
     "prime": "Boeing", "domain": "UAS", "value_m": 13000,
     "description": "Navy carrier-based unmanned aerial refueling system. Extends range of carrier air wing strike fighters."},
    {"id": "prog_007", "name": "NGJ-MB", "full_name": "Next Generation Jammer Mid-Band",
     "prime": "Raytheon", "domain": "EW", "value_m": 7600,
     "description": "Advanced airborne electronic attack system for EA-18G Growler. Replaces ALQ-99 with AESA-based jamming."},
    {"id": "prog_008", "name": "IVAS", "full_name": "Integrated Visual Augmentation System",
     "prime": "Microsoft", "domain": "Soldier Systems", "value_m": 21900,
     "description": "Army mixed-reality headset based on HoloLens for situational awareness, target acquisition, and training."},
]

_CONTACTS = [
    {"id": "c001", "name": "Craig Lindahl", "title": "Program Manager", "company": "Leidos",
     "program": "DCGS-A", "clearance": "TS/SCI w/ CI Poly", "location": "Langley AFB, VA",
     "notes": "Key decision-maker for DCGS-A modernization. Interested in cloud migration and AI/ML integration."},
    {"id": "c002", "name": "Sarah Mitchell", "title": "Deputy PM", "company": "Northrop Grumman",
     "program": "GBSD", "clearance": "TS/SCI", "location": "Hill AFB, UT",
     "notes": "Manages systems engineering team. Looking for cleared software developers with agile experience."},
    {"id": "c003", "name": "James Patel", "title": "Technical Director", "company": "Raytheon",
     "program": "DCGS-N", "clearance": "TS/SCI w/ CI Poly", "location": "St. Inigoes, MD",
     "notes": "Oversees PED pipeline modernization. Pain point: legacy Java codebase needs migration to microservices."},
    {"id": "c004", "name": "Amanda Chen", "title": "SETA Lead", "company": "GDIT",
     "program": "JADC2", "clearance": "TS/SCI", "location": "Pentagon, VA",
     "notes": "Advises Joint Staff on JADC2 architecture. Interested in zero-trust networking and data mesh."},
    {"id": "c005", "name": "Robert Hayes", "title": "Contracting Officer", "company": "US Army",
     "program": "DCGS-A", "clearance": "Secret", "location": "Aberdeen, MD",
     "notes": "Manages DCGS-A contract vehicle. Option Year 3 exercise due June 2026."},
    {"id": "c006", "name": "Diana Torres", "title": "Chief Engineer", "company": "Boeing",
     "program": "MQ-25 Stingray", "clearance": "TS/SCI", "location": "St. Louis, MO",
     "notes": "Leads flight software development. Needs autonomy and mission systems engineers."},
]

_MASTER_NOTES = [
    {"id": "note_001", "contact_id": "c001", "content": "Craig mentioned they're struggling to fill 5 senior cloud architect positions at Langley. The SIGINT processing pipeline has latency issues. Budget for FY26 approved with $20M ceiling increase.", "date": "2026-01-15"},
    {"id": "note_002", "contact_id": "c003", "content": "James discussed the DCGS-N PED modernization effort. Legacy Java monolith needs decomposition into microservices. Raytheon lost 3 key engineers to AWS. Looking for Kubernetes and Kafka expertise.", "date": "2026-01-20"},
    {"id": "note_003", "contact_id": "c002", "content": "Sarah's team at Hill AFB needs 12 cleared developers for GBSD weapon system software. TS/SCI required. Northrop struggling with retention — offered 15% raises but still losing people to commercial tech.", "date": "2026-02-01"},
    {"id": "note_004", "contact_id": "c004", "content": "Amanda briefed on JADC2 architecture review. DOD moving to zero-trust with CMMC 2.0 compliance deadline Q3 FY26. Data mesh approach preferred over centralized data lake.", "date": "2026-02-05"},
    {"id": "note_005", "contact_id": "c005", "content": "Robert confirmed the DCGS-A recompete timeline: RFP expected September 2026, proposals due December. Option Year 3 exercise in June. Incumbent advantage strong but not guaranteed.", "date": "2026-01-28"},
    {"id": "note_006", "contact_id": "c001", "content": "Follow-up with Craig: BAE submitted unsolicited proposal for DCGS-A cloud migration but was rejected. Leidos prefers GDIT's GovCloud approach. Need to schedule demo of our Kubernetes platform.", "date": "2026-02-03"},
    {"id": "note_007", "contact_id": "c006", "content": "Diana needs 8 autonomy engineers for MQ-25 Stingray flight software. Boeing's St. Louis facility. Must have UAS experience and active TS/SCI. Timeline: fill by Q2 FY26.", "date": "2026-01-22"},
    {"id": "note_008", "contact_id": "c003", "content": "DCGS-N performance review: PED throughput improved 30% after initial microservices migration. James wants to accelerate Phase 2 covering ELINT and MASINT fusion. Budget request submitted for additional $15M.", "date": "2026-02-08"},
]

_JOBS = [
    {"id": "job_001", "title": "Senior Cloud Architect", "program": "DCGS-A", "location": "Langley AFB, VA",
     "clearance": "TS/SCI w/ CI Poly", "skills": ["AWS GovCloud", "Kubernetes", "Terraform", "Python"],
     "description": "Design and implement cloud-native architecture for DCGS-A ISR processing pipeline. Lead migration from on-premise to AWS GovCloud."},
    {"id": "job_002", "title": "Software Developer - Mission Systems", "program": "GBSD", "location": "Hill AFB, UT",
     "clearance": "TS/SCI", "skills": ["C++", "Ada", "Real-time systems", "DO-178C"],
     "description": "Develop weapon system software for Ground Based Strategic Deterrent. Safety-critical real-time systems using DO-178C processes."},
    {"id": "job_003", "title": "Kubernetes Platform Engineer", "program": "DCGS-N", "location": "St. Inigoes, MD",
     "clearance": "TS/SCI w/ CI Poly", "skills": ["Kubernetes", "Kafka", "Java", "Microservices"],
     "description": "Lead PED pipeline modernization from Java monolith to Kubernetes-based microservices. Implement Kafka event streaming."},
    {"id": "job_004", "title": "Zero Trust Network Architect", "program": "JADC2", "location": "Pentagon, VA",
     "clearance": "TS/SCI", "skills": ["Zero Trust", "CMMC", "Network Security", "SASE"],
     "description": "Design zero-trust networking architecture for Joint All-Domain Command and Control. Ensure CMMC 2.0 compliance."},
    {"id": "job_005", "title": "Autonomy Engineer", "program": "MQ-25 Stingray", "location": "St. Louis, MO",
     "clearance": "TS/SCI", "skills": ["UAS", "ROS", "Computer Vision", "C++", "Python"],
     "description": "Develop autonomous flight control and mission management software for MQ-25 carrier-based UAS."},
    {"id": "job_006", "title": "SIGINT Analyst - DGS-1", "program": "DCGS-A", "location": "Langley AFB, VA",
     "clearance": "TS/SCI w/ CI Poly", "skills": ["SIGINT", "ELINT", "COMINT", "Palantir"],
     "description": "Perform signals intelligence analysis at DGS-1 Langley. Process and exploit SIGINT data using DCGS-A tools."},
]

_ACRONYMS = {
    "DCGS": "Distributed Common Ground System",
    "DCGS-A": "Distributed Common Ground System - Army",
    "DCGS-N": "Distributed Common Ground System - Navy",
    "GBSD": "Ground Based Strategic Deterrent",
    "JADC2": "Joint All-Domain Command and Control",
    "ABMS": "Advanced Battle Management System",
    "ISR": "Intelligence, Surveillance, and Reconnaissance",
    "PED": "Processing, Exploitation, and Dissemination",
    "SIGINT": "Signals Intelligence",
    "ELINT": "Electronic Intelligence",
    "COMINT": "Communications Intelligence",
    "MASINT": "Measurement and Signature Intelligence",
    "GEOINT": "Geospatial Intelligence",
    "HUMINT": "Human Intelligence",
    "C2": "Command and Control",
    "C4ISR": "Command, Control, Communications, Computers, Intelligence, Surveillance, and Reconnaissance",
    "EW": "Electronic Warfare",
    "UAS": "Unmanned Aircraft System",
    "SETA": "Systems Engineering and Technical Assistance",
    "TS/SCI": "Top Secret / Sensitive Compartmented Information",
    "CI Poly": "Counterintelligence Polygraph",
    "DGS-1": "Distributed Ground Station 1 (Langley AFB)",
    "DGS-2": "Distributed Ground Station 2 (Beale AFB)",
    "IDIQ": "Indefinite Delivery / Indefinite Quantity",
    "BPA": "Blanket Purchase Agreement",
    "CMMC": "Cybersecurity Maturity Model Certification",
    "RFP": "Request for Proposal",
    "CDR": "Critical Design Review",
    "PDR": "Preliminary Design Review",
    "SRR": "System Requirements Review",
    "FY26": "Fiscal Year 2026",
    "GovCloud": "AWS Government Cloud",
    "ATO": "Authority to Operate",
    "STIG": "Security Technical Implementation Guide",
    "DO-178C": "Software Considerations in Airborne Systems and Equipment Certification",
    "AESA": "Active Electronically Scanned Array",
    "IVAS": "Integrated Visual Augmentation System",
    "NGJ-MB": "Next Generation Jammer Mid-Band",
    "MQ-25": "MQ-25 Stingray Unmanned Aerial Refueling System",
}


# =========================================
# SYNTHETIC DATA GENERATOR
# =========================================

class SyntheticDataGenerator:
    """Generates (query, positive, negative) triplets for embedding fine-tuning."""

    def __init__(self) -> None:
        self._triplets: List[Triplet] = []
        self._jobs: List[GenerationJob] = []
        self._rng = random.Random(42)

    # --------------------------------------------------
    # MAIN GENERATION ENTRY POINT
    # --------------------------------------------------

    def generate(
        self,
        strategies: Optional[List[str]] = None,
        max_per_strategy: int = 50,
    ) -> GenerationJob:
        """Generate training triplets across all strategies."""
        import time
        start = time.time()

        if strategies is None:
            strategies = [s.value for s in QueryStrategy]

        generated: List[Triplet] = []
        strategy_counts: Dict[str, int] = {}
        source_counts: Dict[str, int] = {}
        difficulty_counts: Dict[str, int] = {}

        strategy_map = {
            QueryStrategy.ENTITY_CENTRIC.value: self._generate_entity_centric,
            QueryStrategy.ROLE_CENTRIC.value: self._generate_role_centric,
            QueryStrategy.PAIN_POINT.value: self._generate_pain_point,
            QueryStrategy.RELATIONSHIP.value: self._generate_relationship,
            QueryStrategy.JOB_MAPPING.value: self._generate_job_mapping,
            QueryStrategy.ACRONYM.value: self._generate_acronym,
            QueryStrategy.TEMPORAL.value: self._generate_temporal,
        }

        for strategy in strategies:
            fn = strategy_map.get(strategy)
            if not fn:
                continue
            triplets = fn(max_per_strategy)
            for t in triplets:
                t.strategy = strategy
            generated.extend(triplets)
            strategy_counts[strategy] = len(triplets)

        for t in generated:
            source_counts[t.source_collection] = source_counts.get(t.source_collection, 0) + 1
            difficulty_counts[t.difficulty] = difficulty_counts.get(t.difficulty, 0) + 1

        self._triplets.extend(generated)

        job = GenerationJob(
            strategies=strategies,
            total_triplets=len(generated),
            triplets_by_strategy=strategy_counts,
            triplets_by_source=source_counts,
            triplets_by_difficulty=difficulty_counts,
            duration_sec=round(time.time() - start, 3),
        )
        self._jobs.append(job)
        return job

    # --------------------------------------------------
    # STRATEGY: ENTITY-CENTRIC
    # --------------------------------------------------

    def _generate_entity_centric(self, max_count: int) -> List[Triplet]:
        """Generate queries asking about specific programs/companies."""
        triplets: List[Triplet] = []

        for prog in _PROGRAMS[:max_count]:
            # Query by acronym → expect full description
            query = f"What is {prog['name']}?"
            positive = f"{prog['name']} ({prog['full_name']}) is a {prog['domain']} program primed by {prog['prime']}. {prog['description']}"
            # Hard negative: different program in same domain
            others = [p for p in _PROGRAMS if p['id'] != prog['id']]
            neg_prog = self._rng.choice(others)
            negative = f"{neg_prog['name']} ({neg_prog['full_name']}) is a {neg_prog['domain']} program primed by {neg_prog['prime']}. {neg_prog['description']}"

            triplets.append(Triplet(
                query=query, positive=positive, negative=negative,
                source_collection="programs", difficulty="easy",
            ))

            # Query by full name → expect program details
            query2 = f"Tell me about the {prog['full_name']}"
            triplets.append(Triplet(
                query=query2, positive=positive, negative=negative,
                source_collection="programs", difficulty="medium",
            ))

        return triplets

    # --------------------------------------------------
    # STRATEGY: ROLE-CENTRIC
    # --------------------------------------------------

    def _generate_role_centric(self, max_count: int) -> List[Triplet]:
        """Generate queries about people and their roles."""
        triplets: List[Triplet] = []

        for contact in _CONTACTS[:max_count]:
            query = f"Who is the {contact['title']} for {contact['program']}?"
            positive = f"{contact['name']} is the {contact['title']} at {contact['company']} for {contact['program']}. Located at {contact['location']}. {contact['notes']}"
            # Hard negative: someone at same company different role
            others = [c for c in _CONTACTS if c['id'] != contact['id']]
            neg = self._rng.choice(others)
            negative = f"{neg['name']} is the {neg['title']} at {neg['company']} for {neg['program']}. Located at {neg['location']}. {neg['notes']}"

            triplets.append(Triplet(
                query=query, positive=positive, negative=negative,
                source_collection="contacts", difficulty="medium",
            ))

            # Query by name
            query2 = f"What does {contact['name']} work on?"
            triplets.append(Triplet(
                query=query2, positive=positive, negative=negative,
                source_collection="contacts", difficulty="easy",
            ))

        return triplets

    # --------------------------------------------------
    # STRATEGY: PAIN POINT
    # --------------------------------------------------

    def _generate_pain_point(self, max_count: int) -> List[Triplet]:
        """Generate queries about organizational challenges."""
        triplets: List[Triplet] = []

        pain_queries = [
            ("staffing challenges", "struggling to fill", "budget"),
            ("technical debt", "legacy", "staffing"),
            ("cloud migration", "cloud", "retention"),
            ("retention problems", "losing people", "cloud migration"),
        ]

        for query_text, positive_kw, negative_kw in pain_queries[:max_count]:
            # Find a note mentioning the positive keyword
            pos_notes = [n for n in _MASTER_NOTES if positive_kw in n["content"].lower()]
            neg_notes = [n for n in _MASTER_NOTES if negative_kw in n["content"].lower() and positive_kw not in n["content"].lower()]

            if pos_notes:
                pos_note = pos_notes[0]
                neg_note = neg_notes[0] if neg_notes else self._rng.choice([n for n in _MASTER_NOTES if n['id'] != pos_note['id']])

                query = f"Which programs are experiencing {query_text}?"
                triplets.append(Triplet(
                    query=query, positive=pos_note["content"], negative=neg_note["content"],
                    source_collection="notes", difficulty="hard",
                ))

        return triplets

    # --------------------------------------------------
    # STRATEGY: RELATIONSHIP
    # --------------------------------------------------

    def _generate_relationship(self, max_count: int) -> List[Triplet]:
        """Generate queries about organizational relationships."""
        triplets: List[Triplet] = []

        # Program-to-company relationships
        for prog in _PROGRAMS[:max_count]:
            query = f"Who primes {prog['name']}?"
            positive = f"{prog['prime']} is the prime contractor for {prog['name']} ({prog['full_name']}), a ${prog['value_m']}M {prog['domain']} program."
            others = [p for p in _PROGRAMS if p['prime'] != prog['prime']]
            neg = self._rng.choice(others) if others else _PROGRAMS[0]
            negative = f"{neg['prime']} is the prime contractor for {neg['name']} ({neg['full_name']}), a ${neg['value_m']}M {neg['domain']} program."

            triplets.append(Triplet(
                query=query, positive=positive, negative=negative,
                source_collection="programs", difficulty="easy",
            ))

        # Contact-to-program relationships
        for contact in _CONTACTS[:max_count]:
            query = f"Who works on {contact['program']} at {contact['company']}?"
            positive = f"{contact['name']} ({contact['title']}) works on {contact['program']} at {contact['company']}. Clearance: {contact['clearance']}."
            others = [c for c in _CONTACTS if c['program'] != contact['program']]
            neg = self._rng.choice(others) if others else _CONTACTS[0]
            negative = f"{neg['name']} ({neg['title']}) works on {neg['program']} at {neg['company']}. Clearance: {neg['clearance']}."

            triplets.append(Triplet(
                query=query, positive=positive, negative=negative,
                source_collection="contacts", difficulty="medium",
            ))

        return triplets

    # --------------------------------------------------
    # STRATEGY: JOB MAPPING
    # --------------------------------------------------

    def _generate_job_mapping(self, max_count: int) -> List[Triplet]:
        """Generate queries mapping skills to job openings."""
        triplets: List[Triplet] = []

        for job in _JOBS[:max_count]:
            # Skill-based query
            skills_str = ", ".join(job["skills"][:3])
            query = f"Find positions requiring {skills_str}"
            positive = f"{job['title']} on {job['program']} at {job['location']}. Requires {job['clearance']}. Skills: {', '.join(job['skills'])}. {job['description']}"
            others = [j for j in _JOBS if j['id'] != job['id']]
            neg = self._rng.choice(others)
            negative = f"{neg['title']} on {neg['program']} at {neg['location']}. Requires {neg['clearance']}. Skills: {', '.join(neg['skills'])}. {neg['description']}"

            triplets.append(Triplet(
                query=query, positive=positive, negative=negative,
                source_collection="jobs", difficulty="medium",
            ))

            # Location-based query
            query2 = f"Open positions at {job['location']} requiring {job['clearance']}"
            triplets.append(Triplet(
                query=query2, positive=positive, negative=negative,
                source_collection="jobs", difficulty="hard",
            ))

        return triplets

    # --------------------------------------------------
    # STRATEGY: ACRONYM
    # --------------------------------------------------

    def _generate_acronym(self, max_count: int) -> List[Triplet]:
        """Generate acronym resolution triplets."""
        triplets: List[Triplet] = []
        acronym_items = list(_ACRONYMS.items())[:max_count]

        for acronym, expansion in acronym_items:
            query = f"What does {acronym} stand for?"
            positive = f"{acronym} stands for {expansion}."

            # Hard negative: similar-sounding acronym
            others = [(a, e) for a, e in _ACRONYMS.items() if a != acronym]
            neg_a, neg_e = self._rng.choice(others)
            negative = f"{neg_a} stands for {neg_e}."

            triplets.append(Triplet(
                query=query, positive=positive, negative=negative,
                source_collection="acronyms", difficulty="easy",
            ))

            # Reverse: expansion → acronym
            query2 = f"What is the abbreviation for {expansion}?"
            positive2 = f"{expansion} is abbreviated as {acronym}."
            negative2 = f"{neg_e} is abbreviated as {neg_a}."

            triplets.append(Triplet(
                query=query2, positive=positive2, negative=negative2,
                source_collection="acronyms", difficulty="medium",
            ))

        return triplets

    # --------------------------------------------------
    # STRATEGY: TEMPORAL
    # --------------------------------------------------

    def _generate_temporal(self, max_count: int) -> List[Triplet]:
        """Generate time-aware queries about milestones and deadlines."""
        triplets: List[Triplet] = []

        temporal_facts = [
            {"query": "When is the DCGS-A recompete?", "positive": "The DCGS-A recompete RFP is expected September 2026, with proposals due December 2026. Option Year 3 exercise is due June 2026.", "negative": "The GBSD Critical Design Review is scheduled for early 2027."},
            {"query": "What contract milestones are coming up in FY26?", "positive": "DCGS-A Option Year 3 exercise due June 2026. DCGS-A recompete RFP expected September 2026. CMMC 2.0 compliance deadline Q3 FY26.", "negative": "The MQ-25 Stingray initial operational capability is projected for FY28."},
            {"query": "What budget changes happened recently?", "positive": "DCGS-A FY26 budget approved with $20M ceiling increase. DCGS-N submitted request for additional $15M for Phase 2 PED modernization.", "negative": "GBSD program continues at steady-state funding levels."},
            {"query": "What hiring timelines exist?", "positive": "Boeing MQ-25 needs 8 autonomy engineers filled by Q2 FY26. Langley DCGS-A has 5 open cloud architect positions. GBSD needs 12 cleared developers.", "negative": "JADC2 architecture review is an ongoing advisory role with no fixed hiring deadline."},
        ]

        for fact in temporal_facts[:max_count]:
            triplets.append(Triplet(
                query=fact["query"], positive=fact["positive"], negative=fact["negative"],
                source_collection="notes", difficulty="hard",
            ))

        return triplets

    # --------------------------------------------------
    # COLLECTION-SPECIFIC GENERATORS
    # --------------------------------------------------

    def generate_from_notes(self, max_count: int = 20) -> List[Triplet]:
        """Generate triplets specifically from master notes."""
        triplets: List[Triplet] = []
        for note in _MASTER_NOTES[:max_count]:
            contact = next((c for c in _CONTACTS if c["id"] == note["contact_id"]), None)
            if not contact:
                continue
            query = f"What was discussed with {contact['name']} about {contact['program']}?"
            positive = note["content"]
            others = [n for n in _MASTER_NOTES if n["id"] != note["id"]]
            neg = self._rng.choice(others)
            negative = neg["content"]
            triplets.append(Triplet(
                query=query, positive=positive, negative=negative,
                strategy="entity_centric", source_collection="notes", difficulty="medium",
            ))
        self._triplets.extend(triplets)
        return triplets

    def generate_from_programs(self, max_count: int = 20) -> List[Triplet]:
        """Generate triplets specifically from program data."""
        triplets = self._generate_entity_centric(max_count)
        for t in triplets:
            t.strategy = "entity_centric"
        self._triplets.extend(triplets)
        return triplets

    def generate_from_acronyms(self, max_count: int = 50) -> List[Triplet]:
        """Generate triplets from acronym dictionary."""
        triplets = self._generate_acronym(max_count)
        for t in triplets:
            t.strategy = "acronym"
        self._triplets.extend(triplets)
        return triplets

    def generate_from_jobs(self, max_count: int = 20) -> List[Triplet]:
        """Generate triplets from job listings."""
        triplets = self._generate_job_mapping(max_count)
        for t in triplets:
            t.strategy = "job_mapping"
        self._triplets.extend(triplets)
        return triplets

    def generate_from_contacts(self, max_count: int = 20) -> List[Triplet]:
        """Generate triplets from contact data."""
        triplets = self._generate_role_centric(max_count)
        for t in triplets:
            t.strategy = "role_centric"
        self._triplets.extend(triplets)
        return triplets

    # --------------------------------------------------
    # HARD NEGATIVE MINING
    # --------------------------------------------------

    def mine_hard_negatives(self, triplets: List[Triplet]) -> List[Triplet]:
        """Upgrade easy negatives to hard negatives using similarity signals.

        Hard negatives are documents that are semantically similar to the positive
        but NOT the correct answer — these are the most valuable for training.
        """
        upgraded: List[Triplet] = []
        for t in triplets:
            # Simulated: find a document from the same collection + domain
            # that shares keywords but is about a different entity
            hard_neg = self._find_hard_negative(t)
            if hard_neg:
                upgraded.append(Triplet(
                    query=t.query, positive=t.positive, negative=hard_neg,
                    strategy=t.strategy, source_collection=t.source_collection,
                    difficulty="hard",
                ))
            else:
                upgraded.append(t)
        return upgraded

    def _find_hard_negative(self, triplet: Triplet) -> Optional[str]:
        """Find a hard negative for a triplet based on shared domain keywords."""
        if triplet.source_collection == "programs":
            # Find a program in the same domain but different identity
            pos_lower = triplet.positive.lower()
            for prog in _PROGRAMS:
                prog_text = f"{prog['name']} ({prog['full_name']}) is a {prog['domain']} program primed by {prog['prime']}. {prog['description']}"
                if prog['name'].lower() not in pos_lower and prog['domain'].lower() in pos_lower:
                    return prog_text
        elif triplet.source_collection == "contacts":
            pos_lower = triplet.positive.lower()
            for contact in _CONTACTS:
                contact_text = f"{contact['name']} is the {contact['title']} at {contact['company']} for {contact['program']}. {contact['notes']}"
                if contact['name'].lower() not in pos_lower:
                    # Same clearance level = harder negative
                    if any(cl in pos_lower for cl in [contact['clearance'].lower()]):
                        return contact_text
        return None

    # --------------------------------------------------
    # QUERIES & STATS
    # --------------------------------------------------

    def get_triplets(self, strategy: str = "", source: str = "",
                     difficulty: str = "") -> List[Triplet]:
        """Filter triplets by criteria."""
        results = self._triplets
        if strategy:
            results = [t for t in results if t.strategy == strategy]
        if source:
            results = [t for t in results if t.source_collection == source]
        if difficulty:
            results = [t for t in results if t.difficulty == difficulty]
        return results

    def get_stats(self) -> Dict[str, Any]:
        """Return generation statistics."""
        by_strategy: Dict[str, int] = {}
        by_source: Dict[str, int] = {}
        by_difficulty: Dict[str, int] = {}

        for t in self._triplets:
            by_strategy[t.strategy] = by_strategy.get(t.strategy, 0) + 1
            by_source[t.source_collection] = by_source.get(t.source_collection, 0) + 1
            by_difficulty[t.difficulty] = by_difficulty.get(t.difficulty, 0) + 1

        return {
            "total_triplets": len(self._triplets),
            "total_jobs": len(self._jobs),
            "by_strategy": by_strategy,
            "by_source": by_source,
            "by_difficulty": by_difficulty,
            "programs_available": len(_PROGRAMS),
            "contacts_available": len(_CONTACTS),
            "notes_available": len(_MASTER_NOTES),
            "jobs_available": len(_JOBS),
            "acronyms_available": len(_ACRONYMS),
        }

    def get_generation_history(self) -> List[Dict[str, Any]]:
        """Return generation job history."""
        return [
            {
                "id": j.id, "strategies": j.strategies,
                "total_triplets": j.total_triplets,
                "triplets_by_strategy": j.triplets_by_strategy,
                "duration_sec": j.duration_sec,
                "created_at": j.created_at,
            }
            for j in self._jobs
        ]


# =========================================
# SINGLETON
# =========================================

_instance: Optional[SyntheticDataGenerator] = None


def get_synthetic_generator() -> SyntheticDataGenerator:
    global _instance
    if _instance is None:
        _instance = SyntheticDataGenerator()
    return _instance
