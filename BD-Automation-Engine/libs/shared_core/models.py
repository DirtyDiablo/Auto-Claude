"""
Common Pydantic base models shared across all engines.

These provide a unified interface for search results, pagination,
status/error responses, and other frequently-used shapes.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    """Unified search result across all collections."""

    id: str
    content: str
    score: float
    collection: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PaginatedResponse(BaseModel):
    """Standard paginated response wrapper."""

    items: List[Any]
    total: int
    page: int
    page_size: int
    has_more: bool

    @classmethod
    def build(
        cls,
        items: List[Any],
        total: int,
        page: int,
        page_size: int,
    ) -> "PaginatedResponse":
        """Convenience factory that computes ``has_more`` automatically."""
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            has_more=(page * page_size) < total,
        )


class StatusResponse(BaseModel):
    """Standard status response."""

    status: str
    message: str
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    details: Dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str
    detail: str
    status_code: int
