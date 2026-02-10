"""
Phase 24A — SAM.gov Contract Sync

Real-time federal contract monitoring via SAM.gov / Tango API.
Tracks awards, modifications, opportunities, and generates alerts
for contracts matching BD watch configurations.
"""

import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import structlog

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------


@dataclass
class ContractAward:
    award_id: str = ""
    title: str = ""
    awardee: str = ""
    value: float = 0.0
    naics: str = ""
    set_aside: Optional[str] = None
    agency: str = ""
    sub_agency: Optional[str] = None
    award_date: Optional[date] = None
    pop_start: Optional[date] = None
    pop_end: Optional[date] = None
    description: str = ""
    place_of_performance: Optional[str] = None
    contract_type: str = ""
    modifications: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ContractOpportunity:
    notice_id: str = ""
    title: str = ""
    type: str = ""  # RFI, RFP, Sources Sought, Combined Synopsis
    agency: str = ""
    posted_date: Optional[date] = None
    response_deadline: Optional[date] = None
    naics: str = ""
    set_aside: Optional[str] = None
    description: str = ""
    point_of_contact: Optional[Dict[str, str]] = None
    attachments: List[str] = field(default_factory=list)


@dataclass
class WatchConfig:
    watch_id: str = ""
    name: str = ""
    keywords: List[str] = field(default_factory=list)
    naics_codes: List[str] = field(default_factory=list)
    companies: List[str] = field(default_factory=list)
    agencies: List[str] = field(default_factory=list)
    min_value: Optional[float] = None
    alert_on: List[str] = field(default_factory=lambda: ["new_award", "new_opportunity"])
    enabled: bool = True
    created_at: Optional[str] = None


@dataclass
class ContractAlert:
    alert_type: str = ""  # new_award, modification, new_opportunity, deadline_approaching
    contract: Optional[Union[ContractAward, ContractOpportunity]] = None
    matched_watch: str = ""
    relevance_score: float = 0.0
    recommended_action: str = ""
    created_at: Optional[str] = None


@dataclass
class ContractDetail:
    award: ContractAward = field(default_factory=ContractAward)
    modifications: List[Dict[str, Any]] = field(default_factory=list)
    subcontracting_plan: Optional[Dict[str, Any]] = None
    related_notices: List[str] = field(default_factory=list)


@dataclass
class SyncResult:
    contracts_synced: int = 0
    nodes_created: int = 0
    relationships_created: int = 0
    errors: List[str] = field(default_factory=list)


@dataclass
class SearchQuery:
    keywords: List[str] = field(default_factory=list)
    naics_codes: List[str] = field(default_factory=list)
    set_aside: Optional[str] = None
    awardee: Optional[str] = None
    agency: Optional[str] = None
    date_range: Optional[Tuple[date, date]] = None
    min_value: Optional[float] = None
    limit: int = 50


@dataclass
class OpportunityQuery:
    keywords: List[str] = field(default_factory=list)
    naics_codes: List[str] = field(default_factory=list)
    set_aside: Optional[str] = None
    agency: Optional[str] = None
    response_deadline_after: Optional[date] = None
    type_filter: Optional[str] = None
    limit: int = 50


# ---------------------------------------------------------------------------
# SAM.gov Sync
# ---------------------------------------------------------------------------


