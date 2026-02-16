"""
Phase 9A API Router - Competitive Intelligence Endpoints

Endpoints:
  - GET  /contracts/awards      - Recent contract awards (cached/mock)
  - GET  /contracts/expiring    - Contracts expiring soon (recompete opps)
  - GET  /competitive/summary   - Competitor activity summary for dashboard
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Query

logger = logging.getLogger("BDKnowledgeAPI.phase9a")

router = APIRouter()

# =========================================
# MOCK DATA (replaced by Tango/SAM.gov when available)
# =========================================

MAJOR_PRIMES = ["GDIT", "Leidos", "SAIC", "CACI", "Peraton", "BAE Systems"]

_MOCK_AWARDS = [
    {
        "id": "FA8730-26-C-0012",
        "title": "DCGS-A Sustainment",
        "agency": "USAF",
        "contractor": "GDIT",
        "value_usd": 145_000_000,
        "award_date": "2026-01-15",
        "period": "5 years",
        "naics": "541512",
    },
    {
        "id": "W911W4-25-C-0089",
        "title": "DCGS-A Increment 2",
        "agency": "US Army",
        "contractor": "Leidos",
        "value_usd": 230_000_000,
        "award_date": "2025-11-20",
        "period": "3 years + 2 option",
        "naics": "541330",
    },
    {
        "id": "N00024-26-C-5401",
        "title": "DCGS-N Modernization",
        "agency": "US Navy",
        "contractor": "SAIC",
        "value_usd": 89_000_000,
        "award_date": "2026-02-01",
        "period": "4 years",
        "naics": "541512",
    },
    {
        "id": "FA8730-25-C-0198",
        "title": "ISR Data Fusion Platform",
        "agency": "USAF",
        "contractor": "CACI",
        "value_usd": 67_500_000,
        "award_date": "2025-12-10",
        "period": "3 years",
        "naics": "541715",
    },
    {
        "id": "W56KGZ-25-C-0034",
        "title": "Multi-INT Processing",
        "agency": "US Army",
        "contractor": "Peraton",
        "value_usd": 112_000_000,
        "award_date": "2025-10-05",
        "period": "5 years",
        "naics": "541512",
    },
    {
        "id": "N00024-26-C-5502",
        "title": "Tactical SIGINT Integration",
        "agency": "US Navy",
        "contractor": "BAE Systems",
        "value_usd": 54_000_000,
        "award_date": "2026-01-28",
        "period": "3 years",
        "naics": "541330",
    },
    {
        "id": "FA8730-26-C-0045",
        "title": "Cloud-Based ISR Analytics",
        "agency": "USAF",
        "contractor": "GDIT",
        "value_usd": 78_000_000,
        "award_date": "2026-02-05",
        "period": "4 years",
        "naics": "541512",
    },
    {
        "id": "W911W4-26-C-0011",
        "title": "GEOINT Processing System",
        "agency": "US Army",
        "contractor": "Leidos",
        "value_usd": 95_000_000,
        "award_date": "2025-09-18",
        "period": "5 years",
        "naics": "541715",
    },
]

_MOCK_EXPIRING = [
    {
        "id": "FA8730-21-C-0088",
        "title": "DCGS Backbone Network",
        "agency": "USAF",
        "incumbent": "SAIC",
        "value_usd": 185_000_000,
        "expiry_date": "2026-06-30",
        "months_remaining": 4,
        "recompete_likely": True,
    },
    {
        "id": "W911W4-22-C-0156",
        "title": "ISR Training Systems",
        "agency": "US Army",
        "incumbent": "CACI",
        "value_usd": 42_000_000,
        "expiry_date": "2026-08-15",
        "months_remaining": 6,
        "recompete_likely": True,
    },
    {
        "id": "N00024-21-C-5201",
        "title": "Maritime ISR Ops Support",
        "agency": "US Navy",
        "incumbent": "Peraton",
        "value_usd": 68_000_000,
        "expiry_date": "2026-10-01",
        "months_remaining": 7,
        "recompete_likely": False,
    },
]

_HIRING_BY_LOCATION = {
    "GDIT": {
        "Springfield, VA": 12,
        "San Antonio, TX": 8,
        "Augusta, GA": 5,
        "Honolulu, HI": 3,
        "Tampa, FL": 6,
    },
    "Leidos": {
        "Reston, VA": 15,
        "San Antonio, TX": 6,
        "Augusta, GA": 7,
        "Tampa, FL": 4,
        "Colorado Springs, CO": 3,
    },
    "SAIC": {
        "Reston, VA": 9,
        "San Antonio, TX": 11,
        "Augusta, GA": 3,
        "Honolulu, HI": 5,
        "Tampa, FL": 2,
    },
    "CACI": {
        "Arlington, VA": 7,
        "San Antonio, TX": 4,
        "Augusta, GA": 6,
        "Tampa, FL": 8,
        "Colorado Springs, CO": 2,
    },
    "Peraton": {
        "Herndon, VA": 8,
        "San Antonio, TX": 3,
        "Augusta, GA": 4,
        "Tampa, FL": 5,
        "Honolulu, HI": 2,
    },
    "BAE Systems": {
        "McLean, VA": 6,
        "San Antonio, TX": 2,
        "Augusta, GA": 3,
        "Tampa, FL": 3,
        "Colorado Springs, CO": 4,
    },
}


# =========================================
# ENDPOINTS
# =========================================


@router.get("/contracts/awards")
async def get_contract_awards(
    days: int = Query(default=90, ge=1, le=365),
    agency: Optional[str] = Query(default=None),
    keyword: Optional[str] = Query(default=None),
):
    """Recent contract awards, filtered by date range, agency, and keyword."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    results = []

    for award in _MOCK_AWARDS:
        award_dt = datetime.fromisoformat(award["award_date"])
        if award_dt < cutoff:
            continue
        if agency and agency.upper() not in award["agency"].upper():
            continue
        if keyword and keyword.lower() not in award["title"].lower():
            continue
        results.append(award)

    return {
        "awards": results,
        "total": len(results),
        "period_days": days,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/contracts/expiring")
async def get_expiring_contracts(
    months: int = Query(default=6, ge=1, le=24),
):
    """Contracts expiring within the given timeframe (recompete opportunities)."""
    results = [c for c in _MOCK_EXPIRING if c["months_remaining"] <= months]

    return {
        "contracts": results,
        "total": len(results),
        "horizon_months": months,
        "total_value_usd": sum(c["value_usd"] for c in results),
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/competitive/summary")
async def get_competitive_summary():
    """Aggregated competitor activity summary for the executive dashboard."""
    competitors = []

    for prime in MAJOR_PRIMES:
        awards = [a for a in _MOCK_AWARDS if a["contractor"] == prime]
        hiring = _HIRING_BY_LOCATION.get(prime, {})
        total_jobs = sum(hiring.values())
        total_value = sum(a["value_usd"] for a in awards)

        competitors.append(
            {
                "name": prime,
                "recent_awards": len(awards),
                "total_value_usd": total_value,
                "hiring_activity": total_jobs,
                "top_locations": sorted(hiring.items(), key=lambda x: -x[1])[:3],
                "latest_award": awards[0]["title"] if awards else None,
            }
        )

    # Sort by total value descending
    competitors.sort(key=lambda x: -x["total_value_usd"])

    # Market share calculation
    total_market = sum(c["total_value_usd"] for c in competitors)
    market_share = [
        {
            "name": c["name"],
            "value_usd": c["total_value_usd"],
            "share_pct": round(c["total_value_usd"] / max(total_market, 1) * 100, 1),
        }
        for c in competitors
    ]

    return {
        "competitors": competitors,
        "market_share": market_share,
        "total_market_value": total_market,
        "expiring_soon": len(_MOCK_EXPIRING),
        "timestamp": datetime.utcnow().isoformat(),
    }
