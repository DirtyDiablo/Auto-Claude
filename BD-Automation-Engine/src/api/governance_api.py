"""Phase 43A — Governance API (12 endpoints)

REST endpoints for data catalog, schema registry, contracts, and SLAs.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from src.governance.catalog import DataAsset, get_data_catalog
from src.governance.schema_registry import (
    DataSchema, get_schema_registry,
)
from src.governance.contracts import (
    DataContract, get_contracts_engine,
)
from src.governance.sla_engine import (
    QualitySLA, SLAAlert, get_sla_engine,
)

logger = logging.getLogger(__name__)


# =========================================
# REQUEST MODELS
# =========================================

class ValidateRequest(BaseModel):
    schema_name: str
    data: Dict[str, Any]
    version: Optional[int] = None


class ContractCheckRequest(BaseModel):
    contract_id: str
    metrics: Dict[str, float] = Field(default_factory=dict)
    record_count: int = 0
    staleness_hours: float = 0.0


class SLACheckRequest(BaseModel):
    sla_id: str
    metrics: Dict[str, float] = Field(default_factory=dict)


class CheckAllRequest(BaseModel):
    metrics_by_asset: Dict[str, Dict[str, float]] = Field(default_factory=dict)


# =========================================
# ROUTE SETUP
# =========================================

def include_governance_router(app: FastAPI) -> None:
    """Register all governance endpoints on the FastAPI app."""

    catalog = get_data_catalog()
    registry = get_schema_registry()
    contracts = get_contracts_engine()
    sla_engine = get_sla_engine()

    # --------------------------------------------------
    # 1. GET /governance/catalog — Browse data catalog
    # --------------------------------------------------
    @app.get("/governance/catalog")
    async def governance_catalog(
        domain: str = "",
        asset_type: str = "",
        limit: int = Query(100, ge=1, le=500),
    ):
        """Browse the data catalog."""
        assets = catalog.list_assets(domain=domain, asset_type=asset_type, limit=limit)
        return {
            "assets": [_serialize_asset(a) for a in assets],
            "total": len(assets),
        }

    # --------------------------------------------------
    # 2. GET /governance/catalog/search — Search catalog
    #    (MUST be before {asset_id} to avoid route conflict)
    # --------------------------------------------------
    @app.get("/governance/catalog/search")
    async def governance_search(
        q: str = Query(..., min_length=2),
        limit: int = Query(20, ge=1, le=100),
    ):
        """Search the data catalog."""
        results = catalog.search(q, limit=limit)
        return {
            "query": q,
            "results": [_serialize_asset(a) for a in results],
            "count": len(results),
        }

    # --------------------------------------------------
    # 3. GET /governance/catalog/{asset_id} — Asset details
    # --------------------------------------------------
    @app.get("/governance/catalog/{asset_id}")
    async def governance_catalog_asset(asset_id: str):
        """Get detailed info about a data asset."""
        asset = catalog.get(asset_id)
        if not asset:
            raise HTTPException(404, "Asset not found")
        return _serialize_asset(asset)

    # --------------------------------------------------
    # 4. GET /governance/catalog/{asset_id}/lineage — Asset lineage
    # --------------------------------------------------
    @app.get("/governance/catalog/{asset_id}/lineage")
    async def governance_lineage(asset_id: str):
        """Get data lineage for an asset."""
        lineage = catalog.get_lineage(asset_id)
        if not lineage:
            raise HTTPException(404, "Asset not found")
        return lineage

    # --------------------------------------------------
    # 5. GET /governance/schemas — List all schemas
    # --------------------------------------------------
    @app.get("/governance/schemas")
    async def governance_schemas():
        """List all registered schemas (latest versions)."""
        schemas = registry.list_schemas()
        return {
            "schemas": [_serialize_schema(s) for s in schemas],
            "total": len(schemas),
        }

    # --------------------------------------------------
    # 6. POST /governance/schemas/validate — Validate data
    # --------------------------------------------------
    @app.post("/governance/schemas/validate")
    async def governance_validate(req: ValidateRequest):
        """Validate a data record against a schema."""
        result = registry.validate(req.schema_name, req.data, req.version)
        return {
            "valid": result.valid,
            "errors": result.errors,
            "warnings": result.warnings,
            "fields_checked": result.fields_checked,
            "fields_valid": result.fields_valid,
        }

    # --------------------------------------------------
    # 7. GET /governance/contracts — List contracts
    # --------------------------------------------------
    @app.get("/governance/contracts")
    async def governance_contracts(
        producer: str = "",
        consumer: str = "",
    ):
        """List data contracts."""
        items = contracts.list_contracts(producer=producer, consumer=consumer)
        return {
            "contracts": [_serialize_contract(c) for c in items],
            "total": len(items),
        }

    # --------------------------------------------------
    # 8. POST /governance/contracts/check — Check a contract
    # --------------------------------------------------
    @app.post("/governance/contracts/check")
    async def governance_contract_check(req: ContractCheckRequest):
        """Check whether a contract's terms are met."""
        result = contracts.check_contract(
            req.contract_id, req.metrics, req.record_count, req.staleness_hours,
        )
        return {
            "contract_id": result.contract_id,
            "contract_name": result.contract_name,
            "status": result.status,
            "terms_checked": result.terms_checked,
            "terms_passing": result.terms_passing,
            "breaches": [_serialize_breach(b) for b in result.breaches],
            "checked_at": result.checked_at,
        }

    # --------------------------------------------------
    # 9. GET /governance/slas — List SLAs
    # --------------------------------------------------
    @app.get("/governance/slas")
    async def governance_slas(asset_id: str = ""):
        """List quality SLAs."""
        items = sla_engine.list_slas(asset_id=asset_id)
        return {
            "slas": [_serialize_sla(s) for s in items],
            "total": len(items),
        }

    # --------------------------------------------------
    # 10. POST /governance/slas/check — Check an SLA
    # --------------------------------------------------
    @app.post("/governance/slas/check")
    async def governance_sla_check(req: SLACheckRequest):
        """Check an SLA against current metrics."""
        result = sla_engine.check_sla(req.sla_id, req.metrics)
        return {
            "sla_id": result.sla_id,
            "sla_name": result.sla_name,
            "status": result.status,
            "targets_checked": result.targets_checked,
            "targets_met": result.targets_met,
            "targets_at_risk": result.targets_at_risk,
            "targets_violated": result.targets_violated,
            "alerts": [_serialize_alert(a) for a in result.alerts],
            "checked_at": result.checked_at,
        }

    # --------------------------------------------------
    # 11. POST /governance/check-all — Check all contracts + SLAs
    # --------------------------------------------------
    @app.post("/governance/check-all")
    async def governance_check_all(req: CheckAllRequest):
        """Check all contracts and SLAs against current metrics."""
        contract_results = contracts.check_all(req.metrics_by_asset)
        sla_results = sla_engine.check_all(req.metrics_by_asset)
        return {
            "contracts": [
                {
                    "contract_id": r.contract_id,
                    "status": r.status,
                    "breaches": len(r.breaches),
                }
                for r in contract_results
            ],
            "slas": [
                {
                    "sla_id": r.sla_id,
                    "status": r.status,
                    "targets_violated": r.targets_violated,
                }
                for r in sla_results
            ],
            "total_breaches": sum(len(r.breaches) for r in contract_results),
            "total_violations": sum(r.targets_violated for r in sla_results),
        }

    # --------------------------------------------------
    # 12. GET /governance/stats — Governance statistics
    # --------------------------------------------------
    @app.get("/governance/stats")
    async def governance_stats():
        """Get overall governance statistics."""
        return {
            "catalog": catalog.get_stats(),
            "schemas": registry.get_stats(),
            "contracts": contracts.get_stats(),
            "slas": sla_engine.get_stats(),
        }

    logger.info("Governance API: 12 endpoints registered under /governance/*")


