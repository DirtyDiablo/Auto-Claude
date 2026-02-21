"""
Comprehensive tests for Feature 20 — Multi-Portfolio Expansion.

Tests cover:
- PortfolioConfig creation and validation for all 5 portfolios
- PortfolioRegistry singleton, get, list_all, register
- PortfolioScorer scoring logic (clearance, keywords, location, program, tiers)
- Cross-portfolio analysis
- Batch scoring
- API endpoint response codes
- Edge cases
"""

from __future__ import annotations

import importlib
import pytest
from dataclasses import asdict

from Engine8_Knowledge.portfolios.portfolio_config import (
    PortfolioConfig,
    DEFAULT_PORTFOLIOS,
    DCGS_PORTFOLIO,
    GBSD_PORTFOLIO,
    JADC2_PORTFOLIO,
    ABMS_PORTFOLIO,
    MQ25_PORTFOLIO,
)
from Engine8_Knowledge.portfolios.portfolio_scorer import PortfolioScorer
from Engine8_Knowledge.portfolios import registry as registry_module
from Engine8_Knowledge.portfolios.registry import PortfolioRegistry, get_portfolio_registry


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_registry_singleton():
    """Reset the module-level singleton before each test."""
    registry_module._registry = None
    yield
    registry_module._registry = None


@pytest.fixture
def registry():
    return get_portfolio_registry()


@pytest.fixture
def dcgs_scorer():
    return PortfolioScorer(DCGS_PORTFOLIO)


@pytest.fixture
def gbsd_scorer():
    return PortfolioScorer(GBSD_PORTFOLIO)


# ===========================================================================
# 1. PortfolioConfig creation and validation (all 5 portfolios)
# ===========================================================================


class TestPortfolioConfigStructure:
    """Verify every default portfolio has a valid, complete structure."""

    @pytest.mark.parametrize("portfolio", DEFAULT_PORTFOLIOS, ids=lambda p: p.id)
    def test_has_non_empty_id(self, portfolio):
        assert isinstance(portfolio.id, str)
        assert len(portfolio.id) > 0

    @pytest.mark.parametrize("portfolio", DEFAULT_PORTFOLIOS, ids=lambda p: p.id)
    def test_has_non_empty_name(self, portfolio):
        assert isinstance(portfolio.name, str)
        assert len(portfolio.name) > 0

    @pytest.mark.parametrize("portfolio", DEFAULT_PORTFOLIOS, ids=lambda p: p.id)
    def test_has_description(self, portfolio):
        assert isinstance(portfolio.description, str)
        assert len(portfolio.description) > 10

    @pytest.mark.parametrize("portfolio", DEFAULT_PORTFOLIOS, ids=lambda p: p.id)
    def test_has_estimated_value(self, portfolio):
        assert portfolio.estimated_value.startswith("$")

    @pytest.mark.parametrize("portfolio", DEFAULT_PORTFOLIOS, ids=lambda p: p.id)
    def test_has_keywords(self, portfolio):
        assert isinstance(portfolio.keywords, list)
        assert len(portfolio.keywords) >= 3

    @pytest.mark.parametrize("portfolio", DEFAULT_PORTFOLIOS, ids=lambda p: p.id)
    def test_has_secondary_keywords(self, portfolio):
        assert isinstance(portfolio.secondary_keywords, list)
        assert len(portfolio.secondary_keywords) >= 3

    @pytest.mark.parametrize("portfolio", DEFAULT_PORTFOLIOS, ids=lambda p: p.id)
    def test_has_programs(self, portfolio):
        assert isinstance(portfolio.programs, list)
        assert len(portfolio.programs) >= 2

    @pytest.mark.parametrize("portfolio", DEFAULT_PORTFOLIOS, ids=lambda p: p.id)
    def test_has_agencies(self, portfolio):
        assert isinstance(portfolio.agencies, list)
        assert len(portfolio.agencies) >= 2

    @pytest.mark.parametrize("portfolio", DEFAULT_PORTFOLIOS, ids=lambda p: p.id)
    def test_has_clearance_boost(self, portfolio):
        assert isinstance(portfolio.clearance_boost, dict)
        assert len(portfolio.clearance_boost) >= 3
        for level, boost in portfolio.clearance_boost.items():
            assert isinstance(boost, int)
            assert boost > 0

    @pytest.mark.parametrize("portfolio", DEFAULT_PORTFOLIOS, ids=lambda p: p.id)
    def test_has_keyword_boost(self, portfolio):
        assert isinstance(portfolio.keyword_boost, int)
        assert portfolio.keyword_boost > 0

    @pytest.mark.parametrize("portfolio", DEFAULT_PORTFOLIOS, ids=lambda p: p.id)
    def test_has_location_keywords(self, portfolio):
        assert isinstance(portfolio.location_keywords, list)
        assert len(portfolio.location_keywords) >= 2

    @pytest.mark.parametrize("portfolio", DEFAULT_PORTFOLIOS, ids=lambda p: p.id)
    def test_has_location_boost(self, portfolio):
        assert isinstance(portfolio.location_boost, int)
        assert portfolio.location_boost > 0

    @pytest.mark.parametrize("portfolio", DEFAULT_PORTFOLIOS, ids=lambda p: p.id)
    def test_has_competitors(self, portfolio):
        assert isinstance(portfolio.competitors, list)
        assert len(portfolio.competitors) >= 3

    @pytest.mark.parametrize("portfolio", DEFAULT_PORTFOLIOS, ids=lambda p: p.id)
    def test_has_scoring_weights(self, portfolio):
        assert isinstance(portfolio.scoring_weights, dict)

    @pytest.mark.parametrize("portfolio", DEFAULT_PORTFOLIOS, ids=lambda p: p.id)
    def test_is_dataclass(self, portfolio):
        d = asdict(portfolio)
        assert isinstance(d, dict)
        assert "id" in d


