"""Base document model for unified data."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from uuid import uuid4
from enum import Enum


class SourceProject(str, Enum):
    """Source project identifier for cross-project data."""
    BD_ENGINE = "bd_engine"
    DATA_SCRAPER = "data_scraper"
    N8N_BUILDER = "n8n_builder"


class BaseDocument(BaseModel):
    """
    Base model for all documents in the unified Qdrant collections.

    All data types (contacts, programs, jobs, activities) inherit from this
    to ensure consistent metadata across the platform.
    """
    id: str = Field(default_factory=lambda: str(uuid4()))
    source_project: SourceProject = SourceProject.BD_ENGINE
    source_type: str = "unknown"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    content_hash: Optional[str] = None
    embedding_model: str = "text-embedding-3-small"
    confidence_score: Optional[float] = Field(None, ge=0, le=1)
    tags: List[str] = Field(default_factory=list)
    notion_page_id: Optional[str] = None

    class Config:
        use_enum_values = True
