"""Tests for Phase 35A — Past Performance Matrix Builder."""

import pytest

from src.proposals.past_performance import (
    PastPerformanceBuilder,
    PastPerformanceEntry,
    PerformanceMatrix,
    RelevanceScore,
    CPARSMetrics,
    CPARS_RATINGS,
    CPARS_SCORES,
    RELEVANCE_WEIGHTS,
    compute_relevance,
    generate_narrative,
    get_past_performance_builder,
)


# =========================================
# FIXTURES
# =========================================

@pytest.fixture
def builder():
    return PastPerformanceBuilder()


@pytest.fixture
def sample_entries():
    return [
        PastPerformanceEntry(
            id="pp-1",
            contract_name="DCGS Sustainment",
            contract_number="FA8075-20-D-0001",
            agency="USAF",
            program="DCGS",
            value=5_000_000,
            period_start="2020-01-01",
            period_end="2025-01-01",
            naics="541512",
            labor_categories=["Intelligence Analyst", "Systems Engineer"],
            clearance_level="TS/SCI",
            placements=25,
            cpars=CPARSMetrics(quality="Very Good", schedule="Exceptional", overall="Very Good"),
        ),
        PastPerformanceEntry(
            id="pp-2",
            contract_name="NGEN Service Desk",
            contract_number="N00039-19-D-0002",
            agency="Navy",
            program="NGEN",
            value=3_000_000,
            period_start="2019-06-01",
            period_end="2024-06-01",
            naics="541519",
            labor_categories=["Help Desk Specialist", "Network Engineer"],
            clearance_level="Secret",
            placements=15,
        ),
        PastPerformanceEntry(
            id="pp-3",
            contract_name="GBSD Engineering",
            agency="USAF",
            program="GBSD",
            value=8_000_000,
            naics="541330",
            labor_categories=["Senior Systems Engineer", "Software Engineer"],
            clearance_level="TS/SCI CI Poly",
            placements=10,
            cpars=CPARSMetrics(overall="Exceptional"),
        ),
    ]


@pytest.fixture
def dcgs_requirements():
    return {
        "naics_codes": ["541512"],
        "labor_categories": ["Intelligence Analyst", "Systems Engineer", "Data Scientist"],
        "clearance": "TS/SCI",
        "agency": "USAF",
        "contract_value": 6_000_000,
    }


# =========================================
# RELEVANCE WEIGHTS
# =========================================

class TestRelevanceWeights:
    def test_weights_sum_to_one(self):
        total = sum(RELEVANCE_WEIGHTS.values())
        assert abs(total - 1.0) < 0.001

    def test_five_dimensions(self):
        assert len(RELEVANCE_WEIGHTS) == 5


# =========================================
# RELEVANCE SCORING
# =========================================

class TestRelevanceScoring:
    def test_compute_relevance(self, sample_entries, dcgs_requirements):
        score = compute_relevance(sample_entries[0], dcgs_requirements)
        assert isinstance(score, RelevanceScore)
        assert 0 <= score.overall <= 100

    def test_exact_naics_match_high(self, sample_entries, dcgs_requirements):
        score = compute_relevance(sample_entries[0], dcgs_requirements)
        assert score.naics_match == 100.0  # Exact match

    def test_agency_match_high(self, sample_entries, dcgs_requirements):
        score = compute_relevance(sample_entries[0], dcgs_requirements)
        assert score.agency_match == 100.0  # USAF == USAF

    def test_different_agency_lower(self, sample_entries, dcgs_requirements):
        score = compute_relevance(sample_entries[1], dcgs_requirements)
        # Navy vs USAF — both DoD so moderate
        assert score.agency_match < 100.0

    def test_clearance_match(self, sample_entries, dcgs_requirements):
        score = compute_relevance(sample_entries[0], dcgs_requirements)
        assert score.clearance_match == 100.0  # TS/SCI matches TS/SCI

    def test_higher_clearance_still_compliant(self, sample_entries, dcgs_requirements):
        score = compute_relevance(sample_entries[2], dcgs_requirements)
        # TS/SCI CI Poly >= TS/SCI
        assert score.clearance_match == 100.0

    def test_best_entry_ranks_highest(self, sample_entries, dcgs_requirements):
        scores = [compute_relevance(e, dcgs_requirements) for e in sample_entries]
        # DCGS entry should rank highest for DCGS requirements
        assert scores[0].overall >= scores[1].overall


