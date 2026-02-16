"""Tests for Phase 35A — Capability Statement Generator."""

import pytest

from src.proposals.capability_generator import (
    CapabilityStatementGenerator,
    CapabilityStatement,
    TemplateVariant,
    COMPANY_PROFILE,
    get_capability_generator,
)


# =========================================
# FIXTURES
# =========================================


@pytest.fixture
def generator():
    return CapabilityStatementGenerator()


# =========================================
# TEMPLATE VARIANTS
# =========================================


class TestTemplateVariants:
    def test_one_page_variant(self):
        assert TemplateVariant.ONE_PAGE == "one_page"

    def test_two_page_variant(self):
        assert TemplateVariant.TWO_PAGE == "two_page"

    def test_full_brief_variant(self):
        assert TemplateVariant.FULL_BRIEF == "full_brief"


# =========================================
# COMPANY PROFILE
# =========================================


class TestCompanyProfile:
    def test_has_certifications(self):
        assert "SDVOSB" in COMPANY_PROFILE["certifications"]
        assert "VOSB" in COMPANY_PROFILE["certifications"]

    def test_has_naics_codes(self):
        assert len(COMPANY_PROFILE["naics_codes"]) >= 3

    def test_has_core_capabilities(self):
        assert len(COMPANY_PROFILE["core_capabilities"]) >= 5

    def test_has_clearance_capabilities(self):
        assert "TS/SCI" in COMPANY_PROFILE["clearance_capabilities"]


# =========================================
# GENERATION
# =========================================


@pytest.mark.asyncio
class TestGeneration:
    async def test_generates_statement(self, generator):
        stmt = await generator.generate("DCGS", "USAF")
        assert isinstance(stmt, CapabilityStatement)

    async def test_statement_has_sections(self, generator):
        stmt = await generator.generate("DCGS", "USAF")
        assert len(stmt.sections) == 5

    async def test_sections_ordered(self, generator):
        stmt = await generator.generate("DCGS", "USAF")
        orders = [s.order for s in stmt.sections]
        assert orders == sorted(orders)

    async def test_section_titles(self, generator):
        stmt = await generator.generate("DCGS", "USAF")
        titles = [s.title for s in stmt.sections]
        assert "Company Overview" in titles
        assert "Core Capabilities" in titles
        assert "Past Performance" in titles
        assert "Differentiators" in titles
        assert "Certifications & Clearances" in titles

    async def test_program_in_content(self, generator):
        stmt = await generator.generate("DCGS", "USAF")
        overview = [s for s in stmt.sections if s.title == "Company Overview"][0]
        assert "DCGS" in overview.content

    async def test_agency_in_content(self, generator):
        stmt = await generator.generate("DCGS", "USAF")
        overview = [s for s in stmt.sections if s.title == "Company Overview"][0]
        assert "USAF" in overview.content

    async def test_sdvosb_featured(self, generator):
        stmt = await generator.generate("DCGS", "USAF")
        overview = [s for s in stmt.sections if s.title == "Company Overview"][0]
        assert "SDVOSB" in overview.content

    async def test_word_count_positive(self, generator):
        stmt = await generator.generate("DCGS", "USAF")
        assert stmt.word_count > 0

    async def test_one_page_shorter(self, generator):
        one = await generator.generate("DCGS", variant=TemplateVariant.ONE_PAGE)
        two = await generator.generate("DCGS", variant=TemplateVariant.TWO_PAGE)
        assert one.word_count < two.word_count

    async def test_generates_id(self, generator):
        stmt = await generator.generate("DCGS")
        assert stmt.id.startswith("cap-dcgs-")

    async def test_generated_at_set(self, generator):
        stmt = await generator.generate("DCGS")
        assert stmt.generated_at != ""

    async def test_metadata_has_certifications(self, generator):
        stmt = await generator.generate("DCGS")
        assert "certifications" in stmt.metadata
        assert "SDVOSB" in stmt.metadata["certifications"]


# =========================================
# BATCH & HISTORY
# =========================================


@pytest.mark.asyncio
class TestBatchAndHistory:
    async def test_batch_generation(self, generator):
        stmts = await generator.generate_batch(["DCGS", "NGEN"])
        assert len(stmts) == 2

    async def test_history_tracked(self, generator):
        await generator.generate("DCGS")
        await generator.generate("NGEN")
        assert len(generator.get_history()) == 2


# =========================================
# EXPORT
# =========================================


@pytest.mark.asyncio
class TestExport:
    async def test_export_to_dict(self, generator):
        stmt = await generator.generate("DCGS")
        d = generator.export_to_dict(stmt)
        assert "id" in d
        assert "sections" in d
        assert len(d["sections"]) == 5
        assert d["program"] == "DCGS"


# =========================================
# TEMPLATES
# =========================================


class TestTemplates:
    def test_get_templates(self, generator):
        templates = generator.get_templates()
        assert len(templates) == 3
        ids = [t["id"] for t in templates]
        assert "one_page" in ids
        assert "two_page" in ids
        assert "full_brief" in ids


# =========================================
# SINGLETON
# =========================================


class TestSingleton:
    def test_get_generator_returns_instance(self):
        g = get_capability_generator()
        assert isinstance(g, CapabilityStatementGenerator)

    def test_get_generator_is_singleton(self):
        g1 = get_capability_generator()
        g2 = get_capability_generator()
        assert g1 is g2
