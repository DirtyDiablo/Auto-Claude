"""Federal program data models."""

from pydantic import Field
from typing import Optional, List
from enum import Enum
from .base import BaseDocument


class PTSInvolvement(str, Enum):
    """PTS involvement status with program."""

    CURRENT = "Current"
    PAST = "Past"
    TARGET = "Target"
    NONE = "None"


class PriorityLevel(str, Enum):
    """Program priority level for BD focus."""

    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class FederalProgram(BaseDocument):
    """
    Federal program model for the programs_unified collection.

    Represents defense/intelligence programs for BD targeting.
    """

    program_name: str
    acronym: Optional[str] = None
    agency_owner: Optional[str] = None
    prime_contractor: Optional[str] = None
    known_subcontractors: List[str] = Field(default_factory=list)
    contract_value: Optional[str] = None
    contract_vehicle: Optional[str] = None
    pop_start: Optional[str] = None
    pop_end: Optional[str] = None
    key_locations: List[str] = Field(default_factory=list)
    clearance_requirements: Optional[str] = None
    typical_roles: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    program_type: Optional[str] = None
    pts_involvement: PTSInvolvement = PTSInvolvement.NONE
    priority_level: PriorityLevel = PriorityLevel.MEDIUM
    pain_points: List[str] = Field(default_factory=list)
    confidence_level: Optional[str] = None

    def to_searchable_text(self) -> str:
        """Generate searchable text for embedding."""
        parts = [
            f"Program: {self.program_name}",
            f"Acronym: {self.acronym}" if self.acronym else "",
            f"Agency: {self.agency_owner}" if self.agency_owner else "",
            f"Prime: {self.prime_contractor}" if self.prime_contractor else "",
            f"Locations: {', '.join(self.key_locations)}" if self.key_locations else "",
            f"Keywords: {', '.join(self.keywords)}" if self.keywords else "",
        ]
        return ". ".join(p for p in parts if p)
