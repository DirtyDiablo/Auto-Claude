"""Phase 38A — Self-Healing Pipeline

Autonomous data repair that fixes issues without human intervention.
15+ auto-fix strategies with cascading updates, confidence thresholds,
and full audit logging.
"""

import logging
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from src.data_quality.engine import (
    DataIssue,
    classify_title_tier,
    PROGRAM_LOCATION_MAP,
    VALID_CLEARANCE_LEVELS,
)

logger = logging.getLogger(__name__)


# =========================================
# ENUMS & DATA CLASSES
# =========================================

class FixStatus(str, Enum):
    FIXED = "fixed"
    SKIPPED = "skipped"
    FAILED = "failed"
    NEEDS_HUMAN = "needs_human"


@dataclass
class AutoFixResult:
    """Result of an auto-fix attempt."""
    issue: DataIssue
    status: str  # fixed, skipped, failed, needs_human
    confidence: float
    old_value: Any = None
    new_value: Any = None
    healer_used: str = ""
    cascading_fixes: List["AutoFixResult"] = field(default_factory=list)
    timestamp: str = ""
    reason: str = ""


@dataclass
class HealerConfig:
    """Configuration for a data healer."""
    name: str
    domain: str
    field_name: str
    fix_fn: Optional[Callable] = None
    confidence: float = 0.9
    description: str = ""


# =========================================
# FIX FUNCTIONS
# =========================================

def fix_email_normalize(value: str) -> tuple:
    """Normalize email: lowercase, strip, fix common typos."""
    if not value:
        return None, 0.0
    email = value.strip().lower()

    # Common domain typos
    typo_map = {
        ".con": ".com", ".cmo": ".com", ".ocom": ".com",
        ".coom": ".com", ".orgg": ".org", ".rog": ".org",
        ".nett": ".net", ".gmal.com": ".gmail.com",
        ".gmial.com": ".gmail.com", ".yaho.com": ".yahoo.com",
    }
    for typo, fix in typo_map.items():
        if email.endswith(typo):
            email = email[:-len(typo)] + fix
            return email, 0.95

    if email != value:
        return email, 0.98
    return value, 1.0


def fix_phone_format(value: str) -> tuple:
    """Normalize phone to E.164 format."""
    if not value:
        return None, 0.0
    digits = re.sub(r'\D', '', value.strip())
    if not digits:
        return None, 0.0

    # US numbers
    if len(digits) == 10:
        formatted = f"+1{digits}"
        return formatted, 0.95
    elif len(digits) == 11 and digits.startswith("1"):
        formatted = f"+{digits}"
        return formatted, 0.95
    elif len(digits) >= 7 and len(digits) <= 15:
        if not digits.startswith("1"):
            formatted = f"+1{digits}" if len(digits) == 10 else f"+{digits}"
        else:
            formatted = f"+{digits}"
        return formatted, 0.85
    return value, 0.5


def fix_name_capitalize(value: str) -> tuple:
    """Fix ALL CAPS or all lowercase names to proper case."""
    if not value:
        return None, 0.0
    name = value.strip()
    if name.isupper() or name.islower():
        # Handle special cases
        parts = name.split()
        fixed_parts = []
        for part in parts:
            lower = part.lower()
            # Keep certain prefixes lowercase
            if lower in ("de", "van", "von", "di", "del", "la", "le"):
                fixed_parts.append(lower)
            elif lower.startswith("mc") and len(lower) > 2:
                fixed_parts.append("Mc" + lower[2:].capitalize())
            elif lower.startswith("o'") and len(lower) > 2:
                fixed_parts.append("O'" + lower[2:].capitalize())
            else:
                fixed_parts.append(lower.capitalize())
        result = " ".join(fixed_parts)
        return result, 0.92
    return value, 1.0


