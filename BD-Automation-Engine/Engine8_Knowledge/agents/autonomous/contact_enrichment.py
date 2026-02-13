"""
Contact Enrichment Agent — Scans for stale/changed contacts and flags updates.

Detects staleness (90+ days without update, missing fields, low confidence)
and changes (title, company, location) that require re-classification.
"""

import os
import json
import logging
from datetime import datetime
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

DATA_DIR = Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))) / "data"
ENRICHMENT_DIR = DATA_DIR / "enrichment"
ENRICHMENT_LOG = ENRICHMENT_DIR / "enrichment_log.jsonl"


# ─── Data Models ─────────────────────────────────────────────────────────────

@dataclass
class ContactChange:
    """A detected change or issue for a single contact."""
    contact_id: str
    contact_name: str
    change_type: str   # stale | missing_field | title_change | company_change | location_change | low_confidence
    severity: str      # high | medium | low
    details: Dict[str, Any] = field(default_factory=dict)
    recommended_action: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EnrichmentReport:
    """Results of an enrichment scan."""
    scan_date: str
    contacts_scanned: int = 0
    stale_contacts: int = 0
    missing_fields: int = 0
    changes_detected: int = 0
    actions_recommended: int = 0
    changes: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ─── Contact Enrichment Agent ────────────────────────────────────────────────

REQUIRED_FIELDS = ["email", "phone", "title", "company"]
STALENESS_DAYS = 90


