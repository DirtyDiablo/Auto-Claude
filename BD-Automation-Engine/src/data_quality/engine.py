"""Phase 38A — Autonomous Data Quality Engine

Continuously monitors and scores data health across the platform.
25+ monitors across 4 domains: contacts, programs, jobs, enrichments.
5 quality dimensions: completeness, accuracy, freshness, consistency, validity.
"""

import logging
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# =========================================
# ENUMS
# =========================================

class QualityDimension(str, Enum):
    COMPLETENESS = "completeness"
    ACCURACY = "accuracy"
    FRESHNESS = "freshness"
    CONSISTENCY = "consistency"
    VALIDITY = "validity"


class IssueSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class QualityTrend(str, Enum):
    IMPROVING = "improving"
    STABLE = "stable"
    DEGRADING = "degrading"


class Domain(str, Enum):
    CONTACTS = "contacts"
    PROGRAMS = "programs"
    JOBS = "jobs"
    ENRICHMENTS = "enrichments"


# =========================================
# DATA CLASSES
# =========================================

@dataclass
class DataIssue:
    """A single data quality issue."""
    id: str
    domain: str
    dimension: str
    record_id: str
    record_type: str
    field_name: str
    current_value: Any
    expected_pattern: str
    severity: str
    description: str
    auto_fixable: bool = False
    suggested_fix: Any = None
    detected_at: str = ""
    impact_score: float = 0.0


@dataclass
class DataQualityScore:
    """Quality score for a single dimension."""
    dimension: str
    score: float  # 0-100
    issues: List[DataIssue] = field(default_factory=list)
    auto_fixable: List[DataIssue] = field(default_factory=list)
    checked_at: str = ""
    records_checked: int = 0
    records_failed: int = 0


@dataclass
class RecordQualityScore:
    """Quality score for a single record."""
    record_id: str
    record_type: str
    overall_score: float
    dimension_scores: Dict[str, float] = field(default_factory=dict)
    issues: List[DataIssue] = field(default_factory=list)
    checked_at: str = ""


@dataclass
class DataQualityReport:
    """Full audit report."""
    id: str
    overall_score: float
    domain_scores: Dict[str, float] = field(default_factory=dict)
    dimension_scores: Dict[str, float] = field(default_factory=dict)
    critical_issues: List[DataIssue] = field(default_factory=list)
    all_issues: List[DataIssue] = field(default_factory=list)
    auto_fixable_count: int = 0
    trend: QualityTrend = QualityTrend.STABLE
    recommendations: List[str] = field(default_factory=list)
    records_audited: int = 0
    created_at: str = ""
    duration_seconds: float = 0.0


@dataclass
class DataQualityRule:
    """A single quality rule definition."""
    name: str
    dimension: str
    domain: str
    severity: str
    description: str = ""
    check: Optional[Callable] = None
    auto_fix: Optional[Callable] = None
    impact_score: float = 0.5
    enabled: bool = True


# =========================================
# VALIDATION HELPERS
# =========================================

EMAIL_REGEX = re.compile(
    r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
)

DISPOSABLE_DOMAINS = {
    "mailinator.com", "guerrillamail.com", "tempmail.com",
    "throwaway.email", "yopmail.com", "sharklasers.com",
    "trashmail.com", "10minutemail.com",
}

VALID_CLEARANCE_LEVELS = {
    "none", "public_trust", "secret", "top_secret", "ts_sci",
    "top_secret/sci", "ts/sci", "confidential",
}

# E.164: + followed by 1-15 digits
PHONE_E164_REGEX = re.compile(r'^\+[1-9]\d{1,14}$')

# Common phone patterns
PHONE_LOOSE_REGEX = re.compile(r'[\d\(\)\-\.\s\+]{7,}')

TITLE_TIER_MAP = {
    1: ["ceo", "president", "chief", "cto", "cfo", "cio", "coo", "evp",
        "executive vice president", "managing director"],
    2: ["vice president", "vp", "svp", "senior vice president", "director",
        "senior director", "general manager"],
    3: ["manager", "senior manager", "program manager", "project manager",
        "department head", "section chief"],
    4: ["lead", "senior", "principal", "staff", "architect", "team lead"],
    5: ["analyst", "engineer", "specialist", "developer", "consultant",
        "coordinator", "associate"],
    6: ["intern", "assistant", "junior", "trainee", "entry"],
}

