"""
Contact Classifier Agent - Automatically classifies contacts by tier, program, priority, and location.

Part of the 8-agent CrewAI system for BD Intelligence.
"""

import re
from typing import Dict, List, Optional
from dataclasses import dataclass
import structlog

logger = structlog.get_logger(__name__)

# Import base agent
try:
    from .base_agent import BDAgent, AgentResponse
except ImportError:
    from base_agent import BDAgent, AgentResponse


# Classification patterns
TIER_PATTERNS = {
    1: [  # C-Suite / Flag Officers
        r"\b(ceo|cto|cio|cfo|coo|president|chairman|vice president|vp|svp|evp)\b",
        r"\b(general|admiral|lieutenant general|major general|rear admiral)\b",
        r"\b(chief .* officer|executive director|managing director)\b",
    ],
    2: [  # Directors / Senior Leaders
        r"\b(director|senior director|associate director|deputy director)\b",
        r"\b(colonel|captain|commander|lieutenant colonel)\b",
        r"\b(program manager|portfolio manager|division chief)\b",
    ],
    3: [  # Managers / Program Leadership
        r"\b(manager|senior manager|program lead)\b",
        r"\b(major|lieutenant commander)\b",
        r"\b(team lead|branch chief|section chief)\b",
    ],
    4: [  # Senior Individual Contributors
        r"\b(senior engineer|senior analyst|principal|lead architect)\b",
        r"\b(technical lead|subject matter expert|sme)\b",
        r"\b(senior consultant|senior specialist)\b",
    ],
    5: [  # Individual Contributors
        r"\b(engineer|analyst|developer|consultant)\b",
        r"\b(contractor|specialist|coordinator)\b",
    ],
    6: [  # Support / Entry Level
        r"\b(assistant|associate|intern|trainee|junior)\b",
        r"\b(support|administrative|clerk|technician)\b",
    ],
}

PROGRAM_KEYWORDS = {
    "AF DCGS - Langley": ["langley", "480th", "acc", "air combat command"],
    "AF DCGS - Wright-Patt": ["wright-patt", "nasic", "wright patterson"],
    "AF DCGS - PACAF": ["pacaf", "pacific air", "hickam", "hawaii"],
    "Army DCGS-A": ["dcgs-a", "army intelligence", "inscom", "fort huachuca"],
    "Navy DCGS-N": ["dcgs-n", "naval intelligence", "fleet", "norfolk"],
    "Corporate HQ": ["corporate", "headquarters", "hq", "arlington"],
    "Enterprise Security": ["cyber", "security", "infosec", "ciso"],
}

LOCATION_HUB_MAP = {
    "Hampton Roads": [
        "langley",
        "norfolk",
        "virginia beach",
        "hampton",
        "newport news",
    ],
    "San Diego Metro": ["san diego", "coronado", "point loma"],
    "DC Metro": ["washington", "arlington", "bethesda", "mclean", "reston", "tysons"],
    "Dayton/Wright-Patt": ["dayton", "wright-patt", "fairborn"],
    "OCONUS": ["oconus", "overseas", "germany", "japan", "korea", "uk"],
}


@dataclass
class ClassificationResult:
    """Result of contact classification."""

    hierarchy_tier: int
    tier_label: str
    program: str
    bd_priority: str
    location_hub: str
    confidence: float
    signals: List[str]


