"""Tests for Phase 35A — Compliance Matrix Generator."""

import pytest

from src.proposals.compliance_matrix import (
    ComplianceMatrixGenerator,
    ComplianceMatrix,
    ComplianceRow,
    ComplianceStatus,
    RequirementType,
    GapAnalysis,
    TeamingRecommendation,
    PTS_CAPABILITIES,
    extract_requirements,
    get_compliance_generator,
)


# =========================================
# FIXTURES
# =========================================

@pytest.fixture
def generator():
    return ComplianceMatrixGenerator()


@pytest.fixture
def sample_rfp_text():
    return """
Section L.5.1: The contractor shall provide cleared intelligence analysts with TS/SCI clearances.
Section L.5.2: The contractor shall provide staffing for ISR mission support operations.
Section L.6.1: The contractor must demonstrate past performance on similar DCGS programs.
Section M.3.1: The contractor shall provide certified PMP project managers.
Section M.3.2: The vendor shall implement a quantum computing solution for data processing.
L.7.1: The offeror shall maintain cybersecurity compliance per NIST 800-171.
"""


@pytest.fixture
def sample_requirements():
    return [
        {"id": "REQ-001", "text": "Contractor shall provide TS/SCI cleared intelligence analysts", "section_ref": "L.5.1", "type": "clearance"},
        {"id": "REQ-002", "text": "Contractor shall provide staffing for ISR mission support", "section_ref": "L.5.2", "type": "staffing"},
        {"id": "REQ-003", "text": "Contractor must implement a quantum photonics array for satellite uplink", "section_ref": "L.6.1", "type": "technical"},
    ]


# =========================================
# CAPABILITIES MAP
# =========================================

class TestCapabilitiesMap:
    def test_has_staffing(self):
        assert "staffing" in PTS_CAPABILITIES

    def test_has_intelligence(self):
        assert "intelligence" in PTS_CAPABILITIES

    def test_has_small_business(self):
        assert "small_business" in PTS_CAPABILITIES

    def test_each_has_keywords_and_evidence(self):
        for cap_name, cap_data in PTS_CAPABILITIES.items():
            assert "keywords" in cap_data
            assert "evidence" in cap_data
            assert len(cap_data["keywords"]) > 0


# =========================================
# REQUIREMENT EXTRACTION
# =========================================

class TestRequirementExtraction:
    def test_extracts_from_text(self, sample_rfp_text):
        reqs = extract_requirements(sample_rfp_text)
        assert isinstance(reqs, list)
        assert len(reqs) >= 4  # At least the "shall" requirements

    def test_extracts_section_refs(self, sample_rfp_text):
        reqs = extract_requirements(sample_rfp_text)
        refs = [r["section_ref"] for r in reqs if r["section_ref"]]
        assert len(refs) > 0

    def test_assigns_ids(self, sample_rfp_text):
        reqs = extract_requirements(sample_rfp_text)
        for req in reqs:
            assert req["id"].startswith("REQ-")

    def test_classifies_types(self, sample_rfp_text):
        reqs = extract_requirements(sample_rfp_text)
        types = [r["type"] for r in reqs]
        assert "clearance" in types or "staffing" in types

    def test_empty_text_returns_empty(self):
        reqs = extract_requirements("")
        assert reqs == []


# =========================================
# COMPLIANCE GENERATION FROM TEXT
# =========================================

@pytest.mark.asyncio
class TestComplianceFromText:
    async def test_generates_matrix(self, generator, sample_rfp_text):
        matrix = await generator.generate_from_text("Test RFP", sample_rfp_text)
        assert isinstance(matrix, ComplianceMatrix)

    async def test_matrix_has_rows(self, generator, sample_rfp_text):
        matrix = await generator.generate_from_text("Test RFP", sample_rfp_text)
        assert matrix.total_requirements > 0
        assert len(matrix.rows) > 0

    async def test_compliance_rate_calculated(self, generator, sample_rfp_text):
        matrix = await generator.generate_from_text("Test RFP", sample_rfp_text)
        assert 0 <= matrix.compliance_rate <= 100

    async def test_row_structure(self, generator, sample_rfp_text):
        matrix = await generator.generate_from_text("Test RFP", sample_rfp_text)
        for row in matrix.rows:
            assert isinstance(row, ComplianceRow)
            assert row.requirement_id != ""
            assert row.compliance_status in ComplianceStatus

    async def test_identifies_gaps(self, generator, sample_rfp_text):
        matrix = await generator.generate_from_text("Test RFP", sample_rfp_text)
        # "quantum computing" should create a gap
        assert len(matrix.gaps) > 0


# =========================================
# COMPLIANCE FROM REQUIREMENTS
# =========================================

@pytest.mark.asyncio
class TestComplianceFromRequirements:
    async def test_generates_from_list(self, generator, sample_requirements):
        matrix = await generator.generate_from_requirements("Test RFP", sample_requirements)
        assert matrix.total_requirements == 3

    async def test_clearance_requirement_compliant(self, generator, sample_requirements):
        matrix = await generator.generate_from_requirements("Test RFP", sample_requirements)
        clearance_row = [r for r in matrix.rows if r.requirement_id == "REQ-001"][0]
        # TS/SCI + intelligence analysts = strong match
        assert clearance_row.compliance_status in (
            ComplianceStatus.COMPLIANT, ComplianceStatus.PARTIALLY_COMPLIANT
        )

    async def test_quantum_non_compliant(self, generator, sample_requirements):
        matrix = await generator.generate_from_requirements("Test RFP", sample_requirements)
        quantum_row = [r for r in matrix.rows if r.requirement_id == "REQ-003"][0]
        assert quantum_row.compliance_status == ComplianceStatus.NON_COMPLIANT


# =========================================
# SECTION L/M MAPPING
# =========================================

@pytest.mark.asyncio
class TestSectionMapping:
    async def test_section_l_m_mapping(self, generator, sample_rfp_text):
        matrix = await generator.generate_from_text("Test RFP", sample_rfp_text)
        mapping = generator.get_section_l_m_mapping(matrix)
        assert "L" in mapping
        assert "M" in mapping
        assert "other" in mapping


# =========================================
# TEAMING RECOMMENDATIONS
# =========================================

@pytest.mark.asyncio
class TestTeamingRecommendations:
    async def test_teaming_for_gaps(self, generator, sample_rfp_text):
        matrix = await generator.generate_from_text("Test RFP", sample_rfp_text)
        non_compliant_gaps = [g for g in matrix.gaps if g.severity in ("critical", "high")]
        if non_compliant_gaps:
            assert len(matrix.teaming_recommendations) > 0


# =========================================
# EXPORT
# =========================================

@pytest.mark.asyncio
class TestExport:
    async def test_export_to_dict(self, generator, sample_rfp_text):
        matrix = await generator.generate_from_text("Test RFP", sample_rfp_text)
        d = generator.export_to_dict(matrix)
        assert "rows" in d
        assert "gaps" in d
        assert "compliance_rate" in d


# =========================================
# SINGLETON
# =========================================

class TestSingleton:
    def test_get_generator_returns_instance(self):
        g = get_compliance_generator()
        assert isinstance(g, ComplianceMatrixGenerator)

    def test_get_generator_is_singleton(self):
        g1 = get_compliance_generator()
        g2 = get_compliance_generator()
        assert g1 is g2
