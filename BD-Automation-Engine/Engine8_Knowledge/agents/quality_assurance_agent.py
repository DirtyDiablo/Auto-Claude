"""
Quality Assurance Agent - Validates data quality across all collections.

Part of the 8-agent CrewAI system for BD Intelligence.
"""

import hashlib
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger(__name__)

# Import base agent
try:
    from .base_agent import BDAgent, AgentResponse
except ImportError:
    from base_agent import BDAgent, AgentResponse


@dataclass
class QualityIssue:
    """A data quality issue."""
    issue_type: str  # "duplicate", "missing_field", "stale", "invalid", "low_confidence"
    severity: str  # "critical", "high", "medium", "low"
    record_id: str
    collection: str
    field: Optional[str]
    description: str
    suggested_action: str


@dataclass
class QualityReport:
    """Quality assessment report for a collection."""
    collection: str
    total_records: int
    issues: List[QualityIssue]
    completeness_score: float  # 0-1
    freshness_score: float  # 0-1
    accuracy_score: float  # 0-1
    overall_score: float  # 0-1
    recommendations: List[str]


class QualityAssuranceAgent(BDAgent):
    """
    Agent that validates data quality across all collections.

    Responsibilities:
    - Detect duplicates
    - Identify missing required fields
    - Flag stale/outdated records
    - Validate data formats
    - Track data confidence scores
    """

    # Required fields by collection type
    REQUIRED_FIELDS = {
        "contacts": ["first_name", "last_name", "company"],
        "programs": ["program_name"],
        "jobs": ["title", "company"],
        "activities": ["activity_type", "summary"],
    }

    # Fields to use for duplicate detection
    DEDUP_FIELDS = {
        "contacts": ["first_name", "last_name", "company", "email"],
        "programs": ["program_name", "acronym"],
        "jobs": ["title", "company", "url"],
    }

    # Stale threshold in days
    STALE_THRESHOLDS = {
        "contacts": 180,  # 6 months
        "programs": 365,  # 1 year
        "jobs": 30,  # 30 days
        "activities": 90,  # 3 months
    }

    def __init__(self):
        super().__init__(
            name="Quality Assurance Agent",
            description="Ensure data accuracy, completeness, and freshness across all collections. "
                       "Expert in data quality validation and duplicate detection."
        )
        self._content_hashes: Dict[str, Set[str]] = {}

    def _get_content_hash(self, record: Dict, fields: List[str]) -> str:
        """Generate hash for duplicate detection."""
        values = [str(record.get(f, "")).lower().strip() for f in fields]
        content = "|".join(values)
        return hashlib.md5(content.encode()).hexdigest()

    def check_completeness(
        self,
        records: List[Dict],
        collection_type: str,
    ) -> List[QualityIssue]:
        """Check for missing required fields."""
        issues = []
        required = self.REQUIRED_FIELDS.get(collection_type, [])

        for record in records:
            record_id = record.get("id", "unknown")
            for field in required:
                value = record.get(field)
                if value is None or (isinstance(value, str) and not value.strip()):
                    issues.append(QualityIssue(
                        issue_type="missing_field",
                        severity="high" if field in ["first_name", "last_name", "title"] else "medium",
                        record_id=record_id,
                        collection=collection_type,
                        field=field,
                        description=f"Missing required field: {field}",
                        suggested_action=f"Add {field} to record",
                    ))

        return issues

    def check_duplicates(
        self,
        records: List[Dict],
        collection_type: str,
    ) -> List[QualityIssue]:
        """Check for duplicate records."""
        issues = []
        dedup_fields = self.DEDUP_FIELDS.get(collection_type, ["id"])
        seen_hashes: Dict[str, str] = {}  # hash -> first record id

        for record in records:
            record_id = record.get("id", "unknown")
            content_hash = self._get_content_hash(record, dedup_fields)

            if content_hash in seen_hashes:
                issues.append(QualityIssue(
                    issue_type="duplicate",
                    severity="medium",
                    record_id=record_id,
                    collection=collection_type,
                    field=None,
                    description=f"Duplicate of record {seen_hashes[content_hash]}",
                    suggested_action="Merge or delete duplicate record",
                ))
            else:
                seen_hashes[content_hash] = record_id

        return issues

    def check_freshness(
        self,
        records: List[Dict],
        collection_type: str,
    ) -> List[QualityIssue]:
        """Check for stale/outdated records."""
        issues = []
        threshold_days = self.STALE_THRESHOLDS.get(collection_type, 90)
        cutoff = datetime.utcnow() - timedelta(days=threshold_days)

        for record in records:
            record_id = record.get("id", "unknown")
            updated_at = record.get("updated_at") or record.get("synced_at")

            if updated_at:
                try:
                    if isinstance(updated_at, str):
                        # Try parsing ISO format
                        updated = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                    else:
                        updated = updated_at

                    if updated.replace(tzinfo=None) < cutoff:
                        issues.append(QualityIssue(
                            issue_type="stale",
                            severity="low",
                            record_id=record_id,
                            collection=collection_type,
                            field="updated_at",
                            description=f"Record not updated in {threshold_days}+ days",
                            suggested_action="Review and refresh data",
                        ))
                except (ValueError, TypeError):
                    pass

        return issues

    def check_confidence(
        self,
        records: List[Dict],
        collection_type: str,
        threshold: float = 0.5,
    ) -> List[QualityIssue]:
        """Check for low-confidence records."""
        issues = []

        for record in records:
            record_id = record.get("id", "unknown")
            confidence = record.get("confidence_score") or record.get("match_confidence")

            if confidence is not None and confidence < threshold:
                issues.append(QualityIssue(
                    issue_type="low_confidence",
                    severity="medium" if confidence < 0.3 else "low",
                    record_id=record_id,
                    collection=collection_type,
                    field="confidence_score",
                    description=f"Low confidence score: {confidence:.2f}",
                    suggested_action="Manual review and validation required",
                ))

        return issues

    def assess_quality(
        self,
        records: List[Dict],
        collection_type: str,
    ) -> QualityReport:
        """
        Perform comprehensive quality assessment.

        Returns:
            QualityReport with scores and issues
        """
        all_issues = []

        # Run all checks
        all_issues.extend(self.check_completeness(records, collection_type))
        all_issues.extend(self.check_duplicates(records, collection_type))
        all_issues.extend(self.check_freshness(records, collection_type))
        all_issues.extend(self.check_confidence(records, collection_type))

        # Calculate scores
        total = len(records) or 1

        # Completeness: % of records without missing fields
        missing_issues = [i for i in all_issues if i.issue_type == "missing_field"]
        completeness = 1 - (len(set(i.record_id for i in missing_issues)) / total)

        # Freshness: % of records that are not stale
        stale_issues = [i for i in all_issues if i.issue_type == "stale"]
        freshness = 1 - (len(stale_issues) / total)

        # Accuracy: % without duplicates or low confidence
        accuracy_issues = [i for i in all_issues if i.issue_type in ["duplicate", "low_confidence"]]
        accuracy = 1 - (len(accuracy_issues) / total)

        # Overall score
        overall = (completeness * 0.4 + freshness * 0.3 + accuracy * 0.3)

        # Generate recommendations
        recommendations = []
        if completeness < 0.9:
            recommendations.append(f"Fill in missing fields for {len(set(i.record_id for i in missing_issues))} records")
        if freshness < 0.8:
            recommendations.append(f"Refresh {len(stale_issues)} stale records")
        if accuracy < 0.95:
            dup_count = len([i for i in all_issues if i.issue_type == "duplicate"])
            if dup_count > 0:
                recommendations.append(f"Deduplicate {dup_count} records")

        return QualityReport(
            collection=collection_type,
            total_records=total,
            issues=all_issues,
            completeness_score=completeness,
            freshness_score=freshness,
            accuracy_score=accuracy,
            overall_score=overall,
            recommendations=recommendations,
        )

    async def process(self, query: str, context: Optional[Dict] = None) -> AgentResponse:
        """Process a quality assessment request."""
        if context and "records" in context:
            collection_type = context.get("collection_type", "contacts")
            report = self.assess_quality(context["records"], collection_type)

            return AgentResponse(
                success=True,
                content=(
                    f"Quality Report for {report.collection}:\n"
                    f"- Total records: {report.total_records}\n"
                    f"- Issues found: {len(report.issues)}\n"
                    f"- Completeness: {report.completeness_score:.0%}\n"
                    f"- Freshness: {report.freshness_score:.0%}\n"
                    f"- Accuracy: {report.accuracy_score:.0%}\n"
                    f"- Overall Score: {report.overall_score:.0%}\n"
                    f"- Recommendations: {', '.join(report.recommendations) or 'None'}"
                ),
                sources=[],
                confidence=0.95,
                agent_name=self.name,
                metadata={
                    "report": {
                        "collection": report.collection,
                        "total_records": report.total_records,
                        "issues_count": len(report.issues),
                        "completeness_score": report.completeness_score,
                        "freshness_score": report.freshness_score,
                        "accuracy_score": report.accuracy_score,
                        "overall_score": report.overall_score,
                        "recommendations": report.recommendations,
                    },
                    "issues": [
                        {
                            "type": i.issue_type,
                            "severity": i.severity,
                            "record_id": i.record_id,
                            "description": i.description,
                        }
                        for i in report.issues[:50]  # Limit to first 50
                    ],
                },
            )

        return AgentResponse(
            success=True,
            content=f"QA agent ready. Provide records to validate: {query}",
            sources=[],
            confidence=1.0,
            agent_name=self.name,
            metadata={"status": "ready"},
        )


# CLI test
if __name__ == "__main__":
    import asyncio

    agent = QualityAssuranceAgent()

    # Test with sample records
    test_records = [
        {"id": "1", "first_name": "John", "last_name": "Smith", "company": "GDIT"},
        {"id": "2", "first_name": "Jane", "last_name": "", "company": "Leidos"},  # Missing last_name
        {"id": "3", "first_name": "John", "last_name": "Smith", "company": "GDIT"},  # Duplicate
        {"id": "4", "first_name": "Bob", "last_name": "Jones", "company": "SAIC", "confidence_score": 0.3},
    ]

    async def test():
        result = await agent.process(
            "Check quality",
            context={"records": test_records, "collection_type": "contacts"}
        )
        logger.info("quality_report_generated", content=result.content)

    asyncio.run(test())
