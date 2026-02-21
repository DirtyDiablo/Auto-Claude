"""
Project-wide constants for BD Automation Engine.

Import from here rather than hard-coding magic strings / numbers in
individual engines.
"""

# ---------------------------------------------------------------------------
# Security clearance levels (in descending order of sensitivity)
# ---------------------------------------------------------------------------

CLEARANCE_LEVELS = [
    "TS/SCI CI Poly",
    "TS/SCI",
    "CI Poly",
    "Full Scope Poly",
    "Top Secret",
    "Secret",
    "Public Trust",
]

# ---------------------------------------------------------------------------
# Contact tiers (from Engine 3 OrgChart Classification)
# ---------------------------------------------------------------------------

CONTACT_TIERS = {
    1: "Executive",
    2: "Senior",
    3: "Mid-Level",
    4: "Junior",
    5: "External",
    6: "Unknown",
}

# ---------------------------------------------------------------------------
# BD score tiers (from Engine 5 Scoring)
# ---------------------------------------------------------------------------

SCORE_TIERS = {
    "hot": 80,
    "warm": 50,
    "cold": 0,
}

# ---------------------------------------------------------------------------
# Default Qdrant vector store collections (Engine 8 Knowledge)
# ---------------------------------------------------------------------------

QDRANT_COLLECTIONS = [
    "contacts",
    "programs",
    "documents",
    "activities",
    "jobs",
]

# ---------------------------------------------------------------------------
# Confidence thresholds (from Engine 2 Program Mapping)
# ---------------------------------------------------------------------------

CONFIDENCE_THRESHOLDS = {
    "high": 0.70,
    "medium": 0.50,
    "low": 0.30,
}

# ---------------------------------------------------------------------------
# Default Bullhorn candidate fields
# ---------------------------------------------------------------------------

DEFAULT_CANDIDATE_FIELDS = [
    "id",
    "firstName",
    "lastName",
    "email",
    "phone",
    "occupation",
    "companyName",
    "status",
    "owner",
]

# ---------------------------------------------------------------------------
# Supported engines
# ---------------------------------------------------------------------------

ENGINE_NAMES = {
    1: "Scraper",
    2: "ProgramMapping",
    3: "OrgChart",
    4: "Playbook",
    5: "Scoring",
    6: "QA",
    7: "BullhornETL",
    8: "Knowledge",
}