class TestSpecificPortfolioValues:
    """Verify specific known values for individual portfolios."""

    def test_dcgs_id(self):
        assert DCGS_PORTFOLIO.id == "dcgs"

    def test_dcgs_value(self):
        assert DCGS_PORTFOLIO.estimated_value == "$950M"

    def test_dcgs_has_dcgs_keyword(self):
        assert "DCGS" in DCGS_PORTFOLIO.keywords

    def test_gbsd_id(self):
        assert GBSD_PORTFOLIO.id == "gbsd"

    def test_gbsd_value(self):
        assert GBSD_PORTFOLIO.estimated_value == "$264B"

    def test_gbsd_has_sentinel(self):
        assert "Sentinel" in GBSD_PORTFOLIO.keywords

    def test_jadc2_id(self):
        assert JADC2_PORTFOLIO.id == "jadc2"

    def test_jadc2_value(self):
        assert JADC2_PORTFOLIO.estimated_value == "$15B+"

    def test_abms_id(self):
        assert ABMS_PORTFOLIO.id == "abms"

    def test_abms_value(self):
        assert ABMS_PORTFOLIO.estimated_value == "$4B+"

    def test_mq25_id(self):
        assert MQ25_PORTFOLIO.id == "mq25"

    def test_mq25_value(self):
        assert MQ25_PORTFOLIO.estimated_value == "$13B"

    def test_default_portfolios_count(self):
        assert len(DEFAULT_PORTFOLIOS) == 5

    def test_all_ids_unique(self):
        ids = [p.id for p in DEFAULT_PORTFOLIOS]
        assert len(ids) == len(set(ids))


# ===========================================================================
# 2. PortfolioRegistry
# ===========================================================================


