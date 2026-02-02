"""Scraped job data models."""
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from .base import BaseDocument


class JobStatus(str, Enum):
    """Job processing status."""
    RAW_IMPORT = "raw_import"
    PENDING_ENRICHMENT = "pending_enrichment"
    ENRICHING = "enriching"
    ENRICHED = "enriched"
    VALIDATED = "validated"
    ERROR = "error"


class ScrapedJob(BaseDocument):
    """
    Scraped job posting model for jobs_unified collection.

    Tracks job postings through the enrichment pipeline.
    """
    title: str
    company: Optional[str] = None
    location: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    detected_clearance: Optional[str] = None
    primary_keyword: Optional[str] = None
    scraped_at: Optional[str] = None
    status: JobStatus = JobStatus.RAW_IMPORT
    mapped_program: Optional[str] = None
    bd_score: float = Field(default=0, ge=0, le=100)
    match_confidence: float = Field(default=0, ge=0, le=1)
    match_type: Optional[str] = None
    match_signals: List[str] = Field(default_factory=list)
    recruiter_name: Optional[str] = None
    recruiter_email: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)
    certifications_required: List[str] = Field(default_factory=list)

    def to_searchable_text(self) -> str:
        """Generate searchable text for embedding."""
        parts = [
            f"Job: {self.title}",
            f"Company: {self.company}" if self.company else "",
            f"Location: {self.location}" if self.location else "",
            f"Clearance: {self.detected_clearance}" if self.detected_clearance else "",
            f"Program: {self.mapped_program}" if self.mapped_program else "",
            f"Technologies: {', '.join(self.technologies)}" if self.technologies else "",
        ]
        return ". ".join(p for p in parts if p)
