"""
Root conftest.py — shared fixtures for BD Automation Engine tests.

Provides common test fixtures and configuration shared across all test modules.
"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------------------------
# Environment Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _mock_env(monkeypatch):
    """Ensure tests never use real API keys."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-not-real")
    monkeypatch.setenv("NOTION_TOKEN", "test-token-not-real")
    monkeypatch.setenv("QDRANT_URL", "http://localhost:6333")
    monkeypatch.setenv("BD_API_KEY", "")  # Disable auth in tests


@pytest.fixture
def project_root():
    """Return the project root path."""
    return PROJECT_ROOT


# ---------------------------------------------------------------------------
# Sample Data Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_job():
    """A single sample job posting for testing."""
    return {
        "title": "Senior Systems Engineer - DCGS",
        "company": "Leidos",
        "location": "Fort Belvoir, VA",
        "description": "Support DCGS-A modernization with cloud migration and CI/CD.",
        "clearance": "TS/SCI",
        "source": "test",
    }


@pytest.fixture
def sample_jobs(sample_job):
    """Multiple sample job postings for batch testing."""
    return [
        sample_job,
        {
            "title": "Intelligence Analyst - GBSD",
            "company": "Northrop Grumman",
            "location": "Roy, UT",
            "description": "Ground Based Strategic Deterrent program analysis.",
            "clearance": "Secret",
            "source": "test",
        },
        {
            "title": "DevOps Engineer - JADC2",
            "company": "GDIT",
            "location": "San Antonio, TX",
            "description": "Joint All-Domain Command and Control platform.",
            "clearance": "TS/SCI",
            "source": "test",
        },
    ]


@pytest.fixture
def sample_contact():
    """A single sample contact for testing."""
    return {
        "id": 1,
        "firstName": "Jane",
        "lastName": "Doe",
        "name": "Jane Doe",
        "email": "jane.doe@leidos.com",
        "company": "Leidos",
        "title": "VP of ISR Programs",
        "tier": 1,
    }


@pytest.fixture
def sample_program():
    """A single sample federal program for testing."""
    return {
        "program_name": "DCGS-A",
        "agency": "US Army",
        "prime_contractor": "Leidos",
        "contract_value": 950_000_000,
        "status": "Active",
        "keywords": ["intelligence", "surveillance", "reconnaissance", "ISR"],
    }


# ---------------------------------------------------------------------------
# Mock Service Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_qdrant_client():
    """A mock Qdrant client that returns empty results."""
    client = MagicMock()
    client.get_collections.return_value = MagicMock(collections=[])
    client.search.return_value = []
    client.upsert.return_value = None
    return client


@pytest.fixture
def mock_openai_client():
    """A mock OpenAI client for embeddings."""
    client = MagicMock()
    embedding_response = MagicMock()
    embedding_response.data = [MagicMock(embedding=[0.1] * 1536)]
    client.embeddings.create.return_value = embedding_response
    return client