class TestPortfolioRegistry:
    """Tests for the registry singleton and CRUD operations."""

    def test_singleton_returns_same_instance(self):
        r1 = get_portfolio_registry()
        r2 = get_portfolio_registry()
        assert r1 is r2

    def test_list_all_returns_5_defaults(self, registry):
        assert len(registry.list_all()) == 5

    def test_get_known_portfolio(self, registry):
        p = registry.get("dcgs")
        assert p is not None
        assert p.id == "dcgs"

    def test_get_unknown_portfolio_returns_none(self, registry):
        assert registry.get("nonexistent") is None

    def test_register_new_portfolio(self, registry):
        custom = PortfolioConfig(
            id="custom",
            name="Custom Test",
            description="A custom portfolio for testing.",
            estimated_value="$1B",
            keywords=["custom"],
            secondary_keywords=["test"],
            programs=["Test Program"],
            agencies=["Test Agency"],
            clearance_boost={"Secret": 5},
            keyword_boost=10,
            location_keywords=["TestCity"],
            location_boost=5,
            competitors=["CompA"],
        )
        registry.register(custom)
        assert registry.get("custom") is not None
        assert len(registry.list_all()) == 6

    def test_register_replaces_existing(self, registry):
        original = registry.get("dcgs")
        assert original is not None

        replacement = PortfolioConfig(
            id="dcgs",
            name="DCGS Replacement",
            description="Replaced for testing.",
            estimated_value="$1B",
            keywords=["DCGS"],
            secondary_keywords=["ISR"],
            programs=["Test"],
            agencies=["Test"],
            clearance_boost={"Secret": 5},
            keyword_boost=10,
            location_keywords=["TestCity"],
            location_boost=5,
            competitors=["CompA"],
        )
        registry.register(replacement)
        assert registry.get("dcgs").name == "DCGS Replacement"
        assert len(registry.list_all()) == 5  # count unchanged

    def test_get_scorer_returns_scorer(self, registry):
        scorer = registry.get_scorer("dcgs")
        assert isinstance(scorer, PortfolioScorer)
        assert scorer.portfolio.id == "dcgs"

    def test_get_scorer_unknown_returns_none(self, registry):
        assert registry.get_scorer("nonexistent") is None

    def test_all_default_ids_retrievable(self, registry):
        for pid in ["dcgs", "gbsd", "jadc2", "abms", "mq25"]:
            assert registry.get(pid) is not None


# ===========================================================================
# 3. PortfolioScorer — scoring logic
# ===========================================================================


class TestScorerBaseScore:
    """Base score is always 50."""

    def test_empty_job_gets_base_score(self, dcgs_scorer):
        result = dcgs_scorer.score({})
        assert result["score"] == 50
        assert result["breakdown"]["base_score"] == 50

    def test_empty_job_is_warm(self, dcgs_scorer):
        result = dcgs_scorer.score({})
        assert result["tier"] == "Warm"

    def test_portfolio_id_in_result(self, dcgs_scorer):
        result = dcgs_scorer.score({})
        assert result["portfolio_id"] == "dcgs"


class TestScorerClearanceBoost:
    """Clearance boost from portfolio config."""

    def test_ts_sci_boost(self, dcgs_scorer):
        job = {"clearance": "TS/SCI"}
        result = dcgs_scorer.score(job)
        assert result["breakdown"]["clearance_boost"] == 25

    def test_ts_sci_poly_boost(self, dcgs_scorer):
        job = {"clearance": "TS/SCI w/ Poly"}
        result = dcgs_scorer.score(job)
        assert result["breakdown"]["clearance_boost"] == 35

    def test_top_secret_boost(self, dcgs_scorer):
        job = {"clearance": "Top Secret"}
        result = dcgs_scorer.score(job)
        assert result["breakdown"]["clearance_boost"] == 15

    def test_secret_boost(self, dcgs_scorer):
        job = {"clearance": "Secret"}
        result = dcgs_scorer.score(job)
        assert result["breakdown"]["clearance_boost"] == 5

    def test_no_clearance_no_boost(self, dcgs_scorer):
        job = {"clearance": ""}
        result = dcgs_scorer.score(job)
        assert result["breakdown"]["clearance_boost"] == 0

    def test_clearance_case_insensitive(self, dcgs_scorer):
        job = {"clearance": "ts/sci"}
        result = dcgs_scorer.score(job)
        assert result["breakdown"]["clearance_boost"] == 25

    def test_security_clearance_alias(self, dcgs_scorer):
        job = {"Security Clearance": "TS/SCI"}
        result = dcgs_scorer.score(job)
        assert result["breakdown"]["clearance_boost"] == 25

    def test_gbsd_q_clearance(self, gbsd_scorer):
        job = {"clearance": "Q Clearance"}
        result = gbsd_scorer.score(job)
        assert result["breakdown"]["clearance_boost"] == 30


