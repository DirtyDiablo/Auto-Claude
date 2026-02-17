"""
Master DB Utilities: dedup, normalization, currency parsing, hashing.
"""

import hashlib
import json
import re
import unicodedata
from datetime import datetime
from typing import Any, Optional


# Extended from Engine7_BullhornETL/scripts/bullhorn_etl_v2.py
COMPANY_NORMALIZATIONS = {
    "Leidos - ONLY ONE YOU ARE TO USE": "Leidos",
    "Boeing - ONLY ONE YOU ARE TO USE": "Boeing",
    "BOEING": "Boeing",
    "LEIDOS": "Leidos",
    "Peraton": "Peraton",
    "SAIC": "SAIC",
    "Raytheon": "Raytheon",
    "Lockheed Martin": "Lockheed Martin",
    "CACI": "CACI",
    "ManTech": "ManTech",
    "General Dynamics": "General Dynamics IT",
    "Northrop Grumman": "Northrop Grumman",
    "Booz Allen Hamilton": "Booz Allen Hamilton",
    "Accenture Federal": "Accenture Federal Services",
    "Jacobs": "Jacobs",
    "KBR": "KBR",
    "AECOM": "AECOM",
    "LMI": "LMI",
    "L3Harris": "L3Harris Technologies",
    "L3 Harris": "L3Harris Technologies",
    "BAE Systems": "BAE Systems",
    "GDIT": "General Dynamics IT",
    "Deloitte": "Deloitte",
    "Amentum": "Amentum",
    "Anduril": "Anduril Industries",
    "Parsons": "Parsons",
    "ICF": "ICF",
    "Maximus": "Maximus",
    "Serco": "Serco",
    "DXC Technology": "DXC Technology",
    "CGI Federal": "CGI Federal",
    "Unisys": "Unisys Federal",
}


def normalize_company_name(name: str) -> str:
    """Normalize company name for matching."""
    if not name:
        return ""
    # Direct mapping first
    for key, value in COMPANY_NORMALIZATIONS.items():
        if key.lower() in name.lower():
            return value
    # Clean up
    name = name.strip()
    name = re.sub(r"\s*-\s*ONLY ONE.*$", "", name, flags=re.IGNORECASE)
    name = re.sub(r"\s+", " ", name)
    # Remove common suffixes for matching
    name = re.sub(r",?\s*(Inc\.?|LLC|Corp\.?|Corporation|Ltd\.?)$", "", name, flags=re.IGNORECASE)
    return name.strip()


def generate_id(*key_fields) -> str:
    """Generate deterministic UUID from key fields."""
    key = "|".join(str(f).lower().strip() for f in key_fields if f)
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def compute_hash(record: dict) -> str:
    """SHA256 hash of record for change detection."""
    serialized = json.dumps(record, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode()).hexdigest()


def parse_currency(value) -> Optional[float]:
    """Parse currency strings to float. Handles $47.5M, $1.2B, $500K, $1,234.56"""
    if value is None or value == "" or (isinstance(value, float) and value != value):
        return None
    s = str(value).strip()
    if not s or s.lower() in ("nan", "none", "n/a", "-"):
        return None

    # Already a number
    try:
        return float(s)
    except ValueError:
        pass

    # Remove $ and commas
    s = re.sub(r"[$,]", "", s)

    # Handle B/M/K suffixes
    multiplier = 1.0
    match = re.match(r"^([0-9.]+)\s*([BMKbmk])(?:illion|$)", s)
    if match:
        num_str, suffix = match.group(1), match.group(2).upper()
        multiplier = {"B": 1_000_000_000, "M": 1_000_000, "K": 1_000}.get(suffix, 1)
        try:
            return float(num_str) * multiplier
        except ValueError:
            return None

    # Plain number after cleanup
    try:
        return float(re.sub(r"[^0-9.\-]", "", s))
    except (ValueError, TypeError):
        return None


