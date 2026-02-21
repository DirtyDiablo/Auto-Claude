"""Canonical SearchResult dataclass for Engine8 Knowledge System."""

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class SearchResult:
    """Unified search result returned by all retrieval engines.

    Used by vector_store, hybrid_search, and all retrieval pipelines.
    For API serialization, see SearchResultModel in Engine8_Knowledge/models.py.
    """

    id: str
    score: float
    content: str = ""
    source: str = ""
    collection: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    payload: Dict[str, Any] = field(default_factory=dict)
    search_type: str = ""  # "dense", "sparse", "graph", "semantic"
    channel_scores: Dict[str, float] = field(default_factory=dict)
    rrf_score: float = 0.0  # Reciprocal Rank Fusion score (hybrid search)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "score": self.score,
            "content": self.content,
            "source": self.source,
            "collection": self.collection,
            "metadata": self.metadata,
            "payload": self.payload,
            "search_type": self.search_type,
            "channel_scores": self.channel_scores,
            "rrf_score": self.rrf_score,
        }
