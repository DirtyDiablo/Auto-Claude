"""Tests for Phase 33A — Smart Autocomplete."""

import pytest

from src.nlq.autocomplete import SmartAutocomplete, Suggestion


# =========================================
# FIXTURES
# =========================================

@pytest.fixture
def autocomplete():
    return SmartAutocomplete()


# =========================================
# SUGGESTION BASICS
# =========================================

@pytest.mark.asyncio
class TestSuggestionBasics:
    async def test_empty_returns_defaults(self, autocomplete):
        suggestions = await autocomplete.suggest("")
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0

    async def test_returns_suggestions(self, autocomplete):
        suggestions = await autocomplete.suggest("show me")
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0

    async def test_suggestions_are_typed(self, autocomplete):
        suggestions = await autocomplete.suggest("find")
        for s in suggestions:
            assert isinstance(s, Suggestion)
            assert isinstance(s.text, str)
            assert isinstance(s.category, str)
            assert isinstance(s.score, float)

    async def test_limit_parameter(self, autocomplete):
        suggestions = await autocomplete.suggest("show", limit=3)
        assert len(suggestions) <= 3


# =========================================
# TEMPLATE MATCHING
# =========================================

@pytest.mark.asyncio
class TestTemplateMatching:
    async def test_show_me_completions(self, autocomplete):
        suggestions = await autocomplete.suggest("show me")
        texts = [s.text.lower() for s in suggestions]
        assert any("show me" in t for t in texts)

    async def test_compare_completions(self, autocomplete):
        suggestions = await autocomplete.suggest("compare")
        texts = [s.text.lower() for s in suggestions]
        assert any("compare" in t for t in texts)

    async def test_find_completions(self, autocomplete):
        suggestions = await autocomplete.suggest("find")
        texts = [s.text.lower() for s in suggestions]
        assert any("find" in t for t in texts)


# =========================================
# ENTITY MATCHING
# =========================================

@pytest.mark.asyncio
class TestEntityMatching:
    async def test_company_match(self, autocomplete):
        suggestions = await autocomplete.suggest("contacts at Lei")
        # Should suggest Leidos
        texts = [s.text for s in suggestions]
        assert any("Leidos" in t for t in texts)

    async def test_location_match(self, autocomplete):
        suggestions = await autocomplete.suggest("jobs in San")
        texts = [s.text for s in suggestions]
        assert any("San" in t for t in texts)


# =========================================
# INDEX BUILDING
# =========================================

@pytest.mark.asyncio
class TestIndexBuilding:
    async def test_build_index(self, autocomplete):
        count = await autocomplete.build_suggestion_index()
        assert count > 0

    async def test_index_contains_companies(self, autocomplete):
        await autocomplete.build_suggestion_index()
        entities = [s.text for s in autocomplete._index if s.metadata.get("type") == "company"]
        assert "Leidos" in entities
        assert "GDIT" in entities

    async def test_index_contains_programs(self, autocomplete):
        await autocomplete.build_suggestion_index()
        entities = [s.text for s in autocomplete._index if s.metadata.get("type") == "program"]
        assert "AF DCGS" in entities

    async def test_custom_entities(self, autocomplete):
        autocomplete.add_custom_entities("custom", ["CustomEntity1", "CustomEntity2"])
        count = await autocomplete.build_suggestion_index()
        entities = [s.text for s in autocomplete._index if s.metadata.get("type") == "custom"]
        assert "CustomEntity1" in entities
        assert "CustomEntity2" in entities


# =========================================
# RECENT QUERIES
# =========================================

@pytest.mark.asyncio
class TestRecentQueries:
    async def test_add_recent_query(self, autocomplete):
        autocomplete.add_recent_query("Find contacts at Leidos")
        assert len(autocomplete._recent_queries) == 1

    async def test_recent_queries_in_suggestions(self, autocomplete):
        autocomplete.add_recent_query("Find contacts at Leidos")
        suggestions = await autocomplete.suggest("Find")
        categories = [s.category for s in suggestions]
        assert "recent" in categories

    async def test_recent_queries_limit(self, autocomplete):
        for i in range(150):
            autocomplete.add_recent_query(f"Query {i}")
        assert len(autocomplete._recent_queries) == 100


# =========================================
# DEDUPLICATION
# =========================================

@pytest.mark.asyncio
class TestDeduplication:
    async def test_no_duplicate_suggestions(self, autocomplete):
        suggestions = await autocomplete.suggest("show me")
        texts = [s.text.lower() for s in suggestions]
        assert len(texts) == len(set(texts))
