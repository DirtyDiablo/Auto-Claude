"""Canonical SearchResult dataclass for Engine8 Knowledge System."""

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class SearchResult:
    """Unified search result returned by all retrieval engines."""

    id: str
    score: float
    content: str = ""
    source: str = ""
    collection: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    payload: Dict[str, Any] = field(default_factory=dict)
    search_type: str = ""
    channel_scores: Dict[str, float] = field(default_factory=dict)