# =========================================
# SERIALIZATION HELPERS
# =========================================

def _serialize_asset(a: DataAsset) -> Dict[str, Any]:
    return {
        "id": a.id, "name": a.name, "description": a.description,
        "asset_type": a.asset_type, "status": a.status,
        "owner": a.owner, "domain": a.domain, "schema_id": a.schema_id,
        "tags": a.tags, "record_count": a.record_count,
        "quality": {
            "completeness": a.quality.completeness,
            "accuracy": a.quality.accuracy,
            "freshness_hours": a.quality.freshness_hours,
            "overall_score": a.quality.overall_score,
        },
        "usage": {
            "total_reads": a.usage.total_reads,
            "total_writes": a.usage.total_writes,
            "popularity_score": a.usage.popularity_score,
        },
        "created_at": a.created_at, "updated_at": a.updated_at,
    }


def _serialize_schema(s: DataSchema) -> Dict[str, Any]:
    return {
        "id": s.id, "name": s.name, "version": s.version,
        "domain": s.domain, "description": s.description,
        "status": s.status,
        "fields": [
            {"name": f.name, "type": f.field_type, "required": f.required,
             "description": f.description}
            for f in s.fields
        ],
        "compatibility": s.compatibility,
        "created_at": s.created_at,
    }


def _serialize_contract(c: DataContract) -> Dict[str, Any]:
    return {
        "id": c.id, "name": c.name, "version": c.version,
        "producer": c.producer, "consumer": c.consumer,
        "asset_id": c.asset_id, "schema_name": c.schema_name,
        "description": c.description, "status": c.status,
        "refresh_schedule": c.refresh_schedule,
        "max_staleness_hours": c.max_staleness_hours,
        "quality_terms": [
            {"metric": t.metric, "operator": t.operator, "threshold": t.threshold}
            for t in c.quality_terms
        ],
        "created_at": c.created_at,
    }


def _serialize_breach(b) -> Dict[str, Any]:
    return {
        "id": b.id, "severity": b.severity,
        "term_violated": b.term_violated,
        "expected": b.expected, "actual": b.actual,
        "message": b.message, "detected_at": b.detected_at,
    }


def _serialize_sla(s: QualitySLA) -> Dict[str, Any]:
    return {
        "id": s.id, "name": s.name, "asset_id": s.asset_id,
        "owner": s.owner, "description": s.description,
        "status": s.status,
        "targets": [
            {"metric": t.metric, "target_value": t.target_value,
             "operator": t.operator, "window": t.window}
            for t in s.targets
        ],
        "created_at": s.created_at,
    }


def _serialize_alert(a: SLAAlert) -> Dict[str, Any]:
    return {
        "id": a.id, "level": a.level,
        "target_metric": a.target_metric,
        "expected": a.expected, "actual": a.actual,
        "message": a.message, "created_at": a.created_at,
    }
