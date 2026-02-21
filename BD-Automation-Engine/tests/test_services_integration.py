"""Tests for service layer: BullhornClient and NotionSyncService.

All HTTP calls are mocked — no external services needed.
"""

import json
from datetime import datetime
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

# ---------------------------------------------------------------------------
# BullhornClient tests
# ---------------------------------------------------------------------------


@pytest.fixture()
def bullhorn_config():
    from services.bullhorn_integration import BullhornConfig

    return BullhornConfig(
        api_url="https://rest.bullhornstaffing.com",
        client_id="test-client-id",
        client_secret="test-secret",
        username="testuser",
        password="testpass",
    )


@pytest.fixture()
def bullhorn_client(bullhorn_config):
    from services.bullhorn_integration import BullhornClient

    client = BullhornClient(config=bullhorn_config)
    return client


@pytest.fixture()
def authenticated_client(bullhorn_client):
    """A BullhornClient that is already authenticated with mock tokens."""
    bullhorn_client._authenticated = True
    bullhorn_client.config.rest_url = "https://rest99.bullhornstaffing.com/rest-services/abc123"
    bullhorn_client.config.bh_rest_token = "fake-bh-rest-token"
    bullhorn_client.config.access_token = "fake-access-token"
    return bullhorn_client


class TestBullhornAuthenticate:
    @patch("services.bullhorn_integration.requests")
    def test_authenticate_success(self, mock_requests, bullhorn_client):
        # Step 2 — token response
        token_resp = MagicMock()
        token_resp.status_code = 200
        token_resp.json.return_value = {
            "access_token": "at_123",
            "refresh_token": "rt_456",
        }

        # Step 3 — REST login response
        login_resp = MagicMock()
        login_resp.status_code = 200
        login_resp.json.return_value = {
            "restUrl": "https://rest99.bullhornstaffing.com/rest-services/abc",
            "BhRestToken": "bh_token_789",
        }

        mock_requests.post.return_value = token_resp
        mock_requests.get.return_value = login_resp

        result = bullhorn_client.authenticate()
        assert result is True
        assert bullhorn_client._authenticated is True
        assert bullhorn_client.config.access_token == "at_123"
        assert bullhorn_client.config.bh_rest_token == "bh_token_789"

    @patch("services.bullhorn_integration.requests")
    def test_authenticate_token_failure(self, mock_requests, bullhorn_client):
        token_resp = MagicMock()
        token_resp.status_code = 401
        token_resp.text = "Invalid credentials"
        mock_requests.post.return_value = token_resp

        result = bullhorn_client.authenticate()
        assert result is False
        assert bullhorn_client._authenticated is False

    @patch("services.bullhorn_integration.requests")
    def test_authenticate_rest_login_failure(self, mock_requests, bullhorn_client):
        token_resp = MagicMock()
        token_resp.status_code = 200
        token_resp.json.return_value = {
            "access_token": "at_123",
            "refresh_token": "rt_456",
        }
        mock_requests.post.return_value = token_resp

        login_resp = MagicMock()
        login_resp.status_code = 500
        mock_requests.get.return_value = login_resp

        result = bullhorn_client.authenticate()
        assert result is False

    def test_authenticate_no_credentials(self):
        from services.bullhorn_integration import BullhornClient, BullhornConfig

        client = BullhornClient(config=BullhornConfig(client_id="", client_secret=""))
        result = client.authenticate()
        assert result is False

    @patch("services.bullhorn_integration.requests")
    def test_authenticate_empty_rest_url(self, mock_requests, bullhorn_client):
        token_resp = MagicMock()
        token_resp.status_code = 200
        token_resp.json.return_value = {"access_token": "at", "refresh_token": "rt"}
        mock_requests.post.return_value = token_resp

        login_resp = MagicMock()
        login_resp.status_code = 200
        login_resp.json.return_value = {"restUrl": "", "BhRestToken": ""}
        mock_requests.get.return_value = login_resp

        result = bullhorn_client.authenticate()
        assert result is False

    @patch("services.bullhorn_integration.requests")
    def test_authenticate_network_error(self, mock_requests, bullhorn_client):
        mock_requests.post.side_effect = ConnectionError("DNS failure")
        result = bullhorn_client.authenticate()
        assert result is False


