"""
Quality Assurance & Feedback Loop Engine - QA gating, human review queues, and feedback collection.

Enhanced with Superpowers Systematic Debugging pattern:
- Root cause analysis before flagging issues
- Issue type classification (low_confidence, missing_data, invalid_mapping, data_quality)
- Severity levels (low, medium, high, critical)
- Recommended fixes and auto-fixable detection
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class QAStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    NEEDS_REVIEW = "needs_review"
    REJECTED = "rejected"


@dataclass
class QAConfig:
    auto_approve_threshold: float = 0.70
    review_threshold: float = 0.50
    batch_size: int = 10


@dataclass
class RootCause:
    """Root cause analysis for QA issues - Systematic Debugging pattern."""

    issue_type: (
        str  # 'low_confidence', 'missing_data', 'invalid_mapping', 'data_quality'
    )
    severity: str  # 'low', 'medium', 'high', 'critical'
    description: str
    affected_fields: List[str]
    recommended_fix: str
    auto_fixable: bool = False


@dataclass
class QAResult:
    job_id: str
    status: QAStatus
    confidence: float
    review_reasons: List[str] = field(default_factory=list)
    original_program: str = ""
    root_cause: Optional[RootCause] = None


@dataclass
class BatchQAReport:
    batch_id: str
    total_items: int
    auto_approved: int
    needs_review: int
    rejected: int
    avg_confidence: float
    timestamp: str
    items: List[QAResult] = field(default_factory=list)


def analyze_root_cause(job: Dict[str, Any]) -> Optional[RootCause]:
    """
    Analyze root cause of QA failure using Systematic Debugging pattern.

    Steps:
    1. Check for invalid mapping (CRITICAL - no program match)
    2. Check for low confidence mapping
    3. Check for missing required data
    4. Assess data quality for moderate confidence
    5. Return None if no issues (should auto-approve)
    """
    mapping = job.get("_mapping", {})
    confidence = mapping.get("match_confidence", 0.0)
    program = mapping.get("program_name", "")

    # Issue 1: Invalid program mapping (CRITICAL severity) - Check first!
    if program in ["Unmatched", "Unknown", "", None]:
        return RootCause(
            issue_type="invalid_mapping",
            severity="critical",
            description="No valid program match found",
            affected_fields=["_mapping.program_name"],
            recommended_fix="Re-run program mapper with expanded search criteria",
            auto_fixable=True,
        )

    # Issue 2: Low confidence mapping (HIGH severity)
    if confidence < 0.50:
        return RootCause(
            issue_type="low_confidence",
            severity="high",
            description=f"Mapping confidence {confidence:.1%} below threshold (50%)",
            affected_fields=["_mapping.match_confidence", "_mapping.program_name"],
            recommended_fix="Manual review required - verify program match signals",
            auto_fixable=False,
        )

    # Issue 3: Missing critical data (MEDIUM severity)
    missing_fields = []
    if not job.get("Security Clearance"):
        missing_fields.append("Security Clearance")
    if not job.get("Location"):
        missing_fields.append("Location")
    if not job.get("Prime Contractor"):
        missing_fields.append("Prime Contractor")

    if missing_fields:
        return RootCause(
            issue_type="missing_data",
            severity="medium",
            description=f"Missing required fields: {', '.join(missing_fields)}",
            affected_fields=missing_fields,
            recommended_fix="Data enrichment - fetch from source or request manual input",
            auto_fixable=True,  # Can be auto-fixed via re-scraping
        )

    # Issue 4: Data quality - moderate confidence (LOW severity)
    if 0.50 <= confidence < 0.70:
        return RootCause(
            issue_type="data_quality",
            severity="low",
            description=f"Moderate confidence {confidence:.1%} - verification recommended",
            affected_fields=["_mapping"],
            recommended_fix="Quick review - validate program match makes sense",
            auto_fixable=False,
        )

    return None  # No root cause identified (should auto-approve)


def debug_qa_failure(job: Dict[str, Any]) -> Dict[str, Any]:
    """
    Systematic debugging report for QA failure.

    Returns structured debug information following Systematic Debugging pattern.
    """
    debug_report = {
        "job_id": (
            job.get("Source URL", "") or job.get("Job Title/Position", "unknown")
        )[:100],
        "failure_reason": "",
        "data_quality_check": {},
        "suggested_actions": [],
        "root_cause": None,
    }

    # Step 1: Identify root cause
    root_cause = analyze_root_cause(job)
    if root_cause:
        debug_report["root_cause"] = {
            "type": root_cause.issue_type,
            "severity": root_cause.severity,
            "description": root_cause.description,
            "affected_fields": root_cause.affected_fields,
            "auto_fixable": root_cause.auto_fixable,
        }
        debug_report["failure_reason"] = root_cause.description

    # Step 2: Data quality checks
    mapping = job.get("_mapping", {})
    debug_report["data_quality_check"] = {
        "has_mapping": bool(mapping),
        "confidence": mapping.get("match_confidence", 0.0),
        "program_identified": bool(mapping.get("program_name")),
        "required_fields_present": {
            "clearance": bool(job.get("Security Clearance")),
            "location": bool(job.get("Location")),
            "prime_contractor": bool(job.get("Prime Contractor")),
            "job_title": bool(job.get("Job Title/Position")),
        },
    }

    # Step 3: Suggested actions
    if root_cause:
        debug_report["suggested_actions"].append(root_cause.recommended_fix)

        if root_cause.auto_fixable:
            debug_report["suggested_actions"].append(
                "AUTO-FIX: Can be resolved programmatically"
            )
        else:
            debug_report["suggested_actions"].append("MANUAL: Requires human review")

    return debug_report


def evaluate_item(job, config=None):
    if config is None:
        config = QAConfig()
    mapping = job.get("_mapping", {})
    confidence = mapping.get("match_confidence", 0.5)
    program = mapping.get("program_name", "Unmatched")
    clearance = job.get("Security Clearance", "")
    job_id = job.get("Source URL", "") or job.get("Job Title/Position", str(id(job)))
    review_reasons = []
    root_cause = None

    if confidence >= config.auto_approve_threshold:
        status = QAStatus.APPROVED
    elif confidence >= config.review_threshold:
        status = QAStatus.NEEDS_REVIEW
        review_reasons.append(f"Confidence {confidence:.0%} below threshold")
        root_cause = analyze_root_cause(job)  # Systematic debugging
    else:
        status = QAStatus.NEEDS_REVIEW
        review_reasons.append(f"Low confidence {confidence:.0%}")
        root_cause = analyze_root_cause(job)  # Systematic debugging

    if "TS/SCI" in clearance.upper():
        if status == QAStatus.APPROVED:
            status = QAStatus.NEEDS_REVIEW
        review_reasons.append("High clearance requires verification")

    if program == "Unmatched":
        status = QAStatus.NEEDS_REVIEW
        review_reasons.append("No program match found")
        if not root_cause:  # Only analyze if not already done
            root_cause = analyze_root_cause(job)

    return QAResult(
        job_id=job_id[:100],
        status=status,
        confidence=confidence,
        review_reasons=review_reasons,
        original_program=program,
        root_cause=root_cause,
    )


def evaluate_batch(jobs, config=None, batch_id=None):
    if config is None:
        config = QAConfig()
    if batch_id is None:
        batch_id = datetime.now().strftime("BATCH_%Y%m%d_%H%M%S")
    results = []
    total_conf = 0.0
    for job in jobs:
        result = evaluate_item(job, config)
        results.append(result)
        total_conf += result.confidence
    auto_approved = sum(1 for r in results if r.status == QAStatus.APPROVED)
    needs_review = sum(1 for r in results if r.status == QAStatus.NEEDS_REVIEW)
    rejected = sum(1 for r in results if r.status == QAStatus.REJECTED)
    avg_conf = total_conf / len(results) if results else 0.0
    return BatchQAReport(
        batch_id=batch_id,
        total_items=len(results),
        auto_approved=auto_approved,
        needs_review=needs_review,
        rejected=rejected,
        avg_confidence=avg_conf,
        timestamp=datetime.now().isoformat(),
        items=results,
    )


class ReviewQueue:
    def __init__(self, queue_file=None):
        if queue_file is None:
            queue_file = Path(__file__).parent.parent / "data" / "review_queue.json"
        self.queue_file = Path(queue_file)
        self.items = []
        self._load()

    def _load(self):
        if self.queue_file.exists():
            with open(self.queue_file, "r") as f:
                self.items = json.load(f)

    def _save(self):
        self.queue_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.queue_file, "w") as f:
            json.dump(self.items, f, indent=2, default=str)

    def add(self, job, qa_result):
        item = {
            "job_id": qa_result.job_id,
            "added_at": datetime.now().isoformat(),
            "status": qa_result.status.value,
            "confidence": qa_result.confidence,
            "review_reasons": qa_result.review_reasons,
            "original_program": qa_result.original_program,
            "reviewed": False,
            "root_cause": {
                "type": qa_result.root_cause.issue_type,
                "severity": qa_result.root_cause.severity,
                "description": qa_result.root_cause.description,
                "recommended_fix": qa_result.root_cause.recommended_fix,
                "auto_fixable": qa_result.root_cause.auto_fixable,
            }
            if qa_result.root_cause
            else None,
        }
        self.items.append(item)
        self._save()

    def get_pending(self):
        return [i for i in self.items if not i.get("reviewed", False)]

    def get_stats(self):
        total = len(self.items)
        pending = len(self.get_pending())
        approved = sum(1 for i in self.items if i.get("status") == "approved")
        rejected = sum(1 for i in self.items if i.get("status") == "rejected")
        by_root_cause = {}
        for item in self.items:
            rc = item.get("root_cause")
            if rc and isinstance(rc, dict):
                rc_type = rc.get("type", "unknown")
                by_root_cause[rc_type] = by_root_cause.get(rc_type, 0) + 1
        return {
            "total": total,
            "pending": pending,
            "reviewed": total - pending,
            "approved": approved,
            "rejected": rejected,
            "by_root_cause": by_root_cause,
        }

    def get_item(self, job_id: str) -> Optional[Dict]:
        """Get a single item by job_id."""
        for item in self.items:
            if item.get("job_id") == job_id:
                return item
        return None

    def _add_audit_entry(self, item: Dict, action: str, reviewer: str, details: str = "") -> None:
        """Append an audit log entry to an item."""
        if "audit_log" not in item:
            item["audit_log"] = []
        item["audit_log"].append({
            "action": action,
            "reviewer": reviewer,
            "timestamp": datetime.now().isoformat(),
            "details": details,
        })

    def approve(self, job_id: str, reviewer: str = "system") -> bool:
        """Mark an item as approved."""
        item = self.get_item(job_id)
        if item is None:
            return False
        item["status"] = "approved"
        item["reviewed"] = True
        item["reviewed_at"] = datetime.now().isoformat()
        self._add_audit_entry(item, "approved", reviewer)
        self._save()
        return True

    def reject(self, job_id: str, reviewer: str, reason: str = "") -> bool:
        """Mark an item as rejected with a reason."""
        item = self.get_item(job_id)
        if item is None:
            return False
        item["status"] = "rejected"
        item["reviewed"] = True
        item["reviewed_at"] = datetime.now().isoformat()
        item["rejection_reason"] = reason
        self._add_audit_entry(item, "rejected", reviewer, details=reason)
        self._save()
        return True

    def reclassify(self, job_id: str, new_program: str, reviewer: str) -> bool:
        """Change the program mapping for an item."""
        item = self.get_item(job_id)
        if item is None:
            return False
        old_program = item.get("original_program", "")
        item["original_program"] = new_program
        item["reviewed"] = True
        item["reviewed_at"] = datetime.now().isoformat()
        item["status"] = "approved"
        self._add_audit_entry(
            item, "reclassified", reviewer,
            details=f"Changed program from '{old_program}' to '{new_program}'",
        )
        self._save()
        return True

    def bulk_approve(self, job_ids: List[str], reviewer: str) -> Dict:
        """Approve multiple items. Returns success/failure counts."""
        success = 0
        failed = 0
        for job_id in job_ids:
            if self.approve(job_id, reviewer):
                success += 1
            else:
                failed += 1
        return {"success": success, "failed": failed}

    def bulk_reject(self, job_ids: List[str], reviewer: str, reason: str = "") -> Dict:
        """Reject multiple items. Returns success/failure counts."""
        success = 0
        failed = 0
        for job_id in job_ids:
            if self.reject(job_id, reviewer, reason):
                success += 1
            else:
                failed += 1
        return {"success": success, "failed": failed}

    def get_review_history(self) -> List[Dict]:
        """Return all reviewed items with timestamps."""
        return [i for i in self.items if i.get("reviewed", False)]


def run_qa_workflow(jobs, config=None, auto_queue=True):
    if config is None:
        config = QAConfig()
    report = evaluate_batch(jobs, config)
    approved_jobs, review_jobs = [], []
    queue = ReviewQueue() if auto_queue else None
    for i, result in enumerate(report.items):
        job = jobs[i]
        if result.status == QAStatus.APPROVED:
            approved_jobs.append(job)
        else:
            review_jobs.append(job)
            if queue:
                queue.add(job, result)
    return report, approved_jobs, review_jobs


def generate_qa_summary_report(report: BatchQAReport, output_dir: str = None) -> str:
    """
    Generate QA summary report with root cause analysis.

    Follows Verification-Before-Completion pattern - creates evidence of QA results.
    """
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "outputs"

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Aggregate root causes
    root_causes_by_type = {}
    root_causes_by_severity = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    auto_fixable_count = 0

    for item in report.items:
        if item.root_cause:
            # By type
            rtype = item.root_cause.issue_type
            root_causes_by_type[rtype] = root_causes_by_type.get(rtype, 0) + 1

            # By severity
            sev = item.root_cause.severity
            if sev in root_causes_by_severity:
                root_causes_by_severity[sev] += 1

            # Auto-fixable
            if item.root_cause.auto_fixable:
                auto_fixable_count += 1

    # Generate markdown report
    report_lines = [
        f"# QA Summary Report - {report.batch_id}",
        f"Generated: {report.timestamp}",
        "",
        "## Overall Statistics",
        f"- **Total Items:** {report.total_items}",
        f"- **Auto-Approved:** {report.auto_approved} ({report.auto_approved / report.total_items * 100:.1f}%)"
        if report.total_items > 0
        else "- **Auto-Approved:** 0",
        f"- **Needs Review:** {report.needs_review} ({report.needs_review / report.total_items * 100:.1f}%)"
        if report.total_items > 0
        else "- **Needs Review:** 0",
        f"- **Average Confidence:** {report.avg_confidence:.1%}",
        "",
        "## Root Cause Analysis",
        f"- **Auto-Fixable Issues:** {auto_fixable_count}/{report.needs_review}",
        f"- **Manual Review Required:** {report.needs_review - auto_fixable_count}",
        "",
        "### Issues by Type",
    ]

    for issue_type, count in sorted(
        root_causes_by_type.items(), key=lambda x: x[1], reverse=True
    ):
        report_lines.append(f"- **{issue_type}:** {count} items")

    if not root_causes_by_type:
        report_lines.append("- No root causes identified (all items approved)")

    report_lines.extend(
        [
            "",
            "### Issues by Severity",
        ]
    )
    for sev in ["critical", "high", "medium", "low"]:
        count = root_causes_by_severity.get(sev, 0)
        if count > 0:
            report_lines.append(f"- **{sev.upper()}:** {count} items")

    # Detailed items requiring review
    review_items = [
        item
        for item in report.items
        if item.status == QAStatus.NEEDS_REVIEW and item.root_cause
    ]
    if review_items:
        report_lines.extend(
            [
                "",
                "## Items Requiring Review",
                "",
                "| Job ID | Issue Type | Severity | Recommended Fix |",
                "|--------|-----------|----------|-----------------|",
            ]
        )

        # Sort by severity (critical first)
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        review_items.sort(
            key=lambda x: (
                severity_order.get(x.root_cause.severity, 4) if x.root_cause else 4
            )
        )

        for item in review_items[:50]:  # Limit to 50 items
            rc = item.root_cause
            job_id_short = (
                item.job_id[:40] + "..." if len(item.job_id) > 40 else item.job_id
            )
            fix_short = (
                rc.recommended_fix[:60] + "..."
                if len(rc.recommended_fix) > 60
                else rc.recommended_fix
            )
            report_lines.append(
                f"| {job_id_short} | {rc.issue_type} | {rc.severity} | {fix_short} |"
            )

    # Summary recommendations
    report_lines.extend(["", "## Recommended Actions", ""])

    if root_causes_by_severity.get("critical", 0) > 0:
        report_lines.append(
            f"1. **CRITICAL:** Address {root_causes_by_severity['critical']} critical issues immediately (invalid program mappings)"
        )

    if auto_fixable_count > 0:
        report_lines.append(
            f"2. **AUTO-FIX:** {auto_fixable_count} issues can be resolved by re-running the pipeline with expanded criteria"
        )

    manual_count = report.needs_review - auto_fixable_count
    if manual_count > 0:
        report_lines.append(
            f"3. **MANUAL REVIEW:** {manual_count} items require human verification"
        )

    report_lines.extend(
        [
            "",
            "---",
            f"*Report generated by BD-Automation-Engine QA Module (Superpowers Systematic Debugging Pattern)*",
        ]
    )

    # Save report
    report_path = output_dir / f"qa_report_{report.batch_id}.md"
    report_content = "\n".join(report_lines)

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    print(f"\nQA Report saved: {report_path}")
    return str(report_path)
