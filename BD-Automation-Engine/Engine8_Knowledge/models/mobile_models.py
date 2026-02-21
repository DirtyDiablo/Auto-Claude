"""Compact Pydantic response models for mobile-optimised API endpoints.

All models are deliberately flat and minimal to keep payloads under 5 KB for
typical responses, supporting offline caching and low-bandwidth scenarios.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

class MobileDashboardResponse(BaseModel):
    """Top-level metrics for the mobile dashboard home screen."""

    pipeline_total: int = Field(0, description="Total items in pipeline")
    hot_leads: int = Field(0, description="Leads with score >= 80")
    warm_leads: int = Field(0, description="Leads with score 50-79")
    avg_score: float = Field(0.0, description="Average BD score")
    contacts_total: int = Field(0, description="Total contacts in system")
    programs_total: int = Field(0, description="Total federal programs")
    recent_alerts: int = Field(0, description="Unread alert count")
    last_updated: str = Field("", description="ISO-8601 timestamp")


# ---------------------------------------------------------------------------
# Contacts
# ---------------------------------------------------------------------------

class MobileContactItem(BaseModel):
    """Compact contact record for list views."""

    id: str
    name: str
    company: str = ""
    tier: int = 0
    tier_label: str = ""
    phone: Optional[str] = None
    email: Optional[str] = None


class MobileContactDetailResponse(BaseModel):
    """Single-contact detail view for mobile."""

    id: str
    name: str
    company: str = ""
    title: str = ""
    tier: int = 0
    tier_label: str = ""
    phone: Optional[str] = None
    email: Optional[str] = None
    program: str = ""
    last_contacted: Optional[str] = None
    notes: Optional[str] = None


class MobileContactListResponse(BaseModel):
    """Paginated contact list."""

    items: List[MobileContactItem] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    limit: int = 20
    has_more: bool = False


# ---------------------------------------------------------------------------
# Programs
# ---------------------------------------------------------------------------

class MobileProgramItem(BaseModel):
    """Compact program record."""

    id: str
    name: str
    agency: str = ""
    value: str = ""
    score: Optional[float] = None


class MobileProgramListResponse(BaseModel):
    """Paginated program list."""

    items: List[MobileProgramItem] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    limit: int = 20
    has_more: bool = False


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------

class MobileAlertItem(BaseModel):
    """Single alert / notification."""

    id: str
    type: str = "info"  # new_opportunity | score_change | contact_update | info
    title: str = ""
    summary: str = ""
    created_at: str = ""
    priority: str = "medium"  # high | medium | low


class MobileAlertListResponse(BaseModel):
    """Alert list."""

    items: List[MobileAlertItem] = Field(default_factory=list)
    total: int = 0


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

class MobileSearchResult(BaseModel):
    """Single unified search result."""

    id: str
    type: str  # contact | program | job
    title: str
    subtitle: str = ""
    score: Optional[float] = None


class MobileSearchResponse(BaseModel):
    """Unified search results."""

    items: List[MobileSearchResult] = Field(default_factory=list)
    total: int = 0
    query: str = ""


# ---------------------------------------------------------------------------
# PWA Manifest
# ---------------------------------------------------------------------------

class PWAIcon(BaseModel):
    """PWA icon descriptor."""

    src: str
    sizes: str
    type: str = "image/png"


class PWAManifest(BaseModel):
    """Progressive Web App manifest."""

    name: str = "PTS BD Intelligence"
    short_name: str = "PTS BD"
    start_url: str = "/"
    display: str = "standalone"
    background_color: str = "#1a1a2e"
    theme_color: str = "#0f3460"
    icons: List[PWAIcon] = Field(default_factory=list)
    description: str = "Federal BD Intelligence Dashboard"
    orientation: str = "any"