class TestBullhornSearchCandidates:
    @patch("services.bullhorn_integration.requests")
    def test_search_candidates_success(self, mock_requests, authenticated_client):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {
            "data": [
                {"id": 1, "firstName": "Jane", "lastName": "Doe", "email": "jane@leidos.com"}
            ]
        }
        resp.raise_for_status = MagicMock()
        mock_requests.request.return_value = resp

        results = authenticated_client.search_candidates("Jane Doe")
        assert len(results) == 1
        assert results[0]["firstName"] == "Jane"

    @patch("services.bullhorn_integration.requests")
    def test_search_candidates_empty(self, mock_requests, authenticated_client):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"data": []}
        resp.raise_for_status = MagicMock()
        mock_requests.request.return_value = resp

        results = authenticated_client.search_candidates("nonexistent")
        assert results == []

    @patch("services.bullhorn_integration.requests")
    def test_search_candidates_api_error(self, mock_requests, authenticated_client):
        mock_requests.request.side_effect = Exception("timeout")
        results = authenticated_client.search_candidates("test")
        assert results == []

    @patch("services.bullhorn_integration.requests")
    def test_search_candidates_custom_fields(self, mock_requests, authenticated_client):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"data": [{"id": 1}]}
        resp.raise_for_status = MagicMock()
        mock_requests.request.return_value = resp

        authenticated_client.search_candidates("test", fields=["id", "email"], count=5)
        call_args = mock_requests.request.call_args
        assert call_args[1]["params"]["fields"] == "id,email"
        assert call_args[1]["params"]["count"] == 5


class TestBullhornEnrichContact:
    @patch("services.bullhorn_integration.requests")
    def test_enrich_merges_data(self, mock_requests, authenticated_client):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {
            "data": [
                {
                    "id": 42,
                    "firstName": "Jane",
                    "lastName": "Doe",
                    "phone": "555-0100",
                    "occupation": "VP of Programs",
                    "status": "Active",
                }
            ]
        }
        resp.raise_for_status = MagicMock()
        mock_requests.request.return_value = resp

        contact = {"name": "Jane Doe", "email": "jane@leidos.com", "company": "Leidos"}
        enriched = authenticated_client.enrich_contact_from_bullhorn(contact)

        assert enriched["bullhorn_id"] == 42
        assert enriched["phone"] == "555-0100"
        assert enriched["_enriched_from_bullhorn"] is True

    @patch("services.bullhorn_integration.requests")
    def test_enrich_no_match(self, mock_requests, authenticated_client):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"data": []}
        resp.raise_for_status = MagicMock()
        mock_requests.request.return_value = resp

        contact = {"name": "Nobody", "email": "nobody@example.com"}
        enriched = authenticated_client.enrich_contact_from_bullhorn(contact)
        assert "bullhorn_id" not in enriched

    def test_enrich_no_search_criteria(self, authenticated_client):
        contact = {"company": "Leidos"}  # no name, no email
        enriched = authenticated_client.enrich_contact_from_bullhorn(contact)
        assert enriched == contact  # returned unchanged

    @patch("services.bullhorn_integration.requests")
    def test_enrich_does_not_overwrite_existing_fields(self, mock_requests, authenticated_client):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {
            "data": [{"id": 1, "phone": "999-9999", "occupation": "Manager"}]
        }
        resp.raise_for_status = MagicMock()
        mock_requests.request.return_value = resp

        contact = {"name": "Jane", "phone": "111-1111", "title": "Director"}
        enriched = authenticated_client.enrich_contact_from_bullhorn(contact)
        # Existing phone and title should NOT be overwritten
        assert enriched["phone"] == "111-1111"
        assert enriched["title"] == "Director"


class TestBullhornSyncContact:
    @patch("services.bullhorn_integration.requests")
    def test_sync_creates_new_candidate(self, mock_requests, authenticated_client):
        # First call: search returns empty (no existing)
        search_resp = MagicMock()
        search_resp.status_code = 200
        search_resp.json.return_value = {"data": []}
        search_resp.raise_for_status = MagicMock()

        # Second call: create returns ID
        create_resp = MagicMock()
        create_resp.status_code = 200
        create_resp.json.return_value = {"changedEntityId": 99}
        create_resp.raise_for_status = MagicMock()

        mock_requests.request.side_effect = [search_resp, create_resp]

        contact = {"name": "New Person", "email": "new@gdit.com", "company": "GDIT"}
        result = authenticated_client.sync_contact_to_bullhorn(contact)
        assert result == 99

    @patch("services.bullhorn_integration.requests")
    def test_sync_updates_existing(self, mock_requests, authenticated_client):
        # Search returns existing
        search_resp = MagicMock()
        search_resp.status_code = 200
        search_resp.json.return_value = {"data": [{"id": 50}]}
        search_resp.raise_for_status = MagicMock()

        # Update succeeds
        update_resp = MagicMock()
        update_resp.status_code = 200
        update_resp.json.return_value = {"changedEntityId": 50}
        update_resp.raise_for_status = MagicMock()

        mock_requests.request.side_effect = [search_resp, update_resp]

        contact = {"name": "Existing Person", "email": "existing@leidos.com"}
        result = authenticated_client.sync_contact_to_bullhorn(contact)
        assert result == 50


