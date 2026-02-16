"""
BD-specific entity extraction for LightRAG.
Extracts contractors, programs, contacts, locations, and technologies.
"""

import re
from enum import Enum
from typing import List, Dict, Optional
from dataclasses import dataclass


class EntityType(str, Enum):
    """Types of BD entities."""

    CONTRACTOR = "contractor"
    PROGRAM = "program"
    CONTACT = "contact"
    LOCATION = "location"
    TECHNOLOGY = "technology"
    CONTRACT = "contract"
    AGENCY = "agency"


@dataclass
class Entity:
    """Represents an extracted entity."""

    name: str
    type: EntityType
    aliases: List[str]
    confidence: float
    context: str  # Surrounding text


@dataclass
class Relationship:
    """Represents a relationship between entities."""

    source: str
    target: str
    relationship_type: str
    confidence: float
    evidence: str


class BDEntityExtractor:
    """
    Extract BD-specific entities from documents.
    Used to enhance LightRAG entity extraction.
    """

    # Known contractors
    CONTRACTORS = {
        "gdit": [
            "General Dynamics IT",
            "General Dynamics Information Technology",
            "GDIT",
        ],
        "leidos": ["Leidos", "Leidos Holdings"],
        "saic": ["SAIC", "Science Applications International Corporation"],
        "northrop": ["Northrop Grumman", "NGC", "Northrop"],
        "raytheon": ["Raytheon", "Raytheon Technologies", "RTX"],
        "lockheed": ["Lockheed Martin", "LMT", "Lockheed"],
        "bae": ["BAE Systems", "BAE"],
        "booz": ["Booz Allen", "Booz Allen Hamilton", "BAH"],
        "l3harris": ["L3Harris", "L3 Harris", "L3Harris Technologies"],
        "caci": ["CACI", "CACI International"],
        "mantech": ["ManTech", "ManTech International"],
        "peraton": ["Peraton"],
        "parsons": ["Parsons", "Parsons Corporation"],
        "jacobs": ["Jacobs", "Jacobs Engineering"],
        "kbr": ["KBR", "Kellogg Brown & Root"],
        "serco": ["Serco", "Serco Inc"],
        "aecom": ["AECOM"],
        "accenture_federal": ["Accenture Federal Services", "AFS"],
    }

    # Known programs
    PROGRAMS = {
        "dcgs": ["DCGS", "Distributed Common Ground System", "AF DCGS", "Army DCGS"],
        "bices": [
            "BICES",
            "Battlefield Information Collection and Exploitation System",
        ],
        "gsm_o": ["GSM-O", "Global Solutions Management - Operations"],
        "gbsd": ["GBSD", "Ground Based Strategic Deterrent", "Sentinel"],
        "abms": ["ABMS", "Advanced Battle Management System"],
        "jadc2": ["JADC2", "Joint All-Domain Command and Control"],
        "cms": ["CMS", "Combat Mission Systems"],
        "ngen": ["NGEN", "Next Generation Enterprise Network"],
        "disa_encore": ["ENCORE", "ENCORE III"],
        "ites": ["ITES", "IT Enterprise Solutions"],
        "alliant": ["Alliant 2", "Alliant"],
        "sewp": ["SEWP", "SEWP V"],
        "oasis": ["OASIS", "OASIS+"],
        "stars": ["STARS", "STARS III"],
    }

    # Known locations
    LOCATIONS = {
        "langley": ["Langley", "Langley AFB", "Joint Base Langley-Eustis"],
        "san_diego": ["San Diego", "NAVWAR San Diego"],
        "norfolk": ["Norfolk", "Naval Station Norfolk"],
        "fort_meade": ["Fort Meade", "NSA", "Fort George G. Meade"],
        "pentagon": ["Pentagon", "Arlington"],
        "colorado_springs": ["Colorado Springs", "Peterson AFB", "Schriever AFB"],
        "huntsville": ["Huntsville", "Redstone Arsenal"],
        "tampa": ["Tampa", "MacDill AFB", "CENTCOM"],
        "omaha": ["Omaha", "Offutt AFB", "STRATCOM"],
        "hawaii": ["Hawaii", "Pearl Harbor", "PACOM"],
        "ramstein": ["Ramstein", "Ramstein AB"],
        "beale": ["Beale", "Beale AFB"],
    }

    # Known technologies
    TECHNOLOGIES = {
        "isr": ["ISR", "Intelligence, Surveillance, Reconnaissance"],
        "sigint": ["SIGINT", "Signals Intelligence"],
        "cyber": ["Cyber", "Cybersecurity", "Cyber Operations"],
        "c4isr": ["C4ISR", "C4ISR Systems"],
        "ai_ml": ["AI/ML", "Artificial Intelligence", "Machine Learning"],
        "cloud": ["Cloud", "Cloud Computing", "AWS", "Azure", "GovCloud"],
        "zero_trust": ["Zero Trust", "ZTA"],
        "devsecops": ["DevSecOps", "DevOps"],
        "5g": ["5G", "5G Networks"],
        "space": ["Space", "Space Systems"],
        "electronic_warfare": ["EW", "Electronic Warfare"],
    }

    # Known agencies
    AGENCIES = {
        "air_force": ["Air Force", "USAF", "Department of the Air Force"],
        "army": ["Army", "US Army", "Department of the Army"],
        "navy": ["Navy", "US Navy", "Department of the Navy"],
        "dod": ["DoD", "Department of Defense", "OSD"],
        "disa": ["DISA", "Defense Information Systems Agency"],
        "nsa": ["NSA", "National Security Agency"],
        "cia": ["CIA", "Central Intelligence Agency"],
        "nro": ["NRO", "National Reconnaissance Office"],
        "nga": ["NGA", "National Geospatial-Intelligence Agency"],
        "dia": ["DIA", "Defense Intelligence Agency"],
    }

    # Relationship patterns - flexible patterns for BD document extraction
    RELATIONSHIP_PATTERNS = [
        # Prime contractor patterns
        (
            r"(\w+)\s+(?:is|are)\s+(?:the\s+)?prime\s+(?:contractor\s+)?(?:for|on)\s+(\w+)",
            "primes",
        ),
        (
            r"(\w+)\s+(?:has\s+been\s+)?awarded\s+(?:the\s+)?prime\s+(?:contractor\s+)?(?:role|contract)?\s*(?:for|on)?\s*(\w+)?",
            "primes",
        ),
        (r"(\w+)\s+primes?\s+(?:on|for)\s+(\w+)", "primes"),
        # Subcontractor patterns
        (
            r"(\w+)\s+(?:is|are)\s+(?:a\s+)?(?:key\s+)?subcontractor\s+(?:to|for|on|providing)?\s*(\w+)?",
            "subcontracts",
        ),
        (r"(\w+)\s+subcontracts?\s+(?:to|for|on)\s+(\w+)", "subcontracts"),
        # Teaming patterns
        (r"(\w+)\s+(?:and|&)\s+(\w+)\s+(?:are\s+)?team(?:ing|ed)", "teams_with"),
        (r"(\w+)\s+team(?:s|ed|ing)\s+with\s+(\w+)", "teams_with"),
        # Partner patterns
        (r"(\w+)\s+partner(?:s|ed|ing)\s+with\s+(\w+)", "partners_with"),
        # Work patterns
        (r"(\w+)\s+work(?:s|ing|ed)\s+(?:on|with)\s+(\w+)", "works_on"),
        (r"(\w+)\s+support(?:s|ing|ed)\s+(\w+)", "supports"),
        # M&A patterns
        (r"(\w+)\s+acquired\s+(\w+)", "acquired"),
        (r"(\w+)\s+merged\s+with\s+(\w+)", "merged_with"),
    ]

    def __init__(self):
        """Initialize the entity extractor."""
        self._build_lookup_tables()

    def _build_lookup_tables(self):
        """Build reverse lookup tables for efficient matching."""
        self._alias_to_canonical = {}
        self._alias_to_type = {}

        for canonical, aliases in self.CONTRACTORS.items():
            for alias in aliases:
                self._alias_to_canonical[alias.lower()] = canonical
                self._alias_to_type[alias.lower()] = EntityType.CONTRACTOR

        for canonical, aliases in self.PROGRAMS.items():
            for alias in aliases:
                self._alias_to_canonical[alias.lower()] = canonical
                self._alias_to_type[alias.lower()] = EntityType.PROGRAM

        for canonical, aliases in self.LOCATIONS.items():
            for alias in aliases:
                self._alias_to_canonical[alias.lower()] = canonical
                self._alias_to_type[alias.lower()] = EntityType.LOCATION

        for canonical, aliases in self.TECHNOLOGIES.items():
            for alias in aliases:
                self._alias_to_canonical[alias.lower()] = canonical
                self._alias_to_type[alias.lower()] = EntityType.TECHNOLOGY

        for canonical, aliases in self.AGENCIES.items():
            for alias in aliases:
                self._alias_to_canonical[alias.lower()] = canonical
                self._alias_to_type[alias.lower()] = EntityType.AGENCY

    def extract_entities(self, text: str) -> List[Entity]:
        """
        Extract BD entities from text.

        Args:
            text: Document text to analyze

        Returns:
            List of extracted entities
        """
        entities = []
        text_lower = text.lower()

        # Check for known entities
        for alias, canonical in self._alias_to_canonical.items():
            if alias in text_lower:
                # Find the actual occurrence for context
                idx = text_lower.find(alias)
                context_start = max(0, idx - 50)
                context_end = min(len(text), idx + len(alias) + 50)
                context = text[context_start:context_end]

                entity = Entity(
                    name=canonical,
                    type=self._alias_to_type[alias],
                    aliases=[alias],
                    confidence=0.9,
                    context=context,
                )
                entities.append(entity)

        # Deduplicate by canonical name
        seen = set()
        unique_entities = []
        for entity in entities:
            if entity.name not in seen:
                seen.add(entity.name)
                unique_entities.append(entity)

        return unique_entities

    def extract_relationships(self, text: str) -> List[Relationship]:
        """
        Extract relationships between entities from text.

        Args:
            text: Document text to analyze

        Returns:
            List of extracted relationships
        """
        relationships = []

        for pattern, rel_type in self.RELATIONSHIP_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                source = match.group(1)
                target = match.group(2)

                # Try to normalize to canonical names
                source_canonical = self._alias_to_canonical.get(source.lower(), source)
                target_canonical = self._alias_to_canonical.get(target.lower(), target)

                relationships.append(
                    Relationship(
                        source=source_canonical,
                        target=target_canonical,
                        relationship_type=rel_type,
                        confidence=0.7,
                        evidence=match.group(0),
                    )
                )

        return relationships

    def enrich_document(self, text: str, include_metadata: bool = True) -> str:
        """
        Enrich document with entity tags for better LightRAG extraction.

        Args:
            text: Original document text
            include_metadata: Whether to prepend entity metadata

        Returns:
            Enriched document text
        """
        entities = self.extract_entities(text)
        relationships = self.extract_relationships(text)

        if not include_metadata:
            return text

        # Build metadata prefix
        metadata_parts = []

        # Group entities by type
        by_type: Dict[EntityType, List[str]] = {}
        for entity in entities:
            if entity.type not in by_type:
                by_type[entity.type] = []
            by_type[entity.type].append(entity.name)

        for entity_type, names in by_type.items():
            metadata_parts.append(f"[{entity_type.value.upper()}S: {', '.join(names)}]")

        # Add relationship summary
        if relationships:
            rel_summary = "; ".join(
                [
                    f"{r.source} {r.relationship_type} {r.target}"
                    for r in relationships[:5]  # Limit to 5
                ]
            )
            metadata_parts.append(f"[RELATIONSHIPS: {rel_summary}]")

        if metadata_parts:
            return "\n".join(metadata_parts) + "\n\n" + text
        return text

    def get_entity_info(self, entity_name: str) -> Optional[Dict]:
        """
        Get information about a known entity.

        Args:
            entity_name: Name or alias of entity

        Returns:
            Dict with entity information or None
        """
        canonical = self._alias_to_canonical.get(entity_name.lower())
        if not canonical:
            return None

        entity_type = self._alias_to_type.get(entity_name.lower())

        # Find all aliases
        aliases = []
        if entity_type == EntityType.CONTRACTOR:
            aliases = self.CONTRACTORS.get(canonical, [])
        elif entity_type == EntityType.PROGRAM:
            aliases = self.PROGRAMS.get(canonical, [])
        elif entity_type == EntityType.LOCATION:
            aliases = self.LOCATIONS.get(canonical, [])
        elif entity_type == EntityType.TECHNOLOGY:
            aliases = self.TECHNOLOGIES.get(canonical, [])
        elif entity_type == EntityType.AGENCY:
            aliases = self.AGENCIES.get(canonical, [])

        return {
            "canonical_name": canonical,
            "type": entity_type.value if entity_type else "unknown",
            "aliases": aliases,
        }

    def suggest_tags(self, text: str) -> List[str]:
        """
        Suggest tags for a document based on entities found.

        Args:
            text: Document text

        Returns:
            List of suggested tags
        """
        entities = self.extract_entities(text)
        tags = set()

        for entity in entities:
            tags.add(f"{entity.type.value}:{entity.name}")

        return list(tags)

    @classmethod
    def get_all_known_entities(cls) -> Dict[str, List[str]]:
        """Get all known entities by type."""
        return {
            "contractors": list(cls.CONTRACTORS.keys()),
            "programs": list(cls.PROGRAMS.keys()),
            "locations": list(cls.LOCATIONS.keys()),
            "technologies": list(cls.TECHNOLOGIES.keys()),
            "agencies": list(cls.AGENCIES.keys()),
        }
