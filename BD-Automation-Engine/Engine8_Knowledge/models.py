"""Pydantic models for BD Knowledge API request/response schemas."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    collection: Optional[str] = Field(None, description="Collection to search")
    limit: int = Field(10, ge=1, le=50, description="Max results")
    score_threshold: float = Field(
        0.3, ge=0.0, le=1.0, description="Min relevance score"
    )
    filters: Optional[Dict[str, Any]] = Field(None, description="Filter conditions")
    rerank: bool = Field(False, description="Apply cross-encoder reranking")


class AskRequest(BaseModel):
    question: str = Field(..., description="Natural language question")
    collection: Optional[str] = Field(None, description="Collection to search")
    limit: int = Field(5, ge=1, le=20, description="Max sources")
    include_sources: bool = Field(True, description="Include source citations")


class SimilarRequest(BaseModel):
    item_id: str = Field(..., description="ID of source item")
    collection: str = Field(..., description="Collection containing the item")
    limit: int = Field(10, ge=1, le=50, description="Max similar items")


class SearchResultModel(BaseModel):
    id: str
    score: float
    payload: Dict[str, Any]
    collection: str


class SearchResponse(BaseModel):
    query: str
    collection: Optional[str]
    results: List[SearchResultModel]
    count: int
    timestamp: str


class AskResponse(BaseModel):
    answer: str
    sources: List[SearchResultModel]
    query: str
    confidence: float
    collection_searched: Optional[str]
    timestamp: str


class StatsResponse(BaseModel):
    collections: Dict[str, Dict[str, Any]]
    total_vectors: int
    timestamp: str


class IndexResponse(BaseModel):
    success: bool
    message: str
    indexed: int
    errors: int
    duration_seconds: float


class MemoryInput(BaseModel):
    content: str
    metadata: Optional[Dict[str, Any]] = None


class InsightInput(BaseModel):
    insight_type: str
    insight: str
    source: str = "user"
    confidence: float = 0.8


class DocumentInput(BaseModel):
    text: str
    metadata: Optional[Dict[str, Any]] = None


class ProgramInput(BaseModel):
    name: str
    description: str = ""
    agency: str = ""
    primes: List[str] = []
    value: str = ""
    clearance: str = ""
    technologies: List[str] = []


class CompanyInput(BaseModel):
    name: str
    type: str = ""
    capabilities: List[str] = []
    programs: List[str] = []
    partners: List[str] = []
    locations: List[str] = []


class ContactInput(BaseModel):
    name: str
    company: str = ""
    title: str = ""
    programs: List[str] = []
    clearance: str = ""


class JobInput(BaseModel):
    title: str
    company: str
    location: str = ""
    clearance: str = ""
    description: str = ""


class FilterRequest(BaseModel):
    """Generic filter request for dashboard endpoints."""
    filters: Dict[str, Any] = Field(default_factory=dict)
    limit: int = Field(50, ge=1, le=500)
    offset: int = Field(0, ge=0)


class StageUpdateRequest(BaseModel):
    """Request to update a job's pipeline stage."""
    stage: str = Field(..., description="New stage name")


class TriggerRequest(BaseModel):
    """Request to trigger a pipeline run."""
    input_file: Optional[str] = None
    test_mode: bool = False
