"""
Auto-classify contacts by role level using 6-tier hierarchy.
Reuses TIER_DEFINITIONS patterns from Engine3_OrgChart/scripts/contact_classifier.py.
"""
import re
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DB_PATH = PROJECT_ROOT / "data" / "unified_federal_contracts.db"

# 6-tier hierarchy (from Engine3_OrgChart/scripts/contact_classifier.py)
TIER_DEFINITIONS = {
    1: {
        "name": "Executive",
        "patterns": [
            r"\b(CEO|CTO|COO|CFO|CIO|CISO)\b",
            r"\bChief\s+\w+\s+Officer\b",
            r"\bPresident\b",
            r"\bGeneral\s+Manager\b",
            r"\bExecutive\s+(VP|Vice\s+President)\b",
            r"\bSVP\b",
            r"\bSenior\s+Vice\s+President\b",
        ],
        "bd_priority": "Critical",
    },
    2: {
        "name": "Director",
        "patterns": [
            r"\bDirector\b",
            r"\bVP\b",
            r"\bVice\s+President\b",
            r"\bDivision\s+(?:Head|Chief|Lead)\b",
            r"\bAssociate\s+Director\b",
        ],
        "bd_priority": "Critical",
    },
    3: {
        "name": "Program Leadership",
        "patterns": [
            r"\bProgram\s+Manager\b",
            r"\bProject\s+Manager\b",
            r"\bSite\s+Lead\b",
            r"\bTask\s+Order\s+Manager\b",
            r"\bDeputy\s+Program\s+Manager\b",
            r"\bPrincipal\s+(?:Engineer|Scientist|Analyst)\b",
            r"\bChief\s+(?:Engineer|Architect|Scientist)\b",
        ],
        "bd_priority": "High",
    },
    4: {
        "name": "Management",
        "patterns": [
            r"\bManager\b",
            r"\bTeam\s+Lead\b",
            r"\bTechnical\s+Lead\b",
            r"\bSupervisor\b",
            r"\bSection\s+(?:Chief|Lead)\b",
            r"\bBranch\s+(?:Chief|Manager)\b",
            r"\bGroup\s+Lead\b",
        ],
        "bd_priority": "High",
    },
    5: {
        "name": "Senior IC",
        "patterns": [
            r"\bSenior\s+(?:Engineer|Developer|Analyst|Specialist|Consultant)\b",
            r"\bSr\.?\s+(?:Engineer|Developer|Analyst|Specialist)\b",
            r"\bLead\s+(?:Engineer|Developer|Analyst)\b",
            r"\bStaff\s+(?:Engineer|Scientist)\b",
            r"\bArchitect\b",
            r"\bSME\b",
            r"\bSubject\s+Matter\s+Expert\b",
        ],
        "bd_priority": "Medium",
    },
    6: {
        "name": "Individual Contributor",
        "patterns": [
            r"\bEngineer\b",
            r"\bDeveloper\b",
            r"\bAnalyst\b",
            r"\bSpecialist\b",
            r"\bTechnician\b",
            r"\bAdministrator\b",
            r"\bConsultant\b",
        ],
        "bd_priority": "Standard",
    },
}


def classify_title(title):
    """Classify a title into tier, role_level, bd_priority."""
    if not title:
        return None, None, None

    for tier_num in sorted(TIER_DEFINITIONS.keys()):
        tier_def = TIER_DEFINITIONS[tier_num]
        for pattern in tier_def["patterns"]:
            if re.search(pattern, title, re.IGNORECASE):
                return tier_num, tier_def["name"], tier_def["bd_priority"]

    return None, None, None


def run(db_path=None):
    """Run contact classification."""
    db_path = db_path or DB_PATH
    print("Contact Classification")
    print(f"  Database: {db_path}")

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Get contacts with titles that need classification
    cursor.execute("""
        SELECT id, title FROM contacts
        WHERE title IS NOT NULL AND TRIM(title) != ''
    """)
    contacts = cursor.fetchall()

    classified = 0
    by_tier = {}

    for cid, title in contacts:
        tier, role_level, bd_priority = classify_title(title)
        if tier is not None:
            cursor.execute("""
                UPDATE contacts
                SET tier = ?, inferred_role_level = ?, bd_priority = ?
                WHERE id = ?
            """, (tier, role_level, bd_priority, cid))
            classified += 1
            by_tier[role_level] = by_tier.get(role_level, 0) + 1

    conn.commit()
    conn.close()

    print(f"  Classified: {classified}/{len(contacts)} contacts with titles")
    for role, count in sorted(by_tier.items(), key=lambda x: -x[1]):
        print(f"    {role}: {count}")


if __name__ == "__main__":
    run()