PROGRAM_LOCATION_MAP = {
    "san diego": "AF DCGS - PACAF",
    "la mesa": "AF DCGS - PACAF",
    "langley": "AF DCGS - Langley",
    "hampton": "AF DCGS - Langley",
    "hampton roads": "AF DCGS - Langley",
    "beale": "AF DCGS - Beale",
    "ramstein": "AF DCGS - Ramstein",
    "osan": "AF DCGS - Osan",
}


def validate_email(email: str) -> Tuple[bool, str]:
    """Validate email format."""
    if not email or not isinstance(email, str):
        return False, "Email is empty or not a string"
    email = email.strip().lower()
    if not EMAIL_REGEX.match(email):
        return False, f"Invalid email format: {email}"
    domain = email.split("@")[1]
    if domain in DISPOSABLE_DOMAINS:
        return False, f"Disposable email domain: {domain}"
    return True, "valid"


def validate_phone(phone: str) -> Tuple[bool, str]:
    """Validate phone number."""
    if not phone or not isinstance(phone, str):
        return False, "Phone is empty"
    phone = phone.strip()
    if PHONE_E164_REGEX.match(phone):
        return True, "valid_e164"
    if PHONE_LOOSE_REGEX.match(phone):
        digits = re.sub(r'\D', '', phone)
        if 7 <= len(digits) <= 15:
            return True, "valid_loose"
    return False, f"Invalid phone: {phone}"


def classify_title_tier(title: str) -> int:
    """Classify job title to hierarchy tier (1-6).
    Builds a flat list of (keyword, tier) sorted by keyword length descending
    so longer, more specific phrases match before shorter substrings.
    """
    if not title:
        return 6
    title_lower = title.lower().strip()
    # Build flat list sorted by keyword length (longest first)
    all_keywords: list = []
    for tier, keywords in TITLE_TIER_MAP.items():
        for kw in keywords:
            all_keywords.append((kw, tier))
    all_keywords.sort(key=lambda x: len(x[0]), reverse=True)

    for kw, tier in all_keywords:
        if kw in title_lower:
            return tier
    return 5  # Default to analyst/engineer level


def check_location_program(location: str, program: str) -> Tuple[bool, str]:
    """Check if location matches the expected program assignment."""
    if not location:
        return True, "no_location"
    loc_lower = location.lower().strip()
    for loc_key, expected_program in PROGRAM_LOCATION_MAP.items():
        if loc_key in loc_lower:
            if program and program != expected_program:
                return False, f"Location '{location}' should map to '{expected_program}', got '{program}'"
            return True, "match"
    return True, "unmapped_location"