class SAMGovSync:
    """Monitor federal contract awards, modifications, and opportunities."""

    SAM_API_BASE = "https://api.sam.gov/opportunities/v2"
    TANGO_API_BASE = "https://api.makegov.com/v1"

    def __init__(
        self,
        tango_api_key: Optional[str] = None,
        sam_api_key: Optional[str] = None,
        storage_path: Optional[str] = None,
    ):
        self.tango_key = tango_api_key or os.getenv("TANGO_API_KEY")
        self.sam_key = sam_api_key or os.getenv("SAM_API_KEY")
        self._storage = Path(storage_path or "Engine8_Knowledge/data/sam_gov")
        self._storage.mkdir(parents=True, exist_ok=True)
        self._watches_path = self._storage / "watches.json"
        self._last_check_path = self._storage / "last_check.json"
        self._watches: List[WatchConfig] = self._load_watches()
        logger.info(
            "sam_gov_sync_init",
            has_tango=bool(self.tango_key),
            has_sam=bool(self.sam_key),
            watches=len(self._watches),
        )

    # ------------------------------------------------------------------
    # Watch management
    # ------------------------------------------------------------------

    def _load_watches(self) -> List[WatchConfig]:
        if self._watches_path.exists():
            try:
                data = json.loads(self._watches_path.read_text())
                return [WatchConfig(**w) for w in data]
            except Exception:
                pass
        return []

    def _save_watches(self):
        from dataclasses import asdict
        data = [asdict(w) for w in self._watches]
        self._watches_path.write_text(json.dumps(data, indent=2, default=str))

    def add_watch(self, config: WatchConfig) -> WatchConfig:
        if not config.watch_id:
            config.watch_id = f"watch_{uuid.uuid4().hex[:8]}"
        if not config.created_at:
            config.created_at = datetime.utcnow().isoformat()
        self._watches.append(config)
        self._save_watches()
        logger.info("watch_added", watch_id=config.watch_id, name=config.name)
        return config

    def remove_watch(self, watch_id: str) -> bool:
        before = len(self._watches)
        self._watches = [w for w in self._watches if w.watch_id != watch_id]
        if len(self._watches) < before:
            self._save_watches()
            return True
        return False

    def list_watches(self) -> List[WatchConfig]:
        return list(self._watches)

    # ------------------------------------------------------------------
    # API interactions
    # ------------------------------------------------------------------

    async def _tango_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make request to Tango/MakeGov API."""
        if not self.tango_key:
            logger.warning("tango_api_key_missing")
            return {"results": [], "total": 0}
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(
                    f"{self.TANGO_API_BASE}/{endpoint}",
                    params=params,
                    headers={"Authorization": f"Bearer {self.tango_key}"},
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:
            logger.error("tango_request_error", endpoint=endpoint, error=str(exc))
            return {"results": [], "total": 0}

    async def _sam_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make request to SAM.gov API (free fallback)."""
        if not self.sam_key:
            logger.warning("sam_api_key_missing")
            return {"opportunitiesData": [], "totalRecords": 0}
        try:
            import httpx
            params["api_key"] = self.sam_key
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(
                    f"{self.SAM_API_BASE}/{endpoint}",
                    params=params,
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:
            logger.error("sam_request_error", endpoint=endpoint, error=str(exc))
            return {"opportunitiesData": [], "totalRecords": 0}

    # ------------------------------------------------------------------
    # Search operations
    # ------------------------------------------------------------------

    async def search_awards(self, query: SearchQuery) -> List[ContractAward]:
        """Search contract awards with filters."""
        params: Dict[str, Any] = {"limit": query.limit}
        if query.keywords:
            params["q"] = " ".join(query.keywords)
        if query.naics_codes:
            params["naics"] = ",".join(query.naics_codes)
        if query.awardee:
            params["awardee"] = query.awardee
        if query.agency:
            params["agency"] = query.agency
        if query.set_aside:
            params["set_aside"] = query.set_aside
        if query.min_value:
            params["min_value"] = query.min_value
        if query.date_range:
            params["date_from"] = query.date_range[0].isoformat()
            params["date_to"] = query.date_range[1].isoformat()

        data = await self._tango_request("awards", params)
        awards = []
        for item in data.get("results", []):
            awards.append(ContractAward(
                award_id=item.get("id", ""),
                title=item.get("title", ""),
                awardee=item.get("awardee", {}).get("name", ""),
                value=float(item.get("value", 0)),
                naics=item.get("naics", ""),
                set_aside=item.get("set_aside"),
                agency=item.get("agency", ""),
                sub_agency=item.get("sub_agency"),
                description=item.get("description", ""),
                place_of_performance=item.get("place_of_performance"),
                contract_type=item.get("contract_type", ""),
            ))
        logger.info("search_awards", keywords=query.keywords, results=len(awards))
        return awards

    async def search_opportunities(self, query: OpportunityQuery) -> List[ContractOpportunity]:
        """Search active solicitations (RFIs, RFPs, Sources Sought)."""
        params: Dict[str, Any] = {"limit": query.limit, "status": "active"}
        if query.keywords:
            params["q"] = " ".join(query.keywords)
        if query.naics_codes:
            params["naics"] = ",".join(query.naics_codes)
        if query.agency:
            params["agency"] = query.agency
        if query.set_aside:
            params["set_aside"] = query.set_aside
        if query.type_filter:
            params["type"] = query.type_filter

        # Try Tango first, fall back to SAM.gov
        data = await self._tango_request("opportunities", params)
        if not data.get("results"):
            sam_data = await self._sam_request("search", {
                "keyword": " ".join(query.keywords) if query.keywords else "",
                "limit": query.limit,
            })
            data["results"] = sam_data.get("opportunitiesData", [])

        opportunities = []
        for item in data.get("results", []):
            opportunities.append(ContractOpportunity(
                notice_id=item.get("noticeId", item.get("id", "")),
                title=item.get("title", ""),
                type=item.get("type", item.get("noticeType", "")),
                agency=item.get("agency", item.get("fullParentPathName", "")),
                naics=item.get("naics", ""),
                set_aside=item.get("set_aside", item.get("typeOfSetAsideDescription")),
                description=item.get("description", ""),
                attachments=item.get("attachments", []),
            ))
        logger.info("search_opportunities", keywords=query.keywords, results=len(opportunities))
        return opportunities

    async def monitor_awards(self, watch_list: Optional[List[WatchConfig]] = None) -> List[ContractAlert]:
        """
        Check for new awards matching watch configurations.
        Returns alerts for new/modified awards since last check.
        """
        watches = watch_list or self._watches
        if not watches:
            return []

        alerts: List[ContractAlert] = []
        last_check = self._load_last_check()

        for watch in watches:
            if not watch.enabled:
                continue

            query = SearchQuery(
                keywords=watch.keywords,
                naics_codes=watch.naics_codes,
                agencies=watch.agencies if hasattr(watch, "agencies") else [],
                limit=20,
            )
            if watch.min_value:
                query.min_value = watch.min_value

            awards = await self.search_awards(query)

            for award in awards:
                if award.award_id in last_check.get("seen_awards", set()):
                    continue

                relevance = self._calculate_relevance(award, watch)
                if relevance < 0.3:
                    continue

                alert = ContractAlert(
                    alert_type="new_award",
                    contract=award,
                    matched_watch=watch.name,
                    relevance_score=relevance,
                    recommended_action=self._recommend_action(award, relevance),
                    created_at=datetime.utcnow().isoformat(),
                )
                alerts.append(alert)
                last_check.setdefault("seen_awards", set()).add(award.award_id)

        self._save_last_check(last_check)
        logger.info("monitor_awards_complete", watches=len(watches), alerts=len(alerts))
        return alerts

    async def get_contract_details(self, award_id: str) -> ContractDetail:
        """Full contract details including modifications."""
        data = await self._tango_request(f"awards/{award_id}", {})
        award_data = data.get("award", data)
        award = ContractAward(
            award_id=award_data.get("id", award_id),
            title=award_data.get("title", ""),
            awardee=award_data.get("awardee", {}).get("name", ""),
            value=float(award_data.get("value", 0)),
            description=award_data.get("description", ""),
        )
        return ContractDetail(
            award=award,
            modifications=award_data.get("modifications", []),
            subcontracting_plan=award_data.get("subcontracting_plan"),
            related_notices=award_data.get("related_notices", []),
        )

    async def get_company_awards(
        self, company_name: str, days: int = 365
    ) -> List[ContractAward]:
        """All awards to a specific company in the given time period."""
        from datetime import timedelta
        end = date.today()
        start = end - timedelta(days=days)
        query = SearchQuery(awardee=company_name, date_range=(start, end), limit=100)
        return await self.search_awards(query)

    async def sync_to_neo4j(
        self, awards: List[ContractAward], hub_client=None
    ) -> SyncResult:
        """Create/update Contract nodes in Neo4j."""
        result = SyncResult()
        if not hub_client:
            logger.warning("sync_to_neo4j_no_client")
            return result

        for award in awards:
            try:
                # Create contract node
                await hub_client.post("/neo4j/nodes", json={
                    "label": "Contract",
                    "properties": {
                        "award_id": award.award_id,
                        "title": award.title,
                        "value": award.value,
                        "naics": award.naics,
                        "agency": award.agency,
                        "contract_type": award.contract_type,
                    },
                })
                result.nodes_created += 1

                # Create AWARDED_TO relationship
                if award.awardee:
                    await hub_client.post("/neo4j/relationships", json={
                        "from_label": "Contract",
                        "from_key": "award_id",
                        "from_value": award.award_id,
                        "to_label": "Contractor",
                        "to_key": "name",
                        "to_value": award.awardee,
                        "relationship": "AWARDED_TO",
                    })
                    result.relationships_created += 1

                result.contracts_synced += 1
            except Exception as exc:
                result.errors.append(f"{award.award_id}: {exc}")

        logger.info(
            "sync_to_neo4j_complete",
            synced=result.contracts_synced,
            nodes=result.nodes_created,
            rels=result.relationships_created,
            errors=len(result.errors),
        )
        return result

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _calculate_relevance(self, award: ContractAward, watch: WatchConfig) -> float:
        """Score 0-1 relevance of an award to a watch config."""
        score = 0.0
        text = f"{award.title} {award.description} {award.awardee}".lower()

        if watch.keywords:
            matches = sum(1 for kw in watch.keywords if kw.lower() in text)
            score += 0.4 * (matches / len(watch.keywords))
        if watch.naics_codes and award.naics in watch.naics_codes:
            score += 0.3
        if watch.companies:
            if any(c.lower() in award.awardee.lower() for c in watch.companies):
                score += 0.2
        if watch.min_value and award.value >= watch.min_value:
            score += 0.1

        return min(score, 1.0)

    def _recommend_action(self, award: ContractAward, relevance: float) -> str:
        if relevance >= 0.8:
            return "URGENT: Review immediately — high relevance to PTS BD pipeline"
        elif relevance >= 0.5:
            return "Review and assess teaming/subcontracting opportunity"
        else:
            return "Monitor — track for future reference"

    def _load_last_check(self) -> Dict[str, Any]:
        if self._last_check_path.exists():
            try:
                data = json.loads(self._last_check_path.read_text())
                data["seen_awards"] = set(data.get("seen_awards", []))
                return data
            except Exception:
                pass
        return {"seen_awards": set(), "last_run": None}

    def _save_last_check(self, data: Dict[str, Any]):
        save_data = dict(data)
        save_data["seen_awards"] = list(data.get("seen_awards", set()))
        save_data["last_run"] = datetime.utcnow().isoformat()
        self._last_check_path.write_text(json.dumps(save_data, indent=2))


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_instance: Optional[SAMGovSync] = None


def get_sam_gov_sync(**kwargs) -> SAMGovSync:
    global _instance
    if _instance is None:
        _instance = SAMGovSync(**kwargs)
    return _instance
