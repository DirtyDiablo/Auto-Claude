"""
Bullhorn REST API client with OAuth authentication.

Extracted from services/bullhorn_integration.py.  The public surface
is identical to the original so that existing call sites can switch
imports with no code changes.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import requests
import structlog

logger = structlog.get_logger("BD-Bullhorn")


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass
class BullhornConfig:
    """Configuration for Bullhorn CRM integration."""

    api_url: str = ""
    client_id: str = ""
    client_secret: str = ""
    username: str = ""
    password: str = ""

    # OAuth tokens (populated after authentication)
    access_token: str = ""
    refresh_token: str = ""
    rest_url: str = ""
    bh_rest_token: str = ""

    def __post_init__(self):
        """Fill blanks from environment variables."""
        self.api_url = self.api_url or os.getenv(
            "BULLHORN_API_URL", "https://rest.bullhornstaffing.com"
        )
        self.client_id = self.client_id or os.getenv("BULLHORN_CLIENT_ID", "")
        self.client_secret = self.client_secret or os.getenv(
            "BULLHORN_CLIENT_SECRET", ""
        )
        self.username = self.username or os.getenv("BULLHORN_USERNAME", "")
        self.password = self.password or os.getenv("BULLHORN_PASSWORD", "")


# ---------------------------------------------------------------------------
# Live client
# ---------------------------------------------------------------------------


class BullhornClient:
    """Client for the Bullhorn REST API."""

    def __init__(self, config: Optional[BullhornConfig] = None) -> None:
        self.config = config or BullhornConfig()
        self._authenticated = False
        self._token_expiry: Optional[datetime] = None

    # -- Authentication ------------------------------------------------

    def _ensure_authenticated(self) -> None:
        if not self._authenticated or (
            self._token_expiry and datetime.now() >= self._token_expiry
        ):
            self.authenticate()

    def authenticate(self) -> bool:
        """Multi-step Bullhorn OAuth flow."""
        if not self.config.client_id or not self.config.client_secret:
            logger.warning("Bullhorn credentials not configured")
            return False

        try:
            # Step 1: token exchange
            token_data = {
                "grant_type": "password",
                "client_id": self.config.client_id,
                "client_secret": self.config.client_secret,
                "username": self.config.username,
                "password": self.config.password,
            }
            token_url = f"{self.config.api_url}/oauth/token"
            response = requests.post(token_url, data=token_data, timeout=30)
            if response.status_code != 200:
                logger.error(
                    "bullhorn.oauth_failed",
                    status=response.status_code,
                    body=response.text[:200],
                )
                self._authenticated = False
                return False

            token_response = response.json()
            self.config.access_token = token_response.get("access_token", "")
            self.config.refresh_token = token_response.get("refresh_token", "")

            # Step 2: REST login
            login_url = f"{self.config.api_url}/rest-services/login"
            login_params = {
                "version": "2.0",
                "access_token": self.config.access_token,
            }
            login_response = requests.get(
                login_url, params=login_params, timeout=30
            )
            if login_response.status_code != 200:
                logger.error(
                    "bullhorn.rest_login_failed", status=login_response.status_code
                )
                self._authenticated = False
                return False

            login_data = login_response.json()
            self.config.rest_url = login_data.get("restUrl", "")
            self.config.bh_rest_token = login_data.get("BhRestToken", "")

            if not self.config.rest_url or not self.config.bh_rest_token:
                logger.error("bullhorn.rest_login_empty_tokens")
                self._authenticated = False
                return False

            self._authenticated = True
            self._token_expiry = datetime.now() + timedelta(hours=1)
            logger.info("bullhorn.authenticated")
            return True

        except Exception as e:
            logger.error("bullhorn.auth_failed", error=str(e))
            return False

    # -- HTTP helper ---------------------------------------------------

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
    ) -> Optional[Dict]:
        self._ensure_authenticated()

        if not self.config.rest_url or not self.config.bh_rest_token:
            logger.warning("bullhorn.not_authenticated")
            return None

        url = f"{self.config.rest_url}/{endpoint}"
        headers = {
            "BhRestToken": self.config.bh_rest_token,
            "Content-Type": "application/json",
        }

        try:
            response = requests.request(
                method=method,
                url=url,
                params=params,
                json=data,
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error("bullhorn.request_failed", error=str(e))
            return None

    # -- Candidate / Contact operations --------------------------------

    def search_candidates(
        self,
        query: str,
        fields: Optional[List[str]] = None,
        count: int = 20,
    ) -> List[Dict]:
        if fields is None:
            fields = [
                "id", "firstName", "lastName", "email", "phone",
                "occupation", "companyName", "status", "owner",
            ]
        params = {"query": query, "fields": ",".join(fields), "count": count}
        result = self._make_request("GET", "search/Candidate", params=params)
        return result.get("data", []) if result else []

    def get_candidate(
        self, candidate_id: int, fields: Optional[List[str]] = None
    ) -> Optional[Dict]:
        if fields is None:
            fields = [
                "id", "firstName", "lastName", "email", "phone", "mobile",
                "occupation", "companyName", "status", "address", "owner",
                "customText1", "customText2", "customText3",
            ]
        params = {"fields": ",".join(fields)}
        result = self._make_request(
            "GET", f"entity/Candidate/{candidate_id}", params=params
        )
        return result.get("data") if result else None

    def create_candidate(self, candidate_data: Dict) -> Optional[int]:
        result = self._make_request("PUT", "entity/Candidate", data=candidate_data)
        return result.get("changedEntityId") if result else None

    def update_candidate(self, candidate_id: int, updates: Dict) -> bool:
        result = self._make_request(
            "POST", f"entity/Candidate/{candidate_id}", data=updates
        )
        return result is not None

    # -- Contact enrichment --------------------------------------------

    def enrich_contact_from_bullhorn(self, contact: Dict) -> Dict:
        enriched = contact.copy()
        search_parts = []
        if contact.get("email"):
            search_parts.append(f'email:"{contact["email"]}"')
        if contact.get("name"):
            search_parts.append(f'name:"{contact["name"]}"')
        if not search_parts:
            return enriched

        query = " OR ".join(search_parts)
        candidates = self.search_candidates(query, count=5)
        if candidates:
            bh = candidates[0]
            enriched["bullhorn_id"] = bh.get("id")
            enriched["bullhorn_status"] = bh.get("status")
            if not enriched.get("phone") and bh.get("phone"):
                enriched["phone"] = bh["phone"]
            if not enriched.get("title") and bh.get("occupation"):
                enriched["title"] = bh["occupation"]
            enriched["_enriched_from_bullhorn"] = True
        return enriched

    # -- Job order operations ------------------------------------------

    def search_job_orders(
        self,
        query: str,
        fields: Optional[List[str]] = None,
        count: int = 20,
    ) -> List[Dict]:
        if fields is None:
            fields = [
                "id", "title", "clientCorporation", "status",
                "address", "employmentType", "dateAdded",
            ]
        params = {"query": query, "fields": ",".join(fields), "count": count}
        result = self._make_request("GET", "search/JobOrder", params=params)
        return result.get("data", []) if result else []

    def create_job_order(self, job_data: Dict) -> Optional[int]:
        job_order = {
            "title": job_data.get("Job Title/Position") or job_data.get("title", ""),
            "description": job_data.get("Position Overview")
            or job_data.get("description", ""),
            "employmentType": "Contract",
            "status": "Open",
            "customText1": job_data.get("_mapping", {}).get("program_name", ""),
            "customText2": str(
                job_data.get("_scoring", {}).get("BD Priority Score", 0)
            ),
            "customText3": job_data.get("Source", ""),
        }
        result = self._make_request("PUT", "entity/JobOrder", data=job_order)
        return result.get("changedEntityId") if result else None

    # -- Batch helpers -------------------------------------------------

    def enrich_contacts_batch(self, contacts: List[Dict]) -> List[Dict]:
        enriched = []
        for contact in contacts:
            try:
                enriched.append(self.enrich_contact_from_bullhorn(contact))
            except Exception as e:
                logger.error(
                    "bullhorn.enrich_failed",
                    contact=contact.get("name"),
                    error=str(e),
                )
                enriched.append(contact)
        return enriched

    def sync_contacts_batch(self, contacts: List[Dict]) -> Dict:
        results: Dict = {"synced": 0, "failed": 0, "bullhorn_ids": []}
        for contact in contacts:
            try:
                bh_id = self.sync_contact_to_bullhorn(contact)
                if bh_id:
                    results["synced"] += 1
                    results["bullhorn_ids"].append(bh_id)
                else:
                    results["failed"] += 1
            except Exception as e:
                logger.error(
                    "bullhorn.sync_failed",
                    contact=contact.get("name"),
                    error=str(e),
                )
                results["failed"] += 1
        return results

    def sync_contact_to_bullhorn(self, contact: Dict) -> Optional[int]:
        if contact.get("email"):
            existing = self.search_candidates(
                f'email:"{contact["email"]}"', count=1
            )
            if existing:
                candidate_id = existing[0]["id"]
                updates = self._contact_to_bullhorn_format(contact)
                self.update_candidate(candidate_id, updates)
                return candidate_id
        candidate_data = self._contact_to_bullhorn_format(contact)
        return self.create_candidate(candidate_data)

    @staticmethod
    def _contact_to_bullhorn_format(contact: Dict) -> Dict:
        name = contact.get("name", "")
        parts = name.split(None, 1)
        first_name = parts[0] if parts else ""
        last_name = parts[1] if len(parts) > 1 else ""
        return {
            "firstName": contact.get("first_name") or first_name,
            "lastName": last_name,
            "email": contact.get("email", ""),
            "phone": contact.get("phone", ""),
            "occupation": contact.get("title", ""),
            "companyName": contact.get("company", ""),
            "customText1": contact.get("program", ""),
            "customText2": contact.get("linkedin", ""),
            "customText3": "BD-Automation",
            "status": "Active",
        }


# ---------------------------------------------------------------------------
# Mock client (for testing without credentials)
# ---------------------------------------------------------------------------


class MockBullhornClient:
    """Mock client that stores data in memory."""

    def __init__(self, config: Optional[BullhornConfig] = None) -> None:
        self.config = config or BullhornConfig()
        self._mock_candidates: List[Dict] = []

    def authenticate(self) -> bool:
        return True

    def search_candidates(self, query: str, **kwargs) -> List[Dict]:
        return self._mock_candidates

    def get_candidate(self, candidate_id: int, **kwargs) -> Optional[Dict]:
        return {"id": candidate_id, "firstName": "Mock", "lastName": "User"}

    def create_candidate(self, candidate_data: Dict) -> int:
        mock_id = len(self._mock_candidates) + 1
        self._mock_candidates.append({**candidate_data, "id": mock_id})
        return mock_id

    def update_candidate(self, candidate_id: int, updates: Dict) -> bool:
        return True

    def enrich_contact_from_bullhorn(self, contact: Dict) -> Dict:
        enriched = contact.copy()
        enriched["_mock_enrichment"] = True
        return enriched

    def sync_contact_to_bullhorn(self, contact: Dict) -> int:
        return self.create_candidate(contact)

    def search_job_orders(self, query: str, **kwargs) -> List[Dict]:
        return []

    def create_job_order(self, job_data: Dict) -> int:
        return 1


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def get_bullhorn_client(use_mock: bool = False) -> BullhornClient:
    """Get a Bullhorn client (real or mock)."""
    config = BullhornConfig()
    if use_mock or not config.client_id:
        logger.info("bullhorn.using_mock_client")
        return MockBullhornClient(config)
    return BullhornClient(config)