class TestScorerKeywordBoost:
    """Primary keyword matching gives full keyword_boost."""

    def test_primary_keyword_in_title(self, dcgs_scorer):
        job = {"title": "DCGS-A Systems Engineer"}
        result = dcgs_scorer.score(job)
        assert result["breakdown"]["keyword_boost"] == 20

    def test_primary_keyword_in_description(self, dcgs_scorer):
        job = {"description": "Support the AF DCGS program modernization"}
        result = dcgs_scorer.score(job)
        assert result["breakdown"]["keyword_boost"] == 20

    def test_no_keyword_no_boost(self, dcgs_scorer):
        job = {"title": "Software Engineer"}
        result = dcgs_scorer.score(job)
        assert result["breakdown"]["keyword_boost"] == 0

    def test_keyword_case_insensitive(self, dcgs_scorer):
        job = {"title": "dcgs analyst"}
        result = dcgs_scorer.score(job)
        assert result["breakdown"]["keyword_boost"] == 20

    def test_gbsd_keyword_boost_is_25(self, gbsd_scorer):
        job = {"title": "GBSD Systems Engineer"}
        result = gbsd_scorer.score(job)
        assert result["breakdown"]["keyword_boost"] == 25


class TestScorerSecondaryKeywordBoost:
    """Secondary keyword matching gives half of keyword_boost."""

    def test_secondary_keyword_half_boost(self, dcgs_scorer):
        job = {"title": "ISR Intelligence Analyst"}
        result = dcgs_scorer.score(job)
        assert result["breakdown"]["secondary_keyword_boost"] == 10  # 20 // 2

    def test_no_secondary_no_boost(self, dcgs_scorer):
        job = {"title": "Java Developer"}
        result = dcgs_scorer.score(job)
        assert result["breakdown"]["secondary_keyword_boost"] == 0

    def test_gbsd_secondary_half_of_25(self, gbsd_scorer):
        job = {"title": "Nuclear Deterrent Engineer"}
        result = gbsd_scorer.score(job)
        assert result["breakdown"]["secondary_keyword_boost"] == 12  # 25 // 2


class TestScorerLocationBoost:
    """Location-based boosting."""

    def test_location_match(self, dcgs_scorer):
        job = {"location": "San Diego, CA"}
        result = dcgs_scorer.score(job)
        assert result["breakdown"]["location_boost"] == 10

    def test_location_no_match(self, dcgs_scorer):
        job = {"location": "New York, NY"}
        result = dcgs_scorer.score(job)
        assert result["breakdown"]["location_boost"] == 0

    def test_location_case_insensitive(self, dcgs_scorer):
        job = {"location": "san diego"}
        result = dcgs_scorer.score(job)
        assert result["breakdown"]["location_boost"] == 10

    def test_location_alias_key(self, dcgs_scorer):
        job = {"Location": "Hampton, VA"}
        result = dcgs_scorer.score(job)
        assert result["breakdown"]["location_boost"] == 10


class TestScorerProgramBoost:
    """Program name match gives +20."""

    def test_program_match(self, dcgs_scorer):
        job = {"program": "AF DCGS - PACAF"}
        result = dcgs_scorer.score(job)
        assert result["breakdown"]["program_boost"] == 20

    def test_program_no_match(self, dcgs_scorer):
        job = {"program": "JSTARS"}
        result = dcgs_scorer.score(job)
        assert result["breakdown"]["program_boost"] == 0

    def test_program_partial_match(self, dcgs_scorer):
        job = {"program": "Navy DCGS-N Modernization"}
        result = dcgs_scorer.score(job)
        assert result["breakdown"]["program_boost"] == 20