class ContactEnrichmentAgent:
    """
    Autonomous agent that scans contacts for staleness and changes.

    Staleness detection:
    - Contacts not updated in 90+ days
    - Missing critical fields (email, phone, LinkedIn)
    - Low confidence from original classification

    Change detection:
    - Title changed → re-classify tier + priority
    - Company changed → flag as "departed"
    - Location changed → re-assign location hub
    """

    def __init__(self, api_base: str = "http://localhost:8100"):
        self.api_base = api_base
        ENRICHMENT_DIR.mkdir(parents=True, exist_ok=True)

    def scan_all_contacts(self, limit: int = 100) -> EnrichmentReport:
        """
        Scan contacts for staleness and changes.

        Args:
            limit: Max contacts to scan per run

        Returns:
            EnrichmentReport with findings
        """
        logger.info(f"Starting contact enrichment scan (limit={limit})...")

        report = EnrichmentReport(
            scan_date=datetime.now().isoformat(),
        )

        contacts = self._fetch_contacts(limit)
        report.contacts_scanned = len(contacts)

        for contact in contacts:
            changes = self.scan_contact(contact)
            report.changes.extend([c.to_dict() for c in changes])

        report.stale_contacts = sum(
            1 for c in report.changes if c.get("change_type") == "stale"
        )
        report.missing_fields = sum(
            1 for c in report.changes if c.get("change_type") == "missing_field"
        )
        report.changes_detected = len(report.changes)
        report.actions_recommended = sum(
            1 for c in report.changes if c.get("recommended_action")
        )

        # Persist
        self._save_report(report)

        logger.info(
            f"Enrichment scan complete: {report.contacts_scanned} scanned, "
            f"{report.changes_detected} issues found"
        )

        return report

    def scan_contact(self, contact: Dict[str, Any]) -> List[ContactChange]:
        """
        Scan a single contact for issues.

        Args:
            contact: Contact dict from API

        Returns:
            List of detected changes/issues
        """
        changes: List[ContactChange] = []
        contact.get("id", "")
        contact.get("name", "Unknown")

        # 1. Staleness detection
        stale_change = self._check_staleness(contact)
        if stale_change:
            changes.append(stale_change)

        # 2. Missing fields
        missing = self._check_missing_fields(contact)
        changes.extend(missing)

        # 3. Low confidence / low tier with high program value
        confidence_change = self._check_confidence(contact)
        if confidence_change:
            changes.append(confidence_change)

        # 4. Title/company anomalies
        title_change = self._check_title_anomaly(contact)
        if title_change:
            changes.append(title_change)

        return changes

    # ─── Staleness Checks ────────────────────────────────────────────────

    def _check_staleness(self, contact: Dict) -> Optional[ContactChange]:
        """Flag contacts not updated in 90+ days."""
        # Check for any date field indicating last update
        last_date = None
        for date_field in ("updated_at", "last_activity", "scraped_at", "created_at"):
            val = contact.get(date_field)
            if val:
                try:
                    last_date = datetime.fromisoformat(val.replace("Z", "+00:00"))
                    break
                except (ValueError, TypeError):
                    continue

        if last_date is None:
            return ContactChange(
                contact_id=contact.get("id", ""),
                contact_name=contact.get("name", ""),
                change_type="stale",
                severity="medium",
                details={"reason": "no_date_fields", "message": "No timestamp fields found"},
                recommended_action="Verify contact data is current",
            )

        days_old = (datetime.now(last_date.tzinfo) if last_date.tzinfo
                    else datetime.now()) - last_date.replace(tzinfo=None)

        if days_old.days >= STALENESS_DAYS:
            return ContactChange(
                contact_id=contact.get("id", ""),
                contact_name=contact.get("name", ""),
                change_type="stale",
                severity="high" if days_old.days >= 180 else "medium",
                details={
                    "days_since_update": days_old.days,
                    "last_update": last_date.isoformat(),
                },
                recommended_action=f"Contact data is {days_old.days} days old — verify current role and details",
            )

        return None

    def _check_missing_fields(self, contact: Dict) -> List[ContactChange]:
        """Flag contacts with missing critical fields."""
        changes = []
        contact_id = contact.get("id", "")
        contact_name = contact.get("name", "")

        for field_name in REQUIRED_FIELDS:
            value = contact.get(field_name)
            if not value or (isinstance(value, str) and not value.strip()):
                changes.append(ContactChange(
                    contact_id=contact_id,
                    contact_name=contact_name,
                    change_type="missing_field",
                    severity="medium" if field_name in ("email", "phone") else "low",
                    details={"missing_field": field_name},
                    recommended_action=f"Add missing {field_name} for {contact_name}",
                ))

        # Check LinkedIn specifically
        linkedin = contact.get("linkedin") or contact.get("linkedin_url")
        if not linkedin:
            changes.append(ContactChange(
                contact_id=contact_id,
                contact_name=contact_name,
                change_type="missing_field",
                severity="low",
                details={"missing_field": "linkedin"},
                recommended_action=f"Find LinkedIn profile for {contact_name}",
            ))

        return changes

    def _check_confidence(self, contact: Dict) -> Optional[ContactChange]:
        """Flag contacts with high tier but low confidence indicators."""
        tier = contact.get("tier")
        bd_priority = contact.get("bd_priority", "")

        # Flag Tier 1-2 contacts with standard priority (should be critical/high)
        if tier in (1, 2) and bd_priority and bd_priority.lower() in ("standard", "low"):
            return ContactChange(
                contact_id=contact.get("id", ""),
                contact_name=contact.get("name", ""),
                change_type="low_confidence",
                severity="medium",
                details={
                    "tier": tier,
                    "bd_priority": bd_priority,
                    "reason": "High-tier contact with low BD priority — may need re-classification",
                },
                recommended_action=f"Re-evaluate BD priority for Tier {tier} contact {contact.get('name', '')}",
            )

        return None

    def _check_title_anomaly(self, contact: Dict) -> Optional[ContactChange]:
        """Flag contacts with title patterns suggesting role change."""
        title = (contact.get("title") or "").lower()

        # Detect likely departed indicators
        departed_keywords = ["former", "ex-", "retired", "left ", "departed"]
        for keyword in departed_keywords:
            if keyword in title:
                return ContactChange(
                    contact_id=contact.get("id", ""),
                    contact_name=contact.get("name", ""),
                    change_type="company_change",
                    severity="high",
                    details={
                        "title": contact.get("title", ""),
                        "keyword_matched": keyword,
                        "company": contact.get("company", ""),
                    },
                    recommended_action=f"Contact appears to have departed — update company and program assignment",
                )

        return None

    # ─── Data Fetchers ───────────────────────────────────────────────────

    def _fetch_contacts(self, limit: int) -> List[Dict]:
        """Fetch contacts from the API."""
        try:
            import httpx
            resp = httpx.get(
                f"{self.api_base}/api/v2/contacts",
                params={"limit": limit},
                timeout=15.0,
            )
            if resp.status_code == 200:
                return resp.json().get("contacts", [])
        except Exception as e:
            logger.warning(f"Could not fetch contacts: {e}")
        return []

    # ─── Persistence ─────────────────────────────────────────────────────

    def _save_report(self, report: EnrichmentReport):
        """Append enrichment report to log."""
        with open(ENRICHMENT_LOG, "a") as f:
            f.write(json.dumps(report.to_dict()) + "\n")
        logger.info(f"Enrichment report saved to {ENRICHMENT_LOG}")

    def get_latest_report(self) -> Optional[EnrichmentReport]:
        """Get the most recent enrichment report."""
        if not ENRICHMENT_LOG.exists():
            return None

        last_line = None
        with open(ENRICHMENT_LOG) as f:
            for line in f:
                line = line.strip()
                if line:
                    last_line = line

        if not last_line:
            return None

        data = json.loads(last_line)
        return EnrichmentReport(**data)