def compute_freshness_score(last_updated: str, max_days: int = 90) -> float:
    """Compute freshness score (0-100) based on days since update."""
    if not last_updated:
        return 0.0
    try:
        updated = datetime.fromisoformat(last_updated.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        days_old = (now - updated).days
        if days_old <= 0:
            return 100.0
        if days_old >= max_days:
            return 0.0
        return round(100.0 * (1.0 - days_old / max_days), 1)
    except (ValueError, TypeError):
        return 0.0


def detect_duplicates(records: List[Dict[str, Any]], keys: List[str]) -> List[Tuple[int, int, float]]:
    """Detect duplicate records using field-level comparison.
    Returns list of (idx1, idx2, similarity_score) tuples.
    """
    duplicates = []
    for i in range(len(records)):
        for j in range(i + 1, len(records)):
            sim = _record_similarity(records[i], records[j], keys)
            if sim >= 0.85:
                duplicates.append((i, j, sim))
    return duplicates


def _record_similarity(r1: Dict, r2: Dict, keys: List[str]) -> float:
    """Compute similarity between two records across specified keys."""
    if not keys:
        return 0.0
    scores = []
    for key in keys:
        v1 = str(r1.get(key, "")).lower().strip()
        v2 = str(r2.get(key, "")).lower().strip()
        if not v1 and not v2:
            continue
        if v1 == v2:
            scores.append(1.0)
        else:
            # Simple character-level similarity
            longer = max(len(v1), len(v2))
            if longer == 0:
                continue
            common = sum(1 for a, b in zip(v1, v2) if a == b)
            scores.append(common / longer)
    return sum(scores) / len(scores) if scores else 0.0


# =========================================
# DATA QUALITY ENGINE
# =========================================

class DataQualityEngine:
    """Continuously monitors and scores data health across the platform."""

    def __init__(self):
        self._data: Dict[str, List[Dict[str, Any]]] = {
            "contacts": [],
            "programs": [],
            "jobs": [],
            "enrichments": [],
        }
        self._rules: List[DataQualityRule] = self._register_default_rules()
        self._history: List[DataQualityReport] = []
        self._alert_thresholds: Dict[str, float] = {
            "overall": 70.0,
            "contacts": 65.0,
            "programs": 70.0,
            "jobs": 60.0,
        }

    def set_data(self, domain: str, records: List[Dict[str, Any]]) -> None:
        """Load data for a domain."""
        if domain in self._data:
            self._data[domain] = records

    def get_rules(self) -> List[DataQualityRule]:
        """Get all registered quality rules."""
        return [r for r in self._rules if r.enabled]

    def set_rules(self, rules: List[DataQualityRule]) -> None:
        """Replace rules with custom set."""
        self._rules = rules

    def add_rule(self, rule: DataQualityRule) -> None:
        """Add a quality rule."""
        self._rules.append(rule)

    # -----------------------------------------
    # Default rules
    # -----------------------------------------

    def _register_default_rules(self) -> List[DataQualityRule]:
        """Register all default quality rules."""
        rules = []

        # --- Contact rules ---
        rules.append(DataQualityRule(
            name="email_required", dimension="completeness", domain="contacts",
            severity="high", impact_score=0.8,
            description="Contact must have a valid email address",
        ))
        rules.append(DataQualityRule(
            name="email_valid", dimension="validity", domain="contacts",
            severity="high", impact_score=0.8,
            description="Email must match RFC 5322 format and not be disposable",
        ))
        rules.append(DataQualityRule(
            name="phone_valid", dimension="validity", domain="contacts",
            severity="medium", impact_score=0.5,
            description="Phone must be in valid format",
        ))
        rules.append(DataQualityRule(
            name="name_required", dimension="completeness", domain="contacts",
            severity="critical", impact_score=0.9,
            description="Contact must have first name and last name",
        ))
        rules.append(DataQualityRule(
            name="title_tier_consistency", dimension="consistency", domain="contacts",
            severity="critical", impact_score=0.9,
            description="Job title must be consistent with hierarchy tier",
        ))
        rules.append(DataQualityRule(
            name="location_program_consistency", dimension="consistency", domain="contacts",
            severity="critical", impact_score=0.95,
            description="Location must be consistent with assigned program",
        ))
        rules.append(DataQualityRule(
            name="contact_freshness", dimension="freshness", domain="contacts",
            severity="medium", impact_score=0.6,
            description="Contact must have been updated within 90 days",
        ))
        rules.append(DataQualityRule(
            name="contact_dedup", dimension="accuracy", domain="contacts",
            severity="high", impact_score=0.7,
            description="No duplicate contacts based on name+email+company",
        ))

        # --- Program rules ---
        rules.append(DataQualityRule(
            name="contract_not_expired", dimension="freshness", domain="programs",
            severity="high", impact_score=0.85,
            description="Contract end date must not have passed",
        ))
        rules.append(DataQualityRule(
            name="value_range_valid", dimension="validity", domain="programs",
            severity="medium", impact_score=0.6,
            description="Contract value must be within reasonable bounds",
        ))
        rules.append(DataQualityRule(
            name="program_name_required", dimension="completeness", domain="programs",
            severity="critical", impact_score=0.9,
            description="Program must have a name",
        ))
        rules.append(DataQualityRule(
            name="prime_sub_consistent", dimension="consistency", domain="programs",
            severity="high", impact_score=0.75,
            description="Prime/sub relationships must be bidirectionally consistent",
        ))

        # --- Job rules ---
        rules.append(DataQualityRule(
            name="job_title_standard", dimension="accuracy", domain="jobs",
            severity="medium", impact_score=0.5,
            description="Job title should match standardized taxonomy",
        ))
        rules.append(DataQualityRule(
            name="clearance_valid", dimension="validity", domain="jobs",
            severity="high", impact_score=0.7,
            description="Clearance level must be a recognized value",
        ))
        rules.append(DataQualityRule(
            name="job_location_parsed", dimension="completeness", domain="jobs",
            severity="medium", impact_score=0.5,
            description="Job must have a parsed location",
        ))
        rules.append(DataQualityRule(
            name="program_mapped", dimension="completeness", domain="jobs",
            severity="high", impact_score=0.8,
            description="Job must be mapped to a program",
        ))
        rules.append(DataQualityRule(
            name="job_url_present", dimension="completeness", domain="jobs",
            severity="low", impact_score=0.3,
            description="Job posting should have a source URL",
        ))

        # --- Enrichment rules ---
        rules.append(DataQualityRule(
            name="embedding_present", dimension="completeness", domain="enrichments",
            severity="high", impact_score=0.7,
            description="Record should have vector embedding",
        ))
        rules.append(DataQualityRule(
            name="classification_confidence", dimension="accuracy", domain="enrichments",
            severity="medium", impact_score=0.6,
            description="Classification confidence should be above 0.7",
        ))

        return rules

    # -----------------------------------------
    # Audit
    # -----------------------------------------

    def run_full_audit(self) -> DataQualityReport:
        """Run all monitors across all data stores."""
        import time
        start = time.time()
        now = datetime.now(timezone.utc).isoformat()

        all_issues: List[DataIssue] = []
        domain_scores: Dict[str, float] = {}
        dimension_scores: Dict[str, List[float]] = {}
        total_records = 0

        for domain in Domain:
            d_name = domain.value
            records = self._data.get(d_name, [])
            total_records += len(records)
            domain_rules = [r for r in self._rules if r.domain == d_name and r.enabled]

            if not records:
                domain_scores[d_name] = 100.0
                continue

            issues = self._check_domain(d_name, records, domain_rules)
            all_issues.extend(issues)

            # Score = 100 - (weighted issue rate)
            if records:
                issue_rate = len(issues) / (len(records) * max(len(domain_rules), 1))
                domain_scores[d_name] = round(max(0, 100 * (1 - issue_rate)), 1)
            else:
                domain_scores[d_name] = 100.0

            # Aggregate dimension scores
            for rule in domain_rules:
                dim = rule.dimension
                rule_issues = [i for i in issues if i.dimension == dim]
                if records:
                    dim_score = 100 * (1 - len(rule_issues) / len(records))
                else:
                    dim_score = 100.0
                if dim not in dimension_scores:
                    dimension_scores[dim] = []
                dimension_scores[dim].append(dim_score)

        # Average dimension scores
        dim_avg: Dict[str, float] = {}
        for dim, scores in dimension_scores.items():
            dim_avg[dim] = round(sum(scores) / len(scores), 1) if scores else 100.0

        # Overall score
        if domain_scores:
            overall = round(sum(domain_scores.values()) / len(domain_scores), 1)
        else:
            overall = 100.0

        # Determine trend
        trend = self._compute_trend(overall)

        # Critical issues
        critical = [i for i in all_issues if i.severity == "critical"]
        auto_fixable = [i for i in all_issues if i.auto_fixable]

        # Recommendations
        recommendations = self._generate_recommendations(
            domain_scores, dim_avg, all_issues
        )

        duration = time.time() - start

        report = DataQualityReport(
            id=uuid.uuid4().hex[:12],
            overall_score=overall,
            domain_scores=domain_scores,
            dimension_scores=dim_avg,
            critical_issues=critical,
            all_issues=all_issues,
            auto_fixable_count=len(auto_fixable),
            trend=trend,
            recommendations=recommendations,
            records_audited=total_records,
            created_at=now,
            duration_seconds=round(duration, 3),
        )

        self._history.append(report)
        return report

    def score_single_record(self, record_type: str, record: Dict[str, Any]) -> RecordQualityScore:
        """Score a single record across all applicable dimensions."""
        now = datetime.now(timezone.utc).isoformat()
        rules = [r for r in self._rules if r.domain == record_type and r.enabled]
        issues = self._check_single_record(record_type, record, rules)

        dim_scores: Dict[str, float] = {}
        for rule in rules:
            dim = rule.dimension
            dim_issues = [i for i in issues if i.dimension == dim]
            dim_rules = [r for r in rules if r.dimension == dim]
            if dim_rules:
                dim_scores[dim] = round(100 * (1 - len(dim_issues) / len(dim_rules)), 1)

        overall = round(sum(dim_scores.values()) / len(dim_scores), 1) if dim_scores else 100.0

        return RecordQualityScore(
            record_id=record.get("id", "unknown"),
            record_type=record_type,
            overall_score=overall,
            dimension_scores=dim_scores,
            issues=issues,
            checked_at=now,
        )

    def get_health_summary(self) -> Dict[str, Any]:
        """Get current health summary."""
        if not self._history:
            return {"overall_score": 100.0, "status": "no_data", "trend": "stable"}
        latest = self._history[-1]
        return {
            "overall_score": latest.overall_score,
            "domain_scores": latest.domain_scores,
            "dimension_scores": latest.dimension_scores,
            "total_issues": len(latest.all_issues),
            "critical_issues": len(latest.critical_issues),
            "auto_fixable": latest.auto_fixable_count,
            "trend": latest.trend.value,
            "last_audit": latest.created_at,
        }

    def get_issues(
        self,
        domain: Optional[str] = None,
        severity: Optional[str] = None,
        auto_fixable_only: bool = False,
    ) -> List[DataIssue]:
        """Get filtered list of issues from latest audit."""
        if not self._history:
            return []
        issues = self._history[-1].all_issues
        if domain:
            issues = [i for i in issues if i.domain == domain]
        if severity:
            issues = [i for i in issues if i.severity == severity]
        if auto_fixable_only:
            issues = [i for i in issues if i.auto_fixable]
        return issues

    def get_trends(self, periods: int = 10) -> List[Dict[str, Any]]:
        """Get quality score trends over time."""
        recent = self._history[-periods:] if len(self._history) >= periods else self._history
        return [
            {
                "report_id": r.id,
                "overall_score": r.overall_score,
                "domain_scores": r.domain_scores,
                "total_issues": len(r.all_issues),
                "created_at": r.created_at,
            }
            for r in recent
        ]

    def get_history(self) -> List[DataQualityReport]:
        """Get audit history."""
        return self._history

    # -----------------------------------------
    # Domain checks
    # -----------------------------------------

    def _check_domain(
        self, domain: str, records: List[Dict], rules: List[DataQualityRule],
    ) -> List[DataIssue]:
        """Run all rules for a domain against its records."""
        issues = []
        for record in records:
            record_issues = self._check_single_record(domain, record, rules)
            issues.extend(record_issues)
        return issues

    def _check_single_record(
        self, domain: str, record: Dict, rules: List[DataQualityRule],
    ) -> List[DataIssue]:
        """Check a single record against all domain rules."""
        issues = []
        record_id = record.get("id", "unknown")
        now = datetime.now(timezone.utc).isoformat()

        for rule in rules:
            issue = self._evaluate_rule(domain, record, record_id, rule, now)
            if issue:
                issues.append(issue)

        return issues

    def _evaluate_rule(
        self, domain: str, record: Dict, record_id: str,
        rule: DataQualityRule, now: str,
    ) -> Optional[DataIssue]:
        """Evaluate a single rule against a record."""

        # Contact rules
        if domain == "contacts":
            if rule.name == "email_required":
                email = record.get("email", record.get("email_address", ""))
                if not email:
                    return DataIssue(
                        id=uuid.uuid4().hex[:8], domain=domain,
                        dimension=rule.dimension, record_id=record_id,
                        record_type="contact", field_name="email",
                        current_value=email, expected_pattern="non-empty email",
                        severity=rule.severity, description="Missing email address",
                        auto_fixable=True, detected_at=now,
                        impact_score=rule.impact_score,
                    )

            elif rule.name == "email_valid":
                email = record.get("email", record.get("email_address", ""))
                if email:
                    valid, reason = validate_email(email)
                    if not valid:
                        return DataIssue(
                            id=uuid.uuid4().hex[:8], domain=domain,
                            dimension=rule.dimension, record_id=record_id,
                            record_type="contact", field_name="email",
                            current_value=email, expected_pattern="RFC 5322 format",
                            severity=rule.severity, description=reason,
                            auto_fixable=True, suggested_fix=email.strip().lower(),
                            detected_at=now, impact_score=rule.impact_score,
                        )

            elif rule.name == "phone_valid":
                phone = record.get("phone", record.get("phone_number", ""))
                if phone:
                    valid, reason = validate_phone(phone)
                    if not valid:
                        return DataIssue(
                            id=uuid.uuid4().hex[:8], domain=domain,
                            dimension=rule.dimension, record_id=record_id,
                            record_type="contact", field_name="phone",
                            current_value=phone, expected_pattern="E.164 or valid format",
                            severity=rule.severity, description=reason,
                            auto_fixable=True, detected_at=now,
                            impact_score=rule.impact_score,
                        )

            elif rule.name == "name_required":
                first = record.get("first_name", "")
                last = record.get("last_name", "")
                if not first or not last:
                    return DataIssue(
                        id=uuid.uuid4().hex[:8], domain=domain,
                        dimension=rule.dimension, record_id=record_id,
                        record_type="contact", field_name="name",
                        current_value=f"{first} {last}".strip(),
                        expected_pattern="first and last name required",
                        severity=rule.severity, description="Missing first or last name",
                        auto_fixable=False, detected_at=now,
                        impact_score=rule.impact_score,
                    )

            elif rule.name == "title_tier_consistency":
                title = record.get("job_title", record.get("title", ""))
                tier = record.get("hierarchy_tier", record.get("tier"))
                if title and tier is not None:
                    expected = classify_title_tier(title)
                    if int(tier) != expected:
                        return DataIssue(
                            id=uuid.uuid4().hex[:8], domain=domain,
                            dimension=rule.dimension, record_id=record_id,
                            record_type="contact", field_name="hierarchy_tier",
                            current_value=tier, expected_pattern=f"tier {expected}",
                            severity=rule.severity,
                            description=f"Title '{title}' maps to tier {expected}, got {tier}",
                            auto_fixable=True, suggested_fix=expected,
                            detected_at=now, impact_score=rule.impact_score,
                        )

            elif rule.name == "location_program_consistency":
                location = record.get("location", "")
                program = record.get("program", "")
                if location and program:
                    consistent, reason = check_location_program(location, program)
                    if not consistent:
                        expected = reason.split("'")[1] if "'" in reason else ""
                        return DataIssue(
                            id=uuid.uuid4().hex[:8], domain=domain,
                            dimension=rule.dimension, record_id=record_id,
                            record_type="contact", field_name="program",
                            current_value=program, expected_pattern=expected,
                            severity=rule.severity, description=reason,
                            auto_fixable=True, suggested_fix=expected,
                            detected_at=now, impact_score=rule.impact_score,
                        )

            elif rule.name == "contact_freshness":
                updated = record.get("last_updated", record.get("updated_at", ""))
                score = compute_freshness_score(updated, max_days=90)
                if score < 50:
                    return DataIssue(
                        id=uuid.uuid4().hex[:8], domain=domain,
                        dimension=rule.dimension, record_id=record_id,
                        record_type="contact", field_name="last_updated",
                        current_value=updated, expected_pattern="within 90 days",
                        severity=rule.severity,
                        description=f"Contact is stale (freshness score: {score})",
                        auto_fixable=True, detected_at=now,
                        impact_score=rule.impact_score,
                    )

            elif rule.name == "contact_dedup":
                # Dedup is handled at batch level, skip for single record
                pass

        # Program rules
        elif domain == "programs":
            if rule.name == "program_name_required":
                name = record.get("name", record.get("program_name", ""))
                if not name:
                    return DataIssue(
                        id=uuid.uuid4().hex[:8], domain=domain,
                        dimension=rule.dimension, record_id=record_id,
                        record_type="program", field_name="name",
                        current_value="", expected_pattern="non-empty",
                        severity=rule.severity, description="Program name is missing",
                        auto_fixable=False, detected_at=now,
                        impact_score=rule.impact_score,
                    )

            elif rule.name == "contract_not_expired":
                end_date = record.get("pop_end", record.get("contract_end", ""))
                if end_date:
                    try:
                        end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                        if end < datetime.now(timezone.utc):
                            return DataIssue(
                                id=uuid.uuid4().hex[:8], domain=domain,
                                dimension=rule.dimension, record_id=record_id,
                                record_type="program", field_name="contract_end",
                                current_value=end_date,
                                expected_pattern="future date or null",
                                severity=rule.severity,
                                description=f"Contract expired on {end_date}",
                                auto_fixable=True, detected_at=now,
                                impact_score=rule.impact_score,
                            )
                    except (ValueError, TypeError):
                        pass

            elif rule.name == "value_range_valid":
                value = record.get("contract_value", record.get("value", 0))
                if isinstance(value, (int, float)):
                    if value < 0 or value > 100_000_000_000:  # > 100B seems wrong
                        return DataIssue(
                            id=uuid.uuid4().hex[:8], domain=domain,
                            dimension=rule.dimension, record_id=record_id,
                            record_type="program", field_name="contract_value",
                            current_value=value,
                            expected_pattern="0 to 100B",
                            severity=rule.severity,
                            description=f"Contract value {value} outside valid range",
                            auto_fixable=False, detected_at=now,
                            impact_score=rule.impact_score,
                        )

            elif rule.name == "prime_sub_consistent":
                prime = record.get("prime_contractor", "")
                is_prime = record.get("is_prime", None)
                if is_prime is True and not prime:
                    return DataIssue(
                        id=uuid.uuid4().hex[:8], domain=domain,
                        dimension=rule.dimension, record_id=record_id,
                        record_type="program", field_name="prime_contractor",
                        current_value="", expected_pattern="non-empty when is_prime=True",
                        severity=rule.severity,
                        description="Prime contractor name missing for prime contract",
                        auto_fixable=False, detected_at=now,
                        impact_score=rule.impact_score,
                    )

        # Job rules
        elif domain == "jobs":
            if rule.name == "clearance_valid":
                clearance = record.get("clearance", record.get("clearance_level", ""))
                if clearance:
                    cl = clearance.lower().strip().replace(" ", "_")
                    if cl not in VALID_CLEARANCE_LEVELS:
                        return DataIssue(
                            id=uuid.uuid4().hex[:8], domain=domain,
                            dimension=rule.dimension, record_id=record_id,
                            record_type="job", field_name="clearance",
                            current_value=clearance,
                            expected_pattern=f"one of {VALID_CLEARANCE_LEVELS}",
                            severity=rule.severity,
                            description=f"Unrecognized clearance: {clearance}",
                            auto_fixable=True, detected_at=now,
                            impact_score=rule.impact_score,
                        )

            elif rule.name == "program_mapped":
                program = record.get("program", "")
                if not program:
                    return DataIssue(
                        id=uuid.uuid4().hex[:8], domain=domain,
                        dimension=rule.dimension, record_id=record_id,
                        record_type="job", field_name="program",
                        current_value="", expected_pattern="non-empty program",
                        severity=rule.severity,
                        description="Job not mapped to a program",
                        auto_fixable=True, detected_at=now,
                        impact_score=rule.impact_score,
                    )

            elif rule.name == "job_location_parsed":
                location = record.get("location", "")
                if not location:
                    return DataIssue(
                        id=uuid.uuid4().hex[:8], domain=domain,
                        dimension=rule.dimension, record_id=record_id,
                        record_type="job", field_name="location",
                        current_value="", expected_pattern="non-empty",
                        severity=rule.severity,
                        description="Job location not parsed",
                        auto_fixable=True, detected_at=now,
                        impact_score=rule.impact_score,
                    )

            elif rule.name == "job_title_standard":
                title = record.get("title", record.get("job_title", ""))
                if not title:
                    return DataIssue(
                        id=uuid.uuid4().hex[:8], domain=domain,
                        dimension=rule.dimension, record_id=record_id,
                        record_type="job", field_name="title",
                        current_value="", expected_pattern="non-empty standardized title",
                        severity=rule.severity,
                        description="Job title missing",
                        auto_fixable=False, detected_at=now,
                        impact_score=rule.impact_score,
                    )

            elif rule.name == "job_url_present":
                url = record.get("url", record.get("source_url", ""))
                if not url:
                    return DataIssue(
                        id=uuid.uuid4().hex[:8], domain=domain,
                        dimension=rule.dimension, record_id=record_id,
                        record_type="job", field_name="url",
                        current_value="", expected_pattern="non-empty URL",
                        severity=rule.severity,
                        description="Job source URL missing",
                        auto_fixable=False, detected_at=now,
                        impact_score=rule.impact_score,
                    )

        # Enrichment rules
        elif domain == "enrichments":
            if rule.name == "embedding_present":
                embedding = record.get("embedding", record.get("vector"))
                if not embedding:
                    return DataIssue(
                        id=uuid.uuid4().hex[:8], domain=domain,
                        dimension=rule.dimension, record_id=record_id,
                        record_type="enrichment", field_name="embedding",
                        current_value=None, expected_pattern="non-null vector",
                        severity=rule.severity,
                        description="Vector embedding missing",
                        auto_fixable=True, detected_at=now,
                        impact_score=rule.impact_score,
                    )

            elif rule.name == "classification_confidence":
                confidence = record.get("confidence", 1.0)
                if isinstance(confidence, (int, float)) and confidence < 0.7:
                    return DataIssue(
                        id=uuid.uuid4().hex[:8], domain=domain,
                        dimension=rule.dimension, record_id=record_id,
                        record_type="enrichment", field_name="confidence",
                        current_value=confidence,
                        expected_pattern=">= 0.7",
                        severity=rule.severity,
                        description=f"Low classification confidence: {confidence}",
                        auto_fixable=True, detected_at=now,
                        impact_score=rule.impact_score,
                    )

        return None

    # -----------------------------------------
    # Helpers
    # -----------------------------------------

    def _compute_trend(self, current_score: float) -> QualityTrend:
        """Compute trend based on recent history."""
        if len(self._history) < 2:
            return QualityTrend.STABLE
        prev = self._history[-1].overall_score
        diff = current_score - prev
        if diff > 2:
            return QualityTrend.IMPROVING
        elif diff < -2:
            return QualityTrend.DEGRADING
        return QualityTrend.STABLE

    def _generate_recommendations(
        self,
        domain_scores: Dict[str, float],
        dim_scores: Dict[str, float],
        issues: List[DataIssue],
    ) -> List[str]:
        """Generate actionable recommendations."""
        recs = []
        for domain, score in domain_scores.items():
            if score < 60:
                recs.append(f"Critical: {domain} quality is {score}/100 — immediate attention needed")
            elif score < 80:
                recs.append(f"Warning: {domain} quality is {score}/100 — review open issues")

        auto_fixable = [i for i in issues if i.auto_fixable]
        if auto_fixable:
            recs.append(f"{len(auto_fixable)} issues can be auto-fixed — run self-healing pipeline")

        critical = [i for i in issues if i.severity == "critical"]
        if critical:
            recs.append(f"{len(critical)} critical issues detected — prioritize these first")

        if not recs:
            recs.append("Data quality is healthy — continue monitoring")

        return recs


# =========================================
# SINGLETON
# =========================================

_engine: Optional[DataQualityEngine] = None


def get_quality_engine() -> DataQualityEngine:
    global _engine
    if _engine is None:
        _engine = DataQualityEngine()
    return _engine