# =========================================
# NARRATIVE GENERATION
# =========================================

class TestNarrativeGeneration:
    def test_generates_narrative(self, sample_entries):
        narrative = generate_narrative(sample_entries[0])
        assert isinstance(narrative, str)
        assert len(narrative) > 50

    def test_narrative_includes_contract(self, sample_entries):
        narrative = generate_narrative(sample_entries[0])
        assert "DCGS Sustainment" in narrative

    def test_narrative_includes_agency(self, sample_entries):
        narrative = generate_narrative(sample_entries[0])
        assert "USAF" in narrative

    def test_narrative_includes_clearance(self, sample_entries):
        narrative = generate_narrative(sample_entries[0])
        assert "TS/SCI" in narrative


# =========================================
# MATRIX BUILDING
# =========================================

@pytest.mark.asyncio
class TestMatrixBuilding:
    async def test_build_empty_matrix(self, builder):
        matrix = await builder.build_matrix("Test Solicitation")
        assert isinstance(matrix, PerformanceMatrix)
        assert matrix.total_entries == 0

    async def test_build_with_entries(self, builder, sample_entries, dcgs_requirements):
        builder.set_entries(sample_entries)
        matrix = await builder.build_matrix("DCGS-2025", dcgs_requirements)
        assert matrix.total_entries > 0
        assert matrix.avg_relevance > 0

    async def test_entries_sorted_by_relevance(self, builder, sample_entries, dcgs_requirements):
        builder.set_entries(sample_entries)
        matrix = await builder.build_matrix("DCGS-2025", dcgs_requirements)
        if len(matrix.entries) >= 2:
            assert matrix.entries[0].relevance.overall >= matrix.entries[1].relevance.overall

    async def test_top_n_respected(self, builder, sample_entries, dcgs_requirements):
        builder.set_entries(sample_entries)
        matrix = await builder.build_matrix("DCGS-2025", dcgs_requirements, top_n=2)
        assert matrix.total_entries <= 2

    async def test_narratives_generated(self, builder, sample_entries, dcgs_requirements):
        builder.set_entries(sample_entries)
        matrix = await builder.build_matrix("DCGS-2025", dcgs_requirements)
        for entry in matrix.entries:
            assert entry.relevance_narrative != ""


# =========================================
# EXPORT
# =========================================

@pytest.mark.asyncio
class TestExport:
    async def test_export_to_dict(self, builder, sample_entries, dcgs_requirements):
        builder.set_entries(sample_entries)
        matrix = await builder.build_matrix("DCGS-2025", dcgs_requirements)
        d = builder.export_to_dict(matrix)
        assert "entries" in d
        assert "avg_relevance" in d
        assert len(d["entries"]) > 0


# =========================================
# CPARS
# =========================================

class TestCPARS:
    def test_ratings_ordered(self):
        assert CPARS_RATINGS[0] == "Exceptional"
        assert CPARS_RATINGS[-1] == "Unsatisfactory"

    def test_scores_mapping(self):
        assert CPARS_SCORES["Exceptional"] == 5
        assert CPARS_SCORES["Unsatisfactory"] == 1


# =========================================
# SINGLETON
# =========================================

class TestSingleton:
    def test_get_builder_returns_instance(self):
        b = get_past_performance_builder()
        assert isinstance(b, PastPerformanceBuilder)

    def test_get_builder_is_singleton(self):
        b1 = get_past_performance_builder()
        b2 = get_past_performance_builder()
        assert b1 is b2