class TestBullhornContactFormat:
    def test_contact_to_bullhorn_format(self, authenticated_client):
        contact = {
            "name": "Jane Doe",
            "email": "jane@example.com",
            "phone": "555-1234",
            "title": "Program Manager",
            "company": "Leidos",
            "program": "DCGS-A",
            "linkedin": "https://linkedin.com/in/jane",
        }
        result = authenticated_client._contact_to_bullhorn_format(contact)
        assert result["firstName"] == "Jane"
        assert result["lastName"] == "Doe"
        assert result["email"] == "jane@example.com"
        assert result["occupation"] == "Program Manager"
        assert result["customText1"] == "DCGS-A"
        assert result["customText3"] == "BD-Automation"

    def test_contact_format_single_name(self, authenticated_client):
        contact = {"name": "Madonna"}
        result = authenticated_client._contact_to_bullhorn_format(contact)
        assert result["firstName"] == "Madonna"
        assert result["lastName"] == ""


# ---------------------------------------------------------------------------
# NotionSyncService tests
# ---------------------------------------------------------------------------


@pytest.fixture()
def notion_config():
    from services.notion_sync import NotionConfig

    return NotionConfig(
        token="test-notion-token",
        db_jobs="db-jobs-id-123",
        db_dcgs_contacts="db-contacts-id-456",
    )


@pytest.fixture()
def notion_service(notion_config):
    from services.notion_sync import NotionSyncService

    return NotionSyncService(config=notion_config)


class TestNotionGetDataSource:
    @patch("services.notion_sync.requests")
    def test_get_data_source_id(self, mock_requests, notion_service):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {
            "data_sources": [{"id": "ds-001"}, {"id": "ds-002"}]
        }
        resp.raise_for_status = MagicMock()
        mock_requests.get.return_value = resp

        ds_id = notion_service.get_data_source_id("db-jobs-id-123")
        assert ds_id == "ds-001"

    @patch("services.notion_sync.requests")
    def test_get_data_source_id_cached(self, mock_requests, notion_service):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"data_sources": [{"id": "ds-cached"}]}
        resp.raise_for_status = MagicMock()
        mock_requests.get.return_value = resp

        # First call fetches from API
        notion_service.get_data_source_id("db-123")
        # Second call uses cache
        notion_service.get_data_source_id("db-123")
        assert mock_requests.get.call_count == 1

    @patch("services.notion_sync.requests")
    def test_get_data_source_id_no_sources(self, mock_requests, notion_service):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"data_sources": []}
        resp.raise_for_status = MagicMock()
        mock_requests.get.return_value = resp

        with pytest.raises(ValueError, match="No data sources"):
            notion_service.get_data_source_id("db-empty")

    def test_clear_data_source_cache(self, notion_service):
        notion_service._data_source_cache["db-123"] = "ds-old"
        notion_service.clear_data_source_cache()
        assert len(notion_service._data_source_cache) == 0


class TestNotionCreateJobPage:
    @patch("services.notion_sync.requests")
    def test_create_job_page_success(self, mock_requests, notion_service):
        # Mock get_data_source_id response
        ds_resp = MagicMock()
        ds_resp.status_code = 200
        ds_resp.json.return_value = {"data_sources": [{"id": "ds-001"}]}
        ds_resp.raise_for_status = MagicMock()

        # Mock page creation response
        create_resp = MagicMock()
        create_resp.status_code = 200
        create_resp.json.return_value = {"id": "page-abc-123"}
        create_resp.raise_for_status = MagicMock()

        mock_requests.get.return_value = ds_resp
        mock_requests.post.return_value = create_resp

        job = {
            "title": "Systems Engineer",
            "company": "Leidos",
            "location": "Fort Belvoir, VA",
            "clearance": "TS/SCI",
            "_mapping": {"program_name": "DCGS-A", "match_confidence": 0.85, "match_type": "keyword"},
            "_scoring": {"BD Priority Score": 82, "Priority Tier": "Tier 1 Hot"},
        }
        page_id = notion_service.create_job_page(job)
        assert page_id == "page-abc-123"

    def test_create_job_page_no_db_configured(self):
        from services.notion_sync import NotionSyncService, NotionConfig

        svc = NotionSyncService(config=NotionConfig(token="tok", db_jobs=""))
        assert svc.create_job_page({"title": "test"}) is None

    @patch("services.notion_sync.requests")
    def test_create_job_page_api_error(self, mock_requests, notion_service):
        ds_resp = MagicMock()
        ds_resp.status_code = 200
        ds_resp.json.return_value = {"data_sources": [{"id": "ds-001"}]}
        ds_resp.raise_for_status = MagicMock()
        mock_requests.get.return_value = ds_resp

        create_resp = MagicMock()
        create_resp.raise_for_status.side_effect = Exception("API error")
        mock_requests.post.return_value = create_resp

        page_id = notion_service.create_job_page({"title": "test"})
        assert page_id is None