def standardize_date(value) -> Optional[str]:
    """Parse various date formats to ISO 8601 (YYYY-MM-DD)."""
    if value is None or value == "" or (isinstance(value, float) and value != value):
        return None
    s = str(value).strip()
    if not s or s.lower() in ("nan", "none", "n/a", "-", "null"):
        return None

    # Already ISO format
    if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        return s

    # Try common formats
    formats = [
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%m/%d/%Y",
        "%m/%d/%y",
        "%m-%d-%Y",
        "%d-%b-%Y",
        "%d-%b-%y",
        "%B %d, %Y",
        "%b %d, %Y",
        "%Y/%m/%d",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue

    # Try extracting just the date part
    date_match = re.match(r"(\d{4}-\d{2}-\d{2})", s)
    if date_match:
        return date_match.group(1)

    return None


def json_encode_array(value) -> Optional[str]:
    """Encode a list/value as JSON text for SQLite storage."""
    if value is None:
        return None
    if isinstance(value, str):
        # Already JSON?
        if value.startswith("[") or value.startswith("{"):
            return value
        # Comma-separated -> list
        if "," in value:
            return json.dumps([v.strip() for v in value.split(",") if v.strip()])
        return json.dumps([value]) if value.strip() else None
    if isinstance(value, (list, dict)):
        return json.dumps(value, default=str)
    return json.dumps([str(value)])


def safe_str(value) -> Optional[str]:
    """Convert to string, handling NaN/None."""
    if value is None:
        return None
    if isinstance(value, float) and value != value:  # NaN check
        return None
    s = str(value).strip()
    return s if s and s.lower() not in ("nan", "none") else None


def safe_int(value) -> Optional[int]:
    """Convert to int, handling NaN/None."""
    if value is None:
        return None
    if isinstance(value, float) and value != value:
        return None
    try:
        return int(float(str(value)))
    except (ValueError, TypeError):
        return None


def safe_float(value) -> Optional[float]:
    """Convert to float, handling NaN/None."""
    if value is None:
        return None
    if isinstance(value, float) and value != value:
        return None
    try:
        return float(str(value))
    except (ValueError, TypeError):
        return None


class Deduplicator:
    """Tracks seen records and deduplicates by key."""

    def __init__(self):
        self._seen_keys: set[str] = set()
        self._stats = {"total": 0, "unique": 0, "duplicates": 0}

    def is_new(self, *key_parts) -> bool:
        """Check if this key combination is new (not seen before)."""
        self._stats["total"] += 1
        key = "|".join(str(p).lower().strip() for p in key_parts if p)
        if not key:
            self._stats["unique"] += 1
            return True
        if key in self._seen_keys:
            self._stats["duplicates"] += 1
            return False
        self._seen_keys.add(key)
        self._stats["unique"] += 1
        return True

    @property
    def stats(self) -> dict:
        return self._stats.copy()

    def reset(self):
        self._seen_keys.clear()
        self._stats = {"total": 0, "unique": 0, "duplicates": 0}


def normalize_name(name: str) -> str:
    """Normalize a person/program name for matching."""
    if not name:
        return ""
    # Unicode normalize
    name = unicodedata.normalize("NFKD", name)
    # Remove non-alpha chars except spaces and hyphens
    name = re.sub(r"[^a-zA-Z0-9\s\-]", "", name)
    # Collapse whitespace
    name = re.sub(r"\s+", " ", name).strip()
    return name.lower()


def fuzzy_program_match(program_name: str, program_lookup: dict) -> Optional[str]:
    """Match a program name to program ID using exact, acronym, and fuzzy matching."""
    if not program_name:
        return None

    name_lower = program_name.lower().strip()

    # Exact match
    if name_lower in program_lookup:
        return program_lookup[name_lower]

    # Check if it's an acronym match
    for key, pid in program_lookup.items():
        if key == name_lower or name_lower in key or key in name_lower:
            return pid

    # Normalized match
    norm = normalize_name(program_name)
    for key, pid in program_lookup.items():
        if normalize_name(key) == norm:
            return pid

    return None


def build_program_lookup(conn) -> dict:
    """Build program name -> id lookup from the programs table."""
    cursor = conn.cursor()
    cursor.execute("SELECT id, program_name, acronym FROM programs")
    lookup = {}
    for row in cursor.fetchall():
        pid = row[0]
        name = row[1]
        acronym = row[2]
        if name:
            lookup[name.lower().strip()] = pid
        if acronym:
            lookup[acronym.lower().strip()] = pid
    return lookup


def build_company_lookup(conn) -> dict:
    """Build company name -> id lookup from the companies table."""
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, normalized_name FROM companies")
    lookup = {}
    for row in cursor.fetchall():
        cid = row[0]
        if row[1]:
            lookup[row[1].lower().strip()] = cid
        if row[2]:
            lookup[row[2].lower().strip()] = cid
    return lookup