class ContactClassifierAgent(BDAgent):
    """
    Agent that classifies contacts based on title, company, and location.

    Classification dimensions:
    - Hierarchy Tier (1-6)
    - DCGS Program assignment
    - BD Priority (Critical, High, Medium, Standard)
    - Location Hub
    """

    def __init__(self):
        super().__init__(
            name="Contact Classifier Agent",
            description="Classify contacts by tier, program, priority, and location for BD targeting. "
            "Expert in organizational hierarchy and federal personnel structures.",
        )

    def classify_tier(self, title: str) -> tuple[int, str, List[str]]:
        """Classify contact hierarchy tier based on title."""
        title_lower = title.lower() if title else ""
        signals = []

        for tier, patterns in TIER_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, title_lower, re.IGNORECASE):
                    tier_labels = {
                        1: "Tier 1 - Executive",
                        2: "Tier 2 - Director",
                        3: "Tier 3 - Program Leadership",
                        4: "Tier 4 - Management",
                        5: "Tier 5 - Senior IC",
                        6: "Tier 6 - Individual Contributor",
                    }
                    signals.append(f"Title pattern match: {pattern}")
                    return tier, tier_labels[tier], signals

        return (
            6,
            "Tier 6 - Individual Contributor",
            ["No pattern match, defaulting to Tier 6"],
        )

    def classify_program(
        self, title: str, company: str, location: str
    ) -> tuple[str, List[str]]:
        """Classify which DCGS program the contact is associated with."""
        text = f"{title} {company} {location}".lower()
        signals = []

        for program, keywords in PROGRAM_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    signals.append(f"Program keyword: {keyword}")
                    return program, signals

        return "Unassigned", ["No program keywords found"]

    def classify_location_hub(self, city: str, state: str) -> tuple[str, List[str]]:
        """Classify location into geographic hubs."""
        location = f"{city} {state}".lower()
        signals = []

        for hub, keywords in LOCATION_HUB_MAP.items():
            for keyword in keywords:
                if keyword in location:
                    signals.append(f"Location keyword: {keyword}")
                    return hub, signals

        # State-based fallback
        if state:
            state_upper = state.upper()
            if state_upper in ["VA", "MD", "DC"]:
                return "DC Metro", [f"State: {state_upper}"]
            elif state_upper == "CA":
                return "San Diego Metro", [f"State: {state_upper}"]
            elif state_upper == "OH":
                return "Dayton/Wright-Patt", [f"State: {state_upper}"]
            elif state_upper == "HI":
                return "OCONUS", [f"State: {state_upper}"]

        return "Other CONUS", ["No location hub identified"]

    def calculate_bd_priority(self, tier: int, program: str) -> str:
        """Calculate BD priority based on tier and program."""
        # Critical: Tier 1-2 on active DCGS programs
        if tier <= 2 and program != "Unassigned":
            return "Critical"
        # High: Tier 3 on active programs OR Tier 1-2 unassigned
        elif tier <= 3 and program != "Unassigned":
            return "High"
        elif tier <= 2:
            return "High"
        # Medium: Tier 4 on active programs
        elif tier == 4 and program != "Unassigned":
            return "Medium"
        # Standard: Everyone else
        else:
            return "Standard"

    def classify_contact(
        self,
        first_name: str,
        last_name: str,
        job_title: str = "",
        company: str = "",
        city: str = "",
        state: str = "",
    ) -> ClassificationResult:
        """
        Classify a single contact across all dimensions.

        Returns:
            ClassificationResult with all classifications and confidence score
        """
        all_signals = []

        # Tier classification
        tier, tier_label, tier_signals = self.classify_tier(job_title)
        all_signals.extend(tier_signals)

        # Program classification
        program, program_signals = self.classify_program(
            job_title, company, f"{city} {state}"
        )
        all_signals.extend(program_signals)

        # Location hub
        location_hub, location_signals = self.classify_location_hub(city, state)
        all_signals.extend(location_signals)

        # BD Priority
        bd_priority = self.calculate_bd_priority(tier, program)

        # Confidence based on number of signals
        confidence = min(0.95, 0.3 + (len(all_signals) * 0.1))

        return ClassificationResult(
            hierarchy_tier=tier,
            tier_label=tier_label,
            program=program,
            bd_priority=bd_priority,
            location_hub=location_hub,
            confidence=confidence,
            signals=all_signals,
        )

    async def classify_batch(self, contacts: List[Dict]) -> List[Dict]:
        """
        Classify a batch of contacts.

        Args:
            contacts: List of contact dictionaries

        Returns:
            List of contacts with classification fields added
        """
        results = []

        for contact in contacts:
            classification = self.classify_contact(
                first_name=contact.get("first_name", ""),
                last_name=contact.get("last_name", ""),
                job_title=contact.get("job_title", ""),
                company=contact.get("company", ""),
                city=contact.get("city", ""),
                state=contact.get("state", ""),
            )

            # Add classification to contact
            classified_contact = {
                **contact,
                "hierarchy_tier": classification.tier_label,
                "program": classification.program,
                "bd_priority": classification.bd_priority,
                "location_hub": classification.location_hub,
                "classification_confidence": classification.confidence,
                "classification_signals": classification.signals,
            }
            results.append(classified_contact)

        logger.info("contacts_classified", count=len(results))
        return results

    async def process(
        self, query: str, context: Optional[Dict] = None
    ) -> AgentResponse:
        """Process a classification request."""
        # Check if we have contacts in context
        if context and "contacts" in context:
            classified = await self.classify_batch(context["contacts"])
            return AgentResponse(
                success=True,
                content=f"Classified {len(classified)} contacts",
                sources=[],
                confidence=0.9,
                agent_name=self.name,
                metadata={"classified_contacts": classified},
            )

        # Otherwise, provide classification guidance
        return AgentResponse(
            success=True,
            content=f"Contact classification agent ready. Provide contacts to classify: {query}",
            sources=[],
            confidence=1.0,
            agent_name=self.name,
            metadata={"available_classifications": list(TIER_PATTERNS.keys())},
        )


# CLI test
if __name__ == "__main__":
    pass

    agent = ContactClassifierAgent()

    # Test single classification
    result = agent.classify_contact(
        first_name="John",
        last_name="Smith",
        job_title="Senior Director, DCGS Programs",
        company="GDIT",
        city="Langley",
        state="VA",
    )

    logger.info(
        "classification_result",
        tier=result.tier_label,
        program=result.program,
        priority=result.bd_priority,
        location_hub=result.location_hub,
        confidence=round(result.confidence, 2),
        signals=result.signals,
    )