class TestNotionSyncJobsBatch:
    @patch("services.notion_sync.requests")
    def test_sync_batch(self, mock_requests, notion_service):
        ds_resp = MagicMock()
        ds_resp.status_code = 200
        ds_resp.json.return_value = {"data_sources": [{"id": "ds-001"}]}
        ds_resp.raise_for_status = MagicMock()

        create_resp = MagicMock()
        create_resp.status_code = 200
        create_resp.json.return_value = {"id": "page-1"}
        create_resp.raise_for_status = MagicMock()

        mock_requests.get.return_value = ds_resp
        mock_requests.post.return_value = create_resp

        jobs = [{"title": f"Job {i}", "company": "GDIT"} for i in range(3)]
        results = notion_service.sync_jobs_batch(jobs)
        assert results["created"] == 3
        assert results["failed"] == 0
        assert len(results["page_ids"]) == 3


class TestNotionGetJobsNeedingReview:
    @patch("services.notion_sync.requests")
    def test_returns_jobs(self, mock_requests, notion_service):
        ds_resp = MagicMock()
        ds_resp.status_code = 200
        ds_resp.json.return_value = {"data_sources": [{"id": "ds-001"}]}
        ds_resp.raise_for_status = MagicMock()

        query_resp = MagicMock()
        query_resp.status_code = 200
        query_resp.json.return_value = {"results": []}
        query_resp.raise_for_status = MagicMock()

        mock_requests.get.return_value = ds_resp
        mock_requests.post.return_value = query_resp

        jobs = notion_service.get_jobs_needing_review()
        assert isinstance(jobs, list)

    def test_returns_empty_when_no_db(self):
        from services.notion_sync import NotionSyncService, NotionConfig

        svc = NotionSyncService(config=NotionConfig(token="tok", db_jobs=""))
        assert svc.get_jobs_needing_review() == []


class TestNotionGetDashboardStats:
    @patch("services.notion_sync.requests")
    def test_returns_stats(self, mock_requests, notion_service):
        ds_resp = MagicMock()
        ds_resp.status_code = 200
        ds_resp.json.return_value = {"data_sources": [{"id": "ds-001"}]}
        ds_resp.raise_for_status = MagicMock()

        query_resp = MagicMock()
        query_resp.status_code = 200
        query_resp.json.return_value = {"results": []}
        query_resp.raise_for_status = MagicMock()

        mock_requests.get.return_value = ds_resp
        mock_requests.post.return_value = query_resp

        stats = notion_service.get_dashboard_stats()
        assert "total_jobs" in stats
        assert "hot_leads" in stats

    def test_returns_empty_when_no_db(self):
        from services.notion_sync import NotionSyncService, NotionConfig

        svc = NotionSyncService(config=NotionConfig(token="tok", db_jobs=""))
        assert svc.get_dashboard_stats() == {}


class TestNotionFormatHelpers:
    def test_format_rich_text(self, notion_service):
        result = notion_service._format_rich_text("Hello World")
        assert result[0]["text"]["content"] == "Hello World"

    def test_format_rich_text_empty(self, notion_service):
        result = notion_service._format_rich_text("")
        assert result == []

    def test_format_rich_text_truncates(self, notion_service):
        long_text = "x" * 5000
        result = notion_service._format_rich_text(long_text)
        assert len(result[0]["text"]["content"]) == 2000

    def test_format_select(self, notion_service):
        result = notion_service._format_select("Active")
        assert result == {"name": "Active"}

    def test_format_select_none(self, notion_service):
        result = notion_service._format_select("")
        assert result is None

    def test_format_number(self, notion_service):
        assert notion_service._format_number(42) == 42.0
        assert notion_service._format_number("3.14") == 3.14
        assert notion_service._format_number(None) is None
        assert notion_service._format_number("not-a-number") is None

    def test_format_url(self, notion_service):
        assert notion_service._format_url("https://example.com") == "https://example.com"
        assert notion_service._format_url("not-a-url") is None
        assert notion_service._format_url("") is None

    def test_format_date(self, notion_service):
        result = notion_service._format_date("2026-01-15")
        assert result == {"start": "2026-01-15"}

    def test_format_date_empty(self, notion_service):
        assert notion_service._format_date("") is None
        assert notion_service._format_date(None) is None
