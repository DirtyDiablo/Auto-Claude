"""Contact data models for BD contacts."""
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from .base import BaseDocument


class HierarchyTier(str, Enum):
    """Contact hierarchy tier classification."""
    TIER_1_EXECUTIVE = "Tier 1 - Executive"
    TIER_2_DIRECTOR = "Tier 2 - Director"
    TIER_3_PROGRAM_LEADERSHIP = "Tier 3 - Program Leadership"
    TIER_4_MANAGEMENT = "Tier 4 - Management"
    TIER_5_SENIOR_IC = "Tier 5 - Senior IC"
    TIER_6_IC = "Tier 6 - Individual Contributor"


class BDPriority(str, Enum):
    """BD priority classification for contacts."""
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    STANDARD = "Standard"


class DCGSProgram(str, Enum):
    """DCGS program assignments."""
    AF_LANGLEY = "AF DCGS - Langley"
    AF_WRIGHT_PATT = "AF DCGS - Wright-Patt"
    AF_PACAF = "AF DCGS - PACAF"
    AF_OTHER = "AF DCGS - Other"
    ARMY_DCGS_A = "Army DCGS-A"
    NAVY_DCGS_N = "Navy DCGS-N"
    CORPORATE_HQ = "Corporate HQ"
    ENTERPRISE_SECURITY = "Enterprise Security"
    UNASSIGNED = "Unassigned"


class LocationHub(str, Enum):
    """Geographic location hub classification."""
    HAMPTON_ROADS = "Hampton Roads"
    SAN_DIEGO = "San Diego Metro"
    DC_METRO = "DC Metro"
    DAYTON = "Dayton/Wright-Patt"
    OTHER_CONUS = "Other CONUS"
    OCONUS = "OCONUS"
    UNKNOWN = "Unknown"


class Contact(BaseDocument):
    """
    BD contact model with full classification.

    Matches the unified contacts_unified Qdrant collection schema.
    """
    first_name: str
    last_name: str
    job_title: Optional[str] = None
    company: str = "GDIT"
    email: Optional[str] = None
    phone: Optional[str] = None
    direct_phone: Optional[str] = None
    mobile_phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    program: DCGSProgram = DCGSProgram.UNASSIGNED
    hierarchy_tier: HierarchyTier = HierarchyTier.TIER_6_IC
    bd_priority: BDPriority = BDPriority.STANDARD
    location_hub: LocationHub = LocationHub.UNKNOWN
    functional_areas: List[str] = Field(default_factory=list)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def to_searchable_text(self) -> str:
        """Generate searchable text for embedding."""
        parts = [
            f"Name: {self.full_name}",
            f"Title: {self.job_title}" if self.job_title else "",
            f"Company: {self.company}",
            f"Program: {self.program.value}" if self.program else "",
            f"Location: {self.city}, {self.state}" if self.city else "",
            f"Tier: {self.hierarchy_tier.value}" if self.hierarchy_tier else "",
        ]
        return ". ".join(p for p in parts if p)