def fix_title_standardize(value: str) -> tuple:
    """Map job title variants to canonical forms."""
    if not value:
        return None, 0.0
    title = value.strip()

    abbreviation_map = {
        "Sr.": "Senior", "Sr ": "Senior ", "Jr.": "Junior", "Jr ": "Junior ",
        "VP": "Vice President", "SVP": "Senior Vice President",
        "EVP": "Executive Vice President", "AVP": "Assistant Vice President",
        "Dir.": "Director", "Dir ": "Director ", "Mgr": "Manager",
        "Mgr.": "Manager", "Engr": "Engineer", "Engr.": "Engineer",
        "Dept": "Department", "Dept.": "Department", "Assoc": "Associate",
        "Assoc.": "Associate", "Admin": "Administrator", "Admin.": "Administrator",
        "Coord": "Coordinator", "Coord.": "Coordinator",
    }

    fixed = title
    for abbr, full in abbreviation_map.items():
        if abbr in fixed:
            fixed = fixed.replace(abbr, full)

    confidence = 0.93 if fixed != title else 1.0
    return fixed, confidence


def fix_location_geocode(value: str) -> tuple:
    """Parse freeform location into structured form."""
    if not value:
        return None, 0.0
    location = value.strip()

    # Known location normalization
    location_map = {
        "san diego, ca": "San Diego, CA",
        "san diego ca": "San Diego, CA",
        "la mesa, ca": "La Mesa, CA",
        "hampton, va": "Hampton, VA",
        "hampton roads, va": "Hampton Roads, VA",
        "langley afb": "Langley AFB, VA",
        "langley, va": "Langley, VA",
        "beale afb": "Beale AFB, CA",
        "ramstein ab": "Ramstein AB, Germany",
        "osan ab": "Osan AB, South Korea",
        "washington dc": "Washington, DC",
        "washington, dc": "Washington, DC",
    }

    lower = location.lower().strip()
    if lower in location_map:
        return location_map[lower], 0.97

    # Basic normalization: title case
    if location.isupper() or location.islower():
        return location.title(), 0.88

    return location, 1.0


def fix_program_from_location(location: str) -> tuple:
    """Reassign program based on location."""
    if not location:
        return None, 0.0
    loc_lower = location.lower().strip()
    for loc_key, program in PROGRAM_LOCATION_MAP.items():
        if loc_key in loc_lower:
            return program, 0.92
    return None, 0.0


def fix_tier_from_title(title: str) -> tuple:
    """Recalculate tier from job title."""
    if not title:
        return None, 0.0
    tier = classify_title_tier(title)
    return tier, 0.95


def fix_clearance_normalize(value: str) -> tuple:
    """Map clearance text to standardized levels."""
    if not value:
        return None, 0.0

    clearance_map = {
        "ts": "top_secret",
        "ts/sci": "ts_sci",
        "top secret": "top_secret",
        "top secret/sci": "ts_sci",
        "sci": "ts_sci",
        "s": "secret",
        "secret": "secret",
        "conf": "confidential",
        "confidential": "confidential",
        "public trust": "public_trust",
        "pt": "public_trust",
        "none": "none",
        "n/a": "none",
    }

    lower = value.lower().strip()
    if lower in clearance_map:
        return clearance_map[lower], 0.96
    return value, 0.5


def fix_date_format(value: str) -> tuple:
    """Normalize date to ISO 8601."""
    if not value:
        return None, 0.0

    import re
    # Try common formats
    formats = [
        (r'(\d{1,2})/(\d{1,2})/(\d{4})', lambda m: f"{m.group(3)}-{m.group(1).zfill(2)}-{m.group(2).zfill(2)}"),
        (r'(\d{4})-(\d{1,2})-(\d{1,2})', lambda m: f"{m.group(1)}-{m.group(2).zfill(2)}-{m.group(3).zfill(2)}"),
        (r'(\w+) (\d{1,2}), (\d{4})', None),
    ]
    for pattern, formatter in formats:
        match = re.match(pattern, value.strip())
        if match and formatter:
            try:
                result = formatter(match)
                return result, 0.95
            except (ValueError, IndexError):
                continue

    return value, 0.5


def fix_value_normalize(value: Any) -> tuple:
    """Parse contract value text to number."""
    if value is None:
        return None, 0.0
    if isinstance(value, (int, float)):
        return value, 1.0

    text = str(value).strip().replace(",", "").replace("$", "")
    multipliers = {
        "k": 1_000, "m": 1_000_000, "b": 1_000_000_000,
        "million": 1_000_000, "billion": 1_000_000_000,
        "thousand": 1_000,
    }
    for suffix, mult in multipliers.items():
        if text.lower().endswith(suffix):
            try:
                num = float(text[:text.lower().rindex(suffix)].strip())
                return num * mult, 0.9
            except (ValueError, IndexError):
                continue
    try:
        return float(text), 0.95
    except ValueError:
        return value, 0.0


