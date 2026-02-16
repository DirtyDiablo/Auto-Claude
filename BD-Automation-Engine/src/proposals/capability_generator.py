"""Phase 35A — Capability Statement Generator

Auto-generate PTS capability statements tailored to specific opportunities:
  - Pull from Federal Programs DB, placements, certifications
  - Sections: Company Overview, Core Capabilities, Past Performance, Differentiators, Certs/Clearances
  - Template variants: 1-page summary, 2-page detailed, full capability brief
  - Dynamic content based on target program and agency
  - SDVOSB/VOSB status prominently featured
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# =========================================
# DATA CLASSES
# =========================================


class TemplateVariant(str, Enum):
    ONE_PAGE = "one_page"
    TWO_PAGE = "two_page"
    FULL_BRIEF = "full_brief"


@dataclass
class CapabilitySection:
    title: str
    content: str
    order: int = 0
    bullet_points: List[str] = field(default_factory=list)


@dataclass
class CapabilityStatement:
    id: str
    program: str
    agency: str
    variant: TemplateVariant
    sections: List[CapabilitySection] = field(default_factory=list)
    generated_at: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    word_count: int = 0


# =========================================
# COMPANY PROFILE
# =========================================

COMPANY_PROFILE = {
    "name": "PTS (Precise Talent Solutions)",
    "certifications": ["SDVOSB", "VOSB"],
    "cage_code": "TBD",
    "duns": "TBD",
    "uei": "TBD",
    "naics_codes": [
        "541512",  # Computer Systems Design Services
        "541611",  # Administrative Management Consulting
        "541519",  # Other Computer Related Services
        "561320",  # Temporary Help Services
        "541330",  # Engineering Services
    ],
    "core_capabilities": [
        "Intelligence Systems Staffing & Integration",
        "ISR Mission Support & Operations",
        "C4ISR Systems Engineering",
        "Cybersecurity & Information Assurance",
        "Cloud Migration & DevSecOps",
        "Data Analytics & Machine Learning",
        "Program Management & Technical Leadership",
        "Full Lifecycle Talent Acquisition",
    ],
    "differentiators": [
        "Service-Disabled Veteran-Owned Small Business (SDVOSB)",
        "Deep domain expertise in defense intelligence programs",
        "Proprietary BD intelligence platform with 8,400+ indexed contacts",
        "Average placement time 40% faster than industry average",
        "95%+ placement retention rate across cleared programs",
        "Direct relationships with program leadership across DCGS, NGEN, GBSD",
    ],
    "clearance_capabilities": [
        "TS/SCI with CI Polygraph",
        "TS/SCI",
        "Top Secret",
        "Secret",
        "Public Trust",
    ],
}


# =========================================
# SECTION GENERATORS
# =========================================


def _generate_company_overview(
    program: str, agency: str, variant: TemplateVariant
) -> CapabilitySection:
    """Generate company overview section."""
    profile = COMPANY_PROFILE
    certs = ", ".join(profile["certifications"])

    if variant == TemplateVariant.ONE_PAGE:
        content = (
            f"{profile['name']} is a {certs}-certified firm specializing in mission-critical "
            f"staffing and technical solutions for {agency} programs including {program}. "
            f"Our team brings deep domain expertise in defense intelligence, ISR operations, "
            f"and cleared technical staffing."
        )
    else:
        content = (
            f"{profile['name']} is a {certs}-certified small business delivering mission-critical "
            f"staffing and technical solutions to the Department of Defense and Intelligence Community. "
            f"With deep expertise supporting programs like {program} for {agency}, PTS provides "
            f"rapid deployment of cleared professionals who integrate seamlessly into operational environments.\n\n"
            f"Our proprietary intelligence platform indexes over 8,400 cleared professionals, enabling "
            f"precision matching of talent to mission requirements with an average placement time "
            f"40% faster than industry benchmarks."
        )

    return CapabilitySection(
        title="Company Overview",
        content=content,
        order=1,
        bullet_points=[f"CAGE Code: {profile['cage_code']}", f"UEI: {profile['uei']}"],
    )


def _generate_core_capabilities(
    program: str,
    agency: str,
    variant: TemplateVariant,
    program_data: Optional[dict] = None,
) -> CapabilitySection:
    """Generate core capabilities section."""
    capabilities = COMPANY_PROFILE["core_capabilities"]

    # Customize based on program data
    if program_data:
        focus_areas = program_data.get("focus_areas", [])
        if focus_areas:
            capabilities = focus_areas[:4] + capabilities[:4]

    if variant == TemplateVariant.ONE_PAGE:
        capabilities = capabilities[:5]

    content = f"PTS delivers specialized capabilities aligned with {program} mission requirements:"
    return CapabilitySection(
        title="Core Capabilities",
        content=content,
        order=2,
        bullet_points=capabilities,
    )


def _generate_past_performance_section(
    program: str,
    variant: TemplateVariant,
    placements: Optional[List[dict]] = None,
) -> CapabilitySection:
    """Generate past performance section."""
    if placements:
        count = len(placements)
        programs = list({p.get("program", "N/A") for p in placements})
        content = (
            f"PTS has successfully placed {count} cleared professionals across "
            f"{len(programs)} programs including {', '.join(programs[:5])}."
        )
        bullets = []
        for p in placements[:5]:
            bullets.append(
                f"{p.get('title', 'Analyst')} — {p.get('program', 'N/A')} "
                f"({p.get('clearance', 'TS/SCI')})"
            )
    else:
        content = (
            f"PTS maintains a proven track record supporting defense intelligence programs "
            f"with cleared professionals across all classification levels."
        )
        bullets = [
            "500+ successful placements across DoD/IC programs",
            "95%+ retention rate on cleared positions",
            "Active support across DCGS, NGEN, GBSD, and 15+ programs",
        ]

    if variant == TemplateVariant.ONE_PAGE:
        bullets = bullets[:3]

    return CapabilitySection(
        title="Past Performance",
        content=content,
        order=3,
        bullet_points=bullets,
    )


def _generate_differentiators(
    program: str, variant: TemplateVariant
) -> CapabilitySection:
    """Generate differentiators section."""
    diffs = COMPANY_PROFILE["differentiators"]
    if variant == TemplateVariant.ONE_PAGE:
        diffs = diffs[:3]

    return CapabilitySection(
        title="Differentiators",
        content=f"Key advantages PTS brings to {program}:",
        order=4,
        bullet_points=diffs,
    )


def _generate_certs_clearances(variant: TemplateVariant) -> CapabilitySection:
    """Generate certifications and clearances section."""
    profile = COMPANY_PROFILE
    naics = ", ".join(profile["naics_codes"])
    clearances = profile["clearance_capabilities"]

    content = f"NAICS Codes: {naics}"
    bullets = [f"Certifications: {', '.join(profile['certifications'])}"]
    bullets.extend([f"Clearance Level: {c}" for c in clearances])

    if variant == TemplateVariant.ONE_PAGE:
        bullets = bullets[:4]

    return CapabilitySection(
        title="Certifications & Clearances",
        content=content,
        order=5,
        bullet_points=bullets,
    )


# =========================================
# GENERATOR
# =========================================


class CapabilityStatementGenerator:
    """Auto-generate PTS capability statements."""

    def __init__(self, knowledge_client: Any = None):
        self._knowledge = knowledge_client
        self._history: List[CapabilityStatement] = []

    def set_knowledge_client(self, client: Any) -> None:
        self._knowledge = client

    async def generate(
        self,
        program: str,
        agency: str = "",
        variant: TemplateVariant = TemplateVariant.TWO_PAGE,
        placements: Optional[List[dict]] = None,
        program_data: Optional[dict] = None,
    ) -> CapabilityStatement:
        """Generate a capability statement for a target program."""
        if not agency:
            agency = program_data.get("agency", "DoD") if program_data else "DoD"

        # Fetch program data from knowledge base if available
        if not program_data and self._knowledge:
            program_data = await self._fetch_program_data(program)

        sections = [
            _generate_company_overview(program, agency, variant),
            _generate_core_capabilities(program, agency, variant, program_data),
            _generate_past_performance_section(program, variant, placements),
            _generate_differentiators(program, variant),
            _generate_certs_clearances(variant),
        ]

        word_count = sum(
            len(s.content.split()) + sum(len(b.split()) for b in s.bullet_points)
            for s in sections
        )

        statement = CapabilityStatement(
            id=f"cap-{program.lower().replace(' ', '-')}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            program=program,
            agency=agency,
            variant=variant,
            sections=sections,
            generated_at=datetime.now(timezone.utc).isoformat(),
            word_count=word_count,
            metadata={
                "company": COMPANY_PROFILE["name"],
                "certifications": COMPANY_PROFILE["certifications"],
                "template_variant": variant.value,
            },
        )

        self._history.append(statement)
        logger.info(
            f"Generated {variant.value} capability statement for {program} ({word_count} words)"
        )
        return statement

    async def generate_batch(
        self,
        programs: List[str],
        variant: TemplateVariant = TemplateVariant.TWO_PAGE,
    ) -> List[CapabilityStatement]:
        """Generate capability statements for multiple programs."""
        results = []
        for prog in programs:
            stmt = await self.generate(prog, variant=variant)
            results.append(stmt)
        return results

    def get_history(self) -> List[CapabilityStatement]:
        """Return generation history."""
        return list(self._history)

    def get_templates(self) -> List[Dict[str, str]]:
        """Return available template variants."""
        return [
            {
                "id": "one_page",
                "name": "1-Page Summary",
                "description": "Concise overview for quick briefs",
            },
            {
                "id": "two_page",
                "name": "2-Page Detailed",
                "description": "Standard capability statement",
            },
            {
                "id": "full_brief",
                "name": "Full Capability Brief",
                "description": "Comprehensive multi-section brief",
            },
        ]

    def export_to_dict(self, statement: CapabilityStatement) -> Dict[str, Any]:
        """Export statement to a serializable dictionary (for DOCX generation)."""
        return {
            "id": statement.id,
            "program": statement.program,
            "agency": statement.agency,
            "variant": statement.variant.value,
            "generated_at": statement.generated_at,
            "word_count": statement.word_count,
            "sections": [
                {
                    "title": s.title,
                    "content": s.content,
                    "order": s.order,
                    "bullet_points": s.bullet_points,
                }
                for s in statement.sections
            ],
            "metadata": statement.metadata,
        }

    async def _fetch_program_data(self, program: str) -> Optional[dict]:
        """Fetch program info from knowledge base."""
        if self._knowledge and hasattr(self._knowledge, "search"):
            try:
                results = await self._knowledge.search(
                    program, collection="programs", limit=1
                )
                if results:
                    return results[0] if isinstance(results, list) else results
            except Exception as e:
                logger.warning(f"Could not fetch program data for {program}: {e}")
        return None


# =========================================
# SINGLETON
# =========================================

_generator: Optional[CapabilityStatementGenerator] = None


def get_capability_generator() -> CapabilityStatementGenerator:
    global _generator
    if _generator is None:
        _generator = CapabilityStatementGenerator()
    return _generator
