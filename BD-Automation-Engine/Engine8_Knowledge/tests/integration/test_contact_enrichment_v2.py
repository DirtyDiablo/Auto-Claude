"""
Phase 23A — Contact Enrichment v2 Tests

Tests production contact enrichment workflow: validation, parallel gather,
classification, human approval gate, enrichment, and report generation.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from Engine8_Knowledge.workflows.production.contact_enrichment import (
    CONTACT_ENRICHMENT_STATE,
    validate_input, gather_contacts_qdrant, gather_contacts_neo4j,
    gather_contacts_notion, merge_contact_data, classify_contacts,
    review_classifications, enrich_from_linkedin, enrich_from_zoominfo,
    update_databases, generate_report, get_contact_enrichment_definition,
)


def test_state_schema_keys():
    expected = {"contact_ids", "contacts_raw", "contacts_qdrant", "contacts_neo4j",
                "contacts_notion", "contacts_merged", "classifications",
                "human_approved", "enrichment_results", "update_results",
                "report", "errors", "step_timings"}
    assert set(CONTACT_ENRICHMENT_STATE.keys()) == expected


@pytest.mark.asyncio
async def test_validate_input_empty():
    state = {"contact_ids": [], "errors": []}
    result = await validate_input(state)
    assert len(result["errors"]) > 0


@pytest.mark.asyncio
async def test_validate_input_valid():
    state = {"contact_ids": ["c1", "c2"], "errors": []}
    result = await validate_input(state)
    assert len(result.get("errors", [])) == 0


@pytest.mark.asyncio
async def test_gather_contacts_qdrant():
    mock_client = MagicMock()
    mock_point = MagicMock()
    mock_point.payload = {"name": "John Doe", "id": "c1", "title": "Director"}
    mock_client.scroll.return_value = ([mock_point], None)
    with patch("Engine8_Knowledge.workflows.production.contact_enrichment.get_qdrant_client", return_value=mock_client):
        state = {"contact_ids": ["c1"]}
        result = await gather_contacts_qdrant(state)
        assert "contacts_qdrant" in result


@pytest.mark.asyncio
async def test_gather_contacts_neo4j():
    mock_mgr = AsyncMock()
    mock_mgr.execute_query.return_value = [
        {"p": {"name": "Jane Smith", "title": "VP"}, "companies": ["GDIT"], "programs": ["DCGS"]}
    ]
    with patch("Engine8_Knowledge.workflows.production.contact_enrichment.get_neo4j_manager", return_value=mock_mgr):
        state = {"contact_ids": ["c1"]}
        result = await gather_contacts_neo4j(state)
        assert "contacts_neo4j" in result


@pytest.mark.asyncio
async def test_gather_contacts_notion():
    state = {"contact_ids": ["c1"]}
    result = await gather_contacts_notion(state)
    assert "contacts_notion" in result
    assert isinstance(result["contacts_notion"], list)


@pytest.mark.asyncio
async def test_merge_contact_data():
    state = {
        "contacts_qdrant": [{"id": "c1", "name": "Alice", "source": "qdrant"}],
        "contacts_neo4j": [{"id": "c1", "name": "Alice", "title": "Director", "source": "neo4j"}],
        "contacts_notion": [{"id": "c2", "name": "Bob", "source": "notion"}],
    }
    result = await merge_contact_data(state)
    assert len(result["contacts_merged"]) == 2


@pytest.mark.asyncio
async def test_classify_contacts_tier1():
    state = {"contacts_merged": [{"name": "CEO Person", "title": "Chief Executive Officer"}]}
    result = await classify_contacts(state)
    assert result["classifications"][0]["tier"] == 1
    assert result["classifications"][0]["bd_priority"] == "critical"


@pytest.mark.asyncio
async def test_classify_contacts_tier3():
    state = {"contacts_merged": [{"name": "Director Person", "title": "Director of Engineering"}]}
    result = await classify_contacts(state)
    assert result["classifications"][0]["tier"] == 3
    assert result["classifications"][0]["bd_priority"] == "high"


@pytest.mark.asyncio
async def test_classify_contacts_default_tier():
    state = {"contacts_merged": [{"name": "Analyst", "title": "Business Analyst"}]}
    result = await classify_contacts(state)
    assert result["classifications"][0]["tier"] == 6


@pytest.mark.asyncio
async def test_review_classifications():
    state = {"human_approved": False}
    result = await review_classifications(state)
    assert "human_approved" in result


@pytest.mark.asyncio
async def test_enrich_from_linkedin():
    state = {"contacts_merged": [{"name": "Test", "linkedin": "https://linkedin.com/in/test"}],
             "enrichment_results": {}}
    result = await enrich_from_linkedin(state)
    assert "linkedin" in result["enrichment_results"]


@pytest.mark.asyncio
async def test_enrich_from_zoominfo():
    state = {"contacts_merged": [{"name": "Test"}], "enrichment_results": {}}
    result = await enrich_from_zoominfo(state)
    assert "zoominfo" in result["enrichment_results"]


@pytest.mark.asyncio
async def test_update_databases():
    state = {"classifications": [{"id": "c1", "name": "Test"}]}
    result = await update_databases(state)
    assert "update_results" in result
    assert result["update_results"]["qdrant"] >= 1


@pytest.mark.asyncio
async def test_generate_report():
    state = {
        "classifications": [{"tier": 1, "bd_priority": "critical"}, {"tier": 3, "bd_priority": "high"}],
        "enrichment_results": {"linkedin": {"a": 1}},
        "errors": [],
        "human_approved": True,
        "step_timings": {},
    }
    result = await generate_report(state)
    assert "report" in result
    assert result["report"]["contacts_processed"] == 2


def test_get_definition():
    defn = get_contact_enrichment_definition()
    assert defn.name == "contact_enrichment"
    assert "validate_input" in defn.nodes
    assert "review_classifications" in defn.interrupt_nodes
    assert len(defn.parallel_groups) == 1
    assert "gather_contacts_qdrant" in defn.parallel_groups[0]
