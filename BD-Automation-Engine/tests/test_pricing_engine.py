"""Tests for Phase 35A — Labor Category & Pricing Engine."""

import pytest

from src.proposals.pricing_engine import (
    PricingEngine,
    LaborCategory,
    RateCard,
    PricingTemplate,
    PricingAnalysis,
    PricingModel,
    GSA_SCHEDULE_RATES,
    CLEARANCE_PREMIUMS,
    get_pricing_engine,
)


# =========================================
# FIXTURES
# =========================================


@pytest.fixture
def engine():
    return PricingEngine()


@pytest.fixture
def sample_categories(engine):
    return [
        engine.build_labor_category("Senior Systems Engineer", clearance="TS/SCI"),
        engine.build_labor_category("Intelligence Analyst", clearance="TS/SCI"),
        engine.build_labor_category("Software Engineer", clearance="Secret"),
    ]


# =========================================
# GSA RATES
# =========================================


class TestGSARates:
    def test_has_entries(self):
        assert len(GSA_SCHEDULE_RATES) >= 10

    def test_rates_positive(self):
        for title, data in GSA_SCHEDULE_RATES.items():
            assert data["rate"] > 0

    def test_clearance_premiums(self):
        assert CLEARANCE_PREMIUMS["TS/SCI CI Poly"] > CLEARANCE_PREMIUMS["Secret"]
        assert CLEARANCE_PREMIUMS["Secret"] > CLEARANCE_PREMIUMS["None"]


# =========================================
# LABOR CATEGORY BUILDING
# =========================================


class TestLaborCategory:
    def test_build_known_title(self, engine):
        cat = engine.build_labor_category("Senior Systems Engineer")
        assert isinstance(cat, LaborCategory)
        assert cat.title == "Senior Systems Engineer"

    def test_gsa_rate_positive(self, engine):
        cat = engine.build_labor_category("Intelligence Analyst")
        assert cat.gsa_rate > 0

    def test_market_below_gsa(self, engine):
        cat = engine.build_labor_category("Intelligence Analyst")
        assert cat.market_rate < cat.gsa_rate

    def test_proposed_between_market_and_gsa(self, engine):
        cat = engine.build_labor_category("Intelligence Analyst")
        assert cat.market_rate <= cat.proposed_rate <= cat.gsa_rate

    def test_clearance_premium_applied(self, engine):
        low = engine.build_labor_category("Intelligence Analyst", clearance="Secret")
        high = engine.build_labor_category("Intelligence Analyst", clearance="TS/SCI")
        assert high.gsa_rate > low.gsa_rate

    def test_salary_range_set(self, engine):
        cat = engine.build_labor_category("Software Engineer")
        assert cat.salary_range_low > 0
        assert cat.salary_range_high > cat.salary_range_low

    def test_functional_area_set(self, engine):
        cat = engine.build_labor_category("Senior Systems Engineer")
        assert cat.functional_area == "Engineering"

    def test_unknown_title_gets_default_rate(self, engine):
        cat = engine.build_labor_category("Exotic Space Consultant")
        assert cat.gsa_rate > 0  # Falls back to default


# =========================================
# RATE CARD
# =========================================


class TestRateCard:
    def test_generate_rate_card(self, engine, sample_categories):
        card = engine.generate_rate_card("DCGS Rate Card", sample_categories)
        assert isinstance(card, RateCard)
        assert card.total_categories == 3

    def test_card_has_id(self, engine, sample_categories):
        card = engine.generate_rate_card("Test Card", sample_categories)
        assert card.id.startswith("rc-")

    def test_card_generated_at(self, engine, sample_categories):
        card = engine.generate_rate_card("Test Card", sample_categories)
        assert card.generated_at != ""

    def test_card_pricing_model(self, engine, sample_categories):
        card = engine.generate_rate_card(
            "FFP Card", sample_categories, pricing_model=PricingModel.FIRM_FIXED_PRICE
        )
        assert card.pricing_model == PricingModel.FIRM_FIXED_PRICE


# =========================================
# PRICING TEMPLATE
# =========================================


class TestPricingTemplate:
    def test_generate_template(self, engine, sample_categories):
        card = engine.generate_rate_card("Test", sample_categories, option_years=4)
        labor_mix = {
            "Senior Systems Engineer": 2,
            "Intelligence Analyst": 5,
            "Software Engineer": 3,
        }
        template = engine.generate_pricing_template(card, labor_mix)
        assert isinstance(template, PricingTemplate)

    def test_total_value_positive(self, engine, sample_categories):
        card = engine.generate_rate_card("Test", sample_categories, option_years=4)
        labor_mix = {
            "Senior Systems Engineer": 2,
            "Intelligence Analyst": 5,
            "Software Engineer": 3,
        }
        template = engine.generate_pricing_template(card, labor_mix)
        assert template.total_value > 0
        assert template.base_year_value > 0

    def test_year_values_count(self, engine, sample_categories):
        card = engine.generate_rate_card("Test", sample_categories, option_years=4)
        labor_mix = {"Senior Systems Engineer": 1}
        template = engine.generate_pricing_template(card, labor_mix)
        assert len(template.year_values) == 5  # Base + 4 options

    def test_escalation_applied(self, engine, sample_categories):
        card = engine.generate_rate_card(
            "Test", sample_categories, option_years=1, escalation_rate=10.0
        )
        labor_mix = {"Senior Systems Engineer": 1}
        template = engine.generate_pricing_template(card, labor_mix)
        base = template.year_values[0]["total"]
        option = template.year_values[1]["total"]
        assert option > base  # Escalation should increase


# =========================================
# COMPETITIVE ANALYSIS
# =========================================


@pytest.mark.asyncio
class TestCompetitiveAnalysis:
    async def test_analyze_returns_result(self, engine, sample_categories):
        analysis = await engine.analyze_competitive_pricing("DCGS", sample_categories)
        assert isinstance(analysis, PricingAnalysis)

    async def test_position_valid(self, engine, sample_categories):
        analysis = await engine.analyze_competitive_pricing("DCGS", sample_categories)
        assert analysis.competitive_position in (
            "below_market",
            "at_market",
            "above_market",
        )

    async def test_has_recommendations(self, engine, sample_categories):
        analysis = await engine.analyze_competitive_pricing("DCGS", sample_categories)
        assert len(analysis.recommendations) > 0

    async def test_empty_categories(self, engine):
        analysis = await engine.analyze_competitive_pricing("DCGS", [])
        assert analysis.avg_market_rate == 0


# =========================================
# EXPORT
# =========================================


class TestExport:
    def test_export_rate_card(self, engine, sample_categories):
        card = engine.generate_rate_card("Test", sample_categories)
        d = engine.export_rate_card_to_dict(card)
        assert "categories" in d
        assert len(d["categories"]) == 3
        assert "gsa_rate" in d["categories"][0]


# =========================================
# SINGLETON
# =========================================


class TestSingleton:
    def test_get_engine_returns_instance(self):
        e = get_pricing_engine()
        assert isinstance(e, PricingEngine)

    def test_get_engine_is_singleton(self):
        e1 = get_pricing_engine()
        e2 = get_pricing_engine()
        assert e1 is e2