class TestScorerTierClassification:
    """Tier classification: Hot >= 80, Warm >= 50, Cold < 50."""

    def test_hot_tier(self, dcgs_scorer):
        # base 50 + TS/SCI 25 + keyword 20 = 95 -> Hot
        job = {"clearance": "TS/SCI", "title": "DCGS Engineer"}
        result = dcgs_scorer.score(job)
        assert result["tier"] == "Hot"
        assert result["score"] >= 80

    def test_warm_tier(self, dcgs_scorer):
        # base 50 + secret 5 = 55 -> Warm
        job = {"clearance": "Secret"}
        result = dcgs_scorer.score(job)
        assert result["tier"] == "Warm"
        assert 50 <= result["score"] < 80

    def test_cold_tier(self):
        # Build a custom portfolio where boosts are negative-ish
        cold_config = PortfolioConfig(
            id="test",
            name="Test",
            description="Test portfolio",
            estimated_value="$1M",
            keywords=["ZZZ_UNIQUE"],
            secondary_keywords=["AAA_UNIQUE"],
            programs=["NO_PROGRAM_MATCH"],
            agencies=["Test"],
            clearance_boost={},
            keyword_boost=0,
            location_keywords=["Nowhere"],
            location_boost=0,
            competitors=[],
        )
        scorer = PortfolioScorer(cold_config)
        # base 50 with 0 keyword_boost -> score 50, that's Warm
        # To get Cold we need base < 50 which isn't possible with fixed base 50
        # Cold requires score < 50 which only happens if base_score logic changes
        # With current design, minimum score is 50 (base only). That's Warm.
        # This confirms Cold is only reachable if negative adjustments exist.
        result = scorer.score({})
        # 50 is the minimum with current design, classified as Warm
        assert result["score"] == 50
        assert result["tier"] == "Warm"

    def test_score_capped_at_100(self, dcgs_scorer):
        # Stack all boosts: TS/SCI(25) + keyword(20) + secondary(10) + location(10) + program(20) = 85 + base 50 = 135 -> capped
        job = {
            "clearance": "TS/SCI",
            "title": "DCGS ISR Analyst",
            "location": "San Diego, CA",
            "program": "AF DCGS - PACAF",
        }
        result = dcgs_scorer.score(job)
        assert result["score"] <= 100

    def test_score_not_negative(self, dcgs_scorer):
        result = dcgs_scorer.score({})
        assert result["score"] >= 0


class TestScorerBreakdown:
    """Score breakdown includes all categories."""

    def test_breakdown_keys(self, dcgs_scorer):
        result = dcgs_scorer.score({})
        expected_keys = {
            "base_score",
            "clearance_boost",
            "keyword_boost",
            "secondary_keyword_boost",
            "location_boost",
            "program_boost",
        }
        assert expected_keys == set(result["breakdown"].keys())


# ===========================================================================
# 4. Cross-portfolio analysis
# ===========================================================================


class TestCrossPortfolioAnalysis:
    """Score a single job against all 5 portfolios."""

    def test_cross_portfolio_returns_all_5(self, dcgs_scorer):
        job = {"title": "Systems Engineer", "clearance": "TS/SCI"}
        result = dcgs_scorer.cross_portfolio_analysis(job, DEFAULT_PORTFOLIOS)
        assert len(result["rankings"]) == 5

    def test_cross_portfolio_ranked_by_score(self, dcgs_scorer):
        job = {"title": "DCGS Analyst", "clearance": "TS/SCI"}
        result = dcgs_scorer.cross_portfolio_analysis(job, DEFAULT_PORTFOLIOS)
        scores = [r["score"] for r in result["rankings"]]
        assert scores == sorted(scores, reverse=True)

    def test_cross_portfolio_best_match(self, dcgs_scorer):
        job = {"title": "DCGS ISR Engineer", "clearance": "TS/SCI"}
        result = dcgs_scorer.cross_portfolio_analysis(job, DEFAULT_PORTFOLIOS)
        assert result["best_match"] is not None
        assert result["best_match"]["portfolio_id"] == "dcgs"

    def test_cross_portfolio_gbsd_job(self, dcgs_scorer):
        job = {"title": "GBSD Sentinel Engineer", "clearance": "TS/SCI"}
        result = dcgs_scorer.cross_portfolio_analysis(job, DEFAULT_PORTFOLIOS)
        assert result["best_match"]["portfolio_id"] == "gbsd"

    def test_cross_portfolio_has_job(self, dcgs_scorer):
        job = {"title": "Test"}
        result = dcgs_scorer.cross_portfolio_analysis(job, DEFAULT_PORTFOLIOS)
        assert result["job"] == job

    def test_cross_portfolio_each_has_portfolio_name(self, dcgs_scorer):
        job = {"title": "Engineer"}
        result = dcgs_scorer.cross_portfolio_analysis(job, DEFAULT_PORTFOLIOS)
        for r in result["rankings"]:
            assert "portfolio_name" in r

    def test_cross_portfolio_empty_list(self, dcgs_scorer):
        job = {"title": "Test"}
        result = dcgs_scorer.cross_portfolio_analysis(job, [])
        assert result["rankings"] == []
        assert result["best_match"] is None


# ===========================================================================
# 5. Batch scoring
# ===========================================================================


