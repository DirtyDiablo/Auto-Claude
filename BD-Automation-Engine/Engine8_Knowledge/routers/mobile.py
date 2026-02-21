"""Mobile-optimised API router for BD Intelligence Dashboard.

Provides compact, flat-payload endpoints designed for mobile clients:
- Small payloads (< 5 KB typical)
- Cache-Control headers for offline support
- Pagination for list endpoints
- Unified search across entity types
"""

import asyncio
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Response

from Engine8_Knowledge.models.mobile_models import (
    MobileAlertListResponse,
    MobileContactDetailResponse,
    MobileContactListResponse,
    MobileDashboardResponse,
    MobileProgramListResponse,
    MobileSearchResponse,
    PWAManifest,
)
from Engine8_Knowledge.services.mobile_service import MobileService

try:
    import structlog

    logger = structlog.get_logger("MobileRouter")
except ImportError:
    logger = logging.getLogger("MobileRouter")

router = APIRouter(prefix="/mobile", tags=["Mobile API"])

# Singleton service instance
_mobile_service: Optional[MobileService] = None


def _get_service() -> MobileService:
    """Lazy-init mobile service singleton."""
    global _mobile_service
    if _mobile_service is None:
        _mobile_service = MobileService()
    return _mobile_service


# ---------------------------------------------------------------------------
# Cache helper
# ---------------------------------------------------------------------------

def _set_cache_headers(response: Response, max_age: int = 60) -> None:
    """Apply cache-control headers for mobile / offline support."""
    response.headers["Cache-Control"] = f"public, max-age={max_age}, stale-while-revalidate={max_age * 2}"
    response.headers["X-Mobile-Optimized"] = "true"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/dashboard", response_model=MobileDashboardResponse)
async def mobile_dashboard(response: Response):
    """Compact dashboard summary for mobile rendering.

    Returns top-level metrics in a flat, small-payload structure suitable
    for a mobile home screen widget or dashboard view.
    """
    _set_cache_headers(response, max_age=30)
    svc = _get_service()
    data = await asyncio.to_thread(svc.get_dashboard)
    logger.info("mobile_dashboard_served")
    return MobileDashboardResponse(**data)


@router.get("/contacts", response_model=MobileContactListResponse)
async def mobile_contacts(
    response: Response,
    query: str = Query("", description="Search filter for name/company/email"),
    limit: int = Query(20, ge=1, le=100, description="Page size"),
    page: int = Query(1, ge=1, description="Page number"),
):
    """Touch-optimised contact list with essential fields only.

    Returns: name, company, tier, phone, email — no heavy nested data.
    """
    _set_cache_headers(response, max_age=60)
    svc = _get_service()
    data = await asyncio.to_thread(svc.get_contacts, query, limit, page)
    logger.info("mobile_contacts_served", page=page, limit=limit, query=query)
    return MobileContactListResponse(**data)


@router.get("/programs", response_model=MobileProgramListResponse)
async def mobile_programs(
    response: Response,
    limit: int = Query(20, ge=1, le=100, description="Page size"),
    page: int = Query(1, ge=1, description="Page number"),
):
    """Compact program list with key metrics only."""
    _set_cache_headers(response, max_age=120)
    svc = _get_service()
    data = await asyncio.to_thread(svc.get_programs, limit, page)
    logger.info("mobile_programs_served", page=page, limit=limit)
    return MobileProgramListResponse(**data)


@router.get("/alerts", response_model=MobileAlertListResponse)
async def mobile_alerts(
    response: Response,
    limit: int = Query(10, ge=1, le=50, description="Max alerts"),
):
    """Recent alerts / notifications for mobile push."""
    _set_cache_headers(response, max_age=15)
    svc = _get_service()
    data = await asyncio.to_thread(svc.get_alerts, limit)
    logger.info("mobile_alerts_served", limit=limit)
    return MobileAlertListResponse(**data)


@router.get("/search", response_model=MobileSearchResponse)
async def mobile_search(
    response: Response,
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Max results"),
):
    """Unified search across contacts, programs, jobs — mobile-friendly results."""
    _set_cache_headers(response, max_age=30)
    svc = _get_service()
    data = await asyncio.to_thread(svc.search, q, limit)
    logger.info("mobile_search_served", query=q, limit=limit, results=data.get("total", 0))
    return MobileSearchResponse(**data)


@router.get("/contact/{contact_id}", response_model=MobileContactDetailResponse)
async def mobile_contact_detail(contact_id: str, response: Response):
    """Single contact detail view optimised for mobile."""
    _set_cache_headers(response, max_age=60)
    svc = _get_service()
    data = await asyncio.to_thread(svc.get_contact_detail, contact_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    logger.info("mobile_contact_detail_served", contact_id=contact_id)
    return MobileContactDetailResponse(**data)


@router.get("/pwa-manifest", response_model=PWAManifest)
async def pwa_manifest(response: Response):
    """PWA manifest.json for installable web app."""
    _set_cache_headers(response, max_age=86400)  # 24 h
    logger.info("pwa_manifest_served")
    return PWAManifest(
        icons=[
            {"src": "/icons/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/icons/icon-512.png", "sizes": "512x512", "type": "image/png"},
        ]
    )