def fix_linkedin_url(value: str) -> tuple:
    """Fix common LinkedIn URL issues."""
    if not value:
        return None, 0.0
    url = value.strip().rstrip("/")
    if "linkedin.com" not in url:
        return value, 0.0

    # Add /in/ if missing
    if "/in/" not in url and "/company/" not in url:
        # Try to extract handle
        parts = url.rstrip("/").split("/")
        handle = parts[-1] if parts else ""
        if handle and handle != "linkedin.com":
            url = f"https://www.linkedin.com/in/{handle}"
            return url, 0.85

    # Normalize to https
    if url.startswith("http://"):
        url = "https://" + url[7:]
        return url, 0.98

    return url, 1.0


# =========================================
# SELF-HEALING PIPELINE
# =========================================

class SelfHealingPipeline:
    """Fixes data quality issues automatically when confidence is high enough."""

    def __init__(self, confidence_threshold: float = 0.85):
        self.confidence_threshold = confidence_threshold
        self._healers = self._register_healers()
        self._audit_log: List[AutoFixResult] = []
        self._records: Dict[str, Dict[str, Dict]] = {}  # domain -> {id -> record}

    def set_records(self, domain: str, records: List[Dict[str, Any]]) -> None:
        """Load records for a domain so healing can be applied."""
        self._records[domain] = {r.get("id", str(i)): r for i, r in enumerate(records)}

    def get_audit_log(self) -> List[AutoFixResult]:
        """Get log of all auto-fix attempts."""
        return self._audit_log

    def get_fixed_records(self, domain: str) -> List[Dict[str, Any]]:
        """Get records after healing has been applied."""
        return list(self._records.get(domain, {}).values())

    def _register_healers(self) -> Dict[str, HealerConfig]:
        """Register all data healers."""
        return {
            "email_normalizer": HealerConfig(
                name="email_normalizer", domain="contacts", field_name="email",
                fix_fn=fix_email_normalize, confidence=0.95,
                description="Lowercase, strip whitespace, fix common typos",
            ),
            "phone_formatter": HealerConfig(
                name="phone_formatter", domain="contacts", field_name="phone",
                fix_fn=fix_phone_format, confidence=0.90,
                description="Normalize to E.164 format",
            ),
            "name_capitalizer": HealerConfig(
                name="name_capitalizer", domain="contacts", field_name="name",
                fix_fn=fix_name_capitalize, confidence=0.92,
                description="Fix ALL CAPS or all lowercase names",
            ),
            "title_standardizer": HealerConfig(
                name="title_standardizer", domain="contacts", field_name="job_title",
                fix_fn=fix_title_standardize, confidence=0.93,
                description="Map title abbreviations to canonical forms",
            ),
            "location_geocoder": HealerConfig(
                name="location_geocoder", domain="contacts", field_name="location",
                fix_fn=fix_location_geocode, confidence=0.90,
                description="Parse freeform location to structured form",
            ),
            "program_reassigner": HealerConfig(
                name="program_reassigner", domain="contacts", field_name="program",
                fix_fn=lambda v: fix_program_from_location(v), confidence=0.92,
                description="Re-map program based on location",
            ),
            "tier_recalculator": HealerConfig(
                name="tier_recalculator", domain="contacts", field_name="hierarchy_tier",
                fix_fn=lambda v: fix_tier_from_title(v), confidence=0.95,
                description="Recalculate tier from job title",
            ),
            "clearance_mapper": HealerConfig(
                name="clearance_mapper", domain="jobs", field_name="clearance",
                fix_fn=fix_clearance_normalize, confidence=0.96,
                description="Map clearance text to standardized levels",
            ),
            "date_formatter": HealerConfig(
                name="date_formatter", domain="programs", field_name="dates",
                fix_fn=fix_date_format, confidence=0.95,
                description="Normalize dates to ISO 8601",
            ),
            "value_normalizer": HealerConfig(
                name="value_normalizer", domain="programs", field_name="contract_value",
                fix_fn=fix_value_normalize, confidence=0.90,
                description="Parse value text to consistent number format",
            ),
            "linkedin_fixer": HealerConfig(
                name="linkedin_fixer", domain="contacts", field_name="linkedin_url",
                fix_fn=fix_linkedin_url, confidence=0.85,
                description="Fix common LinkedIn URL issues",
            ),
            "acronym_expander": HealerConfig(
                name="acronym_expander", domain="programs", field_name="name",
                fix_fn=None, confidence=0.90,
                description="Expand known acronyms",
            ),
        }

    def _select_healer(self, issue: DataIssue) -> Optional[HealerConfig]:
        """Select the appropriate healer for an issue."""
        # Map issue rule names to healers
        healer_map = {
            "email_valid": "email_normalizer",
            "email_required": "email_normalizer",
            "phone_valid": "phone_formatter",
            "title_tier_consistency": "tier_recalculator",
            "location_program_consistency": "program_reassigner",
            "clearance_valid": "clearance_mapper",
            "contact_freshness": None,  # Can't auto-fix staleness
            "job_location_parsed": "location_geocoder",
            "contract_not_expired": None,  # Can't extend contracts
            "value_range_valid": "value_normalizer",
            "embedding_present": None,  # Need embedding model
            "classification_confidence": None,  # Need re-classification
        }

        # Check if the issue has a suggested healer
        for rule_name, healer_name in healer_map.items():
            if rule_name in issue.description.lower() or (
                issue.field_name in self._field_to_healer()
            ):
                if healer_name and healer_name in self._healers:
                    return self._healers[healer_name]

        # Fallback: match by field name
        healer_name = self._field_to_healer().get(issue.field_name)
        if healer_name and healer_name in self._healers:
            return self._healers[healer_name]

        return None

    def _field_to_healer(self) -> Dict[str, str]:
        """Map field names to healer names."""
        return {
            "email": "email_normalizer",
            "phone": "phone_formatter",
            "name": "name_capitalizer",
            "job_title": "title_standardizer",
            "location": "location_geocoder",
            "program": "program_reassigner",
            "hierarchy_tier": "tier_recalculator",
            "clearance": "clearance_mapper",
            "contract_value": "value_normalizer",
            "linkedin_url": "linkedin_fixer",
        }

    def heal(self, issues: List[DataIssue]) -> List[AutoFixResult]:
        """Process issues and auto-fix where confidence exceeds threshold."""
        now = datetime.now(timezone.utc).isoformat()
        results = []

        for issue in issues:
            if not issue.auto_fixable:
                result = AutoFixResult(
                    issue=issue, status=FixStatus.SKIPPED.value,
                    confidence=0.0, timestamp=now,
                    reason="Not auto-fixable",
                )
                results.append(result)
                self._audit_log.append(result)
                continue

            healer = self._select_healer(issue)
            if not healer or not healer.fix_fn:
                result = AutoFixResult(
                    issue=issue, status=FixStatus.NEEDS_HUMAN.value,
                    confidence=0.0, timestamp=now,
                    reason="No suitable healer found",
                )
                results.append(result)
                self._audit_log.append(result)
                continue

            # If the issue has a suggested_fix, use it directly
            if issue.suggested_fix is not None:
                new_value = issue.suggested_fix
                confidence = healer.confidence
            else:
                # Run the healer
                try:
                    new_value, confidence = healer.fix_fn(issue.current_value)
                except Exception as e:
                    result = AutoFixResult(
                        issue=issue, status=FixStatus.FAILED.value,
                        confidence=0.0, old_value=issue.current_value,
                        healer_used=healer.name, timestamp=now,
                        reason=f"Healer error: {e}",
                    )
                    results.append(result)
                    self._audit_log.append(result)
                    continue

            if new_value is None or confidence < self.confidence_threshold:
                result = AutoFixResult(
                    issue=issue, status=FixStatus.SKIPPED.value,
                    confidence=confidence, old_value=issue.current_value,
                    new_value=new_value, healer_used=healer.name,
                    timestamp=now,
                    reason=f"Confidence {confidence:.2f} below threshold {self.confidence_threshold}",
                )
                results.append(result)
                self._audit_log.append(result)
                continue

            # Apply fix to record if loaded
            self._apply_fix(issue, new_value)

            result = AutoFixResult(
                issue=issue, status=FixStatus.FIXED.value,
                confidence=confidence, old_value=issue.current_value,
                new_value=new_value, healer_used=healer.name,
                timestamp=now, reason="Auto-fixed",
            )

            # Check for cascading fixes
            cascading = self.heal_cascading(result)
            result.cascading_fixes = cascading

            results.append(result)
            self._audit_log.append(result)

        return results

    def heal_cascading(self, fix: AutoFixResult) -> List[AutoFixResult]:
        """Trigger cascading updates when a fix affects downstream fields."""
        cascading = []
        now = datetime.now(timezone.utc).isoformat()
        issue = fix.issue

        # Location change → program reassignment → priority update
        if issue.field_name == "location" and fix.status == FixStatus.FIXED.value:
            program_result = fix_program_from_location(str(fix.new_value))
            if program_result[0] and program_result[1] >= self.confidence_threshold:
                cascade_issue = DataIssue(
                    id=uuid.uuid4().hex[:8], domain=issue.domain,
                    dimension="consistency", record_id=issue.record_id,
                    record_type=issue.record_type, field_name="program",
                    current_value="", expected_pattern=program_result[0],
                    severity="high",
                    description=f"Cascade: location→program reassignment",
                    auto_fixable=True, suggested_fix=program_result[0],
                    detected_at=now,
                )
                cascade_fix = AutoFixResult(
                    issue=cascade_issue, status=FixStatus.FIXED.value,
                    confidence=program_result[1], old_value="",
                    new_value=program_result[0], healer_used="program_reassigner",
                    timestamp=now, reason="Cascading fix from location change",
                )
                self._apply_fix(cascade_issue, program_result[0])
                cascading.append(cascade_fix)
                self._audit_log.append(cascade_fix)

        # Title change → tier recalculation
        if issue.field_name == "job_title" and fix.status == FixStatus.FIXED.value:
            tier_result = fix_tier_from_title(str(fix.new_value))
            if tier_result[0] is not None and tier_result[1] >= self.confidence_threshold:
                cascade_issue = DataIssue(
                    id=uuid.uuid4().hex[:8], domain=issue.domain,
                    dimension="consistency", record_id=issue.record_id,
                    record_type=issue.record_type, field_name="hierarchy_tier",
                    current_value="", expected_pattern=str(tier_result[0]),
                    severity="high",
                    description="Cascade: title→tier recalculation",
                    auto_fixable=True, suggested_fix=tier_result[0],
                    detected_at=now,
                )
                cascade_fix = AutoFixResult(
                    issue=cascade_issue, status=FixStatus.FIXED.value,
                    confidence=tier_result[1], old_value="",
                    new_value=tier_result[0], healer_used="tier_recalculator",
                    timestamp=now, reason="Cascading fix from title change",
                )
                self._apply_fix(cascade_issue, tier_result[0])
                cascading.append(cascade_fix)
                self._audit_log.append(cascade_fix)

        return cascading

    def _apply_fix(self, issue: DataIssue, new_value: Any) -> None:
        """Apply a fix to the in-memory record store."""
        domain = issue.domain
        record_id = issue.record_id
        field_name = issue.field_name

        if domain in self._records and record_id in self._records[domain]:
            record = self._records[domain][record_id]
            record[field_name] = new_value

    def validate_batch(self, records: List[Dict[str, Any]], domain: str) -> List[Dict[str, Any]]:
        """Validate and auto-fix a batch of records before import."""
        results = []
        for record in records:
            record_issues = []
            fixes = []

            # Quick validation per field
            if domain == "contacts":
                email = record.get("email", "")
                if email:
                    fixed, conf = fix_email_normalize(email)
                    if fixed != email and conf >= self.confidence_threshold:
                        record["email"] = fixed
                        fixes.append({"field": "email", "old": email, "new": fixed})

                phone = record.get("phone", "")
                if phone:
                    fixed, conf = fix_phone_format(phone)
                    if fixed != phone and conf >= self.confidence_threshold:
                        record["phone"] = fixed
                        fixes.append({"field": "phone", "old": phone, "new": fixed})

            results.append({
                "record": record,
                "fixes_applied": fixes,
                "fix_count": len(fixes),
            })
        return results


# =========================================
# SINGLETON
# =========================================

_healer: Optional[SelfHealingPipeline] = None


def get_self_healer() -> SelfHealingPipeline:
    global _healer
    if _healer is None:
        _healer = SelfHealingPipeline()
    return _healer