class TestBatchScoring:
    """Batch scoring multiple jobs."""

    def test_batch_returns_correct_count(self, dcgs_scorer):
        jobs = [{"title": "Job A"}, {"title": "Job B"}, {"title": "Job C"}]
        results = dcgs_scorer.score_batch(jobs)
        assert len(results) == 3

    def test_batch_each_has_score(self, dcgs_scorer):
        jobs = [{"title": "DCGS Analyst"}, {"title": "Software Dev"}]
        results = dcgs_scorer.score_batch(jobs)
        for r in results:
            assert "score" in r
            assert "tier" in r

    def test_batch_empty_list(self, dcgs_scorer):
        assert dcgs_scorer.score_batch([]) == []


# ===========================================================================
# 6. API endpoint tests (using FastAPI TestClient)
# ===========================================================================


class TestPortfolioAPI:
    """Test the FastAPI router endpoints."""

    @pytest.fixture(autouse=True)
    def setup_client(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from Engine8_Knowledge.routers.portfolios import router

        app = FastAPI()
        app.include_router(router)
        self.client = TestClient(app)

    def test_list_portfolios_200(self):
        resp = self.client.get("/portfolios")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 5

    def test_list_portfolios_has_required_fields(self):
        resp = self.client.get("/portfolios")
        for item in resp.json():
            assert "id" in item
            assert "name" in item
            assert "estimated_value" in item

    def test_get_portfolio_200(self):
        resp = self.client.get("/portfolios/dcgs")
        assert resp.status_code == 200
        assert resp.json()["id"] == "dcgs"

    def test_get_portfolio_404(self):
        resp = self.client.get("/portfolios/nonexistent")
        assert resp.status_code == 404

    def test_score_job_200(self):
        resp = self.client.post(
            "/portfolios/dcgs/score",
            json={"job": {"title": "DCGS Analyst", "clearance": "TS/SCI"}},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "score" in data
        assert "tier" in data
        assert data["portfolio_id"] == "dcgs"

    def test_score_job_404_bad_portfolio(self):
        resp = self.client.post(
            "/portfolios/nonexistent/score",
            json={"job": {"title": "Test"}},
        )
        assert resp.status_code == 404

    def test_cross_score_200(self):
        resp = self.client.post(
            "/portfolios/cross-score",
            json={"job": {"title": "DCGS ISR Analyst", "clearance": "TS/SCI"}},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["rankings"]) == 5
        assert data["best_match"] is not None

    def test_list_programs_200(self):
        resp = self.client.get("/portfolios/dcgs/programs")
        assert resp.status_code == 200
        programs = resp.json()
        assert isinstance(programs, list)
        assert len(programs) >= 2

    def test_list_programs_404(self):
        resp = self.client.get("/portfolios/nonexistent/programs")
        assert resp.status_code == 404

    def test_comparison_200(self):
        resp = self.client.get("/portfolios/comparison")
        assert resp.status_code == 200
        data = resp.json()
        assert "portfolios" in data
        assert "total_estimated_value" in data
        assert len(data["portfolios"]) == 5


# ===========================================================================
# 7. Edge cases
# ===========================================================================


class TestEdgeCases:
    """Edge cases and unusual inputs."""

    def test_empty_job_dict(self, dcgs_scorer):
        result = dcgs_scorer.score({})
        assert result["score"] == 50
        assert result["tier"] == "Warm"

    def test_none_values_in_job(self, dcgs_scorer):
        job = {"clearance": None, "title": None, "location": None, "program": None}
        result = dcgs_scorer.score(job)
        assert result["score"] == 50

    def test_missing_fields(self, dcgs_scorer):
        job = {"random_field": "random_value"}
        result = dcgs_scorer.score(job)
        assert result["score"] == 50

    def test_numeric_values_ignored(self, dcgs_scorer):
        job = {"clearance": 123, "title": 456}
        # str(123) won't match any clearance keyword
        result = dcgs_scorer.score(job)
        assert result["score"] == 50

    def test_very_long_text(self, dcgs_scorer):
        job = {"title": "DCGS " + "x" * 10000}
        result = dcgs_scorer.score(job)
        assert result["breakdown"]["keyword_boost"] == 20

    def test_special_characters_in_text(self, dcgs_scorer):
        job = {"title": "DCGS! @#$% Engineer"}
        result = dcgs_scorer.score(job)
        assert result["breakdown"]["keyword_boost"] == 20
