"""
Query Expander — Acronym resolution + defense domain synonym expansion.

Loads acronyms from acronyms.csv (1,058 entries) and adds 60+ defense-specific
expansions. Expands queries before embedding for better retrieval.
"""

import os
import sys
import csv
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent.parent
E7_ANALYSIS = BASE_DIR / "Engine7_BullhornETL" / "colton_scurry_analysis"


@dataclass
class ExpandedQuery:
    """Result of query expansion."""
    original: str
    expanded: str
    acronyms_resolved: List[str] = field(default_factory=list)
    synonyms_added: List[str] = field(default_factory=list)
    expansion_count: int = 0


# Defense domain synonyms (bidirectional)
DEFENSE_SYNONYMS: Dict[str, List[str]] = {
    # Programs
    "DCGS": ["Distributed Common Ground System"],
    "AF DCGS": ["Air Force Distributed Common Ground System", "DCGS-A"],
    "DCGS-A": ["Army Distributed Common Ground System"],
    "BICES": ["Battlefield Information Collection and Exploitation System"],
    "GBSD": ["Ground Based Strategic Deterrent", "Sentinel ICBM"],
    "JADC2": ["Joint All-Domain Command and Control"],
    "ABMS": ["Advanced Battle Management System"],
    "JSTARS": ["Joint Surveillance Target Attack Radar System"],
    "PACAF": ["Pacific Air Forces"],
    "CENTCOM": ["Central Command"],
    "SOCOM": ["Special Operations Command"],
    "CYBERCOM": ["Cyber Command"],
    "DISA": ["Defense Information Systems Agency"],
    "NGA": ["National Geospatial-Intelligence Agency"],
    "NRO": ["National Reconnaissance Office"],
    "DIA": ["Defense Intelligence Agency"],
    "NSA": ["National Security Agency"],

    # Clearances
    "TS/SCI": ["Top Secret Sensitive Compartmented Information", "TS SCI"],
    "TS": ["Top Secret"],
    "S": ["Secret"],
    "CI Poly": ["Counterintelligence Polygraph"],
    "Full Scope Poly": ["Full Scope Polygraph", "Lifestyle Polygraph"],
    "FSP": ["Full Scope Polygraph"],
    "SCI": ["Sensitive Compartmented Information"],
    "SAP": ["Special Access Program"],

    # Roles / Titles
    "PM": ["Program Manager"],
    "DPM": ["Deputy Program Manager"],
    "COTR": ["Contracting Officer Technical Representative"],
    "COR": ["Contracting Officer Representative"],
    "KO": ["Contracting Officer"],
    "FSO": ["Facility Security Officer"],
    "ISSM": ["Information System Security Manager"],
    "ISSO": ["Information System Security Officer"],
    "SME": ["Subject Matter Expert"],
    "BD": ["Business Development"],
    "PTL": ["Program Technical Lead"],
    "TL": ["Technical Lead", "Team Lead"],
    "SA": ["System Administrator", "Systems Analyst"],

    # Technologies / Domains
    "ISR": ["Intelligence Surveillance Reconnaissance"],
    "C4ISR": ["Command Control Communications Computers Intelligence Surveillance Reconnaissance"],
    "SIGINT": ["Signals Intelligence"],
    "GEOINT": ["Geospatial Intelligence"],
    "HUMINT": ["Human Intelligence"],
    "MASINT": ["Measurement and Signature Intelligence"],
    "OSINT": ["Open Source Intelligence"],
    "ELINT": ["Electronic Intelligence"],
    "COMINT": ["Communications Intelligence"],
    "DevSecOps": ["Development Security Operations"],
    "CI/CD": ["Continuous Integration Continuous Deployment"],
    "RMF": ["Risk Management Framework"],
    "STIG": ["Security Technical Implementation Guide"],
    "ATO": ["Authority to Operate"],
    "IATO": ["Interim Authority to Operate"],
    "PKI": ["Public Key Infrastructure"],

    # Contractors
    "GDIT": ["General Dynamics IT", "General Dynamics Information Technology"],
    "L3Harris": ["L3 Harris Technologies"],
    "BAE": ["BAE Systems"],
    "SAIC": ["Science Applications International Corporation"],
    "CACI": ["CACI International"],
    "ManTech": ["ManTech International"],
    "PTS": ["Polaris Technology Solutions", "PTS Inc"],
    "NGC": ["Northrop Grumman"],
    "LM": ["Lockheed Martin"],
    "RTX": ["Raytheon Technologies", "Raytheon"],

    # Contract Vehicles
    "IDIQ": ["Indefinite Delivery Indefinite Quantity"],
    "BPA": ["Blanket Purchase Agreement"],
    "GWA": ["Government-Wide Acquisition"],
    "GSA": ["General Services Administration"],
    "OASIS": ["One Acquisition Solution for Integrated Services"],
    "SEWP": ["Solutions for Enterprise-Wide Procurement"],
    "NAICS": ["North American Industry Classification System"],
    "CPFF": ["Cost Plus Fixed Fee"],
    "FFP": ["Firm Fixed Price"],
    "T&M": ["Time and Materials"],
}


