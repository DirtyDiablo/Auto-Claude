"""Phase 35A — Compliance Matrix Generator

Parse RFP/SOW documents to extract requirements and generate compliance matrices:
  - Requirement → Section → Compliance Status → Evidence
  - Auto-map requirements to PTS capabilities
  - Gap analysis: requirements PTS cannot meet
  - Teaming recommendation for gaps
  - Section L/M mapping for federal proposals
  - Export to XLSX for team collaboration
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# =========================================
# DATA CLASSES
# =========================================


class ComplianceStatus(str, Enum):
    COMPLIANT = "compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    NON_COMPLIANT = "non_compliant"
    NOT_APPLICABLE = "not_applicable"


class RequirementType(str, Enum):
    TECHNICAL = "technical"
    MANAGEMENT = "management"
    STAFFING = "staffing"
    CLEARANCE = "clearance"
    EXPERIENCE = "experience"
    CERTIFICATION = "certification"
    PAST_PERFORMANCE = "past_performance"
    OTHER = "other"


@dataclass
class ComplianceRow:
    """Single requirement compliance entry."""

    requirement_id: str
    requirement_text: str
    section_ref: str = ""  # RFP section (e.g., "L.5.2", "M.3.1")
    requirement_type: RequirementType = RequirementType.OTHER
    compliance_status: ComplianceStatus = ComplianceStatus.COMPLIANT
    evidence: str = ""
    proposal_section: str = ""  # Where addressed in our proposal
    notes: str = ""
    confidence: float = 0.0  # 0-1 confidence in assessment


@dataclass
class GapAnalysis:
    """Requirement gap that PTS cannot currently meet."""

    requirement_id: str
    requirement_text: str
    gap_description: str
    severity: str = "medium"  # critical, high, medium, low
    mitigation: str = ""
    teaming_needed: bool = False


@dataclass
class TeamingRecommendation:
    """Recommendation for teaming partner to fill gaps."""

    gap_id: str
    capability_needed: str
    partner_type: str = ""  # e.g., "large prime", "SB subcontractor"
    recommended_naics: str = ""
    rationale: str = ""


@dataclass
class ComplianceMatrix:
    """Complete compliance matrix for an RFP."""

    id: str
    rfp_title: str
    rows: List[ComplianceRow] = field(default_factory=list)
    gaps: List[GapAnalysis] = field(default_factory=list)
    teaming_recommendations: List[TeamingRecommendation] = field(default_factory=list)
    total_requirements: int = 0
    compliant_count: int = 0
    partial_count: int = 0
    non_compliant_count: int = 0
    compliance_rate: float = 0.0
    generated_at: str = ""


# =========================================
# PTS CAPABILITY MAP
# =========================================

PTS_CAPABILITIES = {
    "staffing": {
        "keywords": [
            "staffing",
            "personnel",
            "workforce",
            "talent",
            "recruitment",
            "hiring",
        ],
        "evidence": "PTS maintains 8,400+ indexed cleared professionals with average placement time 40% faster than industry.",
    },
    "intelligence": {
        "keywords": [
            "intelligence",
            "isr",
            "sigint",
            "geoint",
            "humint",
            "analysis",
            "dcgs",
        ],
        "evidence": "PTS supports 15+ intelligence programs including DCGS, with 500+ successful intelligence analyst placements.",
    },
    "cybersecurity": {
        "keywords": ["cyber", "ia", "information assurance", "security", "rmf", "stig"],
        "evidence": "PTS provides cleared cybersecurity professionals across DoD/IC with TS/SCI CI Poly capabilities.",
    },
    "engineering": {
        "keywords": [
            "systems engineer",
            "software engineer",
            "devops",
            "devsecops",
            "cloud",
            "aws",
        ],
        "evidence": "PTS delivers senior systems and software engineers for C4ISR and cloud migration programs.",
    },
    "cleared_workforce": {
        "keywords": [
            "clearance",
            "ts/sci",
            "top secret",
            "secret",
            "polygraph",
            "cleared",
        ],
        "evidence": "PTS workforce spans all clearance levels from Public Trust to TS/SCI with CI Polygraph.",
    },
    "program_management": {
        "keywords": [
            "program management",
            "project management",
            "pmp",
            "agile",
            "scrum",
        ],
        "evidence": "PTS provides PMP-certified program managers with DoD acquisition experience.",
    },
    "past_performance": {
        "keywords": [
            "past performance",
            "cpars",
            "ppirs",
            "experience",
            "track record",
        ],
        "evidence": "PTS maintains Satisfactory or above CPARS ratings across all active contracts.",
    },
    "small_business": {
        "keywords": ["sdvosb", "vosb", "small business", "set-aside", "veteran"],
        "evidence": "PTS is a certified SDVOSB/VOSB, eligible for VA and DoD set-aside contracts.",
    },
}


# =========================================
# REQUIREMENT EXTRACTION
# =========================================

_SECTION_PATTERNS = [
    re.compile(r"(?:Section\s+)?([LM]\.\d+(?:\.\d+)*)", re.IGNORECASE),
    re.compile(r"(?:Para(?:graph)?\s+)?(\d+\.\d+(?:\.\d+)*)", re.IGNORECASE),
    re.compile(r"(SOW\s+\d+(?:\.\d+)*)", re.IGNORECASE),
]

_REQUIREMENT_INDICATORS = [
    "shall",
    "must",
    "required",
    "mandatory",
    "will provide",
    "contractor shall",
    "offeror shall",
    "vendor shall",
    "is required to",
    "are required to",
]


def extract_requirements(document_text: str) -> List[Dict[str, str]]:
    """Extract requirements from RFP/SOW text."""
    requirements = []
    lines = document_text.split("\n")
    req_id = 0

    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if not line_stripped:
            continue

        # Check if line contains requirement indicators
        line_lower = line_stripped.lower()
        is_requirement = any(ind in line_lower for ind in _REQUIREMENT_INDICATORS)

        if not is_requirement:
            continue

        req_id += 1

        # Extract section reference
        section_ref = ""
        for pattern in _SECTION_PATTERNS:
            match = pattern.search(line_stripped)
            if match:
                section_ref = match.group(1)
                break

        # Classify requirement type
        req_type = _classify_requirement(line_lower)

        requirements.append(
            {
                "id": f"REQ-{req_id:03d}",
                "text": line_stripped,
                "section_ref": section_ref,
                "type": req_type,
            }
        )

    return requirements


def _classify_requirement(text: str) -> str:
    """Classify requirement type from text."""
    type_keywords = {
        "clearance": ["clearance", "cleared", "polygraph", "ts/sci", "secret"],
        "staffing": ["staffing", "personnel", "workforce", "labor", "fte"],
        "technical": [
            "technical",
            "system",
            "software",
            "engineer",
            "design",
            "develop",
        ],
        "management": ["manage", "program management", "project", "schedule", "report"],
        "experience": ["experience", "years", "past performance", "track record"],
        "certification": ["certif", "pmp", "cissp", "comptia", "itil"],
        "past_performance": [
            "cpars",
            "ppirs",
            "past performance",
            "contract reference",
        ],
    }
    for req_type, keywords in type_keywords.items():
        if any(kw in text for kw in keywords):
            return req_type
    return "other"


# =========================================
# COMPLIANCE ASSESSMENT
# =========================================


def _assess_compliance(requirement_text: str) -> tuple:
    """Assess PTS compliance against a requirement, returns (status, evidence, confidence)."""
    text_lower = requirement_text.lower()

    best_match = None
    best_score = 0

    for cap_name, cap_data in PTS_CAPABILITIES.items():
        score = sum(1 for kw in cap_data["keywords"] if kw in text_lower)
        if score > best_score:
            best_score = score
            best_match = cap_data

    if best_score >= 2:
        return (
            ComplianceStatus.COMPLIANT,
            best_match["evidence"],
            min(0.95, 0.6 + best_score * 0.1),
        )
    elif best_score == 1:
        return ComplianceStatus.PARTIALLY_COMPLIANT, best_match["evidence"], 0.5
    else:
        return ComplianceStatus.NON_COMPLIANT, "", 0.2


# =========================================
# GENERATOR
# =========================================


class ComplianceMatrixGenerator:
    """Generate compliance matrices from RFP/SOW documents."""

    def __init__(self, knowledge_client: Any = None):
        self._knowledge = knowledge_client
        self._history: List[ComplianceMatrix] = []

    def set_knowledge_client(self, client: Any) -> None:
        self._knowledge = client

    async def generate_from_text(
        self,
        rfp_title: str,
        document_text: str,
    ) -> ComplianceMatrix:
        """Generate compliance matrix from RFP/SOW text."""
        raw_reqs = extract_requirements(document_text)
        return await self._build_matrix(rfp_title, raw_reqs)

    async def generate_from_requirements(
        self,
        rfp_title: str,
        requirements: List[Dict[str, str]],
    ) -> ComplianceMatrix:
        """Generate compliance matrix from pre-parsed requirements list."""
        return await self._build_matrix(rfp_title, requirements)

    async def _build_matrix(
        self,
        rfp_title: str,
        raw_reqs: List[Dict[str, str]],
    ) -> ComplianceMatrix:
        """Build the compliance matrix from extracted requirements."""
        rows = []
        gaps = []
        teaming = []

        for req in raw_reqs:
            status, evidence, confidence = _assess_compliance(req.get("text", ""))

            row = ComplianceRow(
                requirement_id=req.get("id", ""),
                requirement_text=req.get("text", ""),
                section_ref=req.get("section_ref", ""),
                requirement_type=RequirementType(req.get("type", "other")),
                compliance_status=status,
                evidence=evidence,
                confidence=confidence,
            )
            rows.append(row)

            # Track gaps
            if status == ComplianceStatus.NON_COMPLIANT:
                gap = GapAnalysis(
                    requirement_id=req.get("id", ""),
                    requirement_text=req.get("text", ""),
                    gap_description=f"PTS does not currently have demonstrated capability for: {req.get('text', '')[:100]}",
                    severity="high"
                    if req.get("type") in ("clearance", "technical")
                    else "medium",
                    teaming_needed=True,
                )
                gaps.append(gap)

                teaming.append(
                    TeamingRecommendation(
                        gap_id=req.get("id", ""),
                        capability_needed=req.get("text", "")[:200],
                        partner_type="specialized subcontractor",
                        rationale=f"PTS requires teaming partner to address {req.get('type', 'this')} requirement.",
                    )
                )
            elif status == ComplianceStatus.PARTIALLY_COMPLIANT:
                gap = GapAnalysis(
                    requirement_id=req.get("id", ""),
                    requirement_text=req.get("text", ""),
                    gap_description=f"PTS has partial capability; may need augmentation for: {req.get('text', '')[:100]}",
                    severity="low",
                    mitigation="Augment with targeted recruitment or teaming arrangement.",
                )
                gaps.append(gap)

        compliant = sum(
            1 for r in rows if r.compliance_status == ComplianceStatus.COMPLIANT
        )
        partial = sum(
            1
            for r in rows
            if r.compliance_status == ComplianceStatus.PARTIALLY_COMPLIANT
        )
        non_compliant = sum(
            1 for r in rows if r.compliance_status == ComplianceStatus.NON_COMPLIANT
        )
        total = len(rows)
        rate = ((compliant + partial * 0.5) / total * 100) if total > 0 else 0.0

        matrix = ComplianceMatrix(
            id=f"cm-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            rfp_title=rfp_title,
            rows=rows,
            gaps=[g for g in gaps if g.severity in ("critical", "high", "medium")],
            teaming_recommendations=teaming,
            total_requirements=total,
            compliant_count=compliant,
            partial_count=partial,
            non_compliant_count=non_compliant,
            compliance_rate=round(rate, 1),
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

        self._history.append(matrix)
        logger.info(
            f"Generated compliance matrix for '{rfp_title}': "
            f"{compliant}/{total} compliant ({rate:.1f}%)"
        )
        return matrix

    def get_section_l_m_mapping(
        self, matrix: ComplianceMatrix
    ) -> Dict[str, List[ComplianceRow]]:
        """Map requirements to Section L (instructions) and Section M (evaluation) groupings."""
        mapping: Dict[str, List[ComplianceRow]] = {"L": [], "M": [], "other": []}
        for row in matrix.rows:
            ref = row.section_ref.upper()
            if ref.startswith("L"):
                mapping["L"].append(row)
            elif ref.startswith("M"):
                mapping["M"].append(row)
            else:
                mapping["other"].append(row)
        return mapping

    def get_history(self) -> List[ComplianceMatrix]:
        return list(self._history)

    def export_to_dict(self, matrix: ComplianceMatrix) -> Dict[str, Any]:
        """Export matrix to serializable dictionary (for XLSX generation)."""
        return {
            "id": matrix.id,
            "rfp_title": matrix.rfp_title,
            "total_requirements": matrix.total_requirements,
            "compliant_count": matrix.compliant_count,
            "partial_count": matrix.partial_count,
            "non_compliant_count": matrix.non_compliant_count,
            "compliance_rate": matrix.compliance_rate,
            "generated_at": matrix.generated_at,
            "rows": [
                {
                    "requirement_id": r.requirement_id,
                    "requirement_text": r.requirement_text,
                    "section_ref": r.section_ref,
                    "type": r.requirement_type.value,
                    "compliance_status": r.compliance_status.value,
                    "evidence": r.evidence,
                    "confidence": r.confidence,
                }
                for r in matrix.rows
            ],
            "gaps": [
                {
                    "requirement_id": g.requirement_id,
                    "gap_description": g.gap_description,
                    "severity": g.severity,
                    "teaming_needed": g.teaming_needed,
                }
                for g in matrix.gaps
            ],
            "teaming_recommendations": [
                {
                    "gap_id": t.gap_id,
                    "capability_needed": t.capability_needed,
                    "partner_type": t.partner_type,
                    "rationale": t.rationale,
                }
                for t in matrix.teaming_recommendations
            ],
        }


# =========================================
# SINGLETON
# =========================================

_generator: Optional[ComplianceMatrixGenerator] = None


def get_compliance_generator() -> ComplianceMatrixGenerator:
    global _generator
    if _generator is None:
        _generator = ComplianceMatrixGenerator()
    return _generator
