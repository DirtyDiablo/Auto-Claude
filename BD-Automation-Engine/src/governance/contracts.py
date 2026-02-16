"""Phase 43A — Data Contracts Engine

Formal contracts between data producers and consumers.
Versioned, auditable, machine-enforceable with breach detection.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# =========================================
# ENUMS
# =========================================


class ContractStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    BREACHED = "breached"
    EXPIRED = "expired"
    DEPRECATED = "deprecated"


class BreachSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


# =========================================
# DATA CLASSES
# =========================================


@dataclass
class QualityTerm:
    """A quality requirement within a contract."""

    metric: str = ""  # completeness, accuracy, freshness_hours, consistency
    operator: str = ">="  # >=, <=, ==, >, <
    threshold: float = 0.0
    description: str = ""


@dataclass
class DataContract:
    """Formal contract between a data producer and consumer."""

    id: str = ""
    name: str = ""
    version: int = 1
    producer: str = ""  # e.g., "Engine1_Scraper"
    consumer: str = ""  # e.g., "Engine2_ProgramMapping"
    asset_id: str = ""  # catalog asset ID
    schema_name: str = ""  # schema registry name
    schema_version: Optional[int] = None
    description: str = ""
    quality_terms: List[QualityTerm] = field(default_factory=list)
    refresh_schedule: str = ""  # "daily", "weekly", "hourly"
    max_staleness_hours: float = 24.0
    min_record_count: int = 0
    status: str = ContractStatus.ACTIVE.value
    created_at: str = ""
    updated_at: str = ""
    expires_at: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContractBreach:
    """A detected breach of a data contract."""

    id: str = ""
    contract_id: str = ""
    contract_name: str = ""
    severity: str = BreachSeverity.WARNING.value
    term_violated: str = ""
    expected: str = ""
    actual: str = ""
    message: str = ""
    detected_at: str = ""
    resolved: bool = False
    resolved_at: str = ""


@dataclass
class ContractCheckResult:
    """Result of checking a contract against current data state."""

    contract_id: str = ""
    contract_name: str = ""
    status: str = "passing"
    breaches: List[ContractBreach] = field(default_factory=list)
    terms_checked: int = 0
    terms_passing: int = 0
    checked_at: str = ""


# =========================================
# DATA CONTRACTS ENGINE
# =========================================


class DataContractsEngine:
    """Manages data contracts between producers and consumers."""

    def __init__(self):
        self._contracts: Dict[str, DataContract] = {}
        self._breaches: List[ContractBreach] = []
        self._check_history: List[ContractCheckResult] = []
        self._seed_defaults()

    def _seed_defaults(self) -> None:
        """Seed with known platform contracts."""
        now = datetime.now(timezone.utc).isoformat()

        defaults = [
            DataContract(
                id="contract_jobs_scraper",
                name="Job Scraper → Program Mapper",
                producer="Engine1_Scraper",
                consumer="Engine2_ProgramMapping",
                asset_id="jobs",
                schema_name="job_posting",
                description="Job scraper delivers daily postings conforming to job_posting schema",
                quality_terms=[
                    QualityTerm(
                        metric="completeness",
                        operator=">=",
                        threshold=0.85,
                        description="At least 85% field completeness",
                    ),
                    QualityTerm(
                        metric="accuracy",
                        operator=">=",
                        threshold=0.9,
                        description="At least 90% data accuracy",
                    ),
                ],
                refresh_schedule="daily",
                max_staleness_hours=28.0,
                min_record_count=1,
            ),
            DataContract(
                id="contract_contacts_etl",
                name="Bullhorn ETL → Knowledge System",
                producer="Engine7_BullhornETL",
                consumer="Engine8_Knowledge",
                asset_id="contacts",
                schema_name="contact",
                description="Bullhorn ETL delivers weekly contact updates conforming to contact schema",
                quality_terms=[
                    QualityTerm(
                        metric="completeness",
                        operator=">=",
                        threshold=0.9,
                        description="At least 90% field completeness",
                    ),
                    QualityTerm(
                        metric="accuracy",
                        operator=">=",
                        threshold=0.95,
                        description="At least 95% accuracy for contact data",
                    ),
                ],
                refresh_schedule="weekly",
                max_staleness_hours=168.0,
                min_record_count=100,
            ),
            DataContract(
                id="contract_programs_mapping",
                name="Program Mapping → BD Scoring",
                producer="Engine2_ProgramMapping",
                consumer="Engine5_Scoring",
                asset_id="programs",
                schema_name="program",
                description="Program mapper delivers enriched programs to scoring engine",
                quality_terms=[
                    QualityTerm(
                        metric="completeness",
                        operator=">=",
                        threshold=0.8,
                        description="At least 80% completeness",
                    ),
                ],
                refresh_schedule="weekly",
                max_staleness_hours=168.0,
            ),
        ]

        for contract in defaults:
            contract.created_at = now
            contract.updated_at = now
            self._contracts[contract.id] = contract

    # -----------------------------------------
    # CRUD
    # -----------------------------------------

    def create(self, contract: DataContract) -> str:
        """Create a new data contract."""
        if not contract.id:
            contract.id = uuid.uuid4().hex[:12]
        now = datetime.now(timezone.utc).isoformat()
        if not contract.created_at:
            contract.created_at = now
        contract.updated_at = now
        self._contracts[contract.id] = contract
        logger.debug("Created contract: %s (%s)", contract.name, contract.id)
        return contract.id

    def get(self, contract_id: str) -> Optional[DataContract]:
        """Get a contract by ID."""
        return self._contracts.get(contract_id)

    def list_contracts(
        self,
        producer: str = "",
        consumer: str = "",
        status: str = "",
    ) -> List[DataContract]:
        """List contracts with optional filtering."""
        results = list(self._contracts.values())
        if producer:
            results = [c for c in results if c.producer == producer]
        if consumer:
            results = [c for c in results if c.consumer == consumer]
        if status:
            results = [c for c in results if c.status == status]
        return results

    def update(
        self, contract_id: str, updates: Dict[str, Any]
    ) -> Optional[DataContract]:
        """Update a contract."""
        contract = self._contracts.get(contract_id)
        if not contract:
            return None
        for key, val in updates.items():
            if hasattr(contract, key) and key not in {"id", "created_at"}:
                setattr(contract, key, val)
        contract.updated_at = datetime.now(timezone.utc).isoformat()
        return contract

    def delete(self, contract_id: str) -> bool:
        """Delete a contract."""
        return self._contracts.pop(contract_id, None) is not None

    # -----------------------------------------
    # CHECK / ENFORCE
    # -----------------------------------------

    def check_contract(
        self,
        contract_id: str,
        current_metrics: Dict[str, float],
        record_count: int = 0,
        staleness_hours: float = 0.0,
    ) -> ContractCheckResult:
        """Check whether a contract's terms are currently met."""
        contract = self._contracts.get(contract_id)
        if not contract:
            return ContractCheckResult(
                contract_id=contract_id,
                status="error",
                checked_at=datetime.now(timezone.utc).isoformat(),
            )

        now_iso = datetime.now(timezone.utc).isoformat()
        breaches: List[ContractBreach] = []
        terms_checked = 0
        terms_passing = 0

        # Check quality terms
        for term in contract.quality_terms:
            terms_checked += 1
            actual = current_metrics.get(term.metric, 0.0)
            passed = self._evaluate_term(term.operator, actual, term.threshold)

            if passed:
                terms_passing += 1
            else:
                breach = ContractBreach(
                    id=uuid.uuid4().hex[:10],
                    contract_id=contract_id,
                    contract_name=contract.name,
                    severity=BreachSeverity.WARNING.value,
                    term_violated=term.metric,
                    expected=f"{term.operator} {term.threshold}",
                    actual=str(actual),
                    message=f"{term.metric}: expected {term.operator} {term.threshold}, got {actual}",
                    detected_at=now_iso,
                )
                breaches.append(breach)

        # Check staleness
        if contract.max_staleness_hours > 0 and staleness_hours > 0:
            terms_checked += 1
            if staleness_hours <= contract.max_staleness_hours:
                terms_passing += 1
            else:
                breaches.append(
                    ContractBreach(
                        id=uuid.uuid4().hex[:10],
                        contract_id=contract_id,
                        contract_name=contract.name,
                        severity=BreachSeverity.CRITICAL.value,
                        term_violated="staleness",
                        expected=f"<= {contract.max_staleness_hours}h",
                        actual=f"{staleness_hours}h",
                        message=f"Data staleness {staleness_hours}h exceeds max {contract.max_staleness_hours}h",
                        detected_at=now_iso,
                    )
                )

        # Check record count
        if contract.min_record_count > 0 and record_count > 0:
            terms_checked += 1
            if record_count >= contract.min_record_count:
                terms_passing += 1
            else:
                breaches.append(
                    ContractBreach(
                        id=uuid.uuid4().hex[:10],
                        contract_id=contract_id,
                        contract_name=contract.name,
                        severity=BreachSeverity.WARNING.value,
                        term_violated="record_count",
                        expected=f">= {contract.min_record_count}",
                        actual=str(record_count),
                        message=f"Record count {record_count} below minimum {contract.min_record_count}",
                        detected_at=now_iso,
                    )
                )

        # Update contract status
        status = "passing"
        if breaches:
            status = "breached"
            contract.status = ContractStatus.BREACHED.value
            self._breaches.extend(breaches)
        else:
            if contract.status == ContractStatus.BREACHED.value:
                contract.status = ContractStatus.ACTIVE.value

        result = ContractCheckResult(
            contract_id=contract_id,
            contract_name=contract.name,
            status=status,
            breaches=breaches,
            terms_checked=terms_checked,
            terms_passing=terms_passing,
            checked_at=now_iso,
        )
        self._check_history.append(result)
        return result

    def check_all(
        self,
        metrics_by_asset: Dict[str, Dict[str, float]],
    ) -> List[ContractCheckResult]:
        """Check all active contracts against provided metrics."""
        results = []
        for contract in self._contracts.values():
            if contract.status in {
                ContractStatus.EXPIRED.value,
                ContractStatus.DEPRECATED.value,
            }:
                continue
            asset_metrics = metrics_by_asset.get(contract.asset_id, {})
            result = self.check_contract(
                contract.id,
                current_metrics=asset_metrics,
                record_count=int(asset_metrics.get("record_count", 0)),
                staleness_hours=asset_metrics.get("staleness_hours", 0),
            )
            results.append(result)
        return results

    @staticmethod
    def _evaluate_term(operator: str, actual: float, threshold: float) -> bool:
        """Evaluate a quality term comparison."""
        if operator == ">=":
            return actual >= threshold
        elif operator == "<=":
            return actual <= threshold
        elif operator == ">":
            return actual > threshold
        elif operator == "<":
            return actual < threshold
        elif operator == "==":
            return abs(actual - threshold) < 1e-6
        return False

    # -----------------------------------------
    # BREACHES
    # -----------------------------------------

    def get_breaches(
        self,
        contract_id: str = "",
        unresolved_only: bool = False,
    ) -> List[ContractBreach]:
        """Get breach history."""
        results = list(self._breaches)
        if contract_id:
            results = [b for b in results if b.contract_id == contract_id]
        if unresolved_only:
            results = [b for b in results if not b.resolved]
        return results

    def resolve_breach(self, breach_id: str) -> bool:
        """Mark a breach as resolved."""
        for b in self._breaches:
            if b.id == breach_id:
                b.resolved = True
                b.resolved_at = datetime.now(timezone.utc).isoformat()
                return True
        return False

    # -----------------------------------------
    # STATS
    # -----------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """Get contract engine statistics."""
        contracts = list(self._contracts.values())
        return {
            "total_contracts": len(contracts),
            "by_status": {
                s.value: sum(1 for c in contracts if c.status == s.value)
                for s in ContractStatus
            },
            "total_breaches": len(self._breaches),
            "unresolved_breaches": sum(1 for b in self._breaches if not b.resolved),
            "total_checks": len(self._check_history),
        }


# =========================================
# SINGLETON
# =========================================

_engine: Optional[DataContractsEngine] = None


def get_contracts_engine() -> DataContractsEngine:
    global _engine
    if _engine is None:
        _engine = DataContractsEngine()
    return _engine