class QueryExpander:
    """
    Expands search queries with acronym resolutions and domain synonyms
    for improved semantic search retrieval.
    """

    def __init__(self):
        self._acronym_map: Dict[str, str] = {}
        self._synonym_map: Dict[str, List[str]] = dict(DEFENSE_SYNONYMS)
        self._loaded = False
        self._load_acronyms()

    def _load_acronyms(self):
        """Load acronyms from acronyms.csv."""
        acronyms_path = E7_ANALYSIS / "acronyms.csv"
        if not acronyms_path.exists():
            logger.warning("acronyms.csv not found, using built-in synonyms only")
            self._loaded = True
            return

        try:
            with open(acronyms_path, "r", encoding="utf-8", errors="replace") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Try common column names
                    acronym = (
                        row.get("acronym", "")
                        or row.get("Acronym", "")
                        or row.get("abbreviation", "")
                        or row.get("term", "")
                    ).strip()

                    expansion = (
                        row.get("expansion", "")
                        or row.get("Expansion", "")
                        or row.get("definition", "")
                        or row.get("meaning", "")
                        or row.get("full_name", "")
                    ).strip()

                    if acronym and expansion and len(acronym) >= 2:
                        self._acronym_map[acronym.upper()] = expansion
                        # Also add to synonym map if not already there
                        if acronym.upper() not in self._synonym_map:
                            self._synonym_map[acronym.upper()] = [expansion]

            logger.info(f"Loaded {len(self._acronym_map)} acronyms from CSV")
        except Exception as e:
            logger.warning(f"Error loading acronyms: {e}")

        self._loaded = True

    def add_synonym(self, term: str, expansion: str):
        """Add a custom synonym/expansion."""
        key = term.upper()
        if key not in self._synonym_map:
            self._synonym_map[key] = []
        if expansion not in self._synonym_map[key]:
            self._synonym_map[key].append(expansion)

    def get_expansions(self, term: str) -> List[str]:
        """Get all known expansions for a term."""
        return self._synonym_map.get(term.upper(), [])

    def expand_query(self, query: str) -> ExpandedQuery:
        """
        Expand a query with acronym resolutions and synonyms.

        The expanded query appends resolved terms in parentheses
        without removing the original terms.
        """
        result = ExpandedQuery(original=query, expanded=query)

        # Find words/phrases that match known acronyms/synonyms
        # Process longer terms first to avoid partial matches
        terms_sorted = sorted(self._synonym_map.keys(), key=len, reverse=True)

        additions: List[str] = []
        query_upper = query.upper()

        for term in terms_sorted:
            # Check if term appears as a word boundary in the query
            pattern = r'\b' + re.escape(term) + r'\b'
            if re.search(pattern, query_upper):
                expansions = self._synonym_map[term]
                for exp in expansions:
                    if exp.upper() not in query_upper:
                        additions.append(exp)
                        if term in self._acronym_map:
                            result.acronyms_resolved.append(f"{term} = {exp}")
                        else:
                            result.synonyms_added.append(f"{term} → {exp}")

        if additions:
            result.expanded = query + " (" + "; ".join(additions) + ")"
            result.expansion_count = len(additions)

        return result

    def get_stats(self) -> Dict:
        """Get expander statistics."""
        return {
            "acronyms_loaded": len(self._acronym_map),
            "synonyms_loaded": len(self._synonym_map),
            "builtin_synonyms": len(DEFENSE_SYNONYMS),
            "csv_loaded": self._loaded,
        }


# Singleton
_expander_instance: Optional[QueryExpander] = None


def get_query_expander() -> QueryExpander:
    """Get query expander singleton."""
    global _expander_instance
    if _expander_instance is None:
        _expander_instance = QueryExpander()
    return _expander_instance
