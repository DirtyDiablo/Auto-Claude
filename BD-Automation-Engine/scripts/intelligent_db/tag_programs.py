"""
Auto-tag programs by defense domain using keyword patterns.
13 domain tags applied based on program_name, description, keywords_signals, functional_areas.
"""
import json
import re
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DB_PATH = PROJECT_ROOT / "data" / "unified_federal_contracts.db"

DOMAIN_PATTERNS = {
    "ISR": [
        r"\bISR\b", r"\bintelligence.{0,20}surveillance.{0,20}reconnaissance\b",
        r"\bDCGS\b", r"\bDGS\b", r"\bSIGINT\b", r"\bGEOINT\b", r"\bIMINT\b",
        r"\bfull.?motion.?video\b", r"\bFMV\b", r"\bUAS\b", r"\bdrone\b",
    ],
    "C4ISR": [
        r"\bC4ISR\b", r"\bC2\b", r"\bcommand\s+(?:and\s+)?control\b",
        r"\bcommunications?\b.*\b(?:system|network)\b", r"\bJADC2\b",
        r"\bbattle\s*management\b", r"\btactical\s+(?:data|network|comm)\b",
    ],
    "Cyber": [
        r"\bcyber\b", r"\bcybersecurity\b", r"\binformation\s+assurance\b",
        r"\bSOC\b", r"\bCSFP\b", r"\bCNO\b", r"\boffensive\s+cyber\b",
        r"\bdefensive\s+cyber\b", r"\bincident\s+response\b", r"\bzero.?trust\b",
    ],
    "Space": [
        r"\bspace\b", r"\bsatellite\b", r"\borbital\b", r"\bGPS\b",
        r"\bspace\s+force\b", r"\bSSA\b", r"\bspace\s+domain\s+awareness\b",
        r"\bmissile\s+(?:defense|warning)\b", r"\bSBIRS\b",
    ],
    "Logistics": [
        r"\blogistics\b", r"\bsupply\s+chain\b", r"\bsustainment\b",
        r"\bmaintenance\b", r"\bGCSS\b", r"\bERPi?\b", r"\bwarehousing\b",
        r"\basset\s+management\b",
    ],
    "EW": [
        r"\belectronic\s+warfare\b", r"\bEW\b", r"\bECM\b", r"\bECCM\b",
        r"\bjamming\b", r"\bspectrum\b", r"\bEMSO\b", r"\bsignal\s+processing\b",
    ],
    "Training": [
        r"\btraining\b", r"\bsimulation\b", r"\bLVC\b", r"\bmodeling\s+(?:and|&)\s+simulation\b",
        r"\bexercise\b", r"\bwargam(?:e|ing)\b", r"\binstructional\b",
    ],
    "Aviation": [
        r"\baviation\b", r"\baircraft\b", r"\bfighter\b", r"\bF-(?:35|22|16|15)\b",
        r"\brotary\s+wing\b", r"\bhelicopter\b", r"\bflight\b", r"\bairborne\b",
    ],
    "Navy": [
        r"\bnavy\b", r"\bnaval\b", r"\bmaritime\b", r"\bship\b", r"\bsubmarine\b",
        r"\bfleet\b", r"\bNAVSEA\b", r"\bNAVAIR\b", r"\bSPAWAR\b", r"\bNIWC\b",
    ],
    "Army": [
        r"\barmy\b", r"\bPEO\b.*\b(?:IEW|STRI|AVN|CS|GCS)\b",
        r"\bCECOM\b", r"\binscom\b", r"\bground\s+(?:vehicle|force|system)\b",
    ],
    "Air_Force": [
        r"\bair\s+force\b", r"\bUSAF\b", r"\bAFRL\b", r"\bAFMC\b",
        r"\bAFSOC\b", r"\bACC\b", r"\bAMC\b",
    ],
    "Intel_Community": [
        r"\bNSA\b", r"\bCIA\b", r"\bDIA\b", r"\bNGA\b", r"\bNRO\b",
        r"\bintelligence\s+community\b", r"\bIC\b",
        r"\bclandestine\b", r"\bcounterintelligence\b", r"\bHUMINT\b",
    ],
    "Health": [
        r"\bhealth\b", r"\bmedical\b", r"\bDHA\b", r"\bMHS\b",
        r"\belectronic\s+health\s+record\b", r"\bEHR\b", r"\bMHS\s+GENESIS\b",
        r"\bclinical\b", r"\btelehealth\b",
    ],
}

# Columns to search for patterns
SEARCH_COLUMNS = ["program_name", "description", "keywords_signals", "functional_areas"]


def ensure_column(conn):
    """Add domain_tags column if needed."""
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(programs)")
    cols = [row[1] for row in cursor.fetchall()]
    if "domain_tags" not in cols:
        cursor.execute("ALTER TABLE programs ADD COLUMN domain_tags TEXT")
        conn.commit()


def tag_program(row_dict):
    """Determine domain tags for a program based on text fields."""
    # Combine all searchable text
    text_parts = []
    for col in SEARCH_COLUMNS:
        val = row_dict.get(col)
        if val:
            text_parts.append(str(val))
    combined = " ".join(text_parts)

    if not combined.strip():
        return []

    tags = []
    for domain, patterns in DOMAIN_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, combined, re.IGNORECASE):
                tags.append(domain)
                break

    return tags


def run(db_path=None):
    """Run program domain tagging."""
    db_path = db_path or DB_PATH
    print("Program Domain Tagging")
    print(f"  Database: {db_path}")

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    ensure_column(conn)

    # Get existing columns to know which SEARCH_COLUMNS exist
    cursor.execute("PRAGMA table_info(programs)")
    existing_cols = {row[1] for row in cursor.fetchall()}
    valid_cols = [c for c in SEARCH_COLUMNS if c in existing_cols]

    cols_str = ", ".join(["id"] + valid_cols)
    cursor.execute(f"SELECT {cols_str} FROM programs")
    programs = cursor.fetchall()

    tagged = 0
    domain_counts = {}

    for prog in programs:
        row_dict = dict(prog)
        tags = tag_program(row_dict)
        if tags:
            cursor.execute(
                "UPDATE programs SET domain_tags = ? WHERE id = ?",
                (json.dumps(tags), row_dict["id"])
            )
            tagged += 1
            for t in tags:
                domain_counts[t] = domain_counts.get(t, 0) + 1

    conn.commit()
    conn.close()

    print(f"  Tagged: {tagged}/{len(programs)} programs")
    for domain, count in sorted(domain_counts.items(), key=lambda x: -x[1]):
        print(f"    {domain}: {count}")


if __name__ == "__main__":
    run()
