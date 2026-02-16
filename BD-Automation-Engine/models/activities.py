"""BD activity/engagement data models."""

from typing import Optional
from datetime import datetime
from enum import Enum
from .base import BaseDocument


class ActivityType(str, Enum):
    """Type of BD activity."""

    CALL = "call"
    EMAIL = "email"
    LINKEDIN = "linkedin"
    MEETING = "meeting"
    NOTE = "note"
    HUMINT = "humint"
    SCRAPE = "scrape"
    ENRICHMENT = "enrichment"


class Activity(BaseDocument):
    """
    BD activity model for activities_log collection.

    Tracks all engagement activities with contacts and programs.
    """

    contact_name: Optional[str] = None
    contact_id: Optional[str] = None
    activity_type: ActivityType
    summary: str
    outcome: Optional[str] = None
    author: Optional[str] = None
    program: Optional[str] = None
    follow_up_date: Optional[datetime] = None

    def to_searchable_text(self) -> str:
        """Generate searchable text for embedding."""
        parts = [
            f"Activity: {self.activity_type.value}",
            f"Contact: {self.contact_name}" if self.contact_name else "",
            f"Program: {self.program}" if self.program else "",
            f"Summary: {self.summary}",
            f"Outcome: {self.outcome}" if self.outcome else "",
        ]
        return ". ".join(p for p in parts if p)
